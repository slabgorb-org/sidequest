# Epic 162: NPC origin consolidation — one identity, one arbiter, derived Monster Manual

## Overview

Consolidate SideQuest's NPC/creature generation, which today converges on `snapshot.npcs` from **seven production spawn paths with no precedence arbiter**, reconciled only by name-string dedup that is normalized differently at every seam. The epic delivers three structural fixes in sequence — a derive-don't-cache Monster Manual, id-keyed identity with a prose-name alias ledger, and the Green Room origin-precedence ADR — plus content-drift reconciliation and a permanent lie-detector (wiring test + understudy identity-split hunt). Source of truth for the problem statement: the 2026-07-05 NPC-generation inventory.

**Priority:** P1
**Repo:** server, content, understudy
**Stories:** 8 (18 points)

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **NPC-generation inventory** (`docs/superpowers/specs/2026-07-05-npc-generation-inventory.md`) | Whole document — esp. §3 creation-path inventory, §4 ranked conflict ledger, §5 beneath_sunden case file, §7 open verification items V1–V6, §8 design questions D1–D6 |
| **ADR-059 Monster Manual** (`docs/adr/059-monster-manual-server-side-pregen.md`) | Pre-gen + game-state injection doctrine; 2026-07-02 bestiary-as-source-of-truth addendum; 2026-07-05 implementation-status correction |
| **ADR-155 bestiary-derived creature images** (`docs/adr/155-*.md`) | The derive-don't-duplicate precedent 162-1 generalizes to runtime; creatures.yaml demotion contract 162-5 enforces |
| **ADR-116 / ADR-139 confrontation invariants** (`docs/adr/116-*.md`, `139-*.md`) | Opponent-seater contract, the Other, toothless-Other/`opponent_damage`; 162-3 replaces the stub-mint tail of the seating stack |
| **ADR-117 / 142 / 143 / 144 ruleset modules** (`docs/adr/`) | Genre-scoped session-fixed ruleset binding — why there is no Fate-vs-WWN conflict; WN roster-seating doctrine (108-2 lineage) |
| **ADR-118 retrieval / ADR-138 ratification** (`docs/adr/`) | `NpcPoolMember` vs `Npc`, pool promotion, `invented_from`/`pool_origin` provenance fragments 162-2 unifies |
| **ADR-106 procedural megadungeon** (`docs/adr/106-*.md`) | `region_population` feeder (Amendment C deterministic curate) — one of the seven paths the Green Room ADR must order |
| **ADR-115 persistence substrate** (`docs/adr/115-*.md`) | PG-per-session — a candidate home for the Manual pool if 162-1 forensics rejects content-sha file keying |
| **ADR-087 restoration plan** (`docs/adr/087-*.md`) | "Sweep changes through 2026-07-05" note — current truth on pregen/namegen/encountergen (live) vs loadoutgen (dead) |
| **Party-mode session record 2026-07-05** (chat; summarized in epic description) | Sequencing rationale (cache → aliases → ADR), bestiary-generics and alias-ledger idea provenance |

## Background

**Why this epic exists.** Playtests on caverns_and_claudes/beneath_sunden kept producing "random" NPC behavior — opponents nobody authored, two names for one enemy (narrator prose fights "Molgrath the Eyeless" while the engine seats an invented "Hold-Dead, HP 10, `creature_id=None`" — the open 108-2 finding), and creatures appearing or vanishing across the static→procedural seam. The initial theory ("the beneath_sunden WWN system is fighting the Fate system") was **disproven** by the 2026-07-05 survey: ruleset is genre-scoped and session-fixed (`RulesConfig.ruleset` at `genre/models/rules.py:1277`; no `World.ruleset` field; one module bound per session at `server/session.py:99`), so Fate paths cannot fire in a caverns session.

**The real disorder is structural, in three layers:**

1. *No origin arbiter.* Seven server paths append to `snapshot.npcs`/`npc_pool` (Monster Manual injection with four patch builders inside it; narrator `_apply_npc_mentions` minting; prose-extraction minting; opponent-seater fabrication; session-start authored cast; zone-cast staging; procedural region population). Doctrine review confirms no ADR establishes precedence among the four sanctioned creature origins (authored / MM pre-gen / bestiary-sample / procedural roll-at-attach) — epic 157's faction-zone predicate is the closest partial reconciler.
2. *Name-string identity.* Dedup, purge, seating, and pool promotion all key on names with per-seam normalization (exact / casefold / comma-inverted / `invented_from` alias). Narrator flavor-names fork identity instead of attaching to it.
3. *A shared mutable cache fought over by four clones.* `~/.sidequest/manuals/{genre}_{world}.json` is written by oq-1..oq-4 with divergent content checkouts. Evidence: beneath_sunden's manual sits at 0 NPCs/0 encounters while `purge_foreign_bestiary_encounters` fired **14×** (purged=2 each — a purge/reseed livelock between divergent writers) and its authored-cast count oscillates 0↔4 across 64 loads; at the other extreme flickering_reach holds 310 pooled NPCs and glenross 1,153 (unbounded accumulation); ghost manuals exist keyed with an empty world slug. With the pool starved, WN rounds fall through the six-strategy seating stack to ephemeral stub minting — the observed randomness.

**Why now, and for whom.** The identity split is player-visible in the combat panel — a mechanical-legibility failure for Sebastien and Jade (the group's mechanics-first players), not just dev-side debt. The bestiary-generics story additionally keeps the last-resort opponent **authorable as content** (the Jade homebrew requirement: crunch expressible without engine code). Two prior repair-purges (150-20 stale-ruleset, 158-33 foreign-bestiary) are tourniquets that prove the cache design is wrong; 158-52 already established the correct doctrine at the render layer — *derive, don't duplicate* — and this epic applies it at runtime.

**Content drift riding along.** The survey also found hard content rot: flickering_reach's encounter tables reference 18/20 phantom creature ids and its creatures.yaml still carries a full stat block that disagrees with its bestiary (the last ADR-155 violation); space_opera's three worlds carry byte-identical copy-pasted 12-entry bestiaries because the genre ships no genre-root file.

## Technical Architecture

**Sequencing (party-mode 2026-07-05, Drummer's order):** 162-1 first (cheapest fix, kills the most observed randomness), 162-2/162-3 second (player-visible identity fixes), 162-4 (Green Room ADR) gates any larger refactor — implementation stories for the Green Room itself are deliberately **not** pre-filed; they follow ADR acceptance. 162-5/6/7/8 are independent and parallelizable.

**Current data flow (what the epic reorders):**

```
authored npcs.yaml ─ preload_authored_npcs ─┐
history.yaml chapters ─ WorldBuilder._apply_npc ─┤
cartography entities ─ stage_region_cast ─────┤ (pool)
MM pool (pregen namegen+encountergen) ─┐      │
room encounter_creatures → bestiary ───┤ inject├─→ snapshot.npcs ←─ opponent-seater
region_population (procedural) ────────┘      │        ↑ (6-strategy fallback,
narrator NpcMention mint ─────────────────────┤ (pool)  │  last resort = stub mint)
prose-extraction mint ────────────────────────┘         │
                    pool promotion (3+ sites, name-keyed) ┘
```

**Key files:**

| File | Role in epic |
|---|---|
| `sidequest-server/sidequest/server/dispatch/monster_manual_inject.py` | `ensure_loaded` purge/reseed + 4 patch builders — 162-1's primary surface; purges deleted when staleness becomes impossible |
| `sidequest-server/sidequest/game/monster_manual.py` | Manual model, `needs_seeding`, name-keyed purge membership — 162-1/162-2 |
| `sidequest-server/sidequest/server/dispatch/pregen.py` | `seed_manual` (namegen+encountergen in-process) — 162-1 keying + cap |
| `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` | Seating stack + `_seed_combat_hp_depletion_to_npcs` stub mint (L428) — 162-3 |
| `sidequest-server/sidequest/server/dispatch/narration_apply.py` | `_apply_npc_mentions`, pool promotion, `invented_from` — 162-2 alias ledger |
| `sidequest-server/sidequest/server/session_helpers.py` | `_auto_mint_prose_only_npcs` (second narration-mint path) — 162-2 |
| `sidequest-server/sidequest/genre/models/pack.py:540` | `effective_bestiary` world-over-genre resolution — 162-1 (purge/seed agreement) + 162-6 |
| `sidequest-content/genre_packs/*/worlds/*/bestiary.yaml` | 162-3 generics section (schema addition, `extra="forbid"` model change needed); 162-5/162-6 reconciliation |
| `sidequest-understudy` findings pipeline | 162-7 identity-split hunt scenario |

**Interface contracts to be established (162-2 / 162-4 design surface):**
- `Origin` — one typed provenance struct unifying `invented_from` / `pool_origin` / `manual_origin` / `creature_id`, stamped by every feeder.
- Alias ledger — narrator prose names attach to an existing identity (display-layer), never fork it; flavor-naming a generic is a candidate ADR-128 promotion signal.
- Manual pool keying — content-sha + session-seed (deterministic regeneration per ADR-128 resume-safe randomness precedent); discard-on-mismatch replaces purge-repair; fail loud on empty-world-slug keys.
- Bestiary `generics` — sanctioned per-world last-resort rows; stub fabrication on non-degenerate paths becomes a loud failure (No Silent Fallbacks).
- Green Room (ADR, 162-4) — single-gate materializer; precedence authored > room-bound > region-population > MM pool > narrator mint.

**OTEL:** every changed seam keeps/extends its lie-detector span (`monster_manual.injected`, `encounter.opponent_minted_stub`, `npc.spawn_disposition`, purge spans until deleted). The 162-7 wiring test asserts one identity per creature with all sources firing in one scene.

## Cross-Epic Dependencies

**Depends on:**
- Epic 158 (playtest sweep) — supplies the fix lineage this epic builds on: 158-1 region-aware co-location, 158-33 foreign-bestiary purge (deleted by 162-1), 158-52 derive-don't-duplicate doctrine, 158-60 low-band re-tier. Open 158-61 (107-2 gate hardening) touches the same room-binding surface — coordinate, don't collide.
- Open finding 108-2 (WN round must seat its Other from the bound roster) — 162-2's alias ledger addresses the identity-fork half; the seating-preference half stays with 108-2. Complementary, not duplicative.
- Epic 157 (faction-zone eligibility) — its eligibility predicate is an input to the Green Room ADR's precedence design (162-4).
- Epic 73 (ADR-139 invariant verification) — toothless-Other spans should be green before 162-3 changes the stub path, or verified together.

**Depended on by:**
- Green Room implementation stories (post-162-4 ADR acceptance — intentionally unfiled until the design lands).
- Future content authoring (Jade's homebrew path) — 162-3's generics section becomes part of the world-authoring contract; 162-5/162-6 leave the bestiary layer clean enough to document as such.
- Any future world using the procedural dungeon (heavy_metal/barsoom next) — inherits the consolidated spawn order instead of the current seven-way race.

**Open question for Keith (parked, not a story):** faction leaders named only in `lore.yaml` prose — structured `npcs.yaml` entries or prose-only by design.

---
_Created by Architect (Naomi Nagata, design mode) 2026-07-05 from the NPC-generation inventory, party-mode session, and epic 162 sprint data._
