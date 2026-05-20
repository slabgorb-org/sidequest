---
story_id: "24-2"
jira_key: ""
epic: "24"
workflow: "trivial"
---

# Story 24-2: Author tea_and_murder/glenross weather rules (climate zones, seasonal conditions, special events)

## Story Details

- **ID:** 24-2
- **Jira Key:** (none — SideQuest does not use Jira)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** trivial
**Phase:** setup
**Phase Started:** 2026-05-20T10:32:50Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-20T10:32:50Z | - | - |

## Sm Assessment

**Context:** Story 24-2 is Phase 1 of Epic 24 (Procedural World-Grounding Systems). This story author a weather YAML configuration for the tea_and_murder/glenross world, following the Monster Manual pattern (ADR-059). The schema definition itself (story 24-1) is a prerequisite, but content authoring can proceed in parallel once the epic context is understood.

**Target deliverable:** A `weather.yaml` file in `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/` containing:
- Climate zone definitions (e.g., rolling moorlands, highlands, lowlands, coastal marshes if applicable to glenross geography)
- Seasonal conditions and transitions (glenross seasons mapped to Glenross calendar if available in world.yaml or lore)
- Special weather events (storm patterns, fog conditions, seasonal phenomena unique to the region)
- Mechanical grounding (how weather surfaces in narration — flavor text candidates, tension shifts, environmental hazards)

**Scoping notes:**
1. Check `world.yaml` in glenross to understand existing geography, climate tone, and calendar structure
2. Reference `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` for regional divisions (climate zones should map to physical regions)
3. Cross-check with `history.yaml`, `lore.yaml`, and `cultures.yaml` for weather-relevant cultural detail (e.g., how weather affects NPCs or settlements)
4. Trivial workflow: no TDD, no test setup — implement and review in series

**No Jira.** No `--jira` flags. This is content authoring in sidequest-content, not API code.

## Discovery Findings

### Glenross World Context

**Finding: Glenross has established geography, history, and culture; weather authoring is greenfield content.**

Scope: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/`

Glenross is the flagship world for the tea_and_murder genre pack. Existing context includes:

1. **world.yaml** — Contains world metadata, theme, axis_snapshot (emotional tone axes), and visual description
2. **cartography.yaml** — Detailed region divisions (36KB file, suggesting rich geography; presume multiple climate zones per cartography definitions)
3. **history.yaml** — 35KB history file; may contain seasonal/climate-relevant narrative detail
4. **cultures.yaml** — 2KB summary; points to cultures/directory with per-culture detail (4 cultures)
5. **lore.yaml**, **legends.yaml** — Environmental and cultural lore; may reference seasonal/weather phenomena
6. **npcs.yaml**, **portrait_manifest.yaml** — NPC and asset manifest; may flag NPCs with weather-dependent routines
7. **openings.yaml** — 76KB opening narrations; potential template text for weather-grounded prose style

**No existing weather.yaml** — Confirmed. Greenfield authoring.

**Climate inference from existing files:**
- Tea_and_murder is cosy/gothic mystery genre — weather likely emphasizes fog, damp, seasonal gloom, tea-shop ambiance
- Glenross likely has moorland or coastal climate (Scottish aesthetics); presume cold winters, damp springs, short summers, extended autumns
- Multiple regions in cartography suggest climate variation (highlands ≠ lowlands; coast ≠ interior)

**Type:** Discovery finding — greenfield scope, existing context confirmed
**Urgency:** non-blocking (normal scope clarification)

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No deviations documented at setup.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup.
