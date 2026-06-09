---
story_id: "100-5"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 100-5: Phase 1 — Lore Timeline section JSON projection

## Story Details
- **ID:** 100-5
- **Jira Key:** (none — SideQuest uses sprint YAML, not Jira)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-09

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-09 | - | - |
| red | 2026-06-09 | - | - |

## Repos
- sidequest-server (feat/100-5-lore-timeline-section-projection)

## Branch Strategy
gitflow (feat/100-5-lore-timeline-section-projection)

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

- **[TEA, 2026-06-09] Keeper legend field = `related_tropes`.** The 100-5 firewall
  needs a keeper field on a legend, but `Legend` is a typed pydantic model with
  `extra="forbid"` — you cannot author an arbitrary `gm_notes`/`secret` (load fails
  loud). So the firewall targets the ACCEPTED-but-keeper typed field. Chose
  `related_tropes` (dormant-trope spoiler seeds, named as the legend spoiler axis in
  `reference_timeline.py`'s docstring / ADR-135 D1). Verified in RED that
  `related_tropes` currently LEAKS via the generic-YAML `legends` path (`legends` is a
  PUBLIC stem; `legends.yaml` ∈ LORE_WORLD_FILES, ∉ EXCLUDED_FILES). Dev must (a)
  allowlist the Timeline section builder to slug/name/summary/temporal, and (b) carve
  `classify()` KEEPER for the spoiler legend field so the generic path can't leak it.
- **[TEA, 2026-06-09] Timeline section JSON shape.** Pinned
  `build_timeline_section(legends, *, history_prose) -> dict | None` returning
  `{"id":"timeline","label":"Timeline","sort_mode":"sorted"|"authored_order",
  "preamble":str|None,"entries":[{"slug","name","summary","temporal"}]}` — a single
  `entries` list with the dated spine first (ascending iff every dated entry is a clean
  signed-int year, else authored order) then undated (`temporal:None`) in authored
  order. Diverges from the HTML presenter's two-group (dated `<ol>` + "Undated" `<div>`)
  layout: one ordered list is more React-friendly and makes "undated follows dated"
  directly assertable. sort_mode reuses the shipped `reference_timeline_rendered` span.
