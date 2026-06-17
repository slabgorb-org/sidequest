# Chargen Appearance Field + Ruleset-Shaped Backstory Legibility

- **Date:** 2026-06-17
- **Status:** Draft — pending user review
- **Author:** Hephaestus the Smith (Dev), at Keith's direction
- **Supersedes the framing of:** story 126-5 ("[UX-LOW] Chargen 'Backstory' is fed by the 'Description' input, not 'Background'"). The story is filed `repos: ui`, trivial; the investigation below proves the logic is server-side and the real work is a small feature, not a UI line-swap. This spec re-scopes it.
- **Repos:** `sidequest-server` (model + builder + sheet projection + OTEL), `sidequest-ui` (sheet rendering + chargen labels), `sidequest-content` (label intent only; optional additive appearance capture per pack)
- **Builds on / composes with:**
  - `2026-06-14-ruleset-chargen-seam-design.md` (chargen mechanics owned by `RulesetModule`; the builder is the FSM, the module owns contributions)
  - `2026-06-16-fate-interactive-chargen-design.md` (Fate `FateSheet` aspects/skills/stunts; the **data-driven** ruleset fork — "which scenes a pack authors," never `if ruleset == 'fate'`)
- **Doctrine touchstones:** SOUL "Crunch in the Genre, Flavor in the World"; "Diamonds and Coal" (flavor legible on the sheet); the Sebastien/Jade legibility axis (mechanical/identity surfaces must be visible in the **player UI**); "No Stubbing" / "Verify Wiring" (a new field needs a real consumer now).

---

## Summary (the decision)

Two player-authored chargen inputs are mis-homed today:

1. **"What you look like" (appearance)** is mashed into `Character.background` and then effectively lost — it reaches no player-facing surface and no narrator/visual surface. **Decision (Keith):** give it its own first-class `appearance` field, **surface it on the character sheet now**, and reserve it as the seed for a future custom visual-prompt feature (TBD — not built here).

2. **Backstory** is composed differently per ruleset, and the **Fate** path — where backstory *is* mechanics (aspects = invoke/compel) — is the one that matters most (the eval that spawned 126-5 was Fate/`annees_folles`). **Decision (Keith):** make backstory **ruleset-shaped and Fate-first**, by *surfacing* the load-bearing Fate identity (aspects) on the player sheet, and by making a player's explicitly-typed WWN background **win over the table-roll** (authorship over dice).

The original "Backstory shows the Description" bug **dissolves as a side effect**: once "what you look like" routes to `appearance`, it can no longer pollute `background`/`backstory`.

**Hard rule inherited from the two parent specs:** the ruleset fork is **data-driven** (which scenes a pack authors) and via the `RulesetModule` / `fate_sheet`-presence seam — **never an `if ruleset == 'fate'` branch** in the builder loop or the UI renderer.

---

## Why — the investigation (proven in code)

The chargen `the_story` scene (only authored today by **caverns_and_claudes**, a WWN pack — `genre_packs/caverns_and_claudes/char_creation.yaml`) collects three things; its narration says so verbatim: *"how to refer to you, what you did before, and what you look like."*

| Input | Intent | Where it lands today | Verdict |
|---|---|---|---|
| pronouns | identity | `MechanicalEffects.pronoun_hint` → `Character.pronouns` | correct |
| **Background** ("what you did before") | the character's history = backstory | joined into `MechanicalEffects.background` (`builder.py::_apply_story`, ~2569) → `acc.background` → only the **fallback** branch of the backstory cascade | **mis-homed** |
| **Description** ("what you look like") | physical appearance | **joined into the same `background`** alongside Background | **mis-homed** (pollutes backstory/background; reaches no surface) |

Three structural facts confirm the re-scope:

- **`_apply_story` joins both** into one field: `MechanicalEffects.background = "background | description"` (`builder.py:2569-2577`). There is no appearance home.
- **`Character` already has two distinct fields** — `backstory` (`character.py:99`, the sheet field) and `background` (`character.py:148`, used only for openings/preview). The typed text lands in the **second**, not the first.
- **`CreatureCore.description`** (`creature_core.py:114`) — the narrator-facing description — is auto-composed generic ("A {race} {class}", `builder.py:3284`). The player's typed appearance never reaches it.
- **The sheet backstory** (`Character.backstory`) is composed by a cascade (`builder.py:2938-2961`): `backstory_fragments` → `backstory_tables` → fallback(`acc.background`). For c&c, **tables exist** (`background_autogen_source: backstory_tables`), so a player's typed Background is **out-prioritized by a dice roll** — authorship loses.

For **Fate** (`pulp_noir`/`annees_folles`): there is **no `the_story` scene at all**. The narrative identity is the phase-trio (`crucible`/`connection`/`drive` choice prose → `backstory_fragments` → `Character.backstory`, which composes correctly) **plus the authored aspects** (HC/Trouble/free) on `CreatureCore.fate_sheet`. Aspects are wired to the **narrator** (`orchestrator.py` invokable-aspect directive; `intent_router` `invoke_aspect`; the compel tool) — but **not to the player sheet**. `CharacterSheetDetails` (`protocol/models.py:462`) has `backstory`, `skills`, `foci`, `class_moves` — **no aspects field**. That is the Fate legibility gap.

---

## Deliverable A — `appearance` as a first-class field, surfaced on the sheet

### A1. Model (`sidequest-server`)
- Add `appearance: str = ""` to `Character` (`game/character.py`), adjacent to `background`/`drive` (`:148`). Default `""` so existing saves validate (no non-blank validator — appearance is optional).
- Add `appearance: str = ""` to `AccumulatedChoices` (`builder.py:446`).

### A2. Capture (`builder.py::_apply_story`, ~2539)
- **Stop joining** description into `background`. Route `response.description.strip()` to the new accumulator: `acc.appearance` (carried on the `SceneResult`/effects the same way `background` is, so `go_back`/revert parity holds — see Risks).
- `MechanicalEffects.background` now carries **only** the typed Background ("what you did before").
- `build()` (`builder.py:3281`) sets `Character(appearance=acc.appearance, ...)`.

### A3. Surface on the player sheet (the real consumer — not a stub)
- `CharacterSheetDetails` (`protocol/models.py:462`): add `appearance: str = ""` (additive, defaulted — mirrors the `skills`/`foci` precedent).
- `server/views.py` (sheet projection, ~`:400`): populate `appearance=character.appearance`.
- `sidequest-ui`: `CharacterSheetData` (`CharacterSheet.tsx:70` region) gains `appearance?: string`; `partyStatusMapping.ts` (~`:75`) maps it; `CharacterSheet.tsx` renders an **"Appearance"** block (sibling to Backstory, ~`:285`), **omitted when empty** (same pattern as Skills/Foci — empty ⇒ no section).

### A4. Future visual-prompt hook (design-noted, NOT built)
The portrait pipeline (`sidequest-daemon` `subject_extractor.py` / `prompt_composer.py`) extracts visual subjects from narrative text via LLM; it has no structured per-character appearance input. `Character.appearance` is the seed a future custom-prompt feature consumes. **Out of scope here** — this spec only establishes/surfaces the field. See Open Question 1 (whether `appearance`, when present, should also populate the generic `CreatureCore.description`).

---

## Deliverable B — Backstory legibility, ruleset-shaped (Fate-first)

The fork is **data-driven**, consistent with the Fate-chargen spec. No ruleset conditionals.

### B1. Fate: surface aspects on the player sheet (the priority)
The Fate identity is the aspects, and they are invisible to the player today.
- `CharacterSheetDetails`: add `fate_aspects: list[FateAspectEntry] = Field(default_factory=list)` (reuse the existing `FateAspectEntry`; do **not** invent a new type).
- `server/views.py`: populate from `character.core.fate_sheet.aspects` **when `fate_sheet is not None`** — the same presence gate the Fate spec uses (`fate_sheet is None` for non-Fate), **not** a `ruleset == 'fate'` check. Empty/absent for non-Fate characters.
- `sidequest-ui`: `CharacterSheet.tsx` renders an **"Aspects"** block (High Concept / Trouble / free aspects, kind-labelled) when non-empty. This is the Sebastien/Jade legibility fix for Fate.
- The phase-trio backstory (`crucible`/`connection`/`drive` → `Character.backstory`) already composes correctly and already shows on the sheet — **no change**, only verify it renders for a real `pulp_noir` build (wiring test).

### B2. WWN: player authorship beats the dice
Adjust the backstory cascade (`builder.py:2938-2961`) so a **player's explicitly-typed `the_story` Background** is authoritative over the table-roll — matching the scene's own fiction ("…or you can let her make something up"). Recommended order:

1. explicit typed `the_story` background (when the player typed one) — **new, wins**
2. `backstory_fragments` (choice-description prose; the Fate phase-trio path) — unchanged
3. `backstory_tables` roll — now the "make something up" fallback when the player left Background blank
4. hardcoded "A wanderer with a mysterious past" — unchanged last resort

The exact compose-vs-replace rule between (1) and (2) is **Open Question 2** (recommendation: explicit typed background is authoritative; if both present, prepend typed background then fragments). The OTEL `chargen.backstory_composed` event (`builder.py:2962`) gains `method: "typed"` as a branch so the GM panel sees which path fired.

---

## Deliverable C — the 126-5 bug dissolves
With A2 in place, "what you look like" routes to `appearance` and can no longer appear in `background`/`backstory`. With B2, a typed Background reaches the sheet Backstory. The original symptom ("Backstory shows the Description") is structurally impossible afterward. The 126-5 acceptance test ("a small test pinning the mapping") becomes: *a `the_story` submission with distinct Background and Description text yields `backstory == Background` and `appearance == Description`, with neither cross-contaminating.*

---

## UI copy (chargen labels — `StoryPanel.tsx`)
Keep the two textareas; sharpen the labels to the scene's own fiction so intent is unambiguous:
- **Background** → keep, sublabel "what you did before."
- **Description** → relabel to **"Appearance"**, sublabel "what you look like." (testid stays `story-description` to avoid churn, or rename to `story-appearance` — implementer's call; if renamed, update the StoryPanel test.)
This is cosmetic-but-clarifying; the wire payload field name (`description`) is unchanged (Open Question 3 covers an optional rename).

---

## Invariants / Contracts
- **No ruleset branch.** Appearance capture is gated by a pack authoring an `identity_capture` description field; aspect surfacing is gated by `fate_sheet is not None`. No `if ruleset == …` in builder loop or UI renderer.
- **Appearance has a live consumer.** It renders on the sheet now (A3); it is not a dark field awaiting the visual-prompt feature.
- **Additive, save-safe.** Every new model/protocol field defaults empty; legacy saves and non-Fate / non-`the_story` characters validate and render unchanged (empty ⇒ section omitted).
- **Server is the authority.** The sheet projection (`views.py`) is the single source for `appearance`/`fate_aspects`; the UI mirrors.
- **OTEL.** `chargen.backstory_composed` gains the `typed` method branch; an `chargen.appearance_captured` event (`{present, length}`) fires from `_apply_story` so the GM panel can confirm capture (CLAUDE.md OTEL principle — this touches a chargen subsystem).

---

## Test strategy
- **126-5 mapping test (the pinned regression):** synthetic `the_story` `StoryInput` with Background="X" + Description="Y" → assert `Character.backstory` contains "X" and not "Y", `Character.appearance == "Y"`, `Character.background` carries no "Y". Synthetic fixtures only (no pack load — "no content in unit tests").
- **Authorship-wins (B2):** a build with a typed background **and** `backstory_tables` configured → backstory == typed text, not a table roll; OTEL method == `"typed"`. Mutation: blank typed background → falls through to tables.
- **Fate aspects on sheet (B1) — wiring test, not source-grep:** a real `pulp_noir` Guided build through the production builder → `CharacterSheetDetails.fate_aspects` non-empty with HC+Trouble; a WWN build → `fate_aspects == []` and `appearance` renders. Paired negative keeps the surfaces honest.
- **Appearance sheet wiring:** drive the sheet projection (`views.py`) for a c&c build with a typed appearance → `CharacterSheetDetails.appearance` populated; UI test asserts the Appearance block renders and is omitted when empty.
- **OTEL:** `chargen.appearance_captured` + `chargen.backstory_composed{method:"typed"}` fire via `InMemorySpanExporter` (mirroring existing chargen-span tests).

---

## Out of scope (explicit)
- **The custom visual-prompt feature** itself (daemon prompt composition from `appearance`) — TBD, Keith's call, future story.
- **Appearance capture for Fate / other packs** — the field + sheet surfacing are general; *capturing* appearance in Fate chargen would be additive scene authoring (data-driven, no engine change) and is not built here. WWN `the_story` is the only capture site today.
- **The `RulesetModule` chargen-contribution seam** (`2026-06-14-ruleset-chargen-seam-design.md`) — this spec composes with it but does not move backstory composition onto the module; it adjusts the existing cascade in place. (If that seam lands first, B2 is a natural method on it — flag for the plan.)
- **Fate chargen flow / FateSheet construction** (121-x) — unchanged; B1 only *projects* existing aspects to the sheet.

## Open questions
1. **Should `appearance`, when present, also populate `CreatureCore.description`** (replacing the generic "A {race} {class}")? Pro: the narrator and the future visual pipeline immediately benefit from real appearance text. Con: `core.description` is shared with NPC semantics. **Recommendation:** yes — when the player typed an appearance, it is a strictly better narrator-facing description than the generic default; gate on non-empty so nothing regresses. Flagged for Keith.
2. **Compose vs replace** between a typed WWN background and `backstory_fragments` (B2). **Recommendation:** typed background authoritative; if both present, typed-then-fragments.
3. **Rename the wire field `description` → `appearance`** through the StoryConfirm payload (`protocol/messages.py:511-515`) and `StoryPanel`? **Recommendation:** defer — relabel UI only now; a wire rename is a separate, churny change with no behavior gain.

## References
- Server: `game/character.py` (`backstory`:99, `background`:148), `game/creature_core.py` (`description`:114), `game/builder.py` (`_apply_story`:2539, `AccumulatedChoices`:446, backstory cascade:2938-2961, `Character(...)`:3281, `core.description`:3284), `protocol/models.py` (`CharacterSheetDetails`:462), `server/views.py` (sheet projection:400), `game/ruleset/fate_sheet.py` / `fate_projection.py` (aspects), `agents/orchestrator.py` (narrator aspect directive — the surface this complements).
- UI: `src/components/CharacterSheet.tsx` (:70 data shape, :285 backstory block), `src/components/CharacterCreation/StoryPanel.tsx`, `src/lib/partyStatusMapping.ts:75`.
- Content: `genre_packs/caverns_and_claudes/char_creation.yaml` (`the_story` `identity_capture` scene), `genre_packs/pulp_noir/char_creation.yaml` (phase-trio + `fate_*` scenes).
- Specs: `2026-06-14-ruleset-chargen-seam-design.md`, `2026-06-16-fate-interactive-chargen-design.md`. ADRs: 007 (unified character model), 015/016 (builder FSM / three-mode chargen), 117/142/143 (ruleset seam), 144 (Fate binding), 014 (Diamonds and Coal).
