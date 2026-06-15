# Fate Gear Model — `ruleset: fate` Binding + Gear-as-Aspect Compilation

- **Date:** 2026-06-15
- **Status:** Design (brainstormed; pending Keith review)
- **Story:** 114-9 (design) → 114-10 (apply to the four packs)
- **Implements:** ADR-144 §D5-seam, ADR-145 §D5 (Fate gear deferred here)
- **Repos:** `sidequest-server` (models + chargen compile + OTEL), `sidequest-content` (the four Fate packs)
- **Author:** Atlas (Architect)

---

## Summary (the decision)

Fate has no equipment economy — no cost, no weight, no damage table. So Fate "gear"
is **not** a carried inventory of `CatalogItem`s. It is a thin **authoring shim** that
**compiles into the existing `FateSheet`** at character creation: a piece of gear
becomes an **aspect**, a **stunt**, or a **permission** (a labelled aspect kind), all of
which the F1 Fate engine already runs. There is **no new runtime subsystem and no new
carried-inventory state** — gear dissolves into the aspect/stunt/fate-point economy the
engine inherited from Fate Core.

Concretely, 114-9 specifies:

1. A small, dedicated **`gear.yaml`** content schema (genre + world tier), separate from
   `CatalogItem`, that declares what each piece of starting gear *grants*.
2. Two minimal, deliberate **engine deltas** to the Fate models: a `permission` aspect
   kind, and a `source_gear` back-reference on materialized aspects/stunts (traceability
   for the GM-panel lie-detector and for "you lost the coat" beats).
3. The **chargen compile step** that materializes a character's starting gear onto its
   `FateSheet`, plus the **refresh invariant** that keeps stunt-gear honest (so we never
   re-balance Fate).
4. The **migration** of the four narrative packs to `ruleset: fate` — dropping
   `inventory.yaml`, `starting_gold`, and `currency` — and the boundary against ADR-144's
   F5 (wholesale `native` removal stays a separate, later, gated story).

The governing doctrine is **SOUL.md → Bind the Ruleset, Don't Balance It**: we express
even the biggest magic item (the silver shoes) as *an aspect riding Fate's own
economy*, and let Fate's balance — never homebrew math — do the work.

---

## The four settled design choices

These were resolved in brainstorming (Keith, 2026-06-15). Each closed a genuine fork.

### A — Gear compiles into the sheet (not a carried inventory)
A gear item *is* a FateSheet entry once chargen runs. There is no separate inventory
panel, no live carried-item list the resolver consults. **Consequence:** *mid-game* gear
acquisition needs **zero new mechanism** — finding a magic sword is already Fate's
`create-an-advantage` (place a situation/character aspect) or a milestone (grant a stunt),
both of which the engine does today. 114-9 therefore only designs **how *starting* gear is
authored and compiled at chargen.**

### A2-i — A dedicated `gear.yaml` block; `CatalogItem` is left untouched
`CatalogItem` stays purely WN-shaped (`extra="forbid"`, priced/weighted/damage). Fate packs
**drop `inventory.yaml` entirely** and author a new, lightweight `gear.yaml`. This keeps the
strict WN catalog model uncontaminated by a second paradigm (no union model that rots) and
honors *No Stubbing*. Rejected alternatives: relaxing `CatalogItem` to carry Fate fields
(union rot); folding gear straight into raw aspect/stunt authoring (loses gear→sheet
traceability, which the GM-panel lie-detector and item-loss beats need).

### P-i — "Permission" is a narrator-read aspect kind, never an engine gate
A permission ("the badge that lets you order constables," "the picks that let you *attempt*
the safe") compiles to an aspect of a new `permission` kind. The narrator reads it in-prompt
and adjudicates within genre truth; **the engine never refuses an articulated action for
lack of a permission.** This is the only option consistent with **SOUL.md → The Zork
Problem** (never let gear imply a closed verb set). Rejected: a hard capability gate (builds
the closed-verb-set refusal SOUL forbids, and these four genres are the least
capability-gated of all).

### K-i — Starting gear is archetype-bundled, refresh priced in
A pack's archetypes carry their signature gear; the gear-stunts are already accounted for in
that archetype's authored `refresh`. Player picks an archetype and receives its gear with no
separate shopping step (a one-pick flow that protects Alex-style players). À-la-carte gear
selection (K-ii) and swap/add (K-iii) remain **expressible later with no schema change** —
same posture ADR-144 took toward FAE approaches (YAGNI now).

---

## Architecture & data flow

```
CONTENT (authoring)                 ENGINE (runtime)                    SURFACES
─────────────────────               ────────────────                   ────────
genre/<g>/gear.yaml   ─┐
                       ├─ merge ──►  GearDef[]  ──┐
world/<w>/gear.yaml   ─┘  (by id,   (validated)   │
                          ADR-145 D3              │  chargen compile
                          paradigm-               ▼  (gear → sheet)
                          neutral)         FateSheet                    GM panel reads
archetype.gear: [ids] ───────────────────► aspects[]  (incl. permission)  gear_compiled
                                           stunts[]   (source_gear back-ref) span;
                                           refresh    (debited by stunt-gear) players read
                                                                              fate points
rules.yaml: ruleset: fate ─► FateRulesetModule (F1, already built)
```

- **`gear.yaml`** lives at the **genre tier** (shared signature gear) and the **world tier**
  (world-distinct gear), merged **by `id`** through the *same* paradigm-neutral
  genre/world merge ADR-145 §D3 already provides for `inventory.yaml`. Fate's `gear.yaml`
  slots into the existing layered-content machinery; only the *model* differs.
- **Archetypes reference gear by `id`.** At chargen the referenced `GearDef`s are
  **materialized** onto the new character's `FateSheet`: each grant becomes an `Aspect`
  and/or `Stunt`, every materialized entry stamped with `source_gear` = the gear `id`.
- The **runtime `FateSheet` is the single source of truth.** `gear.yaml` is static
  authoring input, consumed once at chargen. Nothing reads `gear.yaml` mid-session.

---

## Schema

### New content model — `GearDef` (`gear.yaml`)

A new strict model in `sidequest-server` (alongside, not inside, `inventory.py`'s
`CatalogItem`). Each entry declares flavor plus **one or more grants**.

```python
class GearGrantAspect(BaseModel):
    model_config = {"extra": "forbid"}
    text: str                       # the aspect phrase, e.g. "Collar Always Up"
    kind: Literal["character", "permission"] = "character"
                                    # "permission" => P-i narrator-read permission aspect

class GearGrantStunt(BaseModel):
    model_config = {"extra": "forbid"}
    name: str
    description: str = ""            # the mechanical effect, authored as content (Fate stunt)
    # No per-stunt cost field: a Fate stunt costs exactly 1 refresh (SRD), so cost is
    # the stunt *count* against the `free_stunts` allotment — see the refresh invariant.
    # A single source of truth (the count-based formula) beats a redundant cost field.

class GearDef(BaseModel):
    """A piece of Fate starting gear. Compiles into FateSheet entries at chargen.
    Fate has no equipment economy: no value, weight, or damage fields exist here."""
    model_config = {"extra": "forbid"}
    id: str
    name: str                       # presentation; freely reskinnable per world
    description: str = ""            # flavor
    grants_aspects: list[GearGrantAspect] = Field(default_factory=list)
    grants_stunts: list[GearGrantStunt] = Field(default_factory=list)
    # A gear item with neither grant is pure narrative flavor (legal: a hat is a hat).
```

Notes:
- **No provenance field.** ADR-145's `ItemProvenance` exists to distinguish *SRD-verbatim*
  from *bespoke* mechanical envelopes. Fate Core ships **no** equipment catalog, so every
  `GearDef` is bespoke-by-construction — the field would always say the same thing (YAGNI).
  The Fate-Core-SRD licensing posture (`ccby`) attaches to the *ruleset code*, not to
  per-item gear. (If a future Fate setting ever sources gear from a licensed Fate supplement
  with a real economy, provenance can be added then — paradigm-neutral, no rework.)
- **Permission is a `kind` on an aspect grant, not a third top-level grant type.** It is an
  aspect that happens to read as permission. This keeps ADR-145's three-word vocabulary
  (aspect / stunt / permission) while the schema carries only two grant lists.

### Engine deltas to the Fate models (`fate_sheet.py`) — two, both deliberate

1. **`AspectKind` gains `"permission"`:**
   ```python
   AspectKind = Literal["high_concept", "trouble", "character",
                        "situation", "consequence", "boost", "permission"]
   ```
   A permission aspect is invokable/compellable like any aspect; its `kind` tells the
   narrator prompt-builder (F2) to present it as a *capability/justification*, and tells the
   GM panel to badge it as a permission. **No resolver code reads it as a gate** (P-i).

2. **`Aspect` and `Stunt` gain `source_gear: str | None = None`** — the `id` of the
   `GearDef` they were compiled from (`None` for hand-authored, non-gear entries). This is
   the **traceability** we chose A2-i to preserve: the GM panel can prove an aspect came
   from the silver shoes, and a "you lose the coat" beat can identify exactly which aspect to
   remove. `extra="forbid"` stays; this is a first-class field, not loose metadata.

### What is REMOVED for Fate packs (content)

- `inventory.yaml` (genre and world tier) — deleted for the four packs.
- `starting_gold`, `currency`, `starting_equipment`, `item_catalog`, `philosophy`
  (the whole `InventoryConfig`) — gone; Fate has no economy.
- **Loader constraint (No Silent Fallbacks):** the genre loader MUST treat `InventoryConfig`
  as *legitimately absent* for a `ruleset: fate` pack and MUST NOT fabricate a default
  catalog or gold. A `ruleset: fate` pack that *also* ships an `inventory.yaml` is a **hard
  validation error** (paradigm mismatch), not a silently-tolerated leftover.

### `rules.yaml` binding (mirrors the WN packs)

```yaml
ruleset: fate
fate:
  base_refresh: 3          # pack-declared; SRD default 3
  free_stunts: 3           # stunts free at base_refresh before refresh is debited
  # per-genre skill list, aspects guidance, etc. (F4 territory; not gear)
```

---

## Chargen compile + the refresh invariant

At character creation, for the chosen archetype:

1. Resolve the archetype's `gear: [ids]` against the merged `GearDef` set (fail loud on an
   unknown id — No Silent Fallbacks).
2. For each `GearDef`: append each `grants_aspects` entry to `FateSheet.aspects` (with its
   `kind`, `source_gear` set) and each `grants_stunts` entry to `FateSheet.stunts` (with
   `source_gear` set).
3. Compute the sheet's `refresh` and validate the **refresh invariant** below.
4. Emit the `fate.gear_compiled` OTEL span (see OTEL).

### The refresh invariant (this is the whole balance story)

In Fate, **an aspect is free** (it only matters when a fate point is spent to invoke it) but
**a stunt costs refresh**. Therefore:

- **Aspect-gear and permission-gear are free by construction** — author them liberally; they
  cannot unbalance anything. (The coat, the badge, the picks, the silver shoes.)
- **Stunt-gear MUST debit refresh.** A "free" stunt-granting item is exactly the homebrew
  balance break the binding exists to forbid (*Bind the Ruleset, Don't Balance It*).

**Validation (content validator — `sidequest-validate`, not a unit test):** for every
archetype, given `base_refresh` and `free_stunts` from `rules.yaml`, the archetype's
authored net `refresh` MUST equal
`base_refresh − max(0, total_stunts − free_stunts)` (floor per SRD, typically 1), where
`total_stunts` counts **authored stunts + gear-granted stunts**. This makes "stunt-gear
costs refresh" a *checkable* invariant: an author cannot bundle a stunt-item without paying
its refresh, and the validator names the offending archetype if they try. (Per the
no-content-in-unit-tests rule, this lives in the pack validator.)

---

## Worked example — the silver shoes (Baum's, not MGM's)

The single nastiest item in the `wry_whimsy`/Oz target world, and the clearest proof the
model holds. It is a **found** item, so it exercises the **mid-game path that uses no
`gear.yaml` at all**:

- **Acquisition.** Dorothy takes them off the dead Witch of the East. The narrator does a
  `create-an-advantage` and places a **character aspect** `Silver Shoes of the Witch of the
  East`. No schema, no inventory row, no `GearDef` (that's chargen-only).
- **What they grant.** As an **aspect** (free): invoke for +2 where justifiable (the book's
  "the wearer never tires"); *compellable* — the Witch of the West **covets them**, a
  narrator compel that drives Act II. As a **permission** (P-i, narrator-read): they grant
  permission to do the otherwise-impossible — cross the Deadly Desert, step home in three
  strides — honored by the narrator, **never an engine gate**.
- **The power-grab guard.** "Teleport anywhere at will" is plasma-rifle-tier. Two layers
  stop it, neither built specially: (1) it's an **aspect, not a stunt**, so it is a one-shot
  climactic beat gated behind a fate-point invoke / concession, and per canon the shoes are
  **lost forever** over the desert the instant they're used — SOUL's monkey's paw, verbatim;
  (2) the **K-i refresh rule refuses** the power-gamer's "at-will teleport *stunt*" — a
  bounded Fate stunt is "+2 in a circumstance," not a reality-warp, so the binding won't let
  it be a balanced stunt at all.
- **Unknown → revealed.** Dorothy doesn't know what they do for most of the book. The aspect
  starts as coal — `Curious Silver Shoes` — and is **promoted** (renamed to `Silver Shoes
  That Carry You Home`) on Glinda's reveal, using the aspect-rename milestone move the engine
  already inherits. No "identify item" subsystem.

**Contrast that proves the choice:** under a hard `permission:` gate (the rejected P-ii),
someone writes `permission: teleport` and the engine either refuses real player actions or
grants an at-will god-button — both wrong. The A / A2-i / P-i / K-i stack absorbs the item
as *just an aspect riding the fate-point economy*.

---

## Mid-game gear acquisition (explicitly: no new mechanism)

Restating because it bounds the scope: any gear gained in play is handled by mechanics the
engine already runs — `create-an-advantage` → situation/character aspect; milestone → stunt
(refresh-priced); narrator removal of an aspect on item loss (locatable via `source_gear`
when the lost item was chargen gear; for found items the narrator simply drops the aspect it
placed). 114-9 designs none of this; it is already live in F1.

*(Optional future, flagged not built: a world-tier `GearDef` could carry a `findable: true`
marker so the narrator hands out notable named items consistently. YAGNI for 114-9 — mid-game
items need no block. Listed as an open question.)*

---

## OTEL (the lie detector must prove gear fired)

Per the OTEL Observability Principle, chargen gear compilation emits a span so the GM panel
can verify gear actually materialized (not narrator improv):

- **`fate.gear_compiled`** — attributes: `archetype`, and per `GearDef`: `gear_id`,
  `aspects_placed` (text + kind), `stunts_added` (name), `refresh_before` / `refresh_after`
  / `refresh_debited`, `permission_aspects` (count). One span per character build.

Runtime invoke/compel of a gear-sourced aspect already rides the existing F1 spans
(`fate.action_classified`, fate-point deltas); `source_gear` rides through so the panel can
attribute an invoke to its originating item. No new runtime spans are required.

---

## Migration — the four packs (114-10)

`pulp_noir`, `spaghetti_western`, `tea_and_murder`, `wry_whimsy`. Per pack:

1. Set `ruleset: fate` + the `fate:` block in `rules.yaml`; remove the `native:` /
   `ruleset: native` config.
2. Delete `inventory.yaml` (genre + every world); remove `starting_gold` / `currency`.
3. Author `gear.yaml` (genre-tier shared signature gear; world-tier world-distinct gear,
   e.g. Oz's silver shoes *if* pre-authored as findable — else left to mid-game narrator
   placement).
4. Wire each archetype's `gear: [ids]` and set its `refresh` to satisfy the refresh
   invariant.
5. Run `sidequest-validate`: no `inventory.yaml` under a fate pack; every archetype's
   refresh balances; no gear `id` dangling; no permission aspect read by a resolver path.

**Boundary against ADR-144 F5 (wholesale `native` removal).** 114-9/114-10 *bind* the four
packs to `fate` and strip their native config; they do **not** delete `native.py` or the
dial/beat/reprisal machinery. F5 (deleting `native` outright) stays a separate, later story
gated on re-homing WN-pack chase/negotiation off the `native` dial (ADR-144 §Consequences).
Flipping these four packs to `fate` is necessary-but-not-sufficient for F5 and does not
depend on it.

---

## Invariants / Contracts

- **Fate gear is sheet-resident, not carried.** Gear compiles into `FateSheet` at chargen;
  there is no carried-inventory list and no `CatalogItem` for Fate gear.
- **`CatalogItem` is untouched.** The WN priced catalog and Fate gear never share a model.
- **Aspect-gear is free; stunt-gear debits refresh.** Enforced by the refresh invariant in
  the content validator. No free stunts — ever (the forbidden re-balance).
- **Permission is narrator-read, never an engine gate.** No resolver path may refuse an
  action for a missing permission aspect (The Zork Problem).
- **Traceability is data.** Every gear-sourced aspect/stunt carries `source_gear`; the GM
  panel can attribute it and item-loss beats can target it.
- **No silent inventory fallback.** A `ruleset: fate` pack has no `InventoryConfig`; shipping
  one is a hard error, and the loader fabricates nothing.
- **No implied publisher endorsement / SRD-only sourcing** (ADR-145 §D4a/D4b) still binds any
  Fate-Core-SRD attribution in code or README — factual sourcing only.

## Open Questions (Keith to rule)

1. **Pre-authored findable items?** Should `GearDef` carry an optional `findable: true` for
   narrator-consistent named loot (the silver shoes as data), or is mid-game narrator
   placement (no block) sufficient? Recommendation: **mid-game placement only** for 114-9;
   add `findable` later if a world wants deterministic named loot.
2. **À-la-carte gear at chargen (K-ii)?** Confirm we ship **archetype-bundled only** (K-i)
   for 114-9/114-10, leaving player gear-selection to a later story. Recommendation: **yes,
   K-i only now.**
3. **`base_refresh` / `free_stunts` per pack vs. global SRD default.** Confirm packs may
   declare these (recommended, for genre-distinct tone) vs. hardcoding the SRD 3/3.

## Out of scope (explicitly)

- The Fate per-genre **skill lists / aspects / stunts** authoring beyond gear (ADR-144 F4).
- **UI** gear/aspect surfaces (ADR-144 F3) — 114-9 is server + content only.
- **`native` deletion** (ADR-144 F5).
- Any **carried-inventory** or economy feature for Fate.

## Decomposition handed to 114-10 (apply)

1. `GearDef` model + `gear.yaml` loader + genre/world by-`id` merge reuse.
2. `AspectKind += "permission"`; `Aspect`/`Stunt` `source_gear` field.
3. Chargen compile step + `fate.gear_compiled` span.
4. Content validator: refresh invariant, no-inventory-under-fate, dangling-gear-id,
   no-resolver-reads-permission.
5. Migrate the four packs (rules.yaml bind, drop inventory, author gear, wire archetypes).
