---
story_id: "153-25"
jira_key: "153-25"
epic: "153"
workflow: "tdd"
---
# Story 153-25: [DUNGEON-MAP-UI-NO-ROOMGRAPH] Render the procedural room-graph in the Map tab while inside the dungeon

## Story Details
- **ID:** 153-25
- **Jira Key:** 153-25
- **Workflow:** TDD
- **Stack Parent:** none
- **Repository:** sidequest-ui
- **Branch Strategy:** gitflow (feat/153-25-dungeon-map-roomgraph)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T14:50:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-21T14:08:45Z | 2026-06-21T14:27:17Z | 18m 32s |
| green | 2026-06-21T14:27:17Z | 2026-06-21T14:36:52Z | 9m 35s |
| review | 2026-06-21T14:36:52Z | 2026-06-21T14:50:22Z | 13m 30s |
| finish | 2026-06-21T14:50:22Z | - | - |

## Story Context

See the complete story context at:
`sprint/context/context-story-153-25.md`

This document contains:
- Problem statement: `DUNGEON_MAP` frame is dropped at the client (no message type, no handler)
- Root cause: wiring gap — server emits, UI renderer exists, but message is never named/handled
- 6 acceptance criteria: message typing, room-graph rendering, surface/dungeon coexistence, payload typing, telemetry, and wiring/integration test
- Key code areas and technical notes
- Development notes for the TDD red phase

## TEA Assessment

**Tests Required:** Yes
**Reason:** UI behavior change (a dropped WebSocket frame must reach the renderer). Not a chore-bypass category.

**Test Files:**
- `sidequest-ui/src/types/__tests__/dungeon-map-message-type-153-25.test.ts` — AC-1: `MessageType.DUNGEON_MAP` is named on the client const, mirrors the server frame, is a defined string distinct from `MAP_UPDATE`.
- `sidequest-ui/src/__tests__/dungeon-map-wiring-153-25.test.tsx` — AC-2/3/4/5/6: full-App WebSocket dispatch (`death-banner-wiring` harness) proving `DUNGEON_MAP` frame → App handler → `mapData` → MapWidget routes the room-graph payload to the Automapper (`rect[data-room-id]` + `.current-room`), surface↔dungeon↔surface coexistence, the exact server wire shape (no `x`/`y`/`fog_bounds`), and a client consumption marker.

**Tests Written:** 7 tests covering all 6 ACs
**Status:** RED (failing — ready for Dev). Verified via testing-runner twice (full run + post-edit recheck).

**RED isolation (why these failures are correct):** the harness *passes* through App boot, game phase (InputBar), Map-tab mount, and the existing `MAP_UPDATE → MapOverlay` render — then the `DUNGEON_MAP` assertions fail (0 room rects, no marker, no message type). The AC-3 test's step 1 (surface MAP_UPDATE renders) passing while step 2 (dungeon) fails proves the failure is the missing wiring, not a broken test.

### Rule Coverage (TypeScript lang-review checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 type-safety escapes (no blind `as unknown as` that drops fields) | `consumes the server's exact DUNGEON_MAP wire shape` (behavioral guard) | failing |
| #3 enum/const-object patterns | `is named on the client MessageType const` / `key===value convention` | failing |
| #4 null/undefined handling (wire omits `x`/`y`/`fog_bounds` — must not crash) | `consumes the server's exact DUNGEON_MAP wire shape (no x/y/fog_bounds)` | failing |
| #6 React/JSX (stable room keys, render correctness) | Automapper render contract reused via App path (`rect[data-room-id]`, `.current-room`) | failing |
| #8 test quality (no vacuous assertions) | Phase-C self-check on this suite | n/a — guard |

**Rules checked:** 4 of 4 applicable lang-review rules have test coverage (the remaining checklist items — async/Promise, build-config, barrel imports — don't apply to a two-line message-wiring change).
**Self-check:** 1 vacuous test found and fixed — AC-1 test 3 passed vacuously in RED (`undefined !== "MAP_UPDATE"`); strengthened with a `typeof === "string"` guard so it fails in RED and is meaningful in GREEN. testing-runner re-confirmed it now fails at the typeof assertion.

**Handoff:** To Dev (Naomi) for implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-ui/src/types/protocol.ts` — added `MessageType.DUNGEON_MAP` (mirrors the server frame name). [AC-1]
- `sidequest-ui/src/lib/dungeonMap.ts` (NEW) — `DungeonMapPayload` type (accurate wire shape, no `x`/`y`/`fog_bounds`), `isDungeonMapPayload` runtime guard, and `dungeonMapToMapState` adapter. [AC-4]
- `sidequest-ui/src/App.tsx` — `DUNGEON_MAP` handler beside `MAP_UPDATE`: guard → fail-loud `console.warn` on a malformed frame (No Silent Fallbacks) → adapt → `setMapData` → `[dungeon-map]` consumption `console.info` marker (rooms + current room). [AC-2/3/5/6]

**Approach (reuse-first, AC-4-honest):** the Automapper renderer and MapWidget room-graph routing already existed — this is message wiring only. The dungeon wire omits `x`/`y` (rooms have no coordinates, ADR-055) and `fog_bounds`; rather than an `as unknown as MapState` blind cast (which would hide that mismatch) or loosening `ExploredLocation.x/y` to optional (which breaks `tsc` — MapOverlay reads `loc.x`/`loc.y` unguarded at lines 250-275), I narrow with a runtime type guard (`p is DungeonMapPayload` from `unknown`) and adapt explicitly to `MapState`, filling inert `x:0/y:0`/`fog_bounds` the Automapper path never reads.

**Tests:** 7/7 story tests passing (GREEN). 93/93 sibling map-suite tests passing (MapWidget ×3, dungeon-map-renderer, MapOverlay cartography + shared-map) — no regressions.
**Typecheck:** my files clean under `tsc -b`; the only `tsc -b` error is pre-existing and unrelated (see Delivery Findings). **Lint:** 0 errors on changed files (1 pre-existing `useCallback` dep warning at App.tsx:1678, not my code).
**Branch:** `feat/153-25-dungeon-map-roomgraph` (pushed, commit `afc552f`).

**Handoff:** To Reviewer (Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 7/7 green, 0 new lint/tsc; flagged region-guard gap | confirmed 1 (region), rest informational |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 2 (malformed-path untested, dungeonMap unit test), 4 noted-low |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 1 ("alongside" inaccuracy), 1 dismissed (dungeonMap x/y comment is accurate), 3 noted-low |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 3 (2 distinct) | confirmed 1 (region #4/#10), 1 noted-low (test Record cast) |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled per `workflow.reviewer_subagents`)
**Total findings:** 4 confirmed (all MEDIUM/LOW, non-blocking), 1 dismissed (with rationale), several noted-low

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** inbound `DUNGEON_MAP` WS frame → `handleMessage` (App.tsx:1281) → `isDungeonMapPayload` guard (drops loud on malformed) → `dungeonMapToMapState` adapter → `setMapData` → GameBoard → MapWidget → `toExploredRooms` keys on `room_exits` → `<Automapper>`. Safe: the guard validates before field access; the adapter fills inert `x:0/y:0`/`fog_bounds` that the Automapper path never reads; coexistence with the surface `MAP_UPDATE` is a clean switch on the single `mapData` slot (separate `if` blocks, no fall-through).

**Observations (tagged):**
- `[VERIFIED]` AC-4 honored — no `as unknown as` / `as any` in the new production code. The guard uses the canonical `const o = p as Record<string, unknown>` AFTER a `typeof p === "object" && p !== null` check (dungeonMap.ts:31-33) — narrowing idiom, not a blind cast. Evidence: dungeonMap.ts:30-34, App.tsx:1281-1297. Complies with lang-review #1.
- `[VERIFIED]` `Omit<ExploredLocation, "x" | "y">` (dungeonMap.ts:10) is a legitimate specific-key Omit (removes two real required `number` fields), NOT the flagged `Omit<T, string>` anti-pattern (lang-review #2). Evidence: ExploredLocation.x/y are required at MapOverlay.tsx:20-21.
- `[VERIFIED]` `DUNGEON_MAP` added to the `MessageType` const-object, not a TS enum (protocol.ts:23) — complies with the `erasableSyntaxOnly` const-object rule (lang-review #3).
- `[TYPE][RULE]` `isDungeonMapPayload` validates `current_location` + `explored` but NOT the required `region` field (dungeonMap.ts:33). Confirmed by rule-checker (#4/#10) + preflight + comment-analyzer. Practical impact LOW: the real server always sets `region=pc_region` (map_emit.py `_build_dungeon_map_payload`), the dungeon payload renders via Automapper (not MapOverlay, which is the only `region` reader), and MapOverlay's `mapData.region || "Explored Locations"` (MapOverlay.tsx:164) degrades gracefully. Confirmed (not dismissed — matches a project rule), rated LOW, logged as a non-blocking Improvement for follow-up.
- `[DOC]` The "broadcasts DUNGEON_MAP **alongside** the surface MAP_UPDATE" comment (App.tsx:1274, protocol.ts:18-20) is inaccurate: per the server the two emits are **per-world mutually exclusive** — `_maybe_emit_cartography_map` is a "no-op for room_graph worlds (they use DUNGEON_MAP)" (websocket_session_handler.py:2483-2484). They feed the single `mapData` slot at different times/worlds, not simultaneously. Confirmed, LOW, logged for follow-up.
- `[TEST]` The malformed-frame fail-loud branch (App.tsx:1282-1287, the story's "No Silent Fallbacks" guard) is untested, and `src/lib/dungeonMap.ts` has no dedicated unit test. Confirmed by test-analyzer. MEDIUM→LOW (defensive code; the happy path through the guard is covered by the wiring test). Recommended follow-up: `src/lib/__tests__/dungeonMap.test.ts` covering the guard's false branches + the adapter defaults.
- `[SILENT]` (self, subagent disabled) No swallowed errors. The only "drop" is the intentional loud `console.warn` + return on a malformed frame — this IS the No-Silent-Fallbacks behavior, correctly loud. The fall-through `setMessages` tail is not reached (handler returns).
- `[EDGE]` (self, subagent disabled) Empty `explored: []` passes the guard and renders an empty room graph — correct (valid on session start). Null/non-object payload → guard returns false → loud drop. Missing per-room fields → trusted from server contract; `toExploredRooms` tolerates absent optionals.
- `[SEC]` (self, subagent disabled) No security surface — no injection, no auth, no secrets, no `dangerouslySetInnerHTML`. Inbound WS payload IS validated at the boundary (the guard) — strictly better than the pre-existing `MAP_UPDATE` `as unknown as` handler.
- `[SIMPLE]` (self, subagent disabled) No over-engineering. The type+guard+adapter split is the minimal honest factoring; reuse-first (no new renderer). No dead code.

**Error handling:** malformed frames fail loud (App.tsx:1282-1287); guard precedes all field access; graceful render of empty graphs. No try/catch needed (synchronous).

**Why APPROVE despite confirmed findings:** all confirmed findings are MEDIUM/LOW — none Critical or High (severity table: blocking = Critical/High only). The two substantive items (region-guard completeness, malformed-path test) **cannot manifest with the real server** (it always sends well-formed frames with `region`), and the region gap degrades gracefully (no crash, no silent map corruption). The core is correct, reuse-first, AC-4-honest, and well-tested for every reachable scenario (7/7 + 93/93 siblings). Findings are logged as non-blocking Improvements for a fast follow-up rather than gating a clean 3-pt wiring fix.

### Rule Compliance (TypeScript lang-review checklist)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Type-safety escapes (`as any`/`as unknown as`/`@ts-ignore`) | PASS (prod) | None in new prod code; guard uses canonical narrow. Test file uses `MessageType as Record<string,string>` — noted-low (#8). |
| 2 | Generics/interfaces (`Record<string,any>`, `Omit<T,string>`) | PASS | `Omit<…,"x"\|"y">` specific-key; `Record<string,unknown>` (not any). |
| 3 | Enum anti-patterns | PASS | const-object, not TS enum (protocol.ts:23). |
| 4 | Null/undefined (`??` vs `||`, validation) | PARTIAL | region not validated in guard (LOW, logged). x/y/fog_bounds filled with literals. |
| 5 | Module/declaration (`import type`) | PASS | `import type` for types, value import for fns. |
| 6 | React/JSX (hooks/keys) | PASS | No new hooks/JSX; handler is inside the existing dispatch callback. |
| 7 | Async/Promise | PASS | All new code synchronous. |
| 8 | Test quality | PASS-w/-notes | Wiring test is a real end-to-end integration test. Low nits: tautological fixture asserts, `Record<string,string>` cast, /\b2\b/ tightness. |
| 9 | Build/config | PASS | strict on; no config changes. |
| 10 | Input validation at boundary | PARTIAL | Guard validates inbound payload (better than MAP_UPDATE) but misses `region` (LOW, logged). |
| 11 | Error handling | PASS | Fail-loud on malformed; no `catch(e:any)`. |
| 12 | Perf/bundle | PASS | Direct import, type-only MapOverlay import; no hot-path stringify. |
| 13 | Fix-introduced regressions | PASS | No new `as any`/`||`-for-`??`; net improvement over MAP_UPDATE's blind cast. |

### Devil's Advocate

Argue this code is broken. The most damning angle: the story's banner feature is "No Silent Fallbacks — fail loud on a malformed frame," yet the very guard that implements it (`isDungeonMapPayload`) is incomplete — it never checks `region`, a field its own `DungeonMapPayload` interface declares required and the adapter reads unconditionally. So a frame that omits `region` does NOT fail loud; it sails through the guard, and `dungeonMapToMapState` spreads `undefined` into `MapState.region`, producing a value TypeScript swears is a `string`. That is precisely the "convincing surface, broken backing" the OTEL principle warns about — the type system is lied to at the one boundary the story exists to harden. A future consumer that does `mapData.region.toUpperCase()` (no `||` guard, unlike MapOverlay) would throw on a real null. Second angle: the malformed branch is entirely untested — there is no proof the warn fires or that `mapData` is left untouched; a refactor that accidentally moves the `setMapData` above the guard would pass every existing test while reintroducing the silent-corruption defect. Third angle: the explanatory comment is wrong — it claims the server broadcasts DUNGEON_MAP "alongside" MAP_UPDATE, but the server makes them mutually exclusive per world; a maintainer trusting that comment could waste an afternoon hunting for a simultaneous MAP_UPDATE that never comes for a room_graph world. Fourth angle: a malicious/buggy server could send `explored` as a 100k-element array and the adapter `.map`s it every turn with no bound — but that is the server's trust boundary and matches every other handler, so not this PR's problem. **Verdict of the devil's advocate:** the three real issues are genuine but each degrades gracefully against the *actual* emitter (server always sends `region`, always well-formed) and none corrupts the rendered map or crashes today. They are completeness/clarity debts, not live defects — confirmed and logged, not blocking.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the client `ExploredLocation` type marks `x`/`y` required and `MapState` marks `fog_bounds` required, but the server's `DUNGEON_MAP` wire (`map_emit.py` `DungeonMapLocation`/`DungeonMapPayload`) sends none of them. Affects `sidequest-ui/src/components/MapOverlay.tsx` and the new handler in `sidequest-ui/src/App.tsx` (the `DungeonMapPayload` type per AC-4 must NOT require those fields, or `x`/`y`/`fog_bounds` must be made optional). *Found by TEA during test design.*
- **Improvement** (non-blocking): the existing `MAP_UPDATE` handler at `App.tsx:1268` uses `setMapData(msg.payload as unknown as MapState)` — a blind double-cast. AC-4 forbids copying that pattern for `DUNGEON_MAP`. Affects `sidequest-ui/src/App.tsx` (add a typed `DungeonMapPayload` and route it without `as unknown as`). *Found by TEA during test design.*
- **Question** (non-blocking): context Technical Note flags that the server may only re-emit `DUNGEON_MAP` on the next turn after reconnect (ADR-133). The client fix (name + handle the frame) is the deliverable; whether the server re-emits on reconnect into a dungeon is a separate server follow-up to verify in playtest. Affects playtest verification, not this PR. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `tsc -b` is RED on the branch from a PRE-EXISTING, unrelated error — `GameBoard-fate-inventory-tab.test.tsx:203` builds `new Set([..., "fate"])` but `"fate"` is no longer a `WidgetId` (the standalone Fate tab was removed in story 126-26). Confirmed pre-existing via a stash test (reproduces with my changes stashed), so it is NOT introduced by 153-25 — but it means `npm run build`/typecheck is broken on develop and should be fixed in its own chore. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` (drop `"fate"` from the test's WidgetId set, or restore the id). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the `MapUpdatePayload` type at `payloads.ts:322` types `explored?: string[]` — it does NOT describe the room-graph `explored[]` (ExploredLocation with `room_exits`). It was unusable for the dungeon frame, hence the new `DungeonMapPayload`. The two map payload types are now divergent; a future cleanup could reconcile `MapUpdatePayload` with the actual `MapState` wire. Affects `sidequest-ui/src/types/payloads.ts`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `isDungeonMapPayload` validates `current_location` + `explored` but not the required `region` field; a `region`-less frame passes the guard and `dungeonMapToMapState` spreads `undefined` into `MapState.region` (a type-lie). Degrades gracefully today (server always sends `region`; MapOverlay has a `|| "Explored Locations"` fallback and isn't on the dungeon path). Matches lang-review #4/#10. Affects `sidequest-ui/src/lib/dungeonMap.ts:33` (add `&& typeof o.region === "string"`; update the App.tsx warn message to mention region). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the "broadcasts DUNGEON_MAP **alongside** the surface MAP_UPDATE" comment is inaccurate — the server makes the two emits per-world mutually exclusive (`_maybe_emit_cartography_map` is a "no-op for room_graph worlds (they use DUNGEON_MAP)", websocket_session_handler.py:2483-2484). Affects `sidequest-ui/src/App.tsx:1274` and `src/types/protocol.ts:18-20` (reword to "feeds the single mapData slot; the surface MAP_UPDATE and DUNGEON_MAP are per-world mutually exclusive on the server"). *Found by Reviewer during code review.*
- **Gap** (non-blocking): the malformed-frame fail-loud branch (App.tsx:1282-1287) and the `dungeonMap.ts` guard/adapter have no dedicated test. Recommend `sidequest-ui/src/lib/__tests__/dungeonMap.test.ts` covering the guard's false branches (null / non-object / missing current_location / missing region) and the adapter defaults (x:0/y:0/fog_bounds, pass-through room fields). Affects `sidequest-ui/src/lib/dungeonMap.ts`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (1 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** the existing `MAP_UPDATE` handler at `App.tsx:1268` uses `setMapData(msg.payload as unknown as MapState)` — a blind double-cast. AC-4 forbids copying that pattern for `DUNGEON_MAP`. Affects `sidequest-ui/src/App.tsx`.
- **Gap:** `tsc -b` is RED on the branch from a PRE-EXISTING, unrelated error — `GameBoard-fate-inventory-tab.test.tsx:203` builds `new Set([..., "fate"])` but `"fate"` is no longer a `WidgetId` (the standalone Fate tab was removed in story 126-26). Confirmed pre-existing via a stash test (reproduces with my changes stashed), so it is NOT introduced by 153-25 — but it means `npm run build`/typecheck is broken on develop and should be fixed in its own chore. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx`.
- **Improvement:** `isDungeonMapPayload` validates `current_location` + `explored` but not the required `region` field; a `region`-less frame passes the guard and `dungeonMapToMapState` spreads `undefined` into `MapState.region` (a type-lie). Degrades gracefully today (server always sends `region`; MapOverlay has a `|| "Explored Locations"` fallback and isn't on the dungeon path). Matches lang-review #4/#10. Affects `sidequest-ui/src/lib/dungeonMap.ts:33`.

### Downstream Effects

Cross-module impact: 3 findings across 3 modules

- **`sidequest-ui/src`** — 1 finding
- **`sidequest-ui/src/components/GameBoard/__tests__`** — 1 finding
- **`sidequest-ui/src/lib`** — 1 finding

### Deviation Justifications

3 deviations

- **AC-4 type existence covered behaviorally, not via a runtime type assertion**
  - Rationale: you cannot assert an erased type at runtime; the behavioral shape-tolerance test is the strongest runtime guard, and the static guarantees live in the typecheck + reviewer gates.
  - Severity: minor
  - Forward impact: Reviewer should confirm the new handler uses a real `DungeonMapPayload` type and no `as unknown as` blind cast (lang-review #1).
- **AC-3 surface fixture uses plain region nodes, not the full cartography block**
  - Rationale: the coexistence rule (surface MapOverlay vs dungeon Automapper) is what AC-3 locks; cartography-specific node/route rendering is already covered by `MapOverlay.cartography.test.tsx`. Keeping the full-App fixture minimal avoids the CartographyMap/d3-dag path in jsdom.
  - Severity: minor
  - Forward impact: none — surface cartography fidelity remains guarded by the existing MapOverlay cartography test.
- **AC-5 client marker contract fixed to a `[dungeon-map]` console.info/debug log**
  - Rationale: "trace/log marker" is unspecified as to channel; console.info/debug is the established client-trace mechanism in App.tsx, so the test pins that contract rather than inventing a new telemetry channel.
  - Severity: minor
  - Forward impact: Dev must emit the marker via console.info/debug with the `[dungeon-map]` tag, room count, and current room id.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-4 type existence covered behaviorally, not via a runtime type assertion**
  - Spec source: context-story-153-25.md, AC-4
  - Spec text: "A TypeScript type for the `DUNGEON_MAP` payload exists ... No `as unknown as` blind cast that hides a shape mismatch."
  - Implementation: TS types are erased at runtime, so the test sends the *exact server wire shape* (no `x`/`y`/`fog_bounds`) through the App and asserts the rooms still render — proving the consumption tolerates the real shape. The "type exists / no blind cast" source pattern is enforced by `tsc` (typecheck gate) and the TS lang-review #1 reviewer check, not a runtime assertion.
  - Rationale: you cannot assert an erased type at runtime; the behavioral shape-tolerance test is the strongest runtime guard, and the static guarantees live in the typecheck + reviewer gates.
  - Severity: minor
  - Forward impact: Reviewer should confirm the new handler uses a real `DungeonMapPayload` type and no `as unknown as` blind cast (lang-review #1).
- **AC-3 surface fixture uses plain region nodes, not the full cartography block**
  - Spec source: context-story-153-25.md, AC-3
  - Spec text: "the Map tab still renders the cartography region map (Ropefoot / Dropmouth / 'Down the Rope'), unchanged."
  - Implementation: the surface `MAP_UPDATE` fixture carries two region `explored` nodes (no `cartography` metadata block), and the test asserts `map-overlay` renders (and the room graph does not) — it does not assert the specific Ropefoot/Dropmouth nodes or the "Down the Rope" route.
  - Rationale: the coexistence rule (surface MapOverlay vs dungeon Automapper) is what AC-3 locks; cartography-specific node/route rendering is already covered by `MapOverlay.cartography.test.tsx`. Keeping the full-App fixture minimal avoids the CartographyMap/d3-dag path in jsdom.
  - Severity: minor
  - Forward impact: none — surface cartography fidelity remains guarded by the existing MapOverlay cartography test.
- **AC-5 client marker contract fixed to a `[dungeon-map]` console.info/debug log**
  - Spec source: context-story-153-25.md, AC-5
  - Spec text: "the client emits a lightweight client-side trace/log marker when it receives and applies a `DUNGEON_MAP` frame (room count + current room)."
  - Implementation: the test asserts a `console.info` OR `console.debug` call tagged `[dungeon-map]` containing the current room id and the discovered room count, matching the existing App.tsx client-trace convention (e.g. the `[dice-guard]` markers).
  - Rationale: "trace/log marker" is unspecified as to channel; console.info/debug is the established client-trace mechanism in App.tsx, so the test pins that contract rather than inventing a new telemetry channel.
  - Severity: minor
  - Forward impact: Dev must emit the marker via console.info/debug with the `[dungeon-map]` tag, room count, and current room id.

### Dev (implementation)
- No deviations from spec. Implemented AC-1–AC-6 as the tests and context specified: `MessageType.DUNGEON_MAP`, a real `DungeonMapPayload` type + guard + adapter (no `as unknown as` blind cast, per AC-4), `setMapData` routing into the existing Automapper path, a fail-loud malformed-frame guard (context "No Silent Fallbacks"), and the `[dungeon-map]` `console.info` consumption marker (the marker channel TEA's AC-5 deviation left to Dev's choice).

### Reviewer (audit)
- **TEA: AC-4 type existence covered behaviorally** → ✓ ACCEPTED by Reviewer: sound — TS types are erased; I verified the runtime shape-tolerance test plus zero `as unknown as` in the implementation, and the static guarantee lives in `tsc` + lang-review #1.
- **TEA: AC-3 surface fixture uses plain region nodes** → ✓ ACCEPTED by Reviewer: agrees — AC-3 locks the surface↔dungeon switch, which the test proves; cartography-node fidelity is covered by `MapOverlay.cartography.test.tsx`. The surface→dungeon→surface sequence the test models also matches the real per-world emission (region world → MAP_UPDATE; descend → DUNGEON_MAP), both feeding one `mapData` slot.
- **TEA: AC-5 marker contract = console.info/debug `[dungeon-map]`** → ✓ ACCEPTED by Reviewer: reasonable — matches the App.tsx client-trace convention (`[dice-guard]`, `[scene-harness]`); Dev implemented it on `console.info`.
- **Dev: No deviations from spec** → ✓ ACCEPTED by Reviewer: confirmed — implementation matches the ACs and the context "No Silent Fallbacks" note; no undocumented spec divergence found. (The region-guard incompleteness is a quality finding, not a spec deviation.)