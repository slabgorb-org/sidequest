# The Static→Procedural Crossing: Engine-Authoritative, One-Action Descent, Observable

**Date:** 2026-06-22
**Author:** Architect (Atlas the Endurer)
**Status:** Proposed design — approved in shape, pre-implementation
**Repos:** server (engine + telemetry only; no content, no UI)
**Supersedes / corrects:** `2026-06-21-location-single-authority-design.md` — same goal, but that note (a) conflated the surface lateral hop with the deep crossing, (b) dragged in the orbital consequence relocation, and (c) told us to *drop* attempt #8's capability. The forensic evidence below reverses all three. This note is grounded in the actual playtest saves, which the prior note was not.
**Recommends:** promotion to an ADR once verified — this is the 9th attempt at one bug, and the only one written against the save data.

---

## 0. The decision in one sentence

A player at the winch (`ropefoot`) who says "rope down into the deep" is crossed **into the generated dungeon `entrance` in one engine action**, through the single chokepoint `apply_world_patch`; the narrator's scene title can no longer write region state for seam worlds; and **the movement subsystem is made visible in the forensic save record** so we can prove which authority moved each body — the thing eight prior attempts could not see.

---

## 1. The evidence (why this attempt is different)

Every prior attempt was reasoned from code. This one is reasoned from the 6 real `beneath_sunden` playtest saves in the database (`region_transitions` ledger, the authoritative per-PC record, `via` field = what moved them):

| Session | `ropefoot→the_dropmouth` | `the_dropmouth→entrance→exp*` | Outcome |
|---|---|---|---|
| 14759 | — | — | **empty ledger — stranded at ropefoot** |
| 14773 (the spec's "fail") | — | — | **empty ledger — stranded at ropefoot** |
| 14492 | `narration_apply` | — | narrator did the surface hop; never descended |
| 14593 | `narration_apply` | `world_patch` ×2 | reached `exp002.r2` |
| 14754 | `narration_apply` | `world_patch` ×3 | reached `entrance`, bouncing |
| 14812 | `narration_apply` **+ engine, same turn** | `world_patch` ×2 per PC | **party SPLIT — narrator clobbered the engine** |

**Three facts fall out of the ledger:**

1. **The surface hop `ropefoot → the_dropmouth` is narrator-only.** Every instance is `via: narration_apply`. The engine has no live path for it: the seam resolver fires only when the PC's *current* region owns the seam route (`seam_route_for` matches `from_id == from_region`), and only `the_dropmouth` owns it. So the party cannot reach the seam by engine — the narrator must deliver them, and when it doesn't title the scene as the dropmouth, the party is **stranded forever** (14759, 14773 — empty ledgers, the spec's named failure).

2. **The deep crossing `the_dropmouth → entrance` works `via: world_patch`** when reached (14593/14754/14812). The "cross into the generated dungeon" machinery is **not** the dead part. The transit fires — but only after the narrator solves the upstream surface hop.

3. **The clobber is live.** In 14812 the engine moved Groucho `ropefoot→entrance→exp001.r2` *and* `narration_apply` moved him `ropefoot→the_dropmouth` the same turn; the narrator write won, so Groucho ended on the surface while Harpo ended deep. **Two writers, one field, split party.**

**And the reason we could not see any of this for eight attempts:** the movement subsystem emits **zero** rows to the forensic sink. `turn_telemetry` carries `confrontation`, `magic`, `dungeon`, `location` components — but **no `movement` component anywhere in the entire table, across all sessions.** Movement spans (`movement.resolved`, `movement.region_mode`) go to OTEL only; they never reach the saved record. The GM-panel lie detector is blind on the exact subsystem that has been "fixed" eight times. We cannot today distinguish, from the saves, whether the deep `world_patch` crossing was the **engine seam** or the **narrator's `narration_seam_recovery` backstop** — both call `resolve_deep_descent → apply_world_patch` and both stamp `via: world_patch`.

That blindness is the first thing we fix.

## 1.1 The eight attempts (all ours, all on this one crossing)

`fbe28cee` (movement subsystem) · `348c1e5a` 59-12 (bind PC onto entrance on descent) · `de4f85c8` (region-mode "defer cleanly instead of erroring `no_dungeon_store`" — the silent fallback that hands the hop to the narrator) · `cd4c3ff5` 105-2 (seam registry) · `be4f7464` #835 (in-dungeon movement) · `454ac501` 105-3 (reverse seam) · `d8396829` 105-2-Pc2 (per-PC seam vocab) · `5fcea151` 153-21 (don't-clobber — did **not** hold; see 14812) · `711365e0` (make megadungeon reachable from surface seam — `seam_route_via_adjacency`, the dropped attempt #8). `narration_apply.py` has been churned **151 times**.

---

## 2. The law (the invariant this note enshrines)

> For in-scope worlds, `current_region` and `pc_regions` are written by **`apply_world_patch` alone**, driven by the engine. The narrator's scene title is a cosmetic label rendered *under* the engine's region. If the title names a different region, the engine wins and the disagreement is an OTEL alarm (`region.narrator_location_drift`) — never a state change.

This is the policy already half-written at `session.py:1600` ("Movement NEVER sets `current_region`; it sets `pc_region`"). We make it total for in-scope worlds and give the engine the one capability it was missing.

---

## 3. Scope (orbitals stay sealed off)

**In scope:** region-mode worlds that have an engine region mover —
- the seam/dungeon world: `caverns_and_claudes/beneath_sunden`;
- the cartography worlds: `wry_whimsy/{oz,wonderland,gulliver}`.

**Out of scope, untouched:** any world whose region changes flow through the orbital / inter-system path (`perseus_cloud` / space worlds, ADR-141). The narrator-sever (Piece 2) is gated by an explicit predicate, evaluated per world:

> **in-scope ⇔ region-mode AND not orbital-coupled** — where "orbital-coupled" means the world's region-advance triggers `bind_region_scope` (orrery re-center) or `_adjudicate_inter_system_jump_for_advance` (the ADR-141 inter-system jump cost). For v1 this resolves to the four named worlds above; implement it as a predicate (check for orbital coupling), not a hardcoded allowlist, so a future seam world inherits it for free.

We never go near `bind_region_scope` or `_adjudicate_inter_system_jump_for_advance` — an out-of-scope world keeps its current narration region-advance path **unchanged**. The orbital consequence relocation that the 2026-06-21 note demanded is **explicitly not part of this work.** It is a separate concern for a separate day.

---

## 4. Design — three pieces, sequenced

### Piece 3 first — Observability (C): make the mover visible in the save record

This lands **first** because it is the instrument that verifies the other two, and because it immediately answers the question the saves can't: *is the engine movement subsystem even being dispatched on a "descend," or has the narrator's recovery backstop been doing all the crossing?*

- Every region mutation persists a `turn_telemetry` forensic event (the sink that already carries `confrontation`/`magic`/`location`) naming the **writer** and the transition:
  - `writer ∈ { engine_seam, engine_adjacent_descent, engine_lateral, narrator_cosmetic_rejected, bootstrap, self_heal }`
  - `from_region`, `to_region`, `pc_name`, `turn`.
- Mechanism: the movement spans in `sidequest/telemetry/spans/movement.py` declare `component="movement"` but do not reach `PgTelemetrySink`. Route them through the **same watcher publish** that `location`/`confrontation` use (the path that emits `region_current_advanced` in `narration_apply` already persists — reuse it). Investigate why `component="movement"` is dropped and fix the routing, not the span definitions.
- Add a `region.write_authority` forensic event on **every** `apply_world_patch` region change, stamping the caller. This is the single-writer tripwire (design-note §7) made into a persisted, queryable save signal — not a source-grep test (honors CLAUDE.md "No Source-Text Wiring Tests").

**Acceptance for Piece 3:** re-drive a sünden descent and confirm `turn_telemetry` now contains `movement`/`write_authority` rows attributing each region change. This also resolves the open engine-vs-recovery question for good.

### Piece 1 — Engine crosses in one action, from the winch (A/B)

In `run_movement_dispatch`'s region-mode block (`sidequest/agents/subsystems/movement.py`):

- Keep the existing **owned-seam** path: `from_region` owns a descent seam + `direction != "back"` → `resolve_deep_descent` → cross to `entrance`. (`the_dropmouth → entrance`.)
- Add the **adjacent-seam** path: when `from_region` does **not** own a seam but the router-supplied `direction` is a descent (`direction` ∈ {`deeper`,`down`} — the router's coarse direction only; **no freeform descriptor sniffing**, which is the fuzzy matching that has repeatedly misfired) and **exactly one adjacent region owns a descent seam**, route through it and cross to `entrance` in one action. Emits `movement.resolved` with `resolved_via="engine_adjacent_descent"`, `edge_kind="surface_descent"`, through the chokepoint. (`ropefoot → entrance`, one turn.)
  - This is `711365e0`'s `seam_route_via_adjacency` **rebuilt on the clean chokepoint** with real telemetry. The 2026-06-21 note's objection to attempt #8 was its foundation (it was guard #8 stacked on the narrator mess), not the capability. The capability is exactly what "send them in from the winch" requires.
  - **Ambiguity fails loud:** if two adjacent regions own descent seams, `movement.unresolved` (`reason="ambiguous_descent"`) — never a guess (No Silent Fallbacks).
- The lateral mover (named surface moves, oz-style) stays as-is. Owned-seam + adjacent-seam descent + lateral mover together let the engine perform **every** region move sünden and the cartography worlds need — which is the precondition for Piece 2.
- **Remove the silent fallback `de4f85c8` introduced:** a region-mode descent that finds a seam (owned or adjacent) but hits `dungeon_store is None` must fail **loud** (`movement.unresolved`, `reason="no_dungeon_store"`), not defer to the narrator. Deferring a *real* descent is the fallback that strands the party.

### Piece 2 — The narrator goes cosmetic; the clobber dies (A/B)

In `sidequest/server/narration_apply.py`:

- For in-scope worlds, **delete the direct write** of `snapshot.current_region` / `snapshot.pc_regions[...]` from the parsed scene title (the rogue writer at ~`:4464-4490`). The title keeps writing only the **cosmetic** scene label inside the engine's region.
- When the title resolves to a region ≠ the engine's region, emit `region.narrator_location_drift` (alarm) and re-anchor the displayed heading to the engine region's canonical name. This replaces `location_drift_repaired` + `seam_region_sub_location_stripped` + `narration_seam_recovery`'s *crossing* behavior with one alarm + one cosmetic re-anchor.
- **The clobber dies structurally:** the narrator can no longer write region for in-scope worlds, so it cannot override the engine's same-turn crossing (the 14812 failure becomes impossible). 153-21's "don't-clobber" guard becomes unnecessary and is removed (or converted to assert the alarm path).
- **Yes-And preserved:** narrator-invented sub-locations still land as cosmetic POI labels within the engine's region (Diamonds-and-Coal / the MUSH principle). Only the *teleport* dies.

---

## 5. Sequencing (load-bearing)

1. **Piece 3 (observability)** — lands first; verifies dispatch and attributes every mover. Zero behavior change.
2. **Piece 1 (engine one-action descent)** — the engine can now perform every in-scope region move. Verified via Piece 3's writer attribution.
3. **Piece 2 (sever the narrator write)** — safe only after Piece 1, or the cartography worlds freeze (the bug `de4f85c8` was solving). The narrator's surface-hop crutch is removed *after* the engine can walk.

---

## 6. Reuse ledger (pragmatic-restraint)

| Concern | Verdict |
|---|---|
| Single-writer chokepoint | **Reuse** `apply_world_patch` — already correct, already used by every seam resolver. |
| Authoritative region read | **Reuse** `region_for()` consensus. |
| Seam resolution + crossing | **Reuse** `resolve_deep_descent` / the seam registry. |
| Adjacent-seam routing | **Rebuild** `seam_route_via_adjacency` from `711365e0` on the chokepoint (small; the only net-new movement logic). |
| Forensic persistence | **Reuse** the watcher-publish path that already persists `region_current_advanced` to `turn_telemetry`; route `component="movement"` through it. |
| Lateral mover | **Reuse** the Plan-1 `_resolve_cartography_lateral` already in review (PR #1029). |

Net: this attempt **removes** code (the narrator region-write, the reconciliation guards, the `de4f85c8` defer) and adds one small engine path + one telemetry routing fix.

---

## 7. Verification — the gate that ends the dance

1. **Re-run the 6 real sünden scenarios** as fixtures. Assert for each: every descender crosses with `writer = engine_*`; the narrator never writes region; **zero party splits** (14812 stays together); the two stranded sessions (14759, 14773) now cross; and the **mis-title case** — narrator returns `location="Sünden Deep — The Shaft"` — still puts the party on `entrance` (the test all 8 attempts lacked).
2. **The single-writer tripwire** (runtime/behavior, not source-grep): drive representative moves and assert every `current_region`/`pc_regions` mutation carries a `write_authority` forensic event with an `engine_*` writer; a narration-only turn with a drifted title produces a `region.narrator_location_drift` alarm and **zero** region mutation.
3. **Non-regression:** oz/wonderland/gulliver lateral travel still resolves; space/orbital worlds untouched (no in-scope gate match → narration path unchanged).

---

## 8. OTEL signals (acceptance)

| Signal | Source | New/existing |
|---|---|---|
| `movement.resolved` `resolved_via="engine_adjacent_descent"` `edge_kind="surface_descent"` | Piece 1 | **new resolved_via** |
| `movement.unresolved` `reason="ambiguous_descent"` / `reason="no_dungeon_store"` | Piece 1 fail-loud | existing span, **new reasons** |
| `region.write_authority` (writer + from→to) **persisted to `turn_telemetry`** | Piece 3 | **new, and the key fix** — movement becomes visible in saves |
| `region.narrator_location_drift` | Piece 2 alarm | **new** (replaces the crossing guards) |
| `apply_world_patch` region change present on **every** mutation | chokepoint | existing — now the sole source AND now forensically attributed |

The GM-panel test: after this lands, **every** region mutation in the save record is downstream of `apply_world_patch` and carries an `engine_*` writer; any narrator region claim shows as a `narrator_location_drift` alarm with no state behind it. The lie detector goes quiet because there is no lie left — and, for the first time, we can *see* that it is quiet.

---

## 9. SOUL alignment

- **Tabletop First, Then Better** — the DM (engine) decides where the party is; the narrator describes it. Today the description decides — backwards.
- **No Silent Fallbacks** — the `de4f85c8` defer-instead-of-error is removed; a real descent that can't find its dungeon fails loud.
- **The lie detector is the architecture** — we built OTEL to detect the narrator moving the party, then left movement out of the forensic sink so we couldn't. Piece 3 makes the detector's premise true.
- **Yes-And / Diamonds-and-Coal survive** — narrator invention still canonizes as POIs within the engine's region; only the teleport dies.
