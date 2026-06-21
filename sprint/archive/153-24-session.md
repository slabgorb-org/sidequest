---
story_id: "153-24"
jira_key: "153-24"
epic: "153"
workflow: "tdd"
---
# Story 153-24: [DUNGEON-ROOM-STATE-NOT-PERSISTED] Persist discovered_rooms/current_room/room_states to the snapshot as current_region walks the dungeon graph

## Story Details
- **ID:** 153-24
- **Title:** [DUNGEON-ROOM-STATE-NOT-PERSISTED] Persist discovered_rooms/current_room/room_states to the snapshot as current_region walks the dungeon graph
- **Points:** 3
- **Type:** Bug
- **Priority:** P2
- **Jira Key:** 153-24
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Workflow:** tdd
- **Repositories:** sidequest-server
- **Stack Parent:** none

## Story Context
See sprint/context/context-story-153-24.md for detailed problem statement, root cause direction, acceptance criteria, and key code areas.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Owner:** sm
**Phase Started:** 2026-06-21T15:34:14Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T14:33:29Z | 2026-06-21T14:35:46Z | 2m 17s |
| red | 2026-06-21T14:35:46Z | 2026-06-21T14:53:57Z | 18m 11s |
| green | 2026-06-21T14:53:57Z | 2026-06-21T15:08:13Z | 14m 16s |
| review | 2026-06-21T15:08:13Z | 2026-06-21T15:19:35Z | 11m 22s |
| green | 2026-06-21T15:19:35Z | 2026-06-21T15:26:00Z | 6m 25s |
| review | 2026-06-21T15:26:00Z | 2026-06-21T15:34:14Z | 8m 14s |
| finish | 2026-06-21T15:34:14Z | - | - |

## Sm Assessment

Setup complete for 153-24, a P2 TDD bug scoped to **sidequest-server** only.

**What's ready:**
- Session file created; feature branch `feat/153-24-dungeon-room-state-persist` cut off `origin/develop` in sidequest-server.
- Detailed context doc pre-exists at `sprint/context/context-story-153-24.md` (problem statement, root-cause direction, 6 ACs, key code areas, technical notes) — left intact.
- Merge gate clear (0 open PRs across all repos).

**Core problem (for TEA):** On dungeon traversal the snapshot writes the *region* axis (`current_region`, `discovered_regions`, `dungeon.map_emitted`) but never the *room* axis — `discovered_rooms` stays `[]`, `room_states` stays `{}`, `Character.current_room` stays `None`. The room-graph transition seam in `narration_apply.py` (~4081–4116) sets `character_locations` + fires side-effects but never records the entered room. Forensics/reload see an empty dungeon. Fix wires the existing seam to write the existing fields (ADR-055 persistence half) — **not** a new system.

**TDD red-phase guidance:** ACs 1–6 in the context doc are the test spine. Two are load-bearing for this project's principles:
- **AC 6 (wiring/integration test):** drive a multi-turn traversal through the *real* narration-apply seam (not a helper unit test) AND include a save→reload leg (ADR-115) — this is both the wiring test and the reproduction of the playtest finding.
- **AC 5 (OTEL):** a new `room.discovered` (or `dungeon.room_recorded`) span must fire on the write, distinguishing first-discovery from re-entry (CLAUDE.md OTEL principle).

**Two-axis caution (do not regress):** do NOT touch the region axis (`discovered_regions`/`current_region`/`DUNGEON_MAP` emit) — it works. Preserve the Story 45-43 container-retrieval `room_states` write at `narration_apply.py:5088` (don't clobber on re-entry). No silent fallback on a malformed room id — fail loudly.

**Routing:** phased tdd → next phase `red`, owner **tea** (The Architect).

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral bug fix with 6 ACs (state writes + persistence round-trip + OTEL). Wire-first tests are mandatory per CLAUDE.md ("Every Test Suite Needs a Wiring Test").

**Test File:**
- `sidequest-server/tests/server/test_153_24_room_state_persistence.py` — 11 wire-first tests driving the REAL `WebSocketSessionHandler._execute_narration_turn` → `_apply_narration_result_to_snapshot` transition seam.

**Tests Written:** 11 tests covering 6 ACs.
**Status:** RED — 10 failing (room-axis write absent today), 1 passing (region-mode regression guard, see below). Run:
`SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest_test SIDEQUEST_DATABASE_URL=… uv run pytest tests/server/test_153_24_room_state_persistence.py -n0`

**AC → test map:**
| AC | Test(s) | Status |
|----|---------|--------|
| AC1 discovered_rooms records entered room (idempotent) | `test_transition_appends_entered_room_to_discovered_rooms`, `test_reentering_known_room_does_not_duplicate` | failing |
| AC1 playtest repro (empty discovered_rooms → both endpoints) | `TestPlaytestReproduction::test_empty_discovered_rooms_records_both_endpoints` | failing |
| AC2 room_states seeded (no clobber on re-entry) | `test_first_entry_seeds_room_state`, `test_reentry_preserves_existing_room_state` | failing |
| AC3 Character.current_room tracks the crawl | `test_transition_sets_acting_character_current_room`, `test_current_room_follows_multi_turn_crawl` | failing |
| AC4 + AC6 multi-turn real seam + save→reload round-trip | `TestReloadRoundTrip::test_in_dungeon_snapshot_survives_save_reload` | failing |
| AC5 room.discovered OTEL span (first-vs-re-entry flag) | `test_first_discovery_emits_span_newly_true`, `test_reentry_emits_span_newly_false` | failing |
| Regression: region-mode untouched | `TestRegionModeUnaffected::test_region_mode_transition_does_not_write_room_axis` | **passing** (guards existing-correct behavior; passes before & after the fix) |

**Why the seam is correct (proof for Dev):** the failing-test span dumps show `room.transition_tick` IS firing under the test's room-graph setup — confirming the tests engage the Story 71-15 side-effect block at `narration_apply.py:4087`. The bug is precisely that this block fires side-effects but never writes the three room-axis fields. The discovery write belongs at/around this same block (before line 4105's `character_locations` write).

**The catch-22 (load-bearing for Dev):** the Story 71-15 side-effect block is GATED on `snapshot.discovered_rooms` being non-empty (`narration_apply.py:4089`). The NEW write CANNOT reuse that gate (the playtest case starts `discovered_rooms == []`). The seam now has `pack`/`world` context (Story 90-6, lines 4157-4167), so gate the room-axis write on `cartography.navigation_mode == room_graph`, NOT on `discovered_rooms` non-empty. `TestPlaytestReproduction` starts from an empty list and will only go GREEN once the gate is changed.

**OTEL span contract:** `room.discovered` with `{room_id, newly_discovered: bool, discovered_count, character}`. Dev may rename, but must update the two `TestRoomDiscoveryOtelSpan` assertions in the same PR. `newly_discovered` MUST distinguish first-discovery from backtracking (AC5).

### Rule Coverage (python.md lang-review)

| Rule | Coverage | Status |
|------|----------|--------|
| #6 Test quality (no vacuous/false-green) | Self-checked: every test has a specific value assertion; the two re-entry tests were rewritten after they false-greened on pre-seeded state — they now drive REAL transitions so they fail RED before the fix | applied |
| #1 No silent fallback | `TestPlaytestReproduction` proves the write is NOT silently skipped when `discovered_rooms` is empty (the bug = a silent skip). See deviation re: malformed-room-id "fail loud" (not testable at this seam) | partial — see Delivery Findings |
| #4 Logging severity | N/A to test code; flagged for Dev's write site (a malformed/unknown room id is a server-side concern) | deferred to Dev |

**Self-check:** 2 false-green tests found and rewritten (idempotency + no-clobber now drive real transitions). 0 vacuous assertions remain.

**Hermeticity note:** the full-pipeline turn trips the conftest `_refuse` sidecar guard (`sidecar_extraction.failed reason=transport`) — identical to Story 71-15; it is caught by the turn's catch-loops and is log noise, not a failure. No fake needed.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The room-graph-mode gate must change. Story 71-15 gated room-transition side-effects on `snapshot.discovered_rooms` being non-empty (`narration_apply.py:4089`) — a catch-22 for this story, since the playtest bug is precisely an empty `discovered_rooms`. Affects `sidequest-server/sidequest/server/narration_apply.py:4087-4105` (gate the new room-axis write on `cartography.navigation_mode == room_graph`, available via the `pack`/`world` resolved at lines 4157-4167, not on `discovered_rooms`). *Found by TEA during test design.*
- **Question** (non-blocking): Context technical-note #5 ("fail loudly on a room id that isn't a legal room-graph node") is not enforceable at this seam — `_apply_narration_result_to_snapshot` validates *region* names (`validate_region_name`) but is not threaded the world's room-graph node catalog, so it cannot tell a legal room from a narrator-confabulated one. The no-silent-fallback *intent* is covered behaviorally (the write must not be silently skipped — `TestPlaytestReproduction`). Dev to decide whether to thread the room list for hard validation or treat always-writing-in-room-graph-mode as sufficient. Affects `narration_apply.py` + `sidequest/game/room_movement.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): Context doc "Key Code Areas" cites `sidequest/dungeon/room_movement.py`; the real module is `sidequest/game/room_movement.py` (and it exposes `init_room_graph_location` / `process_room_entry`, not the `validate_room_transition`/`apply_validated_move` helpers the context implies — those never landed, per Story 71-15's contract note). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): The base branch (`origin/develop`) has broad pre-existing test failures unrelated to this story — full suite on a stashed-clean tree is 272 failed / 117 errors. The errors are content-pack `GenreLoadError`s (zone-tag validation in `sidequest-content` wonderland/gulliver, story 157-6) plus dogfight/intent-router setup errors; they do not touch the engine room-axis path. My change moves the count to 262 failed / 117 errors (fixes exactly the 10 target 153-24 tests, +10 passed, errors unchanged). Affects `sidequest-content` world authoring and `sidequest-server` test environment (not this PR). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The room-axis write stores narrator-emitted `result.location` into `discovered_rooms` and as a `room_states` key with NO structural hygiene guard, while the sibling region axis 11 lines below calls `validate_region_name(result.location)` (Story 45-16) to reject bracketed/multiline/>80-char narrator asides before they pollute `discovered_regions`. Affects `sidequest-server/sidequest/server/narration_apply.py:4187-4193` and `sidequest/game/room_movement.py:55-59` (gate the room write on `validate_region_name`, or inline the same structural check in `record_room_discovery`; `validate_region_name` is already imported at `narration_apply.py:63`). *Found by Reviewer during code review.* See SEC-1 in the assessment.
- **Improvement** (non-blocking): `record_room_discovery` is public (`__all__`) but its idempotency contract breaks if called with `from_room == to_room` on an undiscovered room (the room is appended twice). The sole caller gates `result.location != old_loc`, so it is not live — but a future caller could trip it. Affects `sidequest/game/room_movement.py:55-59` (early-return or dedup-guard the `to_room` append). *Found by Reviewer during code review.* RESOLVED in rework rt#1.
- **Improvement** (non-blocking, round 2): The pre-existing `character_locations[actor] = result.location` write (`narration_apply.py:~4105`) runs unconditionally BEFORE the validity guard, so a malformed narrator location still lands in the transient scene-tracking dict (shared with the region axis; not the persisted forensics accumulator this story fixed). Out of 153-24 scope. Affects `narration_apply.py:~4104-4105` (a future story could `validate_region_name`-guard that write too, with the same loud-reject pattern). *Found by Reviewer during code review (round 2).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Save→reload leg uses a pydantic JSON round-trip, not a live PgSaveRepository**
  - Spec source: context-story-153-24.md, AC4 / AC6 ("ADR-115 PostgreSQL save/load")
  - Spec text: "Saving an in-dungeon snapshot and reloading it preserves discovered_rooms, room_states, and each character's current_room"
  - Implementation: `TestReloadRoundTrip` saves via `GameSnapshot.model_validate_json(snap.model_dump_json())` — the exact serialization the PG persistence path round-trips — rather than standing up a real `PgSaveRepository` (the test factory's repository is a `MagicMock(spec=SaveRepository)`)
  - Rationale: The AC4 risk is whether the *populated* fields survive serialization; `current_room` already has a model-level round-trip (`test_state_patch_current_room.py`), so the JSON round-trip after a real multi-turn write is the meaningful, hermetic guard. A PG-backed round-trip adds DB coupling without testing more of *this* story's behavior.
  - Severity: minor
  - Forward impact: If Dev finds the fields don't persist through the PG layer specifically (unlikely — plain pydantic fields), a PG-backed assertion can be added in GREEN.
- **No dedicated "fail loud on malformed room id" test**
  - Spec source: context-story-153-24.md, Technical Notes #5 (No silent fallbacks)
  - Spec text: "if a transition resolves a room id that isn't a legal room-graph node, fail loudly rather than silently skipping the write"
  - Implementation: Covered behaviorally (the write must not be silently skipped — `TestPlaytestReproduction`), but no test asserts a raise on an illegal node id.
  - Rationale: The apply seam has no room-graph node catalog threaded to it (it validates region names only), so "legal room-graph node" is not decidable there without a design change. Forcing a `raises` test would dictate an infeasible/over-scoped design. Logged as a Delivery Finding (Question) for Dev instead.
  - Severity: minor
  - Forward impact: If Dev threads the room catalog, a `raises` test should be added in GREEN.

### Dev (implementation)
- **No hard room-graph node-catalog validation at the write site (always-write in room-graph mode)**
  - Spec source: context-story-153-24.md, Technical Notes #5 (No Silent Fallbacks)
  - Spec text: "if a transition resolves a room id that isn't a legal room-graph node, fail loudly rather than silently skipping the write"
  - Implementation: `record_room_discovery` always records the transition when the world is in `navigation_mode == room_graph` (the seam-readable signal). It does NOT raise on a room id that isn't a legal room-graph node, because `_apply_narration_result_to_snapshot` is not threaded the world's room-graph node catalog (it only validates *region* names via `validate_region_name`). The No-Silent-Fallbacks intent — the bug being fixed — is met: the write is never silently skipped (`TestPlaytestReproduction` proves it fires from an empty `discovered_rooms`).
  - Rationale: Threading the room-graph node catalog into this seam for hard validation is a design change beyond this story's scope (TEA logged the same conclusion as a Delivery-Finding Question and a test deviation). The actual failure mode in the playtest finding was a silent *skip*, not a confabulated node id; closing the skip is the fix. Hard node-id validation can be a follow-up once the catalog is threaded.
  - Severity: minor
  - Forward impact: A follow-up that threads the room-graph node catalog could add a fail-loud raise + a `raises` test; nothing here blocks that.
- **`record_room_discovery` lives in `sidequest/game/room_movement.py`, not as a private helper in `narration_apply.py`**
  - Spec source: context-story-153-24.md, "Key Code Areas" + "Development Notes" #2
  - Spec text: "this is the natural home for an idempotent 'record entered room' helper the apply seam can call" (re: `room_movement.py`)
  - Implementation: Added a public `record_room_discovery(...)` to `sidequest/game/room_movement.py` (alongside the chargen-time `init_room_graph_location`, the existing `discovered_rooms` seeder) and call it from the `narration_apply.py` transition seam — rather than inlining a private helper next to `_apply_room_graph_transition_effects`.
  - Rationale: Reuse-first + cohesion — the runtime room-axis writer belongs with the chargen-time room-axis writer it mirrors; keeps the apply seam thin.
  - Severity: minor
  - Forward impact: None — additive public helper; no existing caller affected.
- **`room_states` seeded for the entered room only; `from_room` backfills `discovered_rooms` but not `room_states`**
  - Spec source: context-story-153-24.md, AC1 (both endpoints recorded) + AC2 (room_states seeded on entry)
  - Spec text: AC1 "must now show both the entrance and exp002.r2"; AC2 "On first entry to a room-graph room, snapshot.room_states[room_id] is initialized"
  - Implementation: Both endpoints (`from_room` + `to_room`) are dedup-appended to `discovered_rooms` (AC1), but a fresh `RoomState` is seeded only for `to_room` (the entered room, AC2). The `from_room` backfill exists only to record that the actor was there (the entrance case where it was never recorded); its mechanical state, if any, was/will be seeded when it was entered.
  - Rationale: AC2 scopes room_states seeding to the *entered* room. Seeding a bare empty `RoomState` for every `from_room` would create empty entries with no behavioral need and is not required by any AC; avoiding it keeps room_states meaningful (a key exists because something entered/lives there).
  - Severity: minor
  - Forward impact: If forensics later wants a RoomState for every discovered room, the entrance-only gap is a one-line addition; no field-shape change.
- **(Rework rt#1) Room-axis write now structurally validates `result.location` (amends the first deviation above) — reuses `region_entry_rejected_span` for the room rejection rather than a dedicated span**
  - Spec source: Reviewer SEC-1 (session `## Reviewer Assessment`); context-story-153-24.md Technical Note #5
  - Spec text: SEC-1 — "Gate the room write on `validate_region_name(result.location)` ... emit a rejection span ... OR inline the same structural check"
  - Implementation: Added `validate_region_name(result.location)` at the room-graph call site (`narration_apply.py`), mirroring the region-axis filter (Story 45-16). On invalid (bracketed/multiline/>80-char), the room write is SKIPPED and a rejection is emitted via the existing `region_entry_rejected_span` with `caller_path="narration_apply.room_graph_discovery"` + a `room.entry_rejected` warning log — rather than adding a new dedicated `room.entry_rejected` span. `old_loc` (the actor's already-accepted current position) is not re-validated; only the new `result.location` is. Also hardened `record_room_discovery` against a `from_room == to_room` double-append (Reviewer LOW).
  - Rationale: Reuse-first — `region_entry_rejected_span` is already imported and the rejection is a rare error path, not a core mechanical decision needing its own dashboard widget; `caller_path` makes it attributable to the room path on the GM panel. This supersedes the first deviation's "always-write is sufficient" conclusion: the node-catalog *membership* check remains infeasible/deferred, but the *structural* hygiene the region axis uses is now applied (the previously-unguarded gap the reviewer flagged).
  - Severity: minor
  - Forward impact: If a future reviewer wants a dedicated `room.entry_rejected` span (distinct GM-panel lane from region rejections), it is a trivial additive follow-up; the `caller_path` already distinguishes the source today.

### Reviewer (audit)
- **TEA #1 (JSON round-trip vs live PgSaveRepository)** → ✓ ACCEPTED by Reviewer: `pg/snapshot.py` persists via `model_dump_json()` (confirmed by the security scan), so `GameSnapshot.model_validate_json(snap.model_dump_json())` exercises the exact serialization the PG path round-trips. PG coupling would add DB setup without testing more of *this* story's behavior. Sound.
- **TEA #2 (no fail-loud-on-malformed-room-id test)** → ✓ ACCEPTED by Reviewer (for the node-catalog version only): a *node-membership* raise is infeasible at this seam (no catalog threaded). BUT this acceptance does not extend to *structural* hygiene — the cheap `validate_region_name` guard the region axis uses IS feasible and is now required via finding SEC-1; a guard test must be added in the red rework.
- **Dev #1 (no hard node-catalog validation; always-write in room-graph mode)** → ✗ FLAGGED by Reviewer: the node-catalog half is sound (infeasible here), but the deviation's conclusion — "treat always-writing-in-room-graph-mode as sufficient" — overlooks the structural guard (`validate_region_name`, reject bracketed/multiline/too-long) that the sibling region axis already applies (Story 45-16) and that is already imported in this file. "Never silently skip" was satisfied; "never write narrator garbage into the forensics accumulator" was not. Reopens the Story 45-16 leak class on `discovered_rooms`. See SEC-1 (HIGH).
- **Dev #2 (`record_room_discovery` lives in `room_movement.py`)** → ✓ ACCEPTED by Reviewer: correct reuse-first cohesion — the runtime room-axis writer sits beside the chargen-time `init_room_graph_location` it mirrors, keeping the apply seam thin. Matches the context doc's own guidance.
- **Dev #3 (`room_states` seeded for entered room only; `from_room` backfills `discovered_rooms` only)** → ✓ ACCEPTED by Reviewer: AC2 scopes seeding to the entered room; not minting empty `RoomState` entries for every `from_room` keeps `room_states` meaningful. Defensible and consistent with AC1/AC2 as written.
- **Dev "(Rework rt#1)" (room-axis write now structurally validates `result.location`; reuses `region_entry_rejected_span`)** → ✓ ACCEPTED by Reviewer (round 2): this directly implements SEC-1 — `validate_region_name(result.location)` now guards the room write, mirroring the region axis (Story 45-16). Reusing `region_entry_rejected_span` with `caller_path="narration_apply.room_graph_discovery"` is sound reuse for a rare error path (the `caller_path` distinguishes it on the GM panel); a dedicated `room.entry_rejected` span is a fine optional follow-up but not required. The round-1 FLAG on **Dev #1** is hereby **RESOLVED** — the structural-hygiene gap it identified is closed; the node-catalog *membership* check remains a deferred-and-accepted follow-up.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/game/room_movement.py` — new public `record_room_discovery(snap, *, character_id, from_room, to_room)`: dedup-appends both endpoints to `discovered_rooms`, seeds `room_states[to_room]` (no clobber of Story 45-43 container/prop state), sets the acting character's `current_room`, and emits the `room.discovered` span. Runtime counterpart to the chargen-time `init_room_graph_location`.
- `sidequest-server/sidequest/telemetry/spans/movement.py` — new `room.discovered` span (`SPAN_ROOM_DISCOVERED` + `SpanRoute` + `room_discovered_span` context manager) carrying `room_id`, `newly_discovered` (first-entry vs backtracking), `discovered_count`, `character`. Exported via `__all__` (re-exported through `sidequest.telemetry.spans`).
- `sidequest-server/sidequest/server/narration_apply.py` — wired the call into the `if result.location:` transition seam (right after the room-graph nav-mode is resolvable). Gated on `cartography.navigation_mode == room_graph` (NOT `discovered_rooms` non-empty — the catch-22 TEA flagged) and a genuine transition (`old_loc is not None and result.location != old_loc`).

**How it's wired (production path):** the 153-24 tests drive the real `WebSocketSessionHandler._execute_narration_turn` → `_apply_narration_result_to_snapshot` seam; `record_room_discovery` is called from inside that seam, so the room axis is written on every real room-graph dungeon transition (not a unit-tested helper in isolation).

**Tests:** 11/11 passing (GREEN) — `tests/server/test_153_24_room_state_persistence.py`. RED→GREEN confirmed (was 10 failed / 1 passing pre-fix). Sibling regression green: `test_71_15_room_graph_movement_side_effects`, `test_room_graph_init`, `test_container_retrieval_state`, `tests/dungeon/test_persistence`, `tests/integration/test_dungeon_scene_advance_107_1` (49 passed / 3 skipped), full telemetry suite (417 passed). Full server suite: 262 failed / 13373 passed / 117 errors — verified against a stashed-clean tree (272 failed / 13363 passed / 117 errors) to prove my change fixes exactly the 10 target tests and introduces zero regressions; the remaining failures/errors are pre-existing base-branch content-pack drift (see Delivery Findings).

**Branch:** `feat/153-24-dungeon-room-state-persist` (sidequest-server)

**Handoff:** To verify phase (TEA / The Architect).

### Dev Rework (round-trip 1 — Reviewer REJECT addressed)

**SEC-1 [HIGH] — FIXED.** The room-axis write now applies the same structural hygiene as the region axis (Story 45-16): `validate_region_name(result.location)` is called at the room-graph call site (`narration_apply.py`); a bracketed/multiline/>80-char narrator location is rejected loudly (`region_entry_rejected_span` with `caller_path="narration_apply.room_graph_discovery"` + a `room.entry_rejected` warning) and the room write is skipped — so narrator asides can no longer pollute `discovered_rooms`/`room_states`. This closes the Story 45-16 leak class on the new accumulator and keeps AC4/AC6 forensics trustworthy.

**LOW [EDGE] — FIXED.** `record_room_discovery` now guards the `from_room == to_room` double-append (re-tests membership before appending `to_room`).

**New tests (rework):** `TestMalformedLocationRejected::test_bracketed_aside_not_recorded_on_room_axis` and `::test_multiline_location_not_recorded_on_room_axis` — both assert the garbage location is absent from `discovered_rooms`/`room_states`, `current_room` stays `None`, and no `room.discovered` span fires.

**Files changed (rework):**
- `sidequest/server/narration_apply.py` — SEC-1 structural-validation gate around the room write.
- `sidequest/game/room_movement.py` — `from_room == to_room` idempotency guard.
- `tests/server/test_153_24_room_state_persistence.py` — 2 new SEC-1 guard tests.

**Tests (post-rework):** 13/13 GREEN (11 original + 2 SEC-1 guards) — `tests/server/test_153_24_room_state_persistence.py`. Sibling regression green: `test_71_15_room_graph_movement_side_effects`, `test_room_graph_init`, `test_container_retrieval_state`, `test_region_validation`, `tests/dungeon/test_persistence`, `tests/integration/test_dungeon_scene_advance_107_1`, `tests/telemetry/test_routing_completeness` (81 passed / 3 skipped). Lint clean (ruff).

**Handoff:** Back to review (Reviewer / The Merovingian).

## Round 1 — Subagent Results (superseded by round 2 below)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — lint pass, 11/11 story + 49/49 sibling green, 0 smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge domain assessed by Reviewer ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — silent-failure domain assessed by Reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test domain assessed by Reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — doc domain assessed by Reviewer ([DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type domain assessed by Reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 3 (1 medium-conf, 2 low-conf) | confirmed 1 (SEC-1, upgraded HIGH), deferred 1 (resource-exhaustion → same root as SEC-1), dismissed 1 (pre-existing `character_locations`, not this diff) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity domain assessed by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rule domain assessed by Reviewer ([RULE]) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` and assessed directly by Reviewer)
**Total findings:** 1 confirmed (HIGH, blocking), 1 deferred (folds into the confirmed root cause), 1 dismissed (pre-existing, out of diff)

## Round 1 — Reviewer Assessment (REJECTED — superseded by rework rt#1; see round 2 below)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SEC][RULE] | **SEC-1** — narrator-emitted `result.location` is written to the room-axis accumulators (`discovered_rooms`, `room_states` key) with no structural hygiene guard, while the sibling region axis applies `validate_region_name` 11 lines below. Reopens the Story 45-16 leak (`(aside — narrator brief)` polluting `discovered_regions`) on the new `discovered_rooms` accumulator, defeating this story's own AC4/AC6 ("forensics/reload sees the REAL dungeon"). | `narration_apply.py:4187-4193`, `room_movement.py:55-59` | Gate the room write on `validate_region_name(result.location)` (already imported at `narration_apply.py:63`; reject bracketed/multiline/>80-char and emit a rejection span — mirror line 4202), OR inline the same structural check inside `record_room_discovery` so the public helper is safe regardless of call site. Add a test: a bracketed/multiline narrator `location` in room-graph mode must NOT land in `discovered_rooms`/`room_states`. |
| [LOW] [EDGE] | Latent idempotency hole: `record_room_discovery` double-appends when `from_room == to_room` on an undiscovered room. Not live (sole caller gates `!= old_loc`), but the public helper's contract has a gap. | `room_movement.py:55-59` | Dedup-guard the `to_room` append, or early-return when `from_room == to_room`. Fold into the SEC-1 rework. |

### Rule Compliance (python.md lang-review — reviewer-checked, rule_checker disabled)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Silent exception swallowing | PASS | No `try/except` in the new code; the OTEL span uses `with` (room_movement.py:70). |
| 2 | Mutable default args | PASS | `record_room_discovery`/`room_discovered_span` take no mutable defaults; all params keyword-only scalars. |
| 3 | Type annotations at boundaries | PASS | `record_room_discovery(snap: GameSnapshot, *, character_id: str, from_room: str, to_room: str) -> None`; `room_discovered_span` fully annotated. |
| 4 | Logging coverage/correctness | PARTIAL → SEC-1 | New code emits an OTEL span but does not log/reject a malformed narrator location; that omission is exactly SEC-1. |
| 5 | Path handling | N/A | No filesystem paths. |
| 6 | Test quality | PASS | 11 tests drive the real `_execute_narration_turn` seam; specific value assertions (membership, `.count()==1`, `isinstance`, `current_room ==`, span attrs); re-entry tests drive real transitions so they fail RED before the fix (no false-green). |
| 7 | Resource leaks | PASS | Span acquired via `with room_discovered_span(...)` context manager. |
| 8 | Unsafe deserialization | N/A | No pickle/eval/yaml on input; only `GameSnapshot.model_validate_json` in tests (trusted pydantic). |
| 9 | Async pitfalls | PASS | `record_room_discovery` is sync, no blocking I/O; called from the async seam without `await` (correct — it is not a coroutine). |
| 10 | Import hygiene | PASS | Local import of `record_room_discovery` at the call site mirrors the file's existing `process_room_entry` local import (narration_apply.py:4071); `__all__` updated in both modules; `from .movement import *` re-export is pre-existing. |
| 11 | Input validation at boundaries | **FAIL → SEC-1** | Narrator-emitted `result.location` (an external/LLM boundary) reaches `discovered_rooms`/`room_states` unvalidated. This is the blocking finding. |
| 12 | Dependency hygiene | N/A | No dependency changes. |
| 13 | Fix-introduced regressions | N/A | First implementation pass; no prior fix diff to re-scan. |

### Dispatch-tagged observations (all 8 tags; 7 subagents disabled → reviewer-assessed)

- **[SEC]** CONFIRMED → SEC-1 (HIGH). Security subagent flagged the missing `validate_region_name` guard (medium confidence, category injection but clarified: no executable sink — state corruption). I **upgraded to HIGH** on the Story 45-16 precedent (a documented real-playtest leak on the sibling axis) and because it defeats the story's own forensics AC. Security's resource-exhaustion finding (CWE-400, low conf) shares this root cause and is folded in. Security's third item (pre-existing unguarded `character_locations[actor]` at line 4105) is **dismissed for this PR** — the diff does not touch line 4105 and that single-slot write is the established trust model; SEC-1 is specifically about the *accumulators* (growing list/dict) that the region axis guards.
- **[RULE]** CONFIRMED → SEC-1. python.md #11 (input validation at boundaries) fails on the same line. Corroborates [SEC].
- **[EDGE]** Reviewer-assessed: the `from_room == to_room` double-append (LOW, latent — sole caller gates it). `old_loc is None` is handled by the call-site gate. `character is None` is handled (no crash). `newly_discovered` is captured BEFORE the appends (room_movement.py:55) so the first-vs-re-entry flag is correct on every branch — VERIFIED, evidence: room_movement.py:55 precedes the appends at :56-59.
- **[SILENT]** Reviewer-assessed: no swallowed exceptions in the new code. One silent no-op — `character is None` → `current_room` not set (room_movement.py:66-68) — but this is parity with the sibling `_apply_room_graph_transition_effects` (narration_apply.py:3594-3596) and the actor is an internal invariant (must exist). Acceptable. The *only* silent-skip concern is the unvalidated write, which is SEC-1 (a write-anything, not a swallow).
- **[TEST]** Reviewer-assessed VERIFIED good: wire-first against the real seam; `_execute_narration_turn` (websocket_session_handler.py:1047 → :1177) genuinely reaches the apply path; no vacuous assertions. **Gap:** no test covers the malformed-location guard — TEA must add it as part of the SEC-1 red rework.
- **[DOC]** Reviewer-assessed VERIFIED good: docstrings on `record_room_discovery`/`room_discovered_span` accurately describe behavior (both-endpoints append, no-clobber, span attrs); the inline comment at narration_apply.py:4173-4182 correctly explains the gate choice. No stale/misleading comments.
- **[TYPE]** Reviewer-assessed VERIFIED good: room ids are `str` consistent with the existing `discovered_rooms: list[str]` / `room_states: dict[str, RoomState]` field types (session.py); `RoomState(room_id=to_room)` constructs the typed model (not a bare dict); span attrs are scalars. No new stringly-typed API beyond the pre-existing room-id-as-str convention.
- **[SIMPLE]** Reviewer-assessed VERIFIED good: `_is_room_graph_world` mirrors the adjacent `_is_region_mode_world` (2-line structural parallel — acceptable, aids readability over a shared helper). No dead code, no over-engineering, helper is minimal.

### Devil's Advocate

Assume this code is broken. The narrator is an LLM; `result.location` is whatever it emits, and LLMs emit asides, stage directions, and run-on scene headers — the project has the receipts: Story 45-16 exists *because* `(aside — narrator brief)` leaked into `discovered_regions` during Playtest 3. This change wires that same untrusted string straight into `discovered_rooms` and into a `room_states` dict key with no filter, then serializes it to Postgres and broadcasts it to every client. A confused narrator emitting `"(I should describe the crypt now)"` as the location does not error, does not get rejected — it becomes a "discovered room" forever, and a forensics reviewer reconstructing the crawl sees a hallucinated aside listed beside `exp002.r2`. That is the precise failure this story was opened to eliminate ("forensics/reload sees the REAL dungeon"); the fix half-delivers it — the room axis is now non-empty (good) but is not *trustworthy* (bad). A malicious player exploiting the documented `narrator_hints` ADR-047 bypass (MEMORY.md) could attempt to steer `result.location` into multi-kilobyte strings; each distinct one appends to an unbounded `list[str]`, inflating every subsequent snapshot write and client payload — a slow resource-exhaustion path the region axis bounds via the 80-char `validate_region_name` cap and this axis does not. A stressed run would also see the `from_room == to_room` helper path double-append if any future caller forgets the `!= old_loc` gate. None of these are executable-code injection — everything lands in typed pydantic fields and bound SQL parameters, so there is no RCE — but "state corruption of the exact accumulator the story exists to make trustworthy" is a real defect, not a nit. The good news: the remedy is already in the file — `validate_region_name` is imported at line 63 and used at line 4202 — so closing this is one guard call plus a test, not a redesign.

**Data flow traced:** narrator `result.location` (LLM output) → `_apply_narration_result_to_snapshot` → `record_room_discovery` → `snapshot.discovered_rooms` / `room_states` / `Character.current_room` → `model_dump_json()` → Postgres bound param + client broadcast. Safe from injection (typed fields, no SQL/shell/HTML/eval sink); **unsafe from content hygiene** (no `validate_region_name` guard) — SEC-1.
**Pattern observed:** GOOD — `record_room_discovery` correctly mirrors the chargen-time `init_room_graph_location` dedup-append (room_movement.py:30-56); the room-graph gate correctly mirrors `_is_region_mode_world` (narration_apply.py:4183-4186). BAD — it mirrors the *write* of the region axis but not its *guard*.
**Error handling:** `character is None` no-ops gracefully (parity with sibling); the call-site gate handles `old_loc is None` and same-room re-entry; the missing case is malformed `result.location` (SEC-1).

**Handoff:** Back to TEA (The Architect) for red rework — add the structural-guard test for SEC-1; Dev then implements `validate_region_name` (or inline structural check) on the room-axis write and hardens the `from_room == to_room` edge.

## Subagent Results

(Round 2 — re-review of rework rt#1. Same enabled set: preflight + security; 7 disabled and reviewer-assessed.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — lint pass, 13/13 story + 79 sibling green (3 pre-existing skips), 0 smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge domain assessed by Reviewer ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — silent-failure domain assessed by Reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test domain assessed by Reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — doc domain assessed by Reviewer ([DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type domain assessed by Reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 1 residual (low-conf, pre-existing) | SEC-1 verified CLOSED; residual line-4105 `character_locations` dismissed (pre-existing, out of diff, non-blocking) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity domain assessed by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rule domain assessed by Reviewer ([RULE]) |

**All received:** Yes (2 enabled subagents returned for the re-review; 7 disabled via `workflow.reviewer_subagents` and assessed directly by Reviewer)
**Total findings:** 0 confirmed-blocking, 1 dismissed (pre-existing line-4105, out of scope) — the round-1 HIGH (SEC-1) and LOW are both verified FIXED

## Reviewer Assessment

**Verdict:** APPROVED

Round-1 REJECT findings are both resolved by rework rt#1, independently re-verified:

- **[PRE]** Preflight clean on the rework: `ruff` pass; 13/13 story tests GREEN (11 original + 2 new SEC-1 guards); 79 sibling regressions GREEN (3 pre-existing skips); 0 smells.
- **[SEC]** **SEC-1 (was HIGH) — CLOSED.** The security re-scan adversarially traced that `record_room_discovery` (the writer of `discovered_rooms`/`room_states`/`current_room`) is reachable ONLY via the `else` (valid) branch; a bracketed/multiline/>80-char `result.location` is rejected by `validate_region_name` (narration_apply.py:4199), emits `region_entry_rejected_span` + a `room.entry_rejected` warning (loud, not silent), and is skipped. `discovered_rooms` is now bounded identically to `discovered_regions`. The 2 new guard tests are genuine regression catches (without the gate, the garbage lands in `discovered_rooms` and they fail). VERIFIED — evidence: narration_apply.py:4199 (`is_valid_room, _ = validate_region_name(result.location)`), record call gated in `else` at the room-graph block; tests `TestMalformedLocationRejected::*`.
- **[RULE]** python.md #11 (input validation at boundaries) now **PASS** — the narrator-output boundary is validated before the accumulator write. All other python.md checks remain PASS (no bare excepts, no mutable defaults, full type annotations, `with`-scoped span, `__all__` updated, no star-import additions).
- **[EDGE]** **LOW (from_room == to_room double-append) — FIXED.** `record_room_discovery` now re-tests `to_room not in snap.discovered_rooms` before the second append (room_movement.py). VERIFIED — evidence: the `if newly_discovered and to_room not in snap.discovered_rooms:` guard.
- **[SILENT]** Reviewer-assessed: the rework's skip-on-invalid is LOUD (rejection span + `logger.warning`), not a swallow. No new silent paths. The `character is None` no-op (current_room) remains parity-with-sibling. PASS.
- **[TEST]** Reviewer-assessed: 2 new tests assert garbage absent from `discovered_rooms`/`room_states`, `current_room is None`, and no `room.discovered` span — specific, non-vacuous, drive the real seam. Genuine regression guards. PASS.
- **[DOC]** Reviewer-assessed: the new gate carries an accurate, thorough comment explaining the Story 45-16 parity and the "fail loud, not silent-skip-of-valid-moves" distinction. No stale/misleading comments. PASS.
- **[TYPE]** Reviewer-assessed: `validate_region_name` returns `tuple[bool, str | None]`, unpacked correctly; no new stringly-typed surface. PASS.
- **[SIMPLE]** Reviewer-assessed: the rework reuses `validate_region_name` + `region_entry_rejected_span` (already imported) rather than adding new infra — minimal, reuse-first. The double `validate_region_name` call (room block + region block) is a negligible pure-function recompute; acceptable. PASS.

### Devil's Advocate (round 2)

I tried to defeat the fix. Can garbage still reach the forensics accumulator? No — `record_room_discovery` is in the `else` arm; the only way to skip validation is to skip the whole room block, which also skips the write. Can a valid-looking-but-malicious string slip through? Only strings that pass `validate_region_name` (≤80 chars, no newline, no bracket prefix) — the same bar the region axis trusts, so no asymmetry remains. Could the guard wrongly reject a legitimate room id? The test room ids ("The Crypt") and the real playtest id ("exp002.r2") are short, unbracketed, single-line — all pass; the 80-char cap is generous for room names. Does rejecting leave broken state? No — on reject, the actor simply stays at `old_loc` on the room axis (consistent, recoverable), and the pre-existing `character_locations` write is unchanged (and shared with the region axis). Is there a double-span-emit in room-graph mode (room block + region block both rejecting)? Yes, but both are correct, distinguishable by `caller_path`, and harmless telemetry — not a defect. I could not find a path that reopens SEC-1 or introduces a new blocking issue.

**Data flow traced:** narrator `result.location` → room-graph gate → `validate_region_name` → (invalid: reject span + warning, skip) / (valid: `record_room_discovery` → `discovered_rooms`/`room_states`/`current_room` → `model_dump_json()` → Postgres). Now safe from both injection AND content-hygiene pollution.
**Pattern observed:** the room axis now mirrors the region axis's write AND its guard (narration_apply.py:4199 vs 4227) — parity restored.
**Error handling:** malformed location → loud reject + skip; `old_loc is None` / same-room → gated out; `character is None` → graceful no-op.

**Handoff:** To SM (Morpheus) for finish-story.