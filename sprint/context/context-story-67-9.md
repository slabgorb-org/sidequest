# Story 67-9: Hoist WebSocket connection + slug-connect handshake above <Routes> to kill remount re-handshake

## Context

This is the Layer 2 follow-up explicitly deferred from completed story 67-8 (shipped 2026-05-29). Story 67-8 eliminated the duplicate-socket reconnect loop that stranded confrontations in AwaitingConnect by applying a three-layer fix:

1. **Layer 1 (67-8):** Eliminated the duplicate-socket creation via `createSocket` close-orphan pattern in `useWebSocket.ts` — when a socket close occurs, any orphaned stale socket is cleaned up before a new one is created.
2. **Layer 3 (67-8):** Added `sessionBound` beat-commit gate so frames are not committed during `AwaitingConnect` state, preventing mid-handshake frame submission.
3. **Layer 2 (this story, 67-9):** Hoist the WebSocket connection + slug-connect handshake to a stable component ABOVE `<Routes>` so architecture-level remounts don't re-run the handshake.

## The Problem (Root Cause)

Currently, the WebSocket connection and the slug-connect handshake are owned in `AppInner` (sidequest-ui/src/App.tsx), which is **inside** the per-route `LobbyRoot` component. This `LobbyRoot` is the shared `element` of multiple `<Route>` components and lives under `<StrictMode>`.

**Result:** ANY of the following triggers a remount of the socket-owning tree:
- Route transition (navigating between different pages)
- Dashboard hash toggle (`#/dashboard`)
- StrictMode double-mount (in dev/strict-mode scenarios)

When the tree remounts, the `slugConnectFired` ref is recreated (set to `false`), which causes the entire connect handshake to re-run:
- Second `ws.connection_accepted` message to server
- Second `chargen_gate` cycle
- Duplicate presence/connection tracking

**67-8 made this harmless** (Layer 1 prevents duplicate sockets, Layer 3 prevents mid-handshake frames), but the architectural root cause remains — unnecessary churn that should not happen at all.

## The Fix

Hoist **both** the WebSocket connection **and** the slug-connect handshake latch to a stable parent component that is ABOVE `<Routes>`, ensuring:

1. The connection fires **once per page-session**, not once per route mount.
2. Route transitions, hash changes, and StrictMode remounts do **not** re-run the connect handshake.
3. **Genuine socket drops** still trigger reconnect → server resume (the intended path).

### Key Files (from 67-8 diagnosis)

- **sidequest-ui/src/App.tsx** (~2300 lines)
  - Routing definition (~lines 2298–2320)
  - Slug-connect effect + `slugConnectFired` ref latch (~lines 1691–1790)
  - Reconnect re-send effect (~lines 1848–1873)
  - Socket ownership (~line 1198)
  - The connect path is currently gated on a per-MOUNT ref; a remount recreates the ref (→false) and re-runs the whole connect.

- **sidequest-ui/src/hooks/useWebSocket.ts**
  - Socket lifecycle management
  - `createSocket` close-orphan pattern (from 67-8 Layer 1, already landed)
  - `connect()` honors no-op-when-OPEN contract

## Acceptance Criteria

**AC1: Architecture — Connection hoisted above routes**
The WebSocket connection + slug-connect handshake are owned by a stable component ABOVE `<Routes>`, so route/dashboard-hash/StrictMode remounts do NOT re-run the connect handshake or open a second `ws.connection_accepted` cycle.

**AC2: Slug-connect latch hoisted**
The slug-connect handshake latch is hoisted with the connection so it fires once per page-session (not once per route mount). A genuine socket drop still drives reconnect → server resume.

**AC3: OTEL acceptance**
Across a route transition / dashboard-hash toggle mid-session, OTEL shows:
- NO second `ws.connection_accepted`/`chargen_gate` cycle
- `presence.multi_socket_attach` never fires
- This is the trigger-independent observable that confirms the fix.

**AC4: Regression coverage — no remount re-handshake**
Tests verify that a route change / remount does not re-run the connect handshake. Existing useWebSocket-67-8 duplicate-socket invariants stay green.

**AC5: Behavior regression check**
- Chargen gate still works
- Slug resume still works
- Reconnect-after-genuine-drop still works
- 67-8's sessionBound beat-commit gate still works

## Constraints

- **No Silent Fallbacks:** A genuinely unbound frame must still reject loudly. Reconnect must be a genuine socket-drop → server resume, not a silent re-handshake.
- **Minimalist discipline:** This is an architecture refactor of a ~2300-line `App.tsx`. Contain risk, own RED tests, prepare for review.
- **Base branch:** `develop` (gitflow).
- **PR strategy:** standard (not stacked).

## Related Stories & ADRs

- **67-8** (done, 2026-05-29): Three-layer duplicate-socket elimination (Layers 1 & 3 shipped; Layer 2 deferred here)
- **ADR-036:** Multiplayer turn coordination (relevant for understanding turn submit barriers and per-mount hazards)
- **ADR-038:** WebSocket transport architecture

## Success Metrics

1. Route transitions do not emit a second `ws.connection_accepted` watcher event.
2. Dashboard hash toggles mid-session do not re-run slug-connect.
3. OTEL `presence.multi_socket_attach` never fires for legitimate single-socket sessions.
4. All existing 67-8 regression tests pass.
5. Code review passes with no undocumented spec deviations.
