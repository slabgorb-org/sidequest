---
parent: context-epic-121.md
---

# Story 121-2: F4b — pulp_noir Fate migration (pilot)

## Business Context

F4b is the pilot pack for the Fate Core migration (ADR-144). It proves that the F4a engine spine (chargen seeding, FateSheet provisioning, fate_conflict routing) works end-to-end by authoring pulp_noir as a fully Fate-bound pack. Pulp_noir is the ancestral home of Fate — the genre predates most TTRPG systems and is a natural fit for Fate Core's narrative-crunch balance.

The task is *content authoring, not engine work*. F4a (121-1) laid the engine spine; 121-2 uses it to prove the pattern scales to real content. The acceptance criteria all hinge on the engine wiring from 121-1 being live.

## Technical Guardrails

- **Pack location:** `sidequest-content/genre_packs/pulp_noir/`
- **Files to author/modify:**
  - `rules.yaml` — set `ruleset: fate` (currently native-bound)
  - `rules.yaml` — author `fate:` section with:
    - Skill list (Investigate, Contacts, Deceive, Shoot, Notice, Rapport, Physique, Will, Athletics, Burglary, Drive, Empathy, Fight, Lore, Provoke, Stealth — ~15 skills typical of hard-boiled settings)
    - Stunt catalog (pulp-thematic, e.g., "Faster Than a Speeding Bullet," "Dead Detective," "Loose Cannon")
    - Refresh default (typically 3)
  - `archetypes.yaml` — author per-archetype starting-aspect templates (high concept + trouble pairs for each archetype; free aspects seeded in play)
  - `magic.yaml` — strip or reconcile (pulp has no magic; archive the file or gutcheck against the native system to ensure nothing load-bearing exists)
  - Pack README — note ruleset binding, record any content notes for future Fate packs

- **Reconcile/strip native config:**
  - `rules.yaml`: remove `power_tiers`, `progression_beats`, `char_creation` (native d20 bits)
  - Classes (if present): reconcile or strip — Fate uses skills+aspects+stunts, not classes
  - Ensure the pack can be loaded without d20-shaped attributes (e.g., ability scores, hit dice)

- **No engine changes.** If the acceptance criteria fail, the problem is F4a incomplete — do not patch F4a from F4b. Report the finding and escalate to 121-1 rework.

## Scope Boundaries

**In scope:**
- Author fate: skill list, stunt catalog, refresh
- Author per-archetype aspect templates (high concept + trouble)
- Strip/reconcile native config (power_tiers, progression, d20 bits)
- Update pack README + rules.yaml ruleset binding
- Validate with `sidequest-validate`

**Out of scope:**
- Interactive Fate chargen (F4a2/F4a3, later epic)
- Engine wiring (F4a responsibility)
- UI updates
- Balancing beyond "reasonable defaults" (tuning happens in play, post-pilot)

## AC Context

| AC | Detail |
|----|--------|
| Pack loads | `sidequest-validate` passes on the pulp_noir pack (no schema errors, rules.yaml parses, fate: section valid) |
| FateSheet populated | A created PC has `fate_sheet` populated (not None) with skills, aspects, stunts from the seeded defaults + archetype |
| Fate action routes | A Fate action (e.g., Overcome/CreateAdvantage) resolves through `fate_conflict` (not native), verified via OTEL span `fate.conflict.resolved` + GM-panel inspection |
| Native config stripped | `power_tiers`, `progression_beats`, native d20 bits removed; pack does not require ability scores or hit dice |
| Acceptance criteria from F4a live | F4a's wiring test passes with pulp_noir as the test pack (prerequisite to starting 121-2) |

## Acceptance Criteria Detail

**AC1: Pack loads + sidequest-validate passes**
- Run `sidequest-validate pulp_noir` from the sidequest-server root
- No schema errors, no missing required fields, no malformed YAML
- `rules.yaml` has `ruleset: fate` and a valid `fate:` section

**AC2: FateSheet populated on character creation**
- Create a new character in pulp_noir through the normal chargen flow
- Inspect the CreatureCore in OTEL or the client state: `fate_sheet` is not None
- `fate_sheet.skills` has entries (at least the seeded defaults: Investigate, Shoot, Notice, Contacts, Deceive, Rapport, Physique)
- `fate_sheet.aspects` has high-concept + trouble + any free-aspect defaults from the archetype template
- `fate_sheet.refresh` > 0

**AC3: Fate action resolves through fate_conflict**
- In-play: a player takes a Fate action (Overcome, CreateAdvantage, Attack, Defend, or a custom action bound to Fate)
- OTEL span `fate.conflict.resolved` is emitted
- GM-panel CharacterState / Confrontation view shows the action routed to `fate_conflict` (not native resolution)
- Combat proceeds via Fate mechanics (skill vs skill, outcome tracked in `fate_sheet`, aspects compelled on failure/tie, stress/consequences model active)

**AC4: Native config stripped**
- Review `rules.yaml`: `power_tiers`, `progression_beats`, `char_creation` (native d20 bits) are not present
- Review pack structure: no artifact files that encode native assumptions (e.g., d20-class-to-feat mappings)
- If `magic.yaml` exists: either stripped or gutchecked + reconciled against Fate (pulp has no magic, so stripping is likely correct)

**AC5: F4a wiring test passes with pulp_noir**
- 121-1 includes a mandatory wiring test: a real chargen run + PC builder produces a populated FateSheet + Fate action resolves
- That test MUST pass with `ruleset: fate` bound to `pulp_noir` (not a placeholder)
- Failure here blocks 121-2 from passing — escalate to 121-1

## Dependencies

- **Depends on:** 121-1 (F4a — Fate chargen-seeding spine)
  - Cannot start until 121-1 is complete and its wiring test passes
  - If F4a is incomplete, 121-2's acceptance criteria cannot be met
