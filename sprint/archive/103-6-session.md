---
story_id: "103-6"
jira_key: ""
epic: "103"
workflow: "tdd"
---
# Story 103-6: All 17 regions (GM lane) — places/cartography.yaml + encounter tables

## Story Details
- **ID:** 103-6
- **Jira Key:** (not used — personal project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** sidequest-content

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-11T05:46:50.301671Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-11T05:46:50.301671Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

- **Gap / non-blocking — `encounter_tables.yaml` has no runtime consumer post-Rust-port.** A repo-wide grep finds only a *comment* in `sidequest-server/sidequest/game/cookbook/assemble.py:98` referencing its row shape; nothing opens the file. encountergen for AWN worlds (this world) samples `bestiary.yaml` directly via `pack.effective_bestiary` (encountergen.py:811-826), and the world loader does not read encounter_tables.yaml at all. The file was shipped anyway because the story/spec (§12) + build plan explicitly require it and flickering_reach ships one (convention) — it is valid, cross-checked, cliché-clean, and the natural home for region-keyed encounter design / GM prep. **If region-keyed encounter sampling should drive runtime, that is an engine wiring gap → Dev, not a content gap.**
- **Improvement / non-blocking — bestiary is the load-bearing wired file.** Per `GenrePack.effective_bestiary` the world bestiary REPLACES the genre floor (no wasteland_raider bleed-through); for an AWN world a **`creatures.yaml` was deliberately NOT authored** because its presence (encountergen.py:794) would divert sampling away from the bestiary. 37 stat blocks cover all 18 regions + the Corridor.
- **Question / non-blocking — `openings.yaml` (103-8) region_ids must match these cartography slugs.** `_load_single_world` runs `_validate_opening_region_bindings` (loader.py:1304): every opening `setting.region_id` must resolve to a declared cartography node. 103-8 authors openings — it must use the 18 slugs frozen here (no-prefix forms).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

- **18 regions, not 17.** Spec §3 lists 17 regions and Keith locked "all 17." But the already-shipped `saints.yaml` (103-4) names `pioneer_valley` as Saint Emily of Amherst's patron region, and AC4 (cross-file slug consistency) requires every `patron_regions` slug to exist in cartography. Added **The Pioneer Valley** (Amherst/Northampton/Holyoke, Connecticut River) as the 18th region to satisfy the slug contract. Spec §6 already describes Pioneer Valley as Saint Emily's seat — it was simply omitted from the §3 table. All 18 saints.yaml patron_regions now resolve.
- **Region slugs are no-prefix.** Followed `saints.yaml`'s existing slug forms (`whalecoast`, `hudson_valley`, `merrimack_mills`, `catskills`, `adirondacks`) rather than flickering_reach's `the_`-prefixed convention (`the_bright_junction`), because saints.yaml is the already-shipped cross-file contract. Bestiary tags and encounter table keys match.
- **Cliché fixes during authoring:** renamed route "The Drowned Reach Line" → "The Causeway Line" (§11 bans "Reach" coinages — also a flagged personal-overuse word) and creature id `horseman_of_the_hollow` → `horseman_of_sleepy_hollow` (disambiguate from the §11 "Hollow" ban; Sleepy Hollow is the exempt real place).
