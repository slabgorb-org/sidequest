# Story 150-3 Context

## Title
[PLAYTEST] spaghetti_western/five_points — full-stack verify (fate)

## Metadata
- **Story ID:** 150-3
- **Type:** chore
- **Points:** 2
- **Priority:** p2
- **Workflow:** trivial
- **Repo:** ui,server,content,daemon
- **Epic:** Full-stack playtest verification — ruleset bindings, per-world health, recent-fix regression

## Problem
Full-stack /sq-playtest verification of spaghetti_western/five_points (ruleset: fate). Confirm in play: Fate engine engages (FATE_ROLL + fate.* + confrontation.* spans), harm ablates stress/consequences not core.hp (126-1), FATE_STATE hydrates on connect/resume (#942), items become invokable aspects (#945), Contest resolves opposed checks (#936), 4dF determinative (126-7), native Inventory hidden (126-3). Poker/table game live: trigger a table scene and confirm router-driven seating (126-2). Execute via /sq-playtest full-stack (UI + Playwright + UX Designer); bugs via ping-pong to FIXER.

--- GM CLOSEOUT (2026-06-20, slug 2026-06-20-five_points-effe36cd, PC Cormac Brennan Famine-Irish shootist) — HELD in_progress (MAJOR systemic finding, not a clean close like 150-1/150-2) ---
Verified OTEL-first (GM panel + stored /snapshot, never prose — caught a fabricated roll mid-session that prose alone would have passed). Running oq-1 stack: server #972, ui develop (#430/#431/#432 + dice-lib #28 reconciled live mid-session after a UI<->dice-lib skew white-screened the game), content #479.

VERIFIED GREEN: chargen end-to-end (5-step narrative wizard -> correct Fate sheet); IN-CONFLICT 4dF determinative (126-7, real dice [0,0,-1,1] in encounter.fate_commits); 126-1 harm ablation (2-shift hit checked physical stress 2-box, core.hp UNTOUCHED 10/10); ADR-151 DEFEND barrier (pending_defenses -> throw -> resolve); #942 FATE_STATE hydrate on reconnect (full reload rehydrated conflict+stress+aspects+FP); #945 chargen gear->aspect (4 gear aspects, invokable in-conflict); 126-3 native inventory hidden; ADR-116 participants; SRD Rules page ADR-149 (leads with Fate Core, chapters render, ToC anchors, CC-BY footer); per-world five_points content is EXCELLENT (niche reference-stacking: Anbinder/Dickens/Leone/Yojimbo; period-true funnels, portraits, real-figure cast).

BUGS -> FIXER (ping-pong sq-playtest-pingpong.md): (1) [MAJOR] out-of-conflict skill checks FABRICATE the 4dF — no engine roll, narrator invents faces+result (the fate_commits path only engages INSIDE a seated conflict; in-conflict is sound); (2) [HIGH] dice render blank — #430 same-origin font proxies to a 403 R2 path while local /fonts/Inter-Bold.ttf serves 200 unused; (3) [HIGH] poker (126-2) SEATS (router instantiate_table_encounter + dealt 5-card hand, ADR-129) but is deactivated by the same-turn location change -> no playable table; (4) [HIGH/CONTENT] no chargen_seed_table for spaghetti_western/tea_and_murder/wry_whimsy -> blank Fate pyramid on the narrative on-ramp (8 worlds 150-3..150-9; crunch decision -> Keith; 126-24 shipped infra + pulp_noir content only); (5) LOW: possessive place-ref ("Rynders's grocery") mints a phantom NPC (Keith reframed: store can't represent referenced-but-absent person); historical pre-gens get conlang-mangled names; Isaiah Rynders double-seeded.

CONFIRMED (storied): de-nativize standoff — native tension dial runs in PARALLEL with the Fate exchange (ENCOUNTER_NARRATOR_DIAL_ADVANCE), native core.hp present-but-bypassed. 126-17 chargen-aspect placeholder repro confirmed.

DISPOSITION: per-world five_points health + the Fate CONFLICT engine are GREEN and well-verified; but the MAJOR out-of-conflict fabrication + dice-font 403 + poker deactivation are genre/engine-wide (not five_points-specific) and warrant FIXER work before the Fate ACs can be called green for spaghetti_western. Held in_progress pending those fixes.

## Technical Approach
_Approach hints to be refined by TEA/Dev. The story title above defines the
intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- World loads, connects, and chargen completes through the real UI.
- A multi-turn Fate session runs end-to-end; FATE_STATE renders (aspects/skills/fate points/stress) and hydrates on reconnect (#942).
- Seat a Fate conflict: FATE_ROLL + fate.* + confrontation.* OTEL spans fire (GM-panel lie detector); harm ablates Fate stress/consequences, core.hp untouched (126-1).
- Player 4dF is determinative (thrown dice ARE the roll, 126-7); native Inventory tab hidden for the Fate PC (126-3).
- Poker/table scene seats via the router (table_resolution cdef → instantiate_table_encounter); antes/seats/sealed-commit loop present (126-2).
- Narration is genre-true; no dead UI controls; findings filed via ping-pong to FIXER.
- SRD Rules page (ADR-149; merged via server #948 + content #476 + ui #420): open /reference/rules/spaghetti_western — the page leads with the 'The Rules of Fate Core' ruleset_reference (rules_document) section. Fate player chapters render as readable prose, each chapter appears in the sticky ToC with a working anchor link, and the CC-BY attribution footer is present. Verifies the new player-facing reference surface for this Fate pack (recent-fix regression). Code-level confirmed: build_rules_projection('spaghetti_western') emits the section; this AC is the live-page render check.

---
_Generated by `pf context create story 150-3` from the sprint YAML._
