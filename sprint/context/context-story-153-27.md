# Story 153-27 Context

## Title
[DUNGEON-ZONE-ELIGIBILITY-UNKNOWN-REGION] teach zone/cast-eligibility to recognize procedural dungeon region ids (entrance/expNNN.rN) so cast staging stops skipping every generated room

## Metadata
- **Story ID:** 153-27
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** server
- **Epic:** Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep

## Problem

The procedural Jaquaysed megadungeon (ADR-106, beneath_sunden) generates dungeon regions at runtime with ids in the shape:
- `entrance` (the starting region, Seed=Expansion-0)
- `expNNN.rN` (runtime-generated expansion regions, where NNN=expansion_id zero-padded to 3 digits, N=room index)

However, the zone/cast-eligibility subsystem that gates NPC cast staging into regions does not recognize these procedural region id shapes. It attempts to look them up in `cartography.regions` (the authored region dictionary), finds nothing, and logs a warning. As a result, **every NPC cast staging attempt into a procedurally-generated dungeon room fails silently** — no authored NPCs ever appear in generated rooms.

**Root cause:** The cartography lookup in `region_cast_staging.py:77` and the zone-check in `zone_eligibility.py` treat all region ids as authored (from the world's hand-authored cartography). They have no logic to recognize and validate the procedural region id format.

### Technical Details

**Region id minting:**
- `sidequest/dungeon/seed_bootstrap.py:ENTRANCE_ID = "entrance"` — the entrance region
- `sidequest/dungeon/region_graph/generator.py` — generates expansions with regions named `f"exp{expansion_id:03d}.r{i}"` (e.g., `exp001.r2`)

**Cast staging logic:**
- `sidequest/game/region_cast_staging.py:77` — `region = cartography.regions.get(to_region)` returns `None` for procedural ids
- `sidequest/game/zone_eligibility.py` — contains the shared eligibility predicates that gate content

**Current behavior:**
- When a PC transitions to a procedural region (e.g., `exp001.r5`), `stage_region_cast` is called by `frontier_hook.notify_region_transition`
- Line 77 returns `None` because no authored region exists
- Line 78 logs a warning and returns without staging any cast

## Technical Approach

> **⚠️ CORRECTED 2026-06-22 by Architect (Neo) — see "Architect Decision" below. The
> original draft's "authored NPC cast stages into a procedural room" premise was
> architecturally wrong; the corrected scope is recognition + warning-suppression +
> observability. The original ACs are superseded by the Acceptance Criteria section as
> rewritten here.**

Teach the cast-staging path (and any shared region resolution) to **recognize**
procedural region ids as legitimate runtime regions so the frontier observer stops
misclassifying them as misconfigured cartography ids.

**Approach (decided):** Add **one shared recognizer** `is_procedural_region_id(region_id)`
co-located with the id *minter* so the pattern cannot drift from its producer
(`sidequest/dungeon/seed_bootstrap.py:ENTRANCE_ID = "entrance"` and
`sidequest/dungeon/region_graph/generator.py`'s `f"exp{expansion_id:03d}.r{i}"` →
match `entrance` literal + `^exp\d{3}\.r\d+$`). In
`region_cast_staging.stage_region_cast`, when `cartography.regions.get(to_region)`
misses AND the id is procedural → skip staging **quietly** and emit an OTEL recognition
span (NOT the `unknown_region` warning). When the id misses AND is **not** procedural →
keep the existing `unknown_region` warning (the misconfiguration guard for a
misspelled/narrator-authored WorldStatePatch region id is real and must survive).

**Why not stage cast into the deep:** the procedural deep is *generated, not authored*
(`beneath_sunden/cartography.yaml` says so explicitly), and across all 17
`beneath_sunden/rooms/*.yaml` there are **0 `kind: npc`** bindings — so Seam 2 has
nothing legitimate to stage. Per-room authored content (creatures via
`encounter_creatures`, location features) is already owned by a *separate* pipeline:
curate → materializer → `monster_manual.room_bound` (fixed by 153-26 / #1022). 153-27
must not entangle Seam 2 with that pipeline.

## Architect Decision (2026-06-22, Neo)

**Recognize procedural region ids; suppress the false warning; make it OTEL-observable.
Do NOT extend Seam 2 cast-staging onto the dungeon room-content pipeline.** Authored
NPCs *in* procedural rooms, if ever desired, belong in Pipeline 1 (author a cast /
`kind: npc` block in `rooms/<id>.yaml`, surface via curate) — a separate content-driven
feature + design amendment, **explicitly deferred / out of scope for 153-27**. Full
rationale and the two-pipeline analysis are in the session file's
`## Architect Assessment (design decision)`.

## Scope
- **In scope:** a shared `is_procedural_region_id()` recognizer (entrance + `expNNN.rN`), co-located with the id minter to prevent format drift
- **In scope:** `region_cast_staging` recognizes procedural ids → quiet skip + OTEL recognition span instead of the `unknown_region` warning
- **In scope:** preserve the `unknown_region` warning for genuinely-unknown, non-procedural region ids (misconfiguration guard)
- **In scope:** no-regression for authored-cartography worlds (a real `kind: npc` cartography region still stages its cast)
- **Out of scope:** staging authored NPC cast into procedural rooms (no cast source exists by design; deferred to a Pipeline-1 feature)
- **Out of scope:** changes to dungeon generation, the curate/monster_manual pipeline, or the authored cartography model

## Acceptance Criteria (rewritten 2026-06-22 — supersedes the original draft)
1. A PC transitioning to a procedurally-generated dungeon region (`entrance` or `expNNN.rN`) no longer triggers the `unknown_region` warning.
2. `is_procedural_region_id()` recognizes `entrance` and the `expNNN.rN` shape, and rejects a non-procedural id (e.g. `ropefoot`, `Lilliput-Court`, `exp1.r0` without zero-pad, empty string).
3. A genuinely-unknown, non-procedural region id that is absent from cartography STILL triggers the `unknown_region` warning (misconfiguration guard preserved).
4. Entering a procedural region emits an OTEL span recording the recognition (procedural region → no authored cartography cast, by design), carrying the region id — verifiable on the GM panel per the OTEL Observability Principle.
5. No regression: entering an authored-cartography region that has `kind: npc` entities still stages them into `npc_pool` (Seam 2 behavior unchanged for gulliver/oz-style worlds).
6. Wiring: at least one test drives the real `stage_region_cast` frontier-observer path (not just the predicate in isolation) so the recognition is proven reachable from the production transition path.

---
_Generated by `pf context create story 153-27` from the sprint YAML; Technical Approach + Acceptance Criteria corrected 2026-06-22 by Architect per the design decision recorded in the session file._
