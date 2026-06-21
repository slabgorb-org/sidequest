# Story Context: 153-24 — [DUNGEON-ROOM-STATE-NOT-PERSISTED] Persist discovered_rooms/current_room/room_states as the dungeon graph is walked

## Story Metadata
- **Story ID:** 153-24
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** Bug
- **Points:** 3
- **Workflow:** TDD
- **Repositories:** sidequest-server
- **Priority:** P2

## Problem Statement

After a player crosses into the dungeon, the snapshot reflects movement on **one** axis but not the other:

- `current_region` advances correctly (entrance → exp002.r2).
- `dungeon.map_emitted` counts discovered regions (1/10 → 2/15), so the region graph is tracking the walk.

But the **room-tracking** fields stay empty the whole time:

- `snapshot.discovered_rooms: []`
- `snapshot.room_states: {}`
- `characters[].current_room: None`

The room-graph mutation is emitted to the map handler (region-graph axis) but is never written into the persisted room-tracking fields. The consequence is that **forensics and cold reload see an empty dungeon**: a save taken mid-crawl loads with no room history, no per-room mechanical state, and no per-character room position — even though the party demonstrably moved. This likely **blocks a clean reload of an in-dungeon save** (ADR-133 reconnect rebuilds from persisted state, and the room axis is blank).

Verbatim finding (playtest): "after crossing into the dungeon, snapshot shows current_region correctly advancing entrance → exp002.r2 and dungeon.map_emitted counting 1/10 → 2/15, BUT snapshot.discovered_rooms: [], room_states: {}, and characters[].current_room: None the whole time. The room-graph mutation is emitted to the map handler but not written to the persisted room-tracking fields → forensics/reload sees an empty dungeon."

## Root Cause Direction

There are **two distinct location axes** in the snapshot, and only one of them is being written on dungeon traversal:

1. **Region graph axis (working).** `snapshot.discovered_regions` / `current_region` and `character_locations[actor]` are updated each turn in `narration_apply.py`, and `map_emit.py::_maybe_emit_dungeon_map()` reads `snapshot.discovered_regions` to build the `DUNGEON_MAP` payload and fire the `dungeon.map_emitted` span. This axis is healthy.

2. **Room-graph navigation axis (ADR-055, broken).** `snapshot.discovered_rooms` (`session.py:1021`), `snapshot.room_states` (`session.py:1030`), and `Character.current_room` (`character.py:182`) are the persistence fields for the room-graph crawl. On a dungeon transition, `narration_apply.py` (lines ~4081–4116) **gates** room-graph side-effects on `snapshot.discovered_rooms` being non-empty and fires trope/item side-effects via `_apply_room_graph_transition_effects()` — but it **never appends the entered room to `discovered_rooms`, never seeds `room_states[new_room]`, and never sets `character.current_room`.** The only production write of `room_states[...]` is at `narration_apply.py:5088` (Story 45-43 container-retrieval state), which is a different concern (container lifecycle, keyed by location), not room-graph discovery.

So the gap is precise: the room-graph transition seam updates `character_locations` + side-effects but forgets to record that the room was discovered, what its mechanical state is, and where each character now stands. The fix **wires the existing transition seam to write the existing fields** — it does not introduce a new room-tracking system.

The fix should make the write the single source of truth for the room axis on every dungeon transition (first-entry append + idempotent re-entry), and ensure the persistence/serialization path (ADR-115 PostgreSQL save/load) round-trips those fields so a reloaded in-dungeon save is non-empty.

## Acceptance Criteria

1. **Entered dungeon rooms are recorded in `discovered_rooms`:**
   - When a room-graph transition resolves a new room (`result.location != old_loc` in `narration_apply.py`), the entered room id is appended to `snapshot.discovered_rooms` if not already present (idempotent — re-entering a known room does not duplicate it).
   - The entrance room is present in `discovered_rooms` from first entry (the playtest case where the field was `[]` while standing in `exp002.r2` must now show both the entrance and `exp002.r2`).

2. **Per-room mechanical state is seeded in `room_states`:**
   - On first entry to a room-graph room, `snapshot.room_states[room_id]` is initialized with a `RoomState` (the model already exists; do not change its shape unless the round-trip requires it).
   - Re-entry does not clobber existing `room_states[room_id]` (preserve container/lifecycle state already written by the Story 45-43 path at `narration_apply.py:5088`).

3. **Per-character room position is tracked:**
   - The acting character's `current_room` (`character.py:182`) is set to the entered room id on a room-graph transition, and reflects the room the character currently stands in across the crawl.

4. **Reload round-trips the room axis (ADR-133 / ADR-115):**
   - Saving an in-dungeon snapshot and reloading it preserves `discovered_rooms`, `room_states`, and each character's `current_room` (no longer empty after a cross). Forensics on the reloaded save sees the real dungeon state.

5. **OTEL watcher visibility (telemetry AC):**
   - A new watcher span fires on the room-discovery write — e.g. `room.discovered` (or `dungeon.room_recorded`) with `{room_id, newly_discovered: bool, discovered_count, character}` — emitted from the same seam that appends to `discovered_rooms`, so the GM panel can confirm the room axis advanced (not just the region axis). This complements the already-live `dungeon.map_emitted` (`map_emit.py:940`) and `room.transition_tick_span` (telemetry side-effects) spans, which read/operate on the region and side-effect axes respectively and do not prove the room axis was written.
   - The span MUST distinguish first-discovery from re-entry so the panel can tell genuine exploration from backtracking.

6. **Wiring / integration-test AC (reaches production code path):**
   - An integration test drives a multi-turn dungeon traversal through the real narration-apply seam (not a unit test of a helper in isolation) and asserts that after crossing `entrance → exp002.r2`, the snapshot has non-empty `discovered_rooms` (entrance + `exp002.r2`), a populated `room_states` entry for the entered room, and the acting character's `current_room == "exp002.r2"`.
   - The test MUST include a save→reload leg (ADR-115 persistence path) and re-assert the same three fields survive the round-trip, proving forensics/reload sees the real dungeon (the reproduction of the playtest finding).

## Key Code Areas to Investigate

**The transition seam (where the gap lives):**
- `sidequest-server/sidequest/server/narration_apply.py` — lines ~4081–4116: room-graph transition handling. `character_locations[actor]` is written (~4105) and `_apply_room_graph_transition_effects()` fires side-effects, but `discovered_rooms` / `room_states` / `current_room` are NOT written here. This is the primary edit site.
- `sidequest-server/sidequest/server/narration_apply.py:5088` — the ONLY existing production write of `room_states[room_id]` (Story 45-43 container retrieval); reference for how `room_states` is keyed and to avoid clobbering it.

**The snapshot/Character fields to write:**
- `sidequest-server/sidequest/game/session.py:1021` — `discovered_rooms: list[str]` field (P3-deferred room-graph nav, ADR-055).
- `sidequest-server/sidequest/game/session.py:1030` — `room_states: dict[str, RoomState]` field (Story 45-13/45-43).
- `sidequest-server/sidequest/game/character.py:182` — `Character.current_room: str | None`.

**Room movement / dungeon helpers:**
- `sidequest-server/sidequest/dungeon/room_movement.py` — room-graph movement helpers (confirm the exact entry point; this is the natural home for an idempotent "record entered room" helper the apply seam can call).
- `sidequest-server/sidequest/dungeon/persistence.py` — dungeon map/frontier/mutation persistence; confirm it does NOT (and need not) touch the room-tracking fields, which serialize via the snapshot model.

**Map emit (read side — for context, do not change):**
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py:805–957` — `_build_dungeon_map_payload()` / `_maybe_emit_dungeon_map()`; reads `snapshot.discovered_regions` (line 935) and fires `dungeon.map_emitted` (line 940), `emit_fn(msg, "DUNGEON_MAP")` (line 957). This is the REGION axis; it is the consumer the playtester saw counting up, and it is NOT where the room fields should be written.

**Persistence / reload (round-trip):**
- `sidequest-server/sidequest/game/persistence.py` — main snapshot save/load (ADR-115 PostgreSQL). Verify `discovered_rooms` / `room_states` / `current_room` serialize and deserialize (the fields use `Field(default_factory=...)`, so old saves load empty — the test must save AFTER the write, then reload).

**OTEL spans already in this area (to extend, not duplicate):**
- `dungeon.map_emitted`, `dungeon.map_skipped` — `map_emit.py` (region axis).
- `room.transition_tick_span` — `sidequest/telemetry/spans/movement.py` (transition side-effects).
- `region_current_advanced` / `region_current_advanced` region span — `narration_apply.py` (region axis).

**Existing tests (extend / model after):**
- `sidequest-server/tests/server/test_71_15_room_graph_movement_side_effects.py` — ADR-055 transition side-effects (closest sibling to the new behavior).
- `sidequest-server/tests/server/test_room_graph_init.py` — room-graph init / `discovered_rooms` seeding.
- `sidequest-server/tests/server/test_container_retrieval_state.py` — `room_states` lifecycle (Story 45-43).
- `sidequest-server/tests/dungeon/test_persistence.py` — dungeon persist/load cycle.
- `sidequest-server/tests/integration/test_dungeon_scene_advance_107_1.py` — multi-turn dungeon traversal (good host for the wiring/round-trip test).

## Technical Notes

- **ADR-055 (Room Graph Navigation, partial):** `discovered_rooms` / `room_states` / `current_room` are the room-graph navigation axis. ADR-055 is marked partial precisely because the persistence half is unfinished — this story completes the write path so the room axis is durable, distinct from the region/cartography axis the map emit already serves.
- **ADR-106 (Runtime Procedural Jaquaysed Megadungeon, partial):** the procedural dungeon (beneath_sunden, exp002.r2 et al.) is the world that surfaced this finding. The contiguous edge-expansion crawl generates rooms at runtime; the room-tracking fields are what let forensics reconstruct the actual path through a procedurally-generated maze. An empty `discovered_rooms` defeats the megadungeon's whole forensics story.
- **ADR-133 (Client State Reconciliation v2 / reconnect) & ADR-115 (PostgreSQL persistence):** reconnect and cold reload rebuild client state from the persisted snapshot. If the room axis is never written, a reconnecting or reloading session sees an empty dungeon — this is the blocking reload risk called out in the finding. The round-trip AC guards this.
- **Two-axis caution:** do NOT conflate `discovered_regions` (region graph, already working) with `discovered_rooms` (room graph, the bug). The map handler reads regions; the fix writes rooms. Writing the region field will not help; writing the room fields is the whole job.
- **OTEL principle (CLAUDE.md):** every mechanical-subsystem decision must emit a watcher span so the GM panel can prove the subsystem engaged. The room-discovery write is exactly such a decision and currently emits nothing on the room axis — hence AC 5.
- **No silent fallbacks (CLAUDE.md):** if a transition resolves a room id that isn't a legal room-graph node, fail loudly rather than silently skipping the write — do not let a malformed location quietly leave `discovered_rooms` empty (that is the very failure mode being fixed).

## Story Scope

In scope:
- Writing `discovered_rooms`, `room_states`, and `Character.current_room` on room-graph dungeon transitions, at the existing `narration_apply.py` transition seam, reusing the existing snapshot fields.
- Ensuring the save/load round-trip preserves these fields.
- A new room-discovery OTEL span and an integration/wiring test including a reload leg.

Out of scope:
- The region/cartography axis (`discovered_regions`, `current_region`, `DUNGEON_MAP` emit) — already working; do not modify its behavior.
- The UI rendering of the room graph (that is story **153-25**, sidequest-ui).
- Any change to the `RoomState` model shape beyond what the round-trip strictly requires.
- Container-retrieval lifecycle (`room_states` writes at `narration_apply.py:5088`, Story 45-43) — preserve it, don't refactor it.
- Procedural dungeon generation itself (ADR-106) — this story records the walk, it does not change how rooms are generated.

---

## Development Notes

Start with a light research pass to:
1. Confirm the exact branch in `narration_apply.py` (~4081–4116) where a room-graph transition is detected and `character_locations` is set, and add the room-field writes there (or via a helper in `room_movement.py` that the seam calls).
2. Check whether `room_movement.py` already has an idempotent "record entered room" helper to reuse before writing a new one (reuse-first).
3. Verify the persistence path serializes the three fields and write the save→reload assertion against a populated snapshot.
4. Add the `room.discovered` (or equivalent) span at the write site with a first-discovery vs re-entry flag.
