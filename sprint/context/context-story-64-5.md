---
parent: context-epic-64.md
workflow: tdd
---

# Story 64-5: Cross-reference content lint — ID membership + adjacency closure

## Business Context

Per-file schema validation (64-4) proves each file is internally well-formed,
but it cannot see *across* files. A `tropes.yaml` chapter can reference a trope
id that does not exist; an archetype can declare a `typical_class` that
`rules.yaml` does not allow; an `archetype_constraints.yaml` can name a jungian
or role id outside the canonical set, which then silently never matches in
`pairing_weight()`. Each of these passes 64-4 and fails — quietly — at runtime.
During epic 64 review these checks were run by hand (the jungian×role audit,
the class/race membership pass). This story bakes them into the validator so
the dangling reference is an ERROR at `content-validate` time.

## Technical Guardrails

Add a cross-reference lint layer on top of 64-4's parsed models. The checks:

| Check | Source of truth | Where to look |
|-------|-----------------|---------------|
| Trope ids referenced in `history.yaml` chapters / adjacency exist | resolved trope set (genre + world, post `resolve_trope_inheritance`) | `genre.resolve.resolve_trope_inheritance`, loader l.779-785 |
| Archetype `typical_classes` ∈ allowed | `rules.yaml` `allowed_classes` | per-pack `rules.yaml` |
| Archetype `typical_races` ∈ allowed | `rules.yaml` `allowed_races` | per-pack `rules.yaml` |
| `archetype_constraints` pairing ids canonical | 12 jungian × 7 rpg roles | the canonical sets used in `ArchetypeConstraints`; `genre_flavor` must cover all, no extras |
| Theme adjacency closure | palette ids | `dungeon.themes.load_theme_palette` already raises on this — surface as a validator ERROR rather than an uncaught exception |

- Reuse resolution helpers (`resolve_trope_inheritance`) — do not reimplement
  inheritance merge logic.
- The canonical jungian/role sets must come from one authoritative location
  (whatever `ArchetypeConstraints` / the archetype axes module already defines),
  not a copied literal in the validator.
- Each finding is an ERROR naming the offending id **and** the file it appears
  in, so an author can jump straight to it.
- Do not regress 64-4's parse pass or the structural checks; this is an
  additional layer that runs after contents parse.

## Scope Boundaries

**In scope:**
- Cross-file id-membership checks for tropes, archetype classes/races,
  archetype_constraints jungian/role ids + flavor coverage.
- Theme adjacency-closure surfaced as a validator ERROR.
- All 10 live packs still PASS.

**Out of scope:**
- The per-file `model_validate` pass itself — that is 64-4 (this story assumes
  it exists and consumes its parsed models).
- Deep semantic validation beyond id membership / coverage / closure (e.g.
  balance of pairing tiers, narrative quality) — not a validator concern.
- Any change to `rules.yaml`, the genre models, or `pack_schema.yaml`.

## AC Context

1. **Unresolvable trope id in history/adjacency → ERROR with the id + file.**
   Test: fixture pack whose `history.yaml` chapter references `not_a_trope` →
   FAIL naming `not_a_trope` and the file. Edge case: a world trope that
   legitimately extends a genre trope must resolve and NOT error.
2. **Archetype `typical_classes`/`typical_races` not in `rules.yaml` allowed
   sets → ERROR.** Test: fixture archetype with `typical_classes: [NotAClass]`
   → FAIL naming the class and file. Edge: empty `typical_classes` is allowed
   (some archetypes intentionally leave it open) and must not error.
3. **`archetype_constraints` non-canonical jungian/role id, or missing/extra
   `genre_flavor` entry → ERROR.** Test: fixture with a pairing `[heroo, tank]`
   (typo) → FAIL; fixture missing the `jester` flavor entry → FAIL; extra
   non-canonical flavor key → FAIL. These mirror the by-hand audit from epic 64
   review.
4. **Theme adjacency closure surfaced as a validator ERROR.** Test: fixture
   theme whose `adjacency.prefers` names a non-existent theme → the
   `load_theme_palette` failure is caught and reported as a validator ERROR
   (not an uncaught traceback).
5. **All 10 live packs still PASS.** Real-content smoke check: the live packs
   are internally consistent today (verified in review), so the lint must not
   false-positive on them.

## Assumptions

- 64-4 has landed: file contents already parse into models before this layer
  runs. If 64-4 is not merged, this story is blocked.
- `rules.yaml` carries `allowed_classes` / `allowed_races` in every live pack
  (true today). If a pack lacks them, that absence is itself worth an ERROR.
- The canonical jungian (12) and rpg-role (7) sets are defined once in the
  codebase and importable; the validator references that, not a literal.
- Validator test fixtures live under `tests/cli/validate/` and never point at
  live content.
