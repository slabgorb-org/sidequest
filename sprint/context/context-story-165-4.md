# Story 165-4 Context

## Title
Protocol adjudication echoes + UI grid/resolution-card math display (plan tasks 9–10)

## Metadata
- **Story ID:** 165-4
- **Type:** story
- **Points:** 3
- **Priority:** p1
- **Workflow:** superpowers → run as **spdd** (settled Keith decision, `sm-decisions.md`)
- **Repo:** server, ui
- **Epic:** Mapping Track C — tactical mechanics (ADR-096 v2)

## Problem
Plan tasks 9–10: echo the tactical adjudications (TACTICAL_GRID) + dice-result range onto
additive protocol fields, and render them in the UI as legible, player-facing math (grid +
resolution card). This is the Sebastien/Jade "see the math in the player UI" surface.

## Technical Approach
_TEA/Dev refine per the plan. Additive protocol only — `TACTICAL_GRID` keeps its shape and
gains optional fields with empty defaults (so Track B's SITE_MAP cutover can't collide)._

## Scope
- In scope: protocol echoes + UI display (plan tasks 9–10).
- Out of scope: the enforcement engine itself (165-3), Fate zones (165-5).

## Acceptance Criteria
_TEA to define during the RED phase from plan tasks 9–10._

## Carryover from 165-1 (C1 library — read before starting)
Full detail: `sprint/archive/165-1-session.md` + `context-epic-165.md` §Carryover + the
tea/dev/reviewer `*-gotchas.md` (tagged 165-1). **Most of these bite the display layer:**
- **`ReachResult.cost` is a SUPERSET of `.reachable`** — it includes the origin (cost 0) and
  the immediate over-budget boundary cell (cost > budget). When rendering "cells you can move
  to," use `.reachable`; rendering `cost.keys()` would highlight unreachable cells. This is a
  real display-correctness trap (the 165-1 `ReachResult` docstring understates it).
- **`RangeAdjudication.has_los` means "unchecked" when `require_los=False`** (it is hard-set to
  `True` without calling `line_of_sight`). Do NOT render it as "line of sight confirmed" on a
  melee/require_los=False result — only meaningful as a real LOS check when `require_los=True`.
- **Additive protocol only** — new echo fields need empty defaults.
- **Plan doc has bugs** in its embedded code — hand-verify before transcribing tasks 9–10.
