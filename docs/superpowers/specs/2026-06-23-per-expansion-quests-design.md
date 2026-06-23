# Per-Expansion Quests — Bridging the Dungeon Generator to the Quest Spine

- **Date:** 2026-06-23
- **Status:** Design approved (brainstorming); ready for writing-plans
- **Deciders:** Keith Avery (Operator), Neo (Architect)
- **Related ADRs:** ADR-106 (procedural megadungeon), ADR-137 (player-facing quest spine), ADR-014 (Diamonds and Coal), ADR-006 (Graceful Degradation)
- **Related stories:** 158-15 (QUESTS connect/resume bootstrap re-emit), 158-16 (beneath_sunden empty quest spine)
- **Constraint:** ADR-106 Amendment C (2026-06-23) — the LLM is removed from the dungeon materialize path; the generator is deterministic and the live narrator owns prose at encounter time. This design stays on that side of the line.

## 1. Problem

`beneath_sunden` is the procedural megadungeon world (ADR-106). It authors no
`active_stakes` and no `quest_seed`, and a Without-Number PC typically has no
`drive`, so the turn-0 quest seed (`game/quest_seed.py::seed_quest_spine`)
degrades to an empty spine and the player-facing **Quests tab is blank for the
whole descent**. The player has no legible "what am I doing here" as the dungeon
grows.

The deeper finding (reuse audit, 2026-06-23): there are already **two
disconnected quest representations**, and the dungeon's own quests never reach
the player:

- **(A) The ADR-137 spine** — `GameSnapshot.quest_log: dict[str, QuestEntry]`
  → `game/projection/quests.py::build_quests_payload` →
  `server/websocket_handlers/quests_emit.py::_maybe_emit_quests` → the `QUESTS`
  message → the Quests tab. This is what the player sees.
- **(B) The dungeon complication ledger** — set-pieces already carry
  `QuestComponent`s (`dungeon/setpieces.py`) that seed at attach
  (`dungeon/setpiece_attach.py::seed_quest_components` →
  `ComplicationThread(kind="quest")` in `dungeon_complication_ledger`,
  `dungeon/persistence.py`), with a live `quest.seed` span. **Mature and wired —
  but it writes to the ledger, not to `quest_log`.** The dungeon's quests are
  invisible to the player.

This feature bridges **B → A**: seed one quest per dungeon **expansion**,
project it into the player-facing spine, and resolve it when the expansion's
signature beat fires. Filling the empty `beneath_sunden` Quests tab falls out as
a direct consequence.

## 2. Decisions (locked during brainstorming)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Granularity | **Per expansion** (the burst of regions that pops in together — `Expansion` in `dungeon/region_graph/model.py`), not per region or per set-piece. Matches ADR-106's bursty dramatic pacing; avoids complication-ledger pile-up. |
| D2 | Generation | **Deterministic from the theme palette.** Each theme ships a quest template; the generator fills it from the expansion's own contents. No LLM on the materialize path (Amendment C). Narrator flavors the player-facing prose on surface. |
| D3 | Lifecycle | **Anchored to the expansion's signature beat;** completes when that beat resolves. |
| D4 | Storage | **Ledger is the source of truth; project into the ADR-137 spine.** The per-expansion quest is a `ComplicationThread(kind="quest")`; a reconcile step mirrors open quest threads into `quest_log`. |

Rejected alternatives: per-region / per-set-piece granularity (D1); LLM-at-attach
or code-only objective text (D2); `quest_log`-only seeding and the
"unify-everything: ledger is the only quest store" model (D4 — the latter is the
north-star end-state but out of scope here, see §8).

## 3. The signature beat (D3 detail)

An expansion is a burst of regions, so we need a deterministic rule for **what
completes the quest**. The **theme's quest template declares the signature
kind**, and the generator binds it to a concrete element in the expansion:

- **`big_bad`** — bind the `big_bad` of the deepest region (highest
  `depth_score`) that rolled one (`assemble_region` produces
  `big_bad: dict | None` per region). Objective: "deal with {big_bad}."
  Completes on that NPC's `hp_depletion`.
- **`set_piece`** — bind a set-piece flagged `signature` in the theme. Completes
  when that set-piece's thread resolves (reuses the existing trope-resolution
  handshake, `setpiece_attach.py::resolve_complications_for_resolved_tropes`).
- **`reach_deep`** — bind the terminal / deepest region. Completes on the
  frontier transition into it (`frontier_hook.notify_region_transition`).

**Loud degrade (No Silent Fallbacks / ADR-006):** if the declared kind cannot
bind (e.g. template says `big_bad` but the expansion rolled none),
deterministically fall back to `reach_deep` (always bindable) and emit a
`dungeon.quest.bound` span with `severity="warning"` and `degraded=true`. Never
a silent skip. Themes declare intent explicitly; `reach_deep` is the honest
universal fallback.

## 4. Components

### 4.1 Content — theme quest template (net-new, homebrew-authorable)

Add a `quest_template` slot to `DungeonTheme` (`dungeon/themes.py`, currently
ending at the `set_pieces` field) and to the pack theme YAML
(`genre_packs/caverns_and_claudes/worlds/beneath_sunden/themes/*.yaml`):

```yaml
quest_template:
  signature: big_bad            # big_bad | set_piece | reach_deep
  title: "The {theme} Stirs"
  objective: "Something rules the {theme}. Find it and end it."
```

Slots (`{theme}`, `{big_bad}`, `{anchor}`, `{depth}`) are filled
deterministically from the expansion's own contents. The text is a **hint**, not
the final prose — the narrator renders the player-facing flavor when the quest
surfaces, exactly as Amendment C has it render creature telegraphs. Per
"Crunch in the Genre, Flavor in the World," this slot is content, not engine
code, so Jade/Keith can author it without a server change.

### 4.2 Engine — seed at attach (reuse)

New `seed_expansion_quest()` — sibling of the existing
`setpiece_attach.py::seed_quest_components` — called inside the materializer's
attach transaction (`dungeon/materializer.py` `_stage_attach`/`_stage_commit`,
which already run within a `DungeonTransaction`):

1. Select the signature element per §3 (deterministic).
2. `tx.open_thread(kind="quest", origin_region_id=<signature_region>,
   payload={title, objective, signature_kind, signature_ref, anchor_id})`.
3. Reuse the live `quest.seed` span; add the `dungeon.quest.bound` span carrying
   the selected `signature_kind`, the bound element id, and `degraded`.

One expansion-level quest thread per expansion, atomic with the expansion commit.
This is additive to any set-piece `quest_components` that already seed.

### 4.3 Engine — projection bridge (the new connective tissue)

A reconcile step mirrors **open** dungeon quest threads into
`GameSnapshot.quest_log` as `QuestEntry`:

- `QuestEntry.id` namespaced **`dungeon:expNNN`** (so the projection owns only
  its own entries and never clobbers the drive-spine quest or narrator-recorded
  quests).
- `anchor_id` = the signature element id; `status="active"`; `title`/`objective`
  from the bound template.
- Run at `frontier_hook.notify_region_transition` (already mutates the snapshot —
  `discovered_regions` — and is already wired) and at first attach so the first
  expansion's quest shows immediately.

Once written to `quest_log`, the entry is **persisted in the save**, and the
**existing** `_maybe_emit_quests` carries it to the Quests tab with no new emit
code. Resume visibility depends on **158-15** (the QUESTS connect/resume
bootstrap re-emit) — direct synergy; without 158-15 the projected quest is blank
on reload until the spine next changes.

### 4.4 Engine — resolution (generalize what exists)

Generalize `setpiece_attach.py::resolve_complications_for_resolved_tropes()` (the
45-20 handshake that already flips ledger threads to resolved on a game event) to
also resolve `kind="quest"` threads when their signature beat fires:

- `big_bad` → on `hp_depletion` of the bound NPC.
- `set_piece` → when the bound set-piece's trope/thread resolves (already in the
  handshake).
- `reach_deep` → on the frontier transition into the bound terminal region.

On resolve: flip the ledger thread (`ledger.resolve` span, reuse), flip the
projected `QuestEntry.status` → `"completed"` in `quest_log`, and fire a new
`dungeon.quest.resolved` span. The next emit shows the quest completed in the tab.

### 4.5 OTEL (mandatory — ADR-106 clause 12, CLAUDE.md)

- **Reuse:** `quest.seed`, `ledger.add`, `ledger.resolve`.
- **Add:** `dungeon.quest.bound` (signature selection — `signature_kind`, bound
  element id, `degraded`); `dungeon.quest.resolved` (`signature_kind`,
  `expansion_id`, resolving event).

The GM panel must be able to prove: quest seeded → projected into `quest_log` →
resolved on the beat — not narrator improvisation.

## 5. Reuse map (what exists, file:line)

**Directly reusable:**
- `dungeon/persistence.py` — `ComplicationThread` (`kind="quest"`, open/resolved),
  `open_thread`/`resolve_thread`, `ledger.add`/`ledger.resolve` spans. Mature.
- `dungeon/setpiece_attach.py::seed_quest_components` — the seed pattern to mirror;
  `resolve_complications_for_resolved_tropes` — the resolution handshake to
  generalize.
- `telemetry/spans/dungeon_setpiece.py::quest_seed_span` — `quest.seed`.
- `game/session.py` — `QuestEntry(title, objective, status, anchor_id)`,
  `quest_log`, `quest_anchors`.
- `game/projection/quests.py::build_quests_payload` +
  `server/websocket_handlers/quests_emit.py::_maybe_emit_quests` — spine → wire.
- `dungeon/frontier_hook.py::notify_region_transition` — live snapshot-mutation
  seam, fires on region move.
- `game/cookbook/assemble.py::assemble_region` — per-region manifest with
  `big_bad`, `special_rooms`, `cr_band`.
- `dungeon/region_graph/model.py::Expansion` — the per-expansion object.
- `dungeon/themes.py::DungeonTheme` — the theme palette to extend.

**Net-new:**
1. Expansion **signature-beat designation** (§3) — `Expansion` carries no
   signature/boss today.
2. `DungeonTheme.quest_template` slot + YAML (§4.1).
3. `seed_expansion_quest()` (§4.2).
4. Ledger → `quest_log` **projection bridge** (§4.3) — the core missing link.
5. **Quest-thread resolution** path generalized from the trope handshake (§4.4).
6. `dungeon.quest.bound` / `dungeon.quest.resolved` spans (§4.5).
7. `beneath_sunden` theme `quest_template` content.

## 6. Data flow

```
expansion attach (materializer, in tx)
  └─ seed_expansion_quest(): bind signature → tx.open_thread(kind="quest")   [quest.seed + dungeon.quest.bound]
       │
region transition / first attach (frontier_hook.notify_region_transition)
  └─ reconcile open quest threads → snapshot.quest_log (id="dungeon:expNNN", status=active)   [persisted]
       │
per turn / connect-resume (existing _maybe_emit_quests; resume needs 158-15)
  └─ QUESTS message → Quests tab
       │
signature beat fires (hp_depletion | setpiece resolve | reach_deep transition)
  └─ resolve handshake: ledger thread → resolved  [ledger.resolve]
                        QuestEntry.status → completed                       [dungeon.quest.resolved]
       │
next emit → Quests tab shows completed
```

## 7. Testing / wiring (mandatory)

- **Wiring test** (fixture-driven, per server CLAUDE.md "No Source-Text Wiring
  Tests"): materialize an expansion through the real attach path → assert a
  `kind="quest"` thread opened **and** a `QuestEntry` with id `dungeon:exp...`
  appeared in `snapshot.quest_log`; fire the signature beat → assert both the
  ledger thread and the `QuestEntry` flipped to resolved/completed. Drive the
  flow and assert on OTEL spans + emitted message, never on source text.
- **Determinism parity** (Amendment C): materialize the same expansion twice from
  one seed → identical quest (title/objective/signature binding).
- **Degrade path:** an expansion that cannot bind the declared signature kind →
  `dungeon.quest.bound` with `degraded=true` and a `reach_deep` binding; the
  quest still seeds and projects.
- **Coexistence:** a session with a drive-spine quest (`seed_drive`) AND dungeon
  expansion quests → both present in `quest_log`; the projection never mutates
  non-`dungeon:` entries.

## 8. Scope boundary

**In scope:** per-expansion quest (D1); theme `quest_template` (D2/§4.1);
`seed_expansion_quest` at attach (§4.2); ledger → `quest_log` projection bridge
(§4.3); resolution-handshake generalization (§4.4); OTEL (§4.5); wiring +
determinism tests (§7); `beneath_sunden` `quest_template` content.

**Out / unchanged:**
- **Hierarchical sub-quests** (per-region objectives under an expansion umbrella)
  — rejected at D1; per-expansion only.
- **Completion rewards / loot-on-resolve** — separate concern; note as future.
- **The "unify everything: ledger is the only quest store" model** — the
  north-star end-state, but it merges the drive-spine lifecycle
  (`seed_quest_spine`, which lives in `quest_log`) with the ledger and touches the
  projection for every world. Out of scope; revisit after this ships.
- **Any LLM on the materialize path** — Amendment C holds; objective text is
  deterministic, prose is the narrator's at surface.
- **The drive-spine quest behavior** — untouched; coexists via namespaced ids.

**Dependency:** resume visibility of these quests rides on **158-15** (QUESTS
bootstrap re-emit). This feature does not subsume 158-15 — it depends on it.
**Relationship to 158-16:** 158-16 (author `beneath_sunden` `active_stakes`/
`quest_seed`) is a narrower stop-gap for the empty-tab symptom; this feature is
the structural fix. If this lands, 158-16 may be reduced to "author the theme
`quest_template`s" or closed — to be reconciled when this is planned.

## 9. Open questions for planning

- Exactly **where** the reconcile step lives if a session has no frontier
  transition before the first emit (first-attach hook must cover it).
- Whether `seed_expansion_quest` should also write `quest_anchors` (ADR-137) for
  the signature element, or only `QuestEntry.anchor_id`.
- Whether `set_piece` signature binding should require an explicit
  `signature: true` flag in the theme set-piece, or pick the highest-tier rolled.
