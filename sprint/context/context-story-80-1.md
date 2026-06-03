---
parent: context-epic-80.md
workflow: tdd
---

# Story 80-1: Genre-grouped world picker + scoped lobby theming (house chrome)

## Business Context

The lobby is the first surface every player sees, and today it betrays the
genre→world model the game is built on: a flat 20-world list buries genre, two
scope-mixed reference links sit orphaned, and the chrome wears whatever world the
player last entered. This story fixes all three from the one root cause — scope
leakage — so the lobby reads as *the lobby*: a neutral "house" shell, worlds
grouped by genre under sticky headers, and Rules/Lore links that sit where their
scope is self-evident. For a career GM (Keith) a lobby that cosplays the last
world reads as a bug; for mechanics-first players (Sebastien, Jade) genre is the
rule pack they navigate by; for inclusive pacing (Alex) a legible grouped list
with clean keyboard nav beats a cramped flat scroll. UI-only, no engine change.

## Technical Guardrails

**Key files to modify** (per plan File Structure):
- `src/hooks/useChromeArchetype.ts` — add `house`; pure `applyArchetypeToElement`;
  archetype-driven `useChromeArchetype(archetype)`; new `useScopedChromeArchetype(ref, archetype)`.
- `src/styles/archetype-chrome.css` — append a neutral `[data-archetype="house"]` block.
- `src/App.tsx` — exported pure `resolveRootArchetype(phase, currentGenre)`; drive
  `house` on `<html>` during the `connect` phase, genre archetype otherwise.
- `src/screens/lobby/OptionList.tsx` — optional `groups` mode (sticky headers,
  single radiogroup, header Rules link, auto-scroll-to-selected).
- `src/screens/lobby/WorldPreview.tsx` — scope selected world's archetype to the
  card via ref; host the world-scoped Lore link in the card header.
- `src/screens/ConnectScreen.tsx` — build `OptionGroup[]`; remove the standalone
  lobby `ReferenceLinks`; wire `archetype`/`loreHref` to `WorldPreview`.

**Patterns to follow:**
- Extend the shared `OptionList`, don't fork it — flat `items` mode must stay
  unchanged (`ModePicker` and any genre-only caller depend on it).
- `getArchetypeForGenre` stays **fail-loud** on unknown genre slugs (No Silent
  Fallbacks). `house` is a separate, explicitly-selected identity, never thrown.
- `applyArchetypeToElement` must track and remove previously-set CSS-var keys on
  every change — no leak across archetype swaps. `null` clears the attribute + keys.
- `[data-archetype]` CSS selectors resolve against any ancestor, so scoping the
  attribute to the card subtree confines genre fonts/treatment to that subtree.
- Locked signatures (use verbatim across all tasks): `ChromeArchetype` (4 members),
  `applyArchetypeToElement(el, archetype, prevKeys)`, `useChromeArchetype(archetype)`,
  `useScopedChromeArchetype(ref, archetype)`, `OptionGroup {slug, label, rulesHref, items}`,
  `WorldPreview` props `archetype?`/`loreHref?`, `resolveRootArchetype(phase, currentGenre)`.

**What NOT to touch:**
- **Do NOT delete `src/components/ReferenceLinks.tsx` or its tests.** It is RETAINED —
  `src/components/GameBoard/widgets/NarrativeWidget.tsx` still renders it in-game.
  Only the *lobby* usage in `ConnectScreen` is removed (Task 6/8).
- **Do NOT change in-game chrome.** `resolveRootArchetype` returns the genre
  archetype for `creation`/`game`; the in-world experience must be byte-for-byte
  as before. Only the `connect` phase changes.
- **Do NOT scope `useGenreTheme` / per-card palette** — out of scope. The card
  adopts genre *fonts/borders* (archetype) only; colors stay from the root palette.

## Scope Boundaries

**In scope:**
- Phase 1 (theming): `house` archetype (type + CSS-var table + CSS block); factored
  `applyArchetypeToElement`; archetype-driven root hook; `useScopedChromeArchetype`;
  `house` on `<html>` during connect phase via `resolveRootArchetype`; selected
  world's archetype scoped to the preview card.
- Phase 2 (picker): grouped `OptionList` mode; `ConnectScreen` builds `OptionGroup[]`;
  Rules→genre header (pack-scoped), Lore→preview card (world-scoped); standalone
  lobby `ReferenceLinks` removed; auto-scroll-to-selected; list given real height.

**Out of scope:**
- Accordion/collapse behavior; per-genre color-coding or accent palettes; search/filter.
- Any change to in-game `<html>` chrome.
- Per-card palette scoping (`useGenreTheme`).
- Deletion of `ReferenceLinks.tsx` (retained for in-game caller).
- Final visual fine-tuning of the `house` typefaces/ink/cream/scrollbar values
  (implementation detail within the "distinct editorial" direction — does not change architecture).

## AC Context

**AC1 — `house` archetype exists and is distinct.** `ARCHETYPE_PROPERTIES["house"]`
is defined with a serif `--font-body` distinct from parchment's; all four
archetypes have distinct `--border-radius` (set size 4). A `[data-archetype="house"]`
CSS block exists. *Test:* assert props table entries + radius-set size 4 + CSS
selector presence.

**AC2 — archetype-driven hooks + scoped applier.** `useChromeArchetype("parchment")`
sets `data-archetype="parchment"` on `<html>` and injects the CSS vars (no longer
treats the input as a genre slug, so it no longer throws on archetype names);
switching cleans up prior keys; `null` removes the attribute; genre color vars
(`--primary`) are never clobbered. `useScopedChromeArchetype(ref, "terminal")`
applies to `ref.current` and leaves `<html>` untouched; it is a no-op when the ref
is empty. *Edge cases:* empty ref, switching archetypes, `null` clear, color-var
preservation.

**AC3 — no genre leak in the lobby (regression).** `resolveRootArchetype("connect", "space_opera")`
=== `"house"`; `resolveRootArchetype("connect", null)` === `"house"`;
`resolveRootArchetype("creation", "space_opera")` === `"terminal"`;
`resolveRootArchetype("game", "road_warrior")` === `"rugged"`;
`resolveRootArchetype("game", null)` === `null`. *This is the leak regression
test* — the lobby root must be `house` regardless of the last-entered genre.

**AC4 — preview card scopes the genre archetype.** `WorldPreview` with
`archetype="terminal"` puts `data-archetype="terminal"` on the card element
(`data-testid="world-preview-card"`) and NOT on `document.documentElement`.
`archetype`/`loreHref` props are optional (default `null`) so existing call sites
keep typechecking.

**AC5 — grouped picker.** `OptionList groups={...}` renders one genre header per
group; a single `role="radiogroup"`; one `role="radio"` per world across all groups;
worlds sorted within group, groups sorted by label. *Edge:* `rulesHref: null` omits
the Rules link.

**AC6 — keyboard nav across boundaries.** Arrow keys move across genre boundaries
(last world of group 1 → first world of group 2) and skip headers; Home/End jump to
first/last world; roving tabindex correct. Headers are `role="presentation"`,
excluded from the radio set.

**AC7 — link relocation.** Rules renders on each genre header with the pack href +
`aria-label` (e.g. "Space Opera rules"); Lore renders in the preview card with the
world href + `aria-label` (e.g. "The Aureate Span lore"); the old standalone
`reference-links` block is absent from the lobby. Disabled treatment preserved when
an href is unavailable.

**AC8 — auto-scroll.** A preselected/restored world is scrolled into view
(`scrollIntoView` called); `scroll-mt`/`scroll-margin-top` equal to sticky-header
height so the focus ring is never occluded. *Test:* stub `Element.prototype.scrollIntoView`.

**AC9 — wiring (every-suite-needs-a-wiring-test).** The grouped `OptionList` is
actually rendered by `ConnectScreen` in production (not just unit-tested in
isolation): `ConnectScreen` shows genre headers + world radios + header Rules links.
`ReferenceLinks` still imported by `NarrativeWidget` (in-game), gone from `ConnectScreen`.

**AC10 — gate.** Full UI suite green (`npx vitest run`); lint clean (no unused
imports); `npm run build` succeeds (types resolve).

## Assumptions

- Existing test fixtures in `WorldPreview.test.tsx` and the `ConnectScreen` test
  files expose reusable mock `pack`/`world`/`genres` objects and a render helper
  (`renderConnectScreen`/`mockGenres`) — Dev reuses them rather than re-authoring.
- jsdom has no `scrollIntoView`; tests must stub `Element.prototype.scrollIntoView`.
- The existing `chrome-archetype-css.test.ts` only checks for presence of the three
  current selectors, so adding `house` does not break it (an optional house
  assertion is added).
- `bg-background` Tailwind token is configured for the sticky header; if not, the
  `bg-[var(--background)]` arbitrary-value form (already used for `--primary`) is
  the fallback.
- Repo policy: `sidequest-ui` is gitflow off `develop`; branch
  `feat/80-1-lobby-identity-grouped-picker` already created; PR targets `develop`.

If any assumption proves wrong during implementation, log a Design Deviation and
notify SM.

## Interaction Patterns

- **Pick flow:** player scans genre-grouped sticky-headered list → selects a world
  radio (arrow keys flow across genre boundaries, headers skipped) → preview card
  on the right "lights up" in that world's genre archetype while the shell stays
  neutral house → Rules (on the genre header) and Lore (in the card) open in new tabs.
- **Return-to-lobby:** entering a world then returning leaves the shell `house`,
  never the entered genre (the leak fix).

## Accessibility Requirements

- Single `role="radiogroup"` spanning all worlds; roving tabindex over world radios
  only; genre headers `role="presentation"`, visible but skipped by keyboard nav.
- Sticky headers get a `z-index`; world radios get `scroll-margin-top` equal to the
  sticky-header height so auto-scroll clears the header and the focus-visible ring
  is never occluded.
- Rules/Lore are tab-reachable `<a target="_blank" rel="noopener noreferrer">` with
  descriptive `aria-label`s (visible text is only "Rules"/"Lore").
- House chrome + header/link text meet WCAG 2.1 AA contrast (4.5:1 body, 3:1 large);
  verify the house ink-on-cream pairing explicitly.

## Visual Constraints

- `house` archetype: humanist serif body, neutral UI sans, `3px` radius (distinct
  from parchment 2px / terminal 0px / rugged 4px). Neutral ink-on-cream
  "library/card-catalog" feel — reads as *the menu*, not a world.
- List gets real vertical height (`max-h-[70vh]`) so the top row no longer clips;
  scrollbar styled thin to the house chrome.
- Genre flavor (fonts/borders) is confined to the preview card; the shell stays house.
