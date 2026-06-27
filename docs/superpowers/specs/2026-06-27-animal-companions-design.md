# Animal Companions — Design

**Status:** Approved (Architect design mode, 2026-06-27)
**Author:** Architect (Naomi Nagata, design mode)
**Epic:** 160 — Companion playtest follow-up: animal companions
**Builds on:** epic 159 (companion seat), `2026-06-26-companion-chargen-driver-decision.md`

---

## 1. Goal

Add animal companions — **cat, owl, raven, toad, goat** — as a player-facing
feature, plus world-specific portraits for them. This extends the epic-159
companion seat (Donut the cat) rather than inventing a parallel system.

Keith's decision (2026-06-27): the "feature" is **companion-seat persona
templates**, not a new in-game familiar entity. The §6 familiar-template
question from the chargen doc stays deferred — out of scope here.

## 2. Decisions (locked)

| Question | Decision |
|---|---|
| What is the "pet feature"? | **Companion-seat persona templates** (understudy `CompanionDef` YAMLs). Reuses the epic-159 run loop verbatim — zero new run-loop code. |
| Template world binding | **All five bound to `caverns_and_claudes/beneath_sunden`** (matches Donut, proven path, smallest file set). |
| Portrait worlds | **9 worlds**: wry_whimsy (`oz`, `wonderland`, `gulliver`); caverns_and_claudes (`beneath_sunden`); elemental_harmony (`burning_peace`, `shattered_accord`); heavy_metal (`evropi`, `long_foundry`, `barsoom`). |
| Tracker placement | **New epic 160**, owning all three stories. |
| Validation | **Explicit validation story** keeps the epic open while findings are fixed. |

## 3. Story 160-1 — Animal companion persona templates (understudy)

Five `CompanionDef` YAMLs under `sidequest-understudy/src/companion/examples/`,
one per species, all bound to `caverns_and_claudes/beneath_sunden`. Donut stays
as the canonical cat example; these add distinct-voiced siblings.

| Species | File | Voice register |
|---|---|---|
| cat | `cat_sunden.yaml` | Vain, self-important (Donut lineage) |
| owl | `owl_sunden.yaml` | Pedantic know-it-all, fussy about being correct |
| raven | `raven_sunden.yaml` | Ominous, cryptic, hoards shiny secrets, gallows humor |
| toad | `toad_sunden.yaml` | Phlegmatic, unbothered, blunt, food-motivated |
| goat | `goat_sunden.yaml` | Contrarian, stubborn, headbutts problems, eats everything |

Each: `role: pet`, `axes` tuned to the register, `model: claude_p/sonnet` (the
chargen-doc carryover — `anthropic/*` breaks on the dev box), `game_slug` left
as the `REPLACE-WITH-HUMANS-ROOM-SLUG` placeholder like Donut.

**Wiring test (mandatory — CLAUDE.md "Every Test Suite Needs a Wiring Test"):**
a test that loads every `examples/*_sunden.yaml`, asserts each parses as a valid
`CompanionDef` with `role: pet`, and that `species`/`voice` are populated. This
is the integration proof these are real, reachable defs and not orphan files.

**Blast radius:** `sidequest-understudy` only (branches/PRs to `develop`).

## 4. Story 160-2 — Animal companion portraits (9 worlds)

Add the five species as `companion_creature` entries to each world's
`portrait_manifest.yaml`, with world-specific `appearance` prose, then render
via the daemon Z-Image pipeline and upload to R2 + update `r2_manifest.json`.
Follows the existing Oz `toto` / `the_cowardly_lion` precedent.

- **9 worlds × 5 species = 45 portraits.**
- Each world pulls its drawing style from its own `visual_style.yaml`, so the
  same species renders world-specific (pen-and-ink in `beneath_sunden`,
  storybook in `oz`, brush-ink in `burning_peace`, chiaroscuro in `evropi`).
- `appearance` prose follows Z-Image rules: camera-style concrete prose, no
  proper nouns / dates / quoted phrases, positive-only (no negative prompts),
  cleanup clause ("No text, no caption, no title…"). Style suffix comes from
  `visual_style.yaml`, not the manifest.
- **Validation:** `cliche-judge` + `sidequest-validate` pass on the new entries.

**Relationship to 160-1:** these portraits give the companion seat a real
`selected_portrait_ref` to use later (today it skips with `null`). Useful, not
coupled — the stories ship in either order.

**Blast radius:** `sidequest-content` (manifests + assets); daemon render is an
operator-run pass over the existing pipeline, no daemon code change.

## 5. Story 160-3 — Animal companion dogfood validation (keeps epic open)

An explicit validation story that **stays open while we fix things found in
play**. Spawn each of the five species against a live `beneath_sunden` MP
session and verify the companion lifecycle end-to-end, filing findings as they
surface. Adapts §8 of the chargen doc to the new animals:

1. `companion play <species>_sunden.yaml` reaches `chargen.complete` with
   `char_count=1 seat_count=1` (server log).
2. Each species seats "at the table" under its authored name.
3. With the Inspector open before launch: `companion.bond_resolved(resolved=true)`
   fires at connect, and an owner-private `NARRATION_SEGMENT` reaches the pet
   (`companion.routed_as_pet`) once play begins.
4. Per-species voice lands distinctly in scene choices (the register is the
   point — a pet that's fun at the table).

Findings spin off as fixes; the epic stays open until all five dogfood clean.

## 6. Out of scope (deferred)

- **Player-owned in-game familiar entity** (the §6 familiar-template path) — a
  server `Familiar` type with minimal stats. Larger mechanics/content change;
  revisit if cat-as-PC framing bothers Keith in play.
- New run-loop code, server changes, UI changes.
