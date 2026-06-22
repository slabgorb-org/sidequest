# Sünden Static→Procedural Crossing — FINDINGS (read this first)

**Date:** 2026-06-22
**Status:** Live-verified diagnosis. Supersedes and CORRECTS both
`2026-06-21-location-single-authority-design.md` and
`2026-06-22-static-procedural-crossing-design.md` — **do not trust those two; they
were reasoned from saves and from code, not from a live run, and they were wrong on
the central facts.**
**Repos:** server (engine + telemetry).

---

## ⟳ UPDATE 2026-06-22 (afternoon) — most of the "narrow path forward" LANDED; read this before re-investigating

The TL;DR below was written in the morning **while the server ran attempt #8 on the
unmerged branch `fix/dungeon-seam-reachable-from-surface`, not `--reload`.** Since then
the fixes merged to **develop**, and a fresh afternoon playtest (PC "Puck", session
`2026-06-22-beneath_sunden-926f23f6`, server HEAD `d19afd32` with `--reload`) reconciles
the doc against reality. **Three of the four path-forward items are DONE on develop:**

| Path-forward item | Status now |
|---|---|
| Keep attempt #8's `surface_descent_adjacent` crossing | ✅ **Landed** — PR **#1042** (`43a899ea`, "land the sünden surface→procedural crossing + make movement observable") |
| Bug A — deny narrator `/current_region` write in region-mode | ✅ **Enforced** — `apply_world_patch.py:182-198` returns a recoverable error for `navigation_mode: region` worlds (not just a span) |
| Telemetry gap — route `component="movement"` into `turn_telemetry` | ✅ **Mirrored** by #1042; post-fix saves carry non-zero `mechanical_rows` (Puck = 14, vs 0 on the old AM saves) |
| Bug B — engine runs dry deeper in (`no_candidate_edges` lookahead) | ❓ **Not re-verified.** Puck reached `exp001.r3` (deeper than the AM `exp002.r2` dry-out) without an obvious stall, but the deep turns weren't span-traced this session. Still the one open suspect. |

`#1029` (`feat/region-lateral-mover`, "engine-authoritative lateral region travel") also
merged but is **beside the point for sünden** (it matches named lateral moves, not the
`direction=deeper` seam crossing) — exactly as this doc's "Code/branch state" section
predicted.

### THE TRAP THIS DOC DIDN'T COVER — the room axis is empty BY DESIGN

A fresh investigation burned ~30 min re-deriving "the engine is dead" from a **different**
wrong signal than the AM one. Capture it so nobody does it again:

- **`beneath_sunden/cartography.yaml:17` → `navigation_mode: region`** (deliberate). The
  ADR-106 procedural deep is a **REGION frontier graph** (`discovered_regions` grows
  `entrance → exp001.r0 → exp001.r3 …`; `pc_regions`, `region_transitions` are the ledger).
- The **room axis** (`discovered_rooms`, `room_states`, `current_room`) is the **`room_graph`**
  representation and is **intentionally left empty** under region nav. **153-24's own commit
  ships a passing test: "region-mode regression guard (room axis untouched under region
  nav)."** Reading `discovered_rooms: 0 / current_room: None` as "dungeon is fake" is a
  **misdiagnosis** — and the ping-pong task *"153-24 room axis stays inert after crossing
  onto the procedural graph"* is that misdiagnosis for this world. (153-24 is for room_graph
  worlds.)
- **Likely source of "I'm entering the dungeon… it is NOT" in play:** the **Map tab** (153-25)
  renders the **room** graph, so on a region-mode world it draws **nothing** even while the
  engine generates a real region frontier. That's a UI/representation gap, **not** a dead
  engine. ← the real candidate finding to confirm in the UI.

### How to read sünden dungeon state correctly (so we never re-discover)

1. **Verify the crawl on the REGION axis, not the room axis.** Real descent = `discovered_regions`
   gains `expNNN.rN` frontier nodes + `region_transitions` ledger grows. Empty room axis is expected.
2. **`via=world_patch` in `region_transitions` cannot tell engine from narrator** — both commit
   through `apply_world_patch`. To prove the *engine* moved the PC, read the **Jaeger**
   `movement.resolved` / `resolved_via=surface_descent_adjacent` spans (jsonl), or just note the
   narrator is now *denied* region writes (Bug A fix), so a region advance *is* the engine.
3. **`mechanical_rows`/movement now lands in the DB sink** post-#1042 — but the discriminating
   `resolved_via` detail is still cleanest from the live span dump.
4. **Server freshness:** confirm the uvicorn cwd + HEAD before trusting behavior. `lsof -p <pid> -d cwd`
   → repo path; `git -C <path> log -1` → HEAD. A reboot of a clone behind develop is still stale.

---

## TL;DR (the answer, after a very long investigation)

1. **The crossing WORKS. Attempt #8 — `fix/dungeon-seam-reachable-from-surface`
   (commit `711365e0`), the branch the 2026-06-21 design note told us to DROP — is
   the thing that makes it work.** A live sünden descent crosses `ropefoot → entrance`
   (the winch straight into the generated dungeon) **in one action**, engine-resolved,
   via `resolved_via=surface_descent_adjacent`. Verified 2026-06-22 by a headless
   playtest.
2. **Every prior analysis (including mine, earlier today) wrongly concluded "the engine
   is dark" because the movement subsystem's OTEL spans go to Jaeger but NOT to the
   `turn_telemetry` forensic DB.** The saved record literally omits movement. Reading
   the saves makes a firing engine look dead. This is the real, confirmed observability
   gap — and it is plausibly why this bug has "resisted" 8 attempts: nobody could see
   the engine in the saves.
3. **Two real, narrow bugs remain** (both visible in the live trace, neither requiring
   a re-architecture):
   - **Bug A — the narrator writes region in parallel.** Every descend turn the narrator
     calls the `apply_world_patch` *escape-hatch tool* on `/current_region`; turn 1 it
     tried to send the PC to `exp001.r0` while the engine sent them to `entrance`. The
     engine won this run, but it's a live race (the historical "clobber"/party-split).
   - **Bug B — the engine runs dry deeper in.** At `exp002.r2` the engine reports
     `no_candidate_edges` though the narrator describes four exits → the room graph isn't
     expanded far enough ahead → `dispatch_engagement.movement.mismatch` (narrator
     improvises the move). A lookahead/expansion bug.
4. **The path is narrow, not grand:** keep attempt #8; fix Bug A with a scoped
   region-write denial on the narrator's `apply_world_patch` tool (an *if-statement*,
   not a "sever the narrator" re-architecture); fix Bug B (lookahead); and route movement
   spans into `turn_telemetry` so this is visible in saves. **No single-authority doctrine.
   No touching oz/wonderland/gulliver/orbitals. No `narration_apply` surgery across every
   world.**

---

## What was being investigated

`beneath_sunden` (genre `caverns_and_claudes`, WWN port) descent: a PC on the authored
surface (`ropefoot` → `the_dropmouth`) must cross the **static→procedural boundary** into
the runtime-generated ADR-106 megadungeon (`entrance` → `exp00X.rN`). The
**generation/expansion works fine** — the problem was always the **transit** from the
pre-built cartography into the on-the-fly dungeon. The user's framing, correct throughout:
generation is not the issue; **crossing into the generated dungeon** is.

## The 8-attempt history (all ours, one crossing)

`fbe28cee` (movement subsystem) · `348c1e5a` 59-12 (bind PC onto entrance on descent) ·
`de4f85c8` (region-mode "defer cleanly instead of erroring `no_dungeon_store`" — the
silent fallback that hands the move to the narrator) · `cd4c3ff5` 105-2 (seam registry) ·
`be4f7464` #835 (in-dungeon movement) · `454ac501` 105-3 (reverse seam) ·
`d8396829` 105-2-Pc2 (per-PC seam vocab) · `5fcea151` 153-21 (don't-clobber) ·
**`711365e0` attempt #8 — `seam_route_via_adjacency` / `surface_descent_adjacent`,
THE ONE THAT ACTUALLY CROSSES FROM THE WINCH.** `narration_apply.py` churned 151×.

## THE KEY FINDING — live evidence (2026-06-22)

Ran a focused headless descent: `scenarios/sunden_descend_trace.yaml` (3 actions, no
combat). Server was running attempt #8's code (booted **Sun Jun 21 13:50** on
`fix/dungeon-seam-reachable-from-surface`, **not `--reload`**, so the live behavior is
attempt #8). Span dump: `/tmp/sunden_descend.spans.jsonl` (959 spans). New session:
`2026-06-22-beneath_sunden-597081d5` (session_id **15331**).

Time-ordered crossing spans:

```
turn 1  "I take hold of the rope at the winch-house and climb down into the Deep."
   region.entry_rejected           reason=sub_location_in_region_mode_world  caller=narration_apply.location_update
   intent_router.subsystem         subsystem=movement
   frontier.region_transition      ropefoot → entrance
   movement.resolved               ropefoot → entrance   resolved_via=surface_descent_adjacent  edge_kind=surface_descent   ← ENGINE CROSSES FROM THE WINCH, ONE ACTION
   tool.write.apply_world_patch    path=/current_region  reason="Playtest descends the rope into the Deep via the northeast c…"   ← NARRATOR ALSO WRITES REGION
   frontier.region_transition      ropefoot → exp001.r0   ← narrator's competing target (≠ engine's entrance)
turn 2  "I keep climbing down the rope, descending into the dark."
   intent_router.subsystem         subsystem=movement
   movement.resolved               entrance → exp002.r2  resolved_via=descriptor_fallback_depth_delta  edge_kind=chute
   tool.write.apply_world_patch    path=/current_region  reason="Playtest descends further into the Deep…"
turn 3  "I press deeper into the cavern below."
   intent_router.subsystem         subsystem=movement
   movement.unresolved             reason=no_candidate_edges  from=exp002.r2  direction=deeper   ← ENGINE RUNS DRY
   dispatch_engagement.movement.mismatch                                                          ← lie detector fires
```

DB ledger for session 15331 (the *persisted* truth — engine path won):
```
turn 1  ropefoot → entrance     via=world_patch
turn 2  entrance → exp002.r2    via=world_patch
```
(Note: `via=world_patch` is stamped by `apply_world_patch` and CANNOT distinguish the
engine seam from the narrator tool — both route through it. The Jaeger
`movement.resolved` spans are what prove the engine did it.)

## Why every prior analysis was wrong: the observability gap (CONFIRMED)

- Movement spans (`movement.resolved`, `movement.region_mode`, `movement.unresolved`,
  `room.discovered`) are defined in `sidequest/telemetry/spans/movement.py` with
  `component="movement"` and registered in `SPAN_ROUTES`.
- **They reach Jaeger/OTEL but NOT the `turn_telemetry` Postgres sink.** Confirmed on
  session 15331: Jaeger has `movement.resolved` ×2; `turn_telemetry` has **zero** rows
  with `component='movement'` for that session — and zero across the *entire* table, all
  sessions, ever.
- `magic`/`confrontation`/`location` DO land in `turn_telemetry`, so they use a different
  emit path (publish_event) than movement's `Span.open`. My earlier claim that "movement
  is wired the same way so its absence proves it never ran" was WRONG — they are NOT wired
  the same way for the DB sink.
- **Consequence:** analyzing saves shows the engine as dead when it is firing. The 6
  earlier saves (14492/14593/14754/14759/14773/14812) showed `via=world_patch` /
  `via=narration_apply` and no movement — consistent with BOTH "engine fired but not
  logged to DB" and "narrator did it." The saves cannot tell them apart. Only a live
  Jaeger trace can. **Do not diagnose this from `turn_telemetry` alone.**

## The two real remaining bugs

**Bug A — narrator writes region in parallel (the live clobber).**
The narrator's `apply_world_patch` escape-hatch tool (`sidequest/agents/tools/apply_world_patch.py`)
writes `/current_region` on descend turns. The title-scrape path is *already* fenced for
region-mode worlds (`region.entry_rejected: sub_location_in_region_mode_world` from
`narration_apply.location_update`), so the remaining hole is the TOOL. Turn 1 it targeted
`exp001.r0` while the engine targeted `entrance`; the engine's `pc_region` consensus won,
but it's a race that historically split the party (old session 14812). **Narrow fix:**
deny the `/current_region` (and `/pc_regions`) path in that tool's allowlist for
seam/region-mode worlds. A scoped conditional — NOT a `narration_apply` rewrite.

**Bug B — engine runs dry deeper in (`no_candidate_edges`).**
At `exp002.r2` the engine has no candidate edges though the narrator describes exits
(south/southwest/northeast/up). The dungeon lookahead/expansion (`sidequest/dungeon/`,
`frontier.expand`/`frontier.lookahead`) isn't materializing far enough ahead of the
descent, so the engine stalls and the narrator improvises (the `mismatch`). **Fix:** keep
expansion ahead of the PC so a "deeper" intent always has a real edge.

## The narrow path forward

1. **Keep / merge attempt #8** (`surface_descent_adjacent`). It is the working crossing.
   The 2026-06-21 note's "drop #8" recommendation is **rescinded**. (Its objection was a
   "rotten foundation" argument that the live run disproves — #8 resolves through the
   chokepoint and emits a real span.) Decide: merge `fix/dungeon-seam-reachable-from-surface`,
   or cherry-pick `seam_route_via_adjacency` + the `movement.py` adjacency block onto a
   clean branch off develop.
2. **Bug A:** scoped region-write denial on the `apply_world_patch` tool. If-statement.
3. **Bug B:** lookahead keeps ahead of the descent.
4. **Telemetry gap:** route `component="movement"` spans into `turn_telemetry` (the
   real Piece 3) so the GM panel / saves can see the engine. Model it on how `location`/
   `confrontation` reach the DB sink (publish_event), not on `Span.open` alone.
5. **Scope discipline:** none of this touches oz/wonderland/gulliver or the orbital path.
   No "single authority," no "sever the narrator." The historical over-engineering
   (turning one transit bug into a system-wide doctrine) is the trap; stay narrow.

## Code / branch / PR state (for the next session)

- **Running server (oq-3):** uvicorn pid was 49571, booted **Jun 21 13:50 on
  `fix/dungeon-seam-reachable-from-surface` (attempt #8), NOT --reload.** So the live
  behavior above = attempt #8. The server subrepo working tree is checked out to
  `feat/region-lateral-mover`, but the *process* is still running #8's loaded code.
  To test develop or another branch you must restart the server.
- **`feat/region-lateral-mover`** (server) — my Plan 1 "lateral mover"
  (`_resolve_cartography_lateral`), shipped as **PR #1029 → develop**. It is
  **beside the point** for sünden (the descent is a seam crossing, not a named lateral
  move; and the lateral resolver only matches by name, not on `direction=deeper`). It's
  fine to keep for oz-style named travel, but it does NOT fix the crossing.
- **`fix/dungeon-seam-reachable-from-surface`** (server) — attempt #8. The working
  crossing. NOT merged. The 2026-06-21 note said drop it; that is now reversed.
- **`docs/static-procedural-crossing-design`** (orchestrator) — branch holding the two
  superseded design notes + this findings doc.
- The old 6 sünden saves: 14492/14593/14754/14759/14773/14812. Sessions BEFORE Jun 21
  13:50 predate #8 (narrator-only); sessions after may have run #8 but movement still
  isn't in their DB record (the telemetry gap).

## How to reproduce

```bash
# server must be up (just server) on the branch you want to test (restart to change code)
cd sidequest-server && uv run --with rich --with pillow python3 ../scripts/playtest.py \
  --scenario ../scenarios/sunden_descend_trace.yaml --span-jsonl /tmp/sunden_descend.spans.jsonl --fresh
# then read movement/seam/dispatch spans from the jsonl (Jaeger), NOT from turn_telemetry.
```
Scenario: `scenarios/sunden_descend_trace.yaml`. Read the jsonl by span `name`; the
crossing spans are `movement.resolved`, `movement.unresolved`,
`dispatch_engagement.movement.mismatch`, `tool.write.apply_world_patch`,
`frontier.region_transition`, `intent_router.subsystem`.
