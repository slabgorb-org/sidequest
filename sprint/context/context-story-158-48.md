# Story 158-48 Context

## Title
WWN combat resolution (kill) turn crashes the narrator SDK loop (AnthropicSdkLoopExceeded max_turns=8) — victory NARRATION never persists; client falls back to the opening card (resolution-turn twin of #1086)

## Metadata
- **Story ID:** 158-48
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repo:** sidequest-server
- **Epic:** Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem
sq-playtest 2026-06-27 (caverns_and_claudes/beneath_sunden, WWN, Curly, session 2026-06-27-beneath_sunden-3afa8493 / db id 16570). CONFIRMED root cause of the board's "client renders the OPENING establishing card on a combat-resolution turn" finding (~/Projects/sq-playtest-pingpong.md, line ~42) AND its secondary observation ("does the victory card persist?").

ROOT CAUSE (corrected — NOT the board's hypothesized ADR-051 round/seq collapse): on the KILL turn the narrator SDK tool loop hits max_turns=8 and raises AnthropicSdkLoopExceeded (ws.unexpected_error), so the victory NARRATION is never generated or persisted. This is the RESOLUTION-turn twin of #1086 (a6dc7535). #1086 fixed the cold-SEAT turn (stale in_combat=False before dispatch seats). But on the resolution turn, in_combat legitimately flips to False the instant the encounter resolves, so the A2 de-nativized WN zone (gated on context.in_combat, orchestrator.py ~2226) does NOT fire on the victory turn → the narrator is never told "the throw already resolved; just narrate it; do NOT call dice/beat tools", and the start-a-confrontation menu fires instead → the narrator flails past max_turns → crash → no NARRATION/SCRAPBOOK event for the kill turn.

EVIDENCE (Postgres ground truth + server log):
- session 16570 kill turn fired ENCOUNTER_RESOLVED player_victory (seq 28) with NO accompanying NARRATION. Last persisted NARRATION = seq 22 ("…the axe bites… hurt but not done", the attack-#1 card, opponent 2/4).
- 3 comparison resolution turns (sessions 16514 / 5523d964, 16589 / 95d7d354 x2 incl. a player-death) ALL persisted their resolution narration ~15-30s after the mechanics → persisting is the NORMAL path; the kill turn is the intermittent miss caused by the crash.
- server log (~/.sidequest/logs/sidequest-server.log.20260627-124332, local EDT = UTC-4): turn 8 "throw_resolved total=13 CritSuccess resolved_encounter=True" → "hp_depletion.resolved player_victory" → "monster_manual.injected turn=8 in_combat=False" → "ERROR ws.unexpected_error … AnthropicSdkLoopExceeded max_turns=8" (traceback through anthropic_sdk_client.complete_with_tools).
- the board's cited "SDK narrator returned narration len=595 degraded=False" was actually TURN 7 (the "hurt but not done" card), misattributed to the kill turn.

DOWNSTREAM (client artifact): the "opening card rendered at the bottom on the resolution turn" (ADR-133) is downstream of this crash — on a resolution turn with no NARRATION card + a torn-down socket, the client mirror's narration accumulator falls back to re-rendering the session opening. Self-heals on reload (free-nav restored, scrollback correct minus the lost victory card). The victory card is PERMANENTLY lost from the durable log.

PROPOSED FIX (mirror #1086, ADR-143 "bind don't balance"): fire the A2 de-nativized WN zone on encounter_resolved_this_turn (the turn that resolves the encounter), not only when context.in_combat. The WN engine owns the round; the resolution narration must be the de-nativized "just narrate the outcome" directive, never the native beat menu. Add a resolution-turn OTEL span (twin of cold_seat_context_refreshed) as the GM-panel lie-detector.

ALSO seen on the same turn (likely benign, worth a glance while in here): OTEL attribute error "Invalid type NoneType for attribute 'yield_side'".

Board: ~/Projects/sq-playtest-pingpong.md. Sibling: #1086 (cold-seat), #1089 (shock-on-miss).

## Technical Approach
_Approach hints to be refined by TEA/Dev. The story title above defines the
intended behavior._

## Scope
- In scope: the behavior described by the story title.
- Out of scope: unrelated changes.

## Acceptance Criteria
- On a WWN combat resolution (kill/death) turn where the encounter resolves this turn and in_combat flips to False, the narration turn fires the A2 de-nativized WN directive (throw already resolved; narrate the outcome; do not call dice/beat tools) and converges within max_turns — no AnthropicSdkLoopExceeded, no ws.unexpected_error, no disconnect.
- The victory/defeat NARRATION (+ SCRAPBOOK_ENTRY) persists to the events log on the resolution turn, so /timeline replay shows the victory card after reload (regression-guarded against the session-16570 drop).
- An OTEL watcher span (twin of cold_seat_context_refreshed) fires on the resolution turn; a wiring test drives real refresh + build_narrator_prompt and asserts the de-nativized directive is present and the start-a-confrontation menu is absent on the resolution turn.
- The cold-seat turn (#1086) and non-resolution beat-commit turns are unchanged.

---
_Generated by `pf context create story 158-48` from the sprint YAML._
