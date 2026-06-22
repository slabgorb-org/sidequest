# Dungeon Affordances — Show the Exits, Move by Them, Let Depth Be Difficulty

**Date:** 2026-06-22
**Author:** Architect (Atlas the Endurer)
**Status:** Approved design (brainstormed with Keith, evidence-backed by 5 parallel investigations + the live span trace `/tmp/sunden_descend.spans.jsonl`). Supersedes the Bug-B framing in `2026-06-22-sunden-crossing-FINDINGS.md` (that doc's "expand the ring" Bug B was a misdiagnosis — confirmed: the ring was materialized; the player just couldn't see the exits). **The actual unblock turned out to be one small fix — the generate-before-narrate race (Pillar A) — which SHIPPED and is live-verified (see Implementation Status below). Pillars B/C/D are the remaining, optional hardening; this is not a "cast of thousands" — it is one landed fix plus a tracked backlog.**
**Repos:** server (engine + telemetry + emit), ui (map affordance). No content changes.

---

## TL;DR

A procedural dungeon crawl must, every room, **show the player where they can go, let them choose, and take them there** — and get more dangerous as they go in. The rooms generate and connect correctly. The player flies blind: no reliable exit affordance, so they grope with "down"/"deeper", and the engine mis-reads that vague intent as a literal `depth_score` maximization and dead-ends them in a room whose forward exits *had not been generated yet when the narrator described it*.

**The fix is affordances, not movement-interpretation.** Generate the room's exits *before* narrating it; deliver them as a guaranteed affordance (prose + clickable map); navigate by the exit set, not by a depth number; and free `depth_score` to do its real and only job — difficulty.

## Why there are "huge gaps after all this work" (the load-bearing framing)

Nothing here is unbuilt. **Every piece works in isolation and fails at the seam:**

| Working piece | Built by | The seam that fails |
|---|---|---|
| Room generation + lookahead + connection (10 rooms in 3 turns) | epic 153 / ADR-106 | Materialize **races** the narrator: forward exits land 7s *after* the prompt is built |
| `depth_score → CrBand → monster CR + big_bad + loot` (deeper = harder, REAL) | cookbook/assemble | Same `depth_score` is *also* used for routing — one signal, two jobs |
| Bearing/kind movement resolution ("go north", "take the stairs") | movement subsystem | Only fires if the router passes the player's words through `exit_descriptor`; the vague "deeper" path routes by depth instead |
| DUNGEON_MAP → MapWidget → Automapper (renders exit lines) | story 153-25 | Map is **display-only** — no click-to-move wire |
| Narrator prompt carries exits + strong "describe the way out" directives | prompt_framework | Delivery is **discretionary** — nothing checks the narrator actually surfaced them |

This is the CLAUDE.md failure mode by name: *Verify Wiring, Not Just Existence / No half-wired features.* Each unit passed its own tests. The integration boundaries were never wired or verified — **and they were invisible** because movement telemetry never reached the forensic save sink until today's Task 2 fix. You could not *see* the seam fail, which is why the same crossing "resisted" 8 attempts. The gaps are integration debt made invisible by a telemetry hole, not missing features.

## What already works — DO NOT REBUILD

- **Generation/connectivity.** `available_exits` at the stuck room was `["entrance","exp002.r1","exp003.r0","exp003.r1"]` — the exits exist and are walkable. (trace)
- **depth→difficulty, end-to-end.** `depth_score → band_for_depth() → CrBand(cr_min,cr_max) → build_wandering_table()` + `roll_big_bad()` + loot rarity. Deeper genuinely spawns higher-CR monsters. (`game/cookbook/assemble.py:35,279`)
- **Movement-by-bearing/kind.** `_resolve` matches bearing (pass 1), ordinal (pass 2), token/kind (pass 3) reliably for a *named* exit. (`agents/subsystems/movement.py:709–777`)
- **Map rendering.** DUNGEON_MAP carries per-room exits; Automapper draws the schematic graph with typed exit lines + fog-of-war. (`map_emit.py:799`, `Automapper.tsx`)
- **Crossing + region-race fixes already landed this session** on `feat/sunden-crossing-land-and-observe`: Task 1 (surface_descent_adjacent crossing), Task 2 (movement→turn_telemetry — the observability fix), Task 3 (deny narrator `/current_region` race). These stand and belong to this design. **Task 4 (the misaimed "expand the ring") is reverted** — the ring was never the problem.

## The defect, precisely (per-turn, from the trace)

- **Turn 1:** entrance had 3 exits; narrator described all 3. Clean. ✅
- **Turn 2:** descended `entrance → exp002.r2` via a chute (greedy depth-jump). `dungeon.materialize` for the destination started **2ms after** `narration.turn`; `frontier.expand` (which creates the forward `exp003.*` exits) landed **7s later**. The narrator's prompt for `exp002.r2` showed only 2 exits (up, south) — *the forward exits did not exist yet*. Narrator correctly wrote a near-dead-end as atmosphere, naming no way onward. ❌ (the race)
- **Turn 3:** "press deeper". Engine now knows 4 exits, but `direction="deeper"` filters to `depth_score > current` (27.02); the forward `exp003.*` rooms score *lower* (Jaquays loop-back, by design), so `_resolve` returns nothing → `movement.unresolved no_candidate_edges` → narrator improvises exits with invented bearings, PC stays put, `dispatch_engagement.movement.mismatch` fires. ❌ (depth-as-router + no affordance)

`depth_score`'s own spec (`region_graph/depth.py`) says it is *"a coarse, approximate player-facing bucket — **never an authoritative coordinate, key, or container.**"* The `deeper` resolver using it as the routing coordinate is the category error.

---

## The design — four pillars, three implementable slices

The pillars map to three plans so **nothing is lost** (P1 first because it is the actual unblock; P2/P3 follow with their own plan→implement cycles, all tracked under this one design).

### Pillar A — Generate the room's exits BEFORE narrating it  *(Plan P1)*

**Problem:** the destination's onward frontier materializes *after* the narrator's prompt is assembled (the 2ms/7s race). The narrator describes a room whose exits don't exist yet.

**Fix:** on arrival into a procedural room, **synchronously materialize the destination's onward frontier** so its full exit set exists at prompt-assembly time — *before* the narrator turn and before the DUNGEON_MAP emit. This is the correctly-aimed version of what Task 4 groped at: the work belongs at **arrival**, not at a failed deeper-resolve. Reinforced by Pillar C's step-wise movement (no greedy depth-jump means the lookahead is never outrun).

**Where:** the movement resolution / room-entry path in `agents/subsystems/movement.py` (`run_movement_dispatch`) and the lookahead/materialize seam (`dungeon/lookahead_worker.py`, `dungeon/materializer.py`). Reuse the existing `_sync_materialize` path (it already does sync materialize-then-move); extend it so arrival guarantees the *onward ring* is committed before the turn proceeds, not just the single approached edge.

**Observability:** emit a span proving exits-existed-at-prompt-time (e.g. `room.exits_ready` with `exit_count` + `pc_region`, asserted to fire *before* `prompt_assembled`). Route it to `turn_telemetry` (the Task-2 mirror covers movement spans).

### Pillar B — Deliver exits as a GUARANTEED affordance  *(Plan P1)*

**Problem:** exit delivery is narrator-discretionary (turn 2 silently omitted them); the structured `LOCATION_DESCRIPTION` channel never fires for procedural rooms and carries no exits field anyway; the only structured exit delivery is the Map.

**Fix (two parts):**
1. **Structured, non-optional exits payload for procedural rooms.** Either add an `exits` field to the location-description emit and make it fire for procedural room ids, OR emit the exits as their own typed payload alongside narration. The player must receive a structured exit list every room, independent of narrator prose.
2. **Enforce prose delivery.** A post-narration check (lie-detector style, like `dispatch_engagement_watcher`) that flags when the engine knew ≥1 exit and the narration surfaced none — emitting a mismatch span. Turns "the narrator should describe the way out" from advisory into observable-and-enforced.

**Where:** `server/websocket_handlers/map_emit.py` (location-description source path for procedural ids + exits field), `protocol/models.py` (`LocationDescriptionPayload.exits` or a new payload), a post-narration exits-hygiene check near `agents/.../dispatch_engagement_watcher.py`.

### Pillar C — Navigate by exits, not by depth  *(Plan P2)*

**Problem:** "in/onward/deeper" routes by `depth_score`; "back" routes by `depth_score`. Vague intent + depth-coupling = dead-ends at a local depth max.

**Fix:**
- Reframe the coarse intent class. **"in / onward / deeper / further / press on"** → prefer **undiscovered** frontier exits (the rooms the lookahead just built ahead of the party), then any non-back exit; bearing/kind/name passes (1–3) still win when the player is specific. **"back / out / retreat"** → toward the entrance by **graph topology** (BFS distance), not `depth_score`. Only fail loud (`no_candidate_edges`) on a genuine dead-end (no exits at all).
- **Remove `depth_score` from `_resolve` entirely** (the `deeper`/`back` passes). Replace the up/down vertical bearing labels (`region_projection.assign_bearings`, currently depth-delta) with an explicit `descends: bool` on the vertical edge. The lookahead/sync sort by `spawn_depth_score` degrades gracefully to `frontier_edge_id`; keep or replace with explored-distance — non-load-bearing.
- **Give `RegionExit` a human-readable `label`** so a narrator-named "the cracked archway" matches in `_resolve` token scoring (today only the slug + kind synonyms are the match surface).

**Where:** `agents/subsystems/movement.py` (`_resolve` passes 4–6 → frontier/topology), `dungeon/region_projection.py` (`RegionExit.label`, `descends` flag, `assign_bearings`), `agents/intent_router.py` (intent vocabulary: the coarse classes + verbatim `exit_descriptor` passthrough fidelity — the router must pass the player's words/bearings, not collapse them to "deeper").

### Pillar D — `depth_score` is the difficulty dial, and only that  *(Plan P3 + already-wired)*

**Problem:** none in the difficulty wiring itself — it's real and complete. The only issue is the routing coupling, removed by Pillar C.

**Fix:** confirm/keep `depth_score → CrBand → monster CR + big_bad + loot` as the sole authoritative job, plus the `level_phrase` flavor label ("you reckon you're four levels down"). After Pillar C, `depth_score` has **zero** routing consumers. Optional P3 polish: surface the difficulty band to the player UI (Sebastien/Jade mechanics-legibility — player-facing only, not GM/OTEL). **Clickable map → click-to-move** also lands here: wire `Automapper`/`DungeonMapRenderer`'s `onRoomClick` to a new UI→server navigate message carrying the exact target region id (bypasses fuzzy matching entirely — the strongest possible affordance).

---

## Scope, sequencing, and the "don't lose the rest" guarantee

One design, three plans, tracked together so P2/P3 are not forgotten after P1:

- **P1 — Affordance core (the unblock):** Pillar A (generate-before-narrate) + Pillar B (guaranteed exit delivery). After P1, a player at the end of the rope is shown the ways on and can act. This is the minimum that un-sticks the live bug.
- **P2 — Navigate by frontier; depth out of routing:** Pillar C. Makes vague "go in" reliable and decouples depth from movement.
- **P3 — Depth-as-difficulty surface + clickable map:** Pillar D polish + click-to-move.

The existing branch `feat/sunden-crossing-land-and-observe` (Tasks 1–3) is the foundation P1 builds on; **revert the misaimed Task 4** as part of P1.

## Implementation Status (2026-06-22)

**Pillar A SHIPPED — and it alone unstuck the player.** On branch `feat/sunden-crossing-land-and-observe`:
- `e86ea589` land the crossing (attempt #8) · `1789005a` movement→`turn_telemetry` (the observability that made all this findable) · `60ad546a` deny the narrator `/current_region` race · `7d60f323` **revert** the misaimed Task-4 ring-expand · `10c627e6` **the fix**: `run_movement_dispatch` awaits `lookahead_handle.drain()` after a resolved move, so the destination's onward ring is committed before the narrator's prompt is built. 3 new unit tests + 13 seam tests green.
- **Live-verified twice** against `scenarios/sunden_descend_trace.yaml`:
  - 3-action repro: turn 3 resolves (was a dead-end), `onward_ring_drained=True`, narrator names exits every turn (incl. the previously-pure-atmosphere turn 2), `/current_region` clobber denied ×3.
  - 14-action expansion run: **7 new sections** (expansion_id 3→9), 8/8 in-dungeon moves drained, 8 regions across 5 generations, **zero `no_candidate_edges`**, working backtrack-and-branch. The one non-resolution was a correct `ambiguous_descriptor` refusal ("a different passage" in a 6-exit room).

**Pillar B (guaranteed structured exit delivery + omission enforcement): NOT built.** The narrator reliably *describes* exits now because Pillar A guarantees they exist at prompt time, but the structured `LOCATION_DESCRIPTION`-adjacent exits payload and the post-narration "exits-omitted" check are still open.

**Pillar C (navigate-by-passage, depth out of routing): NOT built — and sharpened.** The live runs reaffirmed `depth_score` is still in the `deeper`/`back` resolver. New concrete first task: the parallel-exit dedup in `region_projection.py` keys on **destination room** (`collapsed.setdefault(e.to_region_id, e)`), so a corridor *and* a chute to the same room collapse to one — flattening the Jaquays parallelism the generator deliberately builds. The fix is the Pillar-C thesis made concrete: **make the passage (kind+bearing+label) the unit of navigation and dedup, not the destination room.**

**Pillar D (depth-as-difficulty surface + clickable map): NOT built.** Difficulty wiring already real; the player-facing surface and click-to-move remain.

## Testing & observability (every pillar)

- **OTEL-first (CLAUDE.md):** each seam fix emits a span and routes to `turn_telemetry` (Task-2 mirror). The seams were invisible; they must not be again. Key new spans: `room.exits_ready` (before `prompt_assembled`), an exits-omitted mismatch span, a navigate-by-frontier resolution span.
- **Wiring test per suite (CLAUDE.md):** each pillar needs an integration test that drives the real path end-to-end and asserts the span fired / the payload emitted — not source-grep, not unit-only. Pillar A: assert exits exist at prompt time. Pillar B: assert structured exits emitted for a procedural room + mismatch fires on omission. Pillar C: assert "go in" with no specific descriptor resolves to an undiscovered frontier exit (live-shaped fixture: forward neighbor *shallower* than current, the real trace shape).
- **Live re-run:** `scenarios/sunden_descend_trace.yaml` must show, per turn: exits present at prompt time, exits in prose, structured exits emitted, and turn-3 "press deeper" resolving to a real onward room (no `no_candidate_edges`, no `movement.mismatch`).
