# Story 83-1: Rebuild ConnectScreen as the Standing Folio lobby — genre accordion + cinematic preview

## Business Context

The lobby is the first surface every player meets. The current `ConnectScreen` groups
worlds in a scrolling list capped at `70vh` with `overflow-y: auto` — Keith opened a
Claude Design session specifically because he "hates the scrollbar" and wanted a holistic
redesign. He reviewed three directions and **locked in Direction A — "The Standing
Folio"**: the lobby reframed as a literary manuscript title page. This is a primary-
audience polish: the lobby must feel like the threshold to "an evening's adventure, told
by lamplight," and it must hold the full real catalogue (11 genres) in the fold with no
scrollbar.

## Technical Guardrails

- **Structural + visual only.** Keep every existing data path and behavior. This is not a
  data-model change — it is a re-layout + re-skin of `ConnectScreen` and its
  `src/screens/lobby/*` children.
- **Reuse existing wiring, do not reinvent.** Source the real catalogue from the existing
  `/api/genres` feed (`GenresResponse` / `GenreMeta` / `WorldMeta` in `@/types/genres`).
  Reuse `WorldPreview`, `CurrentSessions`, `JourneyHistory`, `ModePicker`, `useSessions`,
  `useStartGame`, `useDisplayName`, `historyStore`, `toneAxes`. `OptionList` is the
  scrolling list being replaced.
- **Ignore the prototype's data.** `design-reference/lobby-standing-folio/project/worlds.js`
  invents 20 fake worlds across 11 genres with fabricated copy. It is a visual fixture
  only — wire the real catalogue, never the prototype data.
- **Do not port the prototype structure.** The reference HTML uses inline-Babel + UMD
  React. Recreate the *visual output* in the repo's real React/TS/Vitest stack; do not
  copy its internal structure.
- **No new endpoints.** Use existing `/api/genres`, the sessions feed behind `useSessions`,
  and the dev-gated `/dev/scenes`.
- **Hero art stays a placeholder.** Per-genre/per-world atmospheric **CSS-gradient**
  backgrounds standing in for the runtime AI render (the designer's own note). Wiring real
  hero imagery / image generation is explicitly out of scope.
- **Personal project — no Jira, no work-org anything** (per `sidequest-ui/CLAUDE.md`).
- **No silent fallbacks / no stubs / verify wiring** (project principles): if a `WorldMeta`
  field is absent, degrade gracefully *and visibly*, never fabricate.

## Scope Boundaries

**In scope:** Re-layout of `ConnectScreen` to the Standing Folio (masthead name ritual →
two-pane folio card: genre accordion + cinematic preview → commit row → below-the-fold
sections), the Dark Folio palette/type from `tokens.css`, subtle per-genre accent shift,
responsive breakpoints, scrollbar elimination, ARIA/keyboard semantics, and updating the
existing test suite to prove the new structure.

**Out of scope:** Real hero imagery / image-gen wiring, new server endpoints, new
`WorldMeta` fields, changes to the start/join protocol, character-creation flow, and any
backend change. If a required preview field (era, tone, blurb, inspirations, dinkus)
does not exist on real `WorldMeta`, that is a Delivery Finding — not a license to add a
server field in this story.

## AC Context

Nine acceptance criteria (authoritative copy in `sprint/epic-83.yaml`, story 83-1):

1. **Masthead opening ritual** — ornament dinkus, Pirata One "SideQuest" wordmark, italic
   tagline, centered autofocus name input with placeholder; name persists to/from
   localStorage exactly as today (`useDisplayName` + the existing `sidequest-connect` key).
2. **Genre accordion, zero scrollbar** — one collapsible row per genre from `/api/genres`;
   opening a genre expands its worlds inline and collapses the previously open one; eyebrow
   shows live "{N} worlds across {M} genres" computed from real data.
3. **Keyboard + ARIA** — genre headers are `aria-expanded` buttons with a rotating chevron;
   worlds are `role=radio` within `role=radiogroup`, `aria-checked` on the selected world;
   visible accent focus-ring on keyboard focus across headers, rows, mode buttons, Start.
4. **Cinematic preview on selection** — hero art (CSS-gradient placeholder) + genre label,
   world title, era line, tone chips (from `toneAxes`), blurb, "Inspired by" list, all from
   real `WorldMeta` with graceful fallbacks for absent fields.
5. **Commit row end-to-end** — Solo/Multiplayer segmented toggle drives the Start label
   ("Start Adventure" vs "Start or Join") and the start/join flow via `useStartGame`; Start
   disabled with no world selected; Rules/Lore links present.
6. **Below-the-fold wired to real data** — "Currently in this world" (live presence via
   `useSessions`, empty-state copy when none), "Past journeys" (`historyStore`, click
   re-selects that world), dev-gated "Scene library" (`/dev/scenes`, only when available).
7. **Subtle per-genre accent shift only** — selecting a world sets the `[data-genre]`
   accent per the `tokens.css` map; type + structure stay the manuscript house style.
8. **Responsive + motion** — single-column folio + two-up index grid at ≤880px; stacked
   commit row + full-width Start at ≤560px; global scrollbars hidden; reduced-motion
   respected (transform-only entrance, visible end-state as base — no opacity:0-stuck nodes).
9. **Tests updated/replaced** — `ConnectScreen.test.tsx`, `ConnectScreen.reference.test.tsx`,
   `lobby-*.test.tsx` updated to prove the new structure, including a wiring test that the
   redesigned screen is mounted on the real app route and reachable, not rendered in
   isolation.

## Assumptions

- Real `WorldMeta` may NOT supply every field the prototype shows (era, tone axes, blurb,
  inspirations, dinkus glyph). Tests assert graceful fallbacks rather than the prototype
  shape. Confirm the real shape against `@/types/genres` and `toneAxes`.
- The existing `ConnectScreen` already fetches `/api/genres`, persists name/genre/world to
  localStorage, and renders the below-the-fold sections — so the data plumbing exists and
  is reused, not rebuilt.
- "11 genres" is the live pack count; the eyebrow count must be derived from data, not
  hardcoded.

## Interaction Patterns

- Accordion: single-open semantics — opening genre B collapses genre A. The genre holding
  the currently selected world is open by default on load.
- World selection updates the preview pane and the `[data-genre]` accent; it does not start
  the game. Start/Join is the only commit action.
- Past-journey rows are clickable and re-select that world (driving the preview), matching
  today's behavior.

## Accessibility Requirements

- Accordion headers: `<button>` with `aria-expanded`; worlds: `role=radiogroup` /
  `role=radio` + `aria-checked`.
- Visible focus indication (accent ring) on every interactive control.
- `prefers-reduced-motion`: entrance animations are transform-only with a visible
  end-state as the base — content must never be stuck at `opacity:0` if the animation
  clock never runs (the designer hit and fixed exactly this bug in the prototype).

## Visual Constraints

- Dark Folio palette from `design-reference/lobby-standing-folio/project/tokens.css`:
  `--folio-paper #1a140d`, `--folio-ink #ecdba8`, `--folio-gold #d4a945` (house accent),
  `--folio-crimson #d6735e`; per-genre `[data-genre]` accent overrides.
- Type: EB Garamond (body), Pirata One (display/masthead), Oswald (eyebrows/labels).
- Hero art: layered CSS gradients per world (placeholder for runtime render).
- No genre re-skin — only the accent colour travels with the selected genre; structure and
  type remain the manuscript house style.
- Pixel/layout target: `design-reference/lobby-standing-folio/project/SideQuest Lobby.html`.

## Story Status

- **Story ID:** 83-1
- **Epic:** 83 (Lobby Redesign — The Standing Folio)
- **Points:** 5
- **Workflow:** tdd
- **Repos:** ui (sidequest-ui)
- **Priority:** p2
