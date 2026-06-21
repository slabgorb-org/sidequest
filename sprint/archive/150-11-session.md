---
story_id: "150-11"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-11: [PLAYTEST] elemental_harmony/burning_peace — full-stack verify (wwn)

## Story Details
- **ID:** 150-11
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore
- **Repos:** ui, server, content, daemon

## Overview

Full-stack `/sq-playtest` verification of `elemental_harmony/burning_peace` (ruleset: Worlds Without Number / WWN, ADR-143).
Run via `/pf-gm` as the playtest DRIVER (oq-3); findings routed to FIXER via `~/Projects/sq-playtest-pingpong.md`.

**KNOWN-RED caveat (baked into scope):**
This story carries a deliberately-held p3 status and documented known breakage. The WN-owns-the-round combat work (epic-108 / ADR-143) is **in-flight and currently RED** (empty beat-pool). A combat verify will **likely surface that KNOWN breakage**. The scope is to **confirm the symptom from the player seat** and **attribute it to epic-108**, NOT a new regression in 150-11. Do not file it as a fresh bug; reference epic-108.

**Positive verification scope (expected GREEN):**
- Per-world burning_peace health: world loads, connects, chargen completes, multi-turn narration runs, UI renders.
- WWN engine engages for combat (ablative HP, hp_depletion, state_patch_hp OTEL spans) to the extent epic-108 allows.
- Elemental magic (ADR-126 MagicPlugin): exercise a magic working and confirm the magic subsystem engages (spans fire, not narrator improvisation).

## Acceptance Criteria (from sprint YAML)

1. World loads, connects, and chargen completes through the real UI. — **To Verify**
2. A multi-turn session runs end-to-end; per-world state renders (ablative HP pool, gear/inventory). — **To Verify**
3. Seat combat: the Without-Number engine engages — ablative HP (HpPool), 0-HP triggers hp_depletion win condition, state_patch_hp OTEL spans fire. — **To Verify** (expect epic-108 breakage)
4. A magic working dispatches and magic.* / magic_working OTEL spans fire (ADR-126 MagicPlugin). — **To Verify**
5. KNOWN-RISK (epic-108 / ADR-143): WN-owns-the-round is in-flight; an empty confrontation beat-pool (PackError: encounter_beat_choices ... not in pool) is the EXPECTED pre-existing breakage — confirm the player-seat symptom and attribute to epic-108, NOT a new 150 regression. — **To Document**
6. Narration is genre-true; no dead UI controls; findings filed via ping-pong to FIXER. — **To Verify**

## Workflow Tracking
**Workflow:** trivial
**Phase:** setup
**Phase Started:** 2026-06-20T23:06:19Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T23:06:19Z | - | - |

## Branch Strategy

**Orchestrator:** trunk-based (no feature branch — work happens on main; subrepos are separate)
The orchestrator (this repo) uses trunk-based branching strategy per repos.yaml. The referenced subrepos (ui, server, content, daemon) are gitflow-based and maintain their own feature branches for changes. This story's implementation work is primarily VERIFICATION (playtesting), not code changes; changes will be committed to subrepos as needed.

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

## GM Closeout — VERDICT: PASS-with-carve-out (Keith, 2026-06-20)

Full-stack `/sq-playtest` run as DRIVER (oq-3). PC **Mei**, Lv1 Channeler, Ember Isles, session `2026-06-20-burning_peace-e6f5cbe6`, 6 turns. Stack: server+ui oq-3 develop (current); **daemon DOWN** (new render blocked; pre-rendered R2 assets serve fine). Verified OTEL-first (forensics timeline + stored `/snapshot`, never prose alone — caught the magic logged-not-resolved gap that prose would have passed).

**VERIFIED GREEN (per-world burning_peace health — the real scope):**
- World loads + connect + 5-step narrative chargen → correct **WWN sheet**: 6 reskinned attributes (Agility/Endurance/Harmony/Insight/Spirit/Strength + mods, ADR-142 shaped-attribute retune), **HP 10/10 ablative** (stored `HpPool {current:10,max:10}` ground-truth), Lv1 Channeler.
- Multi-turn (6) genre-true Edo/Sengoku narration, strong pacing/hooks, no dead UI controls, 0 console errors. Monster Manual injects (7 patches/turn), lore_fragments=23, intent_router (haiku) engages each turn, map emits.
- Portraits render from R2 (ukiyo-e, genre-true) despite daemon down.

**CARVED OUT — combat ACs blocked by epic-108 (confirmed, not a 150-11 fault):**
- WWN combat round engine does not fire from the player seat: `total_beats_fired:0`, `encounter:None`, `in_combat:None` on an explicit offensive attack on a present armed antagonist; every `game_patch` `confrontation=None`. The known-red empty-beat-pool symptom (epic-108 / ADR-143), confirmed from the player seat and attributed there. NOT a new regression.

**ROUTED TO FIXER (ping-pong, session block):**
- `[medium]` WWN-MAGIC-LOGGED-NOT-RESOLVED — `cinder_lance` cast logged to `wwn_spell_cast_log` but `magic_state:null`, `resources:{}` (no Effort), no roll/damage/cost resolution; narrator improvises the effect. Magic recognition fires, resolution doesn't (likely gated behind the red encounter engine).
- `[med]` OPENING-REGION-NO-PROPAGATE repro (header "Inn — Hakone" vs shrine narration vs region `edo`, location `None`).
- `[low]` `active_stakes="Channeler"` mis-populated; snapshot `npcs` roster 7 nulls.
- Confirm-only (DO NOT re-file): out-of-encounter fabrication = carried-forward 150-3 MAJOR; NARRATOR-EMPTY-NARRATION-DEGRADED cold-open repro (guard recovered, no hang).

**DISPOSITION:** per-world health GREEN; combat ACs carved out as blocked-by-epic-108 (mirrors 150-8). Cleared to close via SM `finish`.
