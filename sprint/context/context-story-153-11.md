# Story 153-11 Context

## Title
[NARRATOR-EMPTY-NARRATION-DEGRADED] harden empty-prose-on-continuation upstream of the degraded-stall guard

## Metadata
- **Story ID:** 153-11
- **Type:** bug
- **Points:** 2
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

The narrator occasionally returns empty player-facing prose — the tool call fires with content but
`content=''` on the player-facing channel — tripping the degraded-stall guard. The guard was
introduced precisely to recover from this: before it existed the empty turn persisted as a clean
success and hung the client. The guard fires correctly and recovers gracefully (no client hang,
next turn resumes `degraded=False`). But the root glitch — the narrator emitting a tool call with
no player-facing prose on a continuation/re-narration turn — is unaddressed. The fix should harden
the empty-prose path **upstream** of the guard so the guard is a last-resort backstop, not the
primary recovery mechanism.

The pattern recurs across unrelated worlds and turn types (oz concede/continuation, shattered_accord
opening turn, burning_peace cold-open), indicating a general continuation/re-narration path weakness
rather than a world-specific issue.

## Repro / Evidence

Three confirmed playtest instances (capture: `/Users/slabgorb/Projects/sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`):

**Primary — oz, concede/continuation (lines 518–527):**
```
WARNING narrator.empty_narration action='The gate of the Emerald City…'
  raw_len=745 tool_calls=1
  — narrator returned empty player-facing prose;
    tripping the degraded stall (was persisting content='' as a clean success
    and hanging the client)
```
Session `2026-06-20-oz-34212535`. The action text re-fed to the narrator was the *opening*
narration verbatim (a re-narration/continuation path). Narrator emitted a tool call but no
player-facing prose. Turn logged `session.narration_complete … world=oz degraded=True`.
Guard fired correctly; no client hang.

**Supplementary confirms (lines 390–394, 435–439):**
- `shattered_accord` opening turn: same symptom — all prose went to the tool-call action (night-corporal/day-watch/Lotus-Provinces pedlar/courier), `content=''`, degraded-stall guard fired, recovered.
- `burning_peace` cold-open turn 1: all prose went to the tool call (shrine/cryptomerias/votive/bell), `content=''`, degraded-stall guard fired, recovered.

All three are confirm-only repros of the same upstream gap.

## Fix Direction

Locate the continuation/re-narration path in the narrator agent (`sidequest/agents/`) where a
tool call with no player-facing prose is a possible outcome. Add an upstream repair step — catch,
retry, or synthesize a minimal player-facing prose string — before the result reaches the
degraded-stall guard. The guard should remain in place as a last-resort backstop but must not be
the mechanism that normally catches this case.

If the repair fires, emit a watcher event (e.g. `narrator.empty_prose_repaired`) so the GM panel
can confirm the upstream path is active rather than the guard.

## Acceptance Criteria

1. **AC-UPSTREAM:** When the narrator returns `content=''` with a non-empty tool call on a
   continuation/re-narration turn, the empty-prose path is detected and repaired (retry or
   synthesized fallback) **before** reaching the degraded-stall guard; the guard does not log
   `degraded=True` for this case.
2. **AC-GUARD-INTACT:** The degraded-stall guard remains in place and still fires for any
   empty-prose case that bypasses the upstream repair (guard is backstop, not primary path).
3. **AC-OBSERVABILITY:** A watcher span or warning event (e.g. `narrator.empty_prose_repaired`)
   is emitted when the upstream repair activates, distinguishable from the guard's existing
   `narrator.empty_narration` warning.
4. **AC-WIRING:** An integration test exercises the real narration path (not a stub) with a
   simulated empty-prose continuation turn and confirms the upstream repair fires and the guard
   does not.
5. **AC-NO-REGRESSION:** Existing degraded-stall guard tests remain green; the guard still
   catches a genuine empty-prose case that reaches it.

## Source

Capture lines 518–527 (primary, oz) + repro confirms lines 390–394 (shattered_accord) and
435–439 (burning_peace):
`/Users/slabgorb/Projects/sq-playtest-pingpong-archive-2026-06-21-epic153-capture.md`

## Scope Notes

- Server-only change: narrator agent + watcher event; no UI change needed.
- The degraded-stall guard itself is correct and should not be removed — it is the last line of
  defence against a client hang.
- This is p3 / low-severity: the guard always recovers; no client hangs in any of the three
  playtest repros. Fix priority is polish/prevention, not blocking.
