---
story_id: "124-2"
jira_key: "124-2"
epic: "124"
workflow: "tdd"
---
# Story 124-2: Dependency-aware flame chart — emit + render span hierarchy

## Story Details
- **ID:** 124-2
- **Jira Key:** 124-2
- **Epic:** 124
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p3

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T06:37:04Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T05:52:22Z | 2026-06-17T05:55:07Z | 2m 45s |
| red | 2026-06-17T05:55:07Z | 2026-06-17T06:11:53Z | 16m 46s |
| green | 2026-06-17T06:11:53Z | 2026-06-17T06:25:15Z | 13m 22s |
| review | 2026-06-17T06:25:15Z | 2026-06-17T06:37:04Z | 11m 49s |
| finish | 2026-06-17T06:37:04Z | - | - |

## Acceptance Criteria

- turn_complete spans carry hierarchy (parent/depth + leaf flag) sufficient to reconstruct the caller▸callee tree
- FlameChart lays spans out by depth (nested), faded containers vs solid leaves
- critical (bottleneck) span stays outlined in accent; flat-span fallback still works for older servers

## Sm Assessment

**Routing:** New work from `NEW_WORK_STATE`. Mortal selected 124-2 over the three p2 candidates. Merge gate clear at setup (0 in-progress, 0 in-review, no blocking PRs). Phased `tdd` workflow → handing to TEA (Argus Panoptes) for the RED phase.

**Why this is well-formed for RED:** the story is a contract problem with a named blocker. The existing `TurnSpan` is FLAT (`name, component, start_ms, duration_ms`) — no parent/depth/leaf — which is exactly why the shipped `FlameChart` is an honest Gantt, not a nested tree. The work is to widen that contract on both sides of the wire.

**Cross-repo coordination (server + ui) — the seam is the `turn_complete` spans payload.** This is the load-bearing fact for everyone downstream:
- **server** must EMIT hierarchy (parent id or depth, plus a leaf flag) on the `turn_complete` spans payload — the producer side of the contract.
- **ui** (`charts/FlameChart.tsx`) must RENDER by depth: nested layout, container-vs-leaf opacity layering, accent outline retained on the critical span.
- The two repos meet only at the payload shape. TEA's RED tests should pin that shape on the server side AND assert the UI degrades to the flat Gantt when hierarchy is absent (AC3 backward-compat — "flat-span fallback still works for older servers"). That fallback is a **No Silent Fallbacks** nuance: absent hierarchy must render the honest Gantt, not a broken/empty tree — make the absence explicit and tested.

**Scope guardrails for TEA/Dev:**
- This is observability plumbing (Inspector GM panel) — a Keith/dev tool, not a player-facing surface. Do not reach for player-UI framing.
- AC3 backward-compat is non-negotiable: a server that emits no hierarchy must still produce a valid flat chart. Test both the nested path and the flat fallback.
- Per the OTEL Observability Principle and "Every Test Suite Needs a Wiring Test": the RED suite must include an integration assertion that the hierarchy fields actually ride the real `turn_complete` payload end-to-end — not just unit tests on the projection in isolation.

**Risk:** medium. The contract spans a process boundary (server emit → UI render) and must stay backward-compatible. The risk is over-fitting the payload to the current span set; TEA should pin the *shape* (parent/depth + leaf), not specific span names.

**No upstream blockers.** Branches `feat/124-2-dependency-aware-flame-chart` cut in server and ui off develop. Verdict: **proceed to RED.**

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The only per-turn span source today is the flat `PhaseTimings` map (`dict[str, int]`, `sidequest/telemetry/phase_timing.py`) → flat `phase_spans` in `validator.py` (~:510-520). It has **no parent/child**. To honestly emit a multi-level caller▸callee tree (AC1), Dev needs a real hierarchy source — the natural one is the OTEL span parent/child tree (every span flowing through `WatcherSpanProcessor.on_end` in `server/watcher.py` carries `span.parent`/trace context, currently **not** aggregated per-turn). Epic-124's guardrail "No fabricated data — only real telemetry fields" forbids a hand-authored fake nesting. This is an Architect/Dev sourcing decision. Affects `sidequest-server/sidequest/telemetry/validator.py` (the `phase_spans` builder) and likely `turn_record.py`/`phase_timing.py` (needs a hierarchy-carrying input). My server tests pin the OUTPUT contract (depth/leaf present + well-formed tree) without dictating the source, so a shallow-but-honest tree (root + phase leaves) OR a real OTEL-sourced tree both satisfy them. *Found by TEA during test design.*
- **Gap** (non-blocking): `TurnSpan` (`sidequest-ui/src/types/watcher.ts:40`) needs optional `depth?: number` + `leaf?: boolean` added (optional for older-server back-compat). `FlameChart.tsx` must read them with `??` / `=== undefined`, **never `||`**, so a legitimate `depth: 0` / `leaf: false` is not defaulted away (the TS lang-review #4 `||`-vs-`??` trap — a `leaf: false` container collapsing to a leaf would silently defeat AC2). `TimelineTab` already forwards `fields.spans` verbatim, so no TimelineTab change is needed for the data to flow. Affects `sidequest-ui/src/types/watcher.ts` + `charts/FlameChart.tsx`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): This ships a 2-level hierarchy (turn-root container → pipeline-phase leaves). Deeper, real caller▸callee nesting needs a per-turn hierarchy source — aggregating the OTEL span parent/child tree (`span.parent` via `WatcherSpanProcessor.on_end`, `server/watcher.py`) into the turn record. The wire contract (`depth`/`leaf`) already supports arbitrary depth and the UI indent renders any depth, so this is a server-side **sourcing** follow-up only — no contract change. Builds directly on TEA's hierarchy-source Question. Affects `sidequest-server/sidequest/telemetry/validator.py` + `turn_record.py`/`server/watcher.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Harden the turn-root duration to guarantee containment and remove the No-Silent-Fallbacks `or`-pattern: replace `int(record.total_duration_ms) or running` with `max(int(record.total_duration_ms), running)` (validator.py:543). One line resolves the total=0 silent fallback, the negative-clock case, and the `total < sum(phases)` containment overflow. Low production impact (production sets `total_duration_ms > 0`), so deferred — but recommended next touch. Affects `sidequest-server/sidequest/telemetry/validator.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Make the FlameChart honor its "right edge stays at the true end time" comment for sub-INDENT-width phases — `const bx = Math.min(x(s.start_ms||0)+indent, bEnd)` (FlameChart.tsx:57-59) — so short depth-1 phases don't render ~14px past their nominal end. Cosmetic on a dev panel; deferred. Affects `sidequest-ui/src/components/Dashboard/charts/FlameChart.tsx`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Depth-layout encoding left to Dev/UX — assert geometry-change, not band-vs-indent**
  - Spec source: context-story-124-2.md, AC2 / Overview
  - Spec text: "FlameChart lays spans out by depth (nested), faded containers vs solid leaves"
  - Implementation: the UI test `encodes span depth in the rendered geometry` asserts only that depth *changes* the rendered geometry (a nested span set vs an all-depth-0 set must differ), not a specific flamegraph-band-vs-indented-row encoding
  - Rationale: the spec is ambiguous between depth-bands (y by depth) and indented rows; pinning one would false-fail a correct alternative. The opacity-layering, accent, and wiring tests pin the unambiguous parts.
  - Severity: minor
  - Forward impact: Reviewer should confirm the chosen encoding matches the Tufte baseline (PR slabgorb-org/sidequest-ui#398)
- **Server tests pin the output contract only — no multi-level-tree assertion**
  - Spec source: context-story-124-2.md, AC1
  - Spec text: "turn_complete spans carry hierarchy (parent/depth + leaf flag) sufficient to reconstruct the caller▸callee tree"
  - Implementation: server tests assert depth/leaf present+typed, rooted (min depth 0), contiguous-depth, and container⇒deeper-level — but do NOT assert that ≥2 depth levels exist
  - Rationale: the only per-turn span source today (flat `PhaseTimings`) honestly has one level; asserting multi-level would force fabrication, which epic-124 forbids. Multi-level rendering is covered UI-side with synthetic depth/leaf spans. See the TEA Delivery Finding on the hierarchy source.
  - Severity: minor
  - Forward impact: once Dev wires a real hierarchy-carrying input (e.g. the OTEL span tree), add a follow-up server test asserting ≥2 levels

### Dev (implementation)
- **Updated an existing contract test to the containment model**
  - Spec source: story scope (124-2 AC1) + TEA RED suite
  - Spec text: "turn_complete spans carry hierarchy ... sufficient to reconstruct the caller▸callee tree"
  - Implementation: modified the pre-existing `test_turn_complete_carries_spans_array_for_timeline_chart` (`tests/telemetry/test_validator_otel_dashboard_restore.py`), which pinned the OLD flat-sequential contract (exact phase-name list + monotonic `start_ms` across *all* spans). Adding the turn-root container changes the emitted shape, so I extended it to assert the root (depth 0 / leaf False), the phases as depth-1 leaves with monotonic `start_ms`, and root-contains-children — strengthening, not weakening (the bug-#7 "one bar per phase" intent is preserved)
  - Rationale: the containment hierarchy IS the AC; that test encoded the pre-124-2 flat contract. A deliberate, spec-driven contract change requires updating the assertion that pinned the old behavior
  - Severity: minor
  - Forward impact: none — the updated assertions co-witness the 124-2 contract alongside TEA's new tests
- **Hierarchy is a 2-level turn-root container, not deep caller▸callee**
  - Spec source: context-story-124-2.md, AC1 / Overview
  - Spec text: "spans nested caller ▸ callee (containment = depth)"
  - Implementation: emitted a depth-0 `turn` root containing the depth-1 pipeline phases — honest containment (the turn wall-clock contains its phases), but shallow: the phases are siblings, not caller▸callee of each other, because the only per-turn span source (flat `PhaseTimings`) carries no parent links
  - Rationale: deeper nesting needs a real hierarchy source (the per-turn OTEL span tree) that doesn't exist yet; fabricating sub-phase parents would violate epic-124's "real telemetry only" guardrail and SOUL "No Stubbing". TEA scoped the server tests to the output contract for exactly this reason. Delivers real, honest 2-level nesting now
  - Severity: minor
  - Forward impact: a follow-up can source the OTEL span tree for multi-level nesting; the wire contract (depth/leaf) already supports arbitrary depth (see Dev Delivery Finding)
- **Depth encoded as left-inset indent (one row per span), not flamegraph bands**
  - Spec source: context-story-124-2.md, AC2; TEA deviation "Depth-layout encoding left to Dev/UX"
  - Spec text: "FlameChart lays spans out by depth (nested), faded containers vs solid leaves"
  - Implementation: kept one readable row per span (y by index) and inset each bar's LEFT edge by `depth * INDENT`; the bar's right edge stays at the true end time so durations remain honest. Containers (`leaf === false`) are faded via opacity (0.34 vs 0.82)
  - Rationale: indented rows keep the left-gutter labels readable (flamegraph bands collapse siblings onto one row and force in-bar labels), preserve the flat fallback byte-identically, and are a minimal diff. TEA explicitly left the encoding to Dev/UX
  - Severity: minor
  - Forward impact: Reviewer/UX should confirm the indent reads as nesting against the Tufte baseline (PR slabgorb-org/sidequest-ui#398); a band layout remains a possible future refinement

### Reviewer (audit)
- TEA "Depth-layout encoding left to Dev/UX" → ✓ ACCEPTED: encoding-agnostic geometry assertion is sound; pins behavior without over-constraining.
- TEA "Server tests pin the output contract only — no multi-level-tree assertion" → ✓ ACCEPTED: forcing a multi-level tree from flat `PhaseTimings` would be fabrication; correct call, consistent with epic-124's guardrail.
- Dev "Updated an existing contract test to the containment model" → ✓ ACCEPTED: the change *strengthened* the bug-#7 test (root + leaf + containment assertions) rather than weakening it; the old flat-sequential contract was legitimately superseded by the AC1 containment model.
- Dev "Hierarchy is a 2-level turn-root container, not deep caller▸callee" → ✓ ACCEPTED: honest containment with no fabrication; deeper nesting correctly deferred (logged Delivery Finding) since no real per-turn parent-link source exists today.
- Dev "Depth encoded as left-inset indent (one row per span)" → ✓ ACCEPTED **with caveat**: the encoding is fine and TEA-sanctioned, but its stated invariant ("the bar's right edge stays at the true end time") is imprecise for sub-INDENT-width phases (see Reviewer observation #6 / Delivery Finding). Accepted because the deviation itself is valid; the caveat is recorded as a non-blocking follow-up, not a reversal.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — cross-repo behavior change with three testable ACs.

**Test Files:**
- `sidequest-server/tests/telemetry/test_validator_span_hierarchy.py` — pins the `turn_complete` spans **output contract** (depth+leaf present/typed, rooted, contiguous-depth, well-formed). Drives the real `Validator._validate` → `publish_event` emission path (the same wiring boundary `test_validator_phase_timing.py` guards), so it IS the server-side wiring test.
- `sidequest-ui/src/components/Dashboard/__tests__/FlameChartHierarchy.test.tsx` — pins the FlameChart render (container-vs-leaf opacity, depth-affects-geometry, accent on critical, flat-Gantt fallback) plus an **end-to-end wiring test** through the real `TimelineTab` (proves `TurnCompleteFields.spans` → TimelineTab pass-through → FlameChart consumes depth/leaf).

**Tests Written:** 9 tests across 3 ACs (4 server, 5 UI).
**Status:** RED — verified by The Hundred Eyes (testing-runner, RUN_ID 124-2-tea-red).
- Server: 3 fail for the right reason (`depth=None`), 1 back-compat guard passes.
- UI: 3 fail for the right reason (opacity 0.82 ≮ 0.82; nested vs flat geometry identical; wiring shows no layering), 2 guards pass (accent outline; flat fallback).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Python #3 — typed boundary | `test_turn_complete_spans_carry_depth_and_leaf` (asserts `int` depth, `bool` leaf, rejects `bool`-as-int) | failing |
| Python #6 — test quality | self-check below | pass |
| TS #4 — `\|\|` vs `??` (0/false not defaulted) | `fades container spans…` + wiring test (a `leaf: false` container must not collapse to a leaf) | failing |
| TS #8 — test quality (no `as any`) | spans typed via `HierarchySpan = TurnSpan & {depth?;leaf?}` extension, zero `as any` | pass |
| No Silent Fallbacks (CLAUDE.md/SOUL) | `falls back to a flat one-row-per-span Gantt…` (absent hierarchy ⇒ honest flat chart, not empty/broken) | pass (guard) |
| Every Test Suite Needs a Wiring Test | server: real `_validate` emit path; UI: end-to-end through real `TimelineTab` | failing |

**Rules checked:** 6 of the applicable Python/TS lang-review rules have test coverage (the rest — async, resource leaks, deserialization, etc. — are N/A to a telemetry-field + SVG-render change).
**Self-check:** 0 vacuous assertions. Every test asserts a specific value/relationship (opacity `<`, geometry `≠`, typed `depth`/`leaf`, `min(depth)==0`, contiguous depths, accent stroke equality). No `assert True`, no `as any`, no truthy-only checks.

**Handoff:** To Hephaestus the Smith (Dev) for GREEN. Two upstream findings recorded (hierarchy-source decision; `TurnSpan` field + `??`-not-`||` read) — read them before implementing; the hierarchy source is a real design choice, not a free-form fill-in.

## Dev Assessment

**Implementation Complete:** Yes

**Hierarchy-source decision (the open question TEA flagged):** I shipped the honest 2-level containment available today — a depth-0 `turn` root (the whole turn) containing the depth-1 pipeline phases (leaf work). No fabrication: the root's duration is the real turn wall-clock, the children are the real measured phases. Deeper caller▸callee nesting (sourcing the per-turn OTEL span tree) is logged as a Dev Delivery Finding for a follow-up — the wire contract (`depth`/`leaf`) already supports arbitrary depth.

**Files Changed:**
- `sidequest-server/sidequest/telemetry/validator.py` — `_validate` now stamps `depth: 1, leaf: True` on each phase span and inserts a `depth: 0, leaf: False` `turn` root container (degraded turns: single `agent_llm` depth-0 leaf root).
- `sidequest-server/tests/telemetry/test_validator_otel_dashboard_restore.py` — extended the bug-#7 timeline test to the containment model (see deviation #1).
- `sidequest-ui/src/types/watcher.ts` — `TurnSpan` gains optional `depth?: number`, `leaf?: boolean`.
- `sidequest-ui/src/components/Dashboard/charts/FlameChart.tsx` — bars left-inset by `depth * INDENT` (right edge stays honest), containers (`leaf === false`) faded, critical = longest LEAF; flat path (no depth) renders byte-identically. Reads `depth`/`leaf` with `?? 0` / `=== false`, never `||`.

**Tests:** 50/50 passing GREEN (verified by The Automatons, RUN_ID 124-2-dev-green).
- Server: `test_validator_span_hierarchy` 4/4, `test_validator_otel_dashboard_restore` 5/5, `test_validator_phase_timing` 2/2, `test_validator_pipeline` 17/17.
- UI: `FlameChartHierarchy` 5/5, `TufteCharts` 6/6 (flat path unchanged), `TimingTab-phase-breakdown` 5/5, `TimelineTab-session-divider` 6/6.
- Lint/types clean: server `ruff check` + `ruff format --check` pass; UI `tsc --noEmit` exit 0, `eslint` clean.

**Self-review (judgment checks):**
- Wired end-to-end: server `validator._validate` (production emit path) → `TurnCompleteFields.spans` → `TimelineTab` pass-through → `FlameChart`. The UI wiring test mounts the real `TimelineTab`; no half-wired surface.
- Follows patterns: additive payload fields (older dashboards ignore them), same `publish_event` emit, same SVG render structure.
- ACs met: AC1 (depth+leaf, reconstructable tree) ✓; AC2 (nested by depth + faded containers vs solid leaves) ✓; AC3 (slowest leaf accent-outlined + flat fallback for older servers) ✓.
- Error handling / No Silent Fallbacks: absent hierarchy renders the honest flat Gantt (tested), not an empty/broken tree; root duration falls back to summed phase time only when total is unrecorded — never invented.

**Branches (pushed):** `feat/124-2-dependency-aware-flame-chart` on both `sidequest-server` and `sidequest-ui` (base `develop`).

**Handoff:** To Argus Panoptes (TEA) for the verify phase (simplify + quality-pass), then Hermes Psychopompos (Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | GREEN 50/50; 4 structural notes; format-drift | 0 confirmed-blocking; 3 noted (deferred); 1 **corrected** (its claim "degraded span omits depth/leaf" is FALSE — validator.py degraded branch has `depth:0, leaf:True`, verified, degraded test green) |
| 2 | reviewer-edge-hunter | Yes | findings | 10 | 2 confirmed→deferred (root containment clamp; indent honest-edge); 8 dismissed/noted with rationale (won't occur on real data / pre-existing / sub-pixel cosmetic) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 1 | 1 confirmed→deferred (total=0 silent fallback; rule-match recorded, Low production impact) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — lang-review rules assessed by Reviewer (see Rule Compliance + [RULE]) |

**All received:** Yes (3 ran with findings, 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (all deferred non-blocking), 8 dismissed/noted with rationale, 1 subagent claim corrected

### Rule Compliance

Enumerated against the Python + TypeScript lang-review checklists and SOUL/CLAUDE rules, for every changed symbol:

- **Python #3 (typed boundaries):** the new span dicts carry `depth: int`, `leaf: bool` (literals). The validator emit is internal; `_validate` already typed. COMPLIANT.
- **Python #4 / #6 (logging / test quality):** no new logging paths; new tests have meaningful assertions (typed `depth`/`leaf`, `min(depth)==0`, contiguous depths, container⇒deeper), zero vacuous. The `isinstance(d, int) and not isinstance(d, bool)` correctly rejects Python's bool-is-int subclass trap. COMPLIANT.
- **TS #4 (`||` vs `??`):** `s.depth ?? 0` (FlameChart.tsx:57) and `s.leaf === false` (44, 56) — both correct; a real `depth:0`/`leaf:false` is NOT defaulted away. The pre-existing `s.start_ms || 0` is unchanged and safe (0 start). COMPLIANT.
- **TS #8 (no `as any` in tests):** the test uses `type HierarchySpan = TurnSpan & {depth?;leaf?}` — explicit typed extension, zero `as any`. COMPLIANT.
- **No Silent Fallbacks (CLAUDE.md `<critical>`):** `int(record.total_duration_ms) or running` (validator.py:543) is a `or`-style fallback for total=0. **One rule-match finding [RULE]/[SEC]** — see Devil's Advocate + findings; deferred (Low production impact: production always sets `total_duration_ms = timings.total_ms` > 0; raw total co-emitted on the same payload, so nothing is masked). Otherwise no swallowed exceptions, no empty catches.
- **No Stubbing / Don't fabricate (epic-124 "real telemetry only"):** the turn-root duration is the real wall-clock (or honest phase-sum), children are real measured phases. No fabricated nesting. COMPLIANT.
- **Wiring (Every Test Suite Needs a Wiring Test):** server test drives real `Validator._validate`→`publish_event`; UI test mounts real `TimelineTab`. COMPLIANT.

### Observations

1. **[VERIFIED] Flat fallback is byte-identical to the prior render** — evidence: FlameChart.tsx:57 `indent = (undefined ?? 0)*14 = 0`; `isContainer = (undefined === false) = false` → `LEAF_OPACITY 0.82` (== prior hardcoded 0.82); crit guard `undefined !== false = true` → longest-overall (== prior). Confirmed by edge-hunter #5 and the passing `TufteCharts` + flat-fallback tests. Complies with AC3 + No-Silent-Fallbacks (honest flat chart on absent hierarchy).
2. **[VERIFIED] No consumer double-counts the turn-root** — evidence: grep of both repos found the only `turn_complete` `spans` consumer is `TimelineTab.tsx:19-21` (pass-through to FlameChart); no forensic/persistence/p95 path sums the spans array (`validator.py:580` `_unaccounted_ms` uses `phase_durations_ms`, not the spans list). The prepended root is safe.
3. **[VERIFIED] Degraded path carries hierarchy** — evidence: validator.py degraded branch emits `depth:0, leaf:True` on the `agent_llm` span (verified in source; `test_turn_complete_falls_back_to_agent_llm_when_no_phases` green). **This corrects reviewer-preflight's incorrect claim** that the fields are omitted.
4. **[SEC]/[RULE] [LOW, deferred] No-Silent-Fallbacks: `int(record.total_duration_ms) or running`** at validator.py:543 — when total=0 the root silently uses the phase-sum. Production never hits it (`timings.total_ms` > 0 at websocket_session_handler.py:2660/2787) and the raw total is co-emitted, so nothing is masked. Recommended fast-follow: `max(int(record.total_duration_ms), running)` — removes the `or`-fallback AND structurally guarantees containment (resolves #5). Non-blocking.
5. **[EDGE] [LOW–MEDIUM, deferred] Root containment not guaranteed when `total_duration_ms < sum(phases)`** at validator.py:534/543 — root bar shorter than its tiled children (children overflow the container on the chart). Rare: pipeline phases are non-overlapping `with` blocks so `sum(phases) ≤ total` normally; only the `record_phase()` MP-barrier path (pre-`_start` time) can invert it. Same one-line `max()` fix as #4. Non-blocking.
6. **[EDGE] [LOW, deferred] Indent can push `bx` past `bEnd` for sub-INDENT-width phases** at FlameChart.tsx:57-60 — short depth-1 phases (broadcast/dispatch_post etc.) render as 2px ticks ~14px right of their nominal end, so the comment's "right edge stays at the true end time" is imprecise for these. Sub-pixel-duration phases were already 2px-clamped pre-diff, so the visual delta is a 14px tick shift consistent with sibling nesting — cosmetic. Optional fix: `const bx = Math.min(x(s.start_ms||0)+indent, bEnd)`. Non-blocking.
7. **[TEST] [VERIFIED] Test quality is sound** — the updated dashboard-restore test was *strengthened* (root + leaf + containment assertions), not weakened; new tests assert specific relationships, no vacuous checks, real wiring boundaries. The depth-geometry UI test is intentionally encoding-agnostic (documented TEA deviation) — acceptable.
8. **[DOC] [VERIFIED] Comments accurate** except the one "right edge stays at true end" imprecision noted in #6. The validator and watcher.ts doc comments correctly describe additive fields, containment, and the `??`/`=== false` contract.
9. **[TYPE] [VERIFIED] TurnSpan extension is sound** — `depth?: number`, `leaf?: boolean` optional for back-compat; no stringly-typed API; server emits Python `int`/`bool` → JSON `number`/`bool`, UI reads `number`/`=== false`. Edge-hunter confirmed no live encoding mismatch (`json.dumps` distinguishes bool from int).
10. **[SIMPLE] [VERIFIED] Minimal, no over-engineering** — three named constants extracted (INDENT/CONTAINER_OPACITY/LEAF_OPACITY), clean `if phase_spans / else`, no dead code, no speculative depth>1 machinery. Scope matches the 2-level hierarchy shipped.
11. **[SILENT] No swallowed errors introduced** beyond the documented total=0 `or`-fallback (#4). The `else` degraded branch and the `??`/`===` reads are explicit and documented.

### Devil's Advocate

Suppose this code is broken. The most dangerous input is a turn where the recorded wall-clock disagrees with the measured phases. If `total_duration_ms` is genuinely smaller than the phase sum — which the codebase already anticipates (the `_unaccounted_ms = max(0, total - sum)` clamp exists precisely because that subtraction can go negative) — then the emitted "turn" root is *shorter* than the children it claims to contain. On the flame chart, depth-1 phase bars would extend past the right edge of their depth-0 container, visually contradicting the entire premise of the feature (containment = depth). A career GM glancing at the panel would see children escaping their parent and reasonably conclude the telemetry is lying. That is the sharpest real risk, and it is exactly what AC2 is supposed to prevent. It is mitigated only by the fact that pipeline phases are recorded as non-overlapping `with` blocks (so the sum rarely exceeds the total) and that this is a dev-only surface — but `record_phase()` for MP-barrier waits records time from *before* the timer started, which can invert the relationship on multiplayer turns. A confused user is most likely to be misled by the short phases: on every real turn, the sub-second phases (state_apply, persistence, broadcast, dispatch_post) are sub-pixel wide, and the 14px depth indent shifts their 2px ticks rightward of their true time position — so the "honest right edge" the comment promises is quietly false for roughly half the bars on a typical turn. A stressed filesystem or a degraded turn produces `total_duration_ms = 0`; the `or running` fallback then silently swaps in the phase-sum, and although the raw zero is co-emitted elsewhere, a reader trusting the root bar's width is reading an invented number — the exact "no fabricated data" line epic-124 draws. None of these corrupt data, escalate privilege, or crash; they degrade the *honesty* of a dev observability chart at the margins. The redeeming facts: production always records a real positive wall-clock, the flat fallback is byte-identical (so older servers are untouched), no consumer double-counts the root, and the dominant LLM phases — the ones a GM actually cares about — render correctly inset and faded. The flaws are real but cosmetic and edge-bound; the two one-line clamps (`max()` on the root, `Math.min()` on `bx`) would close them and are worth a fast-follow.

## Reviewer Assessment

**Verdict:** APPROVED

**Subagent dispatch (3 ran, 6 disabled):** `[SEC]` total=0 silent-fallback (confirmed→deferred, rule-match recorded); `[EDGE]` root-containment + indent-honest-edge (confirmed→deferred) and 8 won't-occur/cosmetic paths (dismissed with rationale); `[SILENT]` no swallowed errors beyond the documented total=0 `or`; `[TEST]` assertions meaningful, dashboard-restore test strengthened not weakened; `[DOC]` comments accurate except the one "right edge" imprecision (deferred); `[TYPE]` TurnSpan optional `depth?`/`leaf?` sound, no encoding mismatch; `[SIMPLE]` minimal diff, constants extracted, no dead code; `[RULE]` lang-review Python #3/#4/#6 + TS #4/#8 all compliant, one No-Silent-Fallbacks match deferred (Low impact).

**Why APPROVED (not blocked):** every confirmed finding is Medium/Low on the Keith/dev-only Inspector panel — none reach the Critical/High bar the severity rubric requires to block. The feature correctly delivers AC1 (depth+leaf, rooted well-formed tree), AC2 (nested-by-depth + faded containers vs solid leaves), and AC3 (slowest-leaf accent + byte-identical flat fallback for older servers) for production inputs. The No-Silent-Fallbacks rule-match is **confirmed and deferred** (not dismissed): production never hits the total=0 branch (`timings.total_ms` > 0) and the raw total is co-emitted, so nothing is masked.

**Data flow traced:** player turn → `PhaseTimings` (server-internal phase literals, no player input) → `TurnRecord` → `Validator._validate` stamps `depth`/`leaf` + prepends `turn` root → `publish_event("turn_complete", {spans})` → `/ws/watcher` → `TimelineTab.tsx:19-21` pass-through → `FlameChart`. Safe: phase names are server constants (no injection), React escapes `{s.name}` in `<title>`/`<text>` (no XSS), depth/leaf carry only structural metadata (no PII/secrets).

**Pattern observed:** additive wire-contract evolution — new optional fields ignored by older consumers, flat fallback byte-identical — at `validator.py:526-562` / `FlameChart.tsx:57-74` / `watcher.ts:45-55`. Honest containment with no fabricated nesting (epic-124 guardrail upheld).

**Error handling:** absent hierarchy → honest flat Gantt (tested, not empty/broken); degraded turn → single `agent_llm` depth-0 leaf root carrying `depth:0, leaf:True` (verified — corrects preflight's claim of omission); root duration falls back to the honest phase-sum only, never invented.

**Deferred fast-follows (non-blocking):** (1) `max(int(total_duration_ms), running)` on the root duration — resolves the rule-match + containment + negative cases in one line; (2) `Math.min(bx, bEnd)` so short indented phases honor the documented honest-right-edge. Both recorded in Delivery Findings.

**Handoff:** To Themis the Just (SM) for finish-story.