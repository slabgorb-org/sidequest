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
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

Every dungeon-region entry in the beneath_sunden playtest logged:

```
WARNING region_cast_staging zone_eligibility.cast_staged.skip
  reason=unknown_region world='beneath_sunden'
  to_region='entrance' | 'exp001.r0' | 'exp002.r2'
```

The faction/zone content-eligibility layer (epic-157, now archived) does not recognize
procedurally-generated region ids. It keys cast staging on the world's AUTHORED cartography
region ids, and treats every procedural dungeon node id (`entrance`, `expNNN.rN`) as
`unknown_region`. The result: `stage_region_cast` returns early, no authored cast / faction
content is ever staged into a generated room, and the warning is the symptom on every single
move. This is the *cast* (NPC/faction) sibling of the 153-23 creature-population gap — both are
"authored content never reaches the procedural room."

## Status Update (2026-06-22) — re-confirmed live; STILL OPEN, untouched

**Do NOT close this story on the back of the dungeon-affordance / crossing work.** That work
(server PR #1042, squash-merged to `develop` 2026-06-22 — the sünden surface→procedural crossing,
movement→`turn_telemetry` observability, the narrator `/current_region` denial, and the
generate-before-narrate "affordance race" fix) is the **movement/observability layer only**. It
does **not** touch `region_cast_staging` / `zone_eligibility` and satisfies no AC here.

This story's exact symptom was **re-confirmed live and unchanged** on 2026-06-22 (14-turn
`sunden_descend_trace` expansion run, server log `~/.sidequest/logs/sidequest-server.log`) — the
`unknown_region` skip fired on **every region the party entered**:
```
WARNING zone_eligibility.cast_staged.skip reason=unknown_region world='beneath_sunden'
  to_region='entrance' / 'exp002.r2' / 'exp002.r3' / 'exp004.r0' / 'exp005.r4' / 'exp007.r3' / 'exp007.r1'
```
So `stage_region_cast` still hard-returns on every procedural node and no cast is staged into any
generated room — ACs 1–6 all UNMET.

The only thing PR #1042 changed for this story is *helpful, not done*: the party now actually
transits these procedural regions cleanly (movement works) and each transition is observable in
`turn_telemetry`, so the `unknown_region` skip is now trivially reproducible and verifiable on a
real crawl — i.e. this story is **unblocked and easy to test**, but not begun. Keep at `backlog`,
p2. The fix is still the resolver extension described below.

## Root Cause Direction

`region_cast_staging.stage_region_cast` is a frontier observer (registered once at startup) that,
on a real region transition, looks up the entered region in the world's cartography and stages its
authored NPC cast into `snapshot.npc_pool`. The lookup is:

```python
region = cartography.regions.get(to_region)   # region_cast_staging.py:77
if region is None:
    logger.warning("...skip reason=unknown_region world=%r to_region=%r", ...)
    return
```

`cartography.regions` is the AUTHORED cartography dict (`CartographyConfig.regions`, keyed by
authored region id, each carrying `controlled_by`). Procedural dungeon nodes (`entrance`,
`expNNN.rN`) live in the `dungeon_map` / `RegionGraph` (`dungeon/persistence.py`,
`dungeon/region_projection.py`), NOT in authored cartography — so `.get(to_region)` misses and the
skip fires unconditionally for the megadungeon.

The same authored-key assumption runs through the shared predicate:
`zone_eligibility._faction_for_region(cartography, region_id)` →
`cartography.regions.get(region_id).controlled_by`. A procedural id resolves to no faction, so
`active_factions(...)` is `∅` for a dungeon-crawling party. (Note `is_eligible` is permissive on an
empty active set, so creature *filtering* fails toward showing content — but the *cast staging*
seam hard-returns on the `unknown_region` miss, so no cast is staged at all. The two seams behave
differently on the same miss.)

Fix direction (EXTEND the resolver, do not build a new eligibility system): teach the
region→zone resolution to recognize procedural region ids. Likely shape — map a procedural node to
its owning dungeon's faction-group (the megadungeon is conceptually one zone / one faction-group),
or to a default dungeon pool, so:

1. `stage_region_cast` no longer short-circuits on a procedural id — it resolves the procedural
   region to the dungeon's authored cast pool (e.g. the beneath_sunden `creatures.yaml` "nearby"
   NPCs) and stages it, OR honestly stages nothing because the dungeon declares no zoned cast
   (a content gap, logged once, not a per-move warning).
2. `_faction_for_region` / `active_factions` resolve a procedural id to the dungeon's
   faction-group rather than treating it as unowned, so faction-tagged content stays eligible
   inside the dungeon.

beneath_sunden is single-zone (no `controlled_by` on its regions → `world_is_zoned` is `False`),
so the gulliver/oz multi-zone bleed that epic-157 fixed does not apply here — the correct behavior
for an unzoned procedural world is to stage its dungeon cast (or nothing, quietly), never to spam
`unknown_region`. The resolver must distinguish "procedural region of an unzoned dungeon" (fine,
stage the dungeon pool / no-op quietly) from "narrator-invented / misspelled authored region id"
(the real actionable discrepancy the warning was written for).

## Acceptance Criteria

1. **Procedural region ids are recognized.** Entering a procedural dungeon region (`entrance`,
   `expNNN.rN`) no longer logs `zone_eligibility.cast_staged.skip reason=unknown_region`. The
   resolver maps the procedural node to its owning dungeon / faction-group (or a default dungeon
   pool) instead of treating it as unknown.

2. **Dungeon cast stages on entry (or honestly no-ops).** When the world declares a dungeon cast
   pool, entering a procedural region stages that authored cast into `snapshot.npc_pool` (so the
   narrator surfaces the authored "nearby" NPCs rather than inventing walk-ons). When the dungeon
   declares no zoned cast, staging is a clean, quiet no-op — NOT a per-move warning.

3. **Faction eligibility resolves inside the dungeon.** `active_factions(...)` /
   `_faction_for_region(...)` resolve a procedural region to the dungeon's faction-group rather
   than `∅`/unowned, so faction-tagged content does not get spuriously filtered (or spuriously
   admitted) inside generated rooms. For an unzoned world (`world_is_zoned == False`, like
   beneath_sunden) behavior is unchanged-permissive — the fix must not regress the 11 single-zone
   worlds.

4. **The real-discrepancy warning is preserved.** A genuinely unknown region id — a
   narrator-authored or misspelled id that is neither authored cartography NOR a valid procedural
   node — still logs loudly (the actionable case the original `unknown_region` warning was written
   for). The fix narrows the warning to true discrepancies, it does not suppress it.

5. **OTEL / watcher-span AC.** Staging a procedural region's cast emits the existing
   `zone_eligibility.cast_staged` span (`SPAN_ZONE_ELIGIBILITY_CAST_STAGED`) carrying the region +
   staged names, so the GM panel can confirm the engine staged the dungeon cast rather than the
   narrator naming NPCs by luck. The `unknown_region` skip warning no longer fires for valid
   procedural ids (verifiable by absence on a procedural entry).

6. **Wiring / integration-test AC.** A test reachable from the real frontier-observer path drives a
   region transition into a procedural region id (`entrance` / `expNNN.rN`) for a megadungeon world
   through `notify_region_transition` (the production transition seam that fires
   `stage_region_cast`) — not by calling the resolver in isolation — and asserts: (a) no
   `unknown_region` skip for the valid procedural id, (b) the dungeon cast was staged into
   `snapshot.npc_pool` (or a clean no-op for a cast-less dungeon), and (c) the
   `zone_eligibility.cast_staged` span fired when cast was staged. This proves the resolver change
   is live through the real transition path.

## Key Code Areas to Investigate

**The cast-staging observer (the `unknown_region` skip):**
- `sidequest/game/region_cast_staging.py`
  - `stage_region_cast(*, snapshot, pc_name, from_region, to_region)` — line ~44; the
    `cartography.regions.get(to_region)` lookup (line ~77) and the `unknown_region` warning
    (lines ~83–88) are the exact break.
  - `register_cast_staging_observer()` (line ~119) — registers the observer at startup.

**The shared eligibility resolver (authored-key assumption):**
- `sidequest/game/zone_eligibility.py`
  - `cartography_for(snapshot, pack)` (line ~74) — resolves authored cartography.
  - `_faction_for_region(cartography, region_id)` (line ~93) — `cartography.regions.get(...)`;
    returns `None` for a procedural id (the gap).
  - `active_factions(snapshot, pack, *, perspective=None)` (line ~103) — builds the active set
    from `snapshot.region_for()` / `pc_regions`; `∅` for a procedural region.
  - `world_is_zoned(cartography)` (line ~34), `is_eligible(...)` (line ~48) — the permissive
    predicate (note: permissive on `∅`, but cast staging hard-returns instead).

**The transition seam that fires the observer:**
- `sidequest/dungeon/frontier_hook.py::notify_region_transition` (line ~109) — the real per-PC
  region-transition point that dispatches to registered observers (including
  `stage_region_cast`).

**Where procedural region ids come from / what the dungeon pool would be:**
- `sidequest/dungeon/persistence.py::load_map(entrance_id=...)`,
  `sidequest/dungeon/region_projection.py` — the `RegionGraph` that owns `entrance` / `expNNN.rN`.
- `sidequest/dungeon/lookahead_worker.py:69` — `_ENTRANCE_ID = "entrance"`.
- `sidequest/genre/models/world.py` — `Region` (line ~199, `controlled_by` at ~220) and
  `CartographyConfig` (line ~267); confirm whether a dungeon/faction-group hook exists or where a
  procedural→pool mapping should live.

**Spans:**
- `sidequest/telemetry/spans/zone_eligibility.py` — `SPAN_ZONE_ELIGIBILITY_CAST_STAGED`,
  `SPAN_ZONE_ELIGIBILITY_FILTERED`.

**Existing tests:**
- `tests/game/test_region_cast_staging.py` — extend with the procedural-region case driven through
  `notify_region_transition`.

## Technical Notes

- **epic-157 faction/zone (now archived) — design spec:**
  `docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md` (an ADR-059
  amendment). Three rules: (1) reuse the authored key `Region.controlled_by`; (2) runtime is
  permissive, strictness is the validator's (157-7) job — the only exclusion is
  tagged-but-wrong-zone; (3) split-party safe (union of seated PCs' zones). The layer was authored
  for the multi-zone literary-world bleed (gulliver Yahoo on the Lilliput shore); it never
  contemplated procedural region ids, which is the gap this story closes.
- **ADR-059 (Monster Manual):** cast staging is the NPC complement to creature placement — both
  materialize authored content into the snapshot before the narrator runs. 153-23 (creatures) and
  this story (cast/factions) are siblings; the procedural-region recognition fix here parallels the
  `room_id` threading fix there.
- **ADR-106 (runtime procedural Jaquaysed megadungeon):** the dungeon is one procedural region
  graph (`entrance`, `expNNN.rN`) materialized at runtime. Conceptually the whole megadungeon is a
  single zone / faction-group, which is the natural mapping target for the procedural ids. Note its
  **Amendment A Layer 2** degradation (153-26) is a separate, upstream reason authored content can
  fail to reach a generated room — distinct from this eligibility-skip.
- **No silent fallbacks:** the fix must keep failing loud on a genuinely unknown region id (a
  narrator/misspell discrepancy) while ceasing the false-positive `unknown_region` spam on valid
  procedural ids. Distinguish the two cases explicitly — do not blanket-suppress the warning.
- **OTEL principle (CLAUDE.md):** `cast_staged` is the lie-detector that the engine surfaced the
  cast vs. the narrator naming NPCs by luck — so the staging path must emit on success.

## Story Scope

In scope:
- Teach the region→zone / cast-staging resolver to recognize procedural dungeon region ids
  (`entrance`, `expNNN.rN`) and map them to the owning dungeon / faction-group (or default pool).
- Stage the dungeon cast on procedural entry (or quiet no-op), resolve faction eligibility inside
  the dungeon, and preserve the genuinely-unknown-region warning.
- The span + integration ACs proving the change is live through `notify_region_transition`.

Out of scope (reference only):
- Creature/encounter placement into the room (153-23).
- The curate-timeout degradation that drops authored content upstream (153-26).
- Any new eligibility system or validator work (157-7) — extend the existing resolver, do not
  replace it.
