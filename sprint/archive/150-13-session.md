---
story_id: "150-13"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-13: [PLAYTEST] heavy_metal/barsoom — full-stack verify (wwn)

## Story Details
- **ID:** 150-13
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore
- **Repos:** ui, server, content, daemon

## Overview

Full-stack `/sq-playtest` verification of `heavy_metal/barsoom` (ruleset: Worlds Without Number / WWN, ADR-143).
Run via `/pf-gm` as the playtest DRIVER (oq-3); findings routed to FIXER via `~/Projects/sq-playtest-pingpong.md`.
Newest WWN port (105-2 seam registry + entrance room); brief flagged "portraits still rendering" — to confirm.

**KNOWN-RED caveat (baked into scope):**
The WN-owns-the-round combat work (epic-108 / ADR-143) is **in-flight and currently RED** (empty beat-pool). A combat verify will **likely surface that KNOWN breakage**. Scope is to **confirm the symptom from the player seat** and **attribute it to epic-108**, NOT a new regression in 150-13.

## Acceptance Criteria (from sprint YAML)

1. World loads, connects, and chargen completes through the real UI. — **VERIFIED ✅**
2. A multi-turn session runs end-to-end; per-world state renders (ablative HP pool, gear/inventory). — **VERIFIED ✅**
3. Seat combat: the Without-Number engine engages — ablative HP (HpPool), hp_depletion win condition, state_patch_hp spans. — **PARTIAL ⚠️ (epic-108 carve-out)**
4. Seam registry loads + portraits resolve (105-2 port). — **VERIFIED ✅ (portraits complete)**
5. KNOWN-RISK (epic-108 / ADR-143): empty confrontation beat-pool is EXPECTED — confirm + attribute to epic-108. — **DOCUMENTED ✅**
6. Narration is genre-true; no dead UI controls; findings filed via ping-pong to FIXER. — **VERIFIED ✅**

## Workflow Tracking
**Workflow:** trivial
**Phase:** implement

## Branch Strategy

**Orchestrator:** trunk-based (no feature branch — work on main; subrepos separate). This story's work is VERIFICATION (playtest), not code; any fixes land in subrepos via FIXER.

## Sm Assessment

**Routing decision: full-stack playtest → GM DRIVER (`/pf-gm`), not standard Dev.** Same pattern as completed siblings 150-11 (burning_peace) and 150-12 (shattered_accord), both PASS w/ epic-108 carve-out. Merge gate clear at start (no open non-draft server PRs). Story 150-3 left untouched (in_progress, held on FIXER).

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### GM DRIVER playtest closeout (2026-06-20, slug 2026-06-20-barsoom-ae2e011d, PC Kantos — Red Martian Warrior)

Full-stack `/sq-playtest` via `/pf-gm`. Stack: server+ui+content+daemon all on `develop`, current; daemon UP/`ready` (live scene renders). Findings filed to ping-pong (150-13 block). Screenshots `oq-3/playtest-shots/150-13-barsoom-0[1-4]-*.png`.

**Verdict: PASS w/ epic-108 combat carve-out — mirrors siblings 150-11/150-12.**

- **AC1 — load/connect/chargen:** ✅ GREEN. Lobby cover (R2) + 4-step ERB-faithful narrative chargen → correct WWN sheet (raw 6 attrs CHA/CON/DEX/INT/STR/WIS w/ mods; HP 10/10 ablative ♦; stored `hp {10,10,10}`).
- **AC2 — multi-turn + per-world state:** ✅ GREEN. Opening + 2 social turns narrated (excellent ERB tone); inventory stored/categorized (25 mark + Iron Longsword/Dagger/Chain Shirt/Poultice); 7-NPC authored roster with full WWN stat blocks (Kantos Vah captain, disp 5).
- **AC3 — WWN combat engages:** ⚠️ PARTIAL / epic-108. Seats with full scaffolding (`win_condition: hp_depletion`, initiative [8,8], actors seated, dial-disabled sentinel) but wedges `structured_phase: Setup, beat: 0, wn_commits: []` → no beats → player wedged. Narrator improvised "6 damage" NOT applied (Barith Voros stayed 10/10). Attributed to epic-108/ADR-143, NOT a new regression. **OTHER-seating CORRECT here** (Barith Voros, the named target) — did not reproduce the 150-12 mis-seat.
- **AC4 — seam registry + portraits (105-2):** ✅ GREEN. All 18 picker portraits + PC portrait render from R2 — barsoom portraits are COMPLETE (brief's "still rendering" caution is stale for barsoom). `location_drift_repaired` (#1001) fired.
- **AC5 — epic-108 known-risk:** ✅ DOCUMENTED (see AC3).
- **AC6 — narration / no dead UI / findings filed:** ✅ GREEN. Genre-true ERB prose; only "dead control" is the beat-locked confrontation input (= epic-108 wedge). Findings filed.

**NEW findings filed (not 150-13 blockers):** `WWN-COMBAT-NARRATOR-LEAK` (med — "…6 damage, a clean hit. Now I narrate." meta-text leaked to player prose); `HEAVY-METAL-MISSING-SFX` (low — sword_clash.ogg 404); `NPC-NAME-PCSUBSTRING-SUBSTITUTION` (low — "Kantos Vah"→"you Vah", partly self-induced). Data-oddities (generic kit, stale "Adventurer" key) consolidated with 150-11, not re-filed.

**Per-world barsoom health is GREEN.** Remaining reds (AC3 wedge) are engine-wide epic-108, filed + attributed.

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->
