---
story_id: "150-12"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-12: [PLAYTEST] elemental_harmony/shattered_accord — full-stack verify (wwn)

## Story Details
- **ID:** 150-12
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore
- **Repos:** ui, server, content, daemon

## Overview

Full-stack `/sq-playtest` verification of `elemental_harmony/shattered_accord` (ruleset: Worlds Without Number / WWN, ADR-143).
Run via `/pf-gm` as the playtest DRIVER (oq-3); findings routed to FIXER via `~/Projects/sq-playtest-pingpong.md`.

**KNOWN-RED caveat (baked into scope):**
This story carries a deliberately-held p3 status and documented known breakage. The WN-owns-the-round combat work (epic-108 / ADR-143) is **in-flight and currently RED** (empty beat-pool). A combat verify will **likely surface that KNOWN breakage**. The scope is to **confirm the symptom from the player seat** and **attribute it to epic-108**, NOT a new regression in 150-12. Do not file it as a fresh bug; reference epic-108.

**Positive verification scope (expected GREEN):**
- Per-world shattered_accord health: world loads, connects, chargen completes, multi-turn narration runs, UI renders.
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
**Phase:** implement
**Phase Started:** 2026-06-21T00:22:48Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T00:19:32Z | 2026-06-21T00:22:48Z | 3m 16s |
| implement | 2026-06-21T00:22:48Z | - | - |

## Branch Strategy

**Orchestrator:** trunk-based (no feature branch — work happens on main; subrepos are separate)
The orchestrator (this repo) uses trunk-based branching strategy per repos.yaml. The referenced subrepos (ui, server, content, daemon) are gitflow-based and maintain their own feature branches for changes. This story's implementation work is primarily VERIFICATION (playtesting), not code changes; changes will be committed to subrepos as needed.

## Sm Assessment

**Routing decision: full-stack playtest → GM DRIVER (`/pf-gm`), not standard Dev.**

This is a `[PLAYTEST]` trivial story. Its `implement` phase is run by the human DRIVER (this clone, oq-3) via `/pf-gm` driving `/sq-playtest` full-stack — the same pattern as the just-completed sibling 150-11 (`elemental_harmony/burning_peace` WWN, PASS with epic-108 combat carve-out, archived `sprint/archive/150-11-session.md`) and the held sibling 150-3 (`spaghetti_western/five_points`). The workflow machinery owns `implement` as `dev`, but for a playtest the GM DRIVER runs it — the marker may relay to `/pf-dev`; the human should instead run `/pf-gm`.

**Why this is starting now (gate clearances):**
- **Merge gate clear** — no open PRs on `sidequest-server` (`gh pr list --state open` → `[]`), so non-draft-PR blocking does not apply.
- This is a **fresh playtest** (no prior run slug). Its closest precedent is 150-11, which passed with the epic-108 combat carve-out; expect a similar shape here.

**DRIVER caveat (read before running):** The combat AC (#3) sits on top of epic-108 / ADR-143 WN-owns-the-round, which is **in-flight and currently RED** (empty confrontation beat-pool: `PackError: encounter_beat_choices ... not in pool`). A combat verify will most likely re-surface that KNOWN breakage. Confirm the symptom **from the player seat**, document it, and **attribute it to epic-108 — do NOT file it as a new 150-12 regression**. Per-world health (load/connect/chargen/multi-turn/UI), elemental magic (ADR-126 MagicPlugin working + `magic.*`/`magic_working` spans), and any WWN combat spans that *do* fire (ablative HP, `hp_depletion`, `state_patch_hp`) are the expected-GREEN scope. Findings route to FIXER via `~/Projects/sq-playtest-pingpong.md`.

**Parallel-clone / working-tree notes (do NOT commit these onto 150-12):**
- `sprint/epic-150.yaml` carries a pre-existing uncommitted **150-9** status flip from a parallel clone — left untouched, not mine to commit.
- Story **150-3** remains `in_progress` (held on FIXER: its MAJOR out-of-conflict-4dF finding has no fix in flight). Starting 150-12 does not close or disturb 150-3.
- Untracked `150-11-*.png` screenshots from the completed 150-11 run are in the tree — leave them; not part of this story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### GM DRIVER playtest closeout (2026-06-20, slug 2026-06-20-shattered_accord-702c5fb9, PC Anaya — Monsoon Courts Tear-Forged Channeler)

Full-stack `/sq-playtest` run via `/pf-gm`. Stack: server+ui oq-3 develop **current incl. #1001** (uvicorn `--reload` caught the pull mid-session); daemon DOWN by choice (R2-cached portraits/POI/hero render fine; no live image-gen needed for a mechanical verify). Findings filed to ping-pong (`~/Projects/sq-playtest-pingpong.md`, 150-12 block at top). Screenshots in `oq-3/playtest-shots/150-12-0[1-4]-*.png`.

**Verdict: PASS w/ epic-108 combat carve-out + AC4 magic gap filed — mirrors sibling 150-11.**

- **AC1 — load/connect/chargen via real UI:** ✅ GREEN. Lobby hero + 16-portrait picker + 5-step narrative chargen → correct WWN sheet (6 reskinned attrs w/ mods, HP 10/10 ablative ♦, inventory 4 items w/ categories). All images from R2/CDN.
- **AC2 — multi-turn + per-world state renders:** ✅ GREEN. 3 narrated turns end-to-end pre-combat; HpPool, stats, inventory, region all render. Stored ground-truth `HpPool {current:10,max:10}`.
- **AC3 — WWN combat engages:** ⚠️ PARTIAL / epic-108 carve-out. Engine **engages**: `win_condition: hp_depletion`, ablative HP pools (You 10 / Ghost 18), initiative rolled, actors seated. **Wedges** at `structured_phase: Setup`, `beat: 0`, `wn_commits: []` — no beats generated → player cannot act. **Silent wedge (no PackError).** 0-HP→hp_depletion path unreachable. Attributed to **epic-108 / ADR-143**, NOT a new regression (per AC5 KNOWN-RISK). NEW this session: combat now *seats* (150-11's didn't) and seats the **wrong Other** (Restless Battlefield Ghost vs the attacked courier) — filed as `WWN-OTHER-SEATING` (ADR-116, medium).
- **AC4 — magic working dispatches + magic.* spans:** ❌ RED (filed). Substrate exists (`effort: channeler max 3`; `spellcasting: prepared [cinder_lance, river_step], casts 2`) but freeform natural-language channeling never maps to the prepared-spell engine: `wwn_spell_cast_log: []`, `magic_state: null`, no Effort commit, no roll. Narrator improvised outcomes. Filed as repro + worse variant of `WWN-MAGIC-LOGGED-NOT-RESOLVED` (recognition itself doesn't fire here). Engine-wide ADR-126/epic-108 gap, not shattered_accord-specific content.
- **AC5 — document epic-108 known-risk:** ✅ DONE (see AC3; attributed to epic-108).
- **AC6 — genre-true narration / no dead UI / findings filed:** ✅ GREEN. Narration genre-true (monsoon resists the dry highland Wall — strong elemental logic), excellent pacing. Only "dead control" is the beat-locked confrontation input = the epic-108 wedge (documented, not separate). Findings filed.

**Bonus verification:** `OPENING-REGION-NO-PROPAGATE #1001` confirmed GREEN on a new world (`current_region: jade_kingdoms` propagated + held through a sub-location drift). **Confirmed data oddities** (repro of 150-11): `active_stakes: "Channeler"` mis-population; `npcs` roster = 7× `None`.

**Per-world `shattered_accord` health is GREEN.** Remaining reds (AC3 wedge, AC4 magic) are engine-wide (epic-108 / ADR-126), filed to FIXER, and match the 150-11 carve-out precedent — the playtest's job (find + file + attribute) is complete.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->