---
story_id: "100-8"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 100-8: Phase 2 — React reference shell: session-free /reference/* routes + generic node-tree renderer components (C2)

## Story Details
- **ID:** 100-8
- **Jira Key:** (none — SideQuest uses sprint YAML only)
- **Workflow:** tdd
- **Repos:** sidequest-ui

## Workflow Tracking
**Workflow:** tdd
**Phase:** red
**Phase Started:** 2026-06-09T00:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-09 | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): `just client-build` (`tsc -b`) is RED on `origin/develop` independent of this story — `src/components/__tests__/ConfrontationOverlay.beatimpact.test.tsx` has `effect: string` fixtures incompatible with the `BeatEffect` string-literal union (story 73-4 RED commit `78cd19b`, an ancestor of develop; in-flight fix likely `feat/73-13-beatimpactpanel-opponent-readout-gate`). Affects that test file (widen fixtures to `BeatEffect` literals). *Found by Dev during implementation — not introduced by 100-8; my files add zero build errors.*
- **Gap** (non-blocking): `src/__tests__/lobby-start-ws-open.test.tsx` ("Leave + Start opens a new WebSocket…") times out at 5000ms consistently, in isolation, unrelated to `/reference/*` (a `vitest-websocket-mock` + StrictMode WS-choreography timing test). Affects that test (timing/await fragility). *Found by Dev; the 100-8 wiring test also renders `<App/>` and passes, proving my additions load App cleanly.*

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `src/types/reference.ts` (new) — projection JSON types (ReferenceNode/GenericSection/LoreProjection/RulesProjection/theme) (AC6)
- `src/components/reference/NodeTree.tsx` (new) — generic recursive node-tree renderer; skips `_`-prefixed keeper keys (AC3/AC5)
- `src/screens/reference/useReferenceProjection.ts` (new) — session-free REST fetch hook, loading/error states (AC4)
- `src/screens/reference/ReferenceDocument.tsx` (new) — shared loading(`role=status`)/error(`role=alert`)/sections shell (AC4)
- `src/screens/reference/ReferenceLorePage.tsx` (new) — `/reference/lore/:pack/:world` page (AC1/AC2/AC4)
- `src/screens/reference/ReferenceRulesPage.tsx` (new) — `/reference/rules/:pack` page (AC1/AC2/AC4)
- `src/App.tsx` — wired both routes as SIBLINGS of LobbyRoot (session-free invariant C2)

**Tests:** 20/20 100-8 tests passing (GREEN). Full suite: 1936 passing, 1 pre-existing flaky timeout (lobby WS, unrelated). Lint: clean (0 errors). Build: my files type-check clean; only the pre-existing 73-4 test error remains in `tsc -b`.
**Branch:** feat/100-8-react-reference-shell (pushed)

**Handoff:** To review

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Shared fetch hook + presentational shell not named in the pinned contract**
  - Spec source: context-story-100-8.md AC3/AC4 + team-lead pinned contract
  - Spec text: pinned contract named `NodeTree`, the two page components, and `src/types/reference.ts`
  - Implementation: added two co-located helpers — `useReferenceProjection.ts` (REST fetch + loading/error state) and `ReferenceDocument.tsx` (loading `role=status` / error `role=alert` / section map) — shared by both pages
  - Rationale: the two pages are near-identical (only the URL and projection type differ); extracting the fetch+shell avoids duplicating the loading/error/keeper-safe rendering. Pages remain thin `useParams → hook → ReferenceDocument` wrappers, matching the decoupled-renderer design note.
  - Severity: minor
  - Forward impact: none — 100-9 theme injector and 100-10 map component consume the same types/sections; helpers are additive and internal to `screens/reference`.

### TEA (test design)
- **No production deviations.** Tests pin the contract exactly as the Phase-1 server projection emits it (`_project_node` → `{type: scalar|list|dict}`; generic section → `{id, label, node}`; doc → `{schema_version, pack, [world], sections, theme}`). One *additive* contract choice not in the spec letter: I pinned **accessible roles** for async states — loading = `role="status"`, error = `role="alert"` — so error/loading are asserted on behavior, not markup. Dev must surface those roles. Also pinned **AC5 client-side defense-in-depth**: `NodeTree` must skip dict entries whose `key` starts with `_` (devnote/private), mirroring the server's leading-underscore suppression so the UI never assumes a clean payload.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New session-free React surface (routes + renderer + types) — pure greenfield UI behavior, full RED coverage warranted.

**Test Files:**
- `src/components/reference/__tests__/NodeTree.test.tsx` — generic node-tree renderer (scalar/list/dict, deep nesting, null-scalar safety, `_`-key defense-in-depth).
- `src/screens/reference/__tests__/ReferenceLorePage.test.tsx` — session-free `/reference/lore/:pack/:world` route: C2 no-WS render, REST fetch URL, loading (`role=status`), error on reject + non-2xx (`role=alert`), keeper-leak defense.
- `src/screens/reference/__tests__/ReferenceRulesPage.test.tsx` — session-free `/reference/rules/:pack` route: C2, pack-tier fetch URL (no `:world`, not the lore endpoint), error state.
- `src/__tests__/reference-routes-app-wiring-100-8.test.tsx` — **wiring test**: real `<App/>` at `/reference/rules/:pack` renders projection content, shows NO ConnectScreen, opens NO WebSocket (routes reachable + session-free through the production router).

**Tests Written:** 18 tests covering ACs 1,2,3,4,5,7 (AC6 types pinned via typed fixtures importing `@/types/reference`).
**Status:** RED — confirmed failing for the right reason:
- 3 unit files fail at import resolution (`@/components/reference/NodeTree`, `@/screens/reference/ReferenceLorePage`, `@/screens/reference/ReferenceRulesPage`, `@/types/reference` — none exist yet).
- Wiring file: `<App/>` renders an empty `<div/>` at the reference URL (routes not registered) → 3 failing assertions.

**Pinned contract for Dev (GREEN):**
- `src/types/reference.ts` — `ReferenceNode` discriminated union (`{type:"scalar",value}` | `{type:"list",items}` | `{type:"dict",entries:[{key,label,node}]}`), `ReferenceDictEntry`, `GenericSection {id,label,node}`, `LoreProjection {schema_version,pack,world,sections,theme?}`, `RulesProjection {schema_version,pack,sections,theme?}`.
- `src/components/reference/NodeTree.tsx` — `export function NodeTree({ node }: { node: ReferenceNode })`. Recurse; render dict `label` + nested node; skip `_`-prefixed keys; render list items; render scalar `value`; null-scalar must not throw.
- `src/screens/reference/ReferenceLorePage.tsx` — `export function ReferenceLorePage()`: read `:pack`/`:world` (react-router `useParams`), fetch `GET /reference/api/lore/{pack}/{world}`, loading `role=status`, error `role=alert` on reject/non-2xx, render sections via NodeTree. **Must not** import GameStateProvider/useGameSocket.
- `src/screens/reference/ReferenceRulesPage.tsx` — same shape, `:pack` only, `GET /reference/api/rules/{pack}`.
- `src/App.tsx` `AppRoutes` — add `<Route path="/reference/lore/:pack/:world" .../>` and `<Route path="/reference/rules/:pack" .../>` as **siblings of** (not nested under) `LobbyRoot`, so they never mount the session tree.

**Handoff:** To Dev for implementation (GREEN).

### Reviewer (code review)
- **Improvement** (non-blocking): `LoreProjection.sections` is typed `GenericSection[]` (required `node`), but the live server lore projection (`reference_projection.py::build_lore_projection`) emits a heterogeneous list — `map`/`cast`/`poi`/`timeline` sections carry NO `node` (they use `members`/`entries`/`regions`). The runtime `.filter(s => s && s.node)` in `ReferenceDocument` skips them correctly and matches the documented Phase-3 scope, but the load-bearing filter is invisible to `tsc` (the predicate is "always true" against the current type). Phase 3 (100-10) should model `sections` as a discriminated union so a future dev can't drop the filter and crash NodeTree on a node-less section. Affects `sidequest-ui/src/types/reference.ts`. *Found by Reviewer during code review.*
- **Gap** (non-blocking, corroborates Dev): pre-existing red `client-build` on develop — `ConfrontationOverlay.beatimpact.test.tsx` vs tightened `BeatEffect` union (97-3 `552bc62` / 73-4 `78cd19b`). File identical merge-base↔develop-tip, absent from 100-8 diff. Needs a separate fix in `sidequest-ui`. *NOT caused by 100-8.*
- **Gap** (non-blocking, corroborates Dev): pre-existing flaky `client-test` — `lobby-start-ws-open.test.tsx` 5s timeout, fails in isolation, lobby flow untouched by 100-8 (`26d2f3c` on develop). Needs deflaking in `sidequest-ui`. *NOT caused by 100-8.*

## Reviewer Assessment

**Verdict:** APPROVED

**Session-free invariant (C2) — load-bearing, verified STRUCTURAL:** Both routes are siblings of `LobbyRoot` in `AppRoutes` (`App.tsx:2659-2660`), never nested under the session-owning tree (`GameStateProvider → AppInner → WebSocket`). This is structural, not a runtime guard. The wiring test (`reference-routes-app-wiring-100-8.test.tsx`) is **non-vacuous**: it renders the real `<App/>` at `/reference/rules/:pack`, stubs `WebSocket`, and asserts (a) projection content renders, (b) ConnectScreen's player-name field is absent, (c) `WebSocket` ctor is never called. It would fail if a session provider were required.

**Projection consumption — verified field-by-field against server:** `reference_projection.py` emits exactly `{type:"scalar",value}` / `{type:"list",items}` / `{type:"dict",entries:[{key,label,node}]}`, generic section `{id,label,node}`, lore `{schema_version,pack,world,sections}`, rules `{schema_version,pack,sections}`. TS types in `reference.ts` match exactly; `theme?` correctly optional (server omits it, deferred to 100-9). `tsc -b` compiled all six 100-8 files with **zero** errors (AC6). One type-accuracy nit on heterogeneous lore sections logged above (non-blocking, Phase-3 scope).

**Keeper firewall (AC5) — genuinely tested:** `NodeTree` filters `entry.key.startsWith("_")`; tested in NodeTree.test ("_devnote" → secret AND label both absent) and ReferenceLorePage.test ("_seed_tropes" payload leak → `KEEPER_LEAK_*` absent). Both assert `queryByText(...).not.toBeInTheDocument()` — non-vacuous.

**Error handling:** `useReferenceProjection` throws on `!res.ok` (No-Silent-Fallbacks) and surfaces both reject and non-2xx as an error string; loading=`role="status"`, error=`role="alert"`. No white-screen path. The hook's `settled.url` tagging correctly avoids rendering a stale URL's content after a route-param change — a thoughtful correctness detail.

**Test quality:** All assertions are Testing-Library output queries (`getByText`/`findByText`/`getByRole`), `fetch` mocked via `vi.stubGlobal`, no snapshots, no internal-state coupling. 20/20 100-8 tests pass.

**Gates:** `client-test` 1936 pass / 1 pre-existing flaky (unrelated). `client-lint` 0 errors (1 pre-existing warning at App.tsx:1522, unrelated). `client-build` 0 errors in 100-8 files; only the pre-existing develop `BeatEffect` test breakage remains. All gate failures baseline-diffed to develop — none introduced by 100-8.

**Observations:** No Critical/High/Medium-blocking issues. One non-blocking type-accuracy improvement for Phase 3; two pre-existing develop breakages flagged for separate fixes.

**Handoff:** To SM for finish-story.
