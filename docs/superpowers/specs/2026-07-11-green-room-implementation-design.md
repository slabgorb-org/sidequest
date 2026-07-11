# The Green Room, One Cut — Big-Bang Implementation Design

**Date:** 2026-07-11 · **Author:** Architect (Naomi Nagata, design mode) · **Status:** Approved by Keith 2026-07-11
**Supersedes nothing; implements:** ADR-156 (accepted 2026-07-11 with Amendments A + B)
**Closes:** story 166-5 (wrong-Other seated) · **Origin:** brainstorm on 166-5 after the 2026-07-10 /sq-playtest sweep

---

## 1. Why this exists — the post-mortem in three sentences

Epic 162 delivered the Green Room's *substrate* (162-1 derive-don't-cache manual,
162-2 id-keyed identity + alias ledger, 162-3 bestiary generics) and archived with
ADR-156 still `proposed` — the acceptance never happened, the implementation stories
were "deliberately unfiled until accepted," and no process mechanism ever re-surfaced
them. The opponent-seating stack the ADR was written to replace therefore survived
intact, and the 2026-07-10 playtest reproduced the wrong-Other bug in three contexts
(flickering_reach Resonance Grazer, shattered_accord Restless Battlefield Ghost, the
parked coyote_star Gengineered Killer — all logged in `~/Projects/sq-playtest-pingpong.md`).
This spec is the implementation the ADR was always the gate for, executed as **one
branch, one merge** per Keith's explicit call ("3. I am tired of this").

### 1a. The mechanism, precisely (from the 2026-07-10 Chico trace)

- The seater runs **pre-narrator** (ADR-113 dispatch bank). The person the player
  struck ("the loudest Scrapborn in the tally line") exists only in prose at that
  moment — the mention path minted him (`npc.invented_name_routed 'the Scrapborn' →
  'Ihnsch of the Rusted Works'`) **after** the seat was already taken.
- The router names the target as a free string; `resolve_roster_npc` finds no match
  (he isn't an entity yet); the 153-10 pool-antagonist guard requires an **exact**
  name match and cannot fire on a first-engagement turn.
- The **108-2 conscription** (`_resolve_opponent_from_roster`,
  `encounter_lifecycle.py:1313`) then "reconciles" the unresolvable name to a
  co-located, `creature_id`-statted, hostile NPC — which, after Monster-Manual
  injection (7 patches for `toods_dome`, the split-brain region — finding #4), is an
  ambient bestiary herbivore. The dev-gotcha (`dev-gotchas.md:1061`) states the
  structural truth: *"the snake and a legit Molgrath are structurally identical to
  it."* The conscription is a name-agnostic guess by construction.
- The guess has been narrowed five times — 108-2 (#866), 150-2 (category gate),
  153-9 (Fate decline), 153-10 (pool preference), 158-1/-28/-34 (zone reconcile,
  registry normalization, ship-scale firewall) — and the 166-5 repros all live in
  its remaining legal window: combat + WN binding + no exact pool match.
- The **correct path already exists**: if conscription declines, the seater seats
  the router-named threat (`seating_source="materialized"`,
  `encounter_lifecycle.py:2034-2098`), promotes a pool member, or backs the seat
  with 162-3 generics. Conscription pre-empts it.

## 2. Decisions locked (all Keith, 2026-07-11)

1. **Full Green Room now** — 166-5 is closed by this work, not by a targeted patch.
2. **ADR-156 Amendment A** — targeting ≠ arbitration. The seater is target-first;
   the origin ladder arbitrates identity, never overrides the action's target.
3. **ADR-156 Amendment B** — the router-named opponent is the modeled eighth feeder
   (tier 5, pre-narrator, deterministic mint id, authored stat backing).
4. **The 108-2 conscription is deleted outright** — not gated a sixth time. Its
   legitimate case (prose-alias of a bound creature) is covered by the 162-2
   resolver + alias ledger + §6 attach-before-mint.
5. **Big-bang execution** — one branch (`feat/green-room`), internal commit order =
   dependency order, merged as one unit. Nothing lands half-wired.

## 3. Scope of the cut

**Repos:** sidequest-server (all runtime work) · orchestrator (ADR + this spec +
sprint bookkeeping) · sidequest-understudy (wrong-Other detector extension).
**Non-goals:** the split-brain region bootstrap (166 finding #4 — ADR-152
eligibility territory, its own story); the parked faction-leaders content question;
any change to ADR-116's `NoOpponentAvailableError` semantics or to the 162-3
generics/loud-failure contract.

### 3.1 The gate

`GreenRoom.admit(candidates, current_npcs) -> npcs` per ADR-156 §4, called where
Monster-Manual injection already runs every turn pre-narrator
(`websocket_session_handler.py:835-865`), and callable post-narration for the
narrator-mint feeders.

- `MaterializationCandidate(origin: Origin, proposed_fields)` — **reuses 162-2's
  typed `Origin` and `IdentityKey` unchanged.** No new provenance system, no new
  store, no new call site (ADR-156 §8).
- Group candidates by `IdentityKey`; canonical = highest `Origin.tier`
  (deterministic tiebreak: source order, then content_version).
- **Additive merge:** non-canonical candidates fill *absent* fields only; every
  prose name lands in the alias ledger.
- **Idempotence:** an already-materialized identity keeps its live mechanical state
  (HP, disposition, beliefs, last_seen) — `admit` adds identities and aliases, never
  resets. ADR-139 Invariant 2 (`injection_hp_preserved`) stops being a carve-out
  and becomes what the gate does by construction; the carve-out code retires.

### 3.2 The eight feeders

All production paths stop appending to `snapshot.npcs` and emit candidates:

| # | Feeder (existing seam) | Tier |
|---|---|---|
| 1 | MM available-humans, authored backfill (`monster_manual_inject.py:274`) | 1 authored (backfill) / 4 MM pool (pregen) |
| 2 | MM encounters (`:412`) | 4 MM pool |
| 3 | MM room-binding (`:623`, story 107-2) | 2 room-bound |
| 4 | MM region-population (`:582`) + materializer `region_population` | 3 region-population |
| 5 | Authored preload (`world_materialization.py:824`) + zone-cast staging (`region_cast_staging.py:48`) | 1 authored |
| 6 | Narrator mentions (`narration_apply.py` `_apply_npc_mentions`) | 5 narrator mint (post-narration) |
| 7 | Prose extraction (`session_helpers.py` `_auto_mint_prose_only_npcs`) | 5 narrator mint (post-narration) |
| 8 | **NEW: router-named opponent** (Amendment B) — a confrontation dispatch whose `params["opponent"]` resolves to no existing identity | 5 router mint (pre-narrator) |

Feeder 8's identity is the §3 deterministic mint id; its stats come from the world
bestiary `generics:` row (162-3) or the cdef's `opponent_default_stats`
(frame-sourced carve-out unchanged) — never fabricated (ADR-139: the damage lever is
authored content). Legacy direct appends are **deleted** — one door onto the stage.

### 3.3 The seater collapse (this is the 166-5 fix)

- **Target-first** per Amendment A: resolve `params["opponent"]` via
  `resolve_roster_npc` (canonical → alias → invented_from) → seat the match; no
  match → feeder 8 admits the named person → seat *that*. **Never substitute** a
  different co-located identity.
- **Delete `_resolve_opponent_from_roster` whole** — the conscription, the
  150-2/153-9/153-10 decline gates, the spans
  (`encounter.opponent_resolved_from_roster`, `encounter.roster_resolution_skipped`),
  and their tests (`tests/server/test_opponent_roster_resolution.py` et al.). The
  seater's remaining sources, in order: named target (authoritative) → ADR-116 §2
  room-scan (*only* for genuinely-unnamed dispatches) → `NoOpponentAvailableError`
  → prose. `seating_source` on `participant.joined` is retained.
- Stub-mint stays the 162-3 loud failure (`allow_synthetic_opponent` test-only
  opt-in unchanged).
- Ship-scale / sealed-letter firewalls (ADR-153 §6, 158-34) are untouched — they
  live on the no-named-target branch and already refuse personal-scale sources.

### 3.4 §6 attach-before-mint

The mention path's first action becomes **attach, not mint**: a prose name tries the
seated confrontation Other first, then the highest-precedence unaliased identity
active in the scene, before minting a new pool member. "Ihnsch of the Rusted Works"
attaches to the seated Other instead of minting a twin beside it. A flavor name
landing on a bare generics row emits the ADR-128 promotion signal (coal → diamond).
The precise matching heuristic reuses the 162-2 resolver legs; both narrator-mint
feeders (6, 7) route their would-be mints through this pass.

### 3.5 OTEL (the lie detector moves)

New span family, GM-panel wired via the existing watcher:

- `green_room.materialized {identity_key, canonical_tier, canonical_source, candidates_seen, candidates_dropped, alias_count}`
- `green_room.precedence_conflict {identity_key, winning_tier, losing_tiers}`
- `green_room.alias_attached {identity_key, alias, from_tier}`
- `green_room.mint {identity_key, prose_name, content_version}`

Retired with their code: `encounter.opponent_resolved_from_roster`,
`encounter.roster_resolution_skipped`, the ADR-139 `injection_hp_preserved`
per-actor carve-out span (subsumed by gate idempotence).
`encounter.opponent_minted_stub` stays alarm-only (162-3 contract).

### 3.6 Verification — what makes a big-bang survivable

1. **All-sources-one-scene** (extends 162-7's regression guard): every one of the
   eight feeders fires in one scene → exactly one identity per creature, asserted
   by `IdentityKey`, with decoy rosters (162-10 pattern).
2. **The three playtest repros as fixtures** (fixture-driven behavior tests per the
   server testing doctrine — no source-text assertions):
   - *Salt Camp brawl:* router names an unmaterialized person; co-located MM
     bestiary mobs present → the seated Other is the named person (mint-tier), not
     the mob.
   - *Courier grapple:* same shape, WWN pack.
   - *Ship duel:* sealed-letter/frame path still seats the frame Other — proves the
     deletion didn't reopen 158-34.
3. **Idempotence:** `admit` twice in one turn and across turns → no HP/disposition
   reset (replaces the ADR-139 carve-out test).
4. **Alias attach:** post-narration prose rename attaches to the seated Other; the
   next turn's router reference by either name resolves to one identity (the
   Molgrath regression — proves conscription's legitimate case survives its
   deletion).
5. **Loud failure:** Other-requiring type + no named target + empty room + no
   generics → raises; nothing half-seated (162-3 rollback contract).
6. **Understudy:** extend the 162-11 identity-split detector with a wrong-Other
   check (seated opponent name absent from the turn's narration = finding); run a
   live flickering_reach session before merge.
7. `just server-check` green; deleted tests removed with their gates, not skipped.

## 4. Execution shape

Single branch `feat/green-room` in sidequest-server. Internal commit order = the
dependency order (gate → feeders → seater collapse + conscription deletion →
attach-before-mint → verification), so review can walk it, but it merges as **one
PR**. Orchestrator carries the ADR acceptance + this spec; understudy carries the
detector extension as its own small PR gated on the server merge. Drummer (SM) files
the epic shell around the branch and re-points 166-5 to it.

**Risk register, stated plainly:**

- *Largest server PR in months.* Mitigation: the §3.6 harness is written to fail
  loud on every seam the cut touches; commit order permits bisection.
- *Highest-regression area:* the two narrator-mint feeders (`narration_apply.py`
  mention matching has four legs + name-mint routing). Mitigation: the 162-2/162-10
  resolver tests already pin those legs; attach-before-mint adds behavior *before*
  the mint branch and changes no matching leg.
- *Split-brain region (166 #4) still feeds wrong-region candidates* — the Green Room
  stops the wrong candidate *winning the seat*, not the wrong region *feeding the
  pool*. That story stands alone; do not fold it in.
- *Resume determinism:* mint ids depend on `content_version` + `session_seed`
  (162-1); both landed. The §3.6-4 alias test doubles as the resume-fork guard.

## 5. What "done" means

- ADR-156 `status: accepted`, Amendments A + B in-body, indexes regenerated.
- Zero direct appends to `snapshot.npcs` outside `GreenRoom.admit`.
- `_resolve_opponent_from_roster` does not exist; its tests are deleted.
- The three repro fixtures pass; the understudy live run reports no wrong-Other
  finding; `green_room.*` spans visible in the GM panel.
- 166-5 closed with a pointer to this spec. Epic 166's remaining stories unaffected.
