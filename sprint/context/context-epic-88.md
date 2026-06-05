# Epic 88: Ashes Without Number — mutant_wasteland ruleset port

## Overview

Faithful port of *Ashes Without Number* (Kevin Crawford / Sine Nomine, 2025) as the **fourth Without-Number sister module**, binding `mutant_wasteland` to a thin `awn` ruleset. AWN personal combat is mechanically identical to CWN — the engine already contains the entire combat substrate. The epic is decomposed **foundation-first**: Plan 1 (ruleset binding + ablative-HP personal combat) is seeded as stories 88-1 (engine, **done**) and 88-2 (content, backlog); Plans 2–7 (the genre-identity layers) get stories when their specs land.

This is an *instance* of ADR-117 (Pluggable Ruleset Module System) inheriting ADR-114 (Ablative HP) — **no new ADR** (spec §11.3).

**Priority:** P2
**Repo:** server, content
**Stories:** 2 seeded (8 points) — Plan 1 only; Plans 2–7 add stories as specs land

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **AWN design spec** (`docs/superpowers/specs/2026-06-05-ashes-without-number-mutant-wasteland-design.md`) | §1–4 problem/decisions/combat math · §5 genre-layer shapes · §6 Plan 1 design · §8 epic decomposition · §11 Architect Addendum (seam analysis, MUST-change list, story split) |
| **Road-warrior CWN precedent** (`docs/superpowers/specs/2026-06-04-road-warrior-cwn-rig-combat-design.md`) | The shape AWN follows verbatim: existing pack → sister module binding + genre layer |
| **CWN module design** (`docs/superpowers/specs/2026-05-28-neon-cwn-ruleset-design.md`) | CWN subclasses SWN; AWN subclasses CWN |
| **SWN crunch / ablative HP** (`docs/superpowers/specs/2026-05-25-swn-crunch-ablative-hp-design.md`) | The mandate this epic realizes for mutant_wasteland |
| **ADR-117** (`docs/adr/117-pluggable-ruleset-modules.md`) | RulesetModule seam; recommended amendment re: capability gates vs slug strings (spec §11.3) |
| **ADR-114** (`docs/adr/114-ablative-hp-substrate.md`) | HP lethality track beneath the dials |
| **Source SRD** | *AWN Free Edition* PDF (local, see spec header) — printed-page cites inline in spec |

## Background

`mutant_wasteland` runs the `native` dial engine. Its combat — the "Wasteland Brawl" momentum-to-7 confrontation — has no lethality substrate: no HP, no Shock, no Trauma, no death state. This is precisely the absence the two mechanics-first players (**Sebastien and Jade**) named after the broken-engine `coyote_star` session: a narrator improvising combat with nothing mechanical underneath, and no `confrontation.*` spans firing.

Meanwhile AWN's System Quick Reference confirms AWN combat **is** CWN's resolution verbatim — and CWN is fully built in the engine (`CwnRulesetModule`: attack/check/save params, Shock, Trauma, System Strain, Mortal/Major Injury). The gap is **binding and wiring**, not mechanics — "Don't Reinvent — Wire Up What Exists."

**Locked decisions (spec §3, with Keith, 2026-06-05):**

| # | Decision |
|---|----------|
| D1 | Full faithful port, decomposed into sub-projects (spec → plan → PR each) |
| D2 | Foundation-first build order — Plan 1 gates everything |
| D3 | Thin `awn` module: `AwnRulesetModule(CwnRulesetModule)`, slug `"awn"` (honest slug + future-hook home) |
| D4 | Adopt the **standard six** attributes (STR/DEX/CON/INT/WIS/CHA); drop Brawn/Reflexes/Toughness/Wits/Instinct/Presence — requires exhaustive content sweep |
| D5 | Mutations = bespoke `MutationPlugin`, **not** the ADR-126 MagicPlugin seam |
| D6 | Faithful SRD port, no redesign |

## Technical Architecture

**Engine (88-1, done — sidequest-server PR #682):** `AwnRulesetModule(CwnRulesetModule)` in `sidequest/game/ruleset/awn.py`, registered in the ruleset registry; `AwnConfig(CwnConfig)` + `_validate_awn` in `sidequest/genre/models/rules.py`; six slug-string binding sites converted/loosened so awn rides the CWN seams (chargen strain pool, downed seam, stabilize/strain tools). The load-bearing finding (spec §11.1): the engine keys ruleset behavior two ways — **capability/isinstance** (free for a thin subclass) and **slug-string membership** (silent fall-through; each site must be taught `awn`).

**Content (88-2, backlog):** `rules.yaml` gets `ruleset: awn` + `awn:` config block; standard-six rename; "Wasteland Brawl" momentum confrontation → `hp_depletion` combat confrontation; the §6.3 standard-six sweep across pack files; retire the `magic_level` flag.

**OTEL:** Plan 1 reuses the inherited `cwn.*` spans (`cwn.shock.applied`, `cwn.trauma.roll`, `cwn.mortal_injury.declared`, `cwn.major_injury.roll`, `cwn.system_strain.delta`) + `state_patch_hp`. AWN-specific spans (`awn.mutation.*`, `awn.radiation.*`, `awn.stress.*`) arrive with their owning genre-layer plans.

### Roadmap — Plans 1–7 (spec §5, §8)

Each plan is its own spec → plan → PR cycle. Plan 1 gates the mechanical meaning of everything below it. GM owns content lanes; engine lanes route to Architect/Dev through the sprint system.

| # | Plan | Lane | Engine shape | Depends on | Status |
|---|------|------|--------------|------------|--------|
| 1 | `awn` module + binding + ablative-HP combat | engine + content | Thin subclass; no new math | — | 88-1 done; 88-2 backlog |
| 2 | **Mutations** (marquee) | engine + content | Bespoke `MutationPlugin` (D5): MP economy, Stigma, ~40 negative + 60 positive powers, Strain-coupled costs, per-scene/day counters. **Net-new, no analog.** Must reconcile with pack's existing `magic.yaml` framing (spec §7 — Architect call in Plan 2 spec) | 1 | Spec not written |
| 3 | Radiation + Disease (+ Poisons) | engine + content | Periodic-save status tracks; CON attrition; rad-mutation hook links to Plan 2. **Net-new** (Radiation) / semi-net-new (Disease) | 1 | Spec not written |
| 4 | Stress → Breakdown → Hardening/Scars + Addiction | engine + content | Stress pool vs Wisdom; Addiction strictly requires Stress. Genre-gated → lower priority | 1 | Spec not written |
| 5 | Survival hexcrawl (travel/track/forage/hunger) | engine + content | WWN-adjacent, expanded; privation Strain | 1 | Spec not written |
| 6 | Creatures of the Wastes + nemesis traits | content + thin code | AWN bestiary as Monster Manual content (ADR-059); nemesis traits as thin death-override layer | 1 | Spec not written |
| 7 | Enclaves & Settlements faction sim | engine + content | Power/Cohesion/Action-Die monthly turn; **verify against existing faction/disposition systems before building** | — (parallel) | Spec not written |

**Open items handed forward (spec §7):** Mutations ↔ `magic.yaml` reconciliation (Plan 2 Architect call) · AWN-specific OTEL span files (per owning plan) · `flickering_reach` combat-content recalibration to ablative HP (world-layer pass after Plan 1; **spoiler discipline** — its lore must not leak into foundation specs/reviews).

**Known debt (spec §11.3):** slug-string capability gates require editing on every new sister module (fourth module now). Recommended ADR-117 amendment: key cross-cutting gates on config/module type or method-override probes, not `rules.ruleset` slug membership. Targeted capability-form fixes landed in 88-1; full consolidation deliberately deferred (pragmatic restraint).

## Cross-Epic Dependencies

**Depends on:**
- ADR-117 ruleset module system (live) — the seam `awn` plugs into
- ADR-114 ablative HP substrate (partial) — the lethality track beneath `hp_depletion`
- CWN module (neon_dystopia) + road-warrior binding precedent — the seams 88-1 verified rather than rebuilt

**Depended on by:**
- Plans 2–7 above (all gate on Plan 1 except Plan 7)
- `flickering_reach` world recalibration (post-Plan-1 world-layer pass)
- Epic 73 (Confrontation Engine Hardening) — gains a fourth ruleset-bound combat pack to verify against
