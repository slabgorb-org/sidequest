---
story_id: "22-4"
jira_key: null
epic: "22"
workflow: "tdd"
---

# Story 22-4: Seed trope OTEL + GM panel — seed_fired, seed_expired, seed_promoted spans

## Story Details
- **ID:** 22-4
- **Epic:** 22 — Seed Tropes — Narrative Variety via Schrödinger's Gun
- **Jira Key:** None (personal project, no Jira)
- **Workflow:** tdd
- **Points:** 2
- **Priority:** p2
- **Repos:** server (sidequest-server)
- **Branch:** feat/22-4-seed-trope-otel

## Acceptance Criteria

From epic-22.yaml:

1. **OTEL Span Coverage:** Add three OTEL span definitions to `sidequest/telemetry/spans/seed.py`:
   - `SPAN_SEED_FIRED` — emitted when a seed triggers/activates during narrator context injection (sibling discipline of `SPAN_TROPE_ACTIVATE`)
   - `SPAN_SEED_EXPIRED` — already implemented in 22-3; verify wiring complete
   - `SPAN_SEED_PROMOTED` — emitted when a seed is "promoted" (mechanic TBD, likely cross-session callback or ghost→active resurrection per future stories)

2. **GM Panel Routing:** Move seed spans from `FLAT_ONLY_SPANS` into a typed `Subsystems` tab entry so the GM panel can drill down into seed lifecycle alongside trope engine events (analogous to how `SPAN_TROPE_ACTIVATE` / `SPAN_TROPE_RESOLVE` appear in a Tropes subsystem tab).

3. **Call-Site Verification:** Ensure the three span types are emitted at the right seams:
   - `seed.drawn` and `seed.expired` from 22-3 code paths must fire correctly (regression test)
   - `seed.fired` seam location TBD (during narrator VALLEY-zone context injection? at render time?)
   - `seed.promoted` seam location TBD (deferred to 22-5 or future story, but scaffold the span definition now)

4. **No Silent Fallbacks:** If a span is defined but not wired into a call site, tests must fail loudly. Unit tests verify span emissions; integration wiring test confirms end-to-end path from trigger → span fire → GM panel receipt.

## Technical Context

### Prior Story Work

- **Story 22-1** (done 2026-05-21) — `SeedTrope` schema, `SeedDeck` engine, `SeedState` / `SeedGhost` persistence in `GameSnapshot`
- **Story 22-2** (done 2026-05-23) — 20-30 seeds authored for `tea_and_murder` pack with flavor tags and delivery hints
- **Story 22-3** (done 2026-05-23) — Narrator VALLEY-zone context injection via `seed_context_builder.py`; `tick_seeds()` wires expiry logic; initial `SPAN_SEED_DRAWN` / `SPAN_SEED_EXPIRED` definitions in `telemetry/spans/seed.py`

### Architecture Pointers

1. **Span definitions** live at `sidequest/telemetry/spans/seed.py`:
   - Already exists with `SPAN_SEED_DRAWN` and `SPAN_SEED_EXPIRED`
   - Add `SPAN_SEED_FIRED` and `SPAN_SEED_PROMOTED`
   - Move from `FLAT_ONLY_SPANS` to a typed subsystem registry (see `sidequest/telemetry/spans/_core.py` for registry patterns)

2. **OTEL Observability Principle** (CLAUDE.md):
   - Every backend fix touching a subsystem MUST emit OTEL watcher events
   - GM panel is the lie detector — if a subsystem doesn't emit spans, we can't tell if it's engaged or if Claude is improvising
   - Seed trope lifecycle is *not* narrator-tool-driven (seeds mature whether or not the narrator calls time-advancing tools) — state materialization, not improvisation
   - Each state-changing engine decision gets one span (similar to `SPAN_TROPE_ACTIVATE` / `SPAN_TROPE_RESOLVE`)

3. **Related ADRs:**
   - **ADR-031** — Game Watcher semantic telemetry; spans carry subsystem state snapshots
   - **ADR-090** — OTEL Dashboard restoration after Python port
   - **ADR-103** — Native OTEL via tool registry (partial; seed engine predates tool-registry)
   - **ADR-018** — Trope Engine (macro arcs; seed engine is the sibling short-arc subsystem)

4. **Call Sites to Verify:**
   - `sidequest/game/seed_tick.py:tick_seeds()` — already emits `SPAN_SEED_EXPIRED` per migration
   - `sidequest/game/seed_tick.py:ensure_initial_draw()` — already emits `SPAN_SEED_DRAWN` per dealt seed
   - `sidequest/agents/seed_context_builder.py` — render seam where VALLEY-zone context is built (likely location for `SPAN_SEED_FIRED` emit?)
   - Future: resolution seams for `SPAN_SEED_PROMOTED` (deferred to 22-5)

5. **Test Infrastructure:**
   - `tests/game/test_seed_expiry.py` — existing RED-phase tests verify `tick_seeds()` behavior and OTEL emissions
   - Add new tests for `SPAN_SEED_FIRED` once call site is identified
   - Verify GM panel receives seed subsystem tabs alongside trope tabs (integration-level check)

### Wiring Checklist

- [ ] Add `SPAN_SEED_FIRED` and `SPAN_SEED_PROMOTED` to `sidequest/telemetry/spans/seed.py`
- [ ] Move seed spans to typed subsystem registry (exit `FLAT_ONLY_SPANS`)
- [ ] Identify and wire `SPAN_SEED_FIRED` call site (likely `seed_context_builder.py`)
- [ ] Add unit tests for `SPAN_SEED_FIRED` emission (RED phase fixtures)
- [ ] Add integration test: GM panel receives seed subsystem tab with all three span types
- [ ] Scaffold `SPAN_SEED_PROMOTED` definition (no call site wired yet; defer to 22-5)
- [ ] Verify `SPAN_SEED_DRAWN` and `SPAN_SEED_EXPIRED` are still firing (regression)

## Workflow Tracking

**Workflow:** tdd  
**Phase:** finish  
**Phase Started:** 2026-05-25T06:25:40Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-05-25 | 2026-05-25T05:55:58Z | 5h 55m |
| green | 2026-05-25T05:55:58Z | 2026-05-25T06:10:43Z | 14m 45s |
| spec-check | 2026-05-25T06:10:43Z | 2026-05-25T06:12:02Z | 1m 19s |
| verify | 2026-05-25T06:12:02Z | 2026-05-25T06:15:00Z | 2m 58s |
| review | 2026-05-25T06:15:00Z | 2026-05-25T06:24:45Z | 9m 45s |
| spec-reconcile | 2026-05-25T06:24:45Z | 2026-05-25T06:25:40Z | 55s |
| finish | 2026-05-25T06:25:40Z | - | - |

## Sm Assessment

Story 22-4 is ready for RED phase. The seed trope engine landed in 22-1/22-2/22-3 with two span types already defined (SPAN_SEED_DRAWN, SPAN_SEED_EXPIRED). This story adds SPAN_SEED_FIRED wiring and scaffolds SPAN_SEED_PROMOTED, then moves seed spans into a typed subsystem registry for GM panel routing. TDD workflow — TEA writes failing tests first, Dev makes them pass. 2 points, straightforward OTEL instrumentation work with clear prior art in the trope engine spans.

## TEA Assessment

**Tests Required:** Yes
**Reason:** OTEL instrumentation story — span definitions, routing, and emission all need test coverage.

**Test Files:**
- `tests/telemetry/test_seed_span_routing.py` — 12 tests: span constant existence (AC1), FLAT_ONLY→SPAN_ROUTES migration (AC2), component/event_type consistency (AC2), extractor field contracts (AC2)
- `tests/telemetry/test_seed_fired_emission.py` — 8 tests: per-seed SPAN_SEED_FIRED emission from build_seed_context_block (AC3), ghost exclusion (AC3), empty state (AC3), mixed state (AC3), regression guards for DRAWN/EXPIRED after routing migration (AC3), top-level import wiring (AC4)

**Tests Written:** 20 tests covering 4 ACs
**Status:** RED (18 failing, 2 passing — regression guards only)

### Failure Breakdown
- **ImportError (13 tests):** `SPAN_SEED_FIRED` / `SPAN_SEED_PROMOTED` not yet defined in `spans/seed.py`
- **KeyError (5 tests):** `SPAN_SEED_DRAWN` / `SPAN_SEED_EXPIRED` not yet migrated from `FLAT_ONLY_SPANS` to `SPAN_ROUTES`
- **Passing (2 tests):** Regression guards (`test_seed_drawn_still_fires_after_routing_migration`, `test_seed_expired_still_fires_after_routing_migration`) — existing emission call sites work today

### Regression Check
24 existing seed tests pass clean (test_seed_expiry.py, test_seed_valley_injection.py, test_routing_completeness.py).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality | Self-checked all 20 tests — every test has meaningful assertions, no vacuous `assert True` or `let _ =` | pass |
| #10 import hygiene | `test_all_four_seed_span_constants_importable` — verifies `__all__` coverage | failing |
| #14 state cleanup ordering | Not applicable — no lifecycle queue consumption in this story | n/a |

**Rules checked:** 2 of 14 applicable (most rules apply to implementation code, not span definitions)
**Self-check:** 0 vacuous tests found

**Handoff:** To Major Winchester for implementation (GREEN phase)

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/telemetry/spans/seed.py` — Added SPAN_SEED_FIRED + SPAN_SEED_PROMOTED constants; migrated DRAWN/EXPIRED from FLAT_ONLY_SPANS to SPAN_ROUTES with component="seeds" extractors; added PROMOTED to FLAT_ONLY_SPANS
- `sidequest/agents/seed_context_builder.py` — Wired SPAN_SEED_FIRED emission per active seed during context build
- `tests/agents/test_seed_valley_injection.py` — Tightened 22-3 wrapper span filter from broad "seed" match to exact "narrator.seed_context" to prevent collision with new per-seed spans

**Tests:** 44/44 passing (GREEN) — 20 story tests + 24 regression tests
**Branch:** feat/22-4-seed-trope-otel (pushed)

**Handoff:** To Radar for verify phase

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 2 high, 1 medium | Duplicated test fixtures across dirs; extract lambda patterns |
| simplify-quality | clean | No findings |
| simplify-efficiency | 1 high, 1 medium, 1 low | Same fixture dup; extractor helper; span pass block |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 — duplicated test fixtures across `tests/agents/` and `tests/telemetry/` (intentionally independent per-directory scope with different defaults; coupling would create cross-directory fragility)
**Noted:** 2 — extract lambda pattern matches codebase convention (trope.py sibling); Span.open+pass is standard OTEL emission pattern throughout codebase
**Reverted:** 0

**Overall:** simplify: clean (no changes applied — all findings are either codebase-consistent patterns or intentional per-directory test isolation)

**Quality Checks:** All passing (ruff clean, 44/44 tests green)
**Handoff:** To Colonel Potter for code review

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

All four ACs verified against the implementation:

- **AC1 (Span Coverage):** SPAN_SEED_FIRED and SPAN_SEED_PROMOTED defined in `seed.py`; SPAN_SEED_EXPIRED confirmed still present from 22-3. All four constants exported in `__all__`.
- **AC2 (GM Panel Routing):** DRAWN, EXPIRED, FIRED migrated to SPAN_ROUTES with `component="seeds"`, `event_type="state_transition"`, and per-span extractors following the trope.py sibling pattern. PROMOTED in FLAT_ONLY_SPANS (no call site — appropriate).
- **AC3 (Call-Site Verification):** SPAN_SEED_FIRED wired in `build_seed_context_block` — one span per active seed, none for ghosts. Existing DRAWN/EXPIRED call sites in `seed_tick.py` untouched; regression tests confirm they still fire. PROMOTED scaffolded, deferred to 22-5.
- **AC4 (No Silent Fallbacks):** Routing completeness test passes. Tests verify span emission per seed with attribute assertions. No span definitions left unrouted.

Dev's test filter tightening (22-3 `test_seed_valley_injection.py`) is a necessary consequence of adding inner per-seed spans — logged as deviation with clear rationale. No architectural concerns.

**Decision:** Proceed to verify

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design.

### Dev (implementation)
- **Improvement** (non-blocking): Tightened 22-3 test span filter from broad `"seed" in name` to exact `narrator.seed_context` match. The broad filter collided with 22-4's new `seed.fired` per-seed spans (inner spans close before outer, so `seed_spans[0]` was the wrong span type). Affects `tests/agents/test_seed_valley_injection.py` (two tests updated). *Found by Dev during implementation.*

### Architect (spec-check)
- No upstream findings during spec-check.

### TEA (test verification)
- No upstream findings during test verification.

### Reviewer
- **Improvement** (non-blocking): An orchestrator-level wiring test asserting SPAN_SEED_FIRED through the full build_narrator_prompt path would strengthen coverage. Currently proven at the builder level only; implicit wiring coverage exists through 22-3 orchestrator tests. Affects `tests/agents/test_seed_valley_injection.py` or a new integration test. *Found by Reviewer during code review.*

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | No mechanical issues — lint clean, 44/44 tests green, working tree clean | N/A |
| 2 | reviewer-security | Yes | clean | No security concerns — no user input paths, no deserialization, no file I/O in changed code | N/A |
| 3 | reviewer-edge-hunter | Yes | findings | 8 findings (1 high, 5 medium, 2 low) | 1 noted, 7 dismissed |
| 4 | reviewer-silent-failure-hunter | Yes | findings | 3 findings (1 high, 1 medium, 1 low) | All dismissed |
| 5 | reviewer-rule-checker | Yes | findings | 4 violations across 19 rules | 1 noted, 3 dismissed |

**All received:** Yes

## Reviewer Assessment

**Decision:** APPROVE
**Findings:** 6 findings from 3 review subagents; all dismissed or noted as non-blocking
**Blocking Issues:** None

**Summary:**
- Implementation follows established telemetry/spans patterns (trope.py sibling)
- All 4 ACs satisfied; SPAN_SEED_PROMOTED scaffold mandated by AC and routing completeness infrastructure
- Extractor lambda pattern matches codebase convention; changing to sentinels would be inconsistent
- Span-before-render ordering is safe — `_render_active` is a pure string formatter on validated Pydantic models
- Test filter tightening in 22-3 tests is correct and necessary
- 44/44 tests green, lint clean, spec-check aligned
- [SEC] No security concerns — changed code processes only internal domain objects (SeedState, SeedGhost, SeedTrope), no user input, no deserialization, no file I/O, no network calls

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **SPAN_SEED_FIRED tested at build_seed_context_block, not orchestrator**
  - Spec source: context-story-22-4.md, Architecture Overview
  - Spec text: "SPAN_SEED_FIRED — Emit when a seed is surfaced to the narrator's attention (likely during VALLEY-zone context build, but exact seam TBD by Dev)"
  - Implementation: Tests drive `build_seed_context_block` directly instead of the full orchestrator prompt build path
  - Rationale: The orchestrator-level seed span from 22-3 (tested in test_seed_valley_injection.py) already covers the aggregate injection signal. SPAN_SEED_FIRED is per-seed granularity — testing at the builder function is sufficient and avoids async orchestrator setup overhead. If Dev wires the span at the orchestrator level instead, the test call site can be adjusted in GREEN.
  - Severity: minor
  - Forward impact: Dev may need to adjust the test call site if the span fires from the orchestrator rather than the builder

### Dev (implementation)
- **Tightened 22-3 test span filter to avoid collision with per-seed spans**
  - Spec source: tests/agents/test_seed_valley_injection.py, test_seed_injection_fires_otel_span
  - Spec text: "We accept any span whose name contains 'seed' (case-insensitive)"
  - Implementation: Changed filter from `"seed" in s.name.lower()` to exact `s.name == "narrator.seed_context"` to avoid collision with 22-4's `seed.fired` spans
  - Rationale: OTEL inner spans close before outer spans, so `seed.fired` spans appeared before the wrapper in the finished list, causing `seed_spans[0]` to pick the wrong span type. Exact match is more robust.
  - Severity: minor
  - Forward impact: none — the wrapper span name is stable

### Architect (reconcile)
- No additional deviations found.