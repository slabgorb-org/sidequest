---
story_id: "150-14"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-14: [PLAYTEST] heavy_metal/evropi — full-stack verify (wwn)

## Story Details
- **ID:** 150-14
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore
- **Repos:** ui, server, content, daemon

## Overview

Full-stack `/sq-playtest` verification of `heavy_metal/evropi` (ruleset: Worlds Without Number / WWN, ADR-143).
Run via `/pf-gm` as the playtest DRIVER (oq-3); findings routed to FIXER via `~/Projects/sq-playtest-pingpong.md`.

**KNOWN-RED caveat (baked into scope):**
The WN-owns-the-round combat work (epic-108 / ADR-143) is **in-flight and currently RED** (empty beat-pool). A combat verify will **likely surface that KNOWN breakage**. Scope is to **confirm the symptom from the player seat** and **attribute it to epic-108**, NOT a new regression in 150-14.

## Acceptance Criteria (from sprint YAML)

1. World loads, connects, and chargen completes through the real UI. — **VERIFIED ✅**
2. A multi-turn session runs end-to-end; per-world state renders (ablative HP pool, gear/inventory). — **VERIFIED ✅**
3. Seat combat: the Without-Number engine engages — ablative HP (HpPool), hp_depletion win condition, state_patch_hp spans. — **PARTIAL ⚠️ (epic-108 carve-out)**
4. WWN magic engages (Effort/spellcasting, magic.* spans) — ADR-126. — **PARTIAL ⚠️ (logged-not-resolved)**
5. KNOWN-RISK (epic-108 / ADR-143): empty confrontation beat-pool is EXPECTED — confirm + attribute to epic-108. — **DOCUMENTED ✅**
6. Narration is genre-true; no dead UI controls; findings filed via ping-pong to FIXER. — **VERIFIED ✅**

## Workflow Tracking
**Workflow:** trivial
**Phase:** implement

## Branch Strategy

**Orchestrator:** trunk-based (no feature branch — work on main; subrepos separate). This story's work is VERIFICATION (playtest), not code; any fixes land in subrepos via FIXER.

## Sm Assessment

**Routing decision: full-stack playtest → GM DRIVER (`/pf-gm`), not standard Dev.** Same pattern as completed siblings 150-11/150-12/150-13, all PASS w/ epic-108 carve-out. Merge gate clear at start. Story 150-3 left untouched (in_progress, held on FIXER).

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### GM DRIVER playtest closeout (2026-06-20, slug 2026-06-20-evropi-3b24b221, PC Vask — Sestayty Pact-born caster)

Full-stack `/sq-playtest` via `/pf-gm`. Stack: server+ui+content+daemon all on `develop`, current; daemon UP/`ready` (live scene renders). Findings filed to ping-pong (150-14 block). Screenshots `oq-3/playtest-shots/150-14-evropi-0[1-2]-*.png`.

**Verdict: PASS w/ epic-108 combat carve-out + WWN-magic logged-not-resolved (confirm) — mirrors siblings 150-11/150-12/150-13.**

- **AC1 — load/connect/chargen:** ✅ GREEN. Lobby cover (R2) + 6-step narrative funnel chargen (origin/pronoun/mark/bond/purpose/seal) → correct WWN sheet (CHA 14/+2 caster; HP 10/10 ablative ♦; stored `hp {10,10,10}`).
- **AC2 — multi-turn + per-world state:** ✅ GREEN. Opening + spell turn narrated (excellent grimdark prose). **World-skinned inventory** (Mistos gear + Spellbook: Tismenni Corpus Vol. III) — evropi authors bespoke loadouts. 12-NPC conlang roster + 5-NPC scene pool, all named/world_authored.
- **AC3 — WWN combat engages:** ⚠️ PARTIAL / epic-108. Spell-triggered combat seated (`win_condition: hp_depletion`) but wedged `structured_phase: Setup, beat: 0, wn_commits: []`. Attributed to epic-108/ADR-143. **OTHER-seating mis-seated** ("Mistos Warden" 23/23 vs the Daggereyes I attacked, which were in-roster 14/14 & 5/5) — clean WWN-OTHER-SEATING repro (vague target → MM grab; contrast barsoom's correct seat on a named target).
- **AC4 — WWN magic engages:** ⚠️ PARTIAL / advanced WWN-MAGIC-LOGGED-NOT-RESOLVED. Lance of Darkness: cast **logged** (`wwn_spell_cast_log`) + **casts_remaining 2→1**, but **no Effort commit, `magic_state: null`, no damage** (all targets full HP; narrator improvised the kill). Cast accounting fires; resolution does not. Engine-wide ADR-126/epic-108 gap, not evropi content.
- **AC5 — epic-108 known-risk:** ✅ DOCUMENTED (see AC3).
- **AC6 — narration / no dead UI / findings filed:** ✅ GREEN. Genre-true grimdark prose; no name-collision; no narration-leak (barsoom leak did not recur); only "dead control" is the beat-locked input (= epic-108 wedge). Findings filed.

**NEW finding filed:** `EVROPI-MISSING-PORTRAITS` (low — 5/32 picker portraits 404 on CDN: vaermm_copyist_f01, zked_daggereye_f01, gnome_tunnelwise_f01, half_orc_minehand_m01, antman_scoutdrone_m01; likely render-local-not-synced-to-R2). Confirm-only: quest-minting gap (epic-117; chargen drive → `quests: []`), stale "Adventurer" location key.

**Per-world evropi health is GREEN.** Remaining reds (AC3 wedge, AC4 magic) are engine-wide (epic-108 / ADR-126), filed + attributed.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
