# Significant Items → Invokable Fate Aspects

**Date:** 2026-06-18
**Status:** Design — approved, pending implementation plan
**Related:** ADR-144 (Fate Core Binding), ADR-145 (SRD-Sourced Inventory), SOUL.md (*Rule of Cool*, *Diamonds and Coal*, *Yes, And*)

## Problem

In Fate Core, a significant item is not a line in a backpack — it is an **invokable aspect** (an "extra"). The Silver Shoes of the Dead Witch are something you *invoke* for +2 or a reroll, and that also grants narrative permission (they can carry you home). Mundane gear (Harpo's banjo) is pure narrative permission and needs no tracking. Truly special items are extras with their own stunt and aspect.

Our engine already does this **at character creation**: a `GearDef` with `grants_aspects`/`grants_stunts` compiles onto the `FateSheet` via `fate_gear.py`, and `Aspect.source_gear` records the provenance. But items **acquired during play** get none of it. When the narrator grants the slippers via `items_gained`, `narration_apply.py` appends a plain dict to `core.inventory.items` and stops. The chargen door is open; the runtime door is shut.

This spec opens the runtime door.

## Goal

Items acquired during play in a **Fate-bound pack** can become invokable aspects on the player's `FateSheet`, via two paths:

- **Catalog path (Phase 1):** authored items that declare aspect/stunt grants compile identically whether granted at chargen or mid-play.
- **Narrator path (Phase 2):** the narrator can promote an *invented* item on the fly to a single invokable aspect — guarded so it can never hand out a permanent mechanical edge.

Non-Fate packs are unaffected.

## Design Decisions (locked during brainstorming)

1. **Trigger model: both, catalog-first.** Catalog gear auto-compiles (deterministic, author-owned). The narrator can *also* promote on the fly, but it is a guarded, logged second phase, built after the catalog path lands.

2. **Inventory relationship: dual existence, the aspect is the single invoke-source.** A promoted item stays in `core.inventory.items` as the "you are carrying the slippers" ledger record. The invokable aspect lives on the `FateSheet`, linked back via `Aspect.source_gear = item.id`. All invoking goes through the fate sheet — `invoke_aspect()` already iterates `all_aspects()`, and the projection already ships `character_aspects` to narrator and player. The inventory dict carries a `promoted: true` marker.

3. **Power asymmetry: the narrator can make a thing *true*; only an author can make a thing *strong*.**
   - **Catalog path = aspects + permissions in v1; stunts deferred.** `GearDef` carries `grants_aspects` *and* `grants_stunts`, and the catalog author owns that balance. But the chargen compiler `compile_gear_onto_sheet` (`fate_gear.py:56`) is **not reusable mid-session**: it recomputes `refresh` from `base_refresh` and hard-resets `sheet.fate_points = refresh_after` (lines 103–112), which would wipe fate points the player has already spent. Appending **aspects and permissions** never touches `refresh`/`fate_points`, so a focused runtime promoter handles them safely. Granting a **stunt** mid-game debits refresh — a milestone-advancement economy decision — so it is **deferred**: if a matched `GearDef` carries `grants_stunts`, v1 records the count in the OTEL span (`stunts_deferred`) and does **not** apply them (loud, not silent). A content author owns aspect balance now; mid-game stunt placement is a later story.
   - **Narrator path = aspects only.** A narrator promotion mints exactly **one free-text aspect with `free_invokes: 0`** — invokable only by spending a fate point, like any character aspect. No free +2, no stunt, no rules exception. Stunts require catalog authoring.

   This is *Rule of Cool*'s monkey's-paw discipline: the game says "yes, you found the dead witch's slippers, and yes they're now a truth you can lean on" — but it cannot hand out permanent mechanical advantage off improvisation.

   > **Why a new module, not the chargen compiler:** `compile_gear_onto_sheet` is a *chargen* operation that rebuilds the whole refresh/fate-point economy from scratch on a fresh sheet. Mid-session that is destructive. The runtime path needs its own narrow promoter that appends aspects to a *live* sheet without re-deriving the economy. The aspect-append shape is small (a 2-line loop), so the duplication is trivial and the isolation protects the working chargen path.

## Architecture

The entire feature is **one new block in the `items_gained` path**, gated on the active ruleset being `fate`. Everything downstream already exists and is reused.

### Data flow

```
items_gained entry
  → resolve_item_recipient()          [existing] match catalog, inherit mechanical fields
  → append to core.inventory.items    [existing]
  → IF ruleset == fate AND item carries grants:          ◄── NEW BLOCK
       catalog grants  → fate_gear compiler → aspects + stunts onto FateSheet
       narrator grant  → mint ONE Aspect(free_invokes=0, kind="character"), no stunt
       set Aspect.source_gear = item.id
       mark item dict promoted = true
       emit fate_item_promoted_span
  → fate_projection.character_aspects surfaces it    [existing] to narrator + player
  → player invokes via invoke_aspect() → +2 into 4dF ladder   [existing]
```

### Components

**1. Runtime promotion block (Phase 1 — catalog)**
Location: a new module `sidequest-server/sidequest/game/ruleset/fate_item_promotion.py`, called from the `items_gained` block in `sidequest-server/sidequest/server/narration_apply.py` (right after the inventory append at ~line 4821).

Gate: the recipient character has a Fate sheet — `recipient_char.core.fate_sheet is not None`. This is the same per-character signal the projection uses ("only PCs with a Fate sheet contribute"); no ruleset-registry lookup needed.

Logic: match the gained item's name/id against the pack's Fate gear set (`pack.rules.fate.gear_catalog`, a `list[GearDef]`) using the same conservative exact-match discipline as `resolve_gained_item_dict` (id → slug → case-folded name). On a match, append each `grants_aspects` entry as `Aspect(text, kind, source_gear=item_dict["id"], free_invokes=0)` onto the live sheet — **without** touching `refresh`/`fate_points`. Any `grants_stunts` on the matched gear are counted into `stunts_deferred` and **not** applied (v1 deferral; see decision 3).

Dedup: if an aspect with `source_gear == item_dict["id"]` already exists on the sheet, the grant is a **logged no-op** (emit the span with `deduped: true`), never a silent skip — per *No Silent Fallbacks*.

**2. Narrator promotion (Phase 2 — spotlight)**
The `items_gained` entries are free-form dicts (`entry.get(...)`), so this needs **no protocol model change** — add an optional `grants_aspect` key the narrator may set. When present, mint a single `Aspect(text=grants_aspect, kind="character", free_invokes=0, source_gear=item_dict["id"])` and append to the sheet (the narrator tool contract must be told when to set it).

Guardrails, enforced *by construction*:
- The narrator entry schema has **no stunt field** — narrator-granted stunts are impossible.
- `free_invokes` is **hard-set to 0** in the mint call, not read from narrator input.
- One aspect per item; same dedup rule as the catalog path.

**3. Inventory back-link**
The promoted item dict gains `promoted: true`. This (a) lets the inventory UI flag the item "⚡ invokable", and (b) guards against re-promotion. The aspect→item direction already exists via `source_gear`; this adds the item→aspect awareness cheaply.

**4. OTEL**
New span `fate_item_promoted_span` with fields:
`{ item_id, item_name, aspect_text, source: "catalog" | "narrator", grants_stunt: bool, free_invokes: int, deduped: bool }`.

This is the lie-detector for "did the slippers actually become mechanical, or did Claude just *describe* them as magical with zero mechanical backing?" Fires on every promotion attempt. The invoke span (`fate_aspect_invoked_span`) already exists downstream.

**5. Projection + UI wiring**
The aspect already flows to the player via `fate_projection.character_aspects` (`sidequest-server/sidequest/agents/fate_projection.py`). The work here is a **wiring test** confirming end-to-end reachability: a gained item appears in the player's aspect panel with an invoke affordance, and is labelled as item-sourced so the mechanical math is legible in the **player-facing** surface (serves Sebastien/Jade's mechanics-first read). If the panel already renders `character_aspects`, this is automatic and the test simply pins it.

### Error handling — fail loud

- **Non-Fate packs:** the entire block is gated off. `items_gained` behaves exactly as today; no new fields are read or written. Zero behavior change.
- **Malformed catalog `GearDef`:** fail loud per *No Silent Fallbacks* — do not half-compile or fall back to a bare item.
- **Double grant:** explicit, logged dedup (span with `deduped: true`), not a silent skip.

## Testing

Unit:
- Catalog item declaring `grants_aspects` gained mid-play → aspect on sheet with `source_gear` set; inventory item marked `promoted: true`.
- Catalog extra (stunt + aspect) → both compiled onto the sheet.
- Narrator `grants_aspect` → exactly one aspect, `free_invokes == 0`; narrator cannot grant a stunt (no schema field).
- Dedup → same item granted twice → one aspect, second grant emits span with `deduped: true`.
- Non-Fate pack → `items_gained` unchanged; no aspect minted; no new fields blow up.

Wiring / integration (**mandatory** per project rule "Every Test Suite Needs a Wiring Test"):
- End-to-end: gained item → aspect appears in `fate_projection.character_aspects` → invokable via `invoke_aspect()` → contributes +2 to a real 4dF ladder resolution (`resolve_action_from_faces`).

OTEL:
- Promotion fires `fate_item_promoted_span` with correct `source` and `free_invokes`.

## Phasing

- **Phase 1 (catalog):** new `fate_item_promotion.py` (aspects + permissions, dedup, stunt-deferral count) + `fate.item_promoted` OTEL span + the `narration_apply.py` call site + inventory back-link + unit tests + the mandatory wiring test.
- **Phase 2 (narrator):** `grants_aspect` annotation consumed from the `items_gained` entry (one capped aspect) + narrator tool-contract surfacing + guardrails + tests.

## Scope cuts (YAGNI)

Explicitly **not** building:
- **Mid-game catalog stunt grants** — deferred (the refresh-milestone economy entanglement; the chargen compiler that owns refresh is destructive mid-session). A matched gear's stunts are counted in the span (`stunts_deferred`) and not applied.
- Narrator-granted stunts.
- Narrator-granted free invokes.
- Refactoring the chargen compiler (`compile_gear_onto_sheet`) to share code — the runtime promoter is a separate narrow path; the aspect-append duplication is 2 lines and the isolation protects the working chargen economy.
- A `narrative_weight` auto-heuristic for "significance" — promotion is *explicit* (catalog declares grants, or narrator annotates). No magic number guessing significance.
- Retroactive promotion of already-held items — fires at grant time only.
- A `source_gear` field on the player-facing `FateAspectEntry` (the "from item" UI label) — the promoted aspect already rides the existing aspect panel; the explicit source label is future polish, kept out of v1 to keep Phase 1 server-only.

## Open question — deferred, not built in v1

If a player **loses or drops** a promoted item, its aspect currently lingers on the `FateSheet`, still invokable. Auto-removal would couple inventory deletion to fate-sheet mutation. For v1 this stays a **narrator-handled narrative event** (the narrator can compel or narratively strip it); the engine will not auto-remove. Flagged here as future work.

## Content dependency (named, not in engine scope)

Per ADR-145, Fate packs still carry WN-shaped bespoke `CatalogItem` records until story 114-9; the Fate-native `GearDef` with `grants_aspects` is the model this feature rides on. The **engine seam is clean**, but a Fate pack only benefits once its significant items are authored with aspect grants. This is a content-side follow-on, tracked separately from this engine work.

## Key file references

- `sidequest-server/sidequest/server/narration_apply.py` (~4821, the inventory append) — `items_gained` grant path; call site for the new promoter.
- `sidequest-server/sidequest/game/ruleset/fate_gear.py` (`compile_gear_onto_sheet`) — the chargen compiler; **reference for the aspect-append shape**, NOT reused (it resets the economy).
- `sidequest-server/sidequest/game/ruleset/fate_item_promotion.py` — **new** runtime promoter module.
- `sidequest-server/sidequest/game/fate_sheet.py` — `Aspect` (`text`, `kind`, `free_invokes`, `source_gear`), `FateSheet.all_aspects()`.
- `sidequest-server/sidequest/game/ruleset/fate.py` — `invoke_aspect()`, fate-point economy.
- `sidequest-server/sidequest/game/ruleset/fate_resolution.py` (~122) — `resolve_action_from_faces`, the `invoke_bonus` ladder line.
- `sidequest-server/sidequest/game/ruleset/fate_projection.py` — `build_fate_projection` (`character_aspects`) + `build_fate_state_payload` (player `FATE_STATE`).
- `sidequest-server/sidequest/game/item_catalog_resolution.py` (`resolve_gained_item_dict`, `_slugify`) — the conservative exact-match discipline to mirror for gear matching.
- `sidequest-server/sidequest/genre/models/inventory.py` (240–277) — `GearDef`, `GearGrantAspect`, `GearGrantStunt`.
- `sidequest-server/sidequest/genre/models/rules.py` (~1157) — `FateConfig.gear_catalog`; reached as `pack.rules.fate.gear_catalog`.
- `sidequest-server/sidequest/telemetry/spans/fate.py` — add `fate_item_promoted_span` + `SPAN_ROUTES["fate.item_promoted"]`.
