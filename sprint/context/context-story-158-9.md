# Story 158-9 Context

## Title
Genre theme CSS never arrives on connect — repro/confirm (not reproduced in sweep 2; add guard)

## Metadata
- **Story ID:** 158-9
- **Type:** bug
- **Points:** 2
- **Priority:** p3
- **Workflow:** trivial
- **Repo:** ui
- **Epic:** Playtest sweep follow-ups: WWN combat seating, narrator grounding, roster/map/MP polish

## Problem

On connect, the genre `theme_css` `SESSION_EVENT` sometimes never arrives. When it
doesn't, `:root[data-genre]` is never set, the `.dark` base wins, and `--accent`
collapses to a near-invisible `oklch(0.269)` — the whole UI drops to a low-contrast
dark default. Accessibility hit (low contrast → Alex).

**Repro (2026-06-21, full-stack sweep on caverns_and_claudes/beneath_sunden):**
- Client log: `[useGenreTheme] genre theme_css never arrived within 8000ms of connect — the genre theme is NOT loaded and --accent has silently collapsed to the inherited dark default (near-invisible). This is a No-Silent-Fallbacks transport gap. {graceMs: 8000, connected: true}` (`useGenreTheme.ts:130`)
- **Server log:** NO `theme_css` emission anywhere around connect. Connect path otherwise healthy (session created, world_grounding_loaded, audio.backend_ready, dungeon_curate ran).
- **Key condition:** the server had just been **rebooted** before this session.

**NOT REPRODUCED (2026-06-22 solo `697cbc14`):**
- Genre theme loaded correctly on solo connect — fully styled ConnectScreen and game
  board, 0 console errors, no `theme_css never arrived` warning.
- **Difference:** server had been UP a while (NOT freshly rebooted).
- **Hypothesis (DRIVER):** the bug correlates with a **cold / just-rebooted server**,
  not steady-state connect. Repro condition: restart the server, THEN connect fresh.
  Not marked verified because that reboot condition was not exercised in sweep 2.

## ⚠️ Repo-scope nuance (read before implementing)

The story is scoped **`ui`**, but the finding's evidence points the *root cause* at the
**server**: "NO theme/`theme_css` emission anywhere around connect" and the DRIVER's
FIXER note — "check where `theme_css` is supposed to be pushed over the WS on connect
(`handlers/connect` or a theme mixin) and whether it fires." A reboot-gated server emit
is not fixable from the UI alone.

What already exists on the UI side: `useGenreTheme.ts` **already has the loud-fail
guard** (the warning above, per No-Silent-Fallbacks). So "add guard" in the title is
largely already present.

**Decision for TEA/Dev:** First **repro on a freshly-rebooted server**. Then:
- If the emit is genuinely missing/gated server-side → this needs a **server** fix
  (flag SM to expand repos or file a sibling server story; don't silently no-op it).
- If the UI guard is the intended deliverable → confirm the existing guard fires
  correctly under the reboot condition and harden as needed (e.g. coverage for the
  grace-timer fail path).

Don't fabricate a UI-only "fix" that masks a server transport gap — that violates
No-Silent-Fallbacks.

## Technical Approach

1. **Reproduce first** (systematic-debugging): restart the server, connect fresh,
   confirm whether `theme_css` emits over the WS on the cold connect path.
2. Locate the connect-side `theme_css` emitter (server `handlers/connect` or a theme
   mixin) and confirm whether it's reboot-gated.
3. Deliver the narrowest correct fix per the repo-scope decision above.

Relevant references:
- `useGenreTheme.ts` (UI loud-fail guard, ~line 110–140)
- ADR-079 (Genre Theme System Unification)
- Memory: "Connect/resume bootstrap must mirror per-turn emitters" — a recurring class
  where the connect/resume bootstrap fails to re-emit what a per-turn emitter does
  (FATE_STATE, LOCATION_DESCRIPTION, etc.). `theme_css`-on-connect may be the same shape.

## Scope

- In scope: reproduce the reboot-gated `theme_css`-on-connect gap; confirm/harden the
  UI guard; the narrowest correct fix for where the emit is dropped.
- Out of scope: redesigning the theme system; unrelated connect-path emitters.

## Acceptance Criteria

1. **Repro attempted under the stated condition:** the cold/just-rebooted-server fresh
   connect is exercised, and the result (reproduced or not) is recorded.
2. **No silent fallback:** if `theme_css` does not arrive, the UI fails loudly (existing
   `useGenreTheme` guard) — it must NOT mask the gap with an invented default accent.
3. **Correct repo:** if the root cause is a server emit gap, that is surfaced (repo
   expansion or sibling story), not papered over in the UI.
4. **Guard coverage:** the UI loud-fail path has test coverage proving it fires when
   `theme_css` never arrives within the grace window.

---
_Authored by SM from the 2026-06-22 ping-pong finding (~/Projects/sq-playtest-pingpong.md, "Genre theme CSS never arrives on connect")._
