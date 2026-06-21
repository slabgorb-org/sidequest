# Story 153-22 Context

## Title
[DUNGEON-MOVEMENT-RESOLVER-MISSES-EDGES] resolve natural-language exits (deeper, leftmost west passage) to room-graph node edges and dedupe identical-neighbor exit lists

## Metadata
- **Story ID:** 153-22
- **Type:** bug
- **Points:** 5
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep

## Problem Statement

Once a PC is inside the `beneath_sunden` procedural dungeon (ADR-106), natural-language
movement frequently fails to resolve to a graph edge, and the turn drops to free
narration — the "Zork problem" (open NL input against a finite node-id edge set).

Verbatim finding (2026-06-20/21 sweep):

> Standing in `exp002.r2` with available edges
> `['entrance','exp002.r1','exp002.r1','exp002.r1']` (note the triple-listed
> neighbor — three "passages" all converge on `exp002.r1`, possible neighbor-dedup
> glitch). "move deeper into the next chamber" → `movement.unresolved
> reason=ambiguous_descriptor direction=deeper`; "the leftmost of the three west
> passages" → `movement.unresolved reason=no_candidate_edges`. The resolver
> extracts `direction=deeper` and can't bridge fiction-level descriptors to the
> node-id edges. INCONSISTENT: the same "leftmost passage" phrasing DID resolve
> `entrance→exp002.r2` one step earlier, then failed at `exp002.r2` — likely the
> triple-identical `exp002.r1` edge list defeats disambiguation.

Impact: the narrator offers "three passages west, name a bearing" but no bearing
resolves, so the PC is stranded and the dungeon crawl collapses into improvised
prose — the confabulated-crawl failure the movement subsystem exists to prevent.

## Root Cause Direction

Two distinct defects, both fixable by **extending the existing resolver and reusing
the existing graph** — NOT by replacing `RegionGraph` or adding a new navigator.

**(a) Identical-neighbor exit lists defeat disambiguation.** `project_region`
(`region_projection.py:254`) iterates `graph.edges` and emits ONE `RegionExit`
**per edge**; if three distinct edges connect `exp002.r2 → exp002.r1`, the exit
list triple-lists `exp002.r1`. Worse, `assign_bearings` (`region_projection.py:147`)
keys the `bearings` dict by `to_region_id`, so three edges to the same neighbor
collapse to ONE dict key and CANNOT receive three distinct bearings — the
"north passage / east passage / west passage" distinctness the bearing system
exists to create is impossible when all three edges land on the same node id. The
`neighbors()`/`degree()` methods (`region_graph/model.py:109,120`) similarly count
per-edge. The fix needs label-distinct identity for parallel edges (e.g. carry the
edge's own kind/bearing/index into the exit so three parallel passages are
"the west passage", "the northwest passage", etc.) OR a materializer-side
guarantee that parallel multi-edges between the same node pair are not produced
(dedup), so the player's "leftmost / west passage" descriptor can pick exactly one.

**(b) NL descriptors aren't bridged to graph edges.** In
`movement.py::_resolve`, a `direction="deeper"` with the FLAVOR descriptor "into
the next chamber" goes through the descriptor token-overlap path first. The
descriptor-fallback already exists for `deeper`/`back`/`toward_exit` when the
descriptor matches nothing (movement.py ~lines 568-591), but when the candidate
list has tied-score parallel edges the `deeper` resolution still returns
`ambiguous_descriptor` / `no_candidate_edges` because the depth-delta tie-break
(movement.py ~lines 599-618) can't separate three edges to the SAME node (same
depth_score, same id). Positional/ordinal descriptors ("leftmost", "the middle
one", "first passage") have no bridge at all — `requested_bearing` only knows
cardinal/vertical words, and `_KIND_SYNONYMS` only knows kind tokens. The fix
extends the resolver with an ordinal/positional descriptor bridge (and, once (a)
gives parallel edges distinct bearings, "leftmost west passage" resolves through
the existing `requested_bearing` path).

## Acceptance Criteria

1. **Parallel edges are label-distinct (or deduped).** Standing in a region with
   three edges to the same neighbor (`exp002.r1`), the projected exits no longer
   present three indistinguishable `exp002.r1` entries: either each parallel exit
   carries a distinct player-facing bearing/label (so `assign_bearings` no longer
   collapses them on `to_region_id`), or the graph/materializer guarantees a single
   edge per node pair. A career-GM-visible "name a bearing" prompt must list
   distinguishable ways.

2. **`deeper` resolves through parallel edges.** "move deeper into the next
   chamber" from `exp002.r2` resolves to a single concrete neighbor and advances
   the PC (no `ambiguous_descriptor`, no `no_candidate_edges`), with the flavor
   descriptor "into the next chamber" not vetoing the coarse `deeper` direction
   (extend the existing descriptor-fallback so a tie among parallel edges to the
   same node resolves deterministically rather than refusing).

3. **Ordinal / positional descriptors bridge to edges.** "the leftmost of the
   three west passages" (and "the first/second/middle passage") resolves to a
   single edge when the exits are distinguishable, via an ordinal/positional
   descriptor bridge layered onto the existing `requested_bearing` +
   `_KIND_SYNONYMS` matching — not a new resolver subsystem.

4. **Consistency restored.** The same descriptor phrasing that resolved
   `entrance→exp002.r2` one step earlier resolves at `exp002.r2` too; the
   regression was the identical-neighbor edge list, and AC-1 removes it.

5. **Genuine ambiguity still fails loud.** When two genuinely distinct neighbors
   tie under a descriptor, the resolver still returns `ambiguous_descriptor` and
   asks "which way?" (No Silent Fallbacks) — the fix must not paper over real
   ambiguity, only resolve the false ambiguity created by identical-neighbor
   lists.

6. **OTEL / watcher spans (every subsystem decision emits a span).** A resolved
   move emits `movement.resolved` (`movement_resolved_span`,
   `sidequest/telemetry/spans/movement.py`) carrying `resolved_via` (e.g.
   `descriptor_fallback_*`, an ordinal-bridge tag, or `bearing`), `edge_kind`,
   and `candidate_exits`; a still-unresolved move emits `movement.unresolved`
   (`movement_unresolved_span`) with the precise `reason`. The GM panel can see
   the resolver engaged and how it disambiguated, versus the narrator improvising
   the crawl.

7. **Wiring / integration test proves reachability from a real play path.** Add
   behavior tests in `tests/agents/subsystems/test_movement_dispatch.py` that
   build a graph with three parallel edges to one neighbor, fire
   `run_movement_dispatch` (the real production dispatch entrypoint) for
   `direction="deeper"` and for an ordinal descriptor, and assert the PC's
   `pc_regions` patch advanced + the `movement.resolved` span fired. Drive the
   resolver through `run_movement_dispatch`, not `_resolve` in isolation. No
   source-text grep assertions (CLAUDE.md "No Source-Text Wiring Tests").

## Key Code Areas to Investigate

**The resolver (defect (b) — descriptor→edge bridging):**
- `sidequest/agents/subsystems/movement.py::run_movement_dispatch` (line 134) —
  extracts `direction` / `exit_descriptor` from `dispatch.params` (lines 152-153);
  filters hidden exits and builds `candidates` (~lines 396-414); emits
  `no_candidate_edges` (~lines 404-414, 440-450) and `ambiguous_descriptor`
  (~lines 427-438) via `_unresolved`.
- `sidequest/agents/subsystems/movement.py::_resolve` (line 527) — the §Q1
  deterministic resolution: bearing match (`requested_bearing`, ~lines 550-554),
  descriptor token-overlap (`_tokens` + `_KIND_SYNONYMS`, ~lines 556-596) with the
  existing flavor-descriptor fallback for `deeper`/`back`/`toward_exit` (~lines
  568-591), `direction="deeper"` depth-delta (~lines 599-618), `back` (~lines
  621-641), `toward_exit` BFS (~lines 643-659). **The ordinal/positional bridge
  and the parallel-edge tie resolution land here.**
- `sidequest/agents/subsystems/movement.py::_KIND_SYNONYMS` (line 67) +
  `_DEEPER_KIND_RANK` (line 77) + `_way_phrase` (line 96) — the descriptor
  vocabulary and player-facing exit phrasing to extend.

**The projection / graph (defect (a) — identical-neighbor lists):**
- `sidequest/dungeon/region_projection.py::project_region` (line 254) — builds the
  `exits` list one `RegionExit` per `graph.edge` (~lines 287-303). **Triple-lists
  a node when three edges connect to it.**
- `sidequest/dungeon/region_projection.py::assign_bearings` (line 147) — keys the
  `bearings` dict by `to_region_id` (~lines 175-208), so parallel edges to one
  node collapse to a single bearing key. **This is why three passages can't get
  three bearings.**
- `sidequest/dungeon/region_projection.py::requested_bearing` (line 213) +
  `RegionExit` dataclass (line 117, `bearing` field line 132) — the bearing-match
  surface the ordinal bridge complements.
- `sidequest/dungeon/region_graph/model.py::RegionGraph` (line 91) — `neighbors`
  (line 109), `degree` (line 120), `bfs_dist` (line 125), `add_edge` (line 101,
  rejects self-loops but ALLOWS parallel multi-edges between the same pair).
  **Confirm whether parallel edges are legitimate map geometry (Jaquaysed loops)
  or a materializer dedup bug** — `sidequest/dungeon/` materializer + lookahead
  worker that emit `RegionEdge`s.

**OTEL spans:**
- `sidequest/telemetry/spans/movement.py` — `movement_resolved_span` (line 128),
  `movement_unresolved_span` (line 155), `movement_region_mode_span` (line 182).

**Existing tests to extend:**
- `tests/agents/subsystems/test_movement_dispatch.py` — `_dispatch` helper +
  `capture_spans`; `test_deeper_picks_strictly_greater_depth_kind_tiebreak`,
  `test_exit_descriptor_token_overlap`, `test_ambiguous_descriptor_fail_loud`,
  `test_no_candidate_edges_fail_loud`, `test_resolution_in_neighbors`. Add the
  parallel-edge + ordinal-descriptor cases here.
- `tests/dungeon/test_region_bearings.py`,
  `tests/dungeon/test_region_projection_wiring.py` — bearing-assignment and
  projection coverage for the parallel-edge labeling change.

## Technical Notes

- **ADR-106** (Runtime Procedural Jaquaysed Megadungeon): the Jaquaysed design
  intentionally creates loops and multiple paths between areas, so parallel edges
  between two regions MAY be legitimate geometry — the fix must make them
  *distinguishable*, and only dedup if a given pair-of-edges is a true materializer
  duplicate. Confirm intent against the materializer before choosing dedup vs.
  distinct-label.
- **ADR-055** (Room Graph Navigation): movement resolves against the live
  `RegionGraph`; `RegionExit.exits` is the authoritative move vocabulary. The
  bearing system (`assign_bearings`) exists specifically to kill the "the corridor
  ahead" N-way tie — but it currently assumes one edge per neighbor.
- **ADR-113** (Intent Router): the router passes the player's words through
  verbatim as `direction` + `exit_descriptor`; the resolver is the single
  movement-resolution mechanism (one-mechanism rule). The descriptor is often
  flavor, not a way-name — the existing fallback handles flavor for coarse
  directions; this story extends it to handle positional descriptors and parallel
  edges.
- **OTEL Observability Principle** (CLAUDE.md): the resolver already spans every
  decision (`movement.resolved` / `movement.unresolved` with `resolved_via` /
  `reason`); the new ordinal-bridge and parallel-edge resolution must keep emitting
  these so the GM panel sees the disambiguation, not an improvised crawl.
- **Reuse-first / Don't Reinvent** (CLAUDE.md): extend `_resolve` and the bearing
  assignment; reuse `graph.bfs_dist`, `graph.neighbors`, `requested_bearing`,
  `_KIND_SYNONYMS`. Do NOT add a parallel navigator or replace `RegionGraph`.

## Story Scope

**In scope:**
- Making parallel edges to the same neighbor distinguishable (distinct
  bearing/label) OR deduped at the materializer if they are true duplicates —
  whichever ADR-106 intent dictates — so disambiguation is possible.
- Extending `movement.py::_resolve` so `direction="deeper"` resolves through
  parallel edges and ordinal/positional descriptors ("leftmost", "first",
  "middle") bridge to a single edge.
- Preserving fail-loud on genuine ambiguity and on `no_dungeon_store` /
  `no_pc_region`.
- OTEL span coverage + behavior/wiring tests through `run_movement_dispatch`.

**Out of scope:**
- The surface→deep seam-crossing latch (descending the rope into the dungeon) —
  that is Story 153-21 (`narration_apply.py` precedence fix).
- Region-mode (cartography) movement, which defers to the narration_apply
  heading→region path (`_defer_region_mode`).
- Replacing `RegionGraph`, the BFS, or the bearing-assignment algorithm wholesale
  — this is an extension of the existing resolver/graph, not a rewrite.
- A content-authored per-world exit vocabulary (the documented Jade follow-up
  noted in `movement.py::_KIND_SYNONYMS`).

---
_Enriched from the 2026-06-20/21 /sq-playtest finding; code-area claims verified
against `sidequest-server` source on 2026-06-21._
