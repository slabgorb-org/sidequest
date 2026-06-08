---
id: 135
title: "Reference Pages Are a Public Table Tool — Single Fixed Projection, No GM Audience"
status: accepted
date: 2026-06-01
deciders: ["Keith Avery", "Neo (Architect)"]
supersedes: []
superseded-by: null
related: [53, 86, 104, 119, 120, 141]
tags: [core-architecture, frontend-protocol]
implementation-status: partial
implementation-pointer: "sidequest-server reference_renderer.py — audience doctrine + stories 65-7..65-9 live; 65-10..65-12 pending. The 2026-06-08 amendment (server-projection / React-render seam) reframes the render substrate from server HTML to a projected JSON API + React SPA — design-only, implementation tracked as epic 100; see the Amendment section and docs/superpowers/specs/2026-06-08-reference-pages-react-migration-design.md."
---

# ADR-135: Reference Pages Are a Public Table Tool — Single Fixed Projection, No GM Audience

> **Documents a decision governing upcoming work, not live code.** The
> server-rendered reference pages (`/reference/rules/{pack}`,
> `/reference/lore/{pack}/{world}`) are being extended to surface POI and
> portrait imagery and richer world content (epic 65, stories 65-7…65-12;
> design spec dated 2026-06-01). This ADR records the *audience doctrine* for
> that surface and **reverses** the `?audience=gm` filter proposed in the
> never-built `2026-05-23-reference-pages-v2-followup-brief.md`.

## Context

The reference pages are SideQuest's only player-facing, server-rendered view of
a world's lore and a pack's rules. v1 (epic 63) shipped them with a blunt
spoiler defense: `EXCLUDED_FILES` simply omits keeper-side files (`npcs.yaml`,
`seed_tropes.yaml`, etc.) wholesale.

The v2 followup brief proposed widening the surface to re-include those files
behind an **`?audience=gm`** query parameter: a "player" projection by default,
a "gm" projection that reveals everything, with the audience resolved from a URL
param and/or a Cloudflare-identity → role mapping. That design rested on an
implicit assumption: that **one of the humans at the table is "the GM"** and
therefore wants a richer, spoiler-bearing view through this surface.

That assumption is **false for SideQuest and is deprecated.** SideQuest exists so
that the forever-GM can finally *play* — **the AI is the GM/narrator, and every
human at the table is a player** (CLAUDE.md "Who This Is For"; SOUL.md). There is
no human GM seat at the table. The keeper-side, full-fidelity view of a world
already has two homes that are *not* this surface:

1. **The YAML files themselves** — authors read and write them directly.
2. **The future world-building / authoring tools** — the deliberate author
   surface (the homebrew thesis: Jade and others author worlds as content).

Layering a "GM mode" onto the player-facing table tool therefore adds a whole
authentication-shaped subsystem (URL param parsing, identity resolution via
`Cf-Access-Authenticated-User-Email`, a GM-email allowlist synced across clones)
to serve a reader who does not exist on this surface — and creates a flippable
URL that invites self-spoiling. It also risks re-entangling the deleted
session-seat `is_gm` axis (story 71-35 removed it from the projection firewall;
`views.py:is_gm()` survives only as a *live-session* seat concept, unavailable to
a pre-session static page).

## Decision

**The reference pages are a table tool and render exactly one projection — the
public one. There is no `?audience` parameter, no identity/role resolution, no
GM mode, and no toggle of any kind that exposes keeper content.** The only
public-vs-keeper distinction that exists anywhere is enforced *off* this surface;
this surface is always the public side (`public=1`, implicitly and unflippably).

1. **One fixed projection.** Keeper content is reachable only through the YAML and
   the authoring tools — never through any reference URL, parameter, or header.

2. **The spoiler firewall is a projection, not a gate.** Files that were
   wholesale-excluded for *image/identity* value (`npcs.yaml`,
   `portrait_manifest.yaml`) move into **public-projected inclusion**: they
   render, but only ever as the public projection — name + role + appearance +
   portrait for an NPC; image-source-only for the portrait manifest. Hidden NPC
   fields (`ocean`, `history_seeds`, `initial_disposition`,
   `distinguishing_features`), ADR-053 belief/clue data, and `seed_tropes.yaml` /
   `tropes.yaml` are **never rendered** by this surface. An optional authored
   `public_description` overrides the derived appearance text when present (no
   backfill required to ship).

3. **Two readers, one public surface (the upside of dropping GM mode).** Because
   there is no GM view to defer the crunch to, the *public* page must serve both
   the narrative reader (prose, portraits, legends) and the mechanical reader
   (Sebastien/Jade) on one surface. Wherever a section carries a **public**
   mechanical fact — faction disposition, world axis snapshot, survivability-pool
   label, POI type — it is surfaced as a legible chip beside the flavor, never
   buried and never toggled. This is a *player-facing* legibility decision and is
   explicitly appropriate per CLAUDE.md (expose the math in player surfaces); it
   is **not** dev observability (no OTEL/GM-panel framing belongs in the rendered
   page). The spoiler boundary is unchanged: only *public* mechanical facts —
   nothing that reveals scenario structure.

4. **Decoupled from session identity.** The surface MUST NOT read
   `Cf-Access-Authenticated-User-Email`, import `views.py:is_gm()`, or otherwise
   resurrect a seat/role concept. It is a static, public, pre-session document.

## Consequences

**Positive:**

- Deletes an entire subsystem before it is built — no audience param, no identity
  resolution, no GM-email allowlist, no synced-config maintenance.
- The page is structurally incapable of leaking keeper content: there is no
  parameter to flip, so the spoiler invariant is testable as "no query string
  changes the output."
- Forces the crunch onto the public surface, which is the correct outcome for the
  mechanical-first players (the two-reader principle) — a benefit that a GM-mode
  escape hatch would have quietly undermined.
- Keeps the firewall aligned with the perception-filtering doctrine (ADR-104/105):
  the projection happens at the presenter layer, not via an access gate.

**Negative / costs:**

- Authors who want the full view must use the YAML or the authoring tools — there
  is no "view everything in the browser" convenience on this surface. Accepted:
  that is the authoring tools' job, not the table tool's.
- Per-NPC public text quality depends on authored fields (`appearance`, optional
  `public_description`); rough content reads rough until 74-3 smooths it. Accepted
  and non-blocking.

## Alternatives considered

- **`?audience=gm` filter (v2 brief).** Rejected — built on the false
  "one player is the GM" premise; adds an auth-shaped subsystem for a non-existent
  reader; creates a self-spoil URL; risks reviving the deleted `is_gm` axis.
- **Keep v1 wholesale `EXCLUDED_FILES` for npcs/portraits.** Rejected — it is the
  reason portraits can never appear; the value of the surface is the imagery, and
  a *projection* (not exclusion) lets the image through while keeping secrets out.
- **Identity-defaulted audience (Cloudflare email → role), URL override.**
  Rejected for the same root reason — there is no GM reader to default *to* on a
  table tool; reusing ADR-119 identity here would manufacture a role the table
  does not have.

## Implementation pointer

Design spec: `docs/superpowers/specs/2026-06-01-lore-reference-images-and-audience-split-design.md`.
Tracked as epic 65, stories 65-7 (populate `r2_manifest.json`), 65-8 (POI gallery),
65-9 (public Cast/portrait projection), 65-10 (TOC repair), with follow-ons 65-11
(POI map) and 65-12 (world timeline). Renderer: `sidequest-server/sidequest/server/
reference_renderer.py` + `reference_presenters.py`.

## Amendment — Server-Projection / React-Render Seam (epic 100, 2026-06-08)

> **Design-only; implementation tracked as epic 100.** This amendment changes the
> *render substrate* of the reference pages, not the audience doctrine above. The
> original ADR (and the epic-65 work) assumed **server-rendered HTML**
> (`reference_renderer.py` → `HTMLResponse`). Epic 100 splits that single
> responsibility into a **server-side public projection** (JSON) and a
> **client-side React renderer** (SPA routes). Everything the Decision section
> says about the one fixed *public* projection still holds — the firewall is the
> same, and it moves *earlier* (to the JSON boundary), strengthening it. Authority:
> `docs/superpowers/specs/2026-06-08-reference-pages-react-migration-design.md`.

### A1 — The seam: the server projects, React renders

The reference surface is split into two responsibilities across a JSON boundary:

- **Server projects.** `/reference/api/*` emits the *public projection* as JSON —
  the same single fixed public view ADR-135 already mandates, now serialized as
  data rather than HTML.
- **React renders.** Session-free `/reference/*` SPA routes fetch that JSON and
  render it (generic node-tree + section components: POI, Cast, Map, Timeline,
  generic YAML).

This does not reopen the audience question. There is still exactly **one**
projection — the public one (Decision §1). The seam only moves *where the HTML is
assembled* (browser, not server); it does not add a parameter, a role, or a
keeper view.

### A2 — C1: the firewall is a projection at the JSON boundary, never a CSS hide

The spoiler firewall (`reference_visibility.py`: `PUBLIC_STEMS`, `KEEPER`
carve-outs, `EXCLUDED_FILES`, `npc_pool.is_projectable`) is **reused verbatim** as
the projection gate for the JSON API. **Keeper fields never cross the JSON
boundary.** Shipping full YAML and hiding keeper fields in the React layer is a
spoiler leak in the browser network tab — explicitly forbidden. The keeper set
(`ocean`, `history_seeds`, `initial_disposition`, `distinguishing_features`,
ADR-053 belief/clue data, `seed_tropes.yaml`, `tropes.yaml`) is **absent from the
payload**. The security boundary is JSON emit, not the component tree, and is
deterministic and testable there. This is a *strengthening* of Decision §2/§4:
the projection moves off the presenter and onto the wire.

### A3 — C2: the no-session invariant

The `/reference/*` SPA routes MUST mount and fully render with **no WebSocket
session, no auth, no character, no genre-pack session state.** Pack and world come
from the URL (`:pack`, `:world`) only. This is the direct continuation of Decision
§4 ("static, public, pre-session document") into the client: hosting the pages
inside the game client must not couple them to the live-session machinery. Test
strategy: each reference route renders under a bare `MemoryRouter` with **no**
session/WS provider in scope.

### A4 — C3: theme without a session

`useGenreTheme` is session-coupled today (CSS variables injected from a `theme_css`
WebSocket event on connect, 8 s grace timer). A session-free reference route has no
such event. **Resolution:** reuse the *mechanism* (CSS-var `<style>` injection) but
feed it from the reference **projection JSON** (keyed by `:pack`), not the WS event.
The projection API emits theme tokens as part of its payload — one theme source per
surface, no session dependency.

### A5 — C4: determinism is preserved (d3-dag)

The cartography map carries a byte-deterministic layout contract (node order
independent of YAML key order; a test pins it). The migration preserves
determinism: the replacement layout is **d3-dag** (Sugiyama layered — legible *and*
deterministic), **not** `d3-force` (which jiggles per load). The determinism test
moves from Python to Vitest against the shared React/TypeScript layout module.

### A6 — C5: public URL home

Today the canonical public URL is server-hosted (`GET /reference/lore/...` →
`HTMLResponse`). After migration the canonical URL is the **SPA route**
(`/reference/lore/:pack/:world`). FastAPI **retires the HTML routes**, **keeps
`/reference/api/*`** (JSON), and serves the SPA index as a history-fallback for
`/reference/*` deep-links. (If the SPA is hosted separately, a redirect-to-SPA-host
substitutes; the deploy topology is confirmed at planning time.) The "works without
the game running" property of Decision §4 is retained — the canonical home is just
a static SPA route instead of a server HTML route.

### A7 — Shared map component is drill-aware-ready (epic 98 / ADR-141 bridge)

The cartography Map section becomes **one** d3-dag component shared by the reference
page and the in-game `MapOverlay` (killing the `reference_map.py` ↔
`cartographyLayout.ts` split-brain). Because **ADR-141** (epic 98, story 98-3)
layers a campaign↔local **scale/drill** view-model onto that same in-game map, the
shared component (story 100-10) must be built **drill-aware-ready**:

- Render the cartography graph **self-contained** — no assumption that
  `MapWidget`'s current feed shape or `orbital` toggle is permanent (epic 98
  reworks both).
- Accept a `selected`/`active` node prop and expose a node-select callback, so
  98-3 can layer drill-down **without forking the layout**.

**Ownership boundary:** 100-10 owns the **layout engine** (the d3-dag module + Map
component); 98-3 owns the **view-model** (scale rendering, drill affordances).
**Sequencing:** 100-10 lands first (epic 100 is p2, epic 98 is p3); 98-3 builds
against the shared component, not the deleted `cartographyLayout.ts`. See ADR-141's
2026-06-08 amendment for the reciprocal note, and the epic-100 spec for the
`cartography.yaml` edge semantics (`adjacent` = topology the layout consumes;
`routes` = jump-mechanics annotations the layout must not treat as dangling).

### Implementation (epic 100)

Phased: **Phase 0** — this amendment (story 100-1). **Phase 1** — JSON projection
API + firewall reuse (lore generic/Cast/POI/Timeline sections, rules page, theme
tokens; stories 100-2…100-7). **Phase 2** — React reference shell + session-free
theme injector (100-8, 100-9). **Phase 3** — shared d3-dag Map + React section
components (100-10, 100-11). **Phase 4** — cutover: flip `/reference/*` to the SPA,
retire the Python HTML emitters + `islands.js`, keep `reference_visibility.py`
feeding the API (100-12). Phase 1 Slice A (lore map projection JSON API) already
shipped via `sidequest-server` PR #762.
