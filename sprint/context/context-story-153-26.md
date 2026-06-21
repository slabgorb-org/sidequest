# Story 153-26 Context

## Title
[DUNGEON-CURATE-TIMEOUT] keep dungeon room curate within the 25s wall-clock cap (precurate/stream) so authored room content and encounters are not dropped to the degraded deterministic manifest

## Metadata
- **Story ID:** 153-26
- **Type:** bug
- **Points:** 3
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

During the beneath_sunden playtest the server log spammed:

```
ERROR dungeon.materializer dungeon curate degraded region=exp001.r2..r5
  failure_kind=deadline elapsed_ms=30337
  reason=curate exceeded the 25.0s wall-clock cap — shipping the deterministic
  assemble_region manifest stamped curated=false (ADR-106 Amendment A Layer 2)
```

The consequence is not cosmetic. When curate degrades, the authored entrance room
(`rooms/entrance.yaml`: the rope's-end ring bolt, the bone-drifts, the authored `gnaw_swarm`
"easy first fight on purpose," the three unmarked passages) does NOT surface. The narrator,
handed a generic deterministic manifest, improvises "The Drowned Cavern" instead. The
degradation drops authored ENCOUNTERS and SET-PIECES, not just flavor prose — which is the
upstream cause that starves the room-population path (153-23) of anything authored to place.

This is a performance failure (the LLM curate enrichment pass blows the 25.0s cap) compounded by
a correctness failure (the degraded path discards authored content rather than preserving it).

## Root Cause Direction

The curate stage is an `await`-ed, one-shot SDK `complete_with_tools` enrichment pass over each
region's assembled manifest (the only async stage in the `design → fill → curate → attach →
commit` pipeline). It runs under a hard wall-clock cap, `CURATE_DEADLINE_S = 25.0`
(`materializer.py:191`), wrapping `asyncio.timeout(CURATE_DEADLINE_S)` around at most 2 attempts
(`materializer.py:1251`). On timeout it sets `degrade_kind = "deadline"` and falls to **Layer 2**:
`_degrade_region(...)` for every region, which CR→Edge-translates the deterministic
`assemble_region` wandering table and stamps `curated=false`.

Two distinct things go wrong:

1. **The cap is blown** (perf). The elapsed was 30337ms against a 25000ms cap. A full
   expansion (`exp001.r2..r5` = several regions) is curated in a single bounded prompt
   (`_build_curation_prompt`), so the deadline scales with the expansion size while the cap is
   fixed. Options to EXTEND (not replace the ladder):
   - **Pre-curate ahead of arrival** — the look-ahead worker
     (`dungeon/lookahead_worker.py`, frontier observer) already materializes the frontier in the
     background; move/keep curate off the player's blocking turn so a fully-curated region is
     ready before the PC crosses into it.
   - **Stream / chunk** — curate per-region instead of one whole-expansion prompt, so a single
     slow region doesn't time out the whole band, and partial results are kept.
   - **Raise or stage the cap** — the cap is module-level and injectable; a more honest budget
     (or a per-region rather than per-expansion budget) may simply be correct.

2. **Degradation discards authored content** (correctness). `_degrade_region` /
   `_creatures_from_manifest` only translate the procedurally-assembled `manifest.wandering_table`
   and `big_bad`. They never consult the world's authored `rooms/<id>.yaml`
   (`encounter_creatures`, `entities`). So when `entrance` degrades, its authored `gnaw_swarm`
   binding and ring-bolt/bone-drift set-pieces are simply absent from what ships. The hard
   constraint for this story: **even when curate degrades, authored room content must still
   surface.** Degradation may drop *procedural enrichment* quality; it must NOT silently drop
   *authored set-pieces*. The authored `encounter_creatures` binding is resolved from the room
   YAML by `room_creature_binding.resolve_room_creatures` (a deterministic, LLM-free read) — that
   path is independent of curate and should be honored on the degraded path too.

Reuse-first: the `assemble_region` manifest, the `_degrade_region` Layer-2 ladder, and the
authored-binding resolver all exist. The fix is to (a) stop blowing the cap by moving/chunking the
work that already exists, and (b) make the degraded manifest still carry the deterministic authored
`encounter_creatures` + entities — not to build a new curate engine.

## Acceptance Criteria

1. **Curate stays within budget for a real expansion.** A representative beneath_sunden expansion
   (multi-region band, e.g. `exp001.r2..r5`) completes curate within its wall-clock budget under
   normal LLM latency, rather than timing out and degrading. Achieve this by pre-curating ahead of
   arrival, per-region chunking, and/or an honest (per-region) budget — extending the existing
   pipeline, not replacing it.

2. **Authored room content survives degradation.** When curate DOES degrade (Layer 2), the shipped
   region still surfaces the authored room's `encounter_creatures` (e.g. `entrance` → `gnaw_swarm`)
   and its authored `entities` (ring bolt, bone-drifts). The deterministic authored-binding read
   (`resolve_room_creatures`) is independent of the LLM curate pass and must be honored on the
   degraded path. Degradation may drop procedural enrichment quality; it must not drop authored
   set-pieces.

3. **No silent fallback.** The degraded path remains LOUD — `curated=false`, the per-region
   uncurated marker, and the ERROR log are retained (per the No Silent Fallbacks rule and ADR-106
   Amendment A). This story does not paper over degradation; it reduces how often it fires and
   ensures it stops eating authored content when it does.

4. **OTEL / watcher-span AC.** The existing `dungeon.curate.degraded` span continues to fire on a
   real degrade carrying `failure_kind`, `elapsed_ms`, `attempts`, and the region ids. ADDITIONALLY,
   when the degraded path preserves authored content, that is observable — e.g. the
   `monster_manual.room_bound` span still fires for the authored `gnaw_swarm` on a degraded
   `entrance`, so the GM panel can confirm authored content survived the degrade rather than
   trusting the narrator. A degrade that silently drops authored content must be detectable by
   span absence.

5. **Wiring / integration-test AC.** A test reachable from the real materialize path forces a
   curate timeout (the module-level `CURATE_DEADLINE_S` is injectable — set it tiny, the documented
   test seam) on a region that has an authored room binding, drives the degrade, and asserts:
   (a) the region still ships the authored `encounter_creatures` creature, and (b) the
   `dungeon.curate.degraded` span fired AND the authored-content-preserved span (e.g.
   `monster_manual.room_bound`) fired. This proves authored content survives degradation through
   the real pipeline, not in an isolated unit of `_degrade_region`.

## Key Code Areas to Investigate

**The curate stage + deadline + degrade ladder:**
- `sidequest/dungeon/materializer.py`
  - `CURATE_DEADLINE_S: float = 25.0` (line ~191) — module-level, injectable (tests set it tiny).
  - `_stage_curate(...)` (line ~1048) — the only `await`-ed stage; assembles per region, runs the
    one-shot SDK pass under `asyncio.timeout(CURATE_DEADLINE_S)` (line ~1251), 2 attempts.
  - `_degrade_region(...)` (line ~1021) — Layer-2 LOUD degrade; emits `dungeon.curate.degraded`.
  - `_creatures_from_manifest(...)` (line ~954) — translates the deterministic manifest only;
    DOES NOT read authored `rooms/*.yaml`. The correctness gap lives here / at its callers.
  - `_build_curation_prompt(...)` (line ~879) — one prompt for the WHOLE expansion (the
    per-expansion-vs-per-region budget question).
  - `CURATE_DEADLINE_S` Amendment-A commentary at lines ~179–192 and the degrade docstring at
    ~957–966.

**Pre-curate / ahead-of-arrival seam:**
- `sidequest/dungeon/lookahead_worker.py` — the frontier observer that materializes the band in
  the background (`_ENTRANCE_ID`, `load_map`); the natural home for moving curate off the blocking
  turn.
- `sidequest/dungeon/frontier_hook.py` — `notify_region_transition` / `register_frontier_observer`;
  the producer seam that fires on a real region transition.

**The authored-binding read (degrade must honor this):**
- `sidequest/server/dispatch/room_creature_binding.py::resolve_room_creatures` — deterministic,
  LLM-free read of `rooms/<id>.yaml` `encounter_creatures`; independent of curate.

**Spans:**
- `sidequest/telemetry/spans/dungeon_materialize.py` — `dungeon_curate_degraded_span`,
  `dungeon_curate_parse_failed_span`, `dungeon_materialize_curate_span`,
  `frontier_region_transition_span`.
- `sidequest/telemetry/spans/monster_manual.py` — `SPAN_MONSTER_MANUAL_ROOM_BOUND` (authored
  content survived the degrade).

**Authored content the degrade currently drops:**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml`.

**Existing tests:**
- `tests/dungeon/test_materializer.py`, `tests/dungeon/test_92_2_scratch_curate_local.py`,
  `tests/dungeon/test_materializer_room_yaml.py` — curate/degrade coverage to extend.

## Technical Notes

- **ADR-106 Amendment A (story 50-26) — Layer 0/1/2:** Layer 0 = `max_tokens=16384`; Layer 1 = one
  bounded whole-call retry (exactly 2 attempts) under `CURATE_DEADLINE_S`; Layer 2 = LOUD
  degrade-to-uncurated, shipping the deterministic `assemble_region` manifest stamped
  `curated=false` with a per-region marker, an ERROR log, and a routed `dungeon.curate.degraded`
  span. The turn proceeds (no table freeze). Two retained `CurationError` carve-outs (NOT degraded):
  (i) the assembled manifest itself invalid, (ii) a curated row missing `cr`. This story must
  preserve all of that — it extends Layer 2 to also honor authored content, and reduces how often
  the deadline fires; it does not relax the loudness.
- **ADR-106 (runtime procedural Jaquaysed megadungeon):** the design → fill → curate → attach →
  commit pipeline; only curate awaits. The narrator backend for curate is `claude -p` (per the
  server CLAUDE.md note: "claude -p still serves some non-narrator jobs, e.g. the dungeon curate
  stage"), so its latency is the variable that blows the cap.
- **ADR-059 (Monster Manual):** the authored `encounter_creatures` binding is server-side authored
  truth resolved deterministically (no LLM) — which is exactly why the degraded path CAN preserve
  it cheaply. The degrade dropping it is the bug; honoring it is reuse, not new work.
- **epic-157 faction/zone (now archived):** orthogonal here, but note degradation also interacts
  with cast staging (153-27) — both are "authored content didn't reach the generated room."
- **OTEL principle (CLAUDE.md):** "No silent fallbacks" + "the GM panel is the lie detector." A
  degrade that silently drops authored set-pieces is precisely the failure the span discipline must
  catch — hence the span-presence AC.

## Story Scope

In scope:
- Keep curate within budget (pre-curate ahead of arrival, per-region chunk, and/or honest budget).
- Make the Layer-2 degraded path still surface authored `encounter_creatures` + entities.
- The span + integration ACs proving authored content survives a forced degrade through the real
  pipeline.

Out of scope (reference only):
- The room-population wiring that places the surviving creature into game state (153-23).
- Procedural-region zone/cast eligibility (153-27).
- Any rewrite of the curate engine or the Amendment-A loudness contract — extend the ladder, do
  not replace it.
