---
parent: context-epic-22.md
workflow: tdd
---

# Story 22-1: Seed trope schema + deck engine — lifespan, flavor tags, draw-without-replacement, ghost retention

## Business Context

This is the foundation story for Epic 22. Before the narrator can foreshadow with
seed tropes (22-3), before content authors can write seeds (22-2), and before the GM
panel can observe them (22-4), the engine needs three data shapes and one deck
mechanism. This story delivers exactly that — the schema and the draw engine — and
nothing player-facing yet.

The business value is *narrative variety with memory*: a per-session deck that deals
deliberately vague seeds, tracks which are live, and retains expired seeds as ghosts
for cross-session callbacks. Getting the persistence contract right here (round-trip
through the existing `snapshot_json` column, no migration) is what makes the rest of
the epic cheap to build on.

## Technical Guardrails

**Key files to modify or extend:**
- `sidequest/genre/models/tropes.py` — add `SeedTrope`, `SeedState`, `SeedGhost` as
  Pydantic siblings to `TropeDefinition` (line 42). Follow its conventions:
  `model_config = {"extra": "forbid", "populate_by_name": True}`.
- `sidequest/game/seed_deck.py` — new module for the `SeedDeck` class.
- `sidequest/game/session.py` — `GameSnapshot` (line 515) gains `active_seeds` and
  `seed_ghosts` fields.
- `sidequest/game/persistence.py` — existing `snapshot_json` column; verify round-trip,
  **no schema migration**.

**Patterns to follow:**
- `SeedTrope` is a **sibling type**, not a field extension of `TropeDefinition` — the
  lifecycle differs (short-arc + deck draw + ghost retention vs. long-arc escalation).
- Deck draw must be **reproducible**: `random.Random` seeded by `session_id`.
- Draw is **without replacement**: a drawn seed never returns to the deck, and this
  must survive save/reload (drawn-ids persist).

**What NOT to touch / out of scope:**
- No narrator injection (that's 22-3 — VALLEY zone).
- No seed *content* authoring (that's 22-2 — `tea_and_murder` deck).
- No OTEL spans (that's 22-4).
- No ghost *resolution* mechanics — `SeedGhost` is immutable, record-only.
- No DB schema migration — persistence rides the existing JSON column.

**Test-data discipline (project rule — `feedback_no_content_coupled_tests`):**
Use minimal **seed YAML fixtures** for unit tests. Do NOT load live `genre_packs/*`
and assert properties on real seed content. Live-pack seed content is a content-team
deliverable (22-2) surfaced by a validator, never asserted in a server unit test.

**Wiring requirement (server CLAUDE.md):** the suite needs at least one integration
test proving the new code is reachable from a production path — here, that the
persistence round-trip actually reconstructs deck/seed/ghost state from
`GameSnapshot` JSON, not just that the models serialize in isolation. Do NOT use
source-text grep wiring tests; use fixture-driven behavior tests.

## Scope Boundaries

**In scope:**
- `SeedTrope` Pydantic model (AC1): `id`, `name`, `description`, `flavor_tags`,
  `lifespan_turns`, `delivery_hints`, `narrative_hint`.
- `SeedDeck` class (AC2): constructor takes `genre_id`/`world_id`, loads seeds via
  genre loader, `draw() -> SeedTrope | None`, without-replacement, returns `None` on
  exhaustion, deck state keyed per (genre, world, session_id).
- `SeedGhost` model (AC3): `id`, `name`, `expired_at_turn`, `delivery_hints`; immutable.
- `SeedState` model + `GameSnapshot.active_seeds` (AC4): `id`, `name`,
  `activated_at_turn`, `flavor_tags`, `lifespan_turns`, `delivery_hints`; round-trippable.
- `GameSnapshot.seed_ghosts: list[SeedGhost]` field.
- Persistence round-trip via `snapshot_json` (AC5): drawn seeds don't return after reload.

**Out of scope:**
- Narrator/VALLEY injection (22-3).
- Seed content for any pack (22-2).
- OTEL spans (22-4).
- Engagement-triggered mid-session drops (22-5).
- Ghost resolution mechanics (immutable here).
- Lifespan-elapse migration *trigger* logic at runtime — the *fields* and *shape* land
  here; whatever turn-tick drives the active→ghost transition is exercised via fixture,
  not wired into the live turn loop in this story.

## AC Context

**AC1 — SeedTrope schema.** Pass: a `SeedTrope` with all seven fields constructs and
round-trips via Pydantic (`model_dump()` → `model_validate()` equality). Edge cases:
empty `flavor_tags`/`delivery_hints` default to `[]`; `lifespan_turns` is an int;
`extra="forbid"` rejects unknown keys. Test: construct, dump, reload, assert equality;
assert unknown-field construction raises `ValidationError`.

**AC2 — Deck engine.** Pass: `SeedDeck(genre_id, world_id, session_id, seeds=...)`
loads N seeds; `draw()` returns a `SeedTrope` and removes it; calling `draw()` N+1 times
yields N seeds then `None`. Without-replacement: collect all draws, assert no `id`
repeats and the set equals the input set. Reproducibility: two decks with the same
`session_id` and seed list produce the **same draw order**; different `session_id`
produces a (very likely) different order. Edge cases: empty deck → first `draw()` is
`None`; single-seed deck → one seed then `None`.

**AC3 — Ghost retention.** Pass: a `SeedGhost` carries `id`, `name`, `expired_at_turn`,
`delivery_hints` and round-trips. Immutability: model is frozen / record-only — assert
mutation raises (or that there is no resolution method). A `SeedState` whose
`activated_at_turn + lifespan_turns <= current_turn` maps to a `SeedGhost` preserving
`id`/`name`/`delivery_hints` and recording `expired_at_turn`. Test the expiry mapping
via fixture, not a live turn loop.

**AC4 — Active seed tracking.** Pass: `SeedState` has the six listed fields and is
round-trippable JSON with no side effects on load. `GameSnapshot.active_seeds` is a
`list[SeedState]` defaulting to `[]`. Test: a snapshot with several active seeds dumps
and reloads to an equal snapshot; loading does not mutate or fire anything.

**AC5 — Persist via ADR-023.** Pass: deck-drawn state, `active_seeds`, and `seed_ghosts`
all serialize into `game_state.snapshot_json` and reconstruct on load with **no schema
migration**. The load-bearing assertion (and the wiring test): persist a snapshot after
drawing some seeds, reload, re-instantiate the deck, and confirm **already-drawn seeds
do not return to the deck**. This is the integration test that proves the feature is
wired through real persistence, not just model-level serialization.

## Assumptions

- The genre loader can surface a per-pack seed list to `SeedDeck` (or accept an
  injected seed list in tests) — seed *content* arrives in 22-2, so 22-1 tests inject
  fixtures.
- `GameSnapshot` is the single persisted state object and `snapshot_json` already
  round-trips arbitrary Pydantic fields (ADR-023) — adding two `list` fields needs no
  migration.
- `session_id` is available at `SeedDeck` construction time for reproducible shuffling.
- Drawn-id tracking lives in the persisted deck/snapshot state (not in-memory only), so
  without-replacement survives reload — if this proves false, log a Design Deviation.
