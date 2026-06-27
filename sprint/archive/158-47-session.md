---
story_id: "158-47"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-47: WWN caster spell-seeding: heavy_metal caster's prepared damage spell / casts_remaining assertion fails (test_wwn_cast_spell_routes_through_wwn_module)

## Story Details
- **ID:** 158-47
- **Jira Key:** (none — Jira disabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-27T18:00:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T17:58:29Z | 2026-06-27T18:00:26Z | 1m 57s |
| red | 2026-06-27T18:00:26Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): The story PREMISE was a misread. Chargen seeds the
  prepared damage spell + casts correctly; the failing assertion was the *cast spend*,
  because three WWN cast-dispatch tests (heavy_metal/caverns/elemental_harmony) were
  fossils driving the narrator-beat cast-into-combat path that #1050 de-nativized for
  live WN combat (ADR-143). Verified against records: the test predates the firewall and
  was never updated; CI-skipped via the content guard, so it ran red only locally.
  *Found by TEA during test design.*
- **Improvement** (non-blocking): Migrating the elemental_harmony twin exposed a real
  defect — flavor-attribute WN packs (space_opera/EH/neon_dystopia) crash the WN
  throw-stat path (`without_number._stat` looks up canonical INT/STR; flavor-keyed stats
  KeyError, no neutral-10 fallback). Per Keith (2026-06-27), the fix is to drop the
  flavor relabeling and use the shared canonical STR/DEX/CON/INT/WIS/CHA block.
  **Split into story 158-49** (content + server). Scope kept off 158-47.
  *Found by TEA during test design.*

**Final 158-47 scope (after split):** heavy_metal + caverns WWN cast-proof migration to
the production DICE_THROW seam (server-only, independently green, no engine change).
Merged: sidequest-server#1095. The EH cast migration + canonicalization landed under
158-49 (content#510, server#1096).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

## Sm Assessment

**Finding verified live, not OBE.** Before setup I fast-forward-fetched both subrepos:
sidequest-content is synced to origin/develop and `heavy_metal/barsoom/world.yaml` is
present (so the pack loads — this was the prior blocker). sidequest-server was 2 commits
behind; the feature branch is based on a fresh `origin/develop`. The failing test
`test_wwn_cast_spell_routes_through_wwn_module_on_real_heavy_metal` exists on
origin/develop at `tests/integration/test_wwn_heavy_metal_dispatch.py:133`, and no
sibling commit in recent develop history touches the caster spell-seeding — the bug is
real and unresolved.

**Nature of the bug (per the story).** A real heavy_metal WWN caster built via chargen is
expected to be seeded with a `SpellcastingState` whose `prepared` list contains a
discovered damage spell AND `casts_remaining >= 1`. One of those two assertions fails —
chargen does not seed the prepared spell / casts as expected. This is a WWN-binding
spellcasting-seed gap (engine + heavy_metal content), PRE-EXISTING on develop and
explicitly UNRELATED to the 2026-06-27 cold-seat/GM-NOTE/shock fixes (#1086/#1087/#1089).

**TDD discipline.** The failing test already lives on develop. I left the working tree
clean — no implementation or test changes pre-written (diff vs origin/develop is empty).

**Routing.** Phased `tdd` workflow → RED phase → **TEA (The Caterpillar)**. TEA's job in
red: run the repro (`uv run pytest tests/integration/test_wwn_heavy_metal_dispatch.py::test_wwn_cast_spell_routes_through_wwn_module_on_real_heavy_metal -n0 -q`
from sidequest-server), confirm it fails, and pin *which* of the two assertions fails
(prepared-list-empty vs casts_remaining==0) so green has a precise target. Watch for the
WWN doctrine: bind/seed from the ruleset, do not author or hand-balance a native spell path.

**Scope note.** Story repos = sidequest-server only, but the description flags "engine +
content." If the fix turns out to require heavy_metal content YAML (spell registration /
Calling-gated prepared list), Dev should deliver in the right repo and log a Design
Deviation; SM hand-PRs the content side at finish.