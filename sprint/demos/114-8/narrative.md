# Narrative

## Problem Statement
**Problem:** In SideQuest's mutant wasteland setting, the game's gear system was faking it. Weapons listed in the pack had no combat stats from the actual Ashes Without Number (AWN) rulebook — no trauma damage, no shock values. Worse, `scrap_armor` — the signature protective gear of the wasteland — provided absolutely no protection when worn. A character could equip it and walk into combat with the same defense as wearing nothing. Additionally, an artifact called the `power_glove` appeared on the character creation screen but had been quietly dropped from the catalog it draws from, causing a silent fallback to a broken weapon state.

**Why it matters:** The mutant wasteland pack is supposed to run on AWN's ruleset engine. When gear carries no AWN mechanics, the ruleset engine has nothing to engage — combat outcomes are invented whole-cloth by the narrator rather than resolved by the rules. Players who chose this pack for its crunch were being shortchanged without knowing it. The `scrap_armor` bug is particularly visible: a player equips their only armor and the game's GM panel would show AC 10, indistinguishable from a naked character.

---

## What Changed
Think of it like discovering a gun store in a video game that sold realistic-looking guns with no ammo slots or trigger mechanics modeled. This fix goes into that store and wires up every weapon and piece of armor to the actual game rules.

Specifically:

- **Five gear entries** in the wasteland catalog were re-sourced against the AWN rulebook: two melee weapons (sharpened rebar and pipe wrench), two ranged weapons (crossbow salvage and sawed-off shotgun), and `scrap_armor`.
- Each weapon now carries its official **trauma die**, **trauma rating**, and (for melee) **shock value** — the numbers the combat engine uses to determine injury severity and armor penetration.
- `scrap_armor` now carries **AC 15** — the Scrap Mail value straight from the AWN rulebook — instead of nothing.
- Every re-sourced item carries a machine-readable **provenance stamp**: which rulebook it came from, what page, and under what license — making future audits trivial.
- Twelve wasteland-original items (chargen artifacts, survival tools) are correctly marked as bespoke content, not rulebook reproductions.
- An 11-test suite was added to prove the fix holds: not just that the YAML has the right numbers, but that equipping `scrap_armor` actually results in AC 15 flowing through the character system and that the GM panel's observability span fires `chargen.armor_equipped` rather than the gap-signal `chargen.armor_unresolved`.

No production server code changed — the infrastructure to read and apply these fields already existed from prior stories. This was a content fix backed by tests.

---

## Why This Approach
**The doctrine is "bind the ruleset, don't balance it."** SideQuest's design principle is that when a genre pack declares it runs on AWN, the gear should be AWN gear — not hand-tuned approximations. Hand-tuned gear means the team is implicitly trying to re-balance a 200-page rulebook, which is both endless and futile. Verbatim sourcing ends that loop.

**Two options were considered for how to apply the fix:**

- *Model A* — Replace wasteland flavor names (`scrap_armor`, `sawed_off`) with AWN canonical names (`Scrap Mail`, `Shotgun`). Cleaner in the abstract, but would break every character creation preset that references the old names by id.
- *Model B (chosen)* — Keep the wasteland flavor names. Stamp each item as a reskin of its AWN source, with the AWN mechanics reproduced verbatim underneath. The `scrap_armor` id survives; AC 15 appears beneath the wasteland skin.

Model B was the right call because it delivered the fix without a cascading rewire of character creation references, and it's explicitly permitted by the project's inventory ADR.

**On licensing:** The original story context said AWN gear should be *derived* (paraphrased), not reproduced. During the test design phase, this was corrected: Sine Nomine Publishing's free-use terms allow verbatim reproduction of the rulebook's equipment statistics. The change sources gear verbatim with proper attribution and an explicit non-endorsement disclaimer in the file header.

---

## Before/After
| | Before | After |
|---|---|---|
| **`scrap_armor` AC** | None (no `armor_class` field) | **15** (AWN Scrap Mail, verbatim) |
| **GM panel span when equipping armor** | `chargen.armor_unresolved` (gap signal) | `chargen.armor_equipped` with `armor_class=15` in attrs |
| **Character AC after equipping** | 10 (bare default) | **15** |
| **`sharpened_rebar` (Spear)** | 1d6 damage, no trauma fields, no shock | 1d6, `trauma_die: 1d8`, `trauma_rating: 3`, `shock: 2`, `shock_ac: 13` |
| **`pipe_wrench` (Club)** | 1d6 damage, no trauma fields, no shock | **1d4** (AWN Club), `trauma_die: 1d6`, `trauma_rating: 2`, `shock: 1`, `shock_ac: 18` |
| **`crossbow_salvage` (Primitive Bow)** | 1d8 damage, no trauma fields | **1d6** (AWN Primitive Bow), `trauma_die: 1d8`, `trauma_rating: 3`, range `20/100`, mag 1 |
| **`sawed_off` (Shotgun)** | 3d4 damage, no trauma fields | 3d4, `trauma_die: 1d10`, `trauma_rating: 3`, range `10/30`, mag 2 |
| **Item provenance** | None — no attribution, no license, no sourcing | `mode: verbatim, srd: awn, license: wn-free, srd_ref: "AWN SRD Equipment — ..."` on each item |
| **Test coverage** | Zero tests for this pack's inventory wiring | 11 tests: provenance, trauma fields, AC derivation end-to-end, OTEL span, power_glove regression guard |
| **`power_glove` at chargen** | Present in offer list, missing from catalog → silent weapon fallback | Present in both genre and world catalog; non-droppable merge ensures it survives (confirmed by regression guard) |
