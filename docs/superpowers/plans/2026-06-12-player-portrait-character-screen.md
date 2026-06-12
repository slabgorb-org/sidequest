# Player Portrait on the Character Screen + Rounded-Rect Framing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the portrait a player picks during character creation appear on every character surface, and render all character portraits as a consistent rounded rectangle (1:1 aspect).

**Architecture:** One server wiring fix (resolve the stored portrait slug into an R2 URL at `PARTY_STATUS` emit time via a new pure helper) plus a UI restyle (extract a shared `PortraitFrame` component and route all three character-screen avatars through it). No new infrastructure, no content, no daemon changes.

**Tech Stack:** Python 3.12 / FastAPI / pytest (server); React / TypeScript / Tailwind / Vitest + Testing Library (UI).

**Spec:** `docs/superpowers/specs/2026-06-12-player-portrait-character-screen-design.md`

---

## File Structure

**Server (`sidequest-server`):**
- `sidequest/server/asset_urls.py` — add `resolve_player_portrait_url` next to `resolve_asset_url`. The path-convention string lives here once.
- `sidequest/server/views.py` — `party_member_from_character` (line ~581) calls the helper instead of passing `portrait_url=None`.
- `sidequest/server/rest.py` — `list_chargen_portraits` (line ~964) calls the helper instead of inlining the path string, so the picker list and the emit path can never drift.
- `tests/server/test_asset_urls.py` — unit coverage for the helper.
- `tests/server/test_player_portrait_party_status.py` (new) — fixture test that drives the real `party_member_from_character` emit path.

**UI (`sidequest-ui`):**
- `src/components/PortraitFrame.tsx` (new) — shared img-or-initials frame, rounded-rect, FOLIO-themed.
- `src/components/CharacterPanel.tsx` — header avatar, party rows, and Companions rows route through `PortraitFrame`.
- `src/components/CharacterSheet.tsx` — portrait routes through `PortraitFrame`.
- `src/components/__tests__/PortraitFrame.test.tsx` (new) — component behavior.
- `src/components/__tests__/CharacterPanel.test.tsx` — extend with rounded-rect assertions.
- `src/components/__tests__/CharacterSheet.test.tsx` — extend with rounded-rect assertions.

**Note on two repos:** This plan spans `sidequest-server` and `sidequest-ui`, which are separate git subrepos. Commit inside each subrepo (run `git` from the subrepo root). Tasks 1–3 are server; Tasks 4–7 are UI. The two halves are independent and can be done in either order.

---

## Task 1: `resolve_player_portrait_url` helper

**Files:**
- Modify: `sidequest-server/sidequest/server/asset_urls.py`
- Test: `sidequest-server/tests/server/test_asset_urls.py`

- [ ] **Step 1: Write the failing tests**

Add to the end of `sidequest-server/tests/server/test_asset_urls.py`:

```python
def test_player_portrait_url_resolves_slug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIDEQUEST_ASSET_BASE_URL", raising=False)
    url = asset_urls.resolve_player_portrait_url(
        "space_opera", "perseus_cloud", "drifter_voidborn_a1"
    )
    assert url == (
        "https://cdn.slabgorb.com/genre_packs/space_opera/worlds/"
        "perseus_cloud/assets/portraits/drifter_voidborn_a1.png"
    )


def test_player_portrait_url_none_for_falsy_ref() -> None:
    assert asset_urls.resolve_player_portrait_url("space_opera", "perseus_cloud", None) is None
    assert asset_urls.resolve_player_portrait_url("space_opera", "perseus_cloud", "") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-server && uv run pytest tests/server/test_asset_urls.py -k player_portrait -v`
Expected: FAIL with `AttributeError: module 'sidequest.server.asset_urls' has no attribute 'resolve_player_portrait_url'`

- [ ] **Step 3: Write the helper**

In `sidequest-server/sidequest/server/asset_urls.py`, add directly after the `resolve_asset_url` function (after its `return url`, before the `# Matches a CSS url() token` comment block):

```python
def resolve_player_portrait_url(
    genre_slug: str, world_slug: str, portrait_ref: str | None
) -> str | None:
    """Resolve a picked player-portrait slug to its R2 URL.

    Returns None when ``portrait_ref`` is falsy (player skipped, or the world
    ships no picker art). Otherwise builds the canonical world-portrait path
    — ``genre_packs/<genre>/worlds/<world>/assets/portraits/<slug>.png``, the
    same convention the render script writes and the chargen picker list reads
    — and delegates to :func:`resolve_asset_url`.
    """
    if not portrait_ref:
        return None
    return resolve_asset_url(
        f"genre_packs/{genre_slug}/worlds/{world_slug}/assets/portraits/{portrait_ref}.png"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd sidequest-server && uv run pytest tests/server/test_asset_urls.py -k player_portrait -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/asset_urls.py tests/server/test_asset_urls.py
git commit -m "feat(server): add resolve_player_portrait_url helper"
```

---

## Task 2: Wire the helper into the `PARTY_STATUS` emit path

**Files:**
- Modify: `sidequest-server/sidequest/server/views.py` (the `portrait_url=None` at ~line 581, inside `party_member_from_character`)
- Test: `sidequest-server/tests/server/test_player_portrait_party_status.py` (create)

- [ ] **Step 1: Write the failing test**

Create `sidequest-server/tests/server/test_player_portrait_party_status.py`:

```python
"""party_member_from_character resolves a picked portrait_ref to its R2 URL.

This is the wiring test for the 2026-06-12 player-portrait fix: the stored
``Character.portrait_ref`` must surface as ``PartyMember.portrait_url`` through
the real emit path, not stay hardcoded ``None``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sidequest.game.character import Character
from sidequest.game.creature_core import CreatureCore, HpPool, Inventory
from sidequest.game.persistence import GameMode
from sidequest.game.session import GameSnapshot
from sidequest.game.turn import TurnManager
from sidequest.genre.loader import load_genre_pack
from sidequest.server import views
from sidequest.server.asset_urls import resolve_player_portrait_url
from sidequest.server.session_handler import _SessionData

CONTENT_GENRE_PACKS = Path(__file__).resolve().parents[3] / "sidequest-content" / "genre_packs"


def _char(name: str, portrait_ref: str | None) -> Character:
    return Character(
        core=CreatureCore(
            name=name,
            description="d",
            personality="p",
            inventory=Inventory(),
            hp=HpPool(current=10, max=10, base_max=10),
        ),
        backstory=f"{name}'s tale.",
        char_class="Delver",
        race="Human",
        portrait_ref=portrait_ref,
    )


def _sd(character: Character) -> _SessionData:
    return _SessionData(
        genre_slug="caverns_and_claudes",
        world_slug="mawdeep",
        player_name="P",
        player_id="player:1",
        snapshot=GameSnapshot(
            genre_slug="caverns_and_claudes",
            world_slug="mawdeep",
            turn_manager=TurnManager(interaction=1),
            characters=[character],
        ),
        repository=MagicMock(),
        dungeon_repository=MagicMock(),
        telemetry_sink=MagicMock(),
        genre_pack=load_genre_pack(CONTENT_GENRE_PACKS / "caverns_and_claudes"),
        orchestrator=MagicMock(),
        mode=GameMode.MULTIPLAYER,
    )


def test_portrait_ref_resolves_to_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIDEQUEST_ASSET_BASE_URL", raising=False)
    character = _char("Kael", "delver_human_a1")
    pm = views.party_member_from_character(
        MagicMock(), _sd(character), character, player_id="player:1", player_name="P"
    )
    assert pm.portrait_url == resolve_player_portrait_url(
        "caverns_and_claudes", "mawdeep", "delver_human_a1"
    )
    assert pm.portrait_url is not None


def test_no_portrait_ref_yields_none() -> None:
    character = _char("Kael", None)
    pm = views.party_member_from_character(
        MagicMock(), _sd(character), character, player_id="player:1", player_name="P"
    )
    assert pm.portrait_url is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_player_portrait_party_status.py -v`
Expected: FAIL on `test_portrait_ref_resolves_to_url` — `assert None is not None` (because `views.py` still hardcodes `portrait_url=None`). `test_no_portrait_ref_yields_none` passes already.

- [ ] **Step 3: Wire the helper into views.py**

In `sidequest-server/sidequest/server/views.py`, add the import. The file uses local/lazy imports inside `party_member_from_character`; add `resolve_player_portrait_url` to the existing `from sidequest.server.session_helpers import _resolve_location_display` neighborhood — but it lives in `asset_urls`, so add a dedicated line inside the function's import block (right after the `from sidequest.server.session_helpers import _resolve_location_display` line):

```python
    from sidequest.server.asset_urls import resolve_player_portrait_url
```

Then change the `portrait_url=None,` line (~581) to:

```python
        portrait_url=resolve_player_portrait_url(
            sd.genre_slug, sd.world_slug, character.portrait_ref
        ),
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_player_portrait_party_status.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-server
git add sidequest/server/views.py tests/server/test_player_portrait_party_status.py
git commit -m "fix(server): resolve picked portrait_ref into PARTY_STATUS portrait_url"
```

---

## Task 3: Converge `list_chargen_portraits` on the helper

**Files:**
- Modify: `sidequest-server/sidequest/server/rest.py` (the inline path at ~line 964, inside `list_chargen_portraits`)
- Test: `sidequest-server/tests/server/test_player_portrait_party_status.py` (extend)

This removes the duplicated path-convention string so the picker list and the emit path resolve identically.

- [ ] **Step 1: Write the failing convergence test**

Append to `sidequest-server/tests/server/test_player_portrait_party_status.py`:

```python
def test_rest_picker_url_matches_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """The chargen picker list and the PARTY_STATUS emit path must build the
    same URL for a given slug — guards against the two path strings drifting."""
    monkeypatch.delenv("SIDEQUEST_ASSET_BASE_URL", raising=False)
    from sidequest.server import rest

    # rest.py must build picker URLs via the shared helper, not an inline string.
    import inspect

    src = inspect.getsource(rest.create_rest_router)
    assert "resolve_player_portrait_url" in src, (
        "list_chargen_portraits must build its portrait_url via "
        "resolve_player_portrait_url so it cannot drift from the emit path"
    )
```

> Note: this is a source-presence guard (acceptable here per the spec's drift-prevention intent — the behavioral equality is already covered by Task 1's helper test plus Task 2's emit test; both call the same helper, so equality is guaranteed by construction). If `list_chargen_portraits` is a nested function inside `create_rest_router`, `inspect.getsource(rest.create_rest_router)` captures it.

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd sidequest-server && uv run pytest tests/server/test_player_portrait_party_status.py::test_rest_picker_url_matches_helper -v`
Expected: FAIL — `resolve_player_portrait_url` not yet referenced in `rest.py`.

- [ ] **Step 3: Switch rest.py to the helper**

In `sidequest-server/sidequest/server/rest.py`, update the import at line 32:

```python
from sidequest.server.asset_urls import resolve_asset_url, resolve_player_portrait_url
```

Then replace the `"portrait_url": resolve_asset_url(...)` block (~line 962–967) with:

```python
                    "portrait_url": resolve_player_portrait_url(genre, world, slug),
```

Remove the now-stale explanatory comment immediately above it (the `# Canonical world-portrait path convention:` block) since the convention now lives in the helper's docstring.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd sidequest-server && uv run pytest tests/server/test_player_portrait_party_status.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Run the full asset + party-status suites and lint**

Run: `cd sidequest-server && uv run pytest tests/server/test_asset_urls.py tests/server/test_player_portrait_party_status.py tests/server/test_multiplayer_party_status.py -v && uv run ruff check sidequest/server/asset_urls.py sidequest/server/views.py sidequest/server/rest.py`
Expected: all PASS, no lint errors.

- [ ] **Step 6: Commit**

```bash
cd sidequest-server
git add sidequest/server/rest.py tests/server/test_player_portrait_party_status.py
git commit -m "refactor(server): chargen picker list shares resolve_player_portrait_url"
```

---

## Task 4: `PortraitFrame` component

**Files:**
- Create: `sidequest-ui/src/components/PortraitFrame.tsx`
- Test: `sidequest-ui/src/components/__tests__/PortraitFrame.test.tsx`

`PortraitFrame` is the single img-or-initials frame. It renders a square (`aspect-square`) rounded-rect image; on missing `url` or image `onError`, it shows the initials monogram in an identically-framed box. FOLIO theming (gold border, paper background, display-font monogram) is threaded through props so each consumer keeps its current look.

- [ ] **Step 1: Write the failing tests**

Create `sidequest-ui/src/components/__tests__/PortraitFrame.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PortraitFrame } from "../PortraitFrame";

describe("PortraitFrame", () => {
  it("renders an img with the radius class when url is present", () => {
    render(
      <PortraitFrame url="/renders/kael.png" name="Kael Stormbreaker" sizeClass="w-12 h-12" radiusClass="rounded-lg" />,
    );
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "/renders/kael.png");
    expect(img).toHaveClass("rounded-lg");
    expect(img).not.toHaveClass("rounded-full");
    expect(img).toHaveClass("aspect-square");
  });

  it("renders initials when url is absent", () => {
    render(<PortraitFrame name="Kael Stormbreaker" sizeClass="w-12 h-12" radiusClass="rounded-lg" />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    const placeholder = screen.getByTestId("portrait-frame-initials");
    expect(placeholder).toHaveTextContent("KS");
    expect(placeholder).toHaveClass("rounded-lg");
    expect(placeholder).not.toHaveClass("rounded-full");
  });

  it("swaps img -> initials on image error", () => {
    render(<PortraitFrame url="/renders/missing.png" name="Kael Stormbreaker" sizeClass="w-12 h-12" radiusClass="rounded-lg" />);
    fireEvent.error(screen.getByRole("img"));
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByTestId("portrait-frame-initials")).toHaveTextContent("KS");
  });

  it("caps initials at two characters", () => {
    render(<PortraitFrame name="The Cfrom Mountain Stir Trir" sizeClass="w-8 h-8" radiusClass="rounded-md" />);
    expect(screen.getByTestId("portrait-frame-initials")).toHaveTextContent("TC");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/PortraitFrame.test.tsx`
Expected: FAIL — `Cannot find module '../PortraitFrame'`.

- [ ] **Step 3: Write the component**

Create `sidequest-ui/src/components/PortraitFrame.tsx`:

```tsx
import { useState } from "react";

// Cap at 2 initials — avatar badges are ~2ch wide, and uncapped initials on
// a long sentence-name produce noise like "TCMSTRIR". (Mirrors the prior
// toAvatarInitials in CharacterPanel; centralized here.)
export function toAvatarInitials(name: string): string {
  const words = name.split(/\s+/).filter(Boolean);
  if (words.length === 0) return "";
  if (words.length === 1) return words[0][0].toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

export interface PortraitFrameProps {
  /** Resolved portrait URL; when absent or on load error, initials render. */
  url?: string | null;
  /** Display name — source of the alt text and the initials monogram. */
  name: string;
  /** Tailwind size classes, e.g. "w-12 h-12". */
  sizeClass: string;
  /** Tailwind rounded-rect radius class, e.g. "rounded-lg". Never rounded-full. */
  radiusClass: string;
  /** Inline style for the <img> (e.g. FOLIO gold border). */
  imgStyle?: React.CSSProperties;
  /** Inline style for the initials box (e.g. FOLIO paper/crimson + display font). */
  initialsStyle?: React.CSSProperties;
  /** Extra classes appended to the <img> frame. */
  imgClassName?: string;
  /** Extra classes appended to the initials frame. */
  initialsClassName?: string;
}

export function PortraitFrame({
  url,
  name,
  sizeClass,
  radiusClass,
  imgStyle,
  initialsStyle,
  imgClassName = "",
  initialsClassName = "",
}: PortraitFrameProps) {
  const [errored, setErrored] = useState(false);
  const showImg = Boolean(url) && !errored;

  if (showImg) {
    return (
      <img
        src={url as string}
        alt={name}
        onError={() => setErrored(true)}
        className={`${sizeClass} ${radiusClass} aspect-square object-cover shrink-0 ${imgClassName}`}
        style={imgStyle}
      />
    );
  }

  return (
    <span
      aria-hidden="true"
      data-testid="portrait-frame-initials"
      className={`${sizeClass} ${radiusClass} aspect-square shrink-0 flex items-center justify-center ${initialsClassName}`}
      style={initialsStyle}
    >
      {toAvatarInitials(name)}
    </span>
  );
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/PortraitFrame.test.tsx`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
cd sidequest-ui
git add src/components/PortraitFrame.tsx src/components/__tests__/PortraitFrame.test.tsx
git commit -m "feat(ui): add shared PortraitFrame component (rounded-rect, img-or-initials)"
```

---

## Task 5: Route `CharacterPanel` avatars through `PortraitFrame`

**Files:**
- Modify: `sidequest-ui/src/components/CharacterPanel.tsx` (header avatar ~208–230; party rows ~479–500; Companions rows ~658–671; the local `toAvatarInitials` ~126–132)
- Test: `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx`

- [ ] **Step 1: Write the failing assertions**

In `sidequest-ui/src/components/__tests__/CharacterPanel.test.tsx`, extend the existing portrait tests. Replace the body of `it("displays character portrait when available", ...)` (around line 74) and the placeholder test (around line 87) with these, and add a rounded-rect guard:

```tsx
  it("displays character portrait when available", () => {
    render(<CharacterPanel {...baseProps()} character={CHARACTER} />);
    const img = screen.getAllByRole("img").find((el) => el.getAttribute("src") === "/renders/kael.png");
    expect(img).toBeDefined();
    expect(img).toHaveClass("rounded-lg");
    expect(img).not.toHaveClass("rounded-full");
  });

  it("renders portrait placeholder with rounded-rect initials when no portrait_url", () => {
    const noPortrait = { ...CHARACTER, portrait_url: undefined };
    render(<CharacterPanel {...baseProps()} character={noPortrait} />);
    const placeholder = screen.getByTestId("portrait-frame-initials");
    expect(placeholder).toHaveTextContent("K");
    expect(placeholder).toHaveClass("rounded-lg");
    expect(placeholder).not.toHaveClass("rounded-full");
  });
```

> If the existing test referenced `data-testid="character-portrait-placeholder"`, update those references to `portrait-frame-initials` (the new shared testid). Use whatever prop-builder the file already has — `baseProps()` is a placeholder for the existing render-prop pattern in this test file; keep the file's actual existing setup.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/CharacterPanel.test.tsx`
Expected: FAIL — header img still has `rounded-full`; no `portrait-frame-initials` testid yet.

- [ ] **Step 3: Replace the header avatar**

In `sidequest-ui/src/components/CharacterPanel.tsx`, add the import near the top (with the other component imports):

```tsx
import { PortraitFrame } from "./PortraitFrame";
```

Replace the header avatar block (the `{character.portrait_url ? ( <img ... rounded-full ... /> ) : ( <div ... rounded-full ... >{toAvatarInitials(character.name)}</div> )}` at ~208–231) with:

```tsx
        <PortraitFrame
          url={character.portrait_url}
          name={character.name}
          sizeClass="w-12 h-12"
          radiusClass="rounded-lg"
          imgStyle={{ borderColor: FOLIO.gold }}
          imgClassName="border border-[var(--primary)]/30"
          initialsStyle={{
            background: FOLIO.paper2,
            borderColor: FOLIO.gold,
            color: FOLIO.crimson,
            fontFamily: FONT_DISPLAY,
            fontSize: 28,
          }}
          initialsClassName="border border-[var(--primary)]/30 text-[var(--primary)] text-xl font-semibold"
        />
```

- [ ] **Step 4: Replace the party rows avatar**

Replace the party-rows block (`{c.portrait_url ? ( <img ... rounded-full ... /> ) : ( <span ... rounded-full ...>{toAvatarInitials(c.character_name || c.name)}</span> )}` at ~479–500) with:

```tsx
                <PortraitFrame
                  url={c.portrait_url}
                  name={c.character_name || c.name}
                  sizeClass="w-8 h-8"
                  radiusClass="rounded-md"
                  imgStyle={{ borderColor: FOLIO.gold }}
                  imgClassName="border border-border"
                  initialsStyle={{
                    background: FOLIO.paper,
                    color: FOLIO.crimson,
                    borderColor: FOLIO.gold,
                    fontFamily: FONT_DISPLAY,
                    fontSize: 14,
                    fontWeight: 400,
                  }}
                  initialsClassName="bg-secondary text-secondary-foreground text-[10px] font-bold border border-border"
                />
```

- [ ] **Step 5: Replace the Companions rows avatar**

Replace the Companions `<span ... w-8 h-8 rounded-full ...>{toAvatarInitials(c.name)}</span>` block (~658–671) with (Companions are initials-only — no `url` prop):

```tsx
              <PortraitFrame
                name={c.name}
                sizeClass="w-8 h-8"
                radiusClass="rounded-md"
                initialsStyle={{
                  background: FOLIO.paper,
                  color: FOLIO.gold,
                  borderColor: FOLIO.rule,
                  fontFamily: FONT_DISPLAY,
                  fontSize: 14,
                  fontWeight: 400,
                }}
                initialsClassName="bg-secondary/40 text-secondary-foreground/80 text-[10px] font-bold border border-border/60"
              />
```

- [ ] **Step 6: Remove the now-dead local `toAvatarInitials`**

The local `toAvatarInitials` (lines ~124–132) is now unused in `CharacterPanel.tsx` (all three call sites moved into `PortraitFrame`). Delete the function and its comment block. If TypeScript/ESLint reports it still used elsewhere in the file, re-import it from `./PortraitFrame` instead of deleting; otherwise remove it.

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/CharacterPanel.test.tsx`
Expected: PASS. If other assertions in this file referenced `character-portrait-placeholder`, they now need `portrait-frame-initials` — update any stragglers.

- [ ] **Step 8: Commit**

```bash
cd sidequest-ui
git add src/components/CharacterPanel.tsx src/components/__tests__/CharacterPanel.test.tsx
git commit -m "refactor(ui): CharacterPanel avatars use PortraitFrame (rounded-rect)"
```

---

## Task 6: Route `CharacterSheet` portrait through `PortraitFrame`

**Files:**
- Modify: `sidequest-ui/src/components/CharacterSheet.tsx` (portrait block ~115–122)
- Test: `sidequest-ui/src/components/__tests__/CharacterSheet.test.tsx`

The current sheet renders nothing when `portrait_url` is absent. The spec wants the reframed initials monogram as the placeholder, so the new behavior renders `PortraitFrame` unconditionally (it falls back to initials internally).

- [ ] **Step 1: Write the failing assertions**

In `sidequest-ui/src/components/__tests__/CharacterSheet.test.tsx`, update the two portrait tests (around lines 60–70):

```tsx
  it('renders portrait image with the rounded-rect radius class', () => {
    render(<CharacterSheet data={BASE_DATA} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', '/renders/kael.png');
    expect(img).toHaveClass('rounded-xl');
    expect(img).not.toHaveClass('rounded-full');
  });

  it('renders the initials placeholder when portrait_url is absent', () => {
    const dataNoPortrait = { ...BASE_DATA, portrait_url: undefined };
    render(<CharacterSheet data={dataNoPortrait} />);
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    const placeholder = screen.getByTestId('portrait-frame-initials');
    expect(placeholder).toHaveClass('rounded-xl');
  });
```

> Note: this changes the second test's contract — previously the sheet rendered nothing without a portrait; now it renders an initials monogram. That is the intended new behavior per the spec (goal 3).

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/CharacterSheet.test.tsx`
Expected: FAIL — img has `rounded` not `rounded-xl`; no `portrait-frame-initials` when absent.

- [ ] **Step 3: Replace the portrait block**

In `sidequest-ui/src/components/CharacterSheet.tsx`, add the import at the top (after line 1's type import):

```tsx
import { PortraitFrame } from "./PortraitFrame";
```

Replace the conditional portrait block (~115–122):

```tsx
        {data.portrait_url && (
          <img
            src={data.portrait_url}
            alt={data.name}
            className="w-24 h-24 rounded object-cover"
          />
        )}
```

with:

```tsx
        <PortraitFrame
          url={data.portrait_url}
          name={data.name}
          sizeClass="w-24 h-24"
          radiusClass="rounded-xl"
          initialsClassName="bg-[var(--surface)] text-[var(--primary)] text-3xl font-semibold border border-[var(--primary)]/30"
        />
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/CharacterSheet.test.tsx`
Expected: PASS. Check `CharacterSheet.reference.test.tsx` too (Step 5 below) — it may assume "no img without portrait_url".

- [ ] **Step 5: Run adjacent sheet tests**

Run: `cd sidequest-ui && npx vitest run src/components/__tests__/CharacterSheet.reference.test.tsx`
Expected: PASS. If a test there asserts `queryByRole('img')` is absent for a portrait-less fixture, update it to expect `portrait-frame-initials` (the reframed placeholder is intended).

- [ ] **Step 6: Commit**

```bash
cd sidequest-ui
git add src/components/CharacterSheet.tsx src/components/__tests__/CharacterSheet.test.tsx src/components/__tests__/CharacterSheet.reference.test.tsx
git commit -m "refactor(ui): CharacterSheet portrait uses PortraitFrame (rounded-rect + initials fallback)"
```

---

## Task 7: Full-suite gate + lint

**Files:** none (verification only)

- [ ] **Step 1: Server gate**

Run: `cd sidequest-server && uv run ruff check . && uv run pytest tests/server/test_asset_urls.py tests/server/test_player_portrait_party_status.py tests/server/test_multiplayer_party_status.py -q`
Expected: no lint errors; all PASS.

- [ ] **Step 2: UI gate**

Run: `cd sidequest-ui && npx tsc --noEmit && npx vitest run src/components/__tests__/PortraitFrame.test.tsx src/components/__tests__/CharacterPanel.test.tsx src/components/__tests__/CharacterSheet.test.tsx src/components/__tests__/CharacterSheet.reference.test.tsx`
Expected: typecheck clean; all PASS.

- [ ] **Step 3: Aggregate gate (catches any consumer this plan missed)**

Run from orchestrator root: `just client-lint && just client-test`
Expected: PASS. Any failing test elsewhere that asserted `rounded-full` on a character avatar, or `character-portrait-placeholder` testid, is a consumer this restyle touches — update its assertion to the rounded-rect / `portrait-frame-initials` contract. Do **not** broaden scope to NPC/cast/scrapbook surfaces (out of scope per spec Non-Goals).

- [ ] **Step 4: Manual smoke (optional but recommended)**

Per the spec, verify end-to-end against a running stack: start a session, pick a portrait in chargen for a world with picker art (e.g. `space_opera/perseus_cloud`), confirm the portrait shows in the CharacterPanel header, party row, and CharacterSheet as a rounded rectangle; then create a character and skip the portrait, confirm the initials monogram renders in the same rounded-rect frame.

Run (orchestrator root): `just server` and `just client` in separate panes, or `just tmux`.

---

## Spec Coverage Check

- **Goal 1** (portrait shows on CharacterPanel header, party rows, CharacterSheet) → Tasks 2, 5, 6.
- **Goal 2** (rounded rectangle, 1:1, radius scaled to size) → Task 4 (`aspect-square`, `radiusClass`) + Tasks 5/6 (`rounded-lg`/`rounded-md`/`rounded-xl`).
- **Goal 3** (no-portrait keeps reframed initials monogram) → Task 4 fallback + Tasks 5/6 initials styling.
- **Server design** (helper + 2 call sites, resolve-at-emit Approach A) → Tasks 1, 2, 3.
- **UI design** (one shared PortraitFrame, Companions consistency) → Tasks 4, 5.
- **Error handling** (null → initials; 404 → onError swap) → Task 4 Steps 1/3 (onError → initials), tested in Task 4 Step 1.
- **Testing** (helper unit, emit fixture/wiring test, REST convergence, PortraitFrame, extended panel/sheet) → Tasks 1, 2, 3, 4, 5, 6.
- **Non-Goals respected:** no generation/content (no daemon/content tasks), NPC/cast/scrapbook untouched (Task 7 Step 3 guard), square aspect only, no persisted URL (helper resolves at emit time), no new OTEL span (none added — matches spec's carve-out).
