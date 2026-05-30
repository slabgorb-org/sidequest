# Genre-Pack Content Audit — "Mechanics Only" Separation

**Date:** 2026-05-29
**Author:** GM agent (content audit)
**Goal (Keith):** Strip narrative/world *content* out of the genre tier, leaving genre
packs as **mechanics only**. Premise: "you put it in the genre and the world overrides
it — it's meaningless, because worlds vary too much to share genre-tier content."

**Audited against:** fresh `origin/develop` (`sidequest-content` @ `f8cf6e3`), via a
detached worktree at `/Users/slabgorb/Projects/oq-content-audit` (local `develop` was 5
commits behind). Loader semantics traced in `sidequest-server/sidequest/genre/loader.py`
and consumers across the server.

---

## TL;DR

The premise is **half right, and the audit found more than expected**:

1. **2,518 lines of genre-tier files are flat-out DEAD** — no code path reads the
   pack-root copy at all. These are pure cruft and can be deleted now with **zero**
   behavior change, independent of any philosophy decision.
2. **`cultures.yaml` and (mostly) `archetypes.yaml` are dead-in-practice** — they are
   *fallbacks*, and **every live world authors its own**, so the genre fallback is never
   taken in-session. One exception: `space_opera/perseus_cloud` has no archetypes.
3. **`lore.yaml` is the opposite of "overridden" — it's MERGED.** Genre lore and world
   lore are *both* seeded into the narrator's `LoreStore`; both reach the narrator. So
   genre lore is a **shared base layer added to every world**, not a shadowed default.
   This is the real "genre = mechanics only" decision, and it's a content-quality call,
   not a dead-code cleanup.
4. **`tropes.yaml` is genre-tier but LIVE** — the trope engine reads `genre_pack.tropes`
   directly. It's prose-heavy but it's a **mechanic**. Keep.
5. **`theme` / `visual_style` / `audio` / `weather`** are genre-tier presentation/identity
   — live, but arguably "content." Your call.

---

## How the loader actually combines genre + world (the deciding mechanism)

| File | Genre-tier role | World-tier role | Combine semantics | Consumer evidence |
|---|---|---|---|---|
| `lore.yaml` | `pack.lore` (`Lore`) | `world.lore` (`WorldLore`, **mandatory**) | **MERGED** — both seeded into one `LoreStore` | `game/lore_seeding.py:220-230`, `query_lore` tool |
| `cultures.yaml` | `pack.cultures` | `world.cultures` | **FALLBACK** — world wins if non-empty | `cli/namegen/namegen.py:267-273`, `server/dispatch/culture_context.py:53-66` |
| `archetypes.yaml` | `pack.archetypes` | `world.archetypes`/`archetype_funnels` | **FALLBACK** — world wins if present | `genre/archetype/shim.py:117-158` |
| `tropes.yaml` | `pack.tropes` (engine data) | `world.tropes` resolve `extends:` against genre pool | **GENRE-READ** by engine | `server/session_helpers.py:1103`, `game/trope_tick.py:91`, `agents/tool_registry.py:115` |
| `magic.yaml` | genre layer | world layer | **COMPOSED** — requires both | `genre/loader.py:919-926`, `genre/magic_loader.py` |
| `weather.yaml` | **PACK tier, read** | — | genre-tier only | `game/world_grounding_loader.py:47-55` (docstring L19-23) |
| `calendar.yaml` | — | **WORLD tier only** | genre-tier copy never read | `game/world_grounding_loader.py:78-84` |
| `history.yaml` | — | **WORLD tier only** (`world_path`) | genre-tier copy never read | `genre/loader.py:841` |
| `cartography.yaml` | — | **WORLD tier only** (`world_path`) | genre-tier copy never read | `genre/loader.py:787` |
| `openings.yaml` | **explicitly dead** | world tier mandatory | genre-tier deleted in code | `genre/loader.py:1121-1126` |
| `places.yaml` | — | — | **never referenced anywhere** | grep refs = 0 |
| `spellbook.yaml` | — | — | **never referenced anywhere** | grep refs = 0 |

---

## Bucket A — DEAD: delete now, zero behavior change (2,518 lines)

No code path reads the genre-tier (pack-root) copy of any of these. Confirmed by full
server grep + loader trace.

| Pack | File | Lines | Why dead |
|---|---|--:|---|
| caverns_and_claudes | `places.yaml` | 93 | never referenced |
| caverns_and_claudes | `spellbook.yaml` | 360 | never referenced |
| caverns_and_claudes | `cartography.yaml` | 77 | cartography read at world tier only |
| mutant_wasteland | `places.yaml` | 98 | never referenced |
| heavy_metal | `openings.yaml` | 32 | genre-tier openings explicitly dead |
| neon_dystopia | `openings.yaml` | 61 | genre-tier openings explicitly dead |
| pulp_noir | `openings.yaml` | 62 | genre-tier openings explicitly dead |
| road_warrior | `openings.yaml` | 99 | genre-tier openings explicitly dead |
| spaghetti_western | `openings.yaml` | 61 | genre-tier openings explicitly dead |
| spaghetti_western | `history.yaml` | 82 | history read at world tier only |
| spaghetti_western | `calendar.yaml` | **1368** | calendar read at world tier only |
| tea_and_murder | `history.yaml` | 43 | history read at world tier only |
| tea_and_murder | `cartography.yaml` | 82 | cartography read at world tier only |

> **Recommendation:** delete all of Bucket A regardless of the philosophy decision.
> Aligns with the project's "dead code is worse than no code" rule.

### Design-doc markdown (separate question)
`combat_design.md` / `magic_design.md` in `road_warrior`, `neon_dystopia`, `pulp_noir`,
`space_opera`. The engine never loads `.md`. These are **author reference** (Keith/Jade
design rationale), not runtime content. Recommend **keep or relocate to a docs area**,
not delete.

---

## Bucket B — DEAD-IN-PRACTICE: shadowed by every live world (fallbacks)

These load at genre tier but are *fallbacks* the world copy overrides. **Every live world
authors its own cultures, and all but one its own archetypes** — so the fallback is never
taken in a real session.

- **`cultures.yaml`** (genre) — 1,255 lines across packs. Fallback never taken in-session
  (all 16 live worlds author cultures). *Caveat:* the standalone `namegen` CLI can run
  without a world and would then use genre cultures — but that's a dev tool, not a session.
- **`archetypes.yaml`** (genre) — 2,633 lines. Fallback never taken **except
  `space_opera/perseus_cloud`**, which authors cultures but no archetypes/funnels and thus
  falls back to `space_opera/archetypes.yaml`.

> **Recommendation:** safe to expunge from genre tier *if* (a) we accept the namegen CLI
> loses its world-less default, and (b) we first author `perseus_cloud` archetypes (or
> keep `space_opera/archetypes.yaml` as that one world's fallback).

---

## Bucket C — LIVE shared content: the real "mechanics only" decision

- **`lore.yaml`** (genre) — 509 lines. **MERGED into the narrator**, not overridden.
  Genre lore is shared context added to *every* world in the pack. Deleting it removes
  that shared base from every world's narrator RAG. Keith's "worlds vary too much"
  argument is a *content-quality* case for moving lore down to worlds — not a dead-code
  case. **This is a genuine decision, not a cleanup.**

---

## Bucket D — Presentation / genre identity (live; your call)

Loaded at genre tier, world *can* override (`visual_style`, `client_theme.css` per
ADR-079). Genre-defining aesthetic, arguably not "content":

- `theme.yaml` (223), `visual_style.yaml` (852), `audio.yaml` (2,640), `weather.yaml` (205, live at pack tier).

> **Recommendation:** keep `theme`/`visual_style`/`audio` as genre identity unless you
> consider per-world divergence severe enough to push them down. `weather` is climate —
> borderline content; could move to worlds.

---

## Bucket E — MECHANICS: keep at genre tier (unambiguous)

`pack.yaml`, `rules.yaml`, `progression.yaml`, `axes.yaml`, `power_tiers.yaml`,
`lethality_policy.yaml` (required), `visibility_baseline.yaml` (required),
`classes.yaml`, `chassis_classes.yaml`, `inventory.yaml`, `char_creation.yaml`,
`archetype_constraints.yaml`, `projection.yaml`, `pacing.yaml`, `achievements.yaml`,
`backstory_tables.yaml`, `equipment_tables.yaml`, `seed_tropes.yaml`, `magic.yaml`
(composed), `spells_wwn.yaml` / `spells/`, `powers.yaml`, `prompts.yaml`,
`beat_vocabulary.yaml`, **`tropes.yaml`** (engine-read).

---

## Decisions (Keith, 2026-05-29)

- **A — delete all dead now.** ✅ DONE — commit `80a7e8f` on branch
  `chore/genre-expunge-dead-flavor` (13 files + stale `extensions:` cleanup; validated).
- **B — expunge cultures + archetypes** (author `perseus_cloud` archetypes first).
- **C — move genre lore *down into each world*,** then delete genre lore.
- **D — NO FLAVOR AT GENRE, PERIOD.** Keith: *"I do not want any flavor! That's flavor!
  Even if it shares weather, holidays, calendar, whatever — flavor is in the world, not
  the genre."* → push `theme` / `visual_style` / `audio` / `weather` down to worlds too.

**Governing principle going forward:** the genre tier is **mechanics only**. Anything
whose *purpose* is flavor (lore, cultures, archetypes, theme, visual style, audio,
weather, holidays, calendar) lives in the world. The genre defines *how the game plays*;
the world defines *what it feels like*.

---

## ⚠️ Part 2 is gated on SERVER work — it is NOT a pure content move

Every remaining flavor file is a **mandatory genre-tier load** in the loader
(`_load_yaml(path / "X.yaml", ...)` raises `GenreLoadError` if absent). You cannot just
delete them — the pack stops loading. Making the genre tier mechanics-only requires a
**loader + consumer refactor first** (Python — a Dev story; the GM agent files it, does
not write it), then a per-world content migration, then deletion of the genre copies.

### Server changes required (per file)

| File | Loader today | Required change | Consumer change |
|---|---|---|---|
| `lore.yaml` | mandatory genre + mandatory world (merged) | make genre lore optional → drop | `lore_seeding.py` already merges; just stop seeding genre tier |
| `cultures.yaml` | mandatory genre | make genre optional / world-only | namegen + `culture_context.py` already prefer world; drop genre fallback |
| `archetypes.yaml` | mandatory genre | make genre optional / world-only | `archetype/shim.py` already falls back to world; author `perseus_cloud` first |
| `theme.yaml` | **mandatory genre** (`extra="forbid"`, required fields) | move to world tier (or genre-optional + world-required) | reference-chrome + connect-time theme load must read world |
| `visual_style.yaml` | **mandatory genre** | move to world tier | portrait/POI render pipeline reads genre `visual_style` — must read world |
| `audio.yaml` | **mandatory genre** | move to world tier | `_resolve_audio_urls` + audio engine read genre — must read world |
| `weather.yaml` | optional, **pack-tier read** | switch `load_pack_weather` → world tier | `world_grounding_loader.py:47` |

### Boundary cases needing a ruling (mechanically load-bearing, flavor-skinned)

These three are read at the genre tier and drive **mechanics**, but their *content* is
pure narrative flavor. They can't simply move without an engine change AND a big
authoring lift (most worlds author none today):

- **`tropes.yaml`** — the trope engine reads `genre_pack.tropes` directly
  (`session_helpers.py:1103`, `trope_tick.py:91`). 8/10 packs have **zero** world tropes,
  so moving tropes to worlds means authoring a trope deck for **every world** + changing
  the engine to read world tropes. Tropes are escalation/tension *mechanics* wearing
  flavor text.
- **`prompts.yaml`** — narrator prompt scaffolding; structurally mechanical but carries
  genre *voice* (flavor).
- **`beat_vocabulary.yaml`** — narration beat vocabulary; flavor-laden but mechanical.

> **Recommendation:** keep the *mechanical skeleton* of tropes/prompts/beat_vocabulary at
> genre (escalation arrays, beat structure, prompt zones) and treat their prose as the
> thing to genericize or push down — rather than deleting the subsystems. **Needs Keith's
> ruling.**

### Design-doc `.md` (combat_design / magic_design)
Author reference, never loaded. Relocate to a docs area or leave; not runtime flavor.

---

## Suggested sequencing

1. ✅ **Part 1 — dead files** (done; PR pending Keith's go).
2. **File a Dev/server story:** "Genre tier = mechanics only — loader + consumer refactor"
   making lore/cultures/archetypes/theme/visual_style/audio/weather world-tier (or
   genre-optional, world-authoritative). Includes OTEL spans proving world-tier loads fire.
3. **Author `perseus_cloud` archetypes** (unblocks B).
4. **Per-world content migration** (GM authoring): move each flavor surface into every
   world that lacks it, world by world, validating after each.
5. **Delete genre flavor copies** once every live world is self-sufficient.
6. **Boundary ruling** on tropes/prompts/beat_vocabulary before touching them.
