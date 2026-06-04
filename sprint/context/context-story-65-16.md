---
parent: context-epic-65.md
workflow: tdd
---

# Story 65-16: 65-4 follow-ups: clear preloadedAssets on session switch + preload hardening + test tightening

## Business Context

Story 65-4 shipped the asset-preload feature (fetch prior-turn images from R2 on
reconnect), with the `preloadedAssets` state as a **separate pure input** to
`ImageBusProvider` that **survives the reconnect message purge**. This was the
right design for reconnect (same session, refresh the socket, keep the gallery
backfill). But a **stale gap** remains: when a player **leaves the session** or
**switches to a different session**, the old session's preloaded assets leak into
the new one — the gallery shows images from a different game until the new
session renders its first live image (which has a higher timestamp and sorts above
the stale backfill).

Story 65-4 AC1 coverage was reconnect-only (rising edge of `connected` within the
same session). This story closes the **cross-session isolation** gap.

## Technical Guardrails

### AC1 — Clear preloadedAssets on session leave

When `handleLeave` runs (player leaves the current session):
- `setPreloadedAssets([])` alongside the other state resets
- Test: a session with preloaded assets, then `handleLeave`, asserts the
  preloadedAssets setter was called with an empty array.

### AC2 — Harden the preload path

From the 65-4 review and subsequent analysis:

- **No stale preload on mid-session slug change.** If the slug changes (a modal
  can navigate between sessions without going through the lobby), preload the new
  session's assets. This is a spec clarification — 65-4 only fired on
  `connected` rising edge; slug *changes while connected* don't trigger a
  `connected` flip, so preload would silently not re-fire. Add an effect that
  fires `useAssetPreload` on rising edge of `connected` OR when `slug` changes
  (a dependency watch that triggers a re-fetch). Test: mount AppInner with
  slug="game1", assert first preload fires; then change slug to "game2" while
  `connected=true`, assert a second preload fires.

- **Confirm the onError callback is wired and tested.** The hook accepts an
  `onError` callback (added in 65-4 AC4) but the App mount site
  (`handlePreloadAssets` callback) never passes one. Add a callback that
  surfaces preload errors the same way socket errors surface (transient banner
  or notification). Test: mock `fetch` to return a 500, assert `onError` is
  invoked at the App level and an error is surfaced.

### AC3 — Tighten 65-4 tests

Existing tests in `src/hooks/__tests__/useAssetPreload.test.ts` and integration
tests in `src/App.test.tsx` (if they exist):

- **Test the slug change case (AC2):** a mount with slug="A" then a change to
  slug="B" while connected, each should fire a fetch. Currently if only the
  rising-edge `connected` transition is tested, slug changes are not covered.

- **Test the onError callback contract.** The hook's onError must be invoked on
  fetch failure (non-ok response, thrown request). App level: onError callback
  should be wired and surface the error through the app's transient-error banner
  or a distinct notif.

- **Test the url-less row drop at App level.** A preload response containing
  rows with missing `url` must be console.error'd and dropped (never make it to
  ImageBusProvider). This is already in `handlePreloadAssets`; the test asserts
  the drop behavior and the console.error call.

## Scope Boundaries

**In scope:**
- Clear `preloadedAssets` state in `handleLeave` (AC1).
- Harden `useAssetPreload` to fire on slug changes (AC2a).
- Wire and test the `onError` callback (AC2b).
- Tighten existing tests per AC3.
- Add tests for the new behaviors.

**Out of scope:**
- Server / backend changes — 65-2's asset ledger and `/api/sessions/{slug}/assets` endpoint are finalized.
- Daemon / content.
- The mid-reconnect ordering hazard from 65-4 AC context (Approach 1 vs 2) — that resolved in 65-4 with Approach 2.

## Acceptance Criteria

**AC1 — Clear preloadedAssets on session leave**
- `handleLeave()` calls `setPreloadedAssets([])` alongside its other state resets.
- Test: mount AppInner with a session, set `preloadedAssets` to a sample array,
  call `handleLeave`, assert `setPreloadedAssets` was called with `[]`.

**AC2a — Preload fires on slug changes (while connected)**
- `useAssetPreload` hook dependency array includes `slug` alongside `connected`,
  so a rising edge on either (or a change to slug while connected) triggers a
  fetch.
- Test: mount with slug="game1" + connected=true → preload fires. Change slug to
  "game2" (connected still true) → a second preload fires for the new slug.
  Fetch URL reflects the new slug.

**AC2b — onError callback is wired and tested**
- App mount site passes an `onError` callback to `useAssetPreload`. The callback
  can surface the failure through the same channel as transient errors (app-level
  error state or banner).
- Test: mock `fetch` to reject / return non-ok; assert `onError` is invoked and
  the App's transient-error state is set (or notification fired).

**AC3 — Tighten existing test coverage**
- Hook tests in `useAssetPreload.test.ts`:
  - Test `slug` changes while connected (AC2a).
  - Test `onError` callback invocation on fetch failure (AC2b).
  - Test url-less row handling at App level (console.error + drop).
- Integration / App tests:
  - End-to-end: mock `fetch`, assert preloaded images appear in the gallery
    (existing AC3 from 65-4, extend if needed).
  - Test `handleLeave` clears preloadedAssets (AC1).
  - Test slug change fires a second preload (AC2a).

## Key Files

- `sidequest-ui/src/hooks/useAssetPreload.ts` — slug dependency, re-trigger logic
- `sidequest-ui/src/App.tsx` — `handleLeave` state reset, onError wiring
- `sidequest-ui/src/hooks/__tests__/useAssetPreload.test.ts` — hook unit tests
- `sidequest-ui/src/App.test.tsx` (if exists) or similar — integration tests

## Assumptions

- `preloadedAssets` is App-level state, not ImageBusProvider-internal (it is —
  defined at line ~281 in App.tsx, passed to ImageBusProvider at line ~2246).
- `slug` is stable once retrieved from `useParams` (it is — captured in AppInner
  at the top via `const { slug } = useParams()`).
- The `onError` callback propagating to an App-level surface (transient error
  banner) is acceptable (yes — story 71-3 AC-4 wired transient-error surface;
  this story can reuse it).
