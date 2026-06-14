---
story_id: "107-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 107-1: Generated-dungeon scene/location advance

## Story Details
- **ID:** 107-1
- **Jira Key:** (none—Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server
- **Branch:** feat/107-1-generated-dungeon-scene-advance (in sidequest-server, off develop)

## Sm Assessment

Story 107-1 is a server-only infrastructure fix. The bug: traversing ADR-106
procedural dungeon rooms never advances the structured scene state —
`discovered_rooms`, `scene_id`, and `region_transitions` all freeze after the
scripted opening, so the entire descent reads as a single scene and the
ADR-109/ADR-050 render pipeline under-fires (no fresh POI/illustration per room).

**Scope:** Advance the structured scene on each room entry: populate
`discovered_rooms`, advance `scene_id`, and log `region_transitions`. This unblocks
per-room content binding (107-2 already shipped against this contract and carries a
loud blocking dependency on 107-1 wiring `region_for` / the stable per-room key).

**Why now:** 107-2's Monster Manual per-room binding is in production but dead at
the production call site until 107-1 supplies the per-room location key and wires
the scene-advance path. This is the keystone that makes the descent legible to both
the render pipeline and content binding.

**Routing:** tdd / phased → TEA writes RED tests asserting per-room scene advance
(discovered_rooms grows, scene_id changes, region_transitions logged on room entry),
plus the wiring test (the advance fires from a production room-entry path, not just
in isolation). Read 107-2's archived deviations — the per-room key contract is
already half-defined there.

**Branch correction:** sm-setup created the feature branch in the orchestrator by
mistake; I moved it to sidequest-server (off develop, per repos.yaml) and returned
the orchestrator to main. Context/session edits stay on orchestrator main as usual.

## TEA Assessment

**Tests Required:** Yes (delivered as regression coverage)
**Status:** GREEN — behavior pre-delivered by `be4f7464` (#835); tests lock in the contract.

**Test Files:**
- `tests/agents/subsystems/test_scene_advance_107_1.py` — engine side: a procedural
  move (`run_movement_dispatch`) advances `discovered_regions`, `region_transitions`,
  and `current_region` together. No prior test asserted these side effects fire on a move.
- `tests/integration/test_dungeon_scene_advance_107_1.py` — render side: each procedural
  room entry emits a fresh, DISTINCT `LOCATION_DESCRIPTION` through the real
  materializer-emit → `load_room_payload` → `_maybe_emit_location_description` chain
  (region ids `exp001.r1`/`exp001.r2`; distinct region_id + prose, proving the descent
  no longer reads as one frozen scene).

**Tests Written:** 2 (1 unit, 1 integration). Both green.

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|---------------------------|---------|--------|
| Wiring test (non-test consumer reachable) | `test_each_procedural_room_entry_emits_a_fresh_location_description` (drives real `_maybe_emit_location_description` + real `load_room_payload`) | green |
| No source-text wiring assertions | both tests are behavior/drive-and-assert (no `read_text()` greps) | green |
| Meaningful assertions (no vacuous) | both assert concrete values (region_id, prose substrings, transition fields) | green |

**Self-check:** 0 vacuous tests. Both have value-bearing assertions and a negative
(distinctness) check.

**Verification method (honest):** every link of the render chain driven with real
components; NOT a live postgres turn or headless playtest — recorded as a non-blocking
Delivery Finding for the epic-107 verify step.

**Handoff:** Behavior pre-delivered → Dev's green phase is a no-op confirmation
(run the suite, confirm green, pass through to Reviewer). Per Operator: ship as coverage.

### TEA rework note (round 2 — after Reviewer REJECTED)

Avasarala's rejection was fair; addressed every severity-table item:
- **Overclaiming docstrings (both files):** rewritten. The integration test no longer
  claims "end-to-end"/"render is wired"; it states GREEN proves the helper SOURCES a
  procedural-room YAML (distinct scene per room) and explicitly defers the gate-fires-
  per-room verification to the epic-107 live `sq-playtest`. The unit docstring now frames
  `current_region` as a consensus-sync SIDE EFFECT (single-PC scope; split-party holds).
- **`assert entries` → `assert len(entries) == 1`** (meaningful-assertion rule 6/A4).
- **Split-party negative added** (`test_split_party_move_does_not_advance_current_region`):
  a split move advances the mover's per-PC fields + shared fog-of-war but NOT the party
  `current_region`.
- **No-source negative added** (`test_unmaterialized_room_emits_nothing`): an
  unmaterialized room emits ZERO messages — with `cartography=None` so a MagicMock world
  cannot fake a region and mask the guard (the masking the test-analyzer flagged).
- **Redundant `!=` assertion removed.**

Now 4 tests (2 unit, 2 integration), all green; ruff lint+format clean.
**Handoff:** Dev green phase — confirm green, pass through to Reviewer.

## Dev Assessment

**Implementation:** None required. 107-1's behavior is pre-delivered by `be4f7464`
(#835, "in-dungeon movement for region-mode worlds") + the region machinery. Per
Operator decision (2026-06-14) the story ships as regression coverage; the two tests
Amos committed ARE the deliverable.

**GREEN verification:** `testing-runner` (RUN_ID 107-1-dev-green) — 2 passed, 0 failed,
0 skipped (0.11s):
- `tests/agents/subsystems/test_scene_advance_107_1.py` — 1 passed
- `tests/integration/test_dungeon_scene_advance_107_1.py` — 1 passed

**Code changes:** none (no `src` edits; `git diff develop --stat` shows only the two
test files Amos committed).

**Handoff:** To Avasarala (Reviewer). This is a coverage-only delivery — review the two
tests for fidelity (do they truly assert per-room scene advance + distinct per-room
render, not a vacuous green?) and the TEA finding that #835 closed the behavior. No
production diff to review.

### Dev rework note (round 2 — after Reviewer REJECTED → TEA reworked)

No implementation work for me — TEA's rework was test-only (docstrings, assertion
strength, +2 negative cases). Re-verified GREEN: `testing-runner` (RUN_ID
107-1-dev-green-r2) — **4 passed, 0 failed, 0 skipped**. Still zero production diff
(`git diff develop...HEAD` = the two test files only). Re-handing to Avasarala for
re-review.

## Subagent Results

All received: Yes (4 of 4 enabled subagents, both rounds).

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 2/2 green, lint+format clean, 0 smells | N/A |
| 2 | reviewer-test-analyzer | Yes | findings | gate-not-exercised; split-party untested; `assert entries` weak; no-source negative missing; redundant `!=` | partially confirmed — severities re-scoped (no prod code) |
| 3 | reviewer-comment-analyzer | Yes | findings | 4 high-confidence lying/overclaiming docstrings (integration "end-to-end"/"render is wired"; unit current_region framing) | CONFIRMED — required fix |
| 4 | reviewer-rule-checker | Yes | findings | Rule 6/A4: `assert entries` truthy (must fix); A2 wiring-of-dispatch gap; 3 low type-annotation gaps (exempt) | `assert entries` CONFIRMED (cannot dismiss); rest noted |

**Triage notes (project severity, not subagent self-labels):** Critical/High in this project = security/data-corruption / missing-error-handling-or-races. This diff has ZERO production code, so the subagents' "Critical" labels do not map to blocking production defects. One subagent claim is partly wrong: `notify_region_transition` IS exercised (it appends `discovered_regions`, which the unit test asserts) — only the §Q3 sync-materialize/look-ahead path is skipped. The genuinely actionable, convergent findings are (a) overclaiming docstrings and (b) the `assert entries` rule violation — both cannot be dismissed under the rules-are-not-suggestions principle.

### Subagent Results — Round 2 (re-review of the rework)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 4/4 green, lint+format clean, 0 smells | N/A |
| 2 | reviewer-comment-analyzer | Yes | resolved | all 4 prior overclaims GENUINELY resolved; 1 new Low: `§Q3` jargon unexplained | accept resolution; §Q3 = non-blocking (mirrors `movement.py`'s own §Q1/§Q3/§Q5 labels) |
| 3 | reviewer-rule-checker | Yes | clean | 0 violations; `assert entries` fix confirmed; new tests rule-clean; `cartography=None` confirmed correct No-Silent-Fallbacks | accept |
| 4 | reviewer-test-analyzer | Yes | findings | prior findings resolved; new tests honest/non-vacuous; 3 NEW Low/Med: split-party `Marta=='a'` weak; positive could use `cartography=None`; import via re-export path | all non-blocking — recorded below |

**Round-2 triage:** every round-1 blocking finding (overclaiming docstrings, `assert entries`) is resolved and CONFIRMED by the subagent that raised it. The three new test-analyzer findings are Low/Medium test-quality refinements: none match a project rule (rule-checker clean), none vacuous, and the import-via-re-export mirrors the canonical `test_location_description_emit.py`. The split-party test's load-bearing assertion (`current_region == "a"`) is solid; the `Marta=='a'` line is a weak bonus, not the contract. Not grounds to ping-pong a third round.

## Reviewer Assessment

**Verdict (round 1):** ~~REJECTED~~ — superseded by round-2 re-review below.

**Verdict (round 2, FINAL):** APPROVED

The rework resolved every round-1 finding (confirmed by comment-analyzer + rule-checker re-runs): honest docstrings that state what GREEN proves vs. what's deferred to the epic-107 live playtest; `assert len(entries) == 1`; split-party + no-source negatives added; redundant `!=` removed. Re-review preflight 4/4 green, lint clean, rule-checker 0 violations. Remaining items are non-blocking Low/Medium test-quality notes (recorded in Delivery Findings). The deliverable is now an honest, non-vacuous, rule-clean regression guard.

**Specialist findings incorporated (round 2):**
- `[DOC]` (comment-analyzer): all 4 round-1 overclaiming docstrings GENUINELY resolved; 1 new Low — `§Q3` jargon (non-blocking; mirrors `movement.py` section markers).
- `[RULE]` (rule-checker): clean, 0 violations; `assert entries` → `assert len(entries) == 1` confirmed; `cartography=None` confirmed correct No-Silent-Fallbacks.
- `[TEST]` (test-analyzer): prior findings resolved, new tests honest/non-vacuous; 3 new Low/Med refinements (split-party `Marta` check weak; positive could use `cartography=None`; import via re-export) — all non-blocking, recorded in Delivery Findings.
- `[PREFLIGHT]`: 4/4 green, lint+format clean, 0 smells.

**Handoff:** To SM for finish-story.

<details><summary>Round-1 assessment (retained for history)</summary>

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] | Overclaiming docstrings — "verifies the full per-room render chain **end-to-end**" / "the per-room render **is wired**" / "the way the turn handler's region-mode gate does". The test bypasses the production gate (`_is_region_mode_world` + `_region_changed`); green only proves the helper can source a procedural-room YAML. A lying docstring in a lie-detector-culture project. | `tests/integration/test_dungeon_scene_advance_107_1.py:13,21,81` | Rewrite docstrings to state honestly what green proves vs. what is deferred to the epic-107 live playtest. |
| [MEDIUM] | Unit docstring frames `current_region` as a field the movement mechanism "advances"; it is a consensus-sync SIDE EFFECT that fires only on single-PC/party-consensus. Misleading about scope. | `tests/agents/subsystems/test_scene_advance_107_1.py:13,98` | Qualify: consensus-sync side effect; split-party leaves it unchanged. |
| [LOW · rule, cannot dismiss] | `assert entries` truthy check violates the meaningful-assertion rule (Rule 6 / A4) — does not enforce exactly-one transition. | `tests/agents/subsystems/test_scene_advance_107_1.py:94` | `assert len(entries) == 1`. |
| [LOW] | Missing edge cases that would make the guard real: split-party non-advance (named in the spec) and the no-source negative (the exact under-fire failure mode). | both files | Add the two cases (recommended, strengthens the deliverable). |
| [LOW] | Redundant `assert region_id != region_id` subsumed by the two `==` checks. | `tests/integration/test_dungeon_scene_advance_107_1.py:134` | Remove (noise). |

**Why reject a coverage-only, green delivery:** the deliverable's PURPOSE is trustworthy regression coverage. Two of the findings (overclaiming docstrings, `assert entries`) match stated project principles (honesty / meaningful assertions) and cannot be dismissed. They are cheap test-design fixes. This does NOT re-litigate the Operator's ship-as-coverage decision — it makes the coverage honest about its own scope, which that decision relies on. The gate-firing-per-room verification correctly stays deferred to the epic-107 live `sq-playtest` (carried as a finding), and the docstrings must say so plainly.

**Original review notes (retained — the tests are non-vacuous and the chain is real):**

Coverage-only delivery (235 lines, two test files, zero production diff). I do not
rubber-stamp green — I verified the tests are honest:

- **Engine guard** (`test_scene_advance_107_1.py`): drives the REAL
  `run_movement_dispatch` → REAL `GameSnapshot.apply_world_patch` → REAL
  `frontier_hook.notify_region_transition` + consensus-sync. Only the dungeon store
  and palette are faked (graph source / projection) — the asserted side effects
  (`discovered_regions`, `region_transitions`, `current_region`) are produced by real
  engine code, not the fakes. Non-vacuous: asserts concrete values + the relocation
  receipt's from/to/pc.
- **Render guard** (`test_dungeon_scene_advance_107_1.py`): real `write_room_yaml`
  (materializer seam) → real `load_room_payload` → real `_maybe_emit_location_description`.
  Asserts DISTINCT region_id + DISTINCT prose per room and `len == 1` per emit — a silent
  no-source under-fire (the epic-107 symptom) would fail this. Confirmed it runs in the
  DEFAULT suite (`addopts` ignores only `tests/e2e`; `--collect-only` collects it).

**Data flow traced:** player move → `apply_world_patch(pc_region)` → `pc_regions` +
`region_transitions` + `discovered_regions` + consensus-synced `current_region` →
region-mode render gate (`websocket_session_handler.py:2280`) →
`_maybe_emit_location_description(room_id_override=current_region)` → `load_room_payload`
sources the materializer-emitted `rooms/<region_id>.yaml` → `LocationDescriptionMessage`.
Safe: every link verified by a real-component test except the gate's per-room *firing*,
which is code-read (see Devil's Advocate).

**Pattern observed:** content-free fixture mirrors
`tests/agents/subsystems/test_movement_dispatch.py`; no source-text wiring greps (complies
with the "No Source-Text Wiring Tests" rule); meaningful assertions throughout.

**Error handling:** N/A (no production code). Round-trips real files in `tmp_path`; a
filesystem fault errors loudly, not silently.

### Devil's Advocate

Argue it's broken. The load-bearing weakness: **neither test exercises the production
gate that decides WHEN to render.** The integration test calls
`_maybe_emit_location_description` directly with `room_id_override`; it proves the helper
*can* source a procedural room, not that a live descent *calls* it once per room. The
entire "already delivered" verdict's last link — the region-mode gate at
`websocket_session_handler.py:2263-2287` firing on each `current_region` change — rests on
code-reading. If that gate had a subtle defect (e.g. `_region_changed` computed against a
stale `prior_current_region`, or the room-graph branch at :2215 shadowing the region-mode
branch for a hybrid world), the descent would still under-fire and these green tests would
not catch it. Second: the unit test's `current_region` advance depends on single-PC
consensus (`region_for()` returns the consensus region); a SPLIT party yields no consensus,
`current_region` does not advance, and the render gate does not fire for the moving PC — the
test's single seat hides this. That is arguably correct (split party = no party scene) and
out of 107-1 scope, but it means the guard does not cover the split-party descent. Third:
`sd.genre_pack.worlds` is a `MagicMock` — if `load_room_payload` ever starts reading the
world object, the mock would silently absorb it and mask a regression; low risk today
because sourcing is from disk. None of these are defects in what shipped — the tests are
honest about their scope and the gate-firing gap is already a documented TEA finding. They
are the reason the epic-107 close MUST run a live `sq-playtest` descent. The subagent
fleet (comment-analyzer ×4 high-confidence, test-analyzer, rule-checker) confirmed this
gate-gap AND surfaced the overclaiming docstrings — which is what flipped this from my
premature APPROVED to REJECTED.

**Handoff:** Back to TEA (Amos) for test-design rework — fix the overclaiming docstrings,
strengthen `assert entries`, drop the redundant inequality, and add the split-party +
no-source negative cases. No production code changes.

</details>

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-14T08:47:38Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T07:53:37Z | 2026-06-14T07:56:07Z | 2m 30s |
| red | 2026-06-14T07:56:07Z | 2026-06-14T08:23:30Z | 27m 23s |
| green | 2026-06-14T08:23:30Z | 2026-06-14T08:25:24Z | 1m 54s |
| review | 2026-06-14T08:25:24Z | 2026-06-14T08:36:27Z | 11m 3s |
| red | 2026-06-14T08:36:27Z | 2026-06-14T08:40:31Z | 4m 4s |
| green | 2026-06-14T08:40:31Z | 2026-06-14T08:41:37Z | 1m 6s |
| review | 2026-06-14T08:41:37Z | 2026-06-14T08:47:38Z | 6m 1s |
| finish | 2026-06-14T08:47:38Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): 107-1's behavior was already delivered by `be4f7464`
  (#835, "in-dungeon movement for region-mode worlds") + the region machinery; the real
  gap was missing regression coverage. Per Operator decision (2026-06-14) the story is
  re-framed as *ship-as-coverage* — the two green tests ARE the deliverable. No engine
  change. Affects `tests/agents/subsystems/test_scene_advance_107_1.py` +
  `tests/integration/test_dungeon_scene_advance_107_1.py` (committed). *Found by TEA during test design.*
- **Gap** (non-blocking): definitive e2e confirmation (a headless `sq-playtest` of a
  beneath_sunden descent counting per-room `LOCATION_DESCRIPTION` OTEL emits) was NOT run —
  the chain was verified link-by-link with real components, not through a live
  postgres-backed turn. Affects the epic-107 "verify" step (playtest the descent before
  closing the epic). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation (no code written — coverage-only delivery).

### Reviewer (code review)
- **Gap** (non-blocking): the regression guards prove the render *helper* sources
  procedural rooms, but not that the production region-mode gate *fires* per room in a
  live descent — that link is code-read only. Affects the epic-107 "verify" step: run a
  headless `sq-playtest` beneath_sunden descent and assert N per-room
  `LOCATION_DESCRIPTION`/`narrator.region_patch_check` OTEL emits before closing the epic.
  Affirms the TEA finding above. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): neither guard covers the SPLIT-party descent
  (`current_region` only consensus-syncs when seated PCs agree). Likely correct-by-design,
  but if per-PC render-on-move is ever desired, add a split-party guard. Affects
  `tests/agents/subsystems/test_scene_advance_107_1.py` (single-seat fixture). *Found by Reviewer during code review.*

### TEA (test design — rework round 2)
- All Reviewer severity-table items resolved (see TEA rework note above). The
  split-party Improvement is now COVERED by `test_split_party_move_does_not_advance_current_region`. The gate-fires-per-room Gap stays deferred to the epic-107 live
  `sq-playtest` (now stated plainly in the integration test docstring, not overclaimed).
- Recommended-only items consciously NOT taken (out of 107-1 scope): the §Q3
  sync-materialize/look-ahead coverage (belongs with the look-ahead worker, epic 106)
  and the "tautological to_region" strengthening (resolution logic is owned by
  `test_movement_dispatch.py`; this guard's purpose is scene-state advance).
  *Noted by TEA during rework.*

### Reviewer (re-review, round 2 — non-blocking)
- **Improvement** (non-blocking): split-party test's `assert pc_regions["Marta"] == "a"`
  is a weak supplementary check — it passes even if a misfiring bulk-apply never touched
  Marta. The load-bearing assertion (`current_region == "a"`) is solid. Optional future
  touch: pre-assert Marta before the call, or seed Marta at a different region so a clobber
  is detectable. Affects `tests/agents/subsystems/test_scene_advance_107_1.py`.
  *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): positive integration test could pass `cartography=None`
  for symmetry with the no-source test (the positive path provably never reaches the
  cartography fallback, so it's harmless today). Affects
  `tests/integration/test_dungeon_scene_advance_107_1.py`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): `_maybe_emit_location_description` is imported via the
  re-export on `websocket_session_handler` rather than its defining module `map_emit` —
  matches the canonical `test_location_description_emit.py` convention and the re-export is
  the production call path, so accepted as-is. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): `§Q3` label in `_FakeStore.load_frontier`'s comment is
  unexplained for a test reader, though it mirrors `movement.py`'s own §Q1/§Q3/§Q5 section
  markers. Optional: expand to "the sync-materialize path in run_movement_dispatch".
  *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **RED phase produced GREEN tests (behavior pre-delivered)**
  - Rationale: Operator chose "verify end-to-end first" (2026-06-14); verification was green, so the genuine deliverable is the missing regression coverage, not a RED→GREEN impl cycle.
  - Severity: minor
  - Forward impact: GREEN (not RED) bar at red-phase exit is expected and correct for this story; the tests-fail gate will not see a failing test. Dev's green phase is a no-op confirmation. Surfaced so the gate result is not read as a mistake.
- **Story field names (discovered_rooms, scene_id) do not match the live mechanism**
  - Rationale: testing the named-but-unused fields would assert a contract nothing consumes; the procedural ADR-106 dungeon is region-based.
  - Severity: minor
  - Forward impact: none — the player-visible behavior (fresh POI/render per room) is covered via the real render path.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **RED phase produced GREEN tests (behavior pre-delivered)**
  - Spec source: context-story-107-1.md, Title (advance scene per room entry); the story implies unbuilt behavior
  - Spec text: "traversing ADR-106 procedural rooms never updates discovered_rooms, scene_id, or region_transitions ... advance the structured scene per room entry"
  - Implementation: Wrote characterization + integration tests that assert the contract; both PASS against current code (verified via `run_movement_dispatch` and the real materializer→loader→render-helper chain). The behavior was already implemented by `be4f7464` (#835). Per Operator decision the tests ship as regression coverage rather than driving new impl.
  - Rationale: Operator chose "verify end-to-end first" (2026-06-14); verification was green, so the genuine deliverable is the missing regression coverage, not a RED→GREEN impl cycle.
  - Severity: minor
  - Forward impact: GREEN (not RED) bar at red-phase exit is expected and correct for this story; the tests-fail gate will not see a failing test. Dev's green phase is a no-op confirmation. Surfaced so the gate result is not read as a mistake.
- **Story field names (discovered_rooms, scene_id) do not match the live mechanism**
  - Spec source: context-story-107-1.md, Title
  - Spec text: "populate discovered_rooms, advance scene_id, log region_transitions"
  - Implementation: Tests assert the REGION-based fields the procedural dungeon actually uses — `discovered_regions`, `current_region` (the render scene key), `region_transitions`. `discovered_rooms` is a chargen-only room-graph field and `GameSnapshot` has no `scene_id` field at all.
  - Rationale: testing the named-but-unused fields would assert a contract nothing consumes; the procedural ADR-106 dungeon is region-based.
  - Severity: minor
  - Forward impact: none — the player-visible behavior (fresh POI/render per room) is covered via the real render path.
### Dev (implementation)
- No deviations from spec. No implementation code was written — 107-1's behavior is
  pre-delivered by #835; per Operator decision the deliverable is the regression tests
  Amos committed (coverage-only). No `src` edits, so there is nothing to deviate.

### Reviewer (audit)
- **RED phase produced GREEN tests (behavior pre-delivered)** → ✓ ACCEPTED by Reviewer:
  sound. Verified the green is real (drives real engine + real render-helper, non-vacuous
  assertions), and the Operator explicitly chose ship-as-coverage knowing verification was
  at integration level. The GREEN-at-red-exit is expected for this story.
- **Story field names (discovered_rooms, scene_id) do not match the live mechanism** → ✓
  ACCEPTED by Reviewer: confirmed independently — `GameSnapshot` has no `scene_id` field
  and `discovered_rooms` is chargen-only; the procedural dungeon is region-based. Testing
  the named fields would assert a contract nothing consumes. Correct call.
- **Dev: no deviations (no code written)** → ✓ ACCEPTED by Reviewer: `git diff develop...HEAD`
  is two test files only; no production diff to deviate from.
- No undocumented deviations found.