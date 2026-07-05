---
id: 156
title: "The Green Room — A Single-Gate NPC Materializer with Typed-Provenance Feeders and an Origin-Precedence Ladder (authored > room-bound > region-population > MM pool > narrator mint)"
status: proposed
date: 2026-07-05
deciders: ["Keith Avery", "Naomi Nagata (Architect)"]
supersedes: []
superseded-by: null
related: [7, 59, 106, 109, 116, 118, 121, 128, 138, 139, 140, 152, 155]
tags: [npc-character, game-systems, agent-system, observability]
implementation-status: not-applicable
implementation-pointer: "PROPOSED — design gate for epic 162; nothing built yet. Green Room implementation stories are deliberately unfiled until this ADR is accepted. Substrate stories that must land first: 162-1 (derive-don't-cache Monster Manual → supplies content_version keying), 162-2 (identity-by-id + alias ledger → supplies IdentityKey and the alias ledger), 162-3 (bestiary generics → supplies the sanctioned last-resort Other). Seams the eventual materializer replaces: sidequest-server sidequest/server/dispatch/monster_manual_inject.py (ensure_loaded + 4 patch builders → 4 feeders), sidequest/server/dispatch/narration_apply.py (_apply_npc_mentions → narrator-mint feeder), sidequest/server/session_helpers.py (_auto_mint_prose_only_npcs → second narrator-mint feeder), sidequest/server/dispatch/encounter_lifecycle.py (_seed_combat_hp_depletion_to_npcs stub-mint L428 → loud failure; six-strategy seating stack → Green-Room consumer), sidequest/game/world_materialization.py (preload_authored_npcs → authored feeder), sidequest/game/region_cast_staging.py (stage_region_cast → authored feeder), sidequest/game/materializer.py (region_population → region-population feeder). Single-gate call site: sidequest/server/websocket_session_handler.py:835-865 (where injection already re-runs every turn pre-narrator)."
---

# ADR-156: The Green Room — A Single-Gate NPC Materializer with Typed-Provenance Feeders and an Origin-Precedence Ladder

> Status **proposed**. This ADR answers design question **D1** of the 2026-07-05
> NPC-generation inventory (`docs/superpowers/specs/2026-07-05-npc-generation-inventory.md`)
> and is story **162-4** of the NPC-origin-consolidation epic. It is **design only** —
> the metaphor, the precedence ladder, and the three interface contracts. Nothing is
> built here; the Green Room *implementation* stories are intentionally not filed until
> this decision is accepted, because the ladder is the thing that has to be agreed
> before any of the seven feeders is rewired. Sequencing (party-mode 2026-07-05,
> Drummer's order): 162-1 (cache), 162-2 (identity/alias), 162-3 (generics) supply the
> substrate; this ADR gates the refactor that consumes them.

## Context

SideQuest materializes every NPC and creature into one canonical list —
`snapshot.npcs` — and **seven production paths append to it with no precedence
arbiter.** The inventory enumerates them (§3a); doctrine review confirms no existing
ADR orders the sanctioned creature origins (§4 conflict #1, survey-doctrine
contradiction #5). The closest partial reconciler is ADR-152's faction/zone
*eligibility* predicate — but eligibility answers "may this pool feed this scene?",
not "when two feeders propose the same enemy, which one is real?"

The absence of an arbiter is felt as three symptoms:

1. **N-source convergence.** For a single scene, `snapshot.npcs` can receive a
   Monster-Manual human, an MM encounter, a room-bound bestiary creature, a
   procedural region-population creature, a narrator mention, and an authored
   preload — and they are reconciled only by **name-string dedup that is normalized
   differently at every seam** (exact / casefold / comma-inverted / `invented_from`
   alias). A bestiary creature, its procedural counterpart, and a narrator invention
   with slightly different names coexist as three "enemies."

2. **Identity is a name.** Purge membership, seater matching, MM dedup, pool
   promotion, and `EncounterActor` references are all name-keyed (§4 conflict #7).
   The narrator renames a `creature_id=Thief` to "Molgrath the Eyeless" in prose and
   *forks* identity — the open **108-2 two-names-one-enemy** report: the engine seats
   "Hold-Dead, HP 10, `creature_id=None`" while the narration talks about Molgrath.

3. **A six-strategy seating fallback stack** (`encounter_lifecycle.py:1492`) that
   *guesses* when the sources disagree. Its last resort is **ephemeral stub minting**
   (`_seed_combat_hp_depletion_to_npcs` L428) — a `creature_id=None` combatant
   fabricated on the spot. beneath_sunden is the perfect storm (empty MM pool +
   192-entry SRD bestiary + procedural seams), so its WN rounds routinely fall all the
   way through to stub-mint. That is the observed "random things happening."

The **initial theory was wrong**: there is no Fate-vs-WWN fight (`ruleset` is
genre-scoped and session-fixed — one module per session, `server/session.py:99`; no
`World.ruleset` field). The disorder is structural: **too many doors into the
theater, and no stage manager.**

This ADR installs the stage manager.

## Decision

### The metaphor

A theater has one **green room** — the place where cast members wait, in costume and
identified against the call sheet, before they step on stage. Today SideQuest has
seven unmarked doors that open directly onto the stage (`snapshot.npcs`), and two
actors playing the same role can both walk on under different names. **The Green Room
is the single stage door with a stage manager.** Every arrival — from every feeder —
is checked against the call sheet (identity), given exactly one entry per role
(precedence), and its stage-name (narrator prose) is written next to its real name
(alias), never in place of it.

Concretely: the Green Room is a **single-gate materializer**. All seven paths stop
appending to `snapshot.npcs`. Instead each becomes a **feeder** that emits
`MaterializationCandidate(origin, proposed_fields)`. The gate runs where injection
already re-runs every turn (pre-narrator, `websocket_session_handler.py:835-865`),
collapses candidates to one identity per creature by precedence, and produces the
canonical `snapshot.npcs`.

### 1 — The origin-precedence ladder (the load-bearing decision)

Every candidate carries an **origin tier**. When two or more candidates resolve to the
same identity, the **highest tier is canonical** — it owns the mechanical fields
(stat block, HP defaults, disposition, `creature_id`). Lower tiers may contribute
non-conflicting additive fields and always contribute prose names as aliases.

| Rank | Tier | Feeders that emit it | Why it sits here |
|------|------|----------------------|------------------|
| 1 | **authored** | session-start cast (`preload_authored_npcs` + history chapters); zone-cast staging (`stage_region_cast`, `world_authored`); MM available-humans *authored backfill*; bestiary **generics** rows (162-3) | A human deliberately placed a *named character* with OCEAN, disposition, and history. The world owns the cast (ADR-140, SOUL "Crunch in the Genre, Flavor in the World"). Richest, most intentional record wins. |
| 2 | **room-bound** | MM room-binding patch (107-2): room YAML `encounter_creatures` → bestiary | Authored too, but thinner — a bestiary reference *pinned to a location*. More specific than a general region roster; less than a full authored character. |
| 3 | **region-population** | procedural megadungeon population (`materializer` → `region_population`); MM region-population patch | A **placed, frozen, deterministic** roster (ADR-106 Amdt C). A real persistent creature that belongs to this region — outranks anything merely *available*. |
| 4 | **MM pool** | MM available-humans (pre-gen) and encounters patches (namegen + encountergen) | Correct genre/bestiary shape and mechanical backing, but **available, not placed** — a bench of extras. Outranks improvisation; yields to anything actually sited in the scene. |
| 5 | **narrator mint** | narrator mentions (`_apply_npc_mentions`); prose extraction (`_auto_mint_prose_only_npcs`) | The narrator improvising, with **no mechanical backing**. Valuable for Yes-And walk-ons (SOUL), but must **never** override a mechanically-backed entity. This is the Illusionism guard — the improviser is the lowest authority. |

The seventh path — the **opponent-seater** — is **not a feeder**. It is a *consumer*:
it seats a confrontation's Other from the Green Room's already-materialized identities,
in precedence order, for the current scene. It mints nothing. (See §5.)

**Rationale for the ordering, pairwise:** authored beats room-bound because a named
character outranks a location's generic binding when they collide (rare — different
identity spaces; the merge rule below handles placement-vs-stats without a fight).
Room-bound beats region-population because a hand-placed enemy is more deliberate than
a procedural roll. Region-population beats MM pool because *placed* beats *available*.
MM pool beats narrator mint because *mechanically backed* beats *improvised* — the one
relationship the whole epic exists to enforce.

### 2 — `Origin`: one typed provenance struct (reuse, don't add)

D1 is explicit: `invented_from`, `pool_origin`, `manual_origin`, and `creature_id`
already exist as **partial** provenance breadcrumbs scattered across the feeders.
**Unify them; do not add a parallel system.** Every candidate carries:

```
Origin:
  tier:            OriginTier   # AUTHORED | ROOM_BOUND | REGION_POPULATION | MM_POOL | NARRATOR_MINT
  source:          str          # the specific feeder, e.g. "preload_authored_npcs", "mm.room_binding", "narrator_mention"
  identity_ref:    IdentityRef  # authored_id | creature_id | minted stable id (see §3)
  content_version: str          # content-sha / world content version (from 162-1) — staleness = discard, not repair
```

`tier` replaces the ad-hoc ordering baked into `monster_manual_inject.py:802-806`
("authored-wins" by string). `source` and `content_version` are what the OTEL lie
detector reports. The four legacy fragments collapse into `identity_ref` + `source`.

### 3 — `IdentityKey`: identity by id, not by name

The dedup/purge/seating key is **never a name**. It resolves in this order:

1. **authored_id** — if the entity is authored (npcs.yaml key, cartography entity id,
   bestiary-generics id).
2. **creature_id** — if it is a bestiary or procedural creature.
3. a **deterministically minted stable id** for a narrator invention that matches no
   existing identity: `mint:{hash(content_version + session_seed + normalized_name)}`.
   Deterministic per ADR-128 resume-safe randomness, so a resume regenerates the same
   id and a later turn naming the same walk-on resolves to the same key — the mint no
   longer forks on re-mention.

Two feeders that reference the same underlying `creature_id` produce the **same**
`IdentityKey` and collapse to one identity. This is the structural cure for §4
conflict #7 and the 108-2 fork — implemented by story 162-2, ratified here.

### 4 — The `admit` gate and its merge/idempotence rules

```
GreenRoom.admit(candidates, current_npcs) -> npcs:
  group candidates by IdentityKey
  for each identity group:
    canonical := candidate with the highest-ranked Origin.tier
                 (ties broken deterministically: source order, then content_version)
    record := canonical.proposed_fields
    for each non-canonical candidate:
      fill record's ABSENT fields from it            # additive merge, never override
      record every prose name as an alias (§6)
    reconcile with current_npcs by IdentityKey:
      if already materialized -> preserve live mechanical state (HP, disposition,
                                 beliefs, last_seen); add only new aliases/absent fields
      else                    -> add record
  emit OTEL (§7)
```

Two properties are load-bearing:

- **Additive merge, precedence-gated conflicts.** Precedence resolves conflicts *on
  the same field only*. Non-conflicting fields merge freely — e.g. a room-bound
  candidate contributes *placement* while an authored candidate contributes *stats*;
  no fight. Precedence decides who wins **when both set the same mechanical field.**

- **Idempotence — the ADR-139 carve-out becomes structural.** Injection re-fires every
  combat turn and historically clobbered damaged HP back to full (§4 conflict #5;
  ADR-139's "the encounter is the authority on current HP" was the *patch*). Under the
  Green Room, `admit` **only adds identities and attaches aliases; it never resets the
  live mechanical state of an already-materialized identity.** ADR-139's carve-out is
  no longer a special case — it is what the gate does by construction.

### 5 — The seating stack collapses; stub-mint becomes a loud failure

With the Green Room seated for a scene, the six-strategy opponent-seating stack
(`instantiate_encounter_from_trigger`) reduces to: **seat the Other from the scene's
materialized identities, in precedence order.** Strategies 2 (zone-reconcile), 5
(frame-default), and 6 (stub-mint) become **assertion failures on non-degenerate
paths** (D6, SOUL *No Silent Fallbacks*) — not fallbacks.

The sanctioned last resort is **not** a stub. It is a **bestiary-generics row**
(story 162-3) — authored content with a stable id, real stats, and content
provenance, sitting at the **authored** tier. It keeps the last-resort Other
*authorable as homebrew* (the Jade requirement: crunch expressible without engine
code). The loud failure is: a confrontation needs an Other, the Green Room holds no
scene-appropriate identity, **and** the world authored no generics row → raise, don't
fabricate. A `creature_id=None` combatant is never again minted on a live path.

### 6 — The alias ledger (display layer, never identity)

A narrator prose name is a **stage name**, recorded against the identity it
describes — never a new identity. The alias ledger maps `IdentityKey → [names]` and
lives on the materialized record (`Npc.aliases`), not in a new store.

The narrator-mint feeder's **first action is attach, not mint**: before creating a new
identity it tries to attach the prose name to the highest-precedence *unaliased*
identity active in the current scene — the **seated confrontation Other first**, since
the narrator naming "the enemy" is unambiguous when exactly one Other is seated. Only
if nothing in the scene plausibly matches does it mint (§3, step 3). The combat panel
may show "Molgrath the Eyeless" while the engine keys on `creature_id=Thief` — one
enemy, one identity, two names. A flavor-name landing on a bare generic is a candidate
**ADR-128 promotion** signal (coal → diamond, SOUL *Diamonds and Coal*): the world
cared enough to name it.

*(The precise name-matching heuristic — casefold, comma-inversion, honorific
stripping — is 162-2's implementation surface. This ADR fixes only the principle:
attach before mint; the active Other is the primary attachment target.)*

### 7 — OTEL: the Green Room is the new lie detector

Per project doctrine (OTEL Observability Principle), every arbitration decision emits
a span the GM panel can verify:

- `green_room.materialized` — per admit: `{identity_key, canonical_tier, canonical_source, candidates_seen, candidates_dropped, alias_count}`
- `green_room.precedence_conflict` — when ≥2 tiers propose one identity: `{identity_key, winning_tier, losing_tiers}`
- `green_room.alias_attached` — `{identity_key, alias, from_tier}`
- `green_room.mint` — a narrator invention genuinely created a new identity: `{identity_key, prose_name, content_version}`
- `encounter.opponent_minted_stub` — **retained but repurposed**: fires only on the
  loud-failure path, as an alarm, never as routine. The `foreign_encounter_purged` /
  `stale_encounter_purged` spans are retired when 162-1 deletes the purges.

The panel can now answer, for any scene: *how many identities were proposed, who won,
what got dropped, and whether the narrator invented or attached.* Claude can no longer
"wing" an enemy into existence without a span recording that it did.

### 8 — Where it lives (reuse-first)

- **No new store.** `snapshot.npcs` remains the single canonical materialized list;
  `snapshot.npc_pool` remains identity-only staging (ADR-118/138). The Green Room is a
  **gate function**, not a database.
- **No new call site.** It runs where MM injection already runs every turn.
- **No new provenance system.** `Origin` unifies the four existing fragments.
- **No new persistence for aliases.** They ride on the `Npc` record (ADR-007).
- The four MM patch-builders, the two narrator-mint paths, the authored preload, the
  zone-cast observer, and the region-population loader all become **feeders emitting
  candidates** — same data, new contract.

## Alternatives Considered

**A — Keep name-string dedup, just standardize the normalization.** Rejected. It
treats the symptom (divergent normalization at each seam) not the disease (names are
not identities). A single normalization still forks "Molgrath the Eyeless" from
`creature_id=Thief`, because they are genuinely different strings for the same being.
Identity must be an id.

**B — One giant merge function per feeder pair.** Rejected as O(n²) coupling and
exactly the guessing the six-strategy stack already is. A single ordered ladder with a
uniform `admit` is O(n) and has one place to reason about precedence.

**C — Let the narrator own identity (mint freely; reconcile later).** Rejected on SOUL
grounds. The narrator improvising *is* the lowest authority (Illusionism guard). Giving
mint-first-reconcile-later semantics is how we got 108-2. Attach-before-mint inverts it
correctly.

**D — Move materialization into the PG substrate (ADR-115) as a new table.** Deferred,
not chosen. The Green Room is arbitration logic, not storage; it needs no new table.
162-1 separately decides the *Monster Manual pool's* home (content-sha keying vs PG) —
that is a cache-lifecycle question, orthogonal to the arbiter. Keeping them separate
avoids coupling this design to that outcome.

**E — Make room-bound outrank authored** (a room's explicit placement is "more
local"). Rejected. A hand-authored named character carries OCEAN, disposition, and
history that a bestiary-ref binding does not; when they collide on one identity the
richer record must be canonical. Locality is expressed by the additive merge
(room-bound contributes placement), not by inverting the tiers.

## Consequences

**Positive**

- One identity per creature, keyed by id, across all seven paths — kills the 108-2
  fork and §4 conflicts #1 and #7 at the root.
- The six-strategy seating stack and its stub-mint tail collapse to a precedence read
  (D6); `creature_id=None` combatants stop appearing.
- ADR-139's HP carve-out becomes structural (idempotent `admit`), retiring a patch.
- Player-visible legibility win: the combat panel shows one enemy with one stat line
  and a flavor name — the mechanics-first players (Sebastien, Jade) can trust the
  panel. The last-resort Other is authorable homebrew (Jade's content-not-code
  requirement).
- The Green Room becomes the lie detector for the whole spawn subsystem — one span
  family instead of scattered purge/mint logging.

**Negative / cost**

- Every feeder must be rewired to emit candidates instead of appending — a broad,
  cross-cutting refactor. This is *why* the implementation stories are unfiled until
  this ladder is accepted: agree the arbiter first, rewire once.
- Deterministic mint ids depend on 162-1's `content_version` and a stable
  `session_seed`; if either is unstable, resume can fork a mint. 162-1 must land first.
- Attach-before-mint adds a per-mention scene scan. Bounded (scene-scoped, precedence
  short-circuits on the seated Other), but non-zero — a *Cost Scales with Drama* trade
  that only runs on narrator-mint turns.

**Neutral**

- ADR-152 eligibility is unchanged and complementary: it filters *which* pools feed a
  scene; the Green Room arbitrates the survivors. 152 is an input to feeder candidate
  generation, not a competitor.
- `snapshot.npc_pool` and the ADR-138 ratification ladder are unchanged; pool→npcs
  promotion becomes one feeder among the seven, now precedence-ranked.

## Relationship to the epic

This ADR is the **gate** (162-4). It consumes the substrate the sibling stories build
and unblocks the Green Room implementation stories (intentionally unfiled until
acceptance):

- **162-1** (derive-don't-cache Monster Manual) — supplies `Origin.content_version` and
  the discard-on-mismatch keying; deletes the purge functions whose spans §7 retires.
- **162-2** (identity by id + alias ledger) — *is* `IdentityKey` (§3) and the alias
  ledger (§6); this ADR ratifies the design 162-2 implements.
- **162-3** (bestiary generics) — supplies the authored last-resort Other that replaces
  stub-mint (§5).
- **162-5/6** (content reconciliation) — leave the bestiary layer clean enough that
  `creature_id`-keyed identity is trustworthy input.
- **162-7** (all-sources-one-scene wiring test + understudy identity-split hunt) — the
  permanent regression guard: assert **one identity per creature** with every feeder
  firing in one scene, and flag two-names-one-enemy as an understudy finding.

**Depends on the design inputs of** ADR-152 (faction/zone eligibility predicate feeds
candidate generation), ADR-106 (region-population feeder), ADR-109/140 (authored world
cast), ADR-116/139 (opponent-seater and confrontation invariants — the consumer this
ADR reshapes), ADR-118/138 (pool + ratification), ADR-121 (layered resolution),
ADR-128 (resume-safe randomness + promotion ladder), ADR-155 (the *derive, don't
duplicate* precedent this generalizes from the render layer to runtime).

## Open question (parked for Keith — not resolved here)

Faction leaders named only in `lore.yaml` prose (e.g. coyote_star's Prefect Ilara
Vaskov, in no npcs.yaml) are today an **unstructured NPC source** the narrator
materializes with zero mechanical backing (§4 conflict #10). Under the ladder they
would enter as **narrator mint** (tier 5) unless promoted to structured `npcs.yaml`
(tier 1, authored). Whether prose-only faction leaders should stay prose-only by
design or get structured entries is a **content-authoring decision for Keith**, parked
in the epic — not a blocker for this arbiter design.
