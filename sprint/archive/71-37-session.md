---
story_id: "71-37"
jira_key: ""
epic: "71"
workflow: "tdd"
---
# Story 71-37: Classify person-vs-creature at the NPC invention seam — route beasts to the Monster Manual (ADR-059), not the culture-NPC namer

## Story Details
- **ID:** 71-37
- **Jira Key:** (none — no-Jira project)
- **Workflow:** tdd
- **Type:** bug
- **Points:** 5
- **Priority:** p2
- **Repos:** sidequest-server
- **Base Branch:** develop
- **Feature Branch:** feat/71-37-person-vs-creature-npc-seam

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-04T22:56:52Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04 | 2026-06-04T22:56:52Z | 22h 56m |
| red | 2026-06-04T22:56:52Z | - | - |

## Summary

The NPC invention seam currently routes all NPC-like entities through the culture-NPC Markov namer (ADR-091), which produces person names. This causes creatures and beasts to receive inappropriate person names instead of being routed through the Monster Manual (ADR-059) pregeneration path.

The fix requires classifying entities at the seam: route `person` class to the culture namer, route `creature`/`beast` class to Monster Manual.

## Related ADRs

- **ADR-059** — Monster Manual: Server-Side Pre-Generation via Game-State Injection
- **ADR-091** — Culture-Corpus + Markov Naming
- **ADR-014** — Diamonds and Coal (creature/item schema)

## Acceptance Criteria

1. Creature and beast entities are routed to the Monster Manual pregeneration path instead of the culture-NPC namer at the NPC invention seam.
2. Person-class NPCs continue to be routed through the culture namer as before.
3. Add test coverage for both paths (person → culture namer, creature/beast → Monster Manual).

## Sm Assessment

**Setup complete — routing to TEA (Igor) for RED.**

This is a 5pt bug in epic 71 (the playtest-bugfix residue bucket). The defect is a
classification gap at the NPC invention seam: when the narrator invents an entity,
everything is currently funneled through the culture-NPC Markov namer (ADR-091),
so creatures and beasts come out with *person* names instead of being routed to
the Monster Manual pregeneration path (ADR-059). The fix is a classification step
at the seam — `person` → culture namer (unchanged), `creature`/`beast` → Monster
Manual.

**For Igor (RED):**
- Single repo: `sidequest-server`, branch `feat/71-37-person-vs-creature-npc-seam`
  off `develop`. No Jira (personal project).
- Find the actual invention seam before writing tests — locate where invented NPC
  entities are handed to the culture namer vs. where the Monster Manual
  pregeneration path (ADR-059, `world_materialization`/Monster Manual injection)
  is invoked. The classification decision needs a home; the RED tests should pin
  the routing on both branches.
- Write the wiring test the project mandates: prove the classifier is actually
  *called* at the seam from a production path, not just unit-correct in isolation.
- Watch for the gaslighting doctrine (`project_narrator_gaslighting_doctrine`):
  creatures are materialized into `snap.npcs`/snapshot, and ADR-014 requires the
  HP→Edge translation at the materialization seam — don't let the creature path
  regress that.
- Per the OTEL principle, the routing decision should emit a watcher span
  (person vs creature classification) so the GM panel can verify the seam engages.

**Quality bar:** gate on the FULL server suite with `SIDEQUEST_DATABASE_URL` and
`SIDEQUEST_GENRE_PACKS` set (a "~33 MissingDatabaseUrlError" first pass is the
env tell, not a regression). Record the baseline before claiming any failure is new.

## TEA Assessment

**Tests Required:** No — **story cancelled in RED as overtaken-by-ping-pong-#74.**
**Phase:** red (no tests written)

**What I measured (not asserted):**
- The classification half of this story is **already live on `develop`**, landed
  under a *different* story — commit `bab642a3` *"fix(npc): reserve culture namer
  for people; preserve creatures (ping-pong #74)"* (PR #638).
- The seam branch exists at `sidequest/server/narration_apply.py:1835`
  (`if mention.is_creature:`): creatures skip the ADR-091 culture-NPC namer, keep
  the narrator's descriptive name verbatim, and emit the `npc.creature_preserved`
  OTEL lie-detector span. The `is_creature` flag is carried on `NpcMention`
  (`orchestrator.py`) and `NpcPoolMember` (`npc_pool.py`), and the mechanical
  `Npc` materializes it (`session.py:1801`, hostile disposition).
- **Four** dedicated creature tests already exist and **all pass** (verified
  `4 passed in 0.18s`, `-n0`):
  `test_creature_mention_preserves_name_and_skips_namer`,
  `test_creature_mention_emits_creature_preserved_span_not_routed`,
  `test_person_routed_creature_preserved_in_same_turn`,
  `test_creature_preserved_with_no_culture_bound`
  (`tests/server/test_npc_invented_namegen_routing.py`).

**Scope mapping (story title → reality):**
| Clause | Status |
| --- | --- |
| "Classify person-vs-creature at the NPC invention seam" | DONE (#74) |
| "...not the culture-NPC namer" | DONE (#74) — 4 green tests |
| "route beasts to the Monster Manual (ADR-059)" | NOT done — explicitly **deferred** per code comment `narration_apply.py:1842-1844` |

The only residual scope (full Monster Manual *identity* — `creature_id`/`threat_level`/
HP/stat-block for narrator-invented beasts) is **under-specified** (no mechanism for
mapping an arbitrary invented beast to a bestiary entry / no-match / generate-new-block
semantics) and is properly an ADR-059 design follow-up, not a RED-able bug.

**Decision (Keith, 2026-06-04):** Cancel 71-37 as overtaken-by-#74. No RED tests
written (writing them would duplicate the 4 already-green creature tests). Routing to
SM to set status `canceled` and clean up the empty feature branch.

## Delivery Findings

<!-- Findings appended below this marker. Append-only; never edit another agent's entry. -->

### TEA (test design)
- **Conflict** (blocking): Story 71-37's classification premise is already satisfied
  on `develop` by ping-pong #74 (commit `bab642a3`, PR #638) with 4 passing tests.
  No RED state is reachable for the stated scope. Affects sprint tracking only — no
  code change. The deferred remainder (ADR-059 Monster Manual identity routing for
  invented beasts) is real but under-specified; if Keith wants it later it needs an
  Architect design pass before TDD, filed as a fresh story. *Found by TEA during test design.*

## Design Deviations

### TEA (test design)
- No deviations from spec — story cancelled before any test was written.