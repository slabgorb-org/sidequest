# Chargen Appearance Field + Fate Aspect Sheet Surfacing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the chargen "what you look like" input its own `appearance` field (surfaced on the character sheet, reserved for a future visual-prompt feature), and surface a Fate character's aspects on the player sheet — fixing the 126-5 "Backstory shows the Description" bug as a side effect.

**Architecture:** The player's appearance text stops being joined into `background` and instead rides a new `SceneResult.appearance` carrier → `AccumulatedChoices.appearance` → `Character.appearance`, projected to the sheet via `CharacterSheetDetails`. Fate aspects (already on `CreatureCore.fate_sheet`, already shown to the narrator) get the same one-line projection onto the sheet. No ruleset conditionals: appearance is gated by a pack authoring the `identity_capture` description field; aspect surfacing is gated by `fate_sheet is not None`.

**Tech Stack:** Python 3 / pydantic v2 (sidequest-server), React + TypeScript + Vitest (sidequest-ui).

## Global Constraints

- **Branching (gitflow):** both repos' default branch is `develop`; feature branches `feat/<desc>`; PRs target `develop`. Do **not** target `main`. (The pre-existing empty `feat/126-5-chargen-backstory-field-mapping` ui branch may be reused or replaced.)
- **No Jira.** Personal project under `slabgorb-org`. Never reference tickets.
- **Additive + save-safe:** every new model/protocol field is defaulted (`""` / `default_factory=list`) so legacy saves validate and non-Fate / non-`the_story` characters render unchanged. Empty ⇒ the UI omits the section.
- **No source-text wiring tests** (CLAUDE.md): never grep production source as an assertion. Prove wiring with behavior/OTEL/fixture tests.
- **No content in unit tests:** server unit tests use synthetic fixtures, never real pack loads.
- **OTEL on subsystem decisions:** the chargen appearance capture emits an OTEL event so the GM panel sees it.
- **Server is the authority:** the sheet projection (`views.py`) is the single source for `appearance`/`fate_aspects`; the UI mirrors.
- **No `if ruleset == 'fate'` branches** in builder loop or UI renderer (inherited doctrine from the two parent specs).

**Spec:** `docs/superpowers/specs/2026-06-17-chargen-appearance-and-ruleset-backstory-design.md`. This plan implements **Deliverable A** (appearance) + **Deliverable B1** (Fate aspects on sheet) + **Open Question 1** (Task 6, vetoable). **Deliverable B2** (WWN typed-background beats the table-roll) is **deferred** — it is entangled with `acc.background`'s dual role as a WWN Background-catalog key (`builder.py:3177`, ADR-143 skill grants) and is the explicitly-lower-priority path; it needs its own characterization pass.

---

### Task 1: Capture `appearance` onto `Character` (server data path + the 126-5 regression)

**Files:**
- Modify: `sidequest/game/character.py` (add field near `background`/`drive`, ~line 148)
- Modify: `sidequest/game/builder.py` (`SceneResult` ~322, `AccumulatedChoices` ~446, `_apply_story` ~2539, accumulate loop ~1511, `build()` Character construction ~3281, backstory span region ~2962)
- Test: `tests/game/test_chargen_appearance_126_5.py` (new)

**Interfaces:**
- Produces: `Character.appearance: str` (default `""`); `AccumulatedChoices.appearance: str | None`; `SceneResult.appearance: str | None`. Later tasks read `Character.appearance`.

- [ ] **Step 1: Write the failing test**

Create `tests/game/test_chargen_appearance_126_5.py`. This mirrors how existing builder tests drive a synthetic `the_story` scene. Adjust the builder construction helper to match the nearest existing chargen test in `tests/game/` if the import path differs — the assertions are the contract.

```python
"""Story 126-5: the_story 'Appearance' input routes to Character.appearance,
never polluting background/backstory."""
from sidequest.game.builder import StoryInput


def _story_input(background: str, description: str) -> StoryInput:
    return StoryInput(pronouns="they/them", background=background, description=description)


def test_apply_story_routes_description_to_appearance_not_background(make_story_builder):
    """make_story_builder: a fixture/helper that returns a CharacterBuilder
    parked on an identity_capture (the_story) scene. See the sibling test
    tests/game/test_builder_story_scene.py for the canonical construction; reuse it."""
    builder = make_story_builder()
    builder.apply_response(_story_input(background="Former ratcatcher, owes the apothecary money.",
                                        description="Tall, soot-stained, missing a tooth."))
    char = builder.build()

    assert char.appearance == "Tall, soot-stained, missing a tooth."
    # The 126-5 bug: appearance must NOT appear in background or backstory.
    assert "soot-stained" not in (char.background or "")
    assert "soot-stained" not in char.backstory
    # The typed background still flows to the background channel unchanged.
    assert "ratcatcher" in builder.accumulated().background or ""
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `sidequest-server/`): `uv run pytest tests/game/test_chargen_appearance_126_5.py -v`
Expected: FAIL — `AttributeError: 'Character' object has no attribute 'appearance'` (or the make_story_builder helper needs importing from the sibling test; if so, copy its construction inline).

- [ ] **Step 3: Add the `appearance` field to `Character`**

In `sidequest/game/character.py`, immediately after the `background` / `drive` block (~line 149):

```python
    # Player-authored physical appearance ("what you look like"), captured at
    # chargen from the identity_capture scene's description input (Story 126-5).
    # Distinct from `background` (history) and `backstory`. Default "" so legacy
    # saves and characters built without an appearance input validate. Reserved
    # as the seed for a future custom visual-prompt feature.
    appearance: str = ""
```

- [ ] **Step 4: Add the accumulator + carrier fields**

In `sidequest/game/builder.py`, in `AccumulatedChoices` (after `reputation_bonus`, ~line 455):

```python
    appearance: str | None = None
```

In `SceneResult` (after `choice_label`, before `freeform_class_label`, ~line 338):

```python
    # Player-typed physical appearance from an identity_capture scene's
    # description input. Rides the SceneResult so go_back/revert drops it with
    # the scene. None for every non-story scene (Story 126-5).
    appearance: str | None = None
```

- [ ] **Step 5: Route description → appearance in `_apply_story`**

In `sidequest/game/builder.py::_apply_story` (~2568), replace the background-join block and the `SceneResult(...)` append:

```python
        # Background ("what you did before") stays the backstory channel.
        # Appearance ("what you look like") routes to its own field via the
        # SceneResult carrier — it MUST NOT be joined into background (Story 126-5).
        typed_background = response.background.strip()
        typed_appearance = response.description.strip()

        effects = MechanicalEffects(
            pronoun_hint=pronouns or None,
            background=typed_background or None,
        )

        hooks = extract_hooks(scene.id, effects)
        anchors = extract_anchors(scene.id, effects)

        self._results.append(
            SceneResult(
                input_type=response,
                effects_applied=effects,
                hooks_added=hooks,
                anchors_added=anchors,
                choice_description=None,
                appearance=typed_appearance or None,
                scene_id=scene.id,
                scene_index=scene_index,
            )
        )
```

- [ ] **Step 6: Accumulate appearance in the build loop**

In `sidequest/game/builder.py`, in the accumulate loop right after the `if eff.background is not None:` block (~1514):

```python
            if result.appearance is not None:
                acc.appearance = result.appearance
```

- [ ] **Step 7: Set `appearance` on the constructed Character + emit OTEL**

In `sidequest/game/builder.py::build()`, add `appearance=acc.appearance or "",` to the `Character(...)` call (next to `background=acc.background_label or "",`, ~3315):

```python
            appearance=acc.appearance or "",
```

And right after the existing backstory span (`span.add_event(SPAN_CHARGEN_BACKSTORY_COMPOSED, ...)`, ~2967), add the appearance OTEL event (raw-literal style, matching the existing `"chargen.abilities_resolved"` event):

```python
        span.add_event(
            "chargen.appearance_captured",
            {"present": bool(acc.appearance), "length": len(acc.appearance or "")},
        )
```

- [ ] **Step 8: Run test to verify it passes**

Run: `uv run pytest tests/game/test_chargen_appearance_126_5.py -v`
Expected: PASS.

- [ ] **Step 9: Guard against regressions in the broader builder suite**

Run: `uv run pytest tests/game/ -k "story or builder or chargen" -v`
Expected: PASS (no existing test asserted that description lands in background; if one does, it encoded the bug — update it to expect appearance and note the change in the commit body).

- [ ] **Step 10: Commit**

```bash
git add sidequest/game/character.py sidequest/game/builder.py tests/game/test_chargen_appearance_126_5.py
git commit -m "feat(126-5): route chargen appearance to Character.appearance, off the background join"
```

---

### Task 2: Project `appearance` onto the character sheet (server wire)

**Files:**
- Modify: `sidequest/protocol/models.py` (`CharacterSheetDetails`, after `foci` ~506)
- Modify: `sidequest/server/views.py` (`CharacterSheetDetails(...)` construction ~400)
- Test: `tests/server/test_sheet_appearance_projection.py` (new)

**Interfaces:**
- Consumes: `Character.appearance` (Task 1).
- Produces: `CharacterSheetDetails.appearance: str` (default `""`). The UI (Task 4) reads `sheetFacet.appearance`.

- [ ] **Step 1: Write the failing test**

Create `tests/server/test_sheet_appearance_projection.py`:

```python
"""The sheet projection carries Character.appearance to the wire (Story 126-5)."""
from sidequest.protocol.models import CharacterSheetDetails


def test_character_sheet_details_has_appearance_default():
    # Construct with the existing required fields plus appearance.
    sheet = CharacterSheetDetails(
        race="Human",
        stats={},
        abilities=[],
        backstory="An ex-ratcatcher.",
        personality="Wary",
        appearance="Tall, soot-stained, missing a tooth.",
    )
    assert sheet.appearance == "Tall, soot-stained, missing a tooth."


def test_character_sheet_details_appearance_defaults_empty():
    sheet = CharacterSheetDetails(
        race="Human", stats={}, abilities=[], backstory="x", personality="y",
    )
    assert sheet.appearance == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/test_sheet_appearance_projection.py -v`
Expected: FAIL — `ValidationError: unexpected keyword argument 'appearance'` (extra=forbid) or attribute missing.

- [ ] **Step 3: Add the field to `CharacterSheetDetails`**

In `sidequest/protocol/models.py`, after the `foci` field (~506):

```python
    appearance: str = ""
    """Player-authored physical appearance from chargen (Story 126-5). Empty
    for characters built without an appearance input; the UI renders the
    Appearance section only when non-empty."""
```

- [ ] **Step 4: Populate it in the projection**

In `sidequest/server/views.py`, in the `CharacterSheetDetails(...)` construction (~400), add after `foci=list(character.foci),`:

```python
        appearance=character.appearance,
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/server/test_sheet_appearance_projection.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add sidequest/protocol/models.py sidequest/server/views.py tests/server/test_sheet_appearance_projection.py
git commit -m "feat(126-5): project Character.appearance onto CharacterSheetDetails"
```

---

### Task 3: Project Fate aspects onto the character sheet (server wire, Deliverable B1)

**Files:**
- Modify: `sidequest/protocol/models.py` (`CharacterSheetDetails`, after `appearance`)
- Modify: `sidequest/server/views.py` (`CharacterSheetDetails(...)` construction ~400)
- Test: `tests/server/test_sheet_fate_aspects_projection.py` (new)

**Interfaces:**
- Consumes: `character.core.fate_sheet.aspects` (existing `list[fate_sheet.Aspect]`); the existing mapping `FateAspectEntry(text=a.text, kind=a.kind, free_invokes=a.free_invokes)` (mirrors `ruleset/fate_projection.py:113`).
- Produces: `CharacterSheetDetails.fate_aspects: list[FateAspectEntry]` (empty for non-Fate). The UI (Task 5) reads `sheetFacet.fate_aspects`.

- [ ] **Step 1: Write the failing test**

Create `tests/server/test_sheet_fate_aspects_projection.py`:

```python
"""Fate aspects reach the player sheet (Deliverable B1). Gated on fate_sheet
presence, never on ruleset string."""
from sidequest.protocol.models import CharacterSheetDetails, FateAspectEntry


def test_sheet_carries_fate_aspects():
    sheet = CharacterSheetDetails(
        race="Investigator", stats={}, abilities=[], backstory="x", personality="y",
        fate_aspects=[
            FateAspectEntry(text="Disgraced Pinkerton With a Long Memory", kind="high_concept"),
            FateAspectEntry(text="Can't Leave a Mystery Alone", kind="trouble"),
        ],
    )
    assert [a.kind for a in sheet.fate_aspects] == ["high_concept", "trouble"]


def test_sheet_fate_aspects_default_empty():
    sheet = CharacterSheetDetails(
        race="Human", stats={}, abilities=[], backstory="x", personality="y",
    )
    assert sheet.fate_aspects == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/server/test_sheet_fate_aspects_projection.py -v`
Expected: FAIL — unexpected keyword `fate_aspects`.

- [ ] **Step 3: Add the field to `CharacterSheetDetails`**

In `sidequest/protocol/models.py`, after the `appearance` field added in Task 2:

```python
    fate_aspects: list[FateAspectEntry] = Field(default_factory=list)
    """Named Fate character aspects (high_concept / trouble / character) for the
    player sheet (Deliverable B1). Reuses the FateAspectEntry wire type. Empty
    for non-Fate characters (fate_sheet is None); the UI renders an Aspects
    section only when non-empty (Sebastien/Jade legibility)."""
```

Note: `FateAspectEntry` is defined later in this same module (~974). If the model build raises an unresolved-forward-reference error in Step 5, the documented fix is to call `CharacterSheetDetails.model_rebuild()` at the end of the module, OR relocate the `FateAspectEntry` class definition above `CharacterSheetDetails`. Pydantic v2 resolves same-module forward refs in the common case; the test in Step 1 (which constructs the model) is the proof.

- [ ] **Step 4: Populate it in the projection**

In `sidequest/server/views.py`, in the `CharacterSheetDetails(...)` construction (~400), add after `appearance=character.appearance,`:

```python
        # Deliverable B1: surface named Fate aspects on the player sheet,
        # gated on fate_sheet presence (NOT ruleset string). Same Aspect→entry
        # mapping the narrator projection uses (ruleset/fate_projection.py).
        fate_aspects=(
            [
                FateAspectEntry(text=a.text, kind=a.kind, free_invokes=a.free_invokes)
                for a in character.core.fate_sheet.aspects
            ]
            if character.core.fate_sheet is not None
            else []
        ),
```

Add `FateAspectEntry` to the imports at the top of `views.py` if not already present (it is exported from `sidequest.protocol`):

```python
from sidequest.protocol import FateAspectEntry  # if not already imported
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/server/test_sheet_fate_aspects_projection.py -v`
Expected: PASS.

- [ ] **Step 6: Wiring test — a real-shaped Fate character projects aspects, a WN one does not**

Append to `tests/server/test_sheet_fate_aspects_projection.py` a behavior test that builds the projection through `views.py` for (a) a character whose `core.fate_sheet` carries two aspects and (b) one with `fate_sheet=None`, asserting `fate_aspects` is populated vs `[]`. Reuse the nearest existing `views.py` projection test fixture in `tests/server/` for character construction; assert on the projected `CharacterSheetDetails`.

```python
def test_projection_gates_aspects_on_fate_sheet_presence(make_sheet_for):
    """make_sheet_for: helper returning the CharacterSheetDetails that views.py
    builds for a given Character. Reuse the sibling tests/server projection
    fixture; the gate (fate_sheet is None → []) is the contract."""
    fate_sheet_details = make_sheet_for(with_fate_aspects=["High Concept Line", "Trouble Line"])
    assert len(fate_sheet_details.fate_aspects) == 2
    wn_details = make_sheet_for(with_fate_aspects=None)
    assert wn_details.fate_aspects == []
```

- [ ] **Step 7: Run the projection suite**

Run: `uv run pytest tests/server/test_sheet_fate_aspects_projection.py tests/server/test_sheet_appearance_projection.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add sidequest/protocol/models.py sidequest/server/views.py tests/server/test_sheet_fate_aspects_projection.py
git commit -m "feat(B1): surface Fate character aspects on CharacterSheetDetails"
```

---

### Task 4: Render the Appearance section on the sheet (UI)

**Files:**
- Modify: `src/components/CharacterSheet.tsx` (`CharacterSheetData` interface ~70; render, before the Backstory block ~284)
- Modify: `src/lib/partyStatusMapping.ts` (after the `backstory` mapping ~75)
- Test: `src/__tests__/character-sheet-appearance.test.tsx` (new)

**Interfaces:**
- Consumes: `sheetFacet.appearance` (Task 2 wire field).
- Produces: rendered "Appearance" block, omitted when empty.

- [ ] **Step 1: Write the failing test**

Create `src/__tests__/character-sheet-appearance.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CharacterSheet, type CharacterSheetData } from "../components/CharacterSheet";

const base: CharacterSheetData = {
  name: "Mara", class: "Investigator", class_reference_url: null,
  level: 1, stats: {}, abilities: [], class_moves: [],
  backstory: "An ex-ratcatcher.",
};

describe("CharacterSheet appearance", () => {
  it("renders the Appearance section when appearance is present", () => {
    render(<CharacterSheet data={{ ...base, appearance: "Tall, soot-stained, missing a tooth." }} />);
    expect(screen.getByText("Appearance")).toBeInTheDocument();
    expect(screen.getByText("Tall, soot-stained, missing a tooth.")).toBeInTheDocument();
  });

  it("omits the Appearance section when appearance is empty/absent", () => {
    render(<CharacterSheet data={base} />);
    expect(screen.queryByText("Appearance")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `sidequest-ui/`): `npx vitest run src/__tests__/character-sheet-appearance.test.tsx`
Expected: FAIL — `appearance` not on `CharacterSheetData` type and no "Appearance" text rendered.

- [ ] **Step 3: Add the field to the data type**

In `src/components/CharacterSheet.tsx`, in the `CharacterSheetData` interface after `backstory: string;` (~70):

```tsx
  /** Player-authored physical appearance from chargen (Story 126-5). Absent/
   *  empty ⇒ the Appearance section is NOT rendered. */
  appearance?: string;
```

- [ ] **Step 4: Render the Appearance block**

In `src/components/CharacterSheet.tsx`, immediately before the existing Backstory block (`<h3 ...>Backstory</h3>`, ~284):

```tsx
      {data.appearance && (
        <div>
          <h3 className="text-sm font-semibold mb-1">Appearance</h3>
          <p className="text-sm font-[var(--font-narrative)]">{data.appearance}</p>
        </div>
      )}
```

- [ ] **Step 5: Map the field from the facet**

In `src/lib/partyStatusMapping.ts`, after `backstory: (sheetFacet.backstory as string) ?? "",` (~75):

```ts
    appearance: (sheetFacet.appearance as string) || undefined,
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npx vitest run src/__tests__/character-sheet-appearance.test.tsx`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/components/CharacterSheet.tsx src/lib/partyStatusMapping.ts src/__tests__/character-sheet-appearance.test.tsx
git commit -m "feat(126-5): render Appearance section on the character sheet"
```

---

### Task 5: Render the Aspects section on the sheet (UI, Deliverable B1)

**Files:**
- Modify: `src/components/CharacterSheet.tsx` (import `FateAspectEntry`; `CharacterSheetData` interface; render after the Backstory block)
- Modify: `src/lib/partyStatusMapping.ts` (import `FateAspectEntry`; map `fate_aspects`)
- Test: `src/__tests__/character-sheet-aspects.test.tsx` (new)

**Interfaces:**
- Consumes: `sheetFacet.fate_aspects` (Task 3 wire field); the existing `FateAspectEntry` type from `src/types/payloads.ts:1089` (`{ text: string; kind: string; free_invokes: number }`).
- Produces: rendered "Aspects" block, omitted when empty.

- [ ] **Step 1: Write the failing test**

Create `src/__tests__/character-sheet-aspects.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CharacterSheet, type CharacterSheetData } from "../components/CharacterSheet";

const base: CharacterSheetData = {
  name: "Mara", class: "Investigator", class_reference_url: null,
  level: 1, stats: {}, abilities: [], class_moves: [], backstory: "x",
};

describe("CharacterSheet aspects", () => {
  it("renders Fate aspects with kind labels when present", () => {
    render(<CharacterSheet data={{ ...base, fate_aspects: [
      { text: "Disgraced Pinkerton With a Long Memory", kind: "high_concept", free_invokes: 0 },
      { text: "Can't Leave a Mystery Alone", kind: "trouble", free_invokes: 0 },
    ] }} />);
    expect(screen.getByText("Aspects")).toBeInTheDocument();
    expect(screen.getByText(/High Concept/)).toBeInTheDocument();
    expect(screen.getByText(/Disgraced Pinkerton With a Long Memory/)).toBeInTheDocument();
  });

  it("omits the Aspects section when there are none", () => {
    render(<CharacterSheet data={base} />);
    expect(screen.queryByText("Aspects")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/__tests__/character-sheet-aspects.test.tsx`
Expected: FAIL — `fate_aspects` not on the type, no "Aspects" rendered.

- [ ] **Step 3: Import the type and extend the data interface**

In `src/components/CharacterSheet.tsx`, add the import near the top (path from `src/components/` to `src/types/payloads.ts`):

```tsx
import type { FateAspectEntry } from "../types/payloads";
```

In the `CharacterSheetData` interface, after the `appearance?` field added in Task 4:

```tsx
  /** Named Fate aspects (high_concept / trouble / character) — Deliverable B1.
   *  Absent/empty for non-Fate characters ⇒ the Aspects section is NOT rendered. */
  fate_aspects?: FateAspectEntry[];
```

- [ ] **Step 4: Render the Aspects block**

In `src/components/CharacterSheet.tsx`, immediately after the existing Backstory block (the `</div>` closing the `<h3>Backstory</h3>` div, ~287). `toDisplayName` already exists in this file (~113) and renders `"high_concept"` → `"High Concept"`:

```tsx
      {data.fate_aspects && data.fate_aspects.length > 0 && (
        <div data-testid="character-aspects">
          <h3 className="text-sm font-semibold mb-1">Aspects</h3>
          <ul className="space-y-1">
            {data.fate_aspects.map((aspect, i) => (
              <li key={`${aspect.kind}-${i}`} className="text-sm font-[var(--font-narrative)]">
                <span className="text-muted-foreground">{toDisplayName(aspect.kind)}: </span>
                {aspect.text}
              </li>
            ))}
          </ul>
        </div>
      )}
```

- [ ] **Step 5: Map the field from the facet**

In `src/lib/partyStatusMapping.ts`, add the import near the existing type imports:

```ts
import type { FateAspectEntry } from "../types/payloads";
```

After the `appearance` mapping added in Task 4:

```ts
    fate_aspects: Array.isArray(sheetFacet.fate_aspects)
      ? (sheetFacet.fate_aspects as FateAspectEntry[])
      : undefined,
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npx vitest run src/__tests__/character-sheet-aspects.test.tsx`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/components/CharacterSheet.tsx src/lib/partyStatusMapping.ts src/__tests__/character-sheet-aspects.test.tsx
git commit -m "feat(B1): render Fate aspects section on the character sheet"
```

---

### Task 6: (OPEN QUESTION 1 — vetoable) Appearance overrides the generic `core.description`

**Decision:** when the player typed an appearance, use it as `CreatureCore.description` (a strictly better narrator-facing description than the generic "A {race} {class}", and the natural seed for the future visual prompt). Gated on non-empty so nothing regresses. **If Keith vetoes OQ1, skip this task entirely** — Tasks 1–5 stand alone.

**Files:**
- Modify: `sidequest/game/builder.py` (`CreatureCore(description=...)` in `build()`, ~3284)
- Test: `tests/game/test_chargen_appearance_core_description.py` (new)

**Interfaces:**
- Consumes: `AccumulatedChoices.appearance` (Task 1).

- [ ] **Step 1: Write the failing test**

Create `tests/game/test_chargen_appearance_core_description.py`:

```python
"""OQ1: a typed appearance becomes the narrator-facing core.description."""
from sidequest.game.builder import StoryInput


def test_typed_appearance_becomes_core_description(make_story_builder):
    builder = make_story_builder()
    builder.apply_response(StoryInput(pronouns="they/them", background="An ex-ratcatcher.",
                                      description="Tall, soot-stained, missing a tooth."))
    char = builder.build()
    assert char.core.description == "Tall, soot-stained, missing a tooth."


def test_absent_appearance_falls_back_to_generic_description(make_story_builder):
    builder = make_story_builder()
    builder.apply_response(StoryInput(pronouns="they/them", background="An ex-ratcatcher.",
                                      description=""))
    char = builder.build()
    # Generic "A {race} {class}" shape — non-blank, not the appearance.
    assert char.core.description
    assert "soot-stained" not in char.core.description
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_chargen_appearance_core_description.py -v`
Expected: FAIL on `test_typed_appearance_becomes_core_description` — `core.description` is the generic "A {race} {class}".

- [ ] **Step 3: Use appearance for the core description when present**

In `sidequest/game/builder.py::build()`, replace the inline `description=(f"{indefinite_article(race_str).capitalize()} {race_str} {class_str}")` in the `CreatureCore(...)` call (~3284) with a pre-computed value. Just above the `character = Character(` line (~3281):

```python
        # OQ1 (Story 126-5): a player-typed appearance is a better narrator-
        # facing description than the generic "A {race} {class}". Gated on
        # non-empty so characters without an appearance input keep the generic.
        generic_description = f"{indefinite_article(race_str).capitalize()} {race_str} {class_str}"
        core_description = acc.appearance.strip() if (acc.appearance and acc.appearance.strip()) else generic_description
```

Then in the `CreatureCore(...)` call, change the `description=` line to:

```python
                description=core_description,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_chargen_appearance_core_description.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sidequest/game/builder.py tests/game/test_chargen_appearance_core_description.py
git commit -m "feat(126-5): use typed appearance as core.description when present (OQ1)"
```

---

### Task 7: Sharpen the chargen label (Description → Appearance)

**Files:**
- Modify: `src/components/CharacterCreation/StoryPanel.tsx` (the Description block ~119-137)
- Test: `src/components/CharacterCreation/__tests__/StoryPanel.test.tsx` (extend; update any assertion expecting the literal "Description")

**Interfaces:**
- The wire payload field stays `description` (OQ3: wire rename deferred). Only the visible label changes.

- [ ] **Step 1: Write the failing test**

Add to `src/components/CharacterCreation/__tests__/StoryPanel.test.tsx`:

```tsx
it("labels the appearance input 'Appearance', not 'Description'", () => {
  render(
    <StoryPanel
      pronounsOptions={["she/her", "he/him", "they/them"]}
      pronounsAllowFreeform
      backgroundOptional
      descriptionOptional
      autogenAvailable={false}
      onAutogen={() => {}}
      onConfirm={() => {}}
    />,
  );
  expect(screen.getByText("Appearance")).toBeInTheDocument();
  expect(screen.queryByText("Description")).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/components/CharacterCreation/__tests__/StoryPanel.test.tsx`
Expected: FAIL — the block still reads "Description".

- [ ] **Step 3: Relabel the block**

In `src/components/CharacterCreation/StoryPanel.tsx`, in the Description block (~119), change the label span and sharpen the placeholder. Keep `data-testid="story-description"` and the `description` state/prop names (wire unchanged):

```tsx
      {/* Appearance — "what you look like". Wire field stays `description`
          (OQ3 wire rename deferred); only the player-facing label changed. */}
      <div>
        <div className="text-xs uppercase tracking-widest text-muted-foreground/60 mb-1 flex items-baseline gap-2">
          <span>Appearance</span>
          {descriptionOptional && (
            <span className="normal-case tracking-normal text-[10px] text-muted-foreground/45 italic">
              optional
            </span>
          )}
        </div>
        <textarea
          data-testid="story-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          placeholder="Tall, soot-stained, missing a tooth."
          className="w-full rounded border border-input bg-background text-sm px-3 py-2 placeholder:italic placeholder:text-muted-foreground/50"
        />
      </div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/components/CharacterCreation/__tests__/StoryPanel.test.tsx`
Expected: PASS (fix any sibling assertion in the file that expected the old "Description" label).

- [ ] **Step 5: Commit**

```bash
git add src/components/CharacterCreation/StoryPanel.tsx src/components/CharacterCreation/__tests__/StoryPanel.test.tsx
git commit -m "feat(126-5): relabel chargen Description input to Appearance"
```

---

## Final verification

- [ ] **Server suite (affected areas):** from `sidequest-server/` run `uv run pytest tests/game/ tests/server/test_sheet_appearance_projection.py tests/server/test_sheet_fate_aspects_projection.py -v`. Expected: PASS. (Per memory, if a full parallel run deadlocks on OTEL span-count tests, run those files with `-n0`.)
- [ ] **Server lint/format (touched files only):** `uv run ruff check sidequest/game/builder.py sidequest/game/character.py sidequest/protocol/models.py sidequest/server/views.py` and `uv run ruff format <same files>`. (Do not run bare `ruff format .` — it reformats ~167 files.)
- [ ] **UI suite:** from `sidequest-ui/` run `npx vitest run src/__tests__/character-sheet-appearance.test.tsx src/__tests__/character-sheet-aspects.test.tsx src/components/CharacterCreation/__tests__/StoryPanel.test.tsx`. Expected: PASS.
- [ ] **UI lint:** `npm run lint` (or `npx eslint src/components/CharacterSheet.tsx src/lib/partyStatusMapping.ts src/components/CharacterCreation/StoryPanel.tsx`).
- [ ] **End-to-end manual check (optional):** run the stack (`just server`, `just client`), create a caverns_and_claudes character with distinct Background + Appearance text → the sheet shows Appearance and Backstory separately, neither contaminated; create a pulp_noir (Fate) character → the sheet shows an Aspects section with High Concept + Trouble.

---

## Self-review notes

- **Spec coverage:** Deliverable A → Tasks 1,2,4 (+OQ1 Task 6). Deliverable B1 → Tasks 3,5. Deliverable C (bug dissolution) → proven by Task 1's regression test. UI copy → Task 7. Deliverable B2 → **explicitly deferred** (stated in the spec-link block, with rationale). OTEL → Task 1 Step 7.
- **Ruleset doctrine:** no `if ruleset == 'fate'` anywhere — aspect surfacing gates on `fate_sheet is not None` (Task 3 Step 4); appearance is data-driven by the `identity_capture` scene.
- **Type consistency:** `Character.appearance: str` ↔ `CharacterSheetDetails.appearance: str` ↔ TS `appearance?: string`. `FateAspectEntry` (server protocol) ↔ `FateAspectEntry` (TS `payloads.ts`) — same `text/kind/free_invokes` shape; reused, not redefined.
- **Test-helper caveat:** Tasks 1/6 reference `make_story_builder` and Task 3 references `make_sheet_for` as the construction helpers. These names stand in for the nearest existing fixtures in `tests/game/` and `tests/server/`; the implementer must wire them to the real sibling-test construction (the assertions, not the helper names, are the contract). This is the one place to confirm against existing tests before writing.
