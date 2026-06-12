# Surface→Deep Crossing — Story 105-2 Seam-Design Note

**Date:** 2026-06-12 (rev 2.1 — §8 amendment: drift-strip resolves the §4/§7 contradiction found during implementation; rev 2 — seam registry promoted to v1 scope per boss direction)
**Author:** Architect (Emmanuel Goldstein)
**Story:** 105-2 — Deterministic surface→deep seam crossing (epic 105, Beneath Sünden)
**Status:** Approved design, pre-implementation
**Repos:** server, content *(scope amendment — see §6)*

## 1. Problem (from the 2026-06-12 live dive)

The ADR-106 procedural Deep is fully materialized (6 regions, 12 edges, the_siphon
setpiece) but unreachable in live play. On turn 3 of the dive, the most explicit
descent possible ("down the rope into the dark tunnels … until my boots find rock")
produced **no movement dispatch at all**; the narrator papered the gap with a
`location` patch inventing "The Dropmouth — The Deep" as a surface sub-location —
a confabulated dungeon with zero mechanical backing.

## 2. Root-cause analysis (FOUR compounding defects)

1. **The 59-12 handoff is dead code for beneath_sunden.** Verified by git
   archaeology: 59-12 (`348c1e5a`, 2026-05-28) landed the surface→deep handoff at
   `movement.py:201-269`; five days later `de4f85c8` (2026-06-02) added the
   region-mode early-return *above it* to silence oz's spurious `no_dungeon_store`
   errors. beneath_sunden is `navigation_mode: region` by deliberate design
   (cartography.yaml header), so **every movement dispatch exits at
   `region_mode_deferred` before reaching the handoff** — even a perfectly
   classified `movement{deeper}` cannot cross today. This is why turn 2's
   correctly-fired movement resolved to the adjacent surface region via the
   narration_apply heading path instead of descending.

2. **The router is blind to the seam.** The movement classification prompt
   (`intent_router.py:162-169`) defines movement as relocation "between dungeon
   regions" and the router's state summary never mentions that `the_dropmouth`'s
   one onward exit is a descent named "Down the Rope" (`cartography.yaml routes[]`,
   `to_id: deep_descent`). The router was asked to recognize a descent it was
   never told existed.

3. **There is no deterministic backstop.** When the router misses,
   `narration_apply.location_update` accepts the narrator's scene re-title; the
   90-6 guard (`region.entry_skipped_sub_location`) prevents graph pollution but
   still applies the patch as a cosmetic re-title — the confabulated deep gets
   *narrated* even though it is mechanically nothing.

4. **The far side of the crossing is empty.** The materializer reserves
   expansion 0 for the entrance and refuses to compose content for it
   (`materializer.py:588`; `_stage_emit_room_yamls` runs only for
   `expansion_id >= 1`). Every expansion region gets a cookbook-composed
   `rooms/expNNN.rN.yaml`; the entrance — the first procedural region every
   player lands in — is a bare `RegionNode(id="entrance", theme=…)`. There was
   nothing concrete to land in, which is why the narrator invented something.

## 3. Design decision

**Static→procedural seams are a first-class, registered concept.** Crossing from
authored space into generated space is the *point* of the game — the megadungeon
(ADR-106), and after it the orbital jump scale (ADR-141) and frontier expansion,
all hang off this same boundary. The crossing machinery is therefore a **seam
registry** (mirroring the ruleset registry, ADR-117, and the magic-plugin
import-time registry, ADR-126): a cartography route whose `to_id` names a
registered seam kind is a seam route; the registry maps the kind to a resolver
that performs the real crossing or raises. The generic parts — recognition, the
narration guard, the span contract — are seam-kind-agnostic. **One resolver ships
in this story** (`deep_descent`); future kinds register, they don't re-architect.

And the first procedural region is a **real, authored room** ("Under the Rope") —
landing must be concrete, renderable, and immediately playable.

Rejected alternatives:

- **Lexical descent floor** (keyword sniffer beside the Haiku router) — a second
  intent router by another name; re-introduces text classification as the gate.
- **beneath_sunden-only patch** (literal `deep_descent ==` checks in movement.py)
  — rejected per boss direction: the next world that gens new stuff at an
  intersection would re-discover and re-solve this entire bug class. The seam is
  the product surface, not an edge case.
- **Reject-and-reprompt-only guard** — strands a player who expressed descent
  perfectly well; the narrator's location patch *is* a relocation signal and is
  honored mechanically, not bounced.

## 4. The five pieces

### Piece 0 — Seam registry (server, new module `sidequest/game/seams/`)

- `base.py` — `SeamResolver` protocol; `SeamCrossingResult(to_region)`;
  `SeamCrossingError(reason, surface)` (recoverable, fail-loud: reason feeds the
  span, surface is the honest player-facing line); `UnknownSeamKindError`.
- `registry.py` — explicit dict `{kind: resolver}` exactly like
  `ruleset/registry.py`; `get_seam_resolver(kind)` fails loud on unknown;
  `seam_route_for(cartography, region_id) -> Route | None` — the recognition
  helper: the first route with `from_id == region_id` whose `to_id` is a
  registered kind.
- `deep_descent.py` — the one shipped resolver: the 59-12 bind logic
  **extracted** from movement.py (load graph from `dungeon_store`, verify
  `entrance_id in graph.nodes` else raise `SeamCrossingError("no_dungeon_entrance",…)`,
  apply `WorldStatePatch(pc_region={player: entrance_id})` — which fires the
  frontier transition — and emit `movement_resolved_span` with
  `seam_kind="deep_descent"` and caller-supplied `resolved_via`).
- Extension contract (documented, NOT stubbed): ADR-141 orbital jump and ADR-106
  frontier expansion register here when their stories land.

### Piece 1 — "Under the Rope": author the entrance room (content repo)

`genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/entrance.yaml`, in
the exact `write_room_yaml` shape (`room_type`/`name`/`description`/`entities`)
that `room_file_loader.load_room_payload` consumes and `map_emit` serves on
room-enter. Name: "Under the Rope." Content: the rope's end, bones of the
unlucky, and an easy first encounter — the **Gnaw-Swarm** (the bestiary's
rat-tier shallow-band creature). The materializer's freeze invariant
(`FileExistsError`, production `overwrite=False`) protects the authored file.
Doctrine: every world rooting a procedural dungeon SHOULD author its entrance
room — the threshold scene is a diamond.

### Piece 2 — Tell the router what the exits are (server)

In `_build_state_summary` (`intent_router_pass.py:221`): when the PC's current
region is a cartography region, append a compact `current_region_exits`
projection — adjacency neighbors plus seam routes, each
`{name, kind: "adjacent"|"descent_seam"}`. "Down the rope into the dark tunnels"
classifies trivially when the context literally names an exit *Down the Rope*.
Follows the 59-27 precedent (`confrontation_types` + `intent_verbs` — the
lexical bridge pattern), with a paired vocabulary span.

### Piece 3 — movement.py consumes the registry (server)

- **The hybrid fix (primary):** in the region-mode early-return block, before
  deferring — if `seam_route_for(cart, from_region)` returns a seam route AND
  `direction != "back"`, dispatch the registered resolver
  (`resolved_via="surface_descent"`). A region-mode world *with* a seam route
  and a live `dungeon_store` is the hybrid case the 2026-06-02 fix didn't
  anticipate. Non-seam region-mode worlds (oz, wonderland, the_circuit) hit the
  existing defer exactly as before.
- **Sole-exit relaxation:** from the seam region, `deeper`, `toward_exit`, and
  exit-descriptor matches all cross; `back` still resolves to surface adjacency
  via the existing paths.
- **The old 59-12 block** (`movement.py:214-269`, room-graph surface case)
  delegates to the same resolver — one crossing implementation, two entry doors.

### Piece 4 — The narration guard crosses, it doesn't just reject (server)

In `_apply_narration_result_to_snapshot`'s region-mode branch
(`narration_apply.py:3848`), ahead of the 90-6 `entry_skipped_sub_location`
conclusion: while THIS PC's region owns a seam route and the narrated heading
does not resolve to known cartography, the heading **is the relocation signal
the router missed**:

1. **Recover:** call the registered resolver
   (`resolved_via="narration_seam_recovery"`). Re-anchor the applied location to
   the authored entrance room's `name` ("Under the Rope") via
   `load_room_payload`, discarding the confabulated heading.
2. **Or fail loud:** `SeamCrossingError` → `region_entry_rejected_span`
   (`reason="seam_crossing_unresolvable"`) + honest surface; the location patch
   is NOT applied; `pc_region` unchanged.

Plumbing: `_apply_narration_result_to_snapshot` gains a
`lookahead_handle: LookaheadWorkerHandle | None = None` kwarg (carries
`persistence` = the DungeonStore + `genre_slug`/`world_slug`); the single
production call site (`websocket_session_handler.py:1101` via `_apply_kwargs`
at ~1080) threads `sd.lookahead_handle`.

**90-6 non-regression:** the recovery fires only when the region owns a seam
route AND the heading is unresolvable to cartography. Genuine POI re-titles in
seam-less region-mode worlds hit `entry_skipped_sub_location` unchanged; real
region changes still abandon anchored confrontations; same-region drift still
does not.

## 5. OTEL (the acceptance gate)

| Signal | Source | New/existing |
|---|---|---|
| `movement.resolved` `resolved_via="surface_descent"` `seam_kind="deep_descent"` | resolver via movement.py | existing span, **new `seam_kind` attr** |
| `movement.resolved` `resolved_via="narration_seam_recovery"` `seam_kind=…` | resolver via narration guard | **new `resolved_via` value** |
| `frontier.region_transition` surface→`entrance` | per-PC patch path | existing (fires once bind is real) |
| `region_projection` engages (no "surface lane — no projection") | projection, post-bind | existing (falls out) |
| `region_entry_rejected` `reason="seam_crossing_unresolvable"` | guard fail-loud | **new reason value** |
| `intent_router.region_exits` (exit-vocabulary evidence) | Piece 2 | **new span** (59-27 pattern) |
| `dungeon.map_emitted` `discovered_regions > 0` | map emit, post-bind | existing (falls out) |

A nonzero rate of `narration_seam_recovery` is the live signal that Piece 2's
router context needs tuning. The GM panel reads every seam kind through the
same `movement.resolved` + `seam_kind` contract.

## 6. Scope amendments & dependencies

- **Repos:** `server` → `server,content` (Piece 1 is a content file).
- **AC coverage:** AC1 ← Pieces 0+3+4 (deterministic via state; router never the
  sole gate). AC2 ← Piece 4 fail-loud branch. AC3 ← §5 spans. AC4 ← 59-15
  scenario after 105-1 lands. AC5 ← Piece 4 gating constraint + surface
  adjacency untouched.
- **Materializer:** untouched (epic guardrail holds — the registry consumes the
  store, never writes it).
- **Dependency:** 105-1 (span-proof harness) before AC4 verification; Pieces
  0–4 are implementable and behavior-testable first.
- **MP note (out of scope, recorded):** the resolver binds THIS PC (per-PC
  `pc_region`), consistent with split-party semantics.

## 7. Test strategy (for TEA)

- **Registry unit tests:** `get_seam_resolver` fail-loud on unknown kind;
  `seam_route_for` recognition (seam route found / plain routes ignored /
  region with no routes).
- **Resolver behavior:** synthetic store + graph → bind to `entrance`, span
  attrs (`seam_kind`, `resolved_via`); empty store →
  `SeamCrossingError("no_dungeon_entrance")`.
- **Hybrid movement (AC1):** beneath_sunden-shaped fixture (region-mode cart +
  seam route + live store) — `deeper` / `toward_exit` / "down the rope"
  descriptor each → `pc_region == "entrance"`. Region-mode world WITHOUT a seam
  route → `region_mode_deferred` unchanged (oz non-regression).
- **Recovery (AC1/AC2):** no movement dispatch; narration result with
  `location: "The Dropmouth — The Deep"` while PC on seam region → PC bound to
  `entrance`, applied location == authored room name, recovery span; heading
  NOT in `discovered_regions`.
- **Fail-loud (AC2):** same, empty dungeon store → patch rejected,
  `seam_crossing_unresolvable` span, `pc_region` unchanged.
- **Router context (Piece 2):** summary for a seam-region PC contains
  `current_region_exits` naming "Down the Rope"; absent for non-cartography
  snapshots.
- **Non-regression (AC5):** 90-6 tests green; ropefoot ↔ the_dropmouth
  adjacency still resolves; `entry_skipped_sub_location` unchanged for seam-less
  worlds.

## 8. Rev 2.1 amendment — drift-strip (resolution of the §4/§7 contradiction)

**Found during implementation review (2026-06-12).** Rev 2 was internally
contradictory: §4 Piece 4 gates recovery on "the narrated heading does not
resolve to known cartography," but §7's prescribed recovery test heading —
`"The Dropmouth — The Deep"`, the live turn-3 repro — **does** resolve:
`resolve_known_region_id`'s leading-segment match maps it to `the_dropmouth`,
so it takes the *same-region-drift* path and never reaches the Piece 4 branch.
Both clauses could not hold. Implemented as written, the exact confabulation
the story exists to kill survived as a cosmetic re-title (the rev 1 root-cause
3 harm, verbatim).

**Resolution (Architect adjudication): strip, don't cross.** The drift path
gains a third behavior: when same-region drift fires AND the PC's current
region owns a registered seam route AND the drifted sub-title differs from the
region's canonical display name, the engine **re-anchors the applied title and
the `character_locations` ledger to the canonical region name** — no crossing,
no patch acceptance. Emits `region.entry_rejected`
`reason="seam_region_sub_location_stripped"` with the original heading.
Crossing off a drifted title was rejected because it re-introduces text
classification as the gate (the lexical floor §3 already rejected) and would
teleport a player on a benign POI re-title. Benign sub-titles are flattened
*only* in seam-owning regions — a threshold region is exactly where a narrated
sub-location is how the confabulated deep gets minted. Seam-less region-mode
worlds (oz) keep the 90-6 cosmetic re-title unchanged.

**AC2 is therefore satisfied jointly by three guard outcomes:** drift-strip
(resolvable sub-title over a seam region), recovery (unresolvable heading →
real crossing, re-anchored to "Under the Rope"), and fail-loud rejection
(`seam_crossing_unresolvable`, patch dropped, scene boundary suppressed so an
anchored confrontation survives the refusal).

**Companion fixes landed with the amendment:** the pre-resolution
`character_locations` write is re-anchored on all three outcomes
(`_reanchor_location_ledger`, MP cohort-aware); the rejection path no longer
manufactures a spurious scene boundary (scratch sweep + combat-abandon
suppressed via the same-region-drift mechanism); a rejected patch emits no
`state.location_update` event (the GM panel never sees a move the engine
refused); and `_entrance_room_name` reads `TacticalGridPayload.room_name`
(the rev 2 `payload.get("name")` sketch was a latent AttributeError).

**OTEL addition to the §5 table:** `region_entry_rejected`
`reason="seam_region_sub_location_stripped"` — guard drift-strip — **new
reason value**.
- **Wiring test:** full turn through `execute_intent_router_pre_narrator_pass`
  + `_apply_narration_result_to_snapshot` with the seam fixture, asserting the
  span family — the guard reachable from production paths. Plus an import-time
  registration check (`"deep_descent" in` registry once `sidequest.dungeon` is
  imported).
- **Content validator:** entrance-room presence for dungeon-rooting worlds goes
  in the pack validator, not pytest.
