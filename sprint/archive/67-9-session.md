---
story_id: "67-9"
jira_key: ""
epic: "67"
workflow: "tdd"
---
# Story 67-9: Hoist WebSocket connection + slug-connect handshake above <Routes> to kill remount re-handshake (67-8 Layer 2)

## Story Details
- **ID:** 67-9
- **Jira Key:** (not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Sm Assessment

**Routing decision:** Hand off to TEA (The Architect) for the RED phase of this phased TDD workflow. Single repo: `sidequest-ui`.

**Why this story, why now:** 67-9 is the **Layer 2 follow-up explicitly deferred from completed story 67-8** (done 2026-05-29). I verified the work is genuinely open before setup: no `67-9` branch and no `67-9` PR in `sidequest-ui`, sprint YAML status `backlog`, working tree clean on `develop`. 67-8 shipped a three-layer fix to the duplicate-socket reconnect loop but deferred the architectural root cause: the WebSocket connection + slug-connect handshake live in `AppInner` inside the per-route `LobbyRoot` (the shared `element` of three `<Route>`s) under `<StrictMode>`, so any route transition, `#/dashboard` hash toggle, or StrictMode double-mount remounts the socket-owning tree and re-runs the full connect handshake. Layers 1+3 (already merged) made that re-handshake *harmless* (no duplicate socket; no commit during AwaitingConnect), but the churn itself remains. This story eliminates it at the root by hoisting the connection + handshake latch above `<Routes>`. Both the 67-8 Architect (reconcile) and Dev (delivery finding) recorded this as own-RED-tests + own-review follow-up work — real, unduplicated.

**Scope guardrails for TEA:**
- This is a `type: refactor` of a ~2300-line `App.tsx`. **Minimalist discipline, contain risk** — 67-8 deferred Layer 2 precisely to avoid cramming an untested connection-ownership refactor into a green phase. Own RED tests, own review cycle.
- The connect path is currently gated on the **per-mount** `slugConnectFired` *ref* (`App.tsx` ~:1691-1790) — a remount recreates the ref (→false) and re-runs the whole connect. The latch must be hoisted *with* the connection to a stable owner above `<Routes>` so it fires once per page-session.
- The trigger-independent observable (AC3) is OTEL: across a route transition / dashboard-hash toggle mid-session, **no second `ws.connection_accepted`/`chargen_gate` cycle** and **`presence.multi_socket_attach` never fires** (`session_room.py` spans + the 67-7 `session_unbound` watcher event are the ready-made instruments).
- Reuse, don't reinvent: the 67-8 Layer 1 work (`useWebSocket.createSocket` close-orphan; `connect()` no-op-when-OPEN) and Layer 3 (`sessionBound` beat-commit gate) already landed — RED must keep the `useWebSocket-67-8` duplicate-socket invariants green (AC4/AC5 = no regression).

**No-Silent-Fallbacks reminder:** reconnect must remain a genuine socket-drop → server-resume path, not a silent re-handshake; a genuinely unbound frame must still reject loudly.

**Branch:** `feat/67-9-hoist-websocket-above-routes` cut off `develop` (gitflow, base `develop`). No Jira key (Jira not configured — explicitly skipped, no silent fallback). No blocking open PRs.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-30T20:48:44Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30 | 2026-05-30T19:25:12Z | 19h 25m |
| red | 2026-05-30T19:25:12Z | 2026-05-30T19:36:33Z | 11m 21s |
| green | 2026-05-30T19:36:33Z | 2026-05-30T19:43:17Z | 6m 44s |
| spec-check | 2026-05-30T19:43:17Z | 2026-05-30T19:45:12Z | 1m 55s |
| verify | 2026-05-30T19:45:12Z | 2026-05-30T19:51:42Z | 6m 30s |
| review | 2026-05-30T19:51:42Z | 2026-05-30T20:04:28Z | 12m 46s |
| red | 2026-05-30T20:04:28Z | 2026-05-30T20:15:39Z | 11m 11s |
| green | 2026-05-30T20:15:39Z | 2026-05-30T20:31:50Z | 16m 11s |
| spec-check | 2026-05-30T20:31:50Z | 2026-05-30T20:32:37Z | 47s |
| verify | 2026-05-30T20:32:37Z | 2026-05-30T20:35:19Z | 2m 42s |
| review | 2026-05-30T20:35:19Z | 2026-05-30T20:47:42Z | 12m 23s |
| spec-reconcile | 2026-05-30T20:47:42Z | 2026-05-30T20:48:44Z | 1m 2s |
| finish | 2026-05-30T20:48:44Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** This is a `type: refactor` with a concrete, observable behavioral contract (route/dashboard/StrictMode remounts must NOT re-run the connect handshake). 67-8 deferred Layer 2 specifically so it would get its own RED tests + review — the chore bypass ("refactoring with existing coverage") does NOT apply, because there is no existing coverage of the *no-re-handshake-on-remount* invariant. The 67-8 hook suite covers duplicate-socket elimination at the `useWebSocket` layer; it does not exercise the App-level remount trigger.

**Test Files:**
- `sidequest-ui/src/__tests__/app-dashboard-toggle-rehandshake-67-9.test.tsx` — mounts the real production `<App>` at `/solo/:slug`, drives the slug-connect handshake to completion, then toggles `#/dashboard` on→off mid-session (the pinned, deterministic remount trigger) and asserts the handshake does not re-fire.

**Tests Written:** 5 tests covering AC1–AC5.

| Test | AC | RED/Guardrail | Observable |
|------|----|----|-----------|
| clean slug mount fires handshake exactly once | AC5 | guardrail (passes) | 1 GET `/api/games/:slug`, 1 socket constructed |
| `#/dashboard` toggle fires NO second GET | AC1/AC3 | **RED** | `gameMetaGetCount` stays 1 (pre-fix: 2) |
| `#/dashboard` toggle opens NO second WebSocket | AC1/AC3 | **RED** | `constructedSockets.length` stays 1 (pre-fix: 2) |
| connection persists across toggle (original socket stays OPEN) | AC2 | **RED** | `firstSocket.readyState === OPEN` (pre-fix: CLOSED, torn down on AppInner unmount) |
| initial handshake sends well-formed SESSION_EVENT{connect} | AC4 | guardrail (passes) | payload `event`/`game_slug`/`player_name` intact |

**Status:** RED confirmed via `testing-runner` (run 67-9-tea-red): 5 tests, **2 passed / 3 failed**. The three RED failures are exactly the predicted mechanism — the mid-session dashboard remount re-runs the handshake (2nd GET `expected 2 to be 1`; 2nd socket `length 2`; original socket `readyState 3 = CLOSED`). The two guardrails pass, proving the harness drives the real production handshake and that initial connect is healthy (so the GREEN hoist must not regress it).

### Rule Coverage (lang-review: typescript.md)

| Concern | How covered |
|---------|-------------|
| Meaningful assertions (no vacuous tests) | Every assertion is a concrete count/state (`toBe(1)`, `toHaveLength(1)`, `readyState === OPEN`); failures read `expected 2 to be 1`. Rejected the tempting-but-vacuous `WS.instances.length` check (it counts mock *servers*, of which the harness makes exactly one → always 1 regardless of client reconnects). Replaced with a real client-socket count via a WebSocket-constructor Proxy. |
| No Silent Fallbacks | AC4 reuse: the genuine socket-drop → reconnect path stays covered by the already-green `useWebSocket-67-8-duplicate-socket.test.ts` (its reconnect invariant). Not re-litigated; the hoist must keep that suite green (verify-phase check). |
| Wiring (every suite needs a wiring test) | The RED tests mount the real production `<App>`/`<AppRoutes>`/`<LobbyRoot>` tree — the handshake is exercised through the actual production path, not a harness stub. This IS the integration/wiring proof. |
| Fix-agnostic observables | Both RED observables (GET count, socket count/state) are mechanism-independent — they pass for any hoist shape (context provider, lifted component, router-level owner) and assert only the spec's behavioral outcome, never a guessed component name. |

**Rules checked:** typescript.md test-quality + project No-Silent-Fallbacks + No-Stubbing + wiring-test rules have coverage.
**Self-check:** 1 latent vacuous assertion caught and removed before commit (the `WS.instances` server-count check → replaced with the Proxy client-socket tracker).

**Handoff:** To Dev (Agent Smith) for the GREEN implementation — hoist the WebSocket connection + slug-connect handshake to a stable owner above `<Routes>` so the three RED tests go green without regressing the two guardrails or the 67-8 suite.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/App.tsx` — `LobbyRoot` now renders the session tree (`<GameStateProvider><AppInner/></GameStateProvider>`) **unconditionally** (removed the `#/dashboard` conditional + its `isDashboard` state + `hashchange` effect). The dashboard was hoisted to a new `DashboardGate` component rendered **above `<Routes>`** in `App` as a hash-driven, opaque, full-screen overlay (`position:fixed; inset:0; zIndex:1000`). The session-owning tree — and therefore the WebSocket connection + slug-connect handshake — is no longer unmounted when the GM dashboard opens/closes.

**The fix (root cause → remedy):** Pre-67-9 the `#/dashboard` toggle inside the per-route `LobbyRoot` *replaced* `AppInner`, unmounting it. `useWebSocket`'s unmount cleanup (`useWebSocket.ts:271`) closed the socket; toggling back remounted `AppInner` with a fresh `slugConnectFired` ref → the slug-connect effect re-fetched `/api/games/:slug`, re-opened a socket, and re-sent `SESSION_EVENT{connect}` (the second `ws.connection_accepted`/`chargen_gate` cycle). Rendering the session tree unconditionally and layering the dashboard above `<Routes>` keeps the single connection alive for the whole page-session; the live session simply sits underneath the overlay.

**Why NOT a literal `useGameSocket`-above-`<Routes>` lift:** see the Design Deviation below. In short: `AppInner` is ~2100 lines / 101 hooks and the socket's `onMessage` IS `handleMessage` (App.tsx:556), which is bound to dozens of `AppInner` setState calls. Relocating the connection itself above `<Routes>` means relocating essentially the whole app shell — the opposite of 67-8's explicit "contain risk" scoping for Layer 2. Route-to-route nav was already remount-safe (react-router v6 element reuse, confirmed by `lobby-start-ws-open.test.tsx`), so the dashboard conditional was the sole live remount trigger; hoisting the dashboard removes it.

**Tests:** 5/5 green on `app-dashboard-toggle-rehandshake-67-9.test.tsx` (3 RED→GREEN: no 2nd GET, no 2nd socket, original socket stays OPEN; 2 guardrails still pass). Full sidequest-ui suite **1674/1674** green (173 files) via `testing-runner` run `67-9-dev-green` — the App/AppRoutes/LobbyRoot restructure caused zero regressions. The 67-8 duplicate-socket suite + `lobby-start-ws-open` + `slug-routing` + beat-commit-session-bound all stay green.

**OTEL note:** This is a pure UI render-tree restructure (no subsystem decision logic), so no new OTEL spans are added — consistent with the CLAUDE.md "not needed for cosmetic/structural UI" carve-out. AC3's server-OTEL half (no 2nd `chargen_gate`, `presence.multi_socket_attach` silent) is validated at the next live playtest per the TEA finding; the existing 67-7 `session_unbound` + `presence.multi_socket_attach` spans are the instruments.

**Branch:** `feat/67-9-hoist-websocket-above-routes` (pushed).

**Handoff:** To TEA (The Architect) for the verify phase (simplify + quality-pass).

## Dev Assessment (rework — round-trip 1, green)

**Implementation Complete:** Yes (rework was test-only; production `App.tsx` unchanged from the original green)

**What this green phase did:** The rework was triggered by the Reviewer's HIGH blocker — a *flaky test*, not a production defect (the hoist is correct; reviewer-security clean; the app socket survives). TEA's red-rework replaced the contaminated global socket-count with GET-count + app-socket-lifecycle observables. On my green confirmation I **ran the real CI command directly** (not a `testing-runner` summary — this story already proved those can report false-green) and caught a **residual flake**: 1 failure across 27 runs (~3.7%). Root cause: mock-socket routes *other test files'* `ws://host/ws` sockets to this test's server, so the post-toggle `liveAppSockets()` array re-scan could still admit a foreign OPEN socket at the assertion instant.

**Final hardening (test-only, `64ec95e`):** Assert **only the captured `appSocket` instance's `readyState`** across the toggle — no foreign socket can mutate a specific instance, so it is contamination-proof *by construction*. `liveAppSockets()` is now used only for the synchronous capture at mount (lowest-contamination moment, tolerant of foreign sockets via `>= 1`); the post-toggle array re-scans were dropped. See the Dev deviation below for the role rationale.

**Verification (direct CI command, not summarized):**
- **Flake eliminated:** full suite **0/30 runs failed** (1674/1674 each).
- **RED-pre-fix contract intact:** `git checkout develop -- src/App.tsx` → 67-9 file **3 failed / 2 passed** (the immune observables still catch the bug: post-toggle `appSocket` goes CLOSED + 2nd GET fires). Restored the fix after.
- eslint 0 problems on the test file; no tsc errors introduced.

**Deferred (unchanged from TEA's rework):** the Reviewer's MEDIUM production recommendations — `ErrorBoundary` around the dashboard `Suspense` (epic-67 resilience: session survives a *broken* dashboard) and a `popstate` listener (Back closes the overlay) — remain documented follow-up findings, not implemented here (no RED tests authored; non-blocking; would expand scope beyond the rework's blocker). The ErrorBoundary is the highest-value fast-follow.

**Branch:** `feat/67-9-hoist-websocket-above-routes` (pushed, through `64ec95e`).

**Handoff:** To Architect (Neo) for spec-check.

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected (one Major architectural-mechanism divergence — behaviorally aligned, already logged by Dev)
**Mismatches Found:** 1 (plus 2 acceptance-observable deferrals carried from TEA/Dev, both endorsed)

Structural gate `spec-check` passed: all 5 ACs have Dev Assessment coverage, implementation marked complete, TEA + Dev deviation subsections well-formed. I verified the substance by reading the `git diff develop -- src/App.tsx` (surgical ~40-line change to the routing tail: `LobbyRoot` de-conditionalized; new `DashboardGate` overlay above `<Routes>`; `App` renders both as siblings). The diff matches the Dev Assessment precisely.

**Per-AC substance check:**

| AC | Behavioral intent | Literal mechanism | Verdict |
|----|----|----|----|
| AC1 (connection owned above `<Routes>`; remounts don't re-run handshake) | **MET** — dashboard trigger removed; route nav already v6-reuse-safe; StrictMode latch-deduped | NOT met — `useGameSocket` still in `AppInner` | Drift (below) |
| AC2 (latch hoisted with connection; fires once per page-session; genuine drop still reconnects) | **MET** — `AppInner` never unmounts → latch fires once; 67-8 reconnect suite green | NOT met — latch still in `AppInner` | Drift (below) |
| AC3 (OTEL: no 2nd `ws.connection_accepted`/`chargen_gate`; `presence.multi_socket_attach` silent) | client half **MET** (tested green); server half **deferred to playtest** | n/a | Endorsed deferral |
| AC4 (regression coverage; 67-8 invariants stay green) | **MET** — full suite 1674/1674 + 67-8 duplicate-socket suite green | — | Aligned |
| AC5 (chargen/slug-resume/reconnect/sessionBound gate preserved) | **MET** — full suite green | — | Aligned |

**Mismatch 1 — Connection NOT literally hoisted above `<Routes>`; dashboard hoisted instead** (Different mechanism — Architectural, Major)
- Spec: AC1/AC2 — "The WebSocket connection + slug-connect handshake are owned by a stable component ABOVE `<Routes>`."
- Code: `useGameSocket` + the slug-connect handshake stay in `AppInner` (inside `<Routes>`); the `#/dashboard` view was hoisted to `DashboardGate` above `<Routes>`, and `LobbyRoot` now renders the session tree unconditionally so the dashboard toggle never unmounts it. The behavioral guarantee AC1's "so..." clause specifies is fully achieved; the literal structural claim is not.
- Recommendation: **A (update spec) + D (defer the durable seam).** The implementation reveals the goal ("no remount re-handshake") is best served by hoisting the *actual remount trigger* (the dashboard), not by relocating the connection. A literal lift requires moving ~2100 lines / 101 hooks of `AppInner` + `handleMessage` (the socket's `onMessage`, App.tsx:556, bound to dozens of `AppInner` setState calls) into a provider above the router — directly against 67-8's explicit "contain risk" scoping for Layer 2, and for **zero current behavioral gain** (no live per-route path remounts `AppInner` today; route nav is v6-reuse-safe). I read AC1's intent as "the connection must not be torn down by remounts," which is met. The durable `SocketProvider`-above-`<Routes>` seam (relocating `useGameSocket`+`handleMessage`) is genuinely own-story-sized and is deferred (Dev logged it as a finding) — needed only if a future story introduces a new per-route `AppInner` remount path. **Not Option B:** forcing the literal lift now would be an un-contained, high-risk refactor with no behavioral payoff. Dev's deviation entry already captures this with full 6-field rationale; I endorse it as-written and will confirm the manifest in spec-reconcile.

**Two endorsed acceptance-observable deferrals** (carried, non-blocking): (1) AC3 server-OTEL half validated at next live playtest (a clean synthetic run can't distinguish fixed-from-unfixed — same disposition the 67-8 Architect/Reviewer accepted); (2) StrictMode-double-mount trigger covered transitively (the fix stops `AppInner` being unmounted at all, so it survives StrictMode's remount too) rather than by a dedicated assertion. Both sound.

**Operator decision-point (flagged, not blocking):** AC1 was authored as "hoist the connection above `<Routes>`." My architectural judgment endorses the dashboard-hoist as the correct, intent-satisfying, risk-appropriate realization for this story. If the Operator specifically wants the connection object itself relocated above the router, that is a separate, larger story (the deferred `SocketProvider` seam), not a 67-9 code fix.

**Decision:** Proceed to review (via TEA verify). No code change required — behavioral ACs met, full suite green, risk contained per 67-8's mandate.

### Architect Assessment (spec-check — rework round-trip 1)

**Spec Alignment:** Aligned (unchanged from the first spec-check). **Mismatches:** none new.

The rework diff (`git diff 634d1b6 HEAD`) is **test-file only** — production `App.tsx` is byte-identical to the version I already spec-checked and endorsed. So the AC alignment is unchanged: the one Major dashboard-hoist deviation (behaviorally aligned, Architect/Reviewer-endorsed) stands. I confirmed the **hardened test observable still validly covers the ACs**: AC1/AC3 = GET-count (no re-handshake) + captured `appSocket.readyState` (no second app socket — the app only opens a socket via the GET-gated `connect()`); AC2 = `appSocket.readyState` OPEN (connection persists); AC4/AC5 = payload contract + baseline. Coverage is intact and arguably stronger — the instance-level `readyState` observable is contamination-proof, and TEA/Dev verified it is **0/30 flaky** while still **RED against pre-fix** (3 failed). The Reviewer's blocker (flaky suite) is resolved; the MEDIUM `ErrorBoundary`/`popstate` recommendations remain endorsed-as-deferred follow-ups. **Decision:** Proceed to review (via TEA verify).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 2 (`src/App.tsx` diff vs develop + `src/__tests__/app-dashboard-toggle-rehandshake-67-9.test.tsx`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 4 findings (3 high, 1 medium) | All cross-file extractions of **pre-existing** duplication / unrelated components |
| simplify-quality | clean | No findings — the 67-9 change is well-structured, typed, wired |
| simplify-efficiency | 2 findings (1 medium, 1 low) | Benign style redundancy; defensive mock branches |

**Applied:** 0 high-confidence fixes.
**Flagged for Review:** 0 (none warrant Reviewer action).
**Noted/Deferred:** 6 (dispositions below).
**Reverted:** 0.

**Overall:** simplify: clean (no fixes applied — all findings are out-of-scope or benign)

**Why zero fixes applied (disposition per finding):**
- **reuse #1 — extract `useHashMatch` hook (App.tsx:2372 + narrativeRenderers.tsx):** DECLINE/DEFER. The hash-listener in `DashboardGate` is 8 lines *moved verbatim* from the old `LobbyRoot` (not newly authored). Extracting a shared hook would pull in `narrativeRenderers.tsx` — a file unrelated to 67-9's transport-resilience scope — expanding the blast radius of a deliberately-contained Layer-2 refactor. No test demands it. Noted as future cleanup.
- **reuse #2/#3 — extract shared `makeFetchMock` / `seedTrustedIdentity` (14+ / 5+ test files):** DECLINE/DEFER. Verified the duplication is **pre-existing on `develop`** (`git grep makeFetchMock develop` → 14+ files). 67-9 follows the established suite-wide test-harness convention; consolidating it is a genuine but separate test-infra chore, not a verify-phase auto-fix that should touch a dozen unrelated files. Logged as a delivery finding.
- **reuse #4 — extract `installWebSocketCounter` (medium):** DEFER. Not currently duplicated; premature to hoist.
- **efficiency #5 — Suspense fallback bg duplicates overlay bg (App.tsx:2392, medium):** NOTE only. The fallback's `background:#1a1a2e` is preserved verbatim from the original top-level dashboard render; it's defensive (the centered loader keeps its bg independent of the wrapper) and visually a no-op. Not worth a cosmetic edit + re-run risk for a MEDIUM cosmetic redundancy.
- **efficiency #6 — `makeFetchMock` 4 patterns, test uses 2 (low):** DECLINE. The `/api/genres` + `/api/sessions` branches are **defensive against App's boot fetches** (lobby/ConnectScreen hit them on mount); removing them risks the catch-all returning a wrong-shaped Response → flaky regression. Keep.

**Quality Checks:** All passing — full sidequest-ui suite **1674/1674** (173 files, run `67-9-tea-verify`); eslint on the 2 changed files: **0 errors, 0 new warnings** (the 2 App.tsx warnings at :1344/:1939 are pre-existing, outside the diff). No simplify changes applied → no regression-detection pass needed (tree identical to Dev's green state).

**Handoff:** To Reviewer (The Merovingian) for code review.

## TEA Assessment (rework — round-trip 1, red)

**Trigger:** Reviewer REJECTED — the suite was flaky: `npx vitest run` (full suite) failed AC2 ~3/5 (`constructedSockets.length` saw 2 ≠ 1) while passing in isolation. Production hoist confirmed correct; the **test observable** was contaminated.

**Root cause (confirmed):** `installWebSocketCounter` installs a Proxy on the **global** `WebSocket` and pushes *every* `new WebSocket()` into a module-level array. Other test files' lingering reconnect timers (useWebSocket fixed 1000 ms backoff) construct sockets to the **same `ws://<host>/ws` URL** during this file's run, and the global Proxy captures them → ghost entries. Empirically reproduced: 3/5 full-suite runs failed; `ws://${location.host}/ws` is used by 41 test files, so URL alone can't distinguish the ghost.

**Fix (test-only — no production change):** Replaced the contaminated global-construction count with two **contamination-immune** observables:
1. **GET `/api/games/:slug` count** (`gameMetaGetCount`) — only App's slug-connect fetches this URL; immune to foreign sockets.
2. **The app's own socket lifecycle** — `liveAppSockets()` filters `constructedSockets` to `readyState === OPEN && url === APP_WS_URL`; tests capture the specific `appSocket` instance from `mountAndConnect()` and assert it stays OPEN and is never replaced (`liveAppSockets() === [appSocket]`).

The app opens a socket only via `connect()`, which is gated by the slug-connect GET — so **"GET stays 1" + "appSocket stays OPEN, not replaced"** proves no re-handshake and no second app socket, without counting global constructions. Foreign ghosts (abandoned reconnect sockets that never reach OPEN, or close) are excluded by the OPEN+URL filter.

**Verification:**
- **Still RED against pre-fix** (`git checkout develop -- src/App.tsx`): 3/5 fail (2nd GET → `gameMetaGetCount===2`; `appSocket` CLOSED) — the observables still catch the bug, TDD contract intact. Restored the fix after.
- **GREEN + non-flaky**: full suite **6/6 runs green** (1674/1674); 67-9 file 5/5 in isolation. eslint 0 problems on the test file; no tsc errors.

**Also addressed (LOW review findings, in the test file):** stale `setDashboard` JSDoc (`LobbyRoot`→`DashboardGate`); added `expect(connectMsg.type).toBe("SESSION_EVENT")` to AC4; per-cast explanatory comments on the two Proxy `as unknown as` casts; removed the unguarded `constructedSockets[0]!` (now `mountAndConnect` returns the app socket, guarded by `toHaveLength(1)`).

**Deferred (recommended MEDIUM/LOW production findings — NOT in this rework):** The Reviewer's `ErrorBoundary`-around-dashboard-Suspense and `popstate`-listener recommendations are production changes that would need their own RED tests; they are non-blocking (MEDIUM) and pre-existing-adjacent. To honor 67-8's "contain risk" mandate and keep the rework scoped to the blocker, I did **not** expand 67-9 to include them — they remain documented delivery findings for a fast-follow story. (The ErrorBoundary one is the highest-value follow-up: it closes the session-survives-a-*broken*-dashboard gap that 67-9's always-mounted session widened — worth a quick story.) Reviewer/Operator may choose to require them, in which case I'll author the RED tests.

**Handoff:** To Dev (Agent Smith) for green — the production code is unchanged and the suite is green, so green is a confirmation pass (no new failing tests to implement against). If the Operator wants the ErrorBoundary/popstate bundled, route back to me for RED tests first.

## TEA Assessment (verify — rework round-trip 1)

**Phase:** finish (rework) · **Status:** GREEN confirmed, deterministic

**Scope:** Since the original verify, the only changed file is the test (`git diff 634d1b6 HEAD` = test-only); production `App.tsx` is byte-identical to the version that passed the first verify's simplify fan-out (clean for the 67-9 change). So I did **not** re-spawn the full simplify fan-out on unchanged production code — I self-reviewed the test delta (the contamination-immune observable hardening I co-authored with Dev's final instance-level fix).

**Simplify (applied):** Resolved the one outstanding Reviewer-simplifier LOW finding — dropped the unused `flush(ticks = 4)` parameter (every call site used the default; inlined the constant `4`, commit `83f4b2b`). `liveAppSockets()` is still used (mount-time capture) — not dead. No other simplification warranted in the test delta.

**Quality-pass:**
- Full suite green and **non-flaky** — re-confirmed 3/3 this phase (on top of Dev's 0/30 and the round-trip-1 6/6); eslint 0 problems on the test file; no tsc errors.
- The contamination-immune observable (Dev's final form: captured `appSocket.readyState` across the toggle + GET-count) holds; still RED against pre-fix (verified in green).

**Overall:** simplify: applied 1 trivial fix (flush param) · quality: clean.

**Handoff:** To Reviewer (The Merovingian) for re-review — the round-trip-1 blocker (flaky suite) is resolved (0/30 + 3/3); recommended MEDIUM ErrorBoundary/popstate remain documented deferrals.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (full-suite test failure) + lint clean | confirmed 1 (BLOCKER), 0 dismissed |
| 2 | reviewer-edge-hunter | Yes | findings | 4 (popstate, ErrorBoundary, hash-norm, aria-hidden) | confirmed 3, downgraded 1 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 (ErrorBoundary, mock catch-all, DashboardApp swallow) | confirmed 1 (MED), 1 LOW, 1 deferred (pre-existing/out-of-diff) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (flush, afterEach order, missing-reconnect, AC4 type, mock slug) | confirmed 0 blocking; 5 LOW/improvement |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (stale LobbyRoot JSDoc, "ABOVE" wording) | confirmed 1 LOW, 1 trivial |
| 6 | reviewer-type-design | Yes | findings | 2 (Proxy static cast, nextMessage cast) | dismissed 1 (rationale), 1 LOW |
| 7 | reviewer-security | Yes | clean | none | N/A — VERIFIED no perception-firewall leak |
| 8 | reviewer-simplifier | Yes | findings | 1 (flush dead param) | confirmed 1 trivial |
| 9 | reviewer-rule-checker | Yes | findings | 4 (2× as-unknown-as comment, 2× non-null `!`) | confirmed 4 LOW (guarded/contextual) |

**All received:** Yes (9 returned, 8 with findings, 1 clean)
**Total findings:** 1 confirmed HIGH/blocking, 2 confirmed MEDIUM, ~10 LOW/trivial, 1 dismissed (with rationale), 1 deferred (pre-existing)

## Reviewer Assessment

**Verdict:** REJECTED

**The blocker is a test-isolation defect, not a production-code defect.** The App.tsx hoist is sound — reviewer-security returned clean (no perception-firewall leak from the now-always-mounted session), the diff is minimal and correct in shape, and AC2's `firstSocket.readyState === OPEN` assertions **pass** (proving the original socket genuinely survives the dashboard toggle — the fix works). But the new test's socket-count observable is not robust, so the **full suite fails the real CI command deterministically**.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **Full-suite test failure (test isolation).** `npx vitest run` fails 3/3 runs: AC2 `expect(constructedSockets).toHaveLength(1)` → "got 2". Passes in isolation; fails in full-suite. `installWebSocketCounter` installs a Proxy on `globalThis.WebSocket` and pushes **every** `new WebSocket()` into a module-level array — so a foreign socket constructed by another test file's lingering async (reconnect timers; useWebSocket uses fixed 1000 ms backoff) lands in `constructedSockets` during AC2, inflating the count. `readyState` assertions pass → production code is correct; the **observable** is contaminated. This also explains why the `testing-runner` subagent reported false-green 1674/1674 during dev-green and tea-verify. | `src/__tests__/app-dashboard-toggle-rehandshake-67-9.test.tsx:284` (+ the counter at :113) | Make the observable robust to cross-file contamination: filter counted sockets to the test's own URL (`ws://localhost/ws`), or snapshot a baseline count at mount and assert the **delta** is 0 across the toggle, or assert socket identity (the same `firstSocket` instance, no new instance) rather than a global length. Must make `npx vitest run` (full suite) green 3/3. |

**Strongly recommended to bundle into the rework** (MEDIUM — non-blocking by the severity table, but cheap and directly serves the story's goal while the branch is reopened):

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| [MEDIUM] | **`DashboardGate`'s `<Suspense>` has no `ErrorBoundary`** `[SILENT]`+`[EDGE]` (both flagged). A `LazyDashboard` chunk-load failure propagates past Suspense to the root (main.tsx has no boundary) and **unmounts the whole tree — including the now-always-mounted live session**. Pre-67-9 the missing boundary existed too, but the session wasn't mounted under the dashboard, so 67-9 *widens the blast radius* to orphan the very session it exists to preserve — counter to epic-67's resilience mission and the 67-1 `ErrorBoundary name="Game"` precedent. | `src/App.tsx` DashboardGate Suspense | Wrap in `<ErrorBoundary name="Dashboard">` (already imported, used at App.tsx:2019). Confines a dashboard failure to the overlay; the session underneath survives — completing 67-9's intent. |
| [MEDIUM] | **`popstate` not handled** `[EDGE]`. After `window.location.hash = "#/dashboard"`, the browser Back button fires `popstate`, not `hashchange` — so `isDashboard` stays true and the opaque overlay stays stuck over the live session. (Pre-existing in the old LobbyRoot, but now it strands a full-screen overlay over a live session.) | `src/App.tsx` DashboardGate useEffect | Add a `popstate` listener alongside `hashchange` (same handler reading `window.location.hash`). |

**Confirmed LOW / non-blocking (address opportunistically in the rework):**
- `[DOC]` Stale JSDoc: `setDashboard` says "the hashchange **LobbyRoot** listens for" — the listener moved to `DashboardGate`. Trivial one-line fix. (test:128)
- `[EDGE]` Hash equality is strict — `#/dashboard/`, `#/dashboard?x=1` silently don't open the overlay. Pre-existing semantics; normalize if desired. (LOW)
- `[EDGE]` No `aria-hidden`/`inert` on the underlying session while the opaque overlay is shown — a11y/focus reachability. (LOW)
- `[RULE]` `as unknown as` casts (test:117/124) lack a *per-cast* comment — the block comment (test:106-110) explains the Proxy approach contextually; recommend a one-line inline note. (LOW — rule-match, downgraded: the "why" is documented in the adjacent block.)
- `[RULE]`/`[TYPE]` `constructedSockets[0]!` (test:269) non-null assertion — guarded by `toHaveLength(1)` on the prior line; cleaner as `toBeDefined()` + narrowing. (LOW)
- `[TEST]` `afterEach` ordering (`globalThis.WebSocket = realWebSocket` before `WS.clean()`) is correct but fragile/undocumented — relevant to hardening the isolation fix above.
- `[TEST]` Missing negative test: a genuine socket drop → reconnect under the new architecture (AC4-reuse defers to the 67-8 suite, which predates the hoist). Worth one explicit test.
- `[TEST]` AC4 omits `expect(connectMsg.type).toBe("SESSION_EVENT")` (present in `mountAndConnect`); `makeFetchMock` doesn't assert the slug in the GET URL. (LOW)
- `[SIMPLE]` `flush(ticks = 4)` parameter is never varied — drop it. (trivial)

**Dismissed (with rationale):**
- `[TYPE]` test:124 `Counting as unknown as typeof WebSocket` "hides static constants (WebSocket.OPEN etc.)" — **dismissed.** A JS Proxy with only a `construct` trap forwards all other operations, including static property reads, to the target via default `Reflect.get`; the AC2/AC5 tests read `WebSocket.OPEN` and the readyState assertions pass, empirically confirming the statics resolve. The cast is the canonical, sound way to reassign `globalThis.WebSocket`.

**Deferred (pre-existing, outside the 67-9 diff):**
- `[SILENT]` `DashboardApp.tsx:294` `loadDebugState` swallows fetch errors with an empty catch — pre-existing, `DashboardApp` is not in this diff. Logged as a delivery finding for a future dev-tool-observability story.

**Data flow traced:** `#/dashboard` hash → `hashchange` → `DashboardGate.setIsDashboard(true)` → opaque overlay renders above `<Routes>`; the session tree (`AppRoutes → LobbyRoot → AppInner → useGameSocket`) stays mounted underneath (verified: AC2 `firstSocket` stays OPEN). Slug → `useParams` in `AppInner` → handshake — unchanged, AC4/AC5 green.
**Pattern observed:** Global-overlay-above-router is a sound pattern; the connection-ownership stays in `AppInner` (Architect-endorsed deviation — see deviation audit).
**Error handling:** The gap is the missing `ErrorBoundary` around the lazy dashboard (MEDIUM, above).
**Security:** `[SEC]` reviewer-security returned clean — `DashboardGate` reads the `#/dashboard` hash as a boolean (never injected into the DOM), passes no session/player data to the dashboard, and the always-mounted session shares no React context with the dashboard subtree (no perception-firewall leak). No secrets in the diff.

**Devil's Advocate:** The damning case against this code is that *its own test suite does not pass* — the deliverable fails `npx vitest run` every time, and two upstream `testing-runner` reports masked it as green, which means the pipeline's own verification was lying. A reviewer who trusted those reports would have merged a red suite. Beyond the test: a malicious/unlucky user who opens the GM dashboard during a deploy (chunk hash skew → 404 on the lazy import) crashes the entire client and loses the live session — the exact orphaning epic-67 was built to prevent, now reachable through the very feature meant to preserve the session. A confused user who opens the dashboard then hits browser-Back is stranded behind an opaque overlay with no escape (popstate unhandled). None of these are hypothetical edge-trivia: the test failure is reproduced 3/3, the chunk-404 is a real deploy reality, and Back-button is a reflex. The production hoist is genuinely correct and well-reasoned — but "the code works" is not the bar; "the suite proves it and the failure modes are handled" is, and right now the suite is red.

**Handoff:** Back to TEA (The Architect) — the blocker is a test-design/observable defect (testable → red rework). TEA hardens the socket-count observable so the full suite is green; the recommended production fixes (ErrorBoundary, popstate, stale comment) flow to Dev in the ensuing green phase.

## Subagent Results (re-review — round-trip 1)

Production `App.tsx` is byte-identical to round-trip-0 (rework was test-file only). Subagents re-ran on the full current diff, scoped to the test delta + blocker-resolution confirmation.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | flake RESOLVED — 3/3 green, 0 lint errors | confirmed blocker-resolved |
| 2 | reviewer-edge-hunter | Yes | findings | 6 (capture `>=1`, AC4 await, flush-timing, setDashboard act, WS-order, AC4) | 0 confirmed-blocking; all downgraded/refuted (below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (silent foreign-socket capture) | refuted empirically; documented as non-blocking hardening rec |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (capture `>=1`, AC2/no-2nd-WS redundancy, missing reconnect, 2-cycle) | 0 blocking; validated RED-contract + capture sound |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 ("single"/"immune" JSDoc precision) | LOW; RT0 stale JSDoc confirmed fixed |
| 6 | reviewer-type-design | Yes | findings | 2 (nextMessage cast guard; SessionEventPayload game_slug) | LOW/out-of-diff; RT0 type findings RESOLVED |
| 7 | reviewer-security | Yes | clean | none | re-affirmed clean (no new data flow) |
| 8 | reviewer-simplifier | Yes | findings | 2 (Proxy→server.clients; inline helper) | MEDIUM, speculative API; non-blocking |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations | all 3 RT0 findings confirmed RESOLVED |

**All received:** Yes (9 returned, 6 with findings, 3 clean)
**Total findings:** 0 confirmed blocking · ~12 LOW/MEDIUM non-blocking · 1 empirically refuted · all 3 round-trip-0 blockers/findings RESOLVED

## Reviewer Assessment (re-review — round-trip 1)

**Verdict:** APPROVED

**The round-trip-0 blocker (flaky suite) is resolved, and every round-trip-0 finding is confirmed fixed.** The full suite is now deterministically green: **0/40 failed** (my direct flake check) + Dev's 0/30 + preflight's 3/3 = **70+ clean `npx vitest run` runs**. Production `App.tsx` is byte-identical to the version reviewer-security and I already cleared in round-trip-0 (the rework was test-file only). The reworked observable still goes **RED against pre-fix** (3/5 toggle tests fail) — TDD contract intact.

**Round-trip-0 findings — all resolved (verified by rule-checker + type-design + comment-analyzer + me):**
- `as unknown as` Proxy casts now carry per-cast explanatory comments. ✓
- The unguarded `constructedSockets[0]!` is gone — `mountAndConnect` returns the app socket, guarded by `expect(app.length).toBeGreaterThanOrEqual(1)`. ✓
- The contaminated global `constructedSockets.length`/`toEqual([appSocket])` observable is replaced by the instance-level `appSocket.readyState` + GET-count (contamination-immune). ✓
- Stale `setDashboard` JSDoc (`LobbyRoot`→`DashboardGate`) corrected; `flush(ticks)` dead param dropped; AC4 `SESSION_EVENT` type assertion added. ✓

**The one finding worth a hard look — three subagents converged (edge-hunter HIGH, silent-failure MED, test-analyzer MED): `>= 1` + `app[0]` could *silently* capture a foreign `/ws` socket at index 0, tracking the wrong instance → false-green.** I **refute this empirically and decline the suggested `toBe(1)` fix:**
- `toBe(1)` at capture is the assertion that *flaked* — a foreign OPEN socket makes it 2; `>= 1` + instance-tracking is the deliberate contamination-tolerant design.
- **Decisive evidence the capture is reliably App's own socket:** in the RED-pre-fix verification, all 3 toggle tests *reliably* fail with `appSocket` → CLOSED. A foreign socket would NOT close on my dashboard toggle — so if the capture ever grabbed a foreign socket, the pre-fix toggle tests would intermittently *pass* (foreign stays OPEN). They don't (3/5, with the 2 passes being the AC4/AC5 guardrails that pass by design pre+post). The reliable pre-fix-CLOSED behavior proves `app[0]` is reliably App's socket.
- A green flake-check can't detect a silent-false-green (it passes either way) — but the RED-pre-fix reliability *can*, and it confirms correct capture across the runs.
- **Disposition:** valid theoretical race, empirically non-manifesting; documented as a non-blocking hardening recommendation (deterministic capture or fail-loud), not a blocker.

**Clean / refuted specialists (tagged for completeness):** `[SEC]` reviewer-security — clean, re-affirmed (no new data flow, no perception-firewall leak). `[RULE]` reviewer-rule-checker — clean, 0 violations, all 3 round-trip-0 findings confirmed resolved. `[SILENT]` reviewer-silent-failure-hunter — the one finding (silent foreign-socket capture) is empirically refuted by the reliable RED-pre-fix CLOSED behavior (documented above as a non-blocking hardening rec).

**Other confirmed LOW/MEDIUM (non-blocking, documented for fast-follow):**
- `[TEST]` AC2 and "no second app WebSocket" share the `appSocket.readyState` assertion — distinct AC framings, both meaningful; harmless redundancy (could collapse or make AC2 assert instance identity). LOW.
- `[TEST]` No genuine-drop→reconnect test under the hoisted architecture (AC4-reuse defers to the 67-8 suite, which predates the hoist). MED improvement.
- `[EDGE]` AC4 omits `await server.connected` before `nextMessage` — empirically fine (70+ runs), a defensive-consistency nit. LOW.
- `[DOC]` `mountAndConnect` "single live game socket" / `liveAppSockets` "contamination-immune" JSDoc slightly oversell (the *instance* is immune, not the scan). LOW precision nits.
- `[TYPE]` `(await server.nextMessage) as {...}` is an unchecked cast from `unknown`; matches the established `lobby-start-ws-open.test.tsx` convention and the immediate `expect`s validate; could use `isSessionEvent`. LOW. (`SessionEventPayload` lacking `game_slug` is pre-existing/out-of-diff.)
- `[SIMPLE]` The Proxy mechanism *might* be replaceable by `server.clients` — speculative API, and would be another rewrite of a just-stabilized test; not worth it. MED, declined.

**Carried production deferrals (from round-trip-0, still open as documented follow-ups — non-blocking):** `ErrorBoundary` around the dashboard `Suspense` (epic-67 resilience: session survives a *broken* dashboard — the highest-value fast-follow) and a `popstate` listener (Back closes the overlay). Both are MEDIUM, pre-existing-adjacent, and explicitly out of this story's contained scope.

**Data flow / wiring / security:** unchanged from round-trip-0 — `#/dashboard` hash → `DashboardGate` overlay above `<Routes>`; session tree stays mounted underneath (AC5 is the production wiring proof); reviewer-security re-affirmed clean (no perception-firewall leak).

**Devil's Advocate (round-trip 1):** The strongest case against approving is the three-subagent convergence on silent foreign-socket capture — and silence is this story's original sin, so I owe it more than a wave-off. But the refutation is concrete, not hopeful: the pre-fix toggle tests fail *reliably* with the captured socket CLOSED, which is only possible if the captured socket is App's own (a foreign socket is inert to my toggle and would stay OPEN, flipping those tests to intermittent passes — never observed). The second-order worry — that I'm rationalizing to avoid a third round-trip — is checked by the fact that `toBe(1)`, the proposed "fix," would *reintroduce* a flake (it fails whenever contamination occurs, which is exactly when `>= 1` correctly tolerates it); the genuinely correct alternative (deterministic capture) is a real improvement but not a correctness blocker given the empirical evidence. The deferred ErrorBoundary remains the one place a real user (Keith, opening the GM panel mid-deploy) could still lose a session — but that gap pre-dates 67-9, is non-blocking, and is documented for a fast-follow. The bar — "the suite proves it and the suite is honest" — is now met: 70+ deterministic green runs and a still-valid RED contract.

**Handoff:** To Architect (Neo) for spec-reconcile, then SM for finish.

## Delivery Findings

## Impact Summary

### Overview
Story 67-9 completes the three-layer WebSocket re-handshake elimination initiative (67-8 Layer 1+3 → 67-9 Layer 2). **No remount triggers remain in the session path** — the connection is stable across route transitions and dashboard toggles.

### Delivery Findings (Aggregated)

#### Core Finding: Spec Deviation Endorsed
- **Dev's dashboard-hoist approach:** A literal WebSocket connection lift above `<Routes>` would require relocating ~2100 lines / 101 hooks of `AppInner` (including `handleMessage`, the socket's `onMessage` handler). Architect and Reviewer both endorsed the dashboard-hoist as the correct, risk-respecting realization. All ACs (as encoded in tests) are satisfied; the durable `SocketProvider` seam is deferred as an own-story follow-up (only needed if a future story introduces a new per-route `AppInner` remount path).

#### Test Suite Findings
- **Flaky test observable (resolved):** The RED tests initially used a global `WebSocket` Proxy to count socket constructions. In full-suite runs, other test files' lingering async contaminated the count. Reworked to instance-level `appSocket.readyState` + GET-count (contamination-immune). **Result: 0/30 flakes, still RED pre-fix.**
- **Testing-runner false-green exposure:** `testing-runner` reported 1674/1674 during dev-green and tea-verify, masking a deterministic AC2 failure that the real `npx vitest run` caught. Lesson: count-sensitive suites need spot-check runs of the raw CI command.

#### Non-Blocking Improvements (Documented for Fast-Follow)
1. **`ErrorBoundary` around dashboard `Suspense`** (MEDIUM) — A `LazyDashboard` chunk-load failure currently crashes the now-always-mounted session. Highest-value fast-follow (epic-67 resilience: session survives a *broken* dashboard). `ErrorBoundary` is already imported in `App.tsx`.
2. **Durable `SocketProvider` above `<Routes>`** (MEDIUM) — Relocate `useGameSocket` + `handleMessage` to a stable owner. Only needed if a future story introduces a per-route `AppInner` remount. Own-story-sized.
3. **`popstate` listener** (MEDIUM) — Browser Back fires `popstate`, not `hashchange` — overlay stays stuck over the session. One-line fix.
4. **Suite-wide test-harness consolidation** (IMPROVEMENT) — `makeFetchMock` (14+ files) and `seedTrustedIdentity` (5+ files) are copy-pasted across `src/__tests__/`. A shared `test-fixtures.ts` would cut ~30-50 lines per file. Separate test-infra chore.

#### Observable Deferrals (Non-Blocking, Already Documented)
- **AC3 server-OTEL half** — Client-side observables (no 2nd GET, no 2nd socket) tested green. Server-side OTEL signals (`presence.multi_socket_attach` silent, no 2nd `chargen_gate`) validated at next live playtest (same 67-8 disposition: a synthetic run can't distinguish fixed-from-unfixed).
- **StrictMode double-mount trigger** — Covered transitively by the production fix (connection never unmounts). A dedicated StrictMode assertion would add flakiness without coverage.

### Acceptance Criteria Status

| AC | Status | Notes |
|----|--------|-------|
| AC1 | DONE (behaviorally) | Dashboard toggle no longer unmounts connection; route nav already v6-reuse-safe. Literal `useGameSocket` lift descoped (Architect+Reviewer-endorsed). |
| AC2 | DONE (behaviorally) | Handshake fires once per page-session; genuine drop → reconnect path preserved (67-8 suite green). |
| AC3 | DONE (client) / DEFERRED (server-OTEL → playtest) | No 2nd GET, no 2nd socket (tested). Server-OTEL half: next live playtest. |
| AC4 | DONE | Full suite 1674/1674 (70+ deterministic runs); 67-8 duplicate-socket suite green. |
| AC5 | DONE | Wiring proof: real `<App>` handshake, full suite green. |

### Risk Assessment
**Low:** Production change is surgical (~40 lines to `App.tsx`). Dashboard hoist is a safe pattern (opaque overlay, no context leakage). Reviewer-security confirmed no perception-firewall leak. One round-trip to resolve a test-isolation defect (flaky observable). All deferred improvements are non-blocking and tracked.

### Next Steps
1. Merge the PR (currently draft)
2. Confirm server-OTEL half at next live playtest (AC3 deferred observable)
3. Fast-follow: `ErrorBoundary` around dashboard `Suspense` (highest-value resilience hardening)
4. Own-story: durable `SocketProvider` above `<Routes>` (only if a future story introduces per-route `AppInner` remount)
5. Opportunistic: `popstate` listener, test-fixtures consolidation


Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

### TEA (test design)
- **Improvement** (non-blocking): The pinned remount trigger is the `#/dashboard` hash toggle inside `LobbyRoot` (App.tsx:2343-2371), which conditionally renders `<LazyDashboard/>` vs `<GameStateProvider><AppInner/></GameStateProvider>`. Route-to-route nav does NOT remount (react-router v6 reuses the shared `<LobbyRoot/>` element — confirmed by `lobby-start-ws-open.test.tsx`). So the GREEN hoist must put the connection owner above `<Routes>` AND outside the dashboard conditional — moving it merely above `<Routes>` but still inside a per-route element would not fix the dashboard-toggle case. Affects `sidequest-ui/src/App.tsx` (connection ownership; the dashboard branch in `LobbyRoot`). *Found by TEA during test design.*
- **Question** (non-blocking): The slug-connect handshake reads `slug` from `useParams()` (App.tsx ~:218-302), which is only available *inside* a `<Route>`. Hoisting the handshake above `<Routes>` means the new owner cannot use `useParams` — Dev will need another slug source above the router (parse `window.location` / pass via a route-level effect into a hoisted owner). This is the core design tension of the refactor; flagging so Dev weighs it explicitly rather than discovering it mid-implementation. Affects `sidequest-ui/src/App.tsx`. *Found by TEA during test design.*
- **Improvement** (non-blocking): AC3's server-side OTEL half (`presence.multi_socket_attach` never fires; no second `chargen_gate`/`ws.connection_accepted` span across a mid-session route/dashboard change) is a live-playtest acceptance observable, not a synthetic unit assertion — mirroring the 67-8 disposition (a clean synthetic run can't distinguish fixed-from-unfixed on the server side). The RED tests cover the trigger-independent CLIENT observable (no 2nd GET, no 2nd socket). Recommend confirming the server-OTEL half at the next live playtest. Affects acceptance validation only (no code). *Found by TEA during test design.*
- **Improvement** (non-blocking): Suite-wide test-harness duplication — `makeFetchMock` (14+ files on `develop`) and the journey-history/`seedTrustedIdentity` localStorage seeding (5+ files) are copy-pasted across `src/__tests__/`. Surfaced by simplify-reuse during verify; confirmed pre-existing (not introduced by 67-9). A shared `src/__tests__/test-fixtures.ts` (exporting `makeFetchMock(overrides?)` + `seedGameHistory(slug, ...)`) would cut ~30-50 lines of boilerplate per file. Out of scope for 67-9 (transport refactor); worth a dedicated test-infra chore. Affects `sidequest-ui/src/__tests__/*`. *Found by TEA during test verification.*
- **Process** (non-blocking): `pf workflow phase-check tdd verify` returns `sm`, but the `tdd` workflow YAML (`pf workflow show tdd`) assigns `verify → tea` and the spec-check `resolve-gate`/marker correctly routed `next_agent: tea`. The phase-check CLI appears to misreport the verify-phase owner; I trusted the authoritative workflow definition + routing and proceeded as TEA. Affects the `pf workflow phase-check` resolver (tooling, not story code). *Found by TEA during test verification.*

### Dev (implementation)
- **Improvement** (non-blocking): The GM dashboard now stays mounted *underneath* the live session (opaque overlay) instead of replacing it. Opening `#/dashboard` mid-session no longer tears down the game — a usability win (monitor + play). One consequence worth a glance: `AppInner` keeps running (audio, WS, renders) while the dashboard is shown. No regression observed (full suite green), and it matches "dashboard = monitoring overlay, not session teardown," but if audio-under-dashboard is ever unwanted it's a one-line pause hook. Affects `sidequest-ui/src/App.tsx` (`DashboardGate`). *Found by Dev during implementation.*
- **Question** (non-blocking): The literal connection-above-`<Routes>` hoist (TEA's `useParams` finding) remains technically open — the `useGameSocket` call still lives in `AppInner`. It is no longer *needed* for the ACs (the dashboard hoist removes the only live remount trigger), but if a future story adds a NEW per-route remount path that resets `AppInner`, the connection would churn again. A genuine `SocketProvider` above `<Routes>` (relocating `useGameSocket` + `handleMessage`) would be the durable seam — large, own-story-sized. Affects `sidequest-ui/src/App.tsx`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The 67-9 test suite fails the real CI command. `npx vitest run` (full suite) fails AC2 3/3 — `constructedSockets` length 2 ≠ 1 — because `installWebSocketCounter`'s global `WebSocket` Proxy counts foreign socket constructions bleeding in from other test files' lingering async. Passes in isolation; production code is correct (readyState assertions pass). Affects `sidequest-ui/src/__tests__/app-dashboard-toggle-rehandshake-67-9.test.tsx` (harden the observable: URL-filter or baseline-delta the socket count). *Found by Reviewer during code review.*
- **Gap** (non-blocking, process): The `testing-runner` subagent reported false-green (1674/1674) during dev-green and tea-verify, masking the deterministic AC2 full-suite failure that `reviewer-preflight` (running the real `npx vitest run`) caught. Affects the workflow's reliance on `testing-runner` summaries — agents should spot-check the raw CI command for count-sensitive suites. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `DashboardGate`'s `<Suspense>` lacks an `ErrorBoundary`; a `LazyDashboard` chunk-load failure crashes the whole tree including the now-always-mounted session — counter to epic-67's resilience goal. Affects `sidequest-ui/src/App.tsx` (wrap in `<ErrorBoundary name="Dashboard">`, already imported at App.tsx:2019). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `DashboardGate` listens only for `hashchange`, not `popstate` — browser Back leaves the opaque overlay stuck over the live session. Affects `sidequest-ui/src/App.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing/out-of-diff): `DashboardApp.tsx:294` `loadDebugState` swallows fetch errors with an empty catch — now more exposed as a global overlay; the GM (Keith) gets no signal when debug-state is unreachable. Affects `sidequest-ui/src/components/Dashboard/DashboardApp.tsx`. *Found by Reviewer during code review.*
- **Resolved** (round-trip 1): the blocking flaky-suite Gap above is FIXED — observable redesigned to instance-level `appSocket.readyState` + GET-count; 70+ clean runs, still RED pre-fix. *Confirmed by Reviewer during re-review.*
- **Improvement** (non-blocking, round-trip 1): the test captures App's socket as `liveAppSockets()[0]` with a `>= 1` guard. Empirically reliable (RED-pre-fix toggle tests fail with the captured socket CLOSED, proving it's App's own), but a deterministic capture (or fail-loud `toBe(1)`) would remove the theoretical foreign-socket-at-index-0 race. Affects `sidequest-ui/src/__tests__/app-dashboard-toggle-rehandshake-67-9.test.tsx`. *Found by Reviewer during re-review (edge-hunter/silent-failure/test-analyzer convergence).*
- **Improvement** (non-blocking, round-trip 1): AC4 awaits `server.nextMessage` without a preceding `await server.connected` (the pattern `mountAndConnect` uses); empirically fine but worth the defensive guard. Affects the AC4 test. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Behavioral full-`<App>` mount test instead of the 67-8 sibling's source-assertion style**
  - Spec source: context-story-67-9.md AC1–AC5; sibling `beat-commit-session-bound-wiring-67-8.test.tsx` ("App.tsx is too heavy to mount" → source-grep assertions)
  - Spec text: AC1 "route/dashboard-hash/StrictMode remounts do NOT re-run the connect handshake or open a second `ws.connection_accepted` cycle"; AC3 "trigger-independent observable."
  - Implementation: Wrote a behavioral test that mounts the real `<App>` (via the established `lobby-start-ws-open.test.tsx` harness) and asserts the AC behavior across a real `#/dashboard` toggle, rather than grepping App.tsx source for the hoisted-component shape.
  - Rationale: 67-8's source-assertion choice was driven by an *unpinned* remount trigger (testing it would have encoded a guessed mechanism — the Reviewer accepted that). For 67-9 the trigger IS the spec (the dashboard-hash toggle), so reproducing it is testing the named AC, not guessing. A behavioral test is fix-agnostic (passes for any hoist shape) and also serves as the wiring proof (exercises the real production tree). A source-grep test would couple to Dev's exact component naming — the brittleness 67-8's TEA warned against.
  - Severity: minor (stronger, fix-agnostic coverage than the sibling precedent; not a reduction)
  - Forward impact: Dev's GREEN is validated by behavior, not structure — any hoist that makes the toggle non-remounting passes. Reviewer should confirm the tests assert behavior, not a specific component name.
- **Render WITHOUT StrictMode; StrictMode-double-mount trigger not separately unit-tested**
  - Spec source: context-story-67-9.md AC1 ("...or StrictMode remounts...")
  - Spec text: "route/dashboard-hash/StrictMode remounts do NOT re-run the connect handshake."
  - Implementation: The RED tests mount under a plain `<MemoryRouter>` (no `<StrictMode>`) and exercise the real-mount dashboard-toggle remount. The StrictMode dev-double-mount path is not given its own assertion.
  - Rationale: StrictMode double-invoke is dev-only and adds non-determinism to the construction counts (the slug-connect effect's cancelled-pass design already dedupes connect() under StrictMode, but the pre-latch `fetch` fires twice). The dashboard-hash toggle is the production-relevant, deterministic remount trigger and is sufficient to drive the GREEN hoist; a hoist that survives a real remount also survives StrictMode's. Conflating them would add flakiness without adding AC coverage.
  - Severity: minor (one of three named triggers covered behaviorally; the fix for one fixes all three — the connection simply stops being unmounted)
  - Forward impact: If Reviewer wants explicit StrictMode coverage, it can be added as a follow-up, but the hoist's correctness is fully exercised by the route/dashboard remount path.
- **AC3 OTEL half deferred to playtest; client-observable proxy unit-tested instead**
  - Spec source: context-story-67-9.md AC3
  - Spec text: "OTEL shows NO second `ws.connection_accepted`/`chargen_gate` cycle; `presence.multi_socket_attach` never fires."
  - Implementation: Unit tests assert the CLIENT-side proxy (no 2nd GET `/api/games/:slug`, no 2nd `new WebSocket`, original socket stays OPEN). The server-side OTEL spans are not asserted in a synthetic run.
  - Rationale: Same disposition the 67-8 Architect/Reviewer accepted — a synthetic happy-path run can't distinguish fixed-from-unfixed on the server-OTEL signal, and the honest validation venue is a live playtest. The client proxy is the trigger-independent observable available in a unit test.
  - Severity: minor (acceptance-observable split; client half fully covered, server half validated at playtest)
  - Forward impact: Logged as a non-blocking delivery finding; next live playtest confirms the server-OTEL half.
- **Verify phase applied no simplify fixes (all findings out-of-scope or benign)**
  - Spec source: TEA verify workflow (simplify fan-out → apply high-confidence fixes)
  - Spec text: "For each finding with `confidence: high`: apply the suggestion."
  - Implementation: The 3 high-confidence reuse findings were cross-file extractions of pre-existing, suite-wide duplication (shared `makeFetchMock`/`seedTrustedIdentity` across 14+/5+ files) or an extraction pulling in an unrelated component (`useHashMatch` touching `narrativeRenderers.tsx`). Applied none; logged dispositions in the Simplify Report + a delivery finding instead.
  - Rationale: Auto-applying them would expand a deliberately-contained Layer-2 transport refactor into a dozen unrelated files — violating minimalist discipline and 67-8's "contain risk" mandate. "High confidence" reflects the correctness of the observation, not the appropriateness of acting on it mid-story. simplify-quality returned clean for the 67-9 change itself.
  - Severity: trivial (deviation from the literal "apply all high-confidence fixes" step; the findings are genuine but belong to a separate test-infra chore)
  - Forward impact: none for 67-9; a future test-fixtures consolidation chore can pick up the deferred reuse findings.
- **Rework (round-trip 1): observable changed from global socket-count to app-socket lifecycle; recommended production fixes deferred**
  - Spec source: Reviewer Assessment (round-trip 1) — HIGH blocker (flaky full-suite test) + MEDIUM recommendations (ErrorBoundary, popstate)
  - Spec text: "Make the observable robust to cross-file contamination… Must make `npx vitest run` (full suite) green 3/3." + "Strongly recommended to bundle: ErrorBoundary, popstate."
  - Implementation: Fixed the blocker by replacing the contaminated global `constructedSockets.length` assertions with GET-count + app-socket-lifecycle (`liveAppSockets()` OPEN+URL filter, tracking the specific `appSocket`). Did NOT implement the MEDIUM `ErrorBoundary`/`popstate` production recommendations — deferred as documented follow-up findings.
  - Rationale: The blocker (flaky test) is the rework's mandate and is fixed (6/6 green, still RED pre-fix). The ErrorBoundary/popstate are non-blocking MEDIUM, pre-existing-adjacent, and would need their own RED tests + production work — expanding a rework that 67-8 explicitly scoped to "contain risk." They are tracked for a fast-follow.
  - Severity: minor (test-observable redesign within the same AC intent; one HIGH blocker resolved, two MEDIUM recommendations deferred with documentation)
  - Forward impact: 67-9 completes on its core goal (kill the re-handshake) with a robust suite. The deferred ErrorBoundary (epic-67 resilience: session survives a *broken* dashboard) and popstate (back-button closes overlay) are follow-up findings; if the Operator requires them in 67-9, TEA authors RED tests and the story re-enters green.

### Dev (implementation)
- **Hoisted the DASHBOARD above `<Routes>` rather than literally lifting the WebSocket connection above `<Routes>`**
  - Spec source: context-story-67-9.md AC1/AC2; session SM Assessment ("hoist the connection + handshake latch above `<Routes>`")
  - Spec text: AC1 "The WebSocket connection + slug-connect handshake are owned by a stable component ABOVE `<Routes>`, so route/dashboard-hash/StrictMode remounts do NOT re-run the connect handshake."
  - Implementation: Kept `useGameSocket` + the slug-connect handshake where they are (`AppInner`) and instead made `LobbyRoot` render the session tree unconditionally, hoisting the `#/dashboard` view into a `DashboardGate` overlay above `<Routes>`. Net effect: the connection-owning tree is a stable, always-mounted subtree that the dashboard toggle (and route nav) never unmounts — the behavioral outcome AC1 specifies — but the connection object itself is not relocated above the router.
  - Rationale: A literal lift is infeasible within Layer 2's risk budget. `AppInner` is ~2100 lines / 101 hooks; the socket's `onMessage` is `handleMessage` (App.tsx:556), tightly bound to dozens of `AppInner` setState calls and `useGameState()`. Relocating the connection above `<Routes>` requires relocating the entire app shell into a provider — exactly the un-contained refactor 67-8 deferred Layer 2 to avoid ("minimalist discipline, contain risk", session SM Assessment). The TEA tests are deliberately fix-agnostic ("any hoist that makes the toggle non-remounting passes") and all three RED invariants go green with this approach; route-to-route nav was already remount-safe (v6 element reuse), so the dashboard conditional was the sole live trigger and hoisting *it* removes the defect. Honors CLAUDE.md "do X not Y" by being explicit about doing the dashboard hoist, not silently substituting.
  - Severity: major (diverges from the literal AC1 mechanism — the connection is not above `<Routes>`; the behavioral contract in the tests is fully met)
  - Forward impact: All ACs (as encoded in the tests) are satisfied and the full suite is green. The durable `SocketProvider`-above-`<Routes>` seam (relocating `useGameSocket`+`handleMessage`) is left as an own-story-sized follow-up (logged as a Dev delivery finding) — only needed if a future story introduces a new per-route `AppInner` remount path. Reviewer/Architect should confirm this interpretation is acceptable for the story's intent (kill the dashboard-toggle re-handshake with contained risk) vs. requiring the full connection relocation now.
- **Rework green: Dev edited the test observable (normally TEA's lane) to eliminate a residual flake rather than bounce back**
  - Spec source: Dev green workflow ("make tests pass / keep GREEN"); Reviewer round-trip-1 blocker (flaky suite)
  - Spec text: Dev "writes code to pass tests"; green workflow "Refactor if needed (keep GREEN)." Test *design* (observables/strategy) is nominally TEA's lane.
  - Implementation: On green confirmation I found TEA's red-rework left a residual ~3.7% flake (foreign OPEN `/ws` sockets still admitted by the `liveAppSockets()` post-toggle re-scan). Rather than hand back to TEA for a 3-line assertion change (another full round-trip), I hardened the observable myself: assert only the captured `appSocket` instance's `readyState` (immune by construction), dropping the array re-scans.
  - Rationale: Passing green with a known flake is the exact false-green failure this story exposed — unacceptable. The fix was small, precise, test-only, and preserved the RED-pre-fix contract; a TEA round-trip for it would be process-theater. Verified exhaustively (0/30 full-suite + RED-pre-fix intact). Documented transparently here.
  - Severity: minor (role-boundary deviation — Dev touched test-observable design; no production change, contract preserved, behavior unchanged)
  - Forward impact: none — the suite is now deterministically green. If the project prefers test-design changes always route through TEA, that's a process note, not a code issue.

### Reviewer (audit)

- **TEA: Behavioral full-`<App>` mount test instead of source-assertion** → ✓ ACCEPTED by Reviewer: the right call — the trigger is pinned and in-spec for 67-9, so a behavioral mount test is fix-agnostic and doubles as the wiring proof. (The full-suite failure below is a separate observable-robustness *bug* in that test, not a flaw in choosing the behavioral approach.)
- **TEA: Render WITHOUT StrictMode; StrictMode trigger not separately tested** → ✓ ACCEPTED by Reviewer: sound — the fix stops `AppInner` being unmounted at all, so it covers StrictMode's remount transitively; a dedicated StrictMode assertion would add flakiness without coverage.
- **TEA: AC3 OTEL half deferred to playtest** → ✓ ACCEPTED by Reviewer: consistent with the 67-8 disposition; a synthetic run can't distinguish fixed-from-unfixed on the server-OTEL signal. Client proxy is the right unit-level observable.
- **TEA: Verify applied no simplify fixes** → ✓ ACCEPTED by Reviewer: correct restraint — the high-confidence reuse findings were cross-file extractions of pre-existing suite-wide duplication; auto-applying them would balloon a contained Layer-2 refactor.
- **Dev: Hoisted the DASHBOARD above `<Routes>` rather than literally lifting the connection** → ✓ ACCEPTED by Reviewer: agrees with the Architect's spec-check endorsement. A literal `useGameSocket` lift means relocating ~2100 lines / 101 hooks of `AppInner` + `handleMessage` — out of 67-8's explicit contain-risk scope, for zero current behavioral gain (route nav is v6-reuse-safe; the dashboard conditional was the sole live trigger). reviewer-security confirmed no perception-firewall leak from the resulting always-mounted session. The behavioral contract is met by the production code. **Correction to this entry's "the full suite is green" claim:** as of review it is NOT — `npx vitest run` fails AC2 3/3 (test-isolation defect in the socket-count observable, not the production hoist). That is the rejection blocker; the deviation itself (dashboard hoist) is sound and stands.
- **No undocumented production deviations found.** The App.tsx change matches the logged deviation exactly. The rejection is a test-quality defect (the suite does not pass), plus two recommended resilience hardenings (ErrorBoundary, popstate) — none of which contradict the logged deviations.

**Re-review (round-trip 1) — new deviation audit:**
- **TEA: Rework — observable changed from global socket-count to app-socket lifecycle; production fixes deferred** → ✓ ACCEPTED by Reviewer: the contamination-immune redesign (instance `appSocket.readyState` + GET-count) is the correct fix for the flaky-suite blocker; verified 70+ clean runs + still-RED-pre-fix. Deferring the MEDIUM ErrorBoundary/popstate to keep the rework scoped to the blocker is sound (67-8 contain-risk mandate).
- **Dev: Rework green — Dev edited the test observable (normally TEA's lane) to eliminate a residual flake rather than bounce back** → ✓ ACCEPTED by Reviewer: pragmatic and correct. Dev caught a residual ~3.7% flake by running the *real* CI command (not a `testing-runner` summary — exactly the right instinct given this story's false-green history), fixed it with the instance-level observable, and verified 0/30. The role-boundary cross (Dev touching test design) is minor, transparent, and avoided a needless round-trip. No production change, RED-contract preserved.
- **No new undocumented deviations.** The only changes since round-trip-0 are test-file hardening + the `flush` param drop, all logged. Production `App.tsx` is byte-identical to the round-trip-0 deviation manifest.
### Architect (reconcile)

**Manifest audit — all in-flight deviations verified accurate, 6-field, and self-contained:**

- **TEA (test design) ×5** and **Dev (implementation) ×2** entries reviewed. Spec sources are real and present: `sprint/context/context-story-67-9.md` (ACs quoted accurately), the session SM Assessment, the completed `67-8` session, and `sidequest-ui/src/__tests__/lobby-start-ws-open.test.tsx` (the harness/v6-reuse precedent) all exist. Implementation descriptions match the shipped code (`App.tsx` dashboard-hoist; the test's instance-level `appSocket.readyState` + GET-count observable; `flush()` param dropped). Forward-impact statements are accurate. No corrections needed.
- The Reviewer (audit) subsection stamps every TEA/Dev entry ACCEPTED (round-trip-0 + round-trip-1). The one self-correction (Dev's "full suite is green" claim, true at green but false at round-trip-0 review) is annotated in the Reviewer audit and resolved by round-trip-1 (suite now 70+ runs green).

**No additional deviations found.** The production `App.tsx` change is fully captured by the single Major deviation (dashboard hoisted above `<Routes>` rather than literally relocating `useGameSocket`) — Architect-endorsed (spec-check), Reviewer-accepted. The round-trip-1 changes were test-only (observable hardening + `flush` param) and are logged. The diff contains nothing the manifest doesn't already describe.

**AC accountability (definitive, for the boss):**

| AC | Status | Disposition |
|----|--------|-------------|
| AC1 Connection + handshake owned above `<Routes>` | **DONE (behaviorally) / spec-amended (mechanism)** | The behavioral guarantee ("route/dashboard/StrictMode remounts don't re-run the handshake") is MET — the dashboard (the sole live remount trigger; route nav is v6-reuse-safe) is hoisted above `<Routes>` and the session tree is never unmounted. The *literal* "relocate `useGameSocket`" mechanism was **descoped** as an un-contained ~2100-line refactor with zero current behavioral gain (Option A/D, Architect+Reviewer-endorsed). Durable `SocketProvider` seam deferred to a follow-up. |
| AC2 Latch hoisted; fires once per page-session; genuine drop reconnects | **DONE (behaviorally)** | `AppInner` never unmounts on the toggle → handshake fires once per page-session; genuine-drop reconnect preserved by the unchanged `useWebSocket`/67-8 path. Latch object not literally relocated (same descope as AC1). |
| AC3 OTEL: no 2nd `ws.connection_accepted`/`chargen_gate`; `presence.multi_socket_attach` silent | **DONE (client) / DEFERRED (server-OTEL → playtest)** | Client-observable half tested green (no 2nd GET, app socket survives). Server-OTEL half validated at next live playtest (same disposition as 67-8; a synthetic run can't distinguish fixed-from-unfixed). |
| AC4 Regression coverage; 67-8 invariants stay green | **DONE** | Full suite 1674/1674 (70+ deterministic runs); 67-8 duplicate-socket suite green; reworked observable still RED against pre-fix (3/5). |
| AC5 chargen/slug-resume/reconnect/sessionBound gate preserved | **DONE** | Full suite green; AC5 baseline is the production wiring proof (real `<App>` handshake). |

**Two carried follow-ups (documented, non-blocking for 67-9):**
1. **`ErrorBoundary` around the dashboard `Suspense`** — a `LazyDashboard` chunk-load failure currently crashes the now-always-mounted session (epic-67 resilience gap that 67-9 widened). Highest-value fast-follow; `ErrorBoundary` is already imported in `App.tsx`. *(Reviewer finding.)*
2. **Durable `SocketProvider` above `<Routes>`** — relocate `useGameSocket` + `handleMessage` so any future per-route `AppInner` remount path cannot churn the connection. Own-story-sized. *(Dev finding.)*
   Plus minor test polish (deterministic socket capture / `toBe(1)`, AC4 `await server.connected`, `popstate` listener, JSDoc precision) — all non-blocking.