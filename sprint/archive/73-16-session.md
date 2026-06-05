# Standalone: Opponent-only panel valence + ledger test coverage (73-13 follow-up)

**ID:** 73-16
**Jira:** (no Jira integration)
**Points:** 2
**Priority:** P3
**Workflow:** standalone
**Status:** done
**Repos:** sidequest-ui
**Branch:** feat/73-16-opponent-only-valence-followup
**PR:** slabgorb/sidequest-ui#343 (squash-merged → develop, 2026-06-05)
**Started:** 2026-06-04
**Completed:** 2026-06-04

---

## Description

Closes the two non-blocking findings the Reviewer (Chrisjen Avasarala) raised during the **73-13** review (PR #341), per the user's "take care of the followups" instruction. The pre-existing `?? 0` masking finding was explicitly left out of scope (it predates 73-13).

### 1. Opponent-only panel valence (`data-actor`)
In the opponent-acts-first window (player impact absent, opponent present), `BeatImpactPanel` drove its container `data-effect` from the **opponent's** `BeatImpactView`. The effect taxonomy (advance/setback/backfire/…) is **player-relative** — `beat-impact-advance` resolves to `--encounter-player` (`index.css:101`) — so an opponent `advance` (they pressed their edge) rendered the panel in the *player's* win-green, reading as "you advanced". This is the legibility trap the playgroup rubric cares about (an Alex-style fast reader misreading an enemy hit as a personal win).

**Fix:** the panel now emits `data-actor` (`"opponent"` iff the opponent acted and the player did not, else `"player"`), and `beat-impact.css` adds a `.beat-impact[data-actor="opponent"]` rule that re-keys the actor-level coloring to `--encounter-opponent`. Equal specificity to the `[data-effect]` rules, wins by source order. The effect glyph is kept (it honestly shows the opponent's beat direction) but now inherits the opponent color instead of player-green.

### 2. BeatHistoryLedger coverage
The 73-13 fix relaxed the ledger gate and made the "You" row conditional, but TEA's tests asserted only `BeatImpactPanel` — the ledger change shipped unasserted (flagged by edge-hunter + test-analyzer). New tests pin `beat-history-ledger` in the opponent-only window (only the "Them" row), its suppression when neither side acted (null/null and undefined/undefined), and both rows when both acted.

## TDD trail

- **RED** (`73-13-followup-red`): new file `ConfrontationOverlay.opponentfirstfollowup.test.tsx` — 4 ledger tests PASS (gap was unasserted, not broken), 4 `data-actor` tests FAIL (attribute absent).
- **GREEN** (`73-13-followup-green`): added `data-actor` to the panel + the CSS rule → 100/100 across all 10 ConfrontationOverlay suites; `tsc --noEmit` + `eslint` clean. No regression to the 73-13 `opponentfirstgate` / `beatimpact.coverage` suites.

## Files Changed

| File | Change |
|------|--------|
| `sidequest-ui/src/components/ConfrontationOverlay.tsx` | Emit `data-actor` on the BeatImpactPanel container (opponent-only → `"opponent"`, else `"player"`) + rationale comment |
| `sidequest-ui/src/styles/beat-impact.css` | Add `.beat-impact[data-actor="opponent"]` rule re-keying color/border/background to `--encounter-opponent` |
| `sidequest-ui/src/components/__tests__/ConfrontationOverlay.opponentfirstfollowup.test.tsx` | New — 8 tests: 4 ledger coverage + 4 `data-actor` valence |

## Notes / carry-forward

- The valence fix is CSS-only (a color re-key); jsdom cannot assert computed colors, so `data-actor` — the attribute the CSS keys on — is the pinned test contract. A future visual/Playwright pass could assert the actual rendered color if desired.
- The pre-existing `{impact.own ?? 0}` / `{opponent.own ?? 0}` masking (renders a missing `own` as `0`) remains open as a future hardening note — out of scope here, predates 73-13, also present in `LedgerRow`.
