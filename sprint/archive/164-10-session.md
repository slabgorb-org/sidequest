---
story_id: "164-10"
jira_key: ""
epic: ""
workflow: "architecture"
---
# Story 164-10: Design a lightweight bounded-site interior path — a genre-default/minimal cookbook (or light generator) so tavern/vault archetypes materialize from YAML without the megadungeon cookbook/corpus/themes/world_register stack; fix movement.py uncaught FileNotFoundError on missing interior content. Unblocks 164-7 (Track B B2 e2e)

## Story Details
- **ID:** 164-10
- **Jira Key:** (none — architecture workflow, Jira not in use)
- **Workflow:** architecture (stepped)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** architecture
**Phase:** setup
**Phase Started:** 2026-07-10T20:27:23Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T20:27:23Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Architect (state reconciliation — 2026-07-11)
- **Gap** (non-blocking): Workflow bookkeeping is stale — this session reads `Phase: setup` and the generic `architecture-workflow-session.md` reads step 1, but the actual work is complete. Design (ADR-157 + three-tier spec §1/§5 amendment + 1016-line implementation plan) is committed on orchestrator `main` (2 commits, unpushed: `9c3d1fc0`, `d63f05e2`). Implementation is complete and pushed on `sidequest-server:feat/164-10-bounded-site-interior-path` (6 commits, in sync with origin), and faithfully honors all four ADR-157 decisions (verified in `materializer.py::materialize_bounded` — geometry stages + structural finalize only, `hazard_setpieces=[]`/`creature_count=0`, no curate/attach; `agents/subsystems/movement.py:534-601` — bounded branch is cookbook-free with a broad loud-but-recoverable `except` emitting `site.enter_unresolved` + ERROR log, no dispatch re-raise). Tests green: 11 passed / 0 failed / 7 skipped (skips are env-only — behavioral DB tests need `SIDEQUEST_TEST_DATABASE_URL`). Spec-alignment: **ALIGNED**. *Found by Architect during activation state review.*
- **Gap** (blocking): No PR exists for `sidequest-server:feat/164-10-bounded-site-interior-path` (all-states `gh pr list` → `[]`), and the 2 orchestrator design commits are unpushed. The story is done-but-not-finished — remaining work is integration (push design commits, open + merge the server PR, archive story), which is SM's finish-phase domain. *Found by Architect during activation state review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
