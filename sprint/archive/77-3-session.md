---
story_id: "77-3"
jira_key: "77-3"
epic: "77"
workflow: "tdd"
---
# Story 77-3: Promote quest_anchors to first-class WorldStatePatch field + wire to orbital course

## Story Details
- **ID:** 77-3
- **Epic:** 77 — Quest & Stakes Substrate
- **Workflow:** tdd
- **Repos:** sidequest-server
- **Branch:** feat/77-3-promote-quest-anchors-worldstatepatch
- **Stack Parent:** none

## Specification

### Background

Story 77-1 (complete) seeds quest_anchors at character creation from PC drive/calling.
Story 77-2 (complete) adds narrator tools (record_quest + set_stakes) to bind narrator-controlled state.

This story **promotes quest_anchors to first-class** — adds it as a dedicated field in the WorldStatePatch
data structure (currently world state updates flow through generic `world_data_updates` dict). Quest anchors
are load-bearing for ADR-137 §Implementation: the orbital course (orbital/course.py:157) consumes quest_anchors
to schedule quest-driven story beats. Until this story, quest_anchors are embedded in world_data_updates and
require dict unpacking on every read. Promoting them to a field makes the dependency explicit and the wiring
clear.

### Acceptance Criteria

1. **WorldStatePatch field:**
   - Add `quest_anchors: list[str] | None = None` field to WorldStatePatch pydantic model
   - Update to_dict/from_dict if those exist to round-trip the field
   - OTEL: emit `world.patch.quest_anchors_present` span attribute (boolean) on every patch that touches quest_anchors

2. **Orbital course wiring:**
   - Update `orbital/course.py:157` consumer to read from `patch.quest_anchors` instead of unpacking from `world_data_updates`
   - If `patch.quest_anchors is None`, default to `[]` (no quest anchors, no quest beats scheduled)
   - OTEL: emit `orbital.course.quest_anchors_consumed` span with `anchor_count=N` on each course update that reads quest_anchors

3. **Backward-compatibility (load path):**
   - When loading a save that has quest_anchors in legacy `world_data_updates["quest_anchors"]`, migrate to the new field on first load
   - OTEL: emit `world.patch.quest_anchors_migrated` span with `migrated_count=N` when legacy data is found and moved
   - No test save contains the legacy pattern yet (stories 77-1, 77-2 were born post-promotion); the migration path must be validated by test

4. **No silent fallbacks:**
   - If quest_anchors field is present but malformed (not a list of strings), raise loudly
   - If orbital course read fails on malformed data, raise loudly
   - Never silently skip quest_anchors or default to empty list without OTEL coverage

5. **Tests:**
   - Unit tests: WorldStatePatch field rounds trip correctly; legacy `world_data_updates["quest_anchors"]` migrates on load
   - Integration test: orbital course reads promoted quest_anchors and schedules beats (wiring test per CLAUDE.md §Every Test Suite)
   - OTEL test: all three spans fire with correct attributes

### Design Notes

- **Why promote?** The orbital course is a committed consumer of quest_anchors; storing them in generic `world_data_updates` obscures the dependency. Promoting to a field makes the API contract explicit.
- **ADR-137 §Implementation:** quest_anchors live in `Character.quest_log.quest_anchors` (seeded at creation by 77-1, populated by narrator 77-2 tools). On world-state patches, they must flow to the orbital scheduler. This story makes that flow explicit in the patch structure.
- **Load safety:** Ancient saves (pre-77-1) cannot have quest_anchors in any form; saves from 77-1/77-2 may have them embedded in world_data_updates if the story-2 narrator tool update was never called. The migration path handles the 77-1 → 77-3 case.

## Workflow Tracking

**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-04T01:08:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T01:08:00Z | - | - |

## Delivery Findings

No upstream findings at setup phase.

<!-- Agents: append findings below. Do not edit other agents' entries. -->

### TEA (test design)

- **Question — RESOLVED** (non-blocking): Where should `orbital.course.quest_anchors_consumed` be emitted? SM's final spec said "extend `emit_course_compute`, fire at both call sites, exercise the narration_apply path in the test." Dev implemented it as `emit_quest_anchors_consumed(anchor_count=len(quest_anchors))` INSIDE `compute_courses` (`sidequest/orbital/course.py:161`) — which fires for BOTH call sites automatically (orchestrator.py:2408 + narration_apply.py:1972), satisfying the "both sites covered" intent. My AC5 test now drives the REAL narration_apply path (`_apply_course_sidecar`, `test_narration_apply_course_path_emits_quest_anchors_consumed_span`) and passes against this placement. **Note for Reviewer/verify:** placement differs from the literal "extend emit_course_compute" wording but meets the coverage goal; confirm acceptable. *Found by TEA during test design; resolved at GREEN.*
- **Gap** (non-blocking): `narration_apply.py:1972`'s `compute_courses` call currently emits NO course-compute span (only `orchestrator.py:2408` does, via `emit_course_compute`). Emitting `orbital.course.quest_anchors_consumed` inside `compute_courses` closes this blind spot. Affects `sidequest/server/narration_apply.py` / `sidequest/orbital/course.py`. *Found by TEA during test design.*

### Dev (implementation)

- No upstream findings during implementation. The reconciled contract was clean and self-consistent; TEA's tests encoded it precisely. One observation for Reviewer (non-blocking, informational): `orbital.course.quest_anchors_consumed` now fires on **every** `compute_courses` call with a valid `party_at` (twice per turn in the orbital path — orchestrator prompt assembly + any narration-apply course refresh), carrying `anchor_count` even when 0 anchors. This is intentional (explicit "scheduler read N anchors" signal, never a silent skip) and matches the OTEL decision-point principle, but produces one span per read — not deduped across a turn. If span volume becomes a concern, that's a future tuning question, not a wiring gap.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **AC1 round-trip tested via model_dump/model_validate, not to_dict/from_dict**
  - Spec source: `.session/77-3-session.md`, AC1
  - Spec text: "Update to_dict/from_dict if those exist to round-trip the field"
  - Implementation: `WorldStatePatch` is pydantic v2 with no `to_dict`/`from_dict`; round-trip is asserted via `model_dump()` → `model_validate()`.
  - Rationale: Those methods do not exist on the model; pydantic serialization is the real contract (the AC says "if those exist" — they don't).
  - Severity: minor
  - Forward impact: none

- **AC2 tested as patch→snapshot dedup-append union (per Architect reconcile), not "compute_courses reads patch"**
  - Spec source: `.session/77-3-session.md`, AC2; Architect (reconcile) ruling above
  - Spec text: "Update `orbital/course.py:157` consumer to read from `patch.quest_anchors` instead of unpacking from `world_data_updates`"
  - Implementation: Tests assert `_apply_world_patch_inner` merges `patch.quest_anchors` into `snapshot.quest_anchors` as an order-preserving dedup union under an `is not None` guard; `compute_courses` keeps its pure snapshot-reading signature. No "clear" semantic — empty patch list is a no-op union (test `test_apply_world_patch_empty_list_is_noop_union`), preserving the seeded campaign spine.
  - Rationale: Ratifies Neo's correction — `world_data_updates` does not exist; union (not replace) prevents a world-patch clobbering the ADR-137 quest spine.
  - Severity: major
  - Forward impact: none

- **AC3 migration NOT tested — dropped per Architect ruling**
  - Spec source: `.session/77-3-session.md`, AC3; Architect (reconcile) ruling above
  - Spec text: "migrate quest_anchors from legacy `world_data_updates[\"quest_anchors\"]` … emit `world.patch.quest_anchors_migrated`"
  - Implementation: No migration test written. Load-safety is instead covered by `test_world_patch_lacking_quest_anchors_key_loads_as_default` (a payload with no key loads as the None default) — the only real "legacy" case.
  - Rationale: The legacy source field never existed; a migration test would force fictional production code (dead code + OTEL theater).
  - Severity: major
  - Forward impact: none — no `world.patch.quest_anchors_migrated` span exists; the absence signal is delivered by AC1's `quest_anchors_present=false`.

- **AC5 `orbital.course.quest_anchors_consumed` asserted at the compute_courses decision point, not per-call-site**
  - Spec source: `.session/77-3-session.md`, AC5; Architect ruling ("at both compute_courses call sites … or that read stays blind")
  - Spec text: "emit `orbital.course.quest_anchors_consumed` span with `anchor_count=N` on each course update that reads quest_anchors"
  - Implementation: `test_compute_courses_emits_quest_anchors_consumed_span` drives `compute_courses` directly and asserts the span fires there. This makes "both call sites" automatic and refactor-stable (the OTEL subsystem-decision-point principle) — Dev must emit INSIDE `compute_courses`, not duplicate at each caller.
  - Rationale: Emitting at the single read point covers both callers (incl. the currently-blind narration_apply read) with no duplication and survives refactors. Flagged as a non-blocking Question for Dev/Neo to confirm placement.
  - Severity: minor
  - Forward impact: none — satisfies Neo's "both reads covered" goal.

### Dev (implementation)

- No deviations from spec. Implemented exactly to the reconciled contract TEA encoded in the tests: `WorldStatePatch.quest_anchors: list[str] | None = None` (typed field + `extra="forbid"` yields AC4 loud-reject for free — no manual guard, no silent `[]`); `_apply_world_patch_inner` does an order-preserving dedup-UNION under an `is not None` guard (no replace, no clear semantic — protects the seeded campaign spine); `world.patch.quest_anchors_present` boolean added to the existing `apply_world_patch` span; `orbital.course.quest_anchors_consumed` (`anchor_count`) emitted INSIDE `compute_courses` at the single anchor-read point per TEA's resolved Question — fires for both call sites incl. the previously-blind `narration_apply.py:1972` read (verified by `test_narration_apply_course_path_emits_quest_anchors_consumed_span` driving the real `_apply_course_sidecar`). AC3 migration correctly absent (no legacy `world_data_updates` field ever existed). Reused existing span infra (`telemetry/spans/state_patch.py`, `telemetry/spans/course.py`) — no reinvention.

### Architect (reconcile)

> Ruled at interim spec-check (pulled forward 2026-06-04 at TEA's RED block); ratified
> at spec-reconcile. The story's written AC2/AC3 are built on a data structure
> (`world_data_updates`) that has **zero occurrences** in `sidequest/` — verified by
> grep at HEAD. `GameSnapshot.quest_anchors` (session.py:819) is already first-class
> and persisted; `compute_courses` (course.py:119) already reads it at both call sites.
> The single real gap is that `WorldStatePatch` (session.py:485) carries no
> `quest_anchors` field, so a narrator world-patch cannot contribute anchors.

- **AC2 source premise corrected — patch→snapshot merge, not "world_data_updates" unpack**
  - Spec source: `.session/77-3-session.md`, AC2 (and AC1)
  - Spec text: "Update `orbital/course.py:157` consumer to read from `patch.quest_anchors` instead of unpacking from `world_data_updates`"
  - Implementation: Add `quest_anchors: list[str] | None = None` to `WorldStatePatch`; round-trip via pydantic `model_dump`/`model_validate` (no `to_dict`/`from_dict` exist — the model is pydantic v2 with `extra="forbid"`). `_apply_world_patch_inner` (session.py:1345) merges `patch.quest_anchors` into `snapshot.quest_anchors` under an `is not None` guard, using **dedup-append (order-preserving union), NOT replace** — consistent with the only other two anchor writers (`quest_seed.py:85` and `record_quest.py:122/154`, both dedup-append) and preventing a world-patch from silently clobbering the seeded campaign spine (the exact ADR-137 failure mode). `compute_courses` signature is **unchanged** — it stays a pure keyword-only function reading `snapshot.quest_anchors`; threading a transient patch into a pure presentation fn with two callers would be architecturally wrong (narration_apply reads the snapshot *after* apply; orchestrator reads from context). OTEL: `world.patch.quest_anchors_present` (bool) on apply; `orbital.course.quest_anchors_consumed` (anchor_count) at **both** compute_courses call sites (orchestrator.py:2408 + narration_apply.py:1972 — the latter currently has no course-compute span, so coverage must be added there or that read stays blind).
  - Rationale: The `world_data_updates` source named in the AC never existed in code; the real, minimal, non-dead-code change is to add the missing `WorldStatePatch` field and merge it in the established apply path, leaving the already-correct snapshot→course read untouched.
  - Severity: major
  - Forward impact: none — completes the ADR-137 §Decision-3 "promote quest_anchors to first-class" goal; no sibling story assumes the fictional `world_data_updates` lane.

- **AC3 dropped — no legacy `world_data_updates["quest_anchors"]` exists to migrate**
  - Spec source: `.session/77-3-session.md`, AC3 (Backward-compatibility load path)
  - Spec text: "When loading a save that has quest_anchors in legacy `world_data_updates[\"quest_anchors\"]`, migrate to the new field on first load … emit `world.patch.quest_anchors_migrated`"
  - Implementation: AC3 is **dropped**. `world_data_updates` has zero occurrences anywhere; 77-1 (`quest_seed`) and 77-2 (`record_quest`) already write anchors to the first-class `snapshot.quest_anchors` field, so no save can carry the legacy embedding. Encoding the migration would force Dev to invent a fictional source field and a span that can only ever report "nothing migrated" — dead code + OTEL theater (violates No Stubbing and the OTEL principle, which exists to catch improvisation, not decorate non-events). Load safety is instead guaranteed by pydantic defaults (`snapshot.quest_anchors` → `[]`, `patch.quest_anchors` → `None` → no-op) and covered by a unit test asserting a save/patch lacking the key loads as the default. The "anchors absent" case is already observable on the GM panel via AC1's `world.patch.quest_anchors_present=false` — no separate migration span needed.
  - Rationale: A migration path for a field that never existed is dead code; the absence signal the OTEL principle wants is already delivered by the `quest_anchors_present` boolean.
  - Severity: major
  - Forward impact: none — AC3's premise was counterfactual; dropping it removes fictional scope, no downstream story depends on a migration span.

- **ADR-137's `quest.anchor.added` span superseded by `quest_anchors_present` + `quest_anchors_consumed` (added at reconcile)**
  - Spec source: `docs/adr/137-quest-stakes-substrate.md`, §OTEL spans (the `quest.anchor.added` row) + §Implementation Stories (the promote-story row, "+`quest.anchor.added`")
  - Spec text: "`quest.anchor.added` | an anchor is written | `anchor_id`, `quest_id`, `resolved_to_beat` (bool)"
  - Implementation: 77-3 emits `world.patch.quest_anchors_present` (bool on the apply-patch span — fires every patch, true iff anchors are carried) + `orbital.course.quest_anchors_consumed` (`anchor_count`, at the course read). `quest.anchor.added` is implemented nowhere (grep-confirmed; only a stale forward-reference comment at `telemetry/spans/state_patch.py:48`). The anchor-write event remains observable via `quest_anchors_present=true` on the carrying patch and via `record_quest`'s existing `quest.created` span (which already carries `anchor_count`); the consume event via `quest_anchors_consumed`.
  - Rationale: The story's AC-level OTEL design (present + consumed) covers ADR-137's observability intent — anchor writes and consumption are GM-panel-verifiable — at the two real decision points; a third `quest.anchor.added` span with `resolved_to_beat` would duplicate the present-signal and require beat-resolution data the apply path does not hold. Story scope (session ACs) outranks the ADR span table per the spec-authority hierarchy.
  - Severity: minor
  - Forward impact: minor — epic 77 remaining stories (live 77-4/77-5). Whoever owns anchor-write observability downstream should reuse `quest_anchors_present`/`quest_anchors_consumed` and NOT implement ADR-137's `quest.anchor.added` (it would be a redundant fourth span). ADR-137's OTEL table + story-numbering are stale vs as-built (table says "77-4 promote"; live = 77-3) — captured in the optional epic-close ADR note in the spec-reconcile verdict below.

## TEA Assessment

**Phase:** red (RED complete — handing to Dev/Agent Smith for GREEN)
**Tests Required:** Yes

**Test Files:**
- `sidequest-server/tests/game/test_world_patch_quest_anchors.py` — AC1 (field, defaults, round-trip, load-default), AC2 (apply_world_patch dedup-append union into snapshot), AC4 (malformed raises), AC5 (`world.patch.quest_anchors_present` span attr).
- `sidequest-server/tests/orbital/test_quest_anchors_course_wiring.py` — AC2/AC5 cross-subsystem wiring (patch → apply → `compute_courses` marks QUEST_OBJECTIVE) + `orbital.course.quest_anchors_consumed` span.

**Tests Written:** 15 tests covering AC1, AC2, AC4, AC5. AC3 dropped per Architect ruling (no test).
**Status:** RED confirmed — `14 failed, 1 passed in 0.08s` (direct `uv run pytest -n0`).

**RED honesty notes:**
- The 1 passing test (`test_apply_world_patch_none_quest_anchors_preserves_existing`) is a legitimate already-true invariant: a non-anchor patch must not wipe existing anchors. Non-vacuous; stays green in GREEN.
- `WorldStatePatch` has `extra="forbid"`, so any `quest_anchors=...` raises `extra_forbidden` today. The AC4 negative tests therefore assert a *field-type* error (string_type/list_type) at loc `quest_anchors` and the ABSENCE of `extra_forbidden` — verified they fail now (only `extra_forbidden` fires) and will pass once the field exists and rejects bad types. No false-greens.

**GREEN targets for Dev (Agent Smith):**
1. Add `quest_anchors: list[str] | None = None` to `WorldStatePatch` (session.py:485).
2. `_apply_world_patch_inner` (session.py:1345): `if patch.quest_anchors is not None:` → order-preserving dedup union into `self.quest_anchors` (NOT replace — matches quest_seed.py / record_quest.py; preserves spine).
3. Emit `world.patch.quest_anchors_present` (bool) on the `apply_world_patch` span — True when patch touches the field, False otherwise.
4. Emit `orbital.course.quest_anchors_consumed` (anchor_count=N) INSIDE `compute_courses` (course.py:119) — covers both call sites + the blind narration_apply read.

### Rule Coverage (No Silent Fallbacks / OTEL principle)

| Rule | Test(s) | Status |
|------|---------|--------|
| No silent fallback on malformed data | `test_world_patch_rejects_non_string_quest_anchor_items`, `test_world_patch_rejects_non_list_quest_anchors` | failing (RED) |
| No silent spine-clobber (union, not replace) | `test_apply_world_patch_dedup_appends_anchors_preserving_spine`, `test_apply_world_patch_empty_list_is_noop_union`, `test_apply_world_patch_none_quest_anchors_preserves_existing` | 2 failing / 1 passing |
| OTEL on every subsystem decision | `test_apply_world_patch_emits_quest_anchors_present_attr`, `test_apply_world_patch_quest_anchors_present_false_when_absent`, `test_compute_courses_emits_quest_anchors_consumed_span` | failing (RED) |
| Wiring test (component reachable from prod path) | `test_patch_anchors_flow_through_snapshot_to_course_as_quest_objective` | failing (RED) |

**Self-check:** 0 vacuous tests. Every test has a meaningful assertion on a value, not just `is_some`/`is not None` on a constant.

**Handoff:** To Dev (Agent Smith) for GREEN implementation.

## TEA RED→GREEN Status Note (concurrent implementation)

**Timeline:** RED was authored and verified failing for the right reason — commit `7ff200a`,
ground-truth `uv run pytest -n0` = **14 failed, 1 passed** against the unimplemented code
(WorldStatePatch had no quest_anchors field; spans absent). Agent Smith (Dev) then
implemented GREEN **concurrently in the shared workspace** while I was aligning tests to
SM's final spec.

**Current ground truth:** `16 passed in 0.16s` (direct `uv run pytest -n0`, NOT the
testing-runner — which hallucinated per-test prose 3× this story; all counts independently
verified by hand). Test commits: `7ff200a` (RED) + `5a9a845` (final-spec alignment: union
critical scenario + narration_apply integration test).

**Implementation observed in working tree (Dev's, uncommitted):**
- `session.py:533` — `WorldStatePatch.quest_anchors: list[str] | None = None` (AC1)
- `session.py:1386-1395` — dedup-append order-preserving union into `snapshot.quest_anchors` (AC2, no clobber)
- `session.py:1353` — `world.patch.quest_anchors_present` bool on the apply span (AC1/AC5)
- `course.py:159-161` — `emit_quest_anchors_consumed(anchor_count=len(quest_anchors))` inside `compute_courses` (AC2/AC5; covers both call sites)
- `telemetry/spans/course.py:36,73` — `SPAN_QUEST_ANCHORS_CONSUMED` + emitter (AC5)

**For verify/Reviewer:** all reconciled ACs (AC1/AC2/AC4/AC5) have passing coverage; AC3
correctly absent (dropped). One non-blocking note: consumed-span placement is inside
`compute_courses` rather than via an extended `emit_course_compute` — functionally covers
both sites; confirm acceptable.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/game/session.py` — `WorldStatePatch.quest_anchors: list[str] | None = None` field (AC1/AC4); `world.patch.quest_anchors_present` bool on the `apply_world_patch` span (AC5); order-preserving dedup-union merge into `snapshot.quest_anchors` in `_apply_world_patch_inner` (AC2)
- `sidequest/telemetry/spans/course.py` — `SPAN_QUEST_ANCHORS_CONSUMED` constant (FLAT_ONLY registered) + `emit_quest_anchors_consumed(anchor_count=...)` emitter (AC5)
- `sidequest/orbital/course.py` — call `emit_quest_anchors_consumed` at the single anchor-read point inside `compute_courses` (AC2/AC5; covers both call sites incl. previously-blind narration_apply read). Signature unchanged.

**Tests:** 16/16 passing (GREEN) — `tests/game/test_world_patch_quest_anchors.py` (14) + `tests/orbital/test_quest_anchors_course_wiring.py` (2, incl. real `_apply_course_sidecar` wiring path). Verified via direct `uv run pytest -n0`, NOT testing-runner.

**Regressions:** None. DB-free blast radius (orbital + telemetry + quest_anchors + quest_seed) = 696 passed. The 20 failures / 72 errors in the broader `tests/server/` + one `tests/game` retrieval-wiring run are all pre-existing `MissingDatabaseUrlError` (no `SIDEQUEST_DATABASE_URL` in this env) — confirmed identical against a clean `git stash` of my changes.

**Lint/format:** `ruff check` + `ruff format --check` clean on all 3 changed files.

**ACs:** AC1 ✓ AC2 ✓ AC4 ✓ AC5 ✓ — AC3 (migration) correctly absent per Architect reconcile (no legacy `world_data_updates` ever existed).

**Branch:** feat/77-3-promote-quest-anchors-worldstatepatch (sidequest-server)

**Handoff:** To verify/review phase.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None (the two pre-known AC drift items were ruled at interim spec-check and are already logged + ratified below)
**Verification:** Re-verified the committed GREEN diff (`e0e834d`, 3 files, +49) against HEAD myself — not the relayed summary.

### Ruling ratifications (the two items SM asked me to formally rule on)

1. **AC3 DROPPED — RATIFIED.** The diff contains **zero** migration logic: no `world.patch.quest_anchors_migrated` span, no legacy `world_data_updates` read, no fictional source field. Nothing was stubbed. Load safety rides on pydantic defaults (`snapshot.quest_anchors → []`, `patch.quest_anchors → None` no-op) and is covered by `test_world_patch_lacking_quest_anchors_key_loads_as_default`. The absence signal is delivered for free by AC1's `world.patch.quest_anchors_present=false`. This is the correct No-Stubbing / No-OTEL-theater outcome.

2. **`quest_anchors_consumed` span placement INSIDE `compute_courses` — RATIFIED (improves on my literal suggestion).** I originally said "extend `emit_course_compute` at both call sites." Dev/TEA instead emit `emit_quest_anchors_consumed(anchor_count=len(quest_anchors))` at the single anchor-read point inside `compute_courses` (course.py:159-161), with `SPAN_QUEST_ANCHORS_CONSUMED` registered in `FLAT_ONLY_SPANS` (course.py:36,73). This **fully satisfies my "both sites covered, no blind read" intent** — it covers orchestrator.py:2408 AND the previously-blind narration_apply.py:1972 with one emission, and is refactor-stable (no future caller can forget it). Strictly better than per-call-site wiring. TEA's `test_narration_apply_course_path_emits_quest_anchors_consumed_span` drives the real `_apply_course_sidecar` path and passes against it.

### Verified correctness points

- **Merge semantics (my load-bearing catch): CORRECT.** `_apply_world_patch_inner` (session.py:1386-1395) does `for anchor in patch.quest_anchors: if anchor not in self.quest_anchors: self.quest_anchors.append(anchor)` under an `is not None` guard — order-preserving dedup **union, not replace**. Empty list is a no-op union (no "clear" semantic). The seeded campaign spine cannot be clobbered by a narrator world-patch. Matches `quest_seed.py:85` / `record_quest.py:122/154`.
- **Span no-op safety:** `emit_quest_anchors_consumed` uses `with Span.open(...): pass` — byte-identical to the proven sibling `emit_course_compute`; safe under direct unit calls with no active tracer.
- **anchor_count provenance:** sourced from the real `quest_anchors` param (`len(...)`), emitted after the `party_at` early-return guard (no span when there's no plot origin) and before scope/cap selection ("what the scheduler read"). Correct.
- **AC4 loud-reject:** satisfied upstream for free by `WorldStatePatch`'s `extra="forbid"` + typed `list[str]` — malformed payloads raise `ValidationError` at the model boundary; no manual guard, no silent `[]`.
- **compute_courses signature UNCHANGED** — stays a pure keyword-only fn reading `snapshot.quest_anchors`; no transient patch threaded in. As ruled.

### Dev's non-blocking note (consumed span fires twice/turn, anchor_count even at 0)

**Blessed as intentional, not a defect.** Emitting at every `compute_courses` read with valid `party_at` — including `anchor_count=0` — is the correct decision-point semantic per the OTEL principle: a `0` is signal ("scheduler ran, read no anchors") and distinct from no-span ("scheduler didn't run"). This is a No-Silent-Skip win, not noise. The twice-per-turn / non-deduped volume is a **future tuning question only**, not a wiring gap — recorded as a tuning item, no action required for this story.

**Decision:** PASS — proceed to TEA verify. No changes required. The two logged deviations (AC2 premise correction, AC3 drop) stand ratified; spec-reconcile will carry them forward unchanged.

## TEA Verify Verdict — PASS

**Phase:** verify | **Diff:** e0e834d (3 files, +49) | **Verdict:** PASS — ready for Reviewer. No code changes required.

### Simplify Report
**Teammates:** reuse, quality, efficiency (haiku, parallel) | **Files analyzed:** 3

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | Dedup-append is acceptable local duplication across 3 writers (quest_seed.py:85, record_quest.py:122/154, session.py:1393); too simple/contextual to extract. |
| simplify-efficiency | clean | O(n·m) dedup correct for single-digit anchor lists + order-preservation mandatory; always-emit span correct per OTEL "every decision emits" principle. |
| simplify-quality | 4 findings (3 medium, 1 low) | All cosmetic/spec-locked/convention-consistent — see triage. |

**Quality-finding triage (zero high-confidence → nothing auto-applied):**
- (medium) course.py:159 local import of `emit_quest_anchors_consumed` — mirrors the established `emit_course_compute` local-import convention at orchestrator.py:2415; flagged, not changed.
- (medium) course.py:161 emit placed before the quest loop / "consumed" naming — `anchor_count=len(quest_anchors)` is the read count; Neo already ratified placement; cosmetic, flagged.
- (medium) telemetry/spans/course.py:36 constant `SPAN_QUEST_ANCHORS_CONSUMED` vs sibling `SPAN_COURSE_*` — the span STRING `orbital.course.quest_anchors_consumed` is **spec-mandated** (AC2/AC5), so it must not change; constant-name divergence is minor, flagged.
- (low) docstring-length asymmetry vs `emit_course_compute` — cosmetic, noted.

**Applied:** 0 (no high-confidence findings). **Flagged for Reviewer:** 4 (above). **Reverted:** 0. **Overall:** simplify: clean (no actionable defects).

### Quality Gates
- **ruff check** (3 files): PASS (All checks passed!)
- **ruff format --check** (3 files): PASS (3 files already formatted)
- **Target tests** (`uv run pytest -n0`): **16 passed** (the two 77-3 files).
- **DB-free blast radius:** tests/orbital + tests/telemetry = **666 passed, 6 skipped**; `-k "quest_anchor or quest_seed"` = **36 passed, 2 skipped** (~702, consistent with Dev's ~696).
- **Full suite:** **8875 passed, 1445 skipped, 20 failed, 72 errors** in 42s.

### Wider-suite failure adjudication (SM's spot-check request)
All **20 failed + 72 errors** are the pre-existing **`MissingDatabaseUrlError`** (`SIDEQUEST_DATABASE_URL` unset in this env; ADR-115 fail-loud). Evidence:
- Verbatim error class confirmed on both a "failed" (test_app/forensics/lore_rag/reference `*_fails_loud_500`/chargen/culture/retrieval/scene) and an "errored" (reference_map/timeline/lore) sample: `sidequest.game.db_config.MissingDatabaseUrlError`.
- Sanity grep across all 20 failures for `quest_anchor` / `WorldStatePatch` / `compute_courses` / `quest_anchors_consumed` → **zero hits**. No 77-3 symbol implicated.
- The 77-3 diff touches **no** persistence/DB code (model field + telemetry + orbital only) — it is structurally incapable of causing a DB-connection failure.
- (failed-vs-errored is just pytest classifying the same `MissingDatabaseUrlError` by whether it fires in a fixture/setup vs the test body.)
**Conclusion:** SM's claim CONFIRMED — wider failures are exclusively the pre-existing DB-env gap; 77-3 introduces zero regressions.

## Reviewer Assessment

**Verdict:** APPROVED
**Reviewer:** The Merovingian (adversarial review of e0e834d, 3 files +49) — independently verified, did not trust upstream prose.

**Data flow traced (end-to-end, verified myself):** narrator `WorldStatePatch.quest_anchors`
→ `_apply_world_patch_inner` order-preserving dedup UNION (session.py:1386-1395)
→ `snapshot.quest_anchors` (typed `list[str]`, `default_factory=list`)
→ BOTH `compute_courses` callers read it: orchestrator.py:2413 via `context.quest_anchors`
(← session_helpers.py:1137 `list(snapshot.quest_anchors)`) AND narration_apply.py:1977
directly (`list(snapshot.quest_anchors)`) → `emit_quest_anchors_consumed` fires inside
`compute_courses`. Real wiring, not stubbed — `compute_courses` is the real function in both tests.

**The 5 critical probes SM set, answered:**
1. **Union clobber-proof in ALL paths?** YES. The merge is the only write path for patch-sourced
   anchors; `quest_seed.py:85` + `record_quest.py:122/154` use the identical dedup-append idiom.
   The named critical scenario `[A,B]+[B,C]→[A,B,C]` is tested; empty-list is a no-op union (no clear
   semantic); `None` preserves existing. A replace would wipe `A` — asserted it does NOT.
2. **AC4 raises for EVERY malformed shape?** YES — runtime-verified across 7 shapes (ints,
   bare-string, None-in-list, dict, nested-list, bool, float): ALL rejected at construction. The sneaky
   `string_not_list` case (a bare string is iterable; a naive impl would accept it as a char-list) is
   correctly rejected. Also verified the **save-load** path (`GameSnapshot.model_validate`) rejects
   malformed `quest_anchors` — so bad data cannot reach the orbital read through ANY path.
3. **Wiring test real or stubbed?** REAL. Test 1 drives real `apply_world_patch` → real `compute_courses`
   with `list(snap.quest_anchors)` (production mirror), asserts QUEST_OBJECTIVE selection. Test 2 drives
   the REAL `_apply_course_sidecar` (narration_apply path) and asserts the span fired (anchor_count==1) —
   closing the previously-blind read. No mock of the consumer.
4. **Swallowed errors / silent fallbacks introduced?** NONE. `emit_quest_anchors_consumed` is
   byte-identical in structure to the proven `emit_course_compute` (`with Span.open(...): pass`) — no new
   try/except swallow, no new raise risk. No silent `[]` default anywhere; absence is signalled by
   `quest_anchors_present=false`.
5. **New span reachable from production?** YES — emitted inside `compute_courses`, which has two live
   production callers (orchestrator prompt assembly + narration-apply course refresh). Registered in
   `FLAT_ONLY_SPANS`. Not test-only.

**AC verdict:** AC1 ✓ · AC2 ✓ · AC3 cleanly DROPPED (no fictional migration stub — grep-confirmed zero
`world_data_updates`/`quest_anchors_migrated`; No Stubbing honored) · AC4 ✓ · AC5 ✓.

**Verification I ran myself** (per memory note — testing-runner hallucinates, trust counts only):
16/16 story tests pass; 350 passed in `tests/orbital/` + `tests/game/test_session.py` (zero regressions);
ruff clean on all 3 touched files; runtime malformed-rejection matrix at both construction and save-load.
The 20 failed/72 errored in the full suite are pre-existing `MissingDatabaseUrlError` (DB unset in env) —
structurally unrelated to this DB-free diff; corroborates TEA's adjudication.

**Observations (all non-blocking, ≥5 documented):**
- [VERIFIED GOOD] End-to-end wiring: patch → snapshot union → both compute_courses callers.
- [VERIFIED GOOD] AC4 loud-reject across 7 malformed shapes at construction AND save-load — no coercion.
- [VERIFIED GOOD] Union is clobber-proof (critical scenario + empty no-op + None-preserve tested).
- [VERIFIED GOOD] Wiring tests exercise the real consumer, not a stub.
- [VERIFIED GOOD] AC3 dropped with no dead/fictional code (No Stubbing).
- [VERIFIED GOOD] New emit introduces no swallowed errors; mirrors existing convention.
- [LOW] consumed span fires twice/turn, anchor_count even at 0 — Neo blessed as intentional
  No-Silent-Skip signal; future tuning only. Concur.
- [LOW] local import inside compute_courses + spec-mandated span-name divergence from `course.*`
  siblings — convention-consistent / spec-locked; not defects.

**No Critical / High / Medium findings.**

**Deviation audit:** AC2 premise correction (patch→snapshot union) — ACCEPTED, ratified by Architect,
matches the established two-writer idiom and prevents spine clobber. AC3 drop — ACCEPTED, counterfactual
premise, dropping it removes fictional scope (No Stubbing). Both stand.

**Handoff:** To SM (Morpheus) for finish-story.

### Test-quality self-audit
- No vacuous assertions (scanned for `assert True`/`let _`/`is_some`/trailing `is not None`): none.
- file1: 14 tests / 16 assert lines; file2: 2 tests / 4 assert lines — every test asserts on a concrete value.
- AC5 wiring test genuinely exercises the **real** narration_apply path: real `_apply_course_sidecar` + real `Session(orbital_content=load_orbital_content(world_minimal))` + real `compute_courses`; OTEL asserted via `otel_capture` on real emitted spans. No `unittest.mock` of the path under test.

**Handoff:** To Reviewer (The Merovingian) for code review. AC1/AC2/AC4/AC5 all covered + green; AC3 correctly absent.

## Architect Assessment (spec-reconcile)

**Status:** RECONCILED — clear for finish.

I re-verified the as-built (`e0e834d`) and all logged deviations against HEAD myself, and cross-checked ADR-137/130/128.

### 1. Design Deviations record — COMPLETE & accurate (durable audit trail)

The five logged deviations are the definitive record and all verified accurate against the as-built:
- **AC1** to_dict/from_dict → `model_dump`/`model_validate` (pydantic v2; the named methods never existed). *minor.*
- **AC2** premise correction — `world_data_updates` never existed; promote = add `WorldStatePatch.quest_anchors` + order-preserving dedup-**union** merge into `snapshot.quest_anchors`; `compute_courses` signature unchanged. *major.*
- **AC3** dropped — no legacy `world_data_updates["quest_anchors"]` to migrate; load safety via pydantic defaults + test; absence signal free via `quest_anchors_present=false`. No fictional stub (grep-confirmed). *major.*
- **AC5** consumed-span placed **inside** `compute_courses` (single read point) — covers both call sites incl. the previously-blind `narration_apply.py:1977` read; better-than-literal, refactor-stable. *minor.*
- **ADR-137 `quest.anchor.added`** superseded by `quest_anchors_present` + `quest_anchors_consumed` (added this phase). *minor, forward-impact minor for 77-4/77-5.*

No additional deviations beyond these. No AC deferrals to verify (AC3 was dropped, not deferred; AC1/AC2/AC4/AC5 all DONE).

### 2. ADR-137 reconciliation CALL → **(a) NO ADR amendment required to finish 77-3.**

Rationale: **ADR-137's decision record is accurate as-built.** It has **zero** mentions of `world_data_updates` (grep-confirmed) — that fiction lived only in the 77-3 story spec, and the session-file deviation record is its correct durable home. ADR-137's §Code-grounded root cause ("not a `WorldStatePatch` field… zero write paths") and §Decision-3 ("Add `quest_anchors` to `WorldStatePatch` with a real write path; promote, do not retire — `orbital/course.py` already consumes anchors") describe **exactly** what shipped. The only ADR staleness is cosmetic (story-numbering: table says "77-4 promote", live = 77-3) plus an OTEL span-name evolution (`quest.anchor.added` → present/consumed) whose **intent is fully met**. Neither blocks finish, and forcing an orchestrator-repo ADR edit now would impose a coordinated two-PR change (per the project's "subrepo story + ADR note = two PRs" cost) for non-blocking freshness.

**Optional, non-blocking — for epic-close batching only (NOT a 77-3 finish gate).** If you want ADR-137's table kept current, add this addendum as a separate orchestrator-repo change when epic 77 closes. Do NOT edit ADR-137 from the server workspace; do NOT gate 77-3 on it. Exact text:

> **Implementation reconciliation (2026-06-04).** Live sprint numbering differs from the §Implementation Stories table: "promote quest_anchors" shipped as **77-3** (table says 77-4); the epic renumbered seed→77-1, typed-tools→77-2, promote→77-3. The promote story's OTEL landed as `world.patch.quest_anchors_present` (bool, on the apply-patch span) + `orbital.course.quest_anchors_consumed` (`anchor_count`, at the course read) rather than the table's `quest.anchor.added` — the present/consumed pair covers the same observability intent (anchor writes and consumption are GM-panel-verifiable) at the two real decision points; `quest.anchor.added` was not implemented (and downstream stories should reuse present/consumed rather than mint it). §Code-grounded root cause and §Decision remain accurate as-built: `quest_anchors` is a first-class `WorldStatePatch` field with a dedup-union write path, and the `orbital/course.py` consumer is preserved per ADR-130. No `world_data_updates` lane was ever involved — that phrasing appeared only in the 77-3 story spec, not this ADR.

### 3. Sibling ADRs — no contradiction.

- **ADR-130 (orbital clock/course):** as-built keeps `compute_courses` selecting bodies and marking anchors `CourseSource.QUEST_OBJECTIVE` with an **unchanged signature**; the new span is purely additive observability at the existing read. ADR-137 §Decision-3 explicitly preserves this consumer. **Consistent.**
- **ADR-128 (trope governor / seed deck):** untouched by this 3-file diff; zero `quest_anchors`/`WorldStatePatch` coupling (grep-confirmed). `quest_anchors` ≠ `seed_tropes`. **No contradiction.**

**Decision:** RECONCILED. Proceed to finish ceremony. ADR call = **(a)**; the optional ADR-137 freshness note is provided for epic-close batching at SM's discretion, not a finish blocker.
