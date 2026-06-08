---
parent: context-epic-100.md
---

# Story 100-1: Phase 0 — ADR-135 amendment: server-projection/React-render seam, public-firewall rule, no-session invariant

## Business Context

Epic 100 transitions the reference pages from server-rendered HTML to a server-projected JSON API consumed by React SPA routes. The page list (`/reference/rules/{pack}`, `/reference/lore/{pack}/{world}`) today ship fully-formed HTML from the server; the new model has the server **project** public data as JSON and delegate **rendering** to React.

This story (Phase 0) records the architectural boundary in ADR-135 — an amendment capturing the constraint set (C1–C5) and the public-URL home principle that govern the entire epic. No code changes in Phase 0; the design spec is the authority.

**Authoritative design source:** `docs/superpowers/specs/2026-06-08-reference-pages-react-migration-design.md` (epic 100 spec). The Architect updated this spec on 2026-06-08 to reconcile the 98-3 / 100-10 map-stack overlap: the shared Map component built in Phase 3 (story 100-10) must be **drill-aware-ready** for epic 98 / ADR-141 (story 98-3, which layers a campaign↔local scale/drill view-model) without forelosing that future work. Phase 0 must fold this drill-awareness framing into ADR-135.

## Technical Guardrails

### Constraint Set (C1–C5)

**C1 — The firewall is a server-side data projection, not a CSS hide**

- ADR-135's spoiler firewall (`reference_visibility.py`: `PUBLIC_STEMS`, `KEEPER` carve-outs, `EXCLUDED_FILES`, `npc_pool.is_projectable`) is **reused verbatim** as the projection gate for the new JSON API.
- **Keeper fields must never cross the JSON boundary.** The temptation is to ship full YAML and hide keeper fields in the React component layer — that is a spoiler leak in the browser network tab.
- Keeper fields (`ocean`, `history_seeds`, `initial_disposition`, `distinguishing_features`, ADR-053 belief/clue data, `seed_tropes.yaml`, `tropes.yaml`) **never appear in the JSON payload.**
- Projection is deterministic and testable: the security boundary is at JSON emit, not in the React layer.

**C2 — No-session invariant**

- The `/reference/*` SPA routes must mount and fully render with **no WebSocket session, no auth, no character, no genre-pack session state.**
- Pack/world come from the URL (`:pack`, `:world`).
- This is the ADR-135 "public table tool / works without the game running" property — the biggest risk of hosting the pages inside the game client.
- Test: each reference route renders under a bare `MemoryRouter` with **no** session/WS provider in scope.

**C3 — Theme without a session**

- The app's `useGenreTheme` is session-coupled: it injects CSS variables from a `theme_css` WebSocket event on connect, with an 8s grace timer.
- A session-free reference route has no such event.
- **Resolution:** reuse the **mechanism** (CSS-var `<style>` injection) but feed it from the reference projection JSON (keyed by `:pack`), not the WS event.
- The projection API emits theme tokens regardless; theme has one source per surface.

**C4 — Determinism is preserved**

- The current map carries a byte-deterministic contract (test pins it; node order is independent of YAML key order).
- The replacement uses **d3-dag** (Sugiyama layered layout) — pretty *and* deterministic — not `d3-force` (which jiggles per load).
- The determinism test moves from Python to Vitest against the shared React/TypeScript layout module.

**C5 — Public URL home**

- Today the canonical public URL is server-hosted (`GET /reference/lore/...` → `HTMLResponse`, port 8765).
- After migration, the canonical URL is the **SPA route** (`/reference/lore/:pack/:world`).
- FastAPI **retires the HTML routes**, **keeps `/reference/api/*`** (JSON), and serves the SPA index as a history-fallback for `/reference/*` deep-links.
- (Alternative: if SPA is hosted separately, redirect-to-SPA-host; confirm during planning.)

### Epic 98 / 100-10 Wiring (Architect amendment, 2026-06-08)

- Epic 98 / ADR-141 (story 98-3) introduces a campaign↔local **scale/drill** view-model on top of the cartography map in the in-game `MapOverlay`. 
- Story 100-10 (Phase 3) builds the shared d3-dag Map component. The component **must not** assume `MapWidget`'s feed shape or `orbital` toggle is permanent — epic 98 will rework both.
- **Shared Map component drill-aware-ready:** must (a) render the cartography graph as self-contained, not assuming fixed feed shape, and (b) accept a `selected`/`active` node prop and expose a node-select callback so 98-3 can layer drill-down without forking the layout.
- **Boundary:** 100-10 owns the **layout engine** (d3-dag module + Map component); 98-3 owns the **view-model** (scale rendering, drill affordances).
- **Sequencing:** 100-10 lands first (p2 < p3); 98-3 builds against the shared component, not the deleted `cartographyLayout.ts`.

## Scope Boundaries

**In scope (ADR-135 amendment):**

- New section documenting the server-projection / React-render seam
- Explicit record of the JSON boundary: what crosses it (public data + theme tokens) and what never does (keeper fields)
- Statement of constraints C1–C5 with rationale
- Public-URL home principle: SPA canonical, API kept, HTML routes retired
- Drill-aware-readiness requirement for shared Map component (per Architect amendment)

**Out of scope (per epic-100 Non-Goals):**

- No new authoring/world-building surface
- No change to reference page information architecture or content set
- No redesign — same sections (POI, Cast, Map, Timeline, generic YAML)
- No change to in-game `MapOverlay`'s *current* data source (epic 98 will rework it)
- No code changes — Phase 0 is documentation only

## AC Context

| AC | Detail |
|----|--------|
| ADR-135 amended | New section records projection/render seam, restatement of public-vs-keeper boundary |
| Constraint set documented | C1–C5 each explained: firewall is projection, no-session invariant, theme without session, determinism preserved, public URL home |
| C1 firewall — projection gate | Document `reference_visibility.py` reuse; keeper fields never in JSON; security test boundary |
| C2 no-session invariant | Explicit requirement that `/reference/*` routes render without WS/session/auth; test strategy: bare router |
| C3 theme without session | Session-free CSS-var injector pattern; feeds from projection JSON, not WS event |
| C4 determinism & d3-dag | D3-dag (Sugiyama) deterministic; test moves to Vitest against shared React module |
| C5 public URL home | SPA routes canonical; API kept; HTML routes retired; FastAPI history-fallback or redirect per deploy topology |
| Epic 98 / 100-10 bridge | Document drill-aware-ready framing: Map component self-contained, accepts node-select signal, no assumption of fixed feed/toggle |

## Implementation Notes

- The design spec (`2026-06-08-reference-pages-react-migration-design.md`) is the detailed authority; ADR-135 amendment is the structured, binding record.
- The Architect's 2026-06-08 amendment to the spec addresses epic 98 / 100-10 coupling; Phase 0 must fold this into the ADR to set the contract clearly.
- Phase 1 immediately follows (projection API + firewall reuse); Phase 0 is a documentary prelude that unblocks downstream phase gates.
