# Story 100-8: Phase 2 — React reference shell: session-free /reference/* routes + generic node-tree renderer components (C2)

**Epic:** 100 (Reference pages → React SPA migration)
**ID:** 100-8
**Points:** 5
**Priority:** p2
**Workflow:** tdd
**Repos:** sidequest-ui

## Story Summary

Build the React client-side for reference pages. Phase 1 (100-2 through 100-7) shipped server-side JSON projections. This story implements the React shell that consumes those projections:

1. **Session-free routes** — `/reference/lore/:pack/:world` and `/reference/rules/:pack` that do NOT require a WebSocket game session
2. **Generic node-tree renderer components** — composable UI components that render the projected JSON structures (lore sections, rules, etc.)
3. **REST-based data fetch** — consume the API endpoints added in 100-6 and 100-7 (GET /reference/api/lore/{pack}/{world}, GET /reference/api/rules/{pack})

## Acceptance Criteria

1. **C2 — No-session invariant:** Routes mount and render fully without any WebSocket session, auth, game state, or character selection. Test: component renders under a router with no session/WS provider in scope.

2. **Session-free routing:** New route components at `/reference/lore/:pack/:world` and `/reference/rules/:pack` are wired into the app's main router.

3. **Generic node-tree renderer:** A reusable React component (or component family) that accepts generic YAML section JSON and renders it (used by Lore page for generic sections, rules page for rule descriptions, etc.). Must support nesting.

4. **REST fetch + state management:** Components fetch the projection JSON via `GET /reference/api/lore/{pack}/{world}` and `GET /reference/api/rules/{pack}`, handle loading/error states, and pass the data to renderers.

5. **No keeper content leaks:** Verify that keeper fields are never rendered, even if accidentally included in JSON (defense in depth — server should never send them, but UI should also not assume).

6. **Type safety:** TypeScript types for the projection JSON response shape (parsed from spec or inferred from 100-6 + 100-7 implementation).

7. **Integration test:** One Vitest suite confirming the reference route renders without error when no session is in scope. Fixture JSON can be static (not fetched from running server).

## Related Work

- **100-2 through 100-7:** Server-side JSON projection APIs and theme tokens (already shipped).
- **100-9:** Session-free theme injector (next story, depends on this one).
- **100-10:** Shared d3-dag map component (Phase 3, depends on generic renderer patterns).
- **ADR-135:** Reference Pages Are a Public Table Tool — establishes the "no session, no auth, no keeper content" invariant.
- **Spec:** `docs/superpowers/specs/2026-06-08-reference-pages-react-migration-design.md` (sections C2, C3).

## Design Notes

- Routes are **session-free** — they do not subscribe to the game's WebSocket or require the GameStateProvider. This is a hard constraint (C2). Use a separate provider tree if needed.
- The node-tree renderer is a generic building block, reused by multiple reference sections (generic YAML sections, rules descriptions, etc.). Keep it decoupled from domain logic.
- Error handling: graceful degradation on failed fetch (show error message, don't white-screen).
- Loading states: show a spinner while JSON is being fetched.
