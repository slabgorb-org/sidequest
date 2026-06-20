---
story_id: "150-8"
jira_key: ""
epic: "150"
workflow: "trivial"
---
# Story 150-8: [PLAYTEST] wry_whimsy/oz — full-stack verify (fate)

## Story Details
- **ID:** 150-8
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 2
- **Type:** chore

## Overview

Full-stack `/sq-playtest` verification of `wry_whimsy/oz` (ruleset: Fate Core, ADR-144).
Run via `/pf-gm` as the playtest DRIVER (oq-3); findings routed to FIXER via
`~/Projects/sq-playtest-pingpong.md`. Session `2026-06-20-oz-34212535`, character
**Dorothy** (Stubborn Skeptic, Provoke +4 / Will +3). Eighth Fate world, third
wry_whimsy world (after gulliver/150-7). oz chosen specifically to re-attempt the
Contest-path verification that gulliver's high-menace tone could not reach.

## Acceptance Criteria (from sprint YAML)

1. World loads, connects, chargen completes through the real UI. — **PASS**
2. Multi-turn Fate session; FATE_STATE renders + hydrates on reconnect (#942). — **PASS**
3. Seat a Fate conflict: FATE_ROLL + fate.* + confrontation.* spans fire; harm ablates Fate stress/consequences, core.hp untouched (126-1). — **PASS**
4. Player 4dF determinative (126-7); native Inventory hidden (126-3). — **PASS**
5. Narration genre-true; no dead UI controls; findings filed via ping-pong. — **PASS**
6. SRD Rules page (ADR-149): `/reference/rules/wry_whimsy` leads with "The Rules of Fate Core", chapters render as prose, sticky ToC with anchors, CC-BY footer present. — **PASS** (live-verified)

Plus story-description targets: **Contest resolves opposed checks (#936)** — **CARVED OUT, blocked-by-content** (see verdict); items→invokable aspects (#945) — **PASS**; political layer + witnessed-act spans (double-gated) — **PASS**.

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish

## Delivery Findings

### Verification result (DRIVER, oq-3)

Broad-slate **PASS** on oz:
- **Fate engine engages** — Fate Core, FP economy (3/3, Refresh 3), full ladder, stress/consequence ladders, determinative FATE_ROLL.
- **FATE_STATE hydrate connect + resume (#942)** — full sheet rehydrated after page reload; conceded encounter cleared cleanly (no wedge).
- **126-1 harm ablation** — a 6-shift SucceedWithStyle Provoke attack netted onto the Guardian's taken-out meter (0→4/26) **and a mild consequence**; player `core.hp` stayed 10/10. (Stronger than gulliver, where no hit ever landed.)
- **items→invokable aspects (#945)** — chargen item auto-seeded "Stubbornly, Reassuringly Ordinary" + manual "My Plain Pocketknife Keeps Me Myself"; all aspects carry working Invoke (1 FP) buttons.
- **4dF determinative (126-7/148)** — `fate.throw.broadcast dice=(-1,1,1,1) shifts=6 SucceedWithStyle`; server-side, not narrator-fabricated.
- **native Inventory hidden (126-3)** — "Your signature gear lives in your aspects, not as carried items."
- **whimsy genre-true narration** — green-spectacles humbug played dead straight, skeptic-aware; Guardian "officious and kindly, not a threat" honored; The Test passes (no unbidden player action).
- **political layer + witnessed-act classification (double-gated) ✅✅** — `political_state.initialized premises=1 blocs=2` (premise `the_wizards_humbug`; munchkin/winkie blocs); skeptic's challenge classified as `expose_the_humbug` → drained the Wizard's belief reserve (ledger turn 1). wry_whimsy Premise/Bloc uprising substrate fired end-to-end on a fresh oz session.
- **Bonus:** ADR-151 DEFEND barrier + #429 defender-skill-select; legible 4dF (#439); Conflict surface render (#126-31); Knowledge/footnote capture every turn (CLUE-JOURNAL stays closed); chargen drive minted a tracked quest; SRD Rules page (ADR-149) live-verified.

**Carried confirms (reproduced, not re-filed):** 126-17 (HC/Trouble placeholder-only), FATE-STRESS (flat 2-box phys+mental).

## New bugs filed (FIXER, via ping-pong)

1. **WRY-WHIMSY-NO-FATE-CONTEST-DEFS** (high) — wry_whimsy binds `ruleset: fate` but its confrontation catalog is native-dial schema with **zero `resolution_mode: contest`**, so a Fate Contest can never be seated on any wry_whimsy world. Root cause of the un-verifiable #936/#985/#990 across 150-7+150-8; **corrects the gulliver "high-menace tone" hypothesis** (oz is low-menace and still can't reach a Contest). wry_whimsy + pulp_noir both un-ported; spaghetti_western + tea_and_murder were ported. Porting proposal: `docs/superpowers/specs/2026-06-20-wry-whimsy-fate-contest-porting-proposal.md`.
2. **OPENING-REGION-NO-PROPAGATE** (med-high) — the chosen opening's region doesn't update `current_region`; it stays at the static `starting_location: munchkin_country` while the player stands at the Emerald City gate (Location panel says "Munchkin Country"). Concrete trigger for the carried WORLD-ZONE-SCOPING content bleed.
3. **NARRATOR-EMPTY-NARRATION-DEGRADED** (low) — narrator returned empty player-facing prose on a continuation turn, tripping the degraded-stall guard; the guard recovered cleanly (no client hang).

## Assessment

**Verdict:** **APPROVED — PASS with carve-out** (Keith, 2026-06-20).

All *reachable* ACs verified live on oz. The Contest ACs (#936/#985/#990/#987) are **carved out as blocked-by-content** — NOT a fault of the fixes — because wry_whimsy ships no `resolution_mode: contest` def (WRY-WHIMSY-NO-FATE-CONTEST-DEFS). **Contest verification is re-scoped to a tea_and_murder world (glenross)**, where those fixes already trigger. Follow-up porting proposal drafted (awaiting Keith's crunch decision; pulp_noir has the identical gap). Full scorecard in the ping-pong.

**Handoff:** Story complete. 3 bugs to FIXER; 1 crunch proposal to Keith.
