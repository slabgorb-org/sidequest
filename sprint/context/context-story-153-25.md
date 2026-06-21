# Story Context: 153-25 — [DUNGEON-MAP-UI-NO-ROOMGRAPH] Render the procedural room-graph in the Map tab while inside the dungeon

## Story Metadata
- **Story ID:** 153-25
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** Bug
- **Points:** 3
- **Workflow:** TDD
- **Repositories:** sidequest-ui
- **Priority:** P2

## Problem Statement

While the player stands in a dungeon room (`exp002.r2`, discovered = 2/15), the Map tab still renders only the **surface cartography**: the two region nodes (Ropefoot, The Dropmouth) and the "Down the Rope" route. The dungeon room-graph — the entrance, the discovered rooms, and the three passages out of the current room — is never drawn. **The player exploring the maze has no map of it.**

Verbatim finding (playtest): "while standing in exp002.r2 (discovered=2/15), the Map tab still renders only the 2 surface cartography region nodes (Ropefoot, The Dropmouth) + the 'Down the Rope' route. The dungeon.map_emitted room-graph (entrance + discovered rooms + the three passages) is never drawn. The player exploring the maze has no map of it."

The server **already emits** the dungeon room-graph: `map_emit.py` broadcasts a `DUNGEON_MAP` WebSocket frame (alongside the region-mode `MAP_UPDATE` frame) carrying the discovered rooms, current room, and exits. The renderer for room graphs **already exists** in the UI (`Automapper.tsx` / `DungeonMapRenderer.tsx`) and `MapWidget` already routes room-graph data to it. The bug is a **message-wiring gap**: the `DUNGEON_MAP` frame is dropped at the client because there is no `MessageType.DUNGEON_MAP` and no handler for it — so the room-graph payload never reaches `mapData`, and the renderer never fires.

## Root Cause Direction

This is a **wiring gap, not a missing renderer** (reuse-first applies):

- **Server emits it (confirmed).** `sidequest-server/.../map_emit.py:957` does `emit_fn(msg, "DUNGEON_MAP")` from `_maybe_emit_dungeon_map()`, with the room-graph payload built at lines 805–870. This frame is distinct from the region-mode `MAP_UPDATE` frame emitted at `map_emit.py:1042`.
- **UI never names the message.** `sidequest-ui/src/types/protocol.ts` defines `MAP_UPDATE` (line 17) but **has no `DUNGEON_MAP` entry** in the `MessageType` const object.
- **UI never handles the message.** `sidequest-ui/src/App.tsx:1268` handles only `MessageType.MAP_UPDATE` (`setMapData(msg.payload ...)`). There is no `if (msg.type === MessageType.DUNGEON_MAP)` branch, so the frame arrives and is silently dropped — `mapData` is only ever fed the cartography/region payload.
- **The renderer already exists.** `sidequest-ui/src/components/Automapper.tsx` (and `DungeonMapRenderer.tsx`) draw the room-graph SVG (BFS-layered, no compass directions per ADR-055). `MapWidget.tsx:253` already routes `room_graph`-shaped `mapData` to `<Automapper rooms={roomGraph} currentRoomId={currentRoomId} />` (see `MapWidget.tsx:49–70` routing comment). The payload shape (`explored[]` with `room_exits`, `room_type`, `is_current_room`) is already typed in `MapOverlay.tsx` and is the same shape the server's `DUNGEON_MAP` payload carries.

So the fix is: **name the message, handle it, and route its payload into `mapData`** so the existing Automapper path lights up when inside the dungeon. The hard part is deciding how `DUNGEON_MAP` and `MAP_UPDATE` coexist in the single `mapData` slot (the dungeon room-graph should drive the Map tab while in the dungeon; the surface cartography while on the surface — overlay or switch, not both fighting over one state).

## Acceptance Criteria

1. **`DUNGEON_MAP` message is named and handled:**
   - `MessageType.DUNGEON_MAP` is added to `sidequest-ui/src/types/protocol.ts` (mirroring the server frame name).
   - `App.tsx` adds a handler branch for `MessageType.DUNGEON_MAP` that routes the room-graph payload into the map state (`mapData`), analogous to the existing `MAP_UPDATE` handler at `App.tsx:1268`.

2. **The room-graph is drawn while inside the dungeon:**
   - When a `DUNGEON_MAP` frame for `exp002.r2` (discovered = 2/15) is received, the Map tab renders the room-graph (discovered room nodes + current-room marker + the room exits/passages) via the existing `Automapper` / `DungeonMapRenderer` path — not the surface cartography region nodes.
   - The current room is visually marked (`is_current_room`), and the discovered count drives which nodes appear (fog of war: undiscovered rooms are not drawn).

3. **Surface vs dungeon view coexist correctly:**
   - On the surface (region/cartography payload), the Map tab still renders the cartography region map (Ropefoot / Dropmouth / "Down the Rope"), unchanged.
   - Inside the dungeon, the room-graph supersedes (switch) or overlays the surface view per the chosen design — the player never sees only the 2 surface nodes while standing in a dungeon room.

4. **Payload typing:**
   - A TypeScript type for the `DUNGEON_MAP` payload exists (reuse `MapState` / `ExploredLocation` from `MapOverlay.tsx` / the `MapUpdatePayload` shape in `payloads.ts:322` if compatible; the server payload already matches the `explored[]`-with-room-fields shape). No `as unknown as` blind cast that hides a shape mismatch.

5. **Telemetry / observability AC:**
   - The client emits a lightweight client-side trace/log marker when it receives and applies a `DUNGEON_MAP` frame (room count + current room), so a playtest can confirm the frame is being consumed rather than dropped. (This complements the server-side `dungeon.map_emitted` span at `map_emit.py:940` — the server proves it sent; the client marker proves it received and rendered. The dropped-frame failure mode this story fixes is exactly the gap between "server emitted" and "client rendered.")
   - Verify in the playtest repro that the server-side `dungeon.map_emitted` span (already live) and the new client-side consumption marker both fire for the same turn.

6. **Wiring / integration-test AC (reaches production code path):**
   - A test mounts the production message path (App-level dispatch or the map hook/provider that owns `mapData`) and asserts that dispatching a `DUNGEON_MAP` message updates `mapData` to the room-graph payload and causes the Map tab to render room-graph nodes (Automapper), NOT the cartography region nodes. A pure render test of `Automapper` in isolation is NOT sufficient — the test must prove the message is named, dispatched, and reaches the renderer.
   - The test MUST cover the surface→dungeon→surface transition (or at least that a `DUNGEON_MAP` frame after a `MAP_UPDATE` frame flips the rendered view) to lock the coexistence rule from AC 3.

## Key Code Areas to Investigate

**Message type + handler (the gap):**
- `sidequest-ui/src/types/protocol.ts:17` — `MessageType` const object; `MAP_UPDATE` exists, `DUNGEON_MAP` does NOT. Add it here.
- `sidequest-ui/src/App.tsx:1268` — the `MAP_UPDATE` handler (`setMapData(...)`); add the sibling `DUNGEON_MAP` branch. (`mapData` state declared at `App.tsx:377`, reset at `App.tsx:2047`.)

**The renderer that already exists (route into it, don't rebuild):**
- `sidequest-ui/src/components/Automapper.tsx` — room-graph SVG renderer (`ExploredRoom` shape; BFS-layered, ADR-055 no-compass layout).
- `sidequest-ui/src/components/DungeonMapRenderer.tsx` — room-graph SVG renderer (story 29-8 component).
- `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx:49–70, 253, 258` — routing: room-graph `mapData` → `<Automapper>` (line 253); region/cartography → `<MapOverlay>` (line 258). Confirm the routing predicate so the `DUNGEON_MAP` payload lands in the Automapper branch.
- `sidequest-ui/src/components/MapOverlay.tsx` — owns `MapState` / `ExploredLocation` / `CartographyMetadata` types and the cartography-vs-roomgraph render fork; the `explored[]`-with-room-fields shape the server sends is defined here.

**Payload types:**
- `sidequest-ui/src/types/payloads.ts:322` — `MapUpdatePayload` (compatible base shape; has `explored?`, `cartography?`). Decide whether `DUNGEON_MAP` reuses this or needs a dedicated `DungeonMapPayload` type.
- `sidequest-ui/src/components/MapOverlay.tsx` — `MapState`, `ExploredLocation` (room fields: `room_exits`, `room_type`, `is_current_room`), `CartographyMetadata`/`CartographyRoute`/`CartographyRegion`.

**Tab registration (verify dual registration — known gotcha):**
- `sidequest-ui/src/components/GameBoard/widgetRegistry.ts:80` — `map` widget (`dataGated: true`).
- `sidequest-ui/src/components/GameBoard/MobileTabView.tsx:33` — mobile `map` tab entry. Both exist and are in sync today; confirm the tab still gates correctly once `DUNGEON_MAP` also populates `mapData` (the tab is `dataGated` on `mapData` being non-null).

**Server side (reference only — confirms what is emitted):**
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py:805–870` — `_build_dungeon_map_payload()` (room nodes, exits, current-room marker, fog of war).
- `sidequest-server/sidequest/server/websocket_handlers/map_emit.py:957` — `emit_fn(msg, "DUNGEON_MAP")`; `:940` — `dungeon.map_emitted` span; `:1042` — sibling `MAP_UPDATE` region frame.

**Existing UI tests (extend / model after):**
- `sidequest-ui/src/components/__tests__/Automapper.test.tsx` — room-graph renderer (proves the renderer works; the new test must prove the message reaches it).
- `sidequest-ui/src/__tests__/dungeon-map-renderer.test.tsx` — DungeonMapRenderer SVG.
- `sidequest-ui/src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx` — MapWidget routing (room-graph vs region).
- `sidequest-ui/src/components/__tests__/MapOverlay.cartography.test.tsx` / `src/components/map/__tests__/MapOverlay.shared-map.test.tsx` — cartography render (regression guard for AC 3 surface view).

## Technical Notes

- **ADR-055 (Room Graph Navigation, partial):** room graphs have no compass directions; the Automapper/DungeonMapRenderer use a layered BFS layout, not a coordinate/compass grid. Render the room-graph through that path, not the cartography node-link layout. ADR-055 being "partial" is exactly this missing wiring on the client.
- **ADR-106 (Runtime Procedural Jaquaysed Megadungeon, partial):** the room graph is generated at runtime via contiguous edge-expansion (beneath_sunden / exp002.r2). The map must update incrementally as rooms are discovered — each `DUNGEON_MAP` frame is the latest discovered-subgraph snapshot (fog of war hides undiscovered rooms). The UI must re-render on every frame, not cache a stale graph.
- **ADR-026 / ADR-027 (Client-Side State Mirror / Reactive State Messaging):** `mapData` is reactive, session-scoped state driven by inbound WS frames — it is NOT a persisted server field on the client. The dungeon room-graph view is rebuilt from `DUNGEON_MAP` frames, so the wiring must feed those frames into the mirror exactly as `MAP_UPDATE` already does.
- **ADR-133 (Client State Reconciliation v2 / reconnect):** because `mapData` is rebuilt from frames, the server must (and does) re-emit `DUNGEON_MAP` after reconnect for the room-graph to repopulate. Verify on reconnect into a dungeon session the room-graph view returns (don't assume a replay buffer holds it). If the server only re-emits on the next turn, note that as a follow-up — but the client-side fix (name + handle the frame) is the load-bearing change here.
- **Companion story 153-24 (server):** persists `discovered_rooms` / `room_states` / `current_room` into the snapshot. That is the persistence axis; THIS story is the live-render axis off the already-emitted `DUNGEON_MAP` frame. They are independent — 153-25 does not depend on 153-24 landing first, because the `DUNGEON_MAP` frame is built from `discovered_regions`/the dungeon graph in `map_emit.py`, not from `discovered_rooms`.
- **Reuse-first (CLAUDE.md):** the renderer, the routing, the types, and the tab registration already exist. Do not build a new dungeon map component — wire the existing `DUNGEON_MAP` frame into the existing `mapData` → `MapWidget` → `Automapper` path.
- **No silent fallbacks (CLAUDE.md):** if a `DUNGEON_MAP` frame arrives with a payload shape the handler doesn't expect, fail loudly (or log loudly) rather than silently dropping it — silent drop is the exact bug being fixed.

## Story Scope

In scope:
- Naming `MessageType.DUNGEON_MAP` and adding the `App.tsx` handler that routes the room-graph payload into `mapData`.
- Ensuring `MapWidget`/`MapOverlay`/`Automapper` render the room-graph when the dungeon payload is present, and the surface cartography when it isn't (coexistence rule).
- Payload typing for `DUNGEON_MAP`, a client-side consumption marker (telemetry AC), and a wiring/integration test.

Out of scope:
- Server-side persistence of `discovered_rooms` / `room_states` / `current_room` — that is story **153-24** (sidequest-server).
- Building a new dungeon map renderer (Automapper / DungeonMapRenderer already exist).
- Cartography region rendering changes (Ropefoot / Dropmouth / routes) beyond the coexistence switch.
- Orbital/orrery and two-scale galactic map paths in `MapWidget` (unrelated map modes).
- Server-side reconnect re-emit behavior (note as follow-up if `DUNGEON_MAP` isn't re-sent on reconnect; the client wiring is the deliverable).

---

## Development Notes

Start with a light research pass to:
1. Confirm the exact `MessageType` shape in `protocol.ts` and add `DUNGEON_MAP` consistent with the server frame name.
2. Decide the coexistence model in `App.tsx` / `MapWidget`: does `DUNGEON_MAP` overwrite `mapData` (switch) or layer on top (overlay)? The routing predicate in `MapWidget.tsx:49–70` already distinguishes room-graph from region payloads — feed the dungeon payload so it hits the Automapper branch.
3. Confirm the server `DUNGEON_MAP` payload shape matches `MapState`/`ExploredLocation` (it does per the type investigation) so no adapter is needed beyond the existing `MapWidget` adapt step (`MapWidget.tsx:262`).
4. Write the wiring test at the dispatch level (message → `mapData` → rendered Automapper nodes), plus a cartography regression guard for the surface view.
