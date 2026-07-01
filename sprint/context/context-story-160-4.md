# Story 160-4 Context

## Title
Animal companion cannot join a SOLO session — SoloSlotConflict rejects the companion_of/pet connect; resolve doc-vs-engine design fork + make the understudy run loop fail loud on a rejected connect (unblocks 160-3 dogfood)

## Metadata
- **Story ID:** 160-4
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** sidequest-understudy,sidequest-server
- **Epic:** Companion playtest follow-up: animal companions

## Problem
sq-playtest 2026-06-27 (board ~/Projects/sq-playtest-pingpong.md). Found by SM (DRIVER) while dogfooding epic-160 animal companions. BLOCKS 160-3 (the solo dogfood path as written).

WHAT HAPPENS: launching a companion (e.g. `companion play owl_sunden.yaml`, role: pet, companion_of: player1.local, game_slug = the live human room) against a SOLO beneath_sunden session (2026-06-27-beneath_sunden-3afa8493) → the companion opens the WS, sends SESSION_EVENT/connect, and the server immediately replies type=ERROR payload={"message":"solo game … already occupied by Curly","reconnect_required":false}. None of the four 160-3 signals fire (no chargen.complete / bond_resolved / routed_as_pet / distinct voice); the companion never seats.

ROOT CAUSE (server = ground truth): SessionRoom.connect() (sidequest/server/session_room.py ~500-505): when self.mode == GameMode.SOLO, ANY other connected player_id raises SoloSlotConflict("solo game … already occupied by …"). The guard exists to prevent the "two parallel solo games on one slug" bug (playtest 2026-04-26) — but it treats a bonded companion exactly like a second human and rejects it. The connect never reaches bind_companion_bond / the chargen gate (no chargen_gate, no companion.bond_resolved, no traceback — the ERROR frame is the only output for the companion socket). Reproduced cleanly on a freshly-restarted single worker via a minimal WS probe (ProbeOwl, same connect frame → same ERROR), so NOT a stale-server artifact.

DESIGN FORK (needs Keith's call — pick before implementing the guard half):
  (a) DOC-ONLY (if MP-is-intended): companions are multiplayer-only. The companion system prompt (plan C, 2026-06-25-companion-C-companion-package.md:483) literally says "You ARE a character in a live MULTIPLAYER tabletop game", and the epic-159 "Donut beside Keith" run + the existing -mp- saves all use MP rooms. Fix = the CompanionDef SETUP notes (donut_sunden.yaml et al.) + 160-3 must state the human room MUST be a multiplayer session; a companion cannot join a /solo/ game. Cheap, matches current behavior. Touches sidequest-understudy + the orchestrator 160-3 notes.
  (b) ENGINE (if solo-should-allow-a-pet — the natural Keith-solo-with-a-companion case): exempt companion_of-bearing connects from the SoloSlotConflict guard (a bonded pet is not a competing solo player). Touches sidequest-server (session_room.py).

INDEPENDENT OF THE FORK — loud-failure hardening (No Silent Fallbacks, sidequest-understudy): the understudy run loop only handles SESSION_EVENT-ended / CHARACTER_CREATION / prompt / TURN_STATUS, so on an unhandled type=ERROR connect rejection it silently loops back to recv() and HANGS forever. It must surface the rejection loudly (log + exit non-zero), not hang. This half is a real defect regardless of (a)/(b).

REPOS: sidequest-understudy (run-loop hardening, certain; + CompanionDef notes if path a) + sidequest-server (guard exemption if path b). SM should refine --repos once the fork is decided; the orchestrator 160-3 notes get the doc update under path (a).

Related: 160-3 (dogfood validation — surfaced this; may pivot to an MP room instead). Board: ~/Projects/sq-playtest-pingpong.md (the [GAP/QUESTION] companion-seat task).

## Technical Approach

**Path (b) — ENGINE (CHOSEN by Keith)**

A bonded animal companion is NOT a competing solo player and must be exempted from the SOLO-slot guard.

### Primary Change: sidequest-server
**File:** `sidequest/server/session_room.py`
**Location:** `SessionRoom.connect()` (~lines 500-505)

**Current behavior:** When `self.mode == GameMode.SOLO`, ANY other connected `player_id` raises `SoloSlotConflict("solo game … already occupied by …")`.

**Updated behavior:** Exempt connects that carry a `companion_of` bond from the guard, so the connect proceeds to `bind_companion_bond` / the chargen gate instead of being rejected.

**Preservation:** The existing guard's purpose (prevent two parallel solo games on one slug — playtest 2026-04-26) must be PRESERVED for genuine second-human connects; only bonded pets are exempted.

**OTEL instrumentation:** Per the OTEL Observability Principle (CLAUDE.md), emit an OTEL watcher event on the companion-exemption decision (e.g., `companion.solo_exempt` or similar) so the GM panel can verify a bonded pet was seated rather than rejected.

### Secondary Change: sidequest-understudy
**File:** Understudy run loop (exact location TBD by TEA)

**Defect:** On an unhandled `type=ERROR` connect rejection, the run loop silently loops back to `recv()` and HANGS FOREVER (No Silent Fallbacks violation).

**Fix:** Surface the rejection loudly — log the ERROR payload and exit non-zero instead of hanging.

**Test coverage:** Include a test driving a rejected connect frame to verify loud failure.

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- Keith's design fork is resolved and recorded on the story: doc-only (companions are MP-only) OR engine (exempt companion_of connects from the SoloSlotConflict guard).
- Per the chosen path: either the CompanionDef SETUP notes + 160-3 state the human room must be multiplayer (a companion cannot join a /solo/ game), OR SessionRoom.connect() admits a companion_of/pet connect into a SOLO room without raising SoloSlotConflict (and still blocks a genuine second solo human).
- The understudy run loop fails loud on an unhandled type=ERROR connect rejection — logs the server message and exits non-zero instead of hanging at recv() (No Silent Fallbacks). Covered by a test driving a rejected connect frame.
- A companion seats end-to-end on the supported room type: chargen.complete + companion.bond_resolved + routed_as_pet + a distinct per-species voice all fire (the four 160-3 dogfood signals), with an OTEL/wiring assertion.

---
_Generated by `pf context create story 160-4` from the sprint YAML._
