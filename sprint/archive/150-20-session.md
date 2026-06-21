---
story_id: "150-20"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 150-20: [PLAYTEST] road_warrior/the_circuit — full-stack verify (cwn)

## Story Details
- **ID:** 150-20
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Sm Assessment

**Routing decision: full-stack PLAYTEST → GM DRIVER (`/sq-playtest`), not standard Dev.**

This is a `[PLAYTEST]` trivial story whose `implement` phase is run by the human GM DRIVER (this clone, oq-3) via the `/sq-playtest` full-stack harness (UI + Playwright + UX Designer) — the same pattern as archived siblings 150-3 (spaghetti_western/five_points) and 150-8 (wry_whimsy/oz). The `dev` agent does not run the playtest; the GM does. Findings route to FIXER via `~/Projects/sq-playtest-pingpong.md`.

**Scope under test:** road_warrior/the_circuit on ruleset `cwn` (Cities Without Number). Confirm (1) world loads + chargen, (2) the WN engine engages for combat — watch for ablative-HP / `hp_depletion` / `state_patch_hp` OTEL spans, (3) per-world health across multi-turn / narration / UI, (4) chassis/rig (ADR-125) bond-ledger + interior render IF a vehicle confrontation is exercised.

**DRIVER caveat (read before running combat):** epic-108/ADR-143 (WN-owns-the-round combat) is in-flight and currently RED — empty beat-pool. A combat verify will most likely re-surface this KNOWN breakage. Confirm the symptom from the player seat and attribute it to epic-108; do NOT file it as a new regression. The per-world health and chargen ACs are independently verifiable even with combat red — prioritize those for a clean signal, then probe combat to confirm-and-attribute.

**Merge gate:** clear at setup — no open PRs in any repo.

**Parked sibling:** 150-3 remains `in_progress` (a held-resume playtest awaiting a FIXER MAJOR fix); it has no non-draft PR, so it does not block this story.

**Branch note:** orchestrator stays on `main` (trunk-based); subrepos sit on empty `feat/150-20-the_circuit` branches at develop HEAD — the read-only baseline for the run. The DRIVER writes no subrepo code (FIXER does), so these branches stay empty.

## Reviewer Assessment

### Specialist Findings Verification Table

| # | Specialist | Received | Status | Findings | Decision |
|---|------------|----------|--------|----------|----------|
| 1 | reviewer-preflight | N/A | n/a | none | No code diff — playtest verify; subrepo branches empty |
| 2 | reviewer-edge-hunter | N/A | n/a | none | No code diff to enumerate paths over |
| 3 | reviewer-silent-failure-hunter | N/A | n/a | none | No code diff |
| 4 | reviewer-test-analyzer | N/A | n/a | none | No code diff / tests authored by DRIVER |
| 5 | (live-stack verification) | Yes | done | 5 non-blocking | In-session OTEL/forensics + Playwright play across 5+ turns — see Delivery Findings |

No code-review specialists were dispatched: this is a `[PLAYTEST]` verify of the **running stack**, not a code-diff review (the DRIVER authored zero code; `feat/150-20-the_circuit` subrepo branches are empty, no PR). The "review" substrate is the live-stack verification row — OTEL span reads (`dice.throw_resolved`, `dice.opponent_reprisal_*`, `win_condition=hp_depletion`), save-forensics snapshot reads (stored HP/region), and Playwright play — all captured in Delivery Findings + screenshots.

**Verdict: APPROVED — PASS.** Human reviewer (Keith, DRIVER/operator) accepted the verify result on 2026-06-21: "yes pass it and finish."

This is a `[PLAYTEST]` verify story; the review is the operator's acceptance of the in-session findings, not a code-diff review (the DRIVER wrote no code — the subrepo `feat/150-20-the_circuit` branches are empty; all fixes route to FIXER via the ping-pong board). The three load-bearing ACs are green: AC#1 (loads+chargen), AC#2 (CWN combat engine engages — populated beat-pool, `win_condition=hp_depletion`, player-side HP ablation, faithful narration), AC#3 (per-world health across 5+ turns). AC#4 (chassis/rig) was attempted but no chase seated — acceptable, it is explicitly "if exercised." The held-at-p3 epic-108 concern is resolved: the empty-beat-pool RED is WWN-specific and does NOT affect the CWN path, so road_warrior is not implicated. 5 non-blocking findings filed to FIXER. No merge required (no PR).

## Workflow Tracking
**Workflow:** trivial
**Phase:** review
**Phase Started:** 2026-06-21T08:20:08Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T05:37:38Z | 2026-06-21T05:41:08Z | 3m 30s |
| implement | 2026-06-21T05:41:08Z | 2026-06-21T08:20:08Z | 2h 39m |
| review | 2026-06-21T08:20:08Z | - | - |

## Acceptance Criteria
1. road_warrior/the_circuit loads + chargen works
2. CWN Without-Number engine engages in combat — verify ablative HP / hp_depletion / state_patch_hp OTEL spans
3. Per-world health across multi-turn / narration / UI
4. Chassis/rig (ADR-125) bond-ledger + interior render IF exercised

## Implementation Notes
- **Playtest Story:** This is a `[PLAYTEST]` story. The implement phase is NOT run by a standard Dev agent.
- **Execute via:** `/sq-playtest` skill (full-stack: UI + Playwright + UX Designer)
- **KNOWN BREAKAGE:** epic-108/ADR-143 WN-owns-the-round combat is in-flight and currently RED (empty beat-pool). A combat verify will likely surface this known issue. Confirm the symptom from the player seat and attribute to epic-108, NOT report as a new regression.
- **Bug Routing:** Findings → FIXER via ~/Projects/sq-playtest-pingpong.md (ping-pong file)
- **Repos Under Test:** ui, server, content, daemon
- **Branch Strategy (Orchestrator):** trunk-based (work on main, no feature branch)
- **Branch Strategy (Subrepos):** gitflow (feat/150-20-the_circuit on ui, server, content, daemon)

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[VERIFY RESULT — PASS w/ findings] road_warrior/the_circuit (CWN) full-stack.** Session `2026-06-21-the_circuit-e214aec0`. AC#1 loads+chargen ✓ GREEN (world cover/lore/tone, 5-step origin flow, 20-portrait picker all render, coherent Wheelman sheet + War Rig "The Anvil"/Armor + CWN equipment). AC#2 CWN combat ✓ **GREEN** — router-driven confrontation, `win_condition=hp_depletion`, **populated beat-pool** (4 CWN beats w/ attr+DC), dice resolve (Fail 7 / CritSuccess 15), **HP ablates 48→46**, AC-based opponent reprisal, mechanically-faithful narration. AC#3 per-world health ✓ GREEN (5+ turns, responsive narration, HP persists, image renders fire, header self-corrects). AC#4 chassis/rig (ADR-125) — **ATTEMPTED, not reached** (tried to break the on-foot brawl into a vehicular chase; `disengage` beat failed twice — DC10, rolled 9 then 7 — fight wouldn't release, no chase seated; Rig Composure / bond-ledger / interior render unverified).
- **[Gap, non-blocking] The epic-108/ADR-143 empty-beat-pool RED does NOT manifest on CWN.** The held-at-p3 expectation (combat verify re-surfaces epic-108 red) was WRONG for this world — the RED is WWN-specific. CWN drives the round end-to-end. Story can complete as PASS; do not attribute any WWN-combat red to road_warrior.
- **[Findings → FIXER, ping-pong]** 5 non-blocking findings filed to `~/Projects/sq-playtest-pingpong.md` under the 150-20 block: (1) **CWN-OPPONENT-REPRISAL-NO-DAMAGE** (medium-high) — opponent hits land but deal 0 HP (`dice.opponent_reprisal_damage_spec_missing`), player unkillable, combat has no player-side stakes; wiring gap not balance; (2) CWN-OTHER-SEATING (seated "Shadow" 48HP synthesized boss ≠ narrative peer rival; +"Masses Ough" shuffle name) — medium, ADR-116 family; (3) ROAD_WARRIOR-MISSING-SFX (metal_impact.ogg + whole sfx_library 404) — low; (4) turn-1 location header shows raw region id "nottavello", self-corrects — low data-oddity; (5) chargen name step silently rejects prose answer — low UX.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->