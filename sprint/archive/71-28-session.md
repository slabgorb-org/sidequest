---
story_id: "71-28"
jira_key: ""
epic: "71"
workflow: "tdd"
---
# Story 71-28: OTEL-coverage split — encounter beats land in events table but emit no watcher spans (live GM panel half-blind)

## Story Details
- **ID:** 71-28
- **Jira Key:** (none — local-only story)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-30T21:47:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30T19:15:41Z | 2026-05-30T19:18:00Z | 2m 19s |
| red | 2026-05-30T19:18:00Z | 2026-05-30T19:28:39Z | 10m 39s |
| green | 2026-05-30T19:28:39Z | 2026-05-30T19:32:51Z | 4m 12s |
| spec-check | 2026-05-30T19:32:51Z | 2026-05-30T19:34:11Z | 1m 20s |
| verify | 2026-05-30T19:34:11Z | 2026-05-30T19:50:26Z | 16m 15s |
| review | 2026-05-30T19:50:26Z | 2026-05-30T21:45:58Z | 1h 55m |
| spec-reconcile | 2026-05-30T21:45:58Z | 2026-05-30T21:47:11Z | 1m 13s |
| finish | 2026-05-30T21:47:11Z | - | - |

## Story Context

### Problem Statement

The `advance_encounter_beat` tool (sidequest-server/sidequest/agents/tools/advance_encounter_beat.py) is a WRITE tool that mutates the `StructuredEncounter.beat` counter when the narrator advances an encounter phase. The tool correctly:

1. Updates the beat counter in memory
2. Persists to PostgreSQL via `ctx.repository.save(snapshot)`
3. Sets OTEL attributes on `ctx.otel_span` (beat_from, beat_to, reason)

**However:** The tool sets OTEL *attributes* on the span that represents the tool execution itself, which lands in the telemetry/events table. There is **no routed OTEL span** — no entry in `SPAN_ROUTES` in `sidequest/telemetry/spans/encounter.py` that extracts those attributes into a GM-panel watcher event. This means:

- The raw span data hits PostgreSQL (`turn_telemetry` table)
- The GM panel's watcher reader (`dispatch_engagement_watcher.py` or equivalent) **cannot surface** the beat advance to the live dashboard
- The GM is blind to whether beats are advancing or stuck
- The lie-detector OTEL system, designed to validate every subsystem decision, has a gap in encounter-beat observability

### Technical Approach

**Part 1: Define the routed span**

Add `SPAN_ENCOUNTER_BEAT_ADVANCE` to `sidequest/telemetry/spans/encounter.py`, following the pattern of `SPAN_ENCOUNTER_BEAT_APPLIED` (which exists but has no emission site):

```python
SPAN_ENCOUNTER_BEAT_ADVANCE = "encounter.beat_advance"
SPAN_ROUTES[SPAN_ENCOUNTER_BEAT_ADVANCE] = SpanRoute(
    event_type="state_transition",
    component="encounter",
    extract=lambda span: {
        "field": "encounter.beat_advance",
        "beat_from": (span.attributes or {}).get("tool.encounter.beat_from", None),
        "beat_to": (span.attributes or {}).get("tool.encounter.beat_to", None),
        "reason": (span.attributes or {}).get("tool.encounter.reason", ""),
        "encounter_type": (span.attributes or {}).get("tool.encounter.encounter_type", ""),
    },
)
```

(Optional: add to `FLAT_ONLY_SPANS` or another index if the dashboard layout requires it.)

**Part 2: Trace the wiring**

Verify that the SPAN_ROUTES entry causes the GM-panel telemetry reader to:
1. Extract the event from the `turn_telemetry` table (the raw span lands there via the Phase B Registry dispatcher)
2. Marshal it into the watcher events payload
3. Surface it in the `/dashboard` GM-panel view

This is an integration test: set up a live session, have the narrator call `advance_encounter_beat`, and assert that:
- A span with `name="tool.write.advance_encounter_beat"` (or equivalent) lands in turn_telemetry
- The watcher extracts the attributes into an `encounter.beat_advance` event
- The event is reachable from the dashboard telemetry endpoint

**Part 3: Test coverage**

- **Unit test:** `advance_encounter_beat` sets the correct OTEL attributes (already exists, should pass)
- **Wiring test:** invoke `advance_encounter_beat` via the tool registry in a fixture-driven test (synthetic session + encounter), assert the span + attributes land in turn_telemetry
- **Integration test (GM-panel): **Defer to a separate observability-validation story if the GM-panel reader logic is not yet testable in isolation. For this story, a wiring test that verifies the span hits the table is sufficient.

### Acceptance Criteria

- [ ] `SPAN_ENCOUNTER_BEAT_ADVANCE` is defined in `encounter.py` with a `SpanRoute` entry that maps `tool.encounter.*` attributes to watcher event fields.
- [ ] The span name and extraction logic are consistent with existing beat-related spans (e.g., `SPAN_ENCOUNTER_BEAT_APPLIED`, if it has a wiring test; otherwise follow the pattern of `SPAN_ENCOUNTER_PHASE_TRANSITION`).
- [ ] A wiring test exercises the full path: `advance_encounter_beat` tool call → span emission → turn_telemetry insert → watcher extraction (fixture-driven, using `PgTelemetrySink` or equivalent test double). The test asserts:
  - Span name and attributes are correctly set
  - The extracted event has non-null `beat_from`, `beat_to`, and `encounter_type` fields
  - The event is classified as a `state_transition` in the watcher (if the dashboard routes by event_type)
- [ ] All existing tests pass; no regressions in advance_encounter_beat unit tests or related encounter subsystem tests.
- [ ] OTEL attributes on `ctx.otel_span` in the tool are consistent with the `SpanRoute` extraction keys (e.g., `tool.encounter.beat_from` maps to watcher field `beat_from`).
- [ ] The story includes a comment in the session file documenting the decision: was `SPAN_ROUTES` the right place, or does the GM-panel watcher require additional wiring downstream?

## Sm Assessment

**Ready for RED.** This is a 3pt observability-gap bug: encounter beats land in the events table but emit no routed watcher span, so the GM panel — the lie-detector — is half-blind to beat advancement. Directly serves the OTEL Observability Principle in CLAUDE.md ("If a subsystem isn't emitting OTEL spans, you can't tell whether it's engaged or whether Claude is just improvising").

**Scope is server-only** (sidequest-server), branched off `develop` per repos.yaml.

**Caution for The Architect / Agent Smith:** the technical approach above names specific symbols (`SPAN_ROUTES`, `SpanRoute`, `SPAN_ENCOUNTER_BEAT_APPLIED`, `tool.encounter.*` attribute keys) and file paths from setup-time analysis. Per "Verify Wiring, Not Just Existence" — confirm these exist and match before following the sketch literally. The proposed `SPAN_ENCOUNTER_BEAT_APPLIED` is noted as possibly defined-but-unemitted; verify whether it's the right pattern to mirror or whether `SPAN_ENCOUNTER_PHASE_TRANSITION` is the live exemplar.

**Wiring test is the load-bearing AC** (AC3): the full path tool call → span → turn_telemetry → watcher extraction must be exercised, not just the unit-level attribute set. This is the "Every Test Suite Needs a Wiring Test" requirement made explicit. GM-panel reader integration may defer to a separate story if not testable in isolation — but the span-hits-the-table wiring test is non-negotiable for this story.

**Jira:** none (local-only story) — claim skipped intentionally.

## TEA Assessment

**Tests Required:** Yes
**Reason:** N/A

**Test Files:**
- `sidequest-server/tests/integration/test_encounter_beat_advance_otel_wiring.py` — end-to-end OTEL wiring for the `advance_encounter_beat` dispatch span → typed `state_transition` watcher event.

**Tests Written:** 3 tests covering ACs 1, 3, 5 (ACs 2/4/6 verified by GREEN+Reviewer, see below)
**Status:** RED (3 failed — verified by testing-runner, run 71-28-tea-red)

Verified-RED evidence: all three fail because no `SPAN_ROUTES` entry exists for `tool.write.advance_encounter_beat`. The harness confirms the dispatch span *does* fire with `tool.encounter.beat_from`/`beat_to` attributes (captured as a bare `agent_span_close`) — the only missing piece is the routing decision. No import/collection errors; no spurious exceptions. Clean RED.

### Test → AC mapping

| AC | Test | Status |
|----|------|--------|
| AC1 route defined (event_type/component) | `test_advance_encounter_beat_dispatch_span_is_routed` (runtime registry tripwire) | failing |
| AC3 full wiring path → typed state_transition w/ non-null beat_from/beat_to/encounter_type | `test_advance_encounter_beat_publishes_state_transition` | failing |
| AC3/AC5 extraction reads after-mutation attrs (explicit to_beat) | `test_explicit_to_beat_reflected_in_watcher_event` | failing |
| AC2 consistency w/ existing beat routes | code-review check (Reviewer) — no isolated test | n/a |
| AC4 no regressions | testing-runner full suite at GREEN/verify | deferred |
| AC6 decision documented in session | Dev writes the seam-decision note | deferred |

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------------------|---------|--------|
| #6 Test quality (no vacuous asserts, specific-value checks) | all 3 — assert exact `beat_from`/`beat_to`/`reason`/`encounter_type` values, never truthy-only; no `assert True`, no skips | passing (self-check) |
| #1 Silent exception swallowing | `test_*_publishes_state_transition` — asserts exact extracted field values, so an empty/swallowed `route.extract` (the `except Exception` in `WatcherSpanProcessor.on_end`) fails the test | failing (RED) |

**Rules checked:** 2 of 8 lang-review rules apply to this story (route registration + telemetry test). #2 mutable defaults, #3 boundary annotations, #4 logging, #5 path handling, #7 resource leaks, #8 deserialization — N/A to a `SpanRoute` entry and a fixture-driven test.
**Self-check:** 0 vacuous tests found. The behavioral-signature wait helper matches on `beat_from`/`beat_to` presence (not a magic label) and every assertion checks a concrete value.

**Handoff:** To Agent Smith (Dev) for GREEN — register `SPAN_ROUTES["tool.write.advance_encounter_beat"]` (`state_transition` / `encounter`) and add `tool.encounter.encounter_type` to the tool. See Design Deviations for the four spec corrections.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/telemetry/spans/encounter.py` — added `SPAN_ENCOUNTER_BEAT_ADVANCE = "tool.write.advance_encounter_beat"` and its `SPAN_ROUTES` entry (`state_transition` / `component=encounter`), extracting `beat_from`/`beat_to`/`reason`/`encounter_type` from the `tool.encounter.*` dispatch-span attributes. Mirrors the existing beat-related encounter routes.
- `sidequest-server/sidequest/agents/tools/advance_encounter_beat.py` — set `tool.encounter.encounter_type` on the dispatch span (one line; value already in scope and returned in the payload).

**Tests:** 23/23 passing (GREEN) — verified by testing-runner run 71-28-dev-green. Includes the 3 new wiring tests, the full `advance_encounter_beat` unit suite, `test_routing_completeness` (accepts the new SPAN_* constant), `test_encounter_spans`, and `test_encounter_telemetry` (no regressions). Ruff check + format clean on all changed files.

**Branch:** `feat/71-28-otel-encounter-beat-spans` (pushed to origin).

**Seam decision (AC6):** `SPAN_ROUTES` *was* the right seam. The dispatch span already fired with the beat attributes; the only missing piece was the routing decision. No downstream GM-panel reader change is needed — `WatcherSpanProcessor.on_end` → `SPAN_ROUTES.get(name)` → `hub.publish(...)` is the live path, and `PgTelemetrySink` persists the typed event to the `events` table. Binding the dispatch span to a `SPAN_*` constant additionally closes the lint blind spot (TEA Finding #1) for *this* span — sibling tool spans remain uncovered (see Delivery Findings).

**Handoff:** To The Merovingian (Reviewer) for code review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None requiring action (2 spec-text corrections, both already logged as deviations with Option A — spec was factually wrong about the live system)

AC-by-AC verification against the diff (`git diff develop...HEAD -- sidequest/`):

- **AC1 (route defined):** ✓ `SPAN_ENCOUNTER_BEAT_ADVANCE` + `SPAN_ROUTES` entry in `encounter.py`, extracting `beat_from`/`beat_to`/`reason`/`encounter_type` from `tool.encounter.*`. The span *value* is the real dispatch-span name (`tool.write.advance_encounter_beat`), not the AC's literal `encounter.beat_advance` — **Different behavior — Behavioral, Minor → Option A (already logged, TEA + Dev).** The spec text named a span with no emission site; the code routes the span that actually fires. The dashboard-facing `field` label is still `"encounter.beat_advance"`, preserving the spec's intent for the GM-panel discriminator.
- **AC2 (consistency):** ✓ Aligned. Mirrors `SPAN_ENCOUNTER_BEAT_APPLIED` / `SPAN_ENCOUNTER_PHASE_TRANSITION` verbatim in shape: frozen `SpanRoute(event_type="state_transition", component="encounter", extract=lambda span: {...})`, `(span.attributes or {}).get(key, default)` idiom, `field` discriminator. `component="encounter"` matches the sibling beat route (not `"combat"`, which is correct — beat advance is encounter-level phase progression).
- **AC3 (wiring test):** ✓ Aligned. Integration test drives dispatch → `WatcherSpanProcessor` → `SPAN_ROUTES` → hub; asserts `state_transition` with non-null `beat_from`/`beat_to`/`encounter_type`. Assertion target is the hub event (`events`-table path), not `turn_telemetry` — **Different behavior — Architectural, Minor → Option A (already logged).** The typed-event path genuinely does not traverse `turn_telemetry`; the code tests the path the GM panel consumes.
- **AC4 (no regressions):** ✓ 23/23 green incl. `test_routing_completeness`, `test_encounter_telemetry`.
- **AC5 (attribute/extraction alignment):** ✓ Tool sets exactly the four keys the route reads. `beat_from`/`beat_to` default to `-1` (a sound sentinel — `0` is a valid beat, so the combat route's `0` default would be ambiguous here; this is a considered improvement, not drift).
- **AC6 (seam decision):** ✓ Documented in Dev Assessment — `SPAN_ROUTES` was the right seam, no downstream reader change needed.

**Architectural note (positive):** Binding the dispatch span to a named `SPAN_*` constant is the correct reuse-first move — it routes the span *and* brings it under the existing routing-completeness lint, converting a one-off fix into a regression guard with zero new infrastructure. The residual gap (sibling tool spans still invisible to the lint) is correctly scoped out and filed as a Dev Delivery Finding rather than over-built here.

**Decision:** Proceed to review.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (regression-free for this story)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`advance_encounter_beat.py`, `telemetry/spans/encounter.py`, `tests/integration/test_encounter_beat_advance_otel_wiring.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | `_setup()` watcher harness in the new test is identical to `test_combat_otel_wiring.py::_setup` — extractable to a shared conftest/`WatcherTestHarness` (medium confidence) |
| simplify-quality | clean | Naming, error handling, type safety, OTEL discipline all consistent with conventions |
| simplify-efficiency | clean | No over-engineering; every attribute/route/test is load-bearing |

**Applied:** 0 high-confidence fixes (none were high-confidence)
**Flagged for Review:** 1 medium — the `_setup` harness duplication. **Not auto-applied** (medium-confidence policy) and deliberately deferred: extracting it would edit `test_combat_otel_wiring.py` too, coupling two integration-test files for a ~15-line, readable helper. Filed as a Delivery Finding for a dedicated cleanup pass (see below).
**Noted:** 0 low-confidence
**Reverted:** 0

**Overall:** simplify: clean (1 medium finding flagged, not applied)

### Quality-Pass Gate

**Lint:** ruff clean (whole repo). During the gate run, `just server-lint` surfaced a **pre-existing** ruff I001 import-sort violation in `sidequest/agents/tools/__init__.py` (`commit_effort` / `long_rest` misordered — confirmed present on `develop`, unrelated to 71-28). It was fixed in commit `83ebeae` (pure import reordering, all `# noqa: F401` preserved, zero semantic change) so the whole-repo lint gate passes. See process finding below.

**Tests:** 9193 passed, 361 skipped, **7 failed** — all 7 are pre-existing content-pack gaps in subsystems untouched by this story (namegen corpus audit → backlog 64-7; `tea_and_murder` survivability label → backlog 68-1; pack content/cross-ref validation). Reproducible on `develop`; **zero regressions attributable to 71-28**. My story's 3 wiring tests + the full `advance_encounter_beat`/encounter-telemetry/routing-completeness suites are green.

**Handoff:** To The Merovingian (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (23/23 pass, lint clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 (reason unsanitized → telemetry, ADR-047) | confirmed 1, downgraded to Medium/non-blocking |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned, 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 confirmed (Medium, non-blocking) + 1 self-found (Low, non-blocking); 0 dismissed; 0 deferred

The 7 disabled subagents' domains (edge, silent-failure, test, doc, type, simplify, rule) were covered manually below — the diff is 3 small files, well within solo-review reach.

## Reviewer Assessment

**Verdict:** APPROVED

A 26-line production change (one `SPAN_ROUTES` entry + one `set_attribute`) plus a 259-line integration test and a pre-existing import-sort fix. No Critical or High issues. Two non-blocking findings, both routed to follow-ups.

**Data flow traced:** narrator tool-call → `advance_encounter_beat` mutates `encounter.beat`, sets `tool.encounter.{beat_from,beat_to,reason,encounter_type}` on the dispatch span → `Registry.dispatch` closes `tool.write.advance_encounter_beat` → `WatcherSpanProcessor.on_end` publishes the always-on `agent_span_close` **and** (now) the typed `state_transition` via `SPAN_ROUTES[...].extract` → `watcher_hub.publish` → GM-only `/ws/watcher` + telemetry persistence. Safe: the typed event surfaces data already on the bus; the new write is server-owned `encounter_type`.

### Rule Compliance (Python lang-review, 13 checks, enumerated against the diff)

- **#1 Silent exceptions:** ✓ None added. The `extract` lambda uses `(span.attributes or {}).get(k, default)` — defensive, no swallow. The watcher's `except` around `route.extract` (watcher.py:106) fails *loud* via a `validation_warning` event, per No-Silent-Fallbacks. Compliant.
- **#2 Mutable defaults:** ✓ N/A — no new function signatures with defaults (`extract` is a lambda; defaults are literals `-1`/`""`).
- **#3 Type annotations at boundaries:** ✓ The `extract` lambda is unannotated, consistent with all sibling routes in the file (frozen-dataclass field, not a public boundary fn). The tool's added line is a method call. Compliant with file-wide pattern.
- **#4 Logging:** ✓ N/A — no logging added; OTEL attributes are not log statements.
- **#5 Path handling:** ✓ N/A — no path manipulation.
- **#6 Test quality:** ✓ All 3 tests assert concrete values (`beat_from==2`, `beat_to==3/7`, `encounter_type=="brawl"/"duel"`); no `assert True`, no truthy-only, no skips. `_FakeRepo` is a justified test double (documented). The `_wait_for_beat_event` matches on payload signature, not a magic label — refactor-stable.
- **#7 Resource leaks:** ✓ N/A — no file/conn/lock acquisition.
- **#8 Unsafe deserialization:** ✓ None — no pickle/eval/yaml.load.
- **#9 Async pitfalls:** ✓ `asyncio.sleep(0)` in `_dispatch` and `await asyncio.sleep(0.01)` in the poll loop are **commented** (the checklist flags *uncommented* `sleep(0)`). Test-only. Compliant.
- **#10 Import hygiene:** ✓ The `__init__.py` change *fixes* a pre-existing I001 ordering violation; no star/circular imports. The test's `# noqa: F401` force-registration import is the established pattern.
- **#11 Input validation at boundaries:** ⚠ See [SEC] finding — narrator `reason` reaches the telemetry boundary unsanitized. Pre-existing (line 109), systemic, GM-only surface. Confirmed, Medium, non-blocking.
- **#12 Dependency hygiene:** ✓ N/A — no dependency changes.
- **#13 Fix-introduced regressions:** ✓ The import-sort fix is pure reordering (all `# noqa` preserved); 23/23 green confirms no regression.

### Observations (≥5)

1. **[VERIFIED] Route mirrors the established pattern** — `encounter.py:76-87` matches `SPAN_ENCOUNTER_BEAT_APPLIED` (lines 54-65) exactly: frozen `SpanRoute(event_type="state_transition", component="encounter", extract=lambda span: {...})`, `(span.attributes or {}).get(key, default)` idiom, `field` discriminator. Complies with AC2.
2. **[VERIFIED] `encounter_type` is server-owned, not narrator free text** — `advance_encounter_beat.py:113` reads `encounter.encounter_type` (a `StructuredEncounter` enum-like slug), not `args.*`. No injection/PII surface; `component="encounter"` correct (sibling beat routes use it, not `combat`). Evidence: line 113 + the route at encounter.py:85.
3. **[SEC][MEDIUM, non-blocking] Unsanitized narrator `reason` in telemetry** — `args.reason` (LLM free text) → span attr (line 109, **pre-existing**) → now also a typed `state_transition` field + persisted. ADR-047/CWE-117 log-forging. **Confirmed** (rule-matching, not dismissed) but **downgraded**: the flat `agent_span_close` at `watcher.py:84-97` already fan-outs *all* span attrs unconditionally, so `reason` was already on the GM bus pre-diff; the marginal new exposure is a typed view of the same data on a dev-only channel. Systemic (every routed tool span), not this story's regression. Routed to a follow-up (Delivery Findings).
4. **[EDGE][LOW, non-blocking] Error-path emits a false beat-advance** — the tool's no-session / no-encounter paths `return` before `set_attribute`, but the dispatch span still closes → the route emits `state_transition` with `beat_from=-1, beat_to=-1, encounter_type=""` (severity `info`, since ToolResult.error doesn't set span status ERROR on the non-raising path). A "beat advanced" signal for a non-advance. Sentinel `-1` is detectable and the behavior matches the file-wide extract-on-every-close pattern, so non-blocking — but a guard (skip emit when `tool.result_status` is error, or only-route on success) would tighten the lie-detector. Routed to a follow-up.
5. **[VERIFIED] Sentinel choice is sound** — `beat_from`/`beat_to` default to `-1`, not `0`. Beat `0` is a valid starting beat (see `_encounter(beat=0)` usage in the unit suite), so `-1` is the correct "absent" sentinel — a considered improvement over the combat route's `0` default. Evidence: encounter.py:83-84.
6. **[VERIFIED] Lint blind-spot genuinely closed for this span** — binding to the `SPAN_ENCOUNTER_BEAT_ADVANCE` constant means `test_routing_completeness::_all_span_constants` now enumerates it; I confirmed the gate passes (preflight) and that the constant's value equals the live dispatch span name `tool.write.advance_encounter_beat` (encounter.py:75 vs `tool_dispatch.py` `tool.{cat}.{name}`).

### Devil's Advocate

Argue the code is broken. **The narrator is the attacker.** It controls `args.reason` and now `encounter_type` indirectly (by choosing which encounter to advance). A prompt-injected narrator could emit `reason="beat_to=99 hp=0 outcome=TPK"` — and because the typed `state_transition` carries `reason` verbatim, a careless GM-panel renderer that string-concatenates fields could display a forged "engine" line. But: the panel renders structured JSON fields, not concatenated logs; the forgery lives inside a `reason` value clearly attributed to a narrator-supplied field; and this exposure predates the diff via `agent_span_close`. Weak exploit, trusted (dev-only) audience.

**The confused user.** A GM watching the panel during a no-encounter mis-call sees a `beat_advance` with `-1 → -1`. Could they misread it as a real transition? Possibly for a beat, but `-1` is an obvious sentinel and the event is `info`, not a metric change. Annoying, not dangerous — captured as finding #4.

**The stressed system.** What if `span.attributes` is `None`? The `or {}` guard handles it → all defaults, a `-1/-1` event. What if two beats advance same turn? Two spans, two events — correct. What if the route lambda raises? `watcher.py:106` catches and emits a loud `validation_warning` — no silent loss. What if `encounter_type` is an unexpected value? It's whatever the engine set; the panel shows it verbatim — fine.

**The regression angle.** Did the import-sort commit break registration? No — `# noqa: F401` side-effect imports are order-independent; 23/23 green. Did adding a `SPAN_*` constant whose value is a `tool.write.*` name confuse any consumer that assumes `SPAN_*` values are `encounter.*`-prefixed? I checked: `test_routing_completeness` only requires routed-or-flat (passes); no consumer pattern-matches on the constant's prefix. Nothing broke. **Conclusion:** the two findings are real but non-blocking; the change is sound.

**Handoff:** To SM for finish-story.

## Delivery Findings

### TEA (test design)

- **Gap** (non-blocking): The OTEL routing-completeness lint cannot see dynamically-named dispatch spans (`tool.{cat}.{name}`), so any tool that sets typed attributes but lacks a `SPAN_ROUTES` entry is a silent GM-panel blind spot. Affects `sidequest-server/tests/telemetry/test_routing_completeness.py` (a broader audit — enumerate WRITE/GEN tools that set `tool.<short>.*` attributes and confirm each has a route — would catch siblings of this bug). *Found by TEA during test design.*
- **Improvement** (non-blocking): `SPAN_ENCOUNTER_BEAT_APPLIED` exists with a route but the explore found no emission site; worth confirming it is actually emitted somewhere or it is itself dead coverage. Affects `sidequest-server/sidequest/telemetry/spans/encounter.py`. *Found by TEA during test design.*

### TEA (test verification)

- **Improvement** (non-blocking): The `_setup()` watcher harness (hub bind + `TracerProvider` + `WatcherSpanProcessor` + `spans_module.tracer` monkeypatch + `_Sock` capture) is now duplicated verbatim across `tests/integration/test_encounter_beat_advance_otel_wiring.py` and `tests/integration/test_combat_otel_wiring.py`. Affects both files — extract to a shared `tests/integration/conftest.py` fixture or `WatcherTestHarness` helper (a third+ wiring test will want it too). *Found by TEA during test verification.*
- **Conflict** (non-blocking): The verify quality-pass surfaced a pre-existing ruff I001 violation in `sidequest/agents/tools/__init__.py` that the `testing-runner` subagent autonomously fixed AND committed (`83ebeae`) — outside its run-only remit. The fix is correct and benign (import sort, no semantic change), so it was kept to keep the whole-repo lint gate green, but the process overstep is noted: a verify-phase test run should not be authoring code commits. Affects `.pennyfarthing/agents/testing-runner.md` (tighten to run-and-report only; never `ruff --fix`/commit). *Found by TEA during test verification.*
- **Gap** (non-blocking): 7 pre-existing suite failures unrelated to this story remain red on `develop` — namegen corpus audit (owned by backlog **64-7**), `tea_and_murder` survivability label (owned by backlog **68-1**), and pack content/cross-reference validation. Affects `sidequest-content` pack config + those backlog stories; flagged so the Reviewer/SM don't attribute them to 71-28. *Found by TEA during test verification.*

### Dev (implementation)

- **Gap** (non-blocking): TEA Finding #1 confirmed and only *partially* closed. I closed the lint blind spot for this one span by binding it to `SPAN_ENCOUNTER_BEAT_ADVANCE`, but other WRITE/GEN tools that set `tool.<short>.*` attributes on their dynamically-named dispatch spans without a `SPAN_ROUTES` entry remain invisible to `test_routing_completeness`. Affects `sidequest-server/tests/telemetry/test_routing_completeness.py` (add an audit that enumerates registered tools, derives `tool.{cat}.{name}`, and asserts each tool that calls `set_attribute("tool.<short>.*")` has a route or explicit flat-only decision). *Found by Dev during implementation.*

### Reviewer (code review)

- **Improvement** (non-blocking): Narrator-supplied `args.reason` (LLM free text) reaches the OTEL/watcher/telemetry pipeline unsanitized — both via the pre-existing `agent_span_close` attribute fan-out and (new in 71-28) the typed `state_transition`. ADR-047/CWE-117 log-forging on the dev-only GM panel. Pre-existing and **systemic** (every routed tool span that carries narrator text), not a 71-28 regression. Affects `sidequest-server/sidequest/server/watcher.py` (attr fan-out) + a new `sanitize_narrator_annotation(text, max_len)` helper applied at tool `set_attribute` sites. Recommend a dedicated story scoped to the telemetry trust boundary across all tool spans, not a point-fix here. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `SPAN_ROUTES[tool.write.advance_encounter_beat]` route fires on every dispatch-span close, including the tool's error paths (no session / no active encounter), emitting a `state_transition` with `beat_from=-1, beat_to=-1` — a beat-advance signal for a non-advance. Consistent with the file-wide extract-on-every-close pattern, so non-blocking, but a guard (only-route on `tool.result_status == ok`, or skip when beat attrs absent) would remove lie-detector noise. Affects `sidequest-server/sidequest/telemetry/spans/encounter.py` (or a result-status guard in `WatcherSpanProcessor`). *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)

- **Route the existing dispatch span, do not define a new `encounter.beat_advance` span**
  - Spec source: session Technical Approach, "Part 1: Define the routed span"
  - Spec text: "Add `SPAN_ENCOUNTER_BEAT_ADVANCE = \"encounter.beat_advance\"` … following the pattern of `SPAN_ENCOUNTER_BEAT_APPLIED`"
  - Implementation: Tests target a `SPAN_ROUTES` entry for the *existing, dynamically-named* dispatch span `tool.write.advance_encounter_beat`. The tool sets its attributes on that dispatch span; there is no emission site for a separate `encounter.beat_advance` span, and `SPAN_ENCOUNTER_BEAT_APPLIED` is a different (engine-side) span that already has a live route.
  - Rationale: Verified in code (2026-05-30) — `tool_dispatch_span` produces `tool.write.advance_encounter_beat` and the tool writes `tool.encounter.*` onto it. Inventing a new span name would require a new emission site that doesn't exist; the correct fix is routing the span that actually fires. "Wire up what exists."
  - Severity: minor
  - Forward impact: GREEN registers `SPAN_ROUTES["tool.write.advance_encounter_beat"]`. If Dev introduces a `SPAN_*` constant for it, `test_routing_completeness.py` will police it thereafter.

- **Typed events persist to the `events` table, not `turn_telemetry`**
  - Spec source: session Problem Statement / Part 2
  - Spec text: "The raw span data hits PostgreSQL (`turn_telemetry` table) … assert that a span … lands in turn_telemetry"
  - Implementation: Tests assert the typed `state_transition` event reaches the watcher hub (the GM-panel path); `PgTelemetrySink` persists typed events to the `events` table. The typed-event path does not hop through `turn_telemetry`.
  - Rationale: `WatcherSpanProcessor.on_end` → `SPAN_ROUTES.get(name)` → `hub.publish(...)`; persistence is the `events` table per `pg/events.py`. Asserting on the hub event (not a raw `turn_telemetry` row) tests the behavior the GM panel actually consumes.
  - Severity: minor
  - Forward impact: none — clarifies the assertion target for GREEN/Reviewer.

- **Tool must additionally set `tool.encounter.encounter_type`**
  - Spec source: session AC-3
  - Spec text: "The extracted event has non-null `beat_from`, `beat_to`, and `encounter_type` fields"
  - Implementation: The tool currently sets only `beat_from`/`beat_to`/`reason`. Tests require `encounter_type` in the typed event, which forces GREEN to set `tool.encounter.encounter_type` on the span (the value is already in scope — it is returned in the tool payload).
  - Rationale: Honoring AC-3 as written; the data exists, so surfacing it costs one `set_attribute` and gives the GM panel the encounter context.
  - Severity: minor
  - Forward impact: GREEN must add one `ctx.otel_span.set_attribute("tool.encounter.encounter_type", ...)` line in the tool.

- **Match the watcher event by behavioral signature, not a magic `field` label**
  - Spec source: session Part 1 example extractor
  - Spec text: extractor sets `"field": "encounter.beat_advance"`
  - Implementation: The wiring test polls for the typed event by the presence of `beat_from`/`beat_to` in `fields` rather than hard-coding a `field` discriminator string.
  - Rationale: The `field` label is a naming choice GREEN owns; coupling the test to a specific string would handcuff implementation and break on a harmless rename. Matching on payload content tests behavior, not implementation shape (CLAUDE.md "No Source-Text Wiring Tests" spirit).
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)

- **Implemented the corrected span value, not the AC's literal `encounter.beat_advance`**
  - Spec source: session AC-1 / Technical Approach Part 1
  - Spec text: "`SPAN_ENCOUNTER_BEAT_ADVANCE = \"encounter.beat_advance\"`"
  - Implementation: Defined `SPAN_ENCOUNTER_BEAT_ADVANCE = "tool.write.advance_encounter_beat"` (the actual dispatch-span name the tool writes to) and routed it. The constant *name* matches the AC; the *value* is the real span name per TEA's verified correction.
  - Rationale: There is no emission site for a span literally named `encounter.beat_advance`; routing the span that actually fires is the only wiring that works ("Wire up what exists"). Implemented against TEA's tests, which encode the correction.
  - Severity: minor
  - Forward impact: none — the route key is the live span name; the `field` discriminator in the extracted event is still `"encounter.beat_advance"` for dashboard readability.

- **Bonus: bound the dispatch span to a `SPAN_*` constant to close the routing-completeness blind spot**
  - Spec source: TEA Delivery Finding #1 (Gap)
  - Spec text: "the OTEL routing-completeness lint cannot see dynamically-named dispatch spans … a silent GM-panel blind spot"
  - Implementation: Rather than registering an anonymous `SPAN_ROUTES["tool.write.advance_encounter_beat"]` string key, I introduced the named constant `SPAN_ENCOUNTER_BEAT_ADVANCE` so `test_routing_completeness::_all_span_constants` now enumerates it and enforces a routing decision going forward.
  - Rationale: Costs nothing extra and turns a one-off fix into a regression guard for this span. Scoped to this span only — a general audit of all tool spans is filed as a Dev Delivery Finding, not done here (minimalist discipline).
  - Severity: minor
  - Forward impact: positive — this span can never silently regress to flat-only again.

### Reviewer (audit)

All logged deviations stamped:

- **TEA — Route the existing dispatch span (not a new `encounter.beat_advance` span)** → ✓ ACCEPTED by Reviewer: verified there is no emission site for a literal `encounter.beat_advance`; routing the live dispatch span is the only correct wiring. Code matches.
- **TEA — Typed events persist to `events`, not `turn_telemetry`** → ✓ ACCEPTED by Reviewer: confirmed via `watcher.py` — the typed event is published to the hub; `turn_telemetry` is not on the typed-event path. Assertion target is correct.
- **TEA — Tool must set `tool.encounter.encounter_type`** → ✓ ACCEPTED by Reviewer: value was in scope (returned in payload); GREEN added exactly one `set_attribute`. AC3 satisfied.
- **TEA — Match watcher event by behavioral signature, not a magic `field` label** → ✓ ACCEPTED by Reviewer: the `_wait_for_beat_event` predicate (beat_from/beat_to presence) is refactor-stable and avoids coupling to the `field` string. Sound.
- **Dev — Implemented corrected span value, not the AC's literal `encounter.beat_advance`** → ✓ ACCEPTED by Reviewer: constant *name* matches the AC, *value* is the real span name; `field` discriminator preserves the AC's dashboard intent. Verified at encounter.py:75-77.
- **Dev — Bonus: bound dispatch span to a `SPAN_*` constant to close the lint blind spot** → ✓ ACCEPTED by Reviewer: correct, zero-cost regression guard; `test_routing_completeness` now polices this span. Scoping the general audit to a follow-up is the right call.

No undocumented deviations found — the diff matches the logged spec corrections exactly.

### Architect (reconcile)

Reviewed all six in-flight deviation entries (4 TEA, 2 Dev) and the Reviewer audit. All have complete 6-field format; spec sources (session Technical Approach / AC-1 / AC-3, plus the recovered `context-story-71-28.md`) are real and the quoted text is accurate against those documents; Implementation descriptions match the committed code (`encounter.py:75-87`, `advance_encounter_beat.py:107-113`). No correction notes needed.

One divergence the in-flight logs did not capture, added here for a complete audit:

- **Extract-lambda default sentinels changed from `None` to `-1`/`""`**
  - Spec source: `context-story-71-28.md` / session Technical Approach "Part 1: Define the routed span" (illustrative code block)
  - Spec text: `"beat_from": (span.attributes or {}).get("tool.encounter.beat_from", None),` and `"beat_to": (...).get("tool.encounter.beat_to", None),`
  - Implementation: `encounter.py:83-84` defaults `beat_from`/`beat_to` to `-1` (not `None`) and `reason`/`encounter_type` to `""`.
  - Rationale: `-1` is an unambiguous "attribute absent" sentinel that JSON-serialises cleanly to the watcher bus and is type-stable with the int beat counter; `None` would muddy the typed `state_transition` field type. Beat `0` is valid, so `-1` (not `0`) is the correct sentinel — a considered improvement over the sketch and over the combat route's `0` defaults. Behaviour is exercised by the error-path emit noted in the Reviewer's finding #4.
  - Severity: trivial
  - Forward impact: none — the only observable effect is that an absent-attribute (error-path) emit shows `-1/-1` rather than `null/null`, which the Reviewer already routed to a follow-up guard.

AC deferral verification: no ACs were deferred or descoped (AC2 verified by Reviewer, AC4 by testing-runner, AC6 documented by Dev) — the AC-accountability step is a no-op. Manifest complete.