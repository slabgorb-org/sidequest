# Story 153-21 Context

## Title
[DUNGEON-SEAM-CROSSING-STICKY] descend-the-rope must traverse the the_dropmouth->deep_descent seam into the procedural entrance node, not latch the narrator title back to the static cartography region

## Metadata
- **Story ID:** 153-21
- **Type:** bug
- **Points:** 5
- **Priority:** p1
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep

## Problem Statement

In `beneath_sunden` (caverns_and_claudes, region-mode + procedural-dungeon hybrid),
a normal one-descent player is told they are "in the first chamber" but is
mechanically still parked on the **surface** cartography region. The generated
ADR-106 dungeon never attaches.

Verbatim finding (2026-06-20/21 sweep):

> Cartography defines route 'Down the Rope' `from_id: the_dropmouth` →
> `to_id: deep_descent` (a SEAM SENTINEL the ADR-106 materializer maps to the
> procedural dungeon root `entrance`, room `rooms/entrance.yaml` "Under the
> Rope"). Turn-1 action "descend the shaft to the first chamber, step off the
> rope into that chamber" → narrator titles the scene "The Dropmouth — First
> Chamber", and log
> `region.entry_resolved_to_cartography entry='The Dropmouth — First Chamber'
> region_id='the_dropmouth'` — the resolver string-matches "Dropmouth" and parks
> the PC in the static cartography region, never crossing the `deep_descent`
> seam (`dungeon.map_emitted region=the_dropmouth discovered=0/7`). Only a 2nd,
> more insistent descent finally advances `current_region='entrance'` and
> `discovered=1/10`.

Impact: the player believes they have entered the dungeon; the engine has not
moved them. Combat, room graph, fog-of-war, and look-ahead materialization all
remain inert until a second, more forceful descent — a SOUL.md "Illusionism"
failure a career GM will catch immediately.

## Root Cause Direction

The seam-crossing path **already exists** (movement.py hybrid-descent block and
the narration_apply seam-recovery `elif`) — the bug is an ordering/precedence
defect, not a missing subsystem. **Extend the existing seam path; do not build a
new one.**

In `narration_apply.py::_apply_narration_result_to_snapshot`, the narrator scene
title flows through `_resolve_heading_to_cartography(...)` →
`resolve_known_region_id(...)`. That resolver canonicalizes the heading's
**leading place segment** ("The Dropmouth — First Chamber" → `"the_dropmouth"`
via `leading_place_segment`) and matches it against the cartography region ids
(`region_validation.py:172`). Because `the_dropmouth` IS a declared region, the
match succeeds and `known_region_id` is non-None.

That non-None match drives the code into the `if known_region_id is not None:`
branch (narration_apply.py ~line 4291), which latches `current_region` /
`pc_regions[player]` to `the_dropmouth` and logs
`region.entry_resolved_to_cartography` (~line 4374) — the static-region latch.
The seam-crossing recovery lives only in the **sibling** `elif
_is_region_mode_world:` branch (~line 4380), which fires ONLY when the heading
does **not** resolve to a known region. So a descent whose title still names the
seam-owning region ("The Dropmouth — ...") is captured by the latch BEFORE the
seam route can fire.

The seam machinery the fix must reach is intact and proven:
`movement.py::run_movement_dispatch` already has the hybrid descent block
(`seam_route_for(cart, from_region)` + `get_seam_resolver(...)` →
`resolve_deep_descent`) that binds the PC onto the `entrance` node and fires
`movement.resolved`. The fix should make a descent heading that names the
seam-owning region (and whose action crosses `deep_descent`) take the
**seam-crossing** path rather than the static `region.entry_resolved_to_cartography`
latch — i.e. when `known_region_id` equals a region that `seam_route_for` says
owns a registered seam route AND the move semantics are a descent, prefer the
crossing over the static-region re-anchor.

## Acceptance Criteria

1. **One descent crosses the seam.** A turn-1 descent action in `beneath_sunden`
   whose narrator title is "The Dropmouth — First Chamber" (or any
   leading-segment match on `the_dropmouth`) binds the PC onto the procedural
   `entrance` node: after apply, `snapshot.region_for(perspective=player) ==
   "entrance"` and `current_region == "entrance"` (NOT `the_dropmouth`).

2. **The static-region latch no longer wins on a descent heading.** When the
   PC's current region OWNS a registered seam route (`seam_route_for(cart,
   from_region) is not None`) and the incoming heading resolves back to that same
   seam-owning region, the engine performs the `deep_descent` crossing instead of
   logging `region.entry_resolved_to_cartography` and parking on the static
   region. A non-descent re-title of the same region (e.g. a POI sub-title that is
   genuinely "still at the Dropmouth") must NOT spuriously cross — it stays put.

3. **Scene re-anchors to the authored entrance room.** After the crossing,
   `result.location` is re-anchored to the authored entrance room name ("Under
   the Rope", via `_entrance_room_name`), and the location ledger is rewritten so
   ledger and scene agree (reuse the existing `_reanchor_location_ledger` path).

4. **discovered counter advances on the first descent.** `discovered_regions`
   reflects entry into the deep on the first descent (`discovered=1/N`), not after
   a forced second descent.

5. **Fail loud on an unresolvable crossing.** If the crossing cannot complete
   (no dungeon store, no entrance node), the patch is REJECTED loudly via the
   existing `region_entry_rejected_span(reason="seam_crossing_unresolvable")`
   path and the PC stays put honestly — never silently accept the confabulated
   "first chamber" scene (No Silent Fallbacks).

6. **OTEL / watcher spans (every subsystem decision emits a span).** The crossing
   emits `movement.resolved` (`movement_resolved_span`,
   `sidequest/telemetry/spans/movement.py`) with `resolved_via` indicating the
   narration-driven seam crossing, and the static-latch
   `region.entry_resolved_to_cartography` is NOT emitted for the crossed descent.
   The `region_current_advanced` watcher publish fires with
   `new_region="entrance"`. The GM panel can distinguish "the engine crossed the
   seam" from "the narrator just retitled the scene."

7. **Wiring / integration test proves reachability from a real play path.** Add
   a behavior test that drives a `beneath_sunden` narration result with the
   sticky "The Dropmouth — First Chamber" heading through the real
   `_apply_narration_result_to_snapshot` (extend the existing
   `tests/server/test_narration_seam_recovery.py` `hybrid_apply_kit` fixtures) and
   asserts the PC lands on `entrance` after ONE descent, with the
   `movement.resolved` span captured. No source-text grep assertions (CLAUDE.md
   "No Source-Text Wiring Tests").

## Key Code Areas to Investigate

**The static-region latch vs. the seam-recovery branch (the bug site):**
- `sidequest/server/narration_apply.py::_apply_narration_result_to_snapshot`
  (function starts ~line 3907) — the `if result.location:` location-update block:
  - `if known_region_id is not None:` branch (~line 4291) — sets
    `current_region`/`pc_regions` and logs `region.current_region_advanced`
    (~line 4312) + `region.entry_resolved_to_cartography` (~line 4374). **This is
    the latch that wins too early.**
  - `elif _is_region_mode_world:` seam-recovery branch (~line 4380) — calls
    `seam_route_for(_region_cart, _pc_region)` then
    `get_seam_resolver(str(_seam_route.to_id))(...)`, re-anchors via
    `_entrance_room_name` + `_reanchor_location_ledger`, and emits
    `region_entry_rejected_span(reason="seam_crossing_unresolvable")` on failure.
    **This is the path the descent must reach.**
- `sidequest/server/narration_apply.py::_resolve_heading_to_cartography`
  (line 3671) — produces `known_region_id` from the heading.
- `sidequest/server/narration_apply.py` location-drift repair (~lines 4000-4039):
  `_extract_leading_bold_title` + `location_drift_repaired_span` promote the bold
  title into `result.location` when the narrator leaves it blank — the upstream
  that feeds the latch.

**The resolver that string-matches the title back to the region:**
- `sidequest/game/region_validation.py::resolve_known_region_id` (line 172) —
  matches full form then `leading_place_segment`; this is why "The Dropmouth —
  First Chamber" resolves to `the_dropmouth`.

**The seam machinery the fix must reuse (already wired in movement.py):**
- `sidequest/agents/subsystems/movement.py::run_movement_dispatch` — the hybrid
  region-mode descent block (~lines 169-211): `seam_route_for(cart, from_region)`
  + `get_seam_resolver(...)` → `resolve_deep_descent`. The room-graph surface→deep
  handoff (~lines 340-392) is the same resolver via a synthetic Route.
- `sidequest/game/seams/registry.py` — `seam_route_for` (line 34),
  `get_seam_resolver` (line 25), `surface_owner_for_entrance` (line 49); the
  `_REGISTRY` maps `"deep_descent" → resolve_deep_descent`.
- `sidequest/game/seams/deep_descent.py::resolve_deep_descent` — binds the PC onto
  `_ENTRANCE_ID` and fires the per-PC patch + movement span.
- `sidequest/dungeon/seed_bootstrap.py` — `ENTRANCE_ID` (the `entrance` anchor).
- `sidequest/server/narration_apply.py::_entrance_room_name` (line 168) +
  `_reanchor_location_ledger` (line 210) — scene/ledger re-anchor helpers.

**Cartography source (the route under test):**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml`
  — `navigation_mode: region`, `starting_region: ropefoot`; region `the_dropmouth`;
  `routes: [{name: "Down the Rope", from_id: the_dropmouth, to_id: deep_descent}]`.

**Existing tests to extend (wiring + behavior):**
- `tests/server/test_narration_seam_recovery.py` — `hybrid_apply_kit` /
  `hybrid_apply_kit_empty_store` fixtures; `test_unresolved_heading_on_seam_region_recovers_crossing`,
  `test_dead_store_rejects_patch_loud`, `test_drift_strip_on_seam_region`. Add the
  sticky-resolved-heading case here.
- `tests/agents/subsystems/test_movement_seam_crossing.py`,
  `tests/game/test_seam_deep_descent.py`, `tests/game/test_seam_registry.py` —
  seam-resolver unit coverage to mirror.

## Technical Notes

- **ADR-106** (Runtime Procedural Jaquaysed Megadungeon): `deep_descent` is the
  documented static→procedural SEAM SENTINEL; the materializer roots its Stage-1
  `entrance` expansion there. No authored region carries the `deep_descent` id by
  design — the deep is generated at runtime.
- **ADR-055** (Room Graph Navigation): the PC standing inside the dungeon is on a
  graph node (`entrance` / `expNNN.rN`), not a cartography region.
- **ADR-105 / Story 105-2** (broadcast-layer perception firewall / hybrid seam
  recovery): the `elif _is_region_mode_world:` seam-recovery branch exists
  *because* a region-mode hybrid world's seam crossing can arrive as a narrator
  heading; this story closes the precedence gap that 105-2's recovery left open
  when the heading still resolves to the seam-owning region.
- **OTEL Observability Principle** (CLAUDE.md): the crossing decision must emit a
  watcher span so the GM panel can tell an engine crossing from a narrator retitle
  — that span is the lie detector for this exact Illusionism failure.
- **Reuse-first / Don't Reinvent** (CLAUDE.md): movement.py already owns the
  descent-bind path (`surface_owner_for_entrance`, `deep_descent`, `_ENTRANCE_ID`,
  `dungeon_store.load_map`) and narration_apply already owns the seam-recovery
  branch. The fix is precedence/routing — make the resolved-heading descent reach
  the seam crossing — not a new movement mechanism.

## Story Scope

**In scope:**
- The precedence fix in `narration_apply.py` so a descent whose heading resolves
  to a seam-owning region (`the_dropmouth`) crosses the `deep_descent` seam to the
  `entrance` node instead of latching the static region.
- Scene/ledger re-anchor to the authored entrance room on a successful crossing
  (reuse `_entrance_room_name` + `_reanchor_location_ledger`).
- Fail-loud rejection on an unresolvable crossing (reuse the existing rejected
  span path).
- OTEL span coverage + a wiring/behavior test through the real apply path.

**Out of scope:**
- The in-dungeon descriptor→edge resolver and identical-neighbor dedup — that is
  Story 153-22 (`movement.py::_resolve`).
- Multi-descent / multi-seam cartographies (`surface_owner_for_entrance` ambiguity
  case) — a documented follow-up.
- New seam kinds (ascent geometry, lateral crossings) beyond `deep_descent`.
- The intent-router classification of the descent action (the router already
  emits a movement dispatch; this story fixes the narration-apply latch that
  shadows it).

---
_Enriched from the 2026-06-20/21 /sq-playtest finding; code-area claims verified
against `sidequest-server` source on 2026-06-21._

---

## Architect Design Decision (153-21)

_All line numbers and call shapes below re-verified against live `sidequest-server`
source on 2026-06-21 (branch `feat/153-21-dungeon-seam-crossing`)._

### The real bug (re-stated precisely after reading the code)

The finding's "narrator string-matches Dropmouth and parks the PC" framing is the
*symptom*. The mechanism, verified against the source, is **the apply latch clobbers a
crossing the movement subsystem already performed earlier in the same turn.**

Turn ordering (verified, `websocket_session_handler.py`): the Intent-Router pre-narrator
pass runs the dispatch bank — including `run_movement_dispatch` — at ~line 984, which
**mutates the snapshot before the narrator** (ADR-113 engine-first). `_apply_narration_result_to_snapshot`
runs later at ~line 1177. `turn_manager.record_interaction()` does not fire until
NARRATION_END (~line 1359), so `snapshot.turn_manager.interaction` is **stable across the
whole turn** — the movement crossing and the apply call share one turn number.

When movement crosses the seam, `resolve_deep_descent` (`game/seams/deep_descent.py:54`)
calls `snapshot.apply_world_patch(WorldStatePatch(pc_region={player: "entrance"}))`. Inside
`apply_world_patch` (`game/session.py:1537-1594`) this:
1. sets `pc_regions[player] = "entrance"`,
2. appends a `RegionTransition(turn=interaction, pc_name=player, to_region="entrance", via="world_patch")` (genuine-change gate),
3. anchor-syncs: solo party → `region_for()` consensus is `"entrance"` → `current_region = "entrance"`.

So **after** a successful movement crossing, and **before** apply runs:
`region_for(player) == "entrance"` and `current_region == "entrance"`.

Then apply resolves the heading "The Dropmouth — First Chamber" →
`known_region_id == "the_dropmouth"` (via `leading_place_segment`, `region_validation.py:172`).
The drift-strip block at `narration_apply.py:4237` is gated `current_region == known_region_id`
("the_dropmouth" != "entrance") so it does **not** fire. Control falls to the latch at
**`narration_apply.py:4291`**: `if _is_region_mode_world and snapshot.current_region != known_region_id:`
— `"entrance" != "the_dropmouth"` is **True** → the latch **re-sets `current_region = "the_dropmouth"`
and `pc_regions[player] = "the_dropmouth"`** (lines 4293-4294), appends a *reverse*
`RegionTransition(... to_region="the_dropmouth", via="narration_apply")`, and logs
`region.entry_resolved_to_cartography` (line 4374). **That is the clobber-back.** The PC is
dragged from `entrance` back onto the surface region; only a second descent (when no fresh
title shadows it) sticks.

This reframing matters because it picks the signal: the engine truth we must respect is the
**same-turn movement crossing already on the snapshot**, not anything in the heading text.

### 1. The descent-detection signal — candidate (a), the same-turn crossing receipt

**Decision: signal (a). The crossing already lives on the snapshot when apply runs; apply
must detect it and DECLINE to clobber it back. Apply does NOT perform the crossing itself.**

Why (a) and not (b) or (c):
- **(b) `turn_context.dispatch_package`** is *not reachable* at the apply call site. The
  signature of `_apply_narration_result_to_snapshot` (verified, `narration_apply.py:3907-3928`)
  is `snapshot, result, player_name, *, room, pack, world, dice_failed, dice_actor,
  from_explicit_action, opposed_*, acting_character_name, monster_manual, is_dice_replay,
  lookahead_handle`. There is **no `dispatch_package` parameter** and threading one in is
  unnecessary new surface — the crossing's effects are already recorded on `snapshot`. Reject (b).
- **(c) apply performs the crossing keyed on `seam_route_for(region) is not None` + a
  descent marker** reintroduces exactly the text-classification teleportation 105-2 forbade:
  the only descent marker available in apply is the heading/narration text. There is no
  non-text descent signal *inside* apply other than the receipt left by movement. Reject (c).
- **(a)** uses the receipt movement already wrote. It is the only available, non-text,
  reuse-first signal. **Choose (a).**

**Where the signal lives, concretely.** Read it off the snapshot, two pinned facts:
- `snapshot.region_for(perspective=player_name) == ENTRANCE_ID` (`"entrance"`,
  `dungeon/seed_bootstrap.py:31`) — the PC is already standing on the procedural entrance node,
  AND
- the crossing happened **this turn**: there is a `RegionTransition` in
  `snapshot.region_transitions` with `to_region == ENTRANCE_ID` and
  `turn == snapshot.turn_manager.interaction`.

The `region_for == entrance` check alone is *almost* sufficient, but the same-turn
`region_transitions` clause makes the intent explicit and guards the resume/re-entry edge
(a PC who crossed on a *prior* turn and is mid-dungeon must not be special-cased here — that
is the in-dungeon path, out of scope per 153-22). Use BOTH clauses ANDed.

### 2. Crossing mechanism — DON'T-CLOBBER, not re-cross

**Decision: "don't-clobber a same-turn crossing."** Apply must NOT call `get_seam_resolver`
itself on this path. The crossing was already performed by `run_movement_dispatch` →
`resolve_deep_descent`, which **already emitted `movement.resolved`** with
`resolved_via="surface_descent"` (`movement.py:189`, `deep_descent.py:55-69`) and already
advanced `current_region`/`pc_regions`/`discovered_regions`. Re-crossing would double-fire the
span and the frontier hook.

Concretely, the new guard goes at the **top of the `if known_region_id is not None:` block**
(`narration_apply.py:4210`), before the drift-strip (4237) and before the latch (4291):

> If `_is_region_mode_world`, the PC already stands on `ENTRANCE_ID` via a *this-turn*
> `region_transitions` crossing, and `known_region_id` is the **surface seam-owner** of that
> entrance (`surface_owner_for_entrance(_region_cart).from_id == known_region_id`, or simply
> `seam_route_for(_region_cart, known_region_id) is not None`): the narrator merely
> re-titled the surface seam region while the engine already crossed. **Do not advance/clobber
> `current_region` back to `known_region_id`.** Instead, re-anchor the *scene* to the authored
> entrance room and rewrite the ledger so prose follows the engine (AC3), then fall through
> without taking the latch.

**Reconciling AC6.** AC6 says the crossing emits `movement.resolved` with `resolved_via`
indicating a narration-driven crossing, and `region.entry_resolved_to_cartography` is NOT
emitted. Two honest readings; pick deliberately:

- The **load-bearing** half — *`region.entry_resolved_to_cartography` MUST NOT fire for the
  crossed descent* — is satisfied directly by the don't-clobber guard returning before line 4374.
- The `movement.resolved` span **already fired** during the movement-dispatch crossing earlier
  this turn (with `resolved_via="surface_descent"`). The GM panel therefore already sees the
  engine crossing on this turn. To make the *narration-apply decision itself* observable (the
  CLAUDE.md OTEL principle — every subsystem decision emits a span), the apply guard MUST emit
  its **own** span recording that it honored the same-turn crossing rather than clobbering it.
  **Emit a `movement.resolved` span from the apply guard with
  `resolved_via="narration_seam_recovery"`** (the value the existing 105-2 sibling branch
  already uses, `narration_apply.py:4402`) so AC6's "`resolved_via` indicating a
  narration-driven crossing" reads true and the panel can distinguish "apply honored the
  crossing" from "movement performed it." Reuse `movement_resolved_span`
  (`telemetry/spans/movement.py`, imported by `deep_descent.py:16`). Also fire the
  `region_current_advanced` watcher publish with `new_region="entrance"` if and only if the
  apply guard is the thing that observed `entrance` (it will already be `entrance`; publish so
  the panel's region-advance lane carries the entrance on this turn — AC6 explicitly asks for
  `region_current_advanced` with `new_region="entrance"`). **Do not** emit
  `region.entry_resolved_to_cartography`.

  Chosen `resolved_via` value: **`"narration_seam_recovery"`** (string already in use for the
  sibling 105-2 branch — no new vocabulary).

### 3. Coexistence with 105-2 (`test_drift_strip_on_seam_region` stays GREEN)

The existing `test_drift_strip_on_seam_region` seeds `pc_regions={"Groucho": "the_dropmouth"}`,
`current_region="the_dropmouth"` and applies a pure re-title `"The Dropmouth — The Deep"` with
**no movement dispatch** (the test calls apply directly; nothing crossed). Under the chosen
signal, the new guard's first clause — `region_for(player) == ENTRANCE_ID` — is **False** (the
PC is at `the_dropmouth`, not `entrance`), and there is **no this-turn `region_transitions`
entry to `entrance`**. So the new guard does **not** fire; control reaches the drift-strip
exactly as before, strips to "The Dropmouth", emits `seam_region_sub_location_stripped`. GREEN
preserved. The signal is specifically "a crossing **already happened** this turn," which a pure
retitle never satisfies — that is *why* it is the correct non-text discriminator the story asks
for. `test_oz_drift_retitle_unchanged` and `test_seamless_region_mode_world_unchanged` are
likewise untouched (oz has no seam, no entrance crossing).

### 4. Fail-loud (AC5)

On this path there is nothing new to reject: the crossing the guard honors **already
succeeded** during movement dispatch (resolver raised `SeamCrossingError` → `_unresolved`
there if the store/entrance was dead, so the PC would still be at `the_dropmouth` and the
guard's `region_for == entrance` clause is False — control then flows to the existing
unresolvable path). The existing `region_entry_rejected_span(reason="seam_crossing_unresolvable")`
in the `elif _is_region_mode_world:` branch (`narration_apply.py:4412`) continues to own the
genuine fail-loud case: heading resolves to NO region, PC on a seam-owner, crossing attempted
in apply and failed → reject, PC stays put. **Do not** widen or weaken that span; the
don't-clobber guard never reaches it. If for defensiveness the guard ever finds the
`region_for == entrance` receipt but the authored entrance room can't be resolved for
re-anchoring (`_entrance_room_name` returns nothing), prefer leaving the engine's already-correct
`entrance` region intact and skip the cosmetic re-anchor — never drag the PC back to surface to
"fail safe." (Staying at the truthful `entrance` is the honest outcome; the clobber-back is the
dishonest one.)

### 5. Test-construction guidance for TEA

Extend `tests/server/test_narration_seam_recovery.py` using `hybrid_apply_kit`. The
AC1-cross scenario must be made distinguishable from the AC2-stay scenario **by pre-seeding the
same-turn crossing receipt on the snapshot**, NOT by a flag on `result`:

**AC1 — the cross/honor case (new test, e.g. `test_resolved_seam_heading_honors_same_turn_crossing`):**
Build the kit, then BEFORE calling `apply`, simulate what `run_movement_dispatch` already did
this turn — the most faithful way is to drive the real crossing on the kit's snapshot:
`from sidequest.game.seams.deep_descent import resolve_deep_descent` and call it with
`snapshot=kit.snapshot, player_name="Groucho", route=<the Down-the-Rope Route from the hybrid
cart>, resolved_via="surface_descent", dungeon_store=kit.handle.persistence`. That writes
`pc_regions["Groucho"]="entrance"`, advances `current_region`, and appends the same-turn
`RegionTransition`. (Equivalently, hand-seed: `snapshot.apply_world_patch(WorldStatePatch(
pc_region={"Groucho": ENTRANCE_ID}))` — same receipt, simpler.) THEN
`result = kit.narration_result(location="The Dropmouth — First Chamber")` and `kit.apply(result)`.
Assert:
- `kit.snapshot.region_for(perspective="Groucho") == ENTRANCE_ID` and
  `kit.snapshot.current_region == ENTRANCE_ID` (NOT dragged back to `the_dropmouth`),
- `result.location == ENTRANCE_ROOM_NAME` ("Under the Rope") — scene re-anchored (AC3),
- `kit.snapshot.character_locations["Groucho"] == ENTRANCE_ROOM_NAME` — ledger agrees (AC3),
- `kit.assert_no_span_reason(...)` has no analogue for `entry_resolved_to_cartography`; assert
  instead that the apply did NOT log/emit the latch — use the watcher-capture fixture
  (`captured_watcher_events`) and assert NO `region_current_advanced` event carries
  `new_region == "the_dropmouth"`, AND assert a `movement.resolved` span fired with
  `resolved_via == "narration_seam_recovery"` (extend `assert_span` — it already matches on
  attributes), AND a `region_current_advanced` event with `new_region == "entrance"` (AC6).
- discovered counter: assert `ENTRANCE_ID in kit.snapshot.discovered_regions` reflects the
  deep entry on this first descent (AC4 — note the count comes from the crossing's frontier
  hook / region init; assert membership, not a brittle "1/N" string).

**AC2 — the stay case is the EXISTING `test_drift_strip_on_seam_region`, unchanged** — it
seeds NO crossing receipt (`pc_regions["Groucho"]="the_dropmouth"`), so it must stay GREEN as
the negative control. TEA should run it alongside the new test to prove the signal discriminates.

The one moving part TEA introduces is the **pre-seeded same-turn `entrance` receipt** on the
snapshot. That receipt is the entire signal; a pure-retitle test omits it. No new `result`
flag, no `dispatch_package` threading.

### Wiring test (AC7)

The AC1 test above IS the wiring/behavior test: it drives the real
`_apply_narration_result_to_snapshot` through the `hybrid_apply_kit` (real authored
`rooms/entrance.yaml`, real `resolve_deep_descent`, real `movement.resolved` span capture via
`otel_capture`). No source-text grep assertions (CLAUDE.md "No Source-Text Wiring Tests") —
assert on the captured span + the snapshot landing on `entrance`.

### Self-review

- Decision documented with rationale: yes (don't-clobber on same-turn crossing receipt).
- Alternatives considered: (b) dispatch_package threading — rejected (unreachable at call site);
  (c) apply re-crosses on text — rejected (re-introduces 105-2 text teleportation).
- Implementation guidance for Dev: guard placement at `narration_apply.py:4210` top-of-block,
  read receipt off `region_for`+`region_transitions`, re-anchor via `_entrance_room_name` +
  `_reanchor_location_ledger`, emit `movement.resolved`/`region_current_advanced`, skip the
  latch, never emit `region.entry_resolved_to_cartography`.
- Existing patterns checked first: reuses `resolve_deep_descent`'s already-fired crossing,
  the 105-2 `narration_seam_recovery` resolved_via vocabulary, `_entrance_room_name` /
  `_reanchor_location_ledger`, and the existing fail-loud reject span — no new mechanism.
- Read-only: no source edited; only this context file appended.
