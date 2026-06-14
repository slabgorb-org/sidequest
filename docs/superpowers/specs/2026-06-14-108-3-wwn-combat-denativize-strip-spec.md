# 108-3 — WWN Combat De-Nativize: Content Strip-Spec

> **⚠ CORRECTION (2026-06-14, gm).** This spec's central premise — that a de-nativized WWN combat def can author **zero beats** — is FALSE against the current server model. The loader **requires ≥1 beat** per confrontation (`rules.py:590`, unconditional) and validates each `allowed_classes` class's `encounter_beat_choices` against the **combat beats pool** (`loader.py:701`). Stripping the beats today makes all three WWN packs fail to load. 108-3 is therefore **BLOCKED on new server story 108-7** (gate both invariants on the bound ruleset so WN packs may author zero combat beats). Revise this spec once 108-7 lands. Everything below about the *per-pack targets* and the *do-not-touch DIAL defs* remains correct; only the "no beats needed / strip the line" mechanics are premature.

**Author:** Architect (The Man in Black) · **Date:** 2026-06-14
**Story:** 108-3 (content-only; routes to **gm** for VALIDATION, not a TDD RED phase)
**Doctrine:** ADR-143 (WN binding *replaces* native combat — no balancing) · ADR-139 Inv-3 (mechanically-capable Other) · SOUL.md "Bind the Ruleset, Don't Balance It"
**Depends on:** 108-1 (engine core cut — `wn_round.py` — **done/merged**)

---

## Why this is a strip-spec, not a plan

There is **no design to make** here. ADR-143 already decided it (ruled emphatically by Keith, 2026-06-14) and ADR-139 Inv-3 already fixes the canonical def shape. 108-3 *executes settled doctrine* against content YAML. This document is the precise enumeration the gm implementer validates against so they don't (a) over-strip the chase/negotiation defs, or (b) improvise a shape. It is deliberately mechanical.

ADR-143, Decision (verbatim): the native ADR-033 beat/dial engine — the `strike`/`brace`/`push`/`angle` beat kinds, the `edge_config` fleeting-tag system ("Opening"/"Counter Stance"), the inert dial metrics, and the per-beat auto-reprisal — **"is NOT used and is NOT balanced under a WN binding. It is removed from the WN combat path."**

The WN sealed initiative-round engine (`wn_round.py`, landed in 108-1) supplies the combat action set at runtime. ADR-143 line 210: the corrected WN combat action set is **attack / move / item-use / cast**. The content def therefore does not author actions at all — once the native `beats:` list is removed, the engine provides resolution.

---

## Canonical de-nativized WWN COMBAT def (the target shape)

A WWN `win_condition: hp_depletion` confrontation def expresses **only**:

```yaml
<combat def id>:
  win_condition: hp_depletion          # KEEP
  opponent_default_stats:              # KEEP — all six abilities + hp/armor_class/dexterity
    STR/DEX/CON/INT/WIS/CHA: ...       #   (per-pack ability labels vary; keep whatever six exist)
    hp: ...
    armor_class: ...
    dexterity: ...                     # initiative seed (1d8 + DEX)
  opponent_damage: {dice: "...", bonus: 0}   # KEEP — DamageSpec (ADR-139 Inv-3: the damage lever
                                             #   is authored content; a toothless Other is a loud defect)
```

Nothing else. No `resolution_mode`, no `beats:`, no defensive action, no momentum/dial metrics, no `edge_config`.

### STRIP from each COMBAT def
| Field | Note |
|-------|------|
| `resolution_mode: beat_selection` | the native-engine selector — remove the line entirely |
| the entire `beats:` list | **all** beats, regardless of local id names (see role-not-name rule below) |
| `edge_config` | not present in any of the 3 packs today — remove **if** found; do not add |
| momentum / dial-metric block (`metrics:` / `dials:` / momentum fields) | not present as structured fields today (momentum only appears as narrative text *inside* beats, which goes when the beats list goes) — **verify none remain** after the strip |
| the Brace / defensive action | it is a *beat* in the list above; it goes with the list. Brace is not a WWN action (ADR-143). |

### KEEP (do not touch)
`win_condition: hp_depletion`, `opponent_default_stats` (the full six-ability + hp/AC/dexterity block — the WWN defender-save path KeyErrors on a missing ability), `opponent_damage` DamageSpec.

### Role-not-name rule (trap)
The native beats carry different local ids per pack. Strip the **whole list** by role, not by matching literal ids:
- `caverns_and_claudes` / `heavy_metal`: `strike`, `cast_spell`, `brace`, `committed_blow`, `break_contact`
- `elemental_harmony`: `strike`, `elemental_burst`, `cast_spell`, `guard` (the brace-equivalent), `yield` (the break-contact-equivalent)

`cast_spell` / `elemental_burst` go too — casting is the WN `cast` action, supplied by the engine. Do not preserve a casting beat as a special case.

---

## Per-pack targets (genre-tier `rules.yaml` only)

All three packs are `ruleset: wwn`. Crunch loads from the **genre tier**; world-tier confrontation files do **not** exist for any verify-target world (confirmed: beneath_sunden, evropi, long_foundry, barsoom, burning_peace, shattered_accord carry none). So every edit is in the genre `rules.yaml`. The "verify target" worlds are where you playtest the result, not separate edit sites.

### `sidequest-content/genre_packs/caverns_and_claudes/rules.yaml`
- **STRIP →** `Dungeon Combat` (≈ lines 119–219; `resolution_mode` @126, beats @151–218, `opponent_damage: {dice: "1d8", bonus: 0}` kept)
- **DO NOT TOUCH →** `Corridor Pursuit` (chase, ~220–258), `Haggling at the Counter` (negotiation, ~259–311). Both have `beats:` lists — leave them.

### `sidequest-content/genre_packs/heavy_metal/rules.yaml`
- **STRIP →** `Blade-work` (≈ lines 131–228; `resolution_mode` @136, beats @165–227, `opponent_damage: {dice: "1d8", bonus: 0}` kept)
- **DO NOT TOUCH →** `Cold Negotiation` (~88–129), `Pursuit` (~230–272).

### `sidequest-content/genre_packs/elemental_harmony/rules.yaml`
- **STRIP →** `Martial Exchange` (≈ lines 114–209; `resolution_mode` @122, beats @153–208, `opponent_damage: {dice: "1d6", bonus: 0}` kept)
- **DO NOT TOUCH →** `Diplomatic Council` (~69–113), `Pursuit` (~210–252).

> Line numbers are from the 2026-06-14 read and will drift as you edit — anchor on the def **id** and on `win_condition: hp_depletion`, not the numbers. Exactly one `resolution_mode: beat_selection` exists per pack; that line marks the only def to strip.

**Out of scope for this story:** the SWN packs (space_opera), CWN packs (road_warrior, neon_dystopia, mutant_wasteland) — those have their own ruleset epics (114-x). 108-3 is **WWN only**.

---

## ⚠ Open question — the 107-2 stub rider rests on a stale premise

The story also asks to "fix the 107-2 content stubs: Torchdeep/Torchhold/Bileden have `creature_id=None`/`threat=None`/`abilities=[]` … and the 'Dungeon Names' naming-source leak into the description field."

**These do not exist in the content tree.** A case-insensitive sweep of all of `sidequest-content/` finds zero matches for `torchdeep`/`torchhold`/`bileden`, and the string `"Dungeon Names"` appears nowhere under `caverns_and_claudes/`. The story describes them in the present tense as committed content to fix; they are not committed content.

Most likely explanation: beneath_sunden's deep is **procedurally generated** (Sünden Deep engine, ADR-106) — these are runtime room names, not authored YAML. If so, the `creature_id=None`/`threat=None`/`abilities=[]` symptom and the description leak are a **server/engine** artifact, which is **out of the content-repo scope** this story carries (`repos: content`).

**Recommendation (SM/PO decision, not the gm's):**
1. **Descope** the 107-2 rider from 108-3 — keep 108-3 to the clean, ready WWN de-nativize — **or**
2. Have the gm first **reproduce** the null-stat symptom in a live beneath_sunden descent and confirm whether the fix surface is content or server. If server, re-file under the appropriate epic with `repos: server`.

Do **not** author three phantom rooms to satisfy a description that doesn't match the tree. (Pattern: stale story premises — verify the repro before acting.)

---

## What "done/verified" means (content-validation path)

Content-only → **VALIDATE, do not TDD-RED**:
1. `load_genre_pack` succeeds for all three packs after the strip (the loader is the real wiring gate — a validator PASS is not proof of load).
2. Each stripped COMBAT def parses to the canonical shape: `win_condition: hp_depletion` + `opponent_default_stats` (six abilities + hp/AC/dexterity intact) + `opponent_damage` DamageSpec — and **no** `resolution_mode`/`beats`/`edge_config` remain.
3. The three DIAL defs per pack (chase/negotiation) are byte-for-byte unchanged.
4. Cliché audit on any touched prose (none expected — this is deletion).
5. **Live verify** on beneath_sunden (primary): a combat encounter resolves through `wn_round.py` (attack/move/item-use/cast), the seeded Other deals `opponent_damage` (not toothless, ADR-139 Inv-3), and the OTEL `wn.native_scaffolding_suppressed` span fires — proving the native riders did **not** fire under the WN binding. heavy_metal (evropi/long_foundry/barsoom) + elemental_harmony swept the same way.

---

## Housekeeping (SM's lever, flagged not fixed)

Story 108-3 carries `workflow: superpowers`, which is **not a registered pf workflow** (`pf workflow type superpowers` → not found). It must be reconciled to a valid tag or the content→gm validation path before setup completes. Architect does not edit sprint YAML.
