# Story 126-31 Context

## Title
[FATE/UX] Render the opponent stress/consequence track + a taken-out win-meter in FateConflictSurface from the now-projected FATE_STATE.conflict data (#973 carve-out). Data is on the wire (participants[opponent].stress/consequences + fate.conflict.projected span); mirror ConfrontationOverlay's EdgeBar. DRIVER's single highest-impact legibility gap.

## Metadata
- **Story ID:** 126-31
- **Type:** story
- **Points:** 2
- **Priority:** p2
- **Workflow:** tdd (phased: setup → red → green → review → finish)
- **Repo:** ui (sidequest-ui ONLY — no server change)
- **Epic:** 126 — Fate Core playtest follow-ups (annees_folles eval 2026-06-16/17)
- **Branch:** feat/126-31-fate-opponent-track-winmeter (off sidequest-ui `develop`)

## Problem
During a seated Fate conflict the player cannot see how close the opponent is to
being *taken out*. The Fate win signal — per **ADR-143**, the opponent's stress
fill toward taken-out (NOT the vestigial native tension dial) — is computed and
**already projected onto the wire**, but `FateConflictSurface` never draws it. This
is DRIVER's single highest-impact legibility gap from the 150-1/150-2 verify pass.

## Premise check (SM, measured — not asserted)
The story title says "data is on the wire." Confirmed at the **server/protocol**
layer; the gap that makes this a real story is a **lagging UI type**:

- **Server SENDS it.** `protocol/models.py:1065` `FateConflictParticipant` carries
  `stress: dict[str, list[FateStressBox]]` + `consequences: list[FateConsequenceEntry]`
  for OPPONENT-side participants (player-side leaves both empty — its full sheet
  already rides in `FateStatePayload.characters`, never duplicated). Projected by
  `game/ruleset/fate_projection.py:128` `_project_conflict_participant` (reads the
  NPC `core.fate_sheet` seeded by #966). The `fate.conflict.projected` span is
  emitted at `server/websocket_handlers/fate_state_emit.py:106`.
- **UI type LAGS.** `sidequest-ui/src/types/payloads.ts:1220` `FateConflictParticipant`
  still models only `name`, `side`, `committed?` — it has NOT caught up to the
  server's `stress`/`consequences`. So step one is extending the UI type to mirror
  the server (the UI already defines `FateStressBox` + `FateConsequenceEntry` for
  `FateCharacterEntry` — reuse those exact shapes, don't invent new ones).

Net: this is genuinely a 2pt UI-only story — extend the stale type, then render.

## Technical Approach (hints — TEA/Dev refine; SM does not design tests/impl)
1. **Extend the UI wire type** `FateConflictParticipant` (`payloads.ts:~1220`) to add
   optional `stress?: Record<string, FateStressBox[]>` and
   `consequences?: FateConsequenceEntry[]`, mirroring the server model. Keep them
   optional/additive (same back-compat pattern as `committed?`/`stunts?`) so existing
   fixtures stay valid; the surface reads `?? {}` / `?? []`.
2. **Render in `FateConflictSurface.tsx`** an opponent stress track + a taken-out
   win-meter for each opponent-side participant whose track is populated.
3. **Mirror `EdgeBar`** in `ConfrontationOverlay.tsx:365` for the win-meter (fill bar,
   `data-testid="metric-bar"` / `metric-bar-fill`, `data-at-threshold` at full). The
   win-meter VALUE is *used absorption / total capacity* toward taken-out — the server
   already encodes this math in `game/ruleset/fate_projection.py`
   `conflict_opponent_progress()` (checked stress boxes + filled consequence slots over
   total); use it as the reference for the client-side computation. `1.0` = next
   overflow hit takes the opponent out.

## Reference files
| Concern | File |
|---------|------|
| Target component (render here) | `sidequest-ui/src/components/FateConflictSurface.tsx` (+ existing tests in `__tests__/FateConflictSurface.*.test.tsx`) |
| UI wire type to extend | `sidequest-ui/src/types/payloads.ts:1220` (`FateConflictParticipant`); reuse `FateStressBox` / `FateConsequenceEntry` |
| Pattern to mirror (win-meter) | `sidequest-ui/src/components/ConfrontationOverlay.tsx:365` (`EdgeBar`) |
| Server projection (read-only reference) | `sidequest-server/sidequest/game/ruleset/fate_projection.py` (`_project_conflict_participant`, `conflict_opponent_progress`) |

## Scope
- **In scope:** extend the UI `FateConflictParticipant` type; render opponent stress
  track + win-meter in `FateConflictSurface`, mirroring `EdgeBar`.
- **Out of scope:** any server/protocol change (the data already ships); the native
  `ConfrontationOverlay` tension dial; the player's own sheet (rides in `characters`).

## Acceptance Criteria (draft — TEA finalizes in RED)
1. The UI `FateConflictParticipant` type models opponent `stress` + `consequences`
   (reusing `FateStressBox` / `FateConsequenceEntry`); existing payloads/fixtures stay valid.
2. When a conflict has an opponent-side participant with a populated stress track,
   `FateConflictSurface` renders that opponent's stress boxes.
3. `FateConflictSurface` renders a taken-out win-meter whose fill = used-absorption /
   total-capacity (per `conflict_opponent_progress`), reaching full when the next
   overflow hit would take the opponent out.
4. A player-side participant (empty track) and a sheetless opponent (capacity 0) draw
   NO win-meter — the honest empty state, not a zero bar.

## Invariant (do NOT "fix" by relaxing)
Per **ADR-143**, the Fate win signal is the opponent's **stress + consequence fill
toward taken-out**, read from the projected `FateConflictParticipant` track — **never**
the vestigial native `opponent_metric.tension` dial. Do not reintroduce the native
dial into the Fate surface.

---
_Enriched by SM from the very specific story title + epic-126 context + server-side
premise check (`fate_projection.py`, `protocol/models.py`). Original generated by
`pf context create story 126-31`._
