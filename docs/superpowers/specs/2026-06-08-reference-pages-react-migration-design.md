# Reference Pages → React SPA Migration — Design

- **Date:** 2026-06-08
- **Status:** Draft (brainstorm output; pre-plan)
- **Author:** Keith Avery + SM (brainstorm)
- **Supersedes/amends:** ADR-135 (Reference Pages Are a Public Table Tool) — the
  "server-rendered HTML" premise becomes "server-projected JSON, React-rendered."
- **Related:** ADR-079 (genre theme system), ADR-119 (authenticated identity —
  explicitly *not* applied to this surface), ADR-086 (image-composition taxonomy),
  ADR-053 (scenario belief/clue data — keeper-side), epic 65 (reference v2 stories).

## Summary

The player-facing reference pages (`/reference/rules/{pack}`,
`/reference/lore/{pack}/{world}`) are today ~2,000 lines of server-side Python that
emit fully-formed HTML strings (`reference_renderer.py`, `reference_presenters.py`,
`reference_map.py`, `reference_timeline.py`, `reference_theme.py`, hydrated by a
hand-written vanilla `islands.js`). This migration gets the server **out of the HTML
rendering business**: the server keeps the *projection* responsibility (deciding what
public data exists) and hands *rendering* to the main React SPA.

The triggering pain was the cartography **Map** section: its layout is duplicated as
Python (`reference_map.py`) **and** a verbatim TypeScript port
(`cartographyLayout.ts`, consumed by the in-game `MapOverlay`), kept byte-identical by
hand. That split-brain is an artifact of "two runtimes, no shared layout source." The
migration dissolves it: the map becomes a single React component shared by the
reference page and the in-game overlay.

## Goals

- Server renders **no reference HTML**. Server emits **public-projected JSON**; React
  renders it.
- **One** cartography map renderer (React, d3-dag, deterministic) shared by the
  reference page and the in-game `MapOverlay`. Delete `reference_map.py`'s SVG emit and
  `cartographyLayout.ts`.
- Preserve every ADR-135 property: **one fixed public projection, no `?audience`, no
  GM mode, no keeper content**, and **works without the game running** (no session, no
  auth, no character selection).
- Unify on the app's existing theme mechanism (ADR-079 CSS-variable injection), fed
  from a session-free source.

## Non-Goals

- No GM/keeper view, no `?audience` param, no identity resolution. ADR-135's audience
  doctrine stands unchanged — this migration changes *how* the public projection is
  rendered, never *what* it exposes.
- No new authoring/world-building surface. Keeper content stays in YAML + future author
  tools.
- No redesign of the reference page's information architecture or content set. Same
  sections (POI, Cast, Map, Timeline, generic YAML), same data, new rendering substrate.
- No change to the in-game `MapOverlay`'s data source *other than* sharing the new map
  component (the overlay keeps getting cartography from its current session path).

## Load-Bearing Constraints

### C1 — The firewall is a server-side data projection, not a CSS hide

ADR-135's spoiler firewall (`reference_visibility.py`: `PUBLIC_STEMS`, `KEEPER`
carve-outs, `EXCLUDED_FILES`, plus `npc_pool.is_projectable`) currently works because
the server only ever *emits HTML for public data*. In a React world the temptation is
to ship full YAML and hide keeper fields in the component layer. **That is a spoiler
leak in the browser network tab and is forbidden.** Keeper fields (`ocean`,
`history_seeds`, `initial_disposition`, `distinguishing_features`, ADR-053 belief/clue
data, `seed_tropes.yaml`/`tropes.yaml`) **must never cross the JSON boundary.**
`reference_visibility.py` is **reused verbatim** as the projection gate for the new API
and is the focus of this migration's security tests.

### C2 — No-session invariant

The `/reference/*` SPA routes must mount and fully render with **no WebSocket session,
no auth, no character, no genre-pack session state**. Pack/world come from the URL.
This is the ADR-135 "public table tool / works without the game running" property. It
is the single biggest risk of hosting the pages inside the game client, and it gets an
explicit test (route renders under a router with no session/WS provider in scope).

### C3 — Theme without a session

The app's `useGenreTheme` is **session-coupled**: it injects genre CSS variables from a
`theme_css` event the server pushes *over the WebSocket on connect*, with an 8s grace
timer and a loud failure banner (`THEME_CSS_FAILURE_BANNER_ID`) if it never arrives. A
session-free reference route has no such event. **Resolution:** reuse the *mechanism*
(the CSS-variable `<style>` injection that `useGenreTheme` performs) but feed it from
the reference projection JSON (keyed by the URL `:pack`), not the WS event. The
projection API emits theme tokens regardless, so theme has one source per surface. The
WS-delivery path of `useGenreTheme` is untouched for the in-game client; the reference
route uses a session-free injector sharing the same CSS-variable contract.

### C4 — Determinism is preserved

The current map carries a byte-deterministic contract (a test pins it; node order is
independent of YAML key order). The replacement uses **d3-dag** (Sugiyama layered
layout) — pretty *and* deterministic — not `d3-force` (which jiggles per load). The
determinism test moves to Vitest against the shared React/TS layout module.

### C5 — Public URL home

Today the canonical public URL is server-hosted (`GET /reference/lore/...` →
`HTMLResponse` on the FastAPI app, port 8765). After migration the canonical URL is the
SPA route. FastAPI **retires the HTML routes**, **keeps `/reference/api/*`** (JSON), and
serves the SPA index for `/reference/*` as a history-fallback so a cold deep-link to a
reference URL boots the SPA. (Redirect-to-SPA-host is the alternative if the SPA is
hosted separately in prod; the plan resolves which based on the deploy topology — see
Open Questions.)

## Architecture

```
URL: /reference/lore/:pack/:world   (and /reference/rules/:pack)
        │
        ▼
  React SPA route  ── fetch ──►  GET /reference/api/lore/:pack/:world   (FastAPI, JSON)
  (session-free)                       │
        │                              ▼
        │                    reference_visibility.py  (REUSED firewall)
        │                    + POI/Cast/Map/Timeline loaders
        │                    + theme.yaml → tokens
        │                    + R2 portrait gate (resolved server-side)
        ▼                              │
  Components render          public-projected JSON  (no keeper field, ever)
  (YAML-node renderer,
   POI, Cast, Map[d3-dag],
   Timeline)  ◄── theme CSS vars from JSON (session-free injector)
        │
        ▼
  Map component  ◄── shared ──►  in-game MapOverlay
```

**Server-side units (kept / new):**

- `reference_visibility.py` — **kept verbatim.** The firewall. Now gates the JSON API.
- `reference_theme.py` (`ReferenceTheme`, `theme.yaml` loader) — **kept**, but emits
  tokens into JSON instead of a `<style>` block. (May be folded into the API serializer.)
- POI/Cast/Map/Timeline **loaders** (`load_points_of_interest`, `load_cast_entries`,
  `load_cartography_config`, timeline loader) and R2 gates
  (`load_r2_manifest_keys`, `portrait_image_key`, `is_projectable`) — **kept**, moved
  behind the API serializer.
- **New:** a JSON serializer per page (`rules`, `lore`) producing a typed, public-only
  document. The generic YAML→HTML engine (`render_node`/`render_dict`/`render_list`/
  `render_scalar`, label humanization, devnote filtering) is **reimplemented as data
  shaping** (YAML → a normalized node tree in JSON) so the React renderer walks a clean
  structure rather than re-parsing raw YAML.

**Server-side units (deleted at cutover):** `reference_renderer.py` HTML assembly,
`reference_presenters.py` HTML, `reference_map.py` SVG emit, `reference_timeline.py`
HTML, `islands.js`, the reference static CSS now expressed in React.

**Client-side units (new):**

- Reference route shell (session-free) under the existing `react-router-dom` `<Routes>`.
- Generic **node-tree renderer** components (the React counterpart of the YAML engine).
- Section components: POI, Cast, **Map (d3-dag)**, Timeline.
- Session-free **theme injector** (CSS-variable contract shared with `useGenreTheme`).
- Shared **cartography layout module** (d3-dag) consumed by both the reference Map and
  `MapOverlay`'s `RegionNodeGraph`; `cartographyLayout.ts` is deleted in favor of it.

## Data Flow (lore page, representative)

1. SPA mounts `/reference/lore/:pack/:world` with no session. It reads `:pack`/`:world`
   from the URL and fetches `GET /reference/api/lore/:pack/:world`.
2. Server loads the world/pack YAML, applies `reference_visibility.py`, runs the POI/
   Cast/Map/Timeline loaders, resolves R2 portrait/POI image presence and asset URLs
   server-side, derives theme tokens from `theme.yaml`, and serializes a **public-only**
   JSON document (sections + TOC + theme tokens + hero).
3. React applies the theme tokens (CSS vars), renders the TOC + sections. The Map
   section feeds cartography into the shared d3-dag layout module and draws the graph;
   portrait pins use the pre-resolved asset URLs from the JSON.
4. No keeper field is present in the payload; there is nothing to hide client-side.

## Error Handling (fail loud — No Silent Fallbacks)

- Malformed `cartography.yaml` / `theme.yaml` / world YAML → API returns **HTTP 500**
  (current behavior: `ValueError` → 500). React surfaces a loud error state, never a
  silently section-less page.
- Missing world/pack → **404** from the API; React renders a not-found state.
- Theme tokens absent in the payload → loud failure surface (mirrors the existing
  `useGenreTheme` no-silent-degrade banner philosophy), not a silent collapse to dark
  defaults.
- A dangling cartography edge (adjacency to unknown region) is dropped from the edge set
  and reported — the existing `sidequest.reference.map_dangling_edge` WARN span is
  preserved (emitted at projection time, server-side).

## Observability (OTEL)

The reference span family (`sidequest.reference.map_rendered`, `map_pin_resolved`,
`map_pin_not_found`, `map_dangling_edge`, and the lore-assembled span) **moves to the
projection step** — spans fire when the server builds the JSON (the decision point),
not at HTML-emit time. Span attributes (node/edge/pin counts) are unchanged. This keeps
the GM/dev panel's lie-detector coverage: the spans assert the projection actually ran
and what it decided, independent of how React later draws it.

## Testing Strategy

- **Firewall (security) — server, concentrated here per C1.** For every page type and a
  representative spoiler-bearing world, assert the JSON payload contains **no** keeper
  field (`ocean`, `history_seeds`, `initial_disposition`, `distinguishing_features`,
  belief/clue data, `seed_tropes`/`tropes`). Drive the real API; assert on the response
  body. This is the load-bearing test set.
- **No-session invariant — client (C2).** Render each reference route under a bare
  `MemoryRouter` with **no** session/WS provider in scope; assert it mounts and renders
  from a mocked API payload. Fails if a component reaches for session state.
- **Determinism — client (C4).** The shared d3-dag layout module yields identical
  output for the same cartography across runs and is independent of region key order
  (Vitest). Replaces the Python byte-identical test.
- **Map unification — client.** One test exercises the shared map component in both the
  reference context and the `MapOverlay` context, asserting identical topology for the
  same cartography (the split-brain regression guard).
- **Wiring tests (per repo CLAUDE.md "Every Test Suite Needs a Wiring Test").**
  - Server: the projection API is mounted on the app and reachable (hit the route).
  - Server: OTEL — drive the projection, assert the reference spans fired (not a
    source-text grep; behavior/span assertion per "No Source-Text Wiring Tests").
  - Client: the reference routes are registered in the app's `<Routes>` and reachable.
- **Pack/content invariants** (e.g., "every live world's `/reference/api/lore` returns
  200 and a non-empty projection") belong in the **pack validator**, not pytest unit
  tests (per project feedback: no content invariants in unit tests).

## Phasing

The migration is an epic. Phases are sequenced so the firewall is proven before any
HTML is deleted, and the map (the original ask) lands as soon as the shell exists.

- **Phase 0 — ADR-135 amendment.** Record the projection/render seam, C1–C5, and the
  public-URL home. No code.
- **Phase 1 — Projection API + firewall reuse.** `/reference/api/rules/:pack` and
  `/reference/api/lore/:pack/:world`, reusing `reference_visibility.py` and the loaders;
  theme tokens; R2 gates resolved server-side; spans moved to projection. **Security
  tests land here.** Existing HTML routes remain live (parallel surface).
- **Phase 2 — React shell + generic renderer.** Session-free reference routes, theme
  injector, node-tree renderer. Renders rules + lore from the API behind a flag/route,
  HTML routes still canonical.
- **Phase 3 — Sections, incl. shared d3-dag Map.** POI, Cast, Map (d3-dag, shared with
  `MapOverlay`), Timeline. Deletes `cartographyLayout.ts`; `MapOverlay` adopts the shared
  component. Delivers the prettier map.
- **Phase 4 — Cutover + retire.** Flip `/reference/*` to the SPA (history-fallback or
  redirect per Open Questions), delete the Python HTML emitters + `islands.js` + reference
  static CSS, keep `reference_visibility.py` feeding the API, update the ADR pointer.

## Open Questions (resolved during planning)

1. **Prod serving of the public URL (C5).** Does FastAPI serve the SPA bundle (history
   fallback for `/reference/*`), or is the SPA hosted separately with a redirect? Depends
   on the current sidequest-ui prod deploy topology — confirm before Phase 4.
2. **Exact JSON schema per page.** The normalized node-tree shape for the generic YAML
   sections (how `render_node`/`_dict`/`_list` map to JSON nodes) — pinned in Phase 1.
3. **`reference_theme.py` fate.** Kept as a token source feeding the API, or folded into
   the API serializer — decide in Phase 1.
4. **Rules vs lore ordering within phases.** Both migrate; lore carries the map and is the
   richer surface — likely lead with lore through the shell, fold rules in alongside.
