# SideQuest Inspector — Tufte redesign

## What this is
A redesign of the **SideQuest Inspector**, a developer telemetry dashboard for an AI game engine
("SideQuest"). The original is a React/TS codebase (tabs + d3 charts, dark "consumer" theme with
bright colors, rounded cards, a donut chart). Source lives in the user's local mounted folder
`Dashboard/` (DashboardApp/Header/Tabs, `charts/`, `tabs/`, `shared/constants.ts`).

The deliverable is a single Design Component: **`SideQuest Inspector.dc.html`**. It is a faithful,
mostly-visual prototype driven by deterministic synthetic telemetry (seeded RNG in `makeData()`),
not live data.

## Design direction (locked with the user)
Edward **Tufte** principles, applied in **dark mode** (user prefers Tufte over "flashy consumer"):
- No boxes: strip card borders/fills/rounded corners. Structure = hairline rules (`#2a2a2e`) + whitespace.
- Layering & separation: muted context (faint dotted leaders `#3a3a40`, thin range-frame axes); data is the brightest ink. ONE emphasis accent reserved for degraded points / reference lines.
- Maximize data-ink: no gridlines, no legends-in-boxes (use direct labels), no chartjunk.
- Type: **Georgia serif small-caps** for labels, **JetBrains Mono** for every data value.
- Density: denser is better.
- Palette (in `theme` getter): bg `#19191b`, ink `#e7e5df`, muted `#86847d`, accent is a **tweakable prop** (user set default to `#4ab4cf`). Series hues muted & share chroma: steel/ochre/sage/mauve. Agent colors: narrator=steel, ensemble=sage, creature_smith=mauve, dialectician=ochre.

## Build conventions
- All quantitative graphics are SVG built with `React.createElement` in logic-class methods
  (`hist, agentDots, scatter, tokens, tiers, phases, flame, spark`), exposed via `renderVals()`.
  This is the deliberate exception to "no createElement layout" — charts can't be template markup.
  Layout chrome (header, tabs, titles, stat labels) IS template markup so it stays editable.
- Charts use `this.svg(W,H,children)` → viewBox + width:100% so they scale.
- Tweak props (in `data-props`): `accent` (color), `showRefs` (boolean ref/avg lines), `density` (enum).

## What's been built
- **Shell**: header (status, turns/errors/p95 + sparkline, quiet text buttons), session line, Tufte tabs.
- **Timing tab** (default, index 3): summary stats w/ sparkline · phase breakdown (bars + avg tick) ·
  duration histogram (median/p95 ref lines) · per-agent dot plot (min–max range + inline sparkline) ·
  duration-over-time scatter (direct-labeled 5-turn mean + p95, degraded = ✕) ·
  **token & cache** chart (stacked cached/fresh in-bars, cache-hit sparkline w/ cold-start misses, summary) ·
  extraction-tier sorted bar plot (replaced the donut).
- **Timeline tab** (index 0): dependency-aware **flame graph** — spans nested caller ▸ callee,
  faded containers vs solid leaf work, critical span outlined in accent; turn-list sidebar selects
  turns; details panel. Span trees are generated per turn in `makeData()` (hierarchical, with cache fields).
- **State tab** (index 1): world-state inspector — location + discovered regions · trope progression
  bar plot · character stat line (HP bullet bar) + inventory table (narrative-weight bars w/ named/evolved
  threshold ticks) · NPC registry table with **OCEAN 5-bar personality sparkline** per NPC · infra line.
  Working search filter (`state.stateFilter`). Data: `makeState()` (literal, flavorful). Helpers: `hpBar,
  weightBar, oceanGlyph, tropesChart`.
- Other tabs (Subsystems, Console, Prompt, Lore, Encounters, Mechanical) show a quiet placeholder — out of scope.

## In flight / next
- **PENDING:** user asked to **combine the Timeline tab into the Timing tab** (one tab showing both
  the flame chart/turn inspector AND the timing charts). Not yet done.
- Possible follow-ups discussed: cache-savings (latency/cost avoided) view; parallel/async spans in the
  flame graph (media often overlaps).
