# Advancement Effect Hosts — Per-Genre Audit (Story 39-5 / AC6)

**Status:** Decision artifact for ADR-078 / ADR-081 (Rust-era — see implementation-status note)
**Last updated:** 2026-06-17

> **Implementation status (2026-06-17 — ADR-082 port reconciliation).**
> This is a Rust-era decision artifact and the ADR framing has moved on.
> **ADR-078 is superseded by [ADR-114](adr/114-ablative-hp-substrate.md):**
> Edge/Composure was reversed for SWN-style ablative HP, so the
> `AdvancementEffect` vitality variants are re-pointed from Edge to HP
> (`EdgeMaxBonus` → `HpMaxBonus`, `EdgeRecovery` → `HpRecovery` — note the
> pydantic classes are `AdvancementEffectHpMaxBonus` / `...HpRecovery` while
> their wire `type` literals still read `edge_max_bonus` / `edge_recovery`).
> **ADR-081** (the two-variant expansion `AllyEdgeIntercept` /
> `ConditionalEffectGating`) **is accepted but deferred**
> ([ADR-087](adr/087-post-port-subsystem-restoration-plan.md)); neither
> variant exists in code yet.
>
> **Ported:** the data models — `AdvancementTree`, `AdvancementTier`, and the
> five-variant `AdvancementEffect` in
> `sidequest-server/sidequest/genre/models/advancement.py`, plus
> `AffinityTier.mechanical_effects` in
> `sidequest-server/sidequest/genre/models/progression.py`. `progression.yaml`
> is deserialized into `ProgressionConfig` by
> `sidequest-server/sidequest/genre/loader.py`.
>
> **Did NOT port (deferred, ADR-087):** the `load_advancement_tree` harvester
> + dual-host validation, and the consumption engine (`resolved_beat_for` /
> `grant_advancement_tier`). No pack ships an `advancements.yaml` sidecar; only
> `heavy_metal/progression.yaml` populates `mechanical_effects`, and nothing
> applies it at runtime yet. **Read the two-host decision below as the target
> design, not live behavior.**

## Decision

Each genre authors its `AdvancementTree`
(`sidequest-server/sidequest/genre/models/advancement.py`) in one of two
mutually-exclusive locations:

- **Progression host** — `mechanical_effects:` blocks on affinity tiers in
  `progression.yaml` (`AffinityTier.mechanical_effects` in
  `sidequest-server/sidequest/genre/models/progression.py`). The intended
  harvester `load_advancement_tree` (Rust-era; **not yet ported** — ADR-087)
  would fold these into a tree where each tier id is auto-derived from the
  affinity + tier slot (e.g. `iron_tier_1`).
- **Sidecar host** — a standalone `advancements.yaml` file at the genre root,
  deserialised directly as an `AdvancementTree`. (No pack ships one today; the
  sidecar reader is part of the deferred harvester.)

A genre may use **exactly one** of the two hosts. Carrying both files is a
validation error — the loader fails loudly with `GenreValidationError`
(`sidequest-server/sidequest/genre/error.py`, the Python port of Rust
`GenreError::ValidationError`) naming both paths. No silent fallback. (The
dual-host check rides the deferred `load_advancement_tree` harvester — ADR-087.)

A genre with neither host is valid (empty `AdvancementTree()` — pydantic
default of no tiers) and
indicates that the pack has not yet been wired for mechanical advancement —
these genres still author narrative abilities on affinity tiers, but those
abilities do not feed the Edge / Composure mechanical path until a tier carries
a `mechanical_effects:` block or the genre ships an `advancements.yaml`.

## Per-Genre Decisions

Heavy_metal is the lead implementation for 39-5; the remaining genres declare
their host decision here and land their mechanical content in follow-up
stories.

| Genre                 | Host                | Status (as of 39-5) | Rationale |
|-----------------------|---------------------|---------------------|-----------|
| heavy_metal           | progression.yaml    | **populated**       | Six-affinity structure (Iron/Pact/Craft/Lore/Court/Ruin) maps cleanly to `AffinityTier.mechanical_effects`. This story lifts ADR-081 draft §2 into live YAML; see `sidequest-content/genre_packs/heavy_metal/progression.yaml`. |
| caverns_and_claudes   | progression.yaml    | empty (declared)    | Delver / Plunderer / Slayer / Spellweaver / Steel affinities already carry rich `unlocks` → `mechanical_effects` lands on the same tiers when content arrives. Meta-humor genre, so mechanical depth is low priority. |
| elemental_harmony     | progression.yaml    | empty (declared)    | Element affinities already host tiered abilities; `mechanical_effects` lives there rather than in a parallel file. Future story will wire element-specific BeatDiscount / LeverageBonus. |
| mutant_wasteland      | advancements.yaml   | empty (declared)    | Radiation mutations and scavenger perks do not map cleanly to the six-affinity structure used by other packs — a sidecar keeps the mutation catalogue independent from the core progression tree. |
| neon_dystopia         | advancements.yaml   | empty (declared)    | Cybernetic augments are modular and cross-cutting (a neural jack is not a tier on a single affinity). Sidecar allows augment grants to reference multiple triggers and class gates without forcing them into a progression slot. |
| pulp_noir             | progression.yaml    | empty (declared)    | Hunch / Heat / Leverage / Grit affinities carry mechanical effects on their tiers — same pattern as heavy_metal. |
| road_warrior          | advancements.yaml   | empty (declared)    | Vehicle modifications are first-class content — a sidecar lets mod-grant tiers reference `vehicle_class` gates and beat ids from the dogfight subsystem (ADR-077) without cluttering driver progression. |
| space_opera           | progression.yaml    | empty (declared)    | Ship officer archetypes use affinity tiers (Command / Science / Operations / Security) — mechanical effects host there. |
| spaghetti_western     | progression.yaml    | empty (declared)    | Draw / Grit / Survival / Reputation affinities host mechanical effects on tiers, matching heavy_metal / pulp_noir. |
| tea_and_murder              | progression.yaml    | empty (declared)    | Propriety / Reason / Sentiment / Constitution affinities — same host pattern as pulp_noir. |

**Summary:** 7 progression-hosted, 3 sidecar-hosted. The sidecar choice is
reserved for genres where the mechanical content is either modular
(cybernetics, vehicle mods) or categorically outside the affinity model
(mutations). The default is the progression host — it keeps the mechanical
hook adjacent to the authored ability narrative.

## Wiring Path

> The harvest and consumption steps below are the **Rust-era design**; the
> harvester (`load_advancement_tree`) and the consumption engine
> (`resolved_beat_for` / `grant_advancement_tier`) did not port and are
> deferred (ADR-087). Only the data models and `progression.yaml`
> deserialization are live today.

For the progression-hosted genres, the intended `load_advancement_tree`
harvester walks `progression.yaml → affinities[].unlocks.{tier_0..tier_3}.mechanical_effects`
and yields an `AdvancementTier`
(`sidequest-server/sidequest/genre/models/advancement.py`) per populated host.
Tier ids are synthesised as `{affinity_lowercase}_tier_{n}`; authors do not
write ids by hand in this path.

For sidecar-hosted genres, authors write the full `AdvancementTree` YAML
directly, including explicit tier ids. The sidecar schema matches the
`AdvancementTree` type exactly.

Both paths terminate in the same runtime type — `AdvancementTree` — intended to
be consumed identically by `resolved_beat_for` and `grant_advancement_tier`
(Rust-era game-crate functions; **not yet ported** — ADR-087).

## Non-Goals (Story 39-5)

- **Landing content for the other nine genres.** Each genre's mechanical
  content is its own story. This audit captures the *decision*, not the YAML.
- **Migrating from one host to the other.** A genre that declares
  progression and later decides it needs the sidecar (or vice versa) does so
  in a follow-up story that moves the content and lands the dual-host
  validation test.
