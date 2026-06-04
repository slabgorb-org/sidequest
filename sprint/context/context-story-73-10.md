# Context: Story 73-10 — Distinct beat-impact effect styling

**Story:** 73-10 (Epic 73: Confrontation Engine Hardening, 2pts, trivial, sidequest-ui-only)

**Title:** Distinct beat-impact effect styling — ship genre/theme CSS for beat-impact-{resolution,inert,setback,advance,tag,backfire} so the three zero-ish cases (resolution by-design vs inert miss vs negative setback) read DIFFERENTLY visually.

---

## Problem Statement

Story 73-7 surfaced opponent-side beat-impact readouts in the ConfrontationOverlay (numeric deltas + summaries), and 73-4 introduced the `BeatImpactPanel` to explain mechanical outcomes (e.g., "Clean Exit — resolves the confrontation, no dial change by design").

**The gap:** `BeatImpactPanel` emits a `data-effect` discriminator with six categorical values (`resolution`, `inert`, `setback`, `advance`, `tag`, `backfire`), but the CSS to visually distinguish them is **missing or insufficient**. An unstyled genre renders them alike, which defeats the legibility goal for mechanics-first players (Sebastien/Jade).

**Critical distinction:** Three "zero-ish" cases must read visually different at a glance:
1. **`resolution`** — The confrontation ended by design (positive terminal state). The player committed a resolution beat and it resolved the encounter. Example: "Clean Exit — resolves the confrontation (no dial change by design)". This is **GOOD**.
2. **`inert`** — A genuine miss or dial-suppressed beat. The beat landed but nothing happened mechanically. Example: "The barb misses — nothing lands." This is **NEUTRAL**.
3. **`setback`** — Negative outcome. The player's dial worsened or the opponent advanced. Example: "Hamish ripostes — +2 to their edge." This is **BAD**.

Without CSS distinction, all three read as the same low-motion state, making it hard for a player to immediately understand "did I succeed, do nothing, or get hurt?"

---

## Current Implementation

### BeatImpactPanel Component
**File:** `sidequest-ui/src/components/ConfrontationOverlay.tsx` (lines 654-684)

```typescript
function BeatImpactPanel({
  impact,
  opponent,
}: {
  impact: BeatImpactView;
  opponent?: BeatImpactView | null;
}) {
  return (
    <div
      data-testid="beat-impact"
      data-effect={impact.effect}
      data-dial-moved={impact.dial_moved ? "true" : "false"}
      className={`beat-impact mt-2 p-2 rounded border beat-impact-${impact.effect}`}
    >
      <span className="text-xs">{impact.summary}</span>
      <span data-testid="beat-impact-own" className="text-xs">
        {impact.own ?? 0}
      </span>
      {opponent != null && (
        <span data-testid="beat-impact-opponent" className="text-xs">
          {opponent.own ?? 0}
        </span>
      )}
    </div>
  );
}
```

**Key points:**
- Emits `data-effect={impact.effect}` as a data attribute (values: `resolution`, `inert`, `setback`, `advance`, `tag`, `backfire`)
- Applies dynamic CSS class `beat-impact-${impact.effect}` (e.g., `beat-impact-resolution`, `beat-impact-inert`)
- Currently renders semantic text and numeric deltas; no visual styling applied beyond the Tailwind utilities (`p-2 rounded border`)

### BeatEffect Type Definition
**File:** `sidequest-ui/src/components/ConfrontationOverlay.tsx` (lines 90-96)

```typescript
export type BeatEffect =
  | "advance"
  | "setback"
  | "resolution"
  | "tag"
  | "backfire"
  | "inert";
```

---

## Genre Theme System (ADR-079)

The UI uses a **theme injection system** (`useGenreTheme` hook) that allows each genre pack to provide custom CSS delivered via the `theme_css` SESSION_EVENT.

### How Theme CSS Works

1. **Server-side:** The genre pack author defines CSS in `sidequest-content/genre_packs/<genre>/styles/` (or equivalent in the pack structure).
2. **Runtime delivery:** When a session connects, the server emits a `theme_css` SESSION_EVENT containing the genre's full CSS as a string.
3. **Client injection:** `useGenreTheme` (in `sidequest-ui/src/hooks/useGenreTheme.ts`) receives the CSS and injects it into a `<style>` tag in the document `<head>` with id `genre-theme-css`.
4. **CSS custom properties:** Genre CSS defines `:root[data-genre]` CSS variables (e.g., `--accent`, `--primary`, `--encounter-player`, `--encounter-opponent`) that override inherited dark-mode defaults.

### Available Theme Variables

From the current ConfrontationOverlay code, the following theme variables are already in use:
- **`--encounter-player`** — cool blue for the player's edge/dial (oklch-based)
- **`--encounter-opponent`** — amber/red for the opponent's edge/dial (oklch-based)
- **`--background`**, **`--foreground`**, **`--accent`**, **`--primary`** — base palette

**Additional semantic tokens likely available in genre CSS:**
- Success/positive hues (for `resolution`, `advance`, `tag`)
- Neutral/muted hues (for `inert`)
- Warning/danger hues (for `setback`, `backfire`)

### How to Wire New Styles

New beat-impact CSS should:
1. **Use theme variables** — Derive colors from `--accent`, `--primary`, `--encounter-player`, `--encounter-opponent`, or define new genre-scoped variables (e.g., `--beat-impact-resolution`, `--beat-impact-setback`).
2. **Apply via `data-effect` selector** — Scope styles to `.beat-impact[data-effect="resolution"]` etc., so the genre's palette automatically applies.
3. **Stay in genre CSS** — The styling belongs in the `theme_css` payload, not in hardcoded React styles or Tailwind classes (which would be invisible to genre customization).

---

## Acceptance Criteria

1. **CSS exists for all 6 data-effect values:**
   - `.beat-impact[data-effect="resolution"]`
   - `.beat-impact[data-effect="inert"]`
   - `.beat-impact[data-effect="setback"]`
   - `.beat-impact[data-effect="advance"]`
   - `.beat-impact[data-effect="tag"]`
   - `.beat-impact[data-effect="backfire"]`

2. **The three zero-ish cases are visually DISTINCT from each other:**
   - `resolution` — Reads as positive terminal (e.g., bright/green tint, checkmark glyph, or subtle glow)
   - `inert` — Reads as neutral low-motion (e.g., muted gray, dash glyph, or flat appearance)
   - `setback` — Reads as negative (e.g., warm/red tint, warning glyph, or subtle shadow)
   - Not just distinct from `advance/tag/backfire`, but distinguishable **from each other** at a glance.

3. **Styling is genre/theme-coherent:**
   - Colors derive from or respect theme tokens (ADR-079 convention).
   - Styling doesn't clash with any shipped genre's palette (test on at least `tea_and_murder` and `space_opera` so the polychrome set is covered).
   - The six states remain legible across dark-mode and light-mode genres.

4. **A test asserts the distinct styling is applied per data-effect:**
   - New test or enhancement to `ConfrontationOverlay.beatimpact.test.tsx` or `ConfrontationOverlay.beatimpact.coverage.test.tsx`.
   - Example: Assert that `.beat-impact[data-effect="resolution"]` has computed `background-color` or other style differing from `[data-effect="inert"]` or `[data-effect="setback"]`.
   - Prevents an unstyled regression (e.g., if all `.beat-impact` rules are deleted, the test fails).

5. **No change to the data-effect discriminator logic itself:**
   - The server/payload contract (73-7/73-8) remains untouched.
   - This is CSS/presentation only.

---

## Scope Boundary & Related Work

### In Scope (This Story)
- CSS for all 6 effect states
- Visual distinctness of the three zero-ish cases
- Theme-coherent styling
- Test coverage for the styling

### Out of Scope (Related, Not This Story)
- **"You / Them" text labels on the numeric deltas** (73-7 deferred; candidate for enhancement but NOT primary AC)
- **Richer cross-delta readout** (numeric sign, formatted display; related but separate concern)
- **Render-gate fix** (73-13 — BeatImpactPanel render suppression when player impact absent)
- **Server-side impact calculation** (already done in 73-4, 73-7, 73-8)

---

## Investigation Notes

### Theme CSS Delivery
- Server emits `theme_css` on the CONFRONTATION payload or as a SESSION_EVENT
- Client-side injection happens in `useGenreTheme` hook
- The injected CSS contains genre-scoped variables and component-specific rules
- Genres currently shipped: `caverns_and_claudes`, `elemental_harmony`, `heavy_metal`, `mutant_wasteland`, `neon_dystopia`, `pulp_noir`, `road_warrior`, `space_opera`, `spaghetti_western`, `tea_and_murder`, `wry_whimsy` (11 total)

### Code References
- **BeatImpactPanel:** `sidequest-ui/src/components/ConfrontationOverlay.tsx:654-684`
- **BeatEffect type:** `sidequest-ui/src/components/ConfrontationOverlay.tsx:90-96`
- **ConfrontationOverlay mount point:** `sidequest-ui/src/components/ConfrontationOverlay.tsx:733-737` (renders BeatImpactPanel when `data.last_beat_impact` is present)
- **Theme hook:** `sidequest-ui/src/hooks/useGenreTheme.ts`
- **SIDE_COLOR_VAR usage example:** `sidequest-ui/src/components/ConfrontationOverlay.tsx:273-276` (how to reference theme tokens in React)
- **Tests:** 
  - `sidequest-ui/src/components/__tests__/ConfrontationOverlay.beatimpact.test.tsx` (73-4 tests; validates data-effect is present)
  - `sidequest-ui/src/components/__tests__/ConfrontationOverlay.beatimpact.coverage.test.tsx` (73-9 coverage hardening)
  - `sidequest-ui/src/components/__tests__/ConfrontationOverlay.opponentbeatimpact.test.tsx` (73-7 opponent readout)

### How Genre Theme CSS is Currently Structured
- **Example reference:** Look at how `--encounter-player` and `--encounter-opponent` are used in the EdgeBar and HpBar components (inline-styled via `SIDE_COLOR_VAR`)
- **Convention:** Theme variables are declared in `:root[data-genre] { ... }` in the injected genre CSS
- **Cascading:** `:root[data-genre]` specificity (0,2,0) wins over `.dark` (0,1,0) on the root element, ensuring genre colors take precedence

### Story Dependency
- **73-7** (completed) surfaced the opponent impact readout and numeric deltas — this story adds the visual styling to make them legible
- **73-8** (completed) made hp_depletion impacts truthful — styling applies to both dial-threshold and hp_depletion encounters
- **73-9** (completed) hardened test coverage for the data-effect discriminator — this story's test will validate styling actually applies

---

## Player Impact (Audience: Sebastien/Jade)

Sebastien and Jade are **mechanics-first players** who want to understand the numerical outcomes of every action. ADR-002 (SOUL principles) and CLAUDE.md's player rubric highlight that exposing mechanical state visually — without requiring a tooltip or debug panel — is a **player-facing surface requirement**.

By making the six beat-impact effect states visually distinct:
- A player immediately recognizes "resolution" (confrontation ended) vs "inert" (nothing happened) vs "setback" (dial worsened) without reading the summary text.
- The mechanical clarity reinforces the 73-4 goal: a CritSuccess that moves no dial reads as **intentional and good**, not broken.
- Across multiple confrontations in a session, consistent visual language builds familiarity and reduces cognitive load.

---

## Testing Strategy

1. **Existing test suite** should be enhanced with a styling assertion:
   - Test that `[data-effect="resolution"]` renders with distinct computed styles (e.g., `background-color` or `border-color`) vs `[data-effect="inert"]` and `[data-effect="setback"]`.
   - Example: Use `getComputedStyle()` in a Vitest test to assert the hexadecimal or oklch color values differ.

2. **Visual regression prevention:**
   - Ensure any future stylesheet change that removes the beat-impact rules is caught by the test.

3. **Genre palette coverage:**
   - Spot-check the styling on at least two genres (e.g., `tea_and_murder` and `space_opera`) to ensure contrast and legibility across different theme palettes.

---

## Handoff Criteria

Before implementation completes:
- [ ] All 6 effect states have CSS rules and are visually distinct (especially the three zero-ish cases)
- [ ] Styling uses theme tokens (ADR-079 convention)
- [ ] Test added/enhanced to prevent regression
- [ ] Verified on at least 2 different genres
