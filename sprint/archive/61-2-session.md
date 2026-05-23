---
story_id: "61-2"
jira_key: "none"
epic: "61"
workflow: "tdd"
---
# Story 61-2: Extend snapshot slim — seven growing fields

## Story Details
- **ID:** 61-2
- **Epic:** 61 (Bounded Narrator Prompt — Slim Snapshot + Wire RAG)
- **Jira Key:** none (SideQuest personal tracker)
- **Workflow:** tdd
- **Stack Parent:** none

## Summary

Extend `_PHASE_B_DROP_FIELDS` at `sidequest-server/sidequest/server/session_helpers.py:64` to cover the seven snapshot fields that ADR-110 Phase B missed: `room_states`, `journal`, `npcs`, `known_facts`, `footnotes`, `belief_state`, `location_descriptions`. Each field gets one of three per-field treatments — drop / bounded projection / RAG route — per the decision table in epic 61 context document.

This is the root cause of the 2026-05-23 cost-runaway incident (~$313/48h). Seven unslimmed fields flow into Valley/Recency `system_blocks` uncached and unprojected, multiplied by up to 8 tool-loop iterations per turn.

## Scope: Per-Field Decisions

| Field | Decision | Rationale |
|---|---|---|
| `room_states` | Project to current-room + adjacent rooms only | Full retrievable history is dungeon-graph territory (ADR-055), not narrator-prompt territory |
| `journal` | Drop entirely | ADR-100 journal pipeline has its own retrieval path; entries are RAG-shaped, not dump-shaped |
| `npcs` | Project to NPCs-in-current-scene only | Perception filter (ADR-104) already isolates in-scene roster; others route through RAG |
| `known_facts` | Route through RAG | Per-NPC × per-clue cardinality grows fast; RAG-shaped per ADR-053 belief/clue graph |
| `footnotes` | Drop entirely from snapshot dump | Already double-rendered (snapshot + dedicated section, ADR-100); drop one |
| `belief_state` | Route through RAG (in-scene beliefs only) | ADR-053 belief propagation; same shape as `known_facts` |
| `location_descriptions` | Project to active POI only | ADR-109's growth vector; LOCATION_DESCRIPTION message already carries active-POI text — don't duplicate in `<game_state>` |

## Workflow Tracking
**Workflow:** tdd
**Phase:** green
**Phase Started:** 2026-05-23

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-23 | 2026-05-23 | - |
| red | 2026-05-23 | 2026-05-23 | - |
| green | 2026-05-23 | - | - |

## Red phase

### Per-field validation (validated against live code)

Top-level enumeration via `GameSnapshot.model_fields.keys()` (49 fields). Audit of the seven epic-named fields:

| Field | Top-level in GameSnapshot? | Reality | Decision (revised where applicable) |
|---|---|---|---|
| `room_states` | YES (`session.py:752`) | `dict[room_id, RoomState]` — keyed by room id, each carrying container retrieval state. Grows with rooms visited. | **Project to acting PC's current_room only.** `_build_turn_context` already reads only the current room at `session_helpers.py:627` — other room entries are pure carry. |
| `journal` | **NO** — not a snapshot field | Derived from `Character.known_facts` + event log via `JournalRequestHandler`. ADR-100 pipeline is event-log shaped. | **NO-OP for snapshot slimming.** Add regression guard so a future PR that materializes `journal` onto `GameSnapshot` fails fast. |
| `npcs` | YES (`session.py:600`) | `list[Npc]`, each with nested `belief_state`, `last_seen_location`, `last_seen_turn`. Grows with NPC roster. | **Project to in-scene only** (`Npc.last_seen_location == party_location(perspective=char_name)` or encounter participant). Also **drop nested `belief_state`** from surviving entries. |
| `known_facts` | **NO** — nested on `Character` (`character.py:100`) | `list[KnownFact]` per PC. Grows monotonically. Lives inside `characters[*].known_facts` in the dump. | **Project to tail K=8 per PC** (mirrors `persistence.py:889` journal-render pattern). Older facts ride via RAG (61-1 wiring). |
| `footnotes` | **NO** — not a snapshot field | Per-turn `NarrationResult.footnotes` (`orchestrator.py:452`) — event-log-bound, never persisted to snapshot. | **NO-OP for snapshot slimming.** Regression guard added. |
| `belief_state` | **NO** — nested on `Npc` (`session.py:175`) | `BeliefState` per Npc. Grows via gossip / belief-add. Lives at `npcs[*].belief_state` in the dump. | **Drop from each surviving `npcs` entry** in the dump. Belief-state is dispatch-side (gossip propagation, ADR-053), not prompt-side. `scenario_state.discovered_clues` also gets a parallel cap=12. |
| `location_descriptions` | **NO** — not a snapshot field | ADR-109 manifests ride out-of-band via `LOCATION_DESCRIPTION` WebSocket messages; loaded from `cookbook/assemble.py` at room change. No `snapshot.location_descriptions` field exists. | **NO-OP for snapshot slimming.** Regression guard added (matches the exact field-shaped name AND likely variants `location_description` / `location_entities`) so the 2026-05-19 ADR-109 → 2026-05-23 runaway pattern can't re-fire silently. |

**Top-line finding:** the epic preamble overstated the snapshot-bloat surface. Of the seven epic-named "growing fields," only `room_states`, `npcs`, `known_facts` (nested), `belief_state` (nested), and `scenario_state.discovered_clues` actually ride into `snapshot.model_dump()` today. The other three (`journal`, `footnotes`, `location_descriptions`) are real growing subsystems but route via separate channels; they cannot be driving the Valley/Recency cost via the snapshot path. This is a **non-blocking** finding — the cost-runaway diagnosis still stands on the four real bloat sources, and the regression guards lock the door behind the three out-of-band fields.

### Test file

- `sidequest-server/tests/server/test_61_2_snapshot_seven_field_projection.py` — 14 tests

### Failing tests (RED — assertion-level)

| Test | First line of failure |
|---|---|
| `test_room_states_projection_keeps_only_acting_pc_current_room` | `AssertionError: room_states projection failed: state_summary['room_states'] keys=['distant_room_1', 'distant_room_2', 'distant_room_3', 'distant_room_4', 'main_hall'] — expected exactly {'main_hall'}` |
| `test_npcs_projection_keeps_only_in_scene` | `AssertionError: npcs in-scene projection failed: names=['InScene_1', 'InScene_2', 'OffStage_1', 'OffStage_2', 'OffStage_3'], expected=['InScene_1', 'InScene_2']` |
| `test_npcs_projection_drops_belief_state_from_in_scene_entries` | `AssertionError: npc entry retains belief_state in state_summary: name='InScene_1' belief_state={'beliefs': [{'subject': 'victim', 'content': 'in-scene-belief-0-0', ...}]}` |
| `test_known_facts_truncated_to_tail_eight_per_pc` | `AssertionError: known_facts tail-K projection missing: PC has 25 facts in state_summary (expected ≤ 8)` |
| `test_scenario_state_discovered_clues_capped` | `AssertionError: discovered_clues cap missing: state_summary carries 30 entries (fixture seeded 30). Cap to ≤ 12` |
| `test_61_2_extra_byte_reduction_on_late_session_fixture` | `AssertionError: 61-2 extra reduction below acceptance gate: bytes_before=6376 bytes_after=6484 ratio=1.017 (gate: <=0.65)` (today's dump is actually larger than the post-Phase-A+B baseline because session_helpers performs `narrative_log` pop + party_formation/shared_world_delta merges that the baseline emulation doesn't account for — Dev should re-baseline if needed once projections land, but the gate value (≤0.65) is the right ask) |
| `test_prompt_game_state_bytes_span_carries_projection_counts` | `AssertionError: prompt.game_state.bytes span missing or wrong attribute 'room_states_dropped': got None, expected 4` |

### Passing tests (anchor / regression guards — would catch a future regression)

These 7 tests pass today because the conditions they assert are already true; they become live failure detectors once Dev's projection helpers run alongside an accidental anchor strip or a future ADR-109-style field addition.

| Test | Why it passes today |
|---|---|
| `test_journal_absent_from_state_summary` | `journal` is not a `GameSnapshot` field |
| `test_footnotes_absent_from_state_summary` | `footnotes` is not a `GameSnapshot` field |
| `test_location_descriptions_absent_from_state_summary` | `location_descriptions` is not a `GameSnapshot` field |
| `test_anchor_preserved_characters_after_projections` | `characters` is already preserved by Phase B |
| `test_anchor_preserved_quest_log_after_projections` | `quest_log` is already preserved |
| `test_anchor_preserved_npc_pool_after_projections` | `npc_pool` is already preserved |
| `test_npcs_projection_preserves_off_stage_names_in_npc_pool` | Fixture seeds the pool; pool currently survives untouched. Becomes a live assertion once Dev's projection runs — guards against the projection accidentally stripping `npc_pool` as well. |

### Open questions for Dev

1. **`is_in_scene` helper signature.** The `npcs` projection needs a deterministic predicate. Recommend union of two signals:
   - `npc.last_seen_location == snapshot.party_location(perspective=char_name)`
   - `encounter is not None and not encounter.resolved and npc.core.name in encounter.participants` (if the encounter model exposes participants — verify in `sidequest/game/encounter.py`)
   Extract as `_npc_in_scene(npc, snapshot, perspective)` so 61-5's architecture-gate test can pin it.

2. **`known_facts` window K.** Tests pick K=8 to mirror `persistence.py:889`. Confirm the journal pipeline (ADR-100) is happy with 8 — read `commit_known_fact.py` and `persistence.py:873-890` and either cite or revise. If Dev picks a different K, update the test fixture's tail expectation (`expected_tail = [f"fact #{i}" for i in range(17, 25)]`).

3. **`scenario_state.discovered_clues` ordering.** This is a `set[str]`. The cap test asserts size only — recency cannot be preserved without a parallel structure. If Dev wants recency ordering for clues, that's an ADR-053 follow-up; for now size-only is the contract.

4. **Byte-reduction baseline.** The current test fails at ratio=1.017 because the test's "baseline" computation doesn't fully emulate `session_helpers`' existing mutations (narrative_log pop, party_formation merge, shared_world_delta merge — these inflate the live dump slightly above the model-only baseline). Once 61-2 projections land, ratio should drop well below 0.65 on the late-session fixture; if it doesn't, Dev should re-baseline against the actual pre-61-2 `_state_summary` output rather than the model-dump-only emulation. Either approach validates the cost-reduction claim, but the test must be true RED before Dev starts.

5. **OTEL attribute names.** The test asserts four new attributes on the existing `prompt.game_state.bytes` span: `npcs_dropped`, `room_states_dropped`, `known_facts_truncated_total`, `clues_truncated`. If Dev prefers different names, update the test in lockstep — but they must be flat counts (Sebastien-readable on the GM panel).

6. **`npc_pool` exhaustiveness assumption.** The npcs projection's safety depends on `npc_pool` carrying identity for every NPC the projection might drop. Today the fixture seeds the pool by hand; in production `world_materialization` should be populating it. If it isn't, the projection has to be more conservative (e.g. keep last-K turns of NPCs in addition to in-scene).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Conflict** (non-blocking): the 57-5 anchor test `test_anchor_preserved_npcs_with_content` had an unrealistic fixture (NPCs with no `last_seen_location`). Under the 61-2 in-scene predicate, those NPCs are legitimately filtered out. Fixed by seating the fixture NPCs at the acting PC's location ("Main Hall"). The contract is unchanged — the fixture is now realistic. Affects `sidequest-server/tests/server/test_57_5_snapshot_slimming.py::_npc()` only. *Found by Dev when full-suite verification surfaced the regression.*
- **Improvement** (non-blocking): `Encounter`/`StructuredEncounter` exposes participants via `.actors[*].name` (`EncounterActor.name`), not a flat `participants: list[str]` field. TEA's open-question text said "if the encounter model exposes participants — verify in `sidequest/game/encounter.py`". Verified and used the actors path. No code change needed elsewhere; this is just documentation alignment. *Found by Dev during in-scene predicate implementation.*
- **Question** (non-blocking): the `room_states` projection emits an empty dict (`{}`) when the acting PC's `current_room_id` is blank or absent from `room_states`. This preserves the structural anchor (narrator gets "no room state" rather than "field missing"). If Reviewer thinks this should instead `pop("room_states", None)` to match Phase B's drop semantics, it's a one-line change — but the test contract asserts on `payload.get("room_states")` so the empty-dict choice is test-compatible AND signals "we ran the projection" to the GM panel. *Raised by Dev during projection design.*

### TEA (test design)
- **Conflict** (non-blocking): the epic's "seven growing fields" list mixes top-level snapshot fields with nested fields and with fields that aren't in the snapshot at all. Only `room_states` and `npcs` are top-level; `known_facts` and `belief_state` are nested (in `characters[*]` and `npcs[*]` respectively); `journal`, `footnotes`, and `location_descriptions` are NOT snapshot fields. The cost-runaway diagnosis stands on the four real bloat sources — but the epic context table needs correcting for future-reference accuracy. Affects `sprint/context/context-epic-61.md` §"Layer 2 — Snapshot slim (61-2)" table (cosmetic — recommend amending the per-field decision column to note "(nested on Character)" / "(nested on Npc)" / "(not a snapshot field; regression guard only)"). *Found by TEA during red-phase validation against `GameSnapshot.model_fields`.*
- **Improvement** (non-blocking): the test asserts that `npc_pool` carries every off-stage NPC's identity (gaslighting-doctrine fallback for the in-scene projection). If `world_materialization` does NOT exhaustively seed `npc_pool`, Dev will need a wider safety net (e.g., last-K-turns-mentioned). Recommend Dev verify pool seeding before landing the projection. *Found by TEA during fixture design.*
- **Question** (non-blocking): `prompt.game_state.bytes` span already fires per turn (story 57-5). 61-2's test asserts four new count attributes on the SAME span. If Dev would prefer a sibling span (`prompt.game_state.projections`) for separation of concerns, fine — update test. The single-span shape was chosen to keep the GM panel's existing visualization wiring intact. *Raised by TEA during OTEL test design.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

None yet.

## Implementation Notes

- Prerequisite story 61-1 (RAG wiring) landed at commit 06ad79c (2026-05-21); LoreStore is now wired into ToolContext in production. Fields marked "Route through RAG" are unblocked.
- Projection logic goes into `session_helpers.py` around the `snapshot.model_dump()` call (line 559).
- The `_PHASE_B_DROP_FIELDS` tuple at line 64 should be extended with dropped fields. Projected fields need bespoke helpers.
- ADR-110 §Audit method: grep narrator prompt assembly for snapshot field references to verify no silent fallbacks.
- ADR-110 §Implementation Notes: "The DROP list is reviewed at every PR that adds a `GameSnapshot` field going forward." 61-5 enforces this via test.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Cost-runaway root-cause story; per-field projections change `state_summary` shape that flows into the SDK call; every projection needs verifiable contract.

**Test Files:**
- `sidequest-server/tests/server/test_61_2_snapshot_seven_field_projection.py` — 14 tests (7 RED on production code, 7 anchor/regression guards)

**Story Context:**
- `sprint/context/context-story-61-2.md` — validated per-field decision table, open questions, AC table

**Tests Written:** 14 tests covering AC1–AC8 (8 ACs in the validated context document)
**Status:** RED (7 assertion-level failures on the production code path; 7 anchor/regression guards passing as defensive sentinels)

**Branch + commit:** `feat/61-2-snapshot-drop-list-seven-fields` @ `85b9792` — `test(61-2): RED — failing tests for seven-field snapshot projection`

**Handoff:** To Dev for green-phase implementation.

## Green phase

### Implementation

Added two helpers + one wiring call to `sidequest/server/session_helpers.py`:

1. **`_npc_in_scene(npc, snapshot, *, perspective)`** — predicate from TEA's open question #1. Union of `last_seen_location == party_location(perspective=perspective)` AND any NPC named in an unresolved encounter's `actors[*].name`. Encounter shape: `StructuredEncounter.actors: list[EncounterActor]` with `.name`.
2. **`_apply_phase_c_projections(snapshot, payload, *, perspective) -> dict[str, int]`** — mutates `payload` in place, returns the four count attributes for the OTEL span. Projections:
   - `room_states` → `{current_room_id: room_states[current_room_id]}` or `{}` if absent (empty dict preserves the structural anchor — narrator gets "no room state" rather than "field missing").
   - `npcs` → in-scene list via `_npc_in_scene`; each surviving entry pops `belief_state`.
   - `characters[*].known_facts` → tail-K=8 per PC.
   - `scenario_state.discovered_clues` → `sorted(clues)[:12]`.
3. Call site: between the gate-engagement redaction and the `party_formation`/`shared_world_delta` injection (so the projection sees only the canonical snapshot fields, not the merged-in delta sidecars).

OTEL: extended `prompt_game_state_bytes_span` call with `**_projection_counts`. The span signature already accepts `**attrs: Any` (story 57-5 wiring), so no telemetry-package change was needed.

### Resolution of TEA's open questions

1. **`_npc_in_scene` signature.** Implemented as documented. The encounter union uses `StructuredEncounter.actors[*].name` (not a separate `participants` field — encounter.py didn't expose one).
2. **`known_facts` window K.** Kept at 8. `persistence.py:889` uses the same tail-of-8 for journal renders; the journal pipeline (ADR-100) lives on the same Character.known_facts list, so K=8 here mirrors what the journal pipeline already truncates to.
3. **`discovered_clues` ordering.** Settled now (not deferred). Sort by clue id (the safe stable key). A future ADR-053 enrichment that wants recency ordering can replace `sorted(...)` with a parallel structure without touching the cap value.
4. **Byte-reduction baseline.** Test passed without re-baselining — the four projections produce a ratio well below 0.65 on the late-session fixture (5 rooms → 1, 5 NPCs with 4-belief BeliefStates each → 2 minimal entries, 25 known_facts → 8, 30 clues → 12).
5. **OTEL attribute names.** Used TEA's exact names: `room_states_dropped`, `npcs_dropped`, `known_facts_truncated_total`, `clues_truncated`. Stayed on the existing `prompt.game_state.bytes` span (no sibling span) to keep the GM panel's existing visualization wiring intact.
6. **`npc_pool` exhaustiveness.** Not a blocker — the test fixtures seed the pool by hand and the production `world_materialization` path is expected to seed it for materialized NPCs. The off-stage names dropped from `npcs` retain identity in `npc_pool` as long as the seeding stays exhaustive. Documented as a follow-up audit item; no defensive widening of the in-scene predicate.

### Regression handled

Updated `tests/server/test_57_5_snapshot_slimming.py::_npc()` to seat the fixture NPCs at `"Main Hall"` (the acting PC's location). The 57-5 anchor test `test_anchor_preserved_npcs_with_content` asserts "if the fixture seeds 2 NPCs, both survive the per-turn projection" — that contract still holds, but only when the fixture reflects a realistic post-narration state (NPCs with `last_seen_location` set). This is a fixture realism update, not a contract change.

### Verification

- 61-2 tests: **14/14 passing** (7 previously RED, 7 anchor/regression guards).
- 57-5 tests: 15/15 passing (1 fixture update, 0 contract changes).
- Full server suite: **7258 passed, 400 skipped, 0 failed.**
- `uv run ruff check .`: all checks passed.
- `uv run ruff format`: 1 file reformatted (the long block-comment in `_apply_phase_c_projections`).

### Branch + commit

- Branch: `feat/61-2-snapshot-drop-list-seven-fields`
- Commit: `0c043c8` — `feat(61-2): GREEN — Phase C snapshot projections + OTEL counts`
- Pushed: yes.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (green phase):**
- `sidequest-server/sidequest/server/session_helpers.py` — added `_npc_in_scene`, `_apply_phase_c_projections`, projection-counts kwargs to the `prompt.game_state.bytes` span; new `_KNOWN_FACTS_TAIL_K`/`_DISCOVERED_CLUES_CAP` constants.
- `sidequest-server/tests/server/test_57_5_snapshot_slimming.py` — `_npc()` fixture helper now defaults `last_seen_location="Main Hall"` so the 57-5 anchor contract holds under the new in-scene predicate.

**Files Changed (review-fix phase):**
- `sidequest-server/sidequest/server/session_helpers.py` — `_npc_in_scene` now takes `current_room: str | None` (no internal `party_location` call); `_apply_phase_c_projections` takes `current_room_id: str | None` (skips room_states/npcs projections when empty); dead `isinstance` defenses removed; docstring rewritten; `_build_turn_context` hoists `current_room_id` resolution + `actor_location_empty` warning above the projection seam.
- `sidequest-server/tests/server/test_61_2_snapshot_seven_field_projection.py` — added 2 tests for the gaslighting-skip behavior.

**Tests:** 17/17 61-2 GREEN; 7261/7661 full-suite GREEN.
**Branch:** `feat/61-2-snapshot-drop-list-seven-fields` @ `6f589f9` (pushed)

**Handoff:** To SM for finish.

## Review-fix phase

### Reviewer findings applied (same branch, one commit)

**Commit:** `6f589f9` — `fix(61-2): reviewer MUST-FIX + gaslighting-doctrine SHOULD-FIX`

**Fix 1 (MUST-FIX) — OTEL span fan-out.** `_npc_in_scene` no longer calls `snapshot.party_location(perspective=...)` internally; instead it accepts a `current_room: str | None` parameter resolved ONCE by the caller. `_build_turn_context` hoists the `current_room_id` resolution above the projection seam (single call) and the projection passes it into `_npc_in_scene`. Span fan-out drops from N+1 (one per NPC) to 1 per turn. The 45-13 room-state-injection block now reuses the same `current_room_id` instead of re-calling.

**Fix 2 (MUST-FIX) — Lying docstring + dead defenses.** Removed dead `isinstance(room_states, dict)`, `isinstance(npcs_payload, list)`, `isinstance(chars_payload, list)`, and `isinstance(char_entry, dict)` / `isinstance(entry, dict)` guards in the surviving branches — pydantic v2 enforces these shapes upstream. Kept `isinstance(scenario_payload, dict)` and `isinstance(clues, list)` because `scenario_state` is `Optional` (None or absent under `exclude_defaults`) and `discovered_clues` is dumped from a `set`. Rewrote the docstring to describe what the code actually does (and to call out the gaslighting-doctrine skip-on-empty-location ordering for Fix 3).

**Fix 3 (SHOULD-FIX, gaslighting-doctrine) — Projection-skip when actor location empty.** Moved the `actor_location_empty` warning to fire BEFORE `_apply_phase_c_projections`. `_apply_phase_c_projections` now accepts `current_room_id: str | None`; when it's None/empty the room_states and npcs projections noop (pass through original data — degraded location != "no NPCs exist") and the known_facts / discovered_clues projections still run (PC/scenario-scoped). The 45-13 block coalesces `None` to `""` immediately before its existing read.

### Tests

Two new tests added to `tests/server/test_61_2_snapshot_seven_field_projection.py` covering Fix 3:

- `test_projection_skips_room_states_and_npcs_when_actor_location_unresolvable` — clears `snap.character_locations` so `party_location(perspective=Alice)` returns None; asserts (a) `actor_location_empty` warning fires (caplog), (b) room_states retains all 5 rooms (not stripped), (c) npcs retains all 5 NPCs (not stripped).
- `test_projection_still_runs_known_facts_and_clues_when_actor_location_unresolvable` — same fixture; asserts the PC/scenario-scoped projections (tail-K facts, clue cap) DO run despite unresolvable location.

Both pass; full 61-2 file is now 17/17 (was 15/15).

### Verification

- **61-2 file:** 17/17 passing in 2.35s
- **Full suite:** `7261 passed, 400 skipped, 0 failed` in 32.66s (was 7259 — exactly +2 for the new tests)
- **Lint:** `ruff check sidequest/server/session_helpers.py tests/server/test_61_2_snapshot_seven_field_projection.py` — all checks passed
- **Format:** both files already formatted (no changes)

Note: ran `uv run ruff format .` on the full tree once and it reformatted 106 files — reverted those (unrelated to story scope), kept only the two intended files. The format/lint commands in `just server-fmt` operate repo-wide; future runs should scope to changed files.

### Out-of-scope (deferred to 61-7)

Per the review-fix prompt:
- `_npc_in_scene` annotation `npc: object` → `npc: Npc` — defer (folds into 61-7 cleanly).
- `payload["npcs"] = []` / `payload["room_states"] = {}` noise elimination — defer (cosmetic).
- Adversarial probe fixture cleanup (NIT) — defer.

### Delivery Findings — Dev review-fix

- **Improvement** (non-blocking): `just server-fmt` (`uv run ruff format .`) reformats the entire tree, dragging unrelated cosmetic changes into any commit if run from a clean repo. Scoping to changed files (`ruff format $(git diff --name-only)`) keeps commits surgical. Affects developer workflow only; no code change required. *Found by Dev when the post-fix format pass touched 106 files.*

## Verify phase

### Re-verification by TEA

- **Full suite (post-Dev):** `7258 passed, 400 skipped, 0 failed` in 23.76s on `0c043c8` — reproduces Dev's count exactly. No flake.
- **61-2 file in isolation:** 14/14 green, 5 runs in a row (2.35 / 2.38 / 2.36 / 2.41 / 2.40 seconds). No order-dependent failures. `discovered_clues` sort-by-id stability confirmed.
- **Adversarial probe added (1 test):** `test_npc_in_scene_predicate_divergence_from_list_npcs_in_scene_tool` — constructs an NPC with `last_seen_location="main_hall"` (acting PC's room) but `location="distant_chamber"` and `current_room="distant_chamber"`. Asserts the 61-2 contract: the NPC IS kept by `_npc_in_scene` even though `list_npcs_in_scene` (which uses `current_room`/`location`) would NOT consider it in-scene. **Divergence MEASURED; non-blocking.**
- **Full suite (post-probe):** `7259 passed, 400 skipped, 0 failed` in 27.19s. The +1 vs Dev's number is exactly the new probe test.
- **Branch + commit:** `feat/61-2-snapshot-drop-list-seven-fields` @ `fdf6578` — `test(61-2): adversarial _npc_in_scene divergence probe` (pushed locally; SM/Reviewer can push if needed).

### Verdict

**Ready for Reviewer.** No flake, no regression, no blocker. The predicate divergence the probe measures is real and known; it belongs to the 61-7 follow-up Architect proposed and does not affect the 61-2 cost-runaway fix.

### Delivery Findings — TEA verify

- **Improvement** (non-blocking): the `_npc_in_scene` predicate diverges from `list_npcs_in_scene` tool's scene resolution. 61-2 uses `last_seen_location`, the tool uses `current_room`/`location`. Three NPC fields signal scene membership today (`last_seen_location`, `location`, `current_room`); narrator prose updates `last_seen_location` but structured state updates may set `location`/`current_room`. This is the 61-7 unification target. Affects `sidequest-server/sidequest/server/session_helpers.py:84-115` and `sidequest-server/sidequest/agents/tools/list_npcs_in_scene.py:102`. *Found by TEA during verify-phase adversarial probe; confirmed by passing test.*
