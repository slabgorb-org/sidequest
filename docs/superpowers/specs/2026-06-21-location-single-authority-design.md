# Location Has One Author — The Engine. The Narrator Goes Cosmetic.

**Date:** 2026-06-21
**Author:** Architect (Atlas the Endurer)
**Status:** Proposed design — pre-implementation
**Repos:** server (engine only; no content, no UI)
**Supersedes the premise of:** `completed/2026-06-12-surface-deep-crossing-design.md` (105-2)
**Recommends:** promotion to an ADR — this changes a system-wide invariant, and an ADR is what makes attempt 9 un-mergeable by citation.

---

## 0. The one-sentence decision

`current_region` and `pc_regions` have **exactly one writer — `GameSnapshot.apply_world_patch`, driven by the engine.** The narrator's scene title is **cosmetic**: it may decorate a label *inside* the engine's region, but it may never move the party. If the engine didn't cross, the party didn't cross.

---

## 1. Why this note exists: eight attempts, all ours

The static→procedural descent on `beneath_sünden` (and lateral region travel on `oz`/`wonderland`/`gulliver`) has been "fixed" eight times, every commit authored by Keith Avery + Claude, no outside contributor:

| # | Commit / story | What it added |
|---|---|---|
| 1 | `348c1e5a` 59-12 | surface→deep handoff in `movement.py` |
| 2 | `de4f85c8` (2026-06-02) | region-mode early-return *above* it (to silence oz) — **turned 59-12 into dead code for region-mode worlds** |
| 3 | `cd4c3ff5` 105-2 (#831) | seam registry + the title-scrape backstops (Piece 4, narration_seam_recovery) |
| 4 | `454ac501` 105-3 (#837) | reverse seam (entrance→surface) |
| 5 | `be4f7464` (#835) | in-dungeon movement for region-mode worlds |
| 6 | `d8396829` 105-2 Piece-2 (#1016) | seam vocabulary per-acting-PC |
| 7 | `5fcea151` 153-21 (#1020) | "don't clobber a same-turn crossing" |
| 8 | `fix/dungeon-seam-reachable-from-surface` (this branch) | `seam_route_via_adjacency` (descend from one step off the seam) |

**The pattern:** every attempt *added a crossing path or a guard*. **None removed an authority.** We have been treating the alarm as the feature.

The live trace that proves it (sq-playtest 2026-06-21, session `6c89369d`): the descent crossed `ropefoot → the_dropmouth` via `narrator.location_drift_repaired ... new_from_title='The Dropmouth — on the rope, descending'` → `region.current_region_advanced caller=narration_apply.location_update`. **The narrator's prose title moved the party.** Attempt 8's own engine code (`surface_descent_adjacent`) never fired. Had the narrator titled the scene "The Shaft" (as it did in the failing session `e2424194`), it would have failed again — exactly as it has eight times.

---

## 2. Root cause — and the good news

### 2.1 The chokepoint already exists, and it is already correct

`GameSnapshot.apply_world_patch` (`game/session.py:1483`) is a clean single authority:

- **`patch.pc_region`** (`:1537`) is the per-PC transition point: writes `pc_regions[pc]`, stamps the `region_transitions` receipt, fires the frontier hook, then **the anchor `current_region` follows by consensus** (`region_for()`, `:1585-1594`).
- **`patch.current_region`** (`:1595`) is the spawn/teleport anchor, and its own comment states the invariant outright (`:1600`): *"Movement NEVER sets `current_region`; it sets `pc_region`."*
- **`region_for()`** is the authoritative read — consensus of `pc_regions`, **never falls back to the anchor** (`:1575`).

The seam resolvers obey this perfectly. `deep_descent.py:54` crosses via `apply_world_patch(WorldStatePatch(pc_region={pc: entrance_id}))`. The whole seam machinery is engine-authoritative and honest.

### 2.2 There is exactly one bypasser

**`narration_apply.py:4466-4467`** reaches *past* `apply_world_patch` and sets `snapshot.current_region` and `snapshot.pc_regions[player_name]` **directly, from the parsed narrator title** (`_resolve_heading_to_cartography(result.location, …)`). This is the single violation of the §2.1 invariant. Every reconciliation guard in `narration_apply` — `location_drift_repaired`, the §8 drift-strip, `narration_seam_recovery`, and 153-21's "don't-clobber" — exists **only to referee the fight between this rogue writer and the legitimate engine writer.** Remove the rogue write and there is nothing left to reconcile.

### 2.3 Why the rogue write was added (the real gap to close)

The movement subsystem **defers** for lateral region-mode travel. In `movement.py`, a region-mode world (`navigation_mode == region`: oz, wonderland, gulliver, beneath_sünden's *surface*) resolves **seam crossings** (down/up) and **in-dungeon crawl** engine-side — but a *lateral* cartography move (oz: `munchkin_country → the_emerald_city`; beneath_sünden: `ropefoot → the_dropmouth`) hits `_defer_region_mode` (`movement.py:416-423`). **There is no engine path that advances a region-mode region from a lateral movement intent.** The title-scrape is the *only* mover for lateral region travel — which is why deleting it naively would freeze oz at `munchkin_country` (the bug `de4f85c8` was solving). The hole is real; we must fill it in the engine, not paper it with prose.

This is precisely the "**There is no deterministic backstop**" the 105-2 note named in its own §2.3 — and then declined to build, choosing a *narrator* backstop instead and calling deterministic-parsing-of-nondeterministic-prose "engine-deterministic."

---

## 3. The invariant (the law this note enshrines)

> **`current_region` and `pc_regions` are written by `apply_world_patch` alone.**
> Movement writes `pc_region`; the anchor follows consensus; spawn/teleport writes the `current_region` anchor. **No other code path — emphatically including `narration_apply` — writes either field.** The narrator's scene title is a cosmetic label rendered *under* the engine's region; if it disagrees with the engine, the engine wins and the disagreement is an OTEL alarm, never a state change.

This is not new policy. It is the policy already written at `session.py:1600` — we are extending it to be **total** by removing the one path that violates it and giving the engine the one capability it was missing.

---

## 4. Design

Three moves. Two are deletions.

### 4.A Give region-mode worlds an engine lateral mover (the only genuinely new code)

In `movement.py`'s region-mode block, before `_defer_region_mode`, add lateral cartography resolution: resolve the movement intent (`direction` / `exit_descriptor`) against **`region_for(pc)`'s cartography adjacency + routes** — the exact `region_exits` set the intent router already projects (`{name, kind: "adjacent"|"seam"}`, `intent_router_pass.py:_build_state_summary`). On a unique match, cross via the existing chokepoint: `apply_world_patch(WorldStatePatch(pc_region={pc: target_region_id}))`. This is the cartography-graph sibling of the §Q1 procedural room-graph navigator that already exists — same shape, same patch path, different graph.

- **Ambiguous or no match → fail loud** via the existing `_unresolved` / `movement.unresolved` path (the OTEL lie-detector), surfacing an honest "which way?" line. A missed lateral move is a *re-prompt*, not a silent confabulation. (When the parked intent-router clarify loop, `2026-06-20-intent-router-clarify-loop-PARKED.md`, ships, it replaces the bare re-prompt with a structured disambiguation — but `movement.unresolved` is the honest floor today.)
- **`back` / no-store non-regression:** seam-less region-mode worlds with no resolvable lateral exit still behave; this resolver only fires on a *real* adjacency/route match.

### 4.B Sever the narrator's region authority

Delete the region-advancement branch in `narration_apply.py` (the `known_region_id` write at `:4464-4490` and its drift/clobber siblings). `location_update` keeps writing **only** the cosmetic scene label (`character_locations` free-text / `result.location` for display) — scoped *inside* `region_for(pc)`. It may **never** write `current_region` or `pc_regions`.

**Yes-And preserved.** The narrator inventing "the gnaw-scarred alcove off the east wall" remains canon — it lands as a POI label within the engine's region (Diamonds-and-Coal, the MUSH principle). What it can no longer do is *relocate the party* to a region the engine didn't move them to.

### 4.C Demote drift to an alarm; engine stamps the heading

When the narrator's title resolves to a region ≠ `region_for(pc)`, that is **`region.narrator_location_drift`** — an OTEL watcher event (the lie detector firing, exactly as CLAUDE.md intends) — and the displayed heading is **re-anchored to the engine region's canonical name**. The engine owns the heading; the narrator fills the prose beneath it. This is the clean replacement for `seam_region_sub_location_stripped` + `location_drift_repaired` + `narration_seam_recovery`: one alarm + one cosmetic re-anchor, instead of three crossing-capable guards.

---

## 5. Reuse analysis (pragmatic-restraint ledger)

| Concern | Verdict |
|---|---|
| Single-writer chokepoint | **Reuse** `apply_world_patch` (`pc_region` + anchor-follows-consensus). Already correct, already used by every seam resolver. |
| Authoritative region read | **Reuse** `region_for()` consensus. No change. |
| Exit vocabulary for the router | **Reuse** `intent_router_pass` `region_exits` projection (105-2 Piece 2). Already built. |
| Adjacency / route data | **Reuse** `cartography.yaml` `regions[].adjacent` + `routes[]`. Already loaded as `cart`. |
| Lateral region-mode resolver | **NEW — small.** The cartography-graph twin of the existing §Q1 room-graph navigator. The *only* net-new logic. |
| Frontier/transition receipts, OTEL spans | **Reuse** — they fire automatically because crossing goes through `apply_world_patch`. |

**Net deletion, not addition.** The following exist solely to reconcile the rogue writer and disappear with it: the `narration_apply` title→region branch, `location_drift_repaired`'s crossing behavior, the §8 drift-strip cross/strip logic, `narration_seam_recovery`, and 153-21's same-turn-don't-clobber. The seam resolvers (`deep_descent`, `surface_ascent`) and the chokepoint stay untouched. This is the first attempt that makes the file *smaller*.

---

## 6. Pieces (implementation order — sequencing is load-bearing)

1. **Piece A — engine lateral mover** (`movement.py` region-mode block). Land *first*: region-mode lateral travel must work engine-side before the scrape is removed, or oz/wonderland/gulliver freeze. Behavior-test each region-mode world's canonical lateral move resolves to `pc_region == target` via the patch path.
2. **Piece B — sever the narrator write** (`narration_apply.py`). Delete the region-advancement branch; keep cosmetic label only. Add the `region.narrator_location_drift` alarm + canonical-name re-anchor.
3. **Piece C — delete the reconciliation scar tissue** (don't-clobber, drift-strip-cross, narration_seam_recovery). These are now unreachable; remove them and their tests, or convert the tests to assert the *alarm* path.
4. **Piece D — the tripwire test** (see §7) lands with Piece B and stays forever.

---

## 7. Test strategy (the gate — this is what ends the dance)

1. **The mis-title wiring test (the one all 8 attempts lacked).** Drive a full turn through `execute_intent_router_pre_narrator_pass` + `_apply_narration_result_to_snapshot` where the narrator returns the *failing* title — `location="Sünden Deep — The Shaft"` (or oz: a wrong region heading) — and **assert the engine still put the party where the movement intent pointed** (`region_for(pc) == "entrance"` / the intended region), and that the `movement.resolved` span (not a narration path) did the crossing. This test is **RED on `develop` and RED on this branch.** It is the acceptance gate. Per CLAUDE.md "Every Test Suite Needs a Wiring Test" — our unit tests proved the function in isolation eight times; not one proved the live turn reaches the engine instead of the prose.
2. **The single-writer tripwire (runtime, not source-grep).** A reflection/behavior test that drives representative moves and asserts `current_region`/`pc_regions` mutations are observed **only** through `apply_world_patch` — e.g. assert the `region_transitions` ledger / `SPAN_APPLY_WORLD_PATCH` span accompanies every region change, and that a narration-only turn with a drifted title produces a `region.narrator_location_drift` alarm and **zero** region mutation. Any future code that writes the field directly fails this test. (Honors CLAUDE.md "No Source-Text Wiring Tests" — OTEL/behavior assertions, never `read_text()`.)
3. **Non-regression — every region-mode world navigates.** oz `munchkin_country → the_emerald_city`, wonderland `the_hall_of_doors → the_garden`, gulliver, and beneath_sünden surface `ropefoot → the_dropmouth` each resolve laterally via Piece A. The_circuit (CWN room-graph) and pure room-graph worlds unaffected (this block is region-mode only).
4. **Fail-loud, not strand.** An ambiguous lateral intent emits `movement.unresolved` + an honest "which way?" line; assert no region mutation and no confabulated heading applied.

---

## 8. OTEL (acceptance signals)

| Signal | Source | New/existing |
|---|---|---|
| `movement.resolved` `resolved_via="region_lateral"` | Piece A | **new `resolved_via` value** |
| `movement.unresolved` `reason="ambiguous_region_exit"` | Piece A fail-loud | existing span, **new reason** |
| `region.narrator_location_drift` (title ≠ engine region) | Piece C alarm | **new watcher event** (replaces `location_drift_repaired` + `seam_region_sub_location_stripped`) |
| `apply_world_patch` span present on **every** region change | chokepoint | existing — now the *sole* source |
| `frontier.region_transition`, `region.anchor_synced` | chokepoint consensus | existing — fire unchanged |

The GM panel test: after the change, **every** `current_region`/`pc_regions` mutation is downstream of an `apply_world_patch` span, and any narration-driven region claim shows as a `narrator_location_drift` alarm with no state behind it. The lie detector goes quiet because there is no lie left to tell.

---

## 9. Risks & mitigations

- **Region-mode worlds regress if Piece A is incomplete.** Mitigation: Piece A lands and is behavior-tested per world *before* Piece B removes the scrape. Sequencing in §6 is mandatory, not advisory.
- **Intent-router lateral classification is an LLM step.** True — but it is the *same* dependency we already accept for the room-graph navigator, confrontation, and magic dispatch (ADR-113), run **pre-narration against a projected exit list and verified by `dispatch_engagement_watcher`** — strictly more bounded and more observable than parsing a freeform prose title post-hoc. We are moving the LLM dependency from "unbounded, unverified, post-narration" to "bounded, verified, pre-narration." That is the ADR-113 thesis applied to location.
- **Scope is system-wide, not beneath_sünden.** That is the point (the long view): single-authored location is inherited for free by the orbital jump scale (ADR-141) and frontier expansion — the same boundary, solved once, retiring the bug *class*, not the bug.

---

## 10. SOUL alignment

- **Tabletop First, Then Better.** The DM (engine) decides where the party is; the narrator describes it. Today the description decides the position — backwards. This restores the baseline before amplifying it.
- **The lie detector is the architecture, not a patch on it.** CLAUDE.md: *"never let the narrator move the party."* We built OTEL to *detect* the narrator moving the party (`session.py:4491`), then built the location system to *let* it. This makes the detector's premise true.
- **Yes-And and Diamonds-and-Coal survive** (§4.B) — narrator invention still canonizes as POIs within the engine's region; only the teleport dies.
- **No Silent Fallbacks** — ambiguous moves fail loud and ask; they never confabulate a deep the engine didn't open.

---

## 11. Recommendation

Promote this to an **ADR** ("Location is Single-Authored: the Engine Owns Region, the Narrator is Cosmetic"). Eight commits circled this because there was no cited law to stop attempt N+1 from adding guard N+1. The ADR + the §7 tripwire are the two artifacts that make the ninth attempt impossible: one states the invariant, the other enforces it in CI.

**Do not merge the current `fix/dungeon-seam-reachable-from-surface` branch as a fix.** Keep its joiner `pc_regions` seeding (`chargen_mixin.py` — genuinely necessary and invariant-compatible: it seeds per-PC truth through the right field). Drop the seam-crossing half (`seam_route_via_adjacency` + the `movement.py` adjacency block + the intent-router projection-via-adjacency) — it is guard #8 on the wrong foundation. Re-scope as the epic this actually is.
