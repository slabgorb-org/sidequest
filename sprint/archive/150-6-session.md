---
story_id: "150-6"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-6: [PLAYTEST] tea_and_murder/glenross — full-stack verify (fate)

## Story Details
- **ID:** 150-6
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore

## Overview

Full-stack `/sq-playtest` verification of `tea_and_murder/glenross` (ruleset: Fate Core,
ADR-144). Run via `/pf-gm` as the playtest DRIVER; bugs routed cross-workspace to FIXER via
`/Users/slabgorb/Projects/sq-playtest-pingpong.md`. Completed per Keith's call (150-5
precedent: COMPLETE now with findings routed), overriding the DRIVER HOLD recommendation —
the playtest did its job (surfaced findings); the open subsystem bug is routed, not a reason
to leave the verify story open.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish

## Delivery Findings

Playtest verification of glenross (Fate Core) — full-stack, headed Playwright, solo, session
`2026-06-20-glenross-e347d596`.

**VERIFIED PASSES:**
- Per-world health: hero image + 18 portraits render; chargen completes end-to-end (14-skill
  cosy ladder, legal pyramid); FATE_STATE hydrates (#942, FP3/Refresh3); tone tags
  world-distinct; lore richly specific (Edwardian Glenross).
- content #481 gear→aspect compilation works (closes the 150-1 "0 gear aspects" finding —
  aspects carry `source_gear` provenance).
- Native chrome hidden (126-1/126-3): native inventory rows 0, `core.hp` present-but-hidden
  (ADR-114 substrate); no HP bar in player panel.
- Living World: NPCs named + acting on own goals (Beresford folds, Mrs. Thornfield resists
  then confesses).
- **#440 (ui) + #987 (server is_contest) — VERIFIED:** a live Fate Contest move rack shows
  Overcome / Create Advantage / Concede with **no Attack tile**; a Conflict still shows all four.
- **#988 (a/an article) — verified** via chargen prose.

**FATE CONTEST commit/persist (#936 / server #985) — HALF-LANDED:**
- ✅ Persist confirmed: a SucceedWithStyle Overcome advanced + persisted
  `encounter.contest.player_victories` 0→2 (correct Fate "+2 on SwS"). The original #936 freeze
  is gone at the single-exchange level.
- 🔴 New HIGH blocker found — **`[FATE-CONTEST-NARRATE-CRASH]`** (routed to FIXER): the
  `_narrate_resolved_fate_exchange` seam #985 added crashes every exchange
  (`AttributeError: 'NoneType' object has no attribute 'value'` in `narrator.build_encounter_context`,
  narrator.py:394 — a `social_duel` beat has `kind=None`). Net in play: no exchange narration,
  a `server_error` per throw, the contest wedges and first-to-3 never resolves. This also
  explains the "lingering at N/3, phase Setup, un-narrated" state (it is this live crash, not
  pre-fix residue). Kept #985 `fixed` (not `verified`) pending the crash fix + clean 0→3 re-verify.

**CARRIED-FORWARD / DEFERRED (storied, not re-filed):**
- 126-7 / ADR-148 (free-text skill checks fire no engine roll) reproduces in the cosy
  investigate/social loop — design-gated.
- CLUE-JOURNAL (ADR-053/100): clue_graph populated (11 nodes) but `known_facts=0`.
- 126-17 (seed HC/Trouble placeholder-not-applied), FATE-STRESS flat-2-box question.
- BUG-LOW other-seating (ADR-116): seat = authored "Reverend Montague Thornfield" vs narration
  "Mrs. Thornfield"; **live evidence captured** → confirmed router-prompt classification (not an
  engine token-match). Stays open/deferred for router-prompt work.
- BUG-LOW degenerate seed-quest drive (chargen sets `character.drive` to the vocation label) —
  deferred to a chargen story.

## Design Deviations

No design deviations — this is a playtest verification story (no implementation). Fixes were
shipped via sibling stories' PRs (server #985/#987/#988, ui #439/#440, dice-lib #30); findings
routed to the FIXER ping-pong.
