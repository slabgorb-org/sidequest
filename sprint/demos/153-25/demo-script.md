### Pre-Demo Setup (5 min before)
- Start server, client, and daemon: `just tmux` from the orchestrator root.
- Load the `beneath_sunden` world (Caverns & Claudes genre, WWN ruleset) with a saved session that has at least 2 discovered dungeon rooms.
- Have the OTEL GM panel open at `localhost:5173/#/dashboard`.
- Have the branch at `feat/153-25-dungeon-map-roomgraph` checked out in `sidequest-ui`.

---

**Slide 2 — Problem**

*Scene 1 (0:00–1:00): Reproduce the bug (or show recording)*

On the **pre-fix** build (or a recording from `2026-06-20` playtest):
1. Load a dungeon session. Navigate to the Map tab.
2. Show: only two region nodes (Ropefoot, The Dropmouth) and the "Down the Rope" route are visible.
3. Show browser DevTools → Network → WS frames: a `DUNGEON_MAP` frame is arriving from the server every turn. Point to it.
4. Show: the frame is dropped. Nothing in the UI changes.

*Fallback: show the screenshot from `sprint/archive/153-25-session.md` or the playtest board finding verbatim: "while standing in exp002.r2 (discovered=2/15), the Map tab still renders only the 2 surface cartography region nodes."*

---

**Slide 3 — What We Built**

*Scene 2 (1:00–2:30): Live demo on the fixed build*

```bash
# Confirm you're on the fixed branch
cd sidequest-ui && git log --oneline -1
# → afc552f feat(153-25): wire DUNGEON_MAP frame → mapData → Automapper room-graph
```

1. Open `localhost:5173` and load the `beneath_sunden` session.
2. Click the Map tab *before* descending — show the surface cartography (Ropefoot, Dropmouth, Down the Rope route). **"Surface map — unchanged."**
3. Play a turn that descends into the dungeon. Click Map tab.
4. Show: the room-graph renders — discovered room nodes, connecting passages, current-room highlighted. **"Dungeon map — now live."**
5. Play another turn (explore a new room). Show the fog of war expand: one new node appears, undiscovered rooms still hidden.
6. Re-surface. Click Map tab. Show: surface cartography is back, room-graph is gone. **"Clean switch — they don't fight."**

*Fallback for live demo failure: show Slide 3 bullets + the test output:*
```bash
cd sidequest-ui && npx vitest run src/__tests__/dungeon-map-wiring-153-25.test.tsx --reporter=verbose
# 7 tests passing, including AC-2 (room nodes), AC-3 (surface↔dungeon coexistence)
```

---

**Slide 4 — Why This Approach**

*Scene 3 (2:30–3:15): Show the OTEL panel*

1. Open `localhost:5173/#/dashboard`.
2. Play a dungeon turn. Show the `dungeon.map_emitted` span from the server.
3. Open browser DevTools console. Show the `[dungeon-map] rooms: 3 current: exp002.r2` marker from the client.
4. Point out: **"The server span proves it sent. The client marker proves it received and rendered. The gap this story fixed is exactly the space between those two signals."**

*Fallback: show the OTEL span screenshot from the session doc + copy the console.info line from `App.tsx:1282`.*

---

**Slide 5 (optional Before/After)**

*Scene 4 (3:15–4:00): Code diff (30 seconds, keep it light)*

```bash
cd sidequest-ui && git diff develop feat/153-25-dungeon-map-roomgraph --stat
# protocol.ts: +1 line (MessageType.DUNGEON_MAP)
# dungeonMap.ts: +47 lines (new file: type, guard, adapter)
# App.tsx: +18 lines (handler)
```

"Three files. The renderer, the routing, and the tab — untouched."

---

**Slide 6 — Roadmap**

*No live demo needed — talk to the slide.*

---

**Slide 7 — Questions**

---