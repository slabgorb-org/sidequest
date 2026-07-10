---
story_id: "163-5"
jira_key: ""
epic: "163"
workflow: "spdd"
---
# Story 163-5: UI: RasterMap component + MapWidget raster branch + mobile tab wiring (plan tasks 12–15)

## Story Details
- **ID:** 163-5
- **Jira Key:** (none — sprint-tracked)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T09:27:16Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T08:47:15Z | 2026-07-10T08:49:53Z | 2m 38s |
| red | 2026-07-10T08:49:53Z | 2026-07-10T09:01:49Z | 11m 56s |
| green | 2026-07-10T09:01:49Z | 2026-07-10T09:09:25Z | 7m 36s |
| review | 2026-07-10T09:09:25Z | 2026-07-10T09:27:16Z | 17m 51s |
| finish | 2026-07-10T09:27:16Z | - | - |

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T08:51:25Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T09:02:47Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T09:08:30Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T09:09:10Z"/>
</skills-invoked>

## Sm Assessment

**Setup complete — routing to TEA (red phase).**

- **Story:** 163-5 — UI: RasterMap component + MapWidget raster branch + mobile tab wiring. 5pts, p1, ui repo only. Epic 163 (Mapping Track A). No Jira (sprint-tracked); Jira steps explicitly skipped, same as all epic-163 siblings.
- **Workflow:** `spdd` (phased). The sprint-YAML tag "superpowers" is the established alias for spdd on this epic (see 163-1/163-2/163-3 archives). Phase flow: setup → red → green → review → finish (setup=sm, red=tea, green=dev, review=reviewer, finish=sm).
- **Branch:** `feat/163-5-rastermap-ui` created in sidequest-ui from `develop` (per repos.yaml the ui subrepo targets develop, not main). Working tree was clean.
- **Authoritative sources for the next agents:**
  - Plan: `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md` — this story = tasks **12, 13, 14, 15**. The plan is fully specified per task (files, interfaces, DOM testids, failing-test-first steps, exact vitest/eslint commands). Follow it in task order.
  - Spec: `docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md` §2, §4 A1, §5.
  - Story context: `sprint/context/context-story-163-5.md` (problem, approach, ACs derived from the plan tasks).
- **Upstream already shipped:** server treatment layer + `CartographyTreatmentWire` + `payload.treatment` (163-1), pack validator (163-3), three raster `map.yaml` worlds (163-4), fixture regression fix (163-7). This story is pure UI consumption of that wire block.
- **Scope for TEA's red phase:** failing tests per plan tasks 12–15 — the `RasterTreatment`/`MapState.treatment` type test, RasterMap DOM-contract tests (scan image, pins, current marker, onNodeSelect, explicit image-error state with NO dag fallback), MapWidget raster-routing + raw-import wiring test, and the GameBoard mobile Map-tab reachability wiring test. The plan contains draft test code for each; task 15's test must confirm the actual `mapData` prop name on `GameBoardProps` (grep noted in the plan). Per CLAUDE.md wiring rules, the tab-reachability test is the mandatory integration test proving RasterMap is reachable from production paths, not just unit-rendered.
- **Doctrine flags for this story:** No Silent Fallbacks — image load failure must surface an explicit error state, never fall back to dag/generated rendering (spec §5). Style branches key off `style_hints`, never genre strings (Track B touchpoint note in plan task 13).
- **Judgment checks:** Jira — skipped (no-jira story). Context — written with technical approach + ACs. Merge gate — clear (activation state NEW_WORK_STATE).

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `sidequest-ui/src/components/map/__tests__/RasterTreatmentType.test.ts` — task 12: ?raw source guards for the `RasterTreatment` export + `MapState.treatment?` field, plus the typed-literal tsc contract
- `sidequest-ui/src/components/map/__tests__/RasterMap.test.tsx` — task 13: full DOM contract (scan `raster-scan`, pins `[data-region-id]`, `data-current` marker, `onNodeSelect`), explicit image-error state with no silent fallback, data-driven `style_hints` branches (`data-route-tracing`, `data-defaced`), NaN-route + unanchored-current guards
- `sidequest-ui/src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx` — task 14 (appended describe): raster routes to RasterMap not MapOverlay, raster wins over room-graph, dag/generated fall through unchanged, raw-import wiring guard
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx` — task 15: raster map reachable through the production mobile Map-tab path (the mandatory wiring test), plus treatment-gated negative guard

**Tests Written:** 17 tests covering all 8 story-context ACs (AC1→file 1; AC2–5→file 2; AC5–7→files 3–4; AC8 verified via eslint-clean commit)
**Status:** RED (verified by testing-runner, run 163-5-tea-red): 6 failing + RasterMap.test.tsx collection-blocked (8 tests) on the missing module — every failure is feature-absence, none harness error. 13 passing = 12 pre-existing MapWidget regression guards + 3 labeled green-on-arrival guards.

**Green-on-arrival by design (labeled honestly):**
1. Typed-literal smoke (file 1) — runtime-green (esbuild erases types), it is the `tsc -b` contract.
2. dag/generated fall-through (file 3) — pins that Dev's branch must gate on `kind === "raster"`, not `treatment != null`; goes red on over-routing.
3. Plain-cartography tab guard (file 4) — harness proof localizing the RED to missing wiring.

### Rule Coverage

| Rule (typescript.md) | Test(s) / handling | Status |
|------|---------|--------|
| #1 type-safety escapes | Dropped plan's `as unknown as` casts; fixtures typed as real MapState (deviation logged). ?raw casts follow repo idiom | enforced in test code |
| #4 null/undefined | `pin click without onNodeSelect does not throw`; `renders without a current marker when party region has no anchor` | failing (RED) |
| #6 React/JSX keys | Plan impl's `key={i}` on route lines flagged as Dev directive (delivery finding — not DOM-observable, no honest RED per 165-4 doctrine) | delegated |
| #8 test quality | No `as any` in assertions; self-check ran — 3 green-on-arrival tests labeled, zero vacuous assertions | pass |
| #10 input validation (fail-loud) | `explicit error state on image load failure — no silent fallback render` (also SOUL No-Silent-Fallbacks + spec §5) | failing (RED) |
| Wiring-test rule (CLAUDE.md) | raw-import guard (file 3) + mobile Map-tab reachability (file 4) | failing (RED) |

**Rules checked:** 6 of 6 applicable lang-review/project rules have coverage or an explicit delegation
**Self-check:** 0 vacuous tests found (3 intentional green guards labeled above)

**Commit:** `a020f79` on `feat/163-5-rastermap-ui` (sidequest-ui), eslint clean. Note: `tsc -b` is red on this branch until tasks 12–13 land — intended ordered cascade, same as 163-1.

**Handoff:** To Naomi (Dev) for GREEN — implement strictly in plan order 12→13→14→15; the plan's per-task impl code is sound (ground-truth-verified) except use a stable key for route lines and the exact regex-pinned tokens in MapOverlay.tsx.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/components/MapOverlay.tsx` — `RasterTreatment` interface (exact regex-pinned tokens) + `treatment?: RasterTreatment` on MapState (task 12)
- `sidequest-ui/src/components/map/RasterMap.tsx` — new component: scan `<img>` + SVG overlay (anchored pins, current marker, route lines), OrbitalChartView-style imperative pan/zoom (wheel clamp [0.25, 8], drag deltas), explicit image-error state, `style_hints`-driven branches (task 13)
- `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` — `RasterMap` import + early-return branch gated strictly on `treatment?.kind === "raster"`, placed after the `!mapData` guard, before room-graph (task 14)
- Task 15 required no implementation — the mobile Map-tab wiring test went green once 12–14 landed, proving reachability through the production tab path.

**Tests:** 29/29 story tests passing; full suite 2590/2590 (316 files, zero regressions) — verified by testing-runner run `163-5-dev-green`, corroborated by direct per-file runs. TEA's three green-on-arrival guards did their job: the dag/generated fall-through guard held (branch gates on `kind === "raster"`, not `treatment != null`).
**Quality:** eslint clean on all touched files. `tsc -b`: zero new errors vs the develop baseline (1 pre-existing error in an untouched Fate test file — delivery finding logged).
**Branch:** `feat/163-5-rastermap-ui` (sidequest-ui, pushed; commits: RED `a020f79`, GREEN `fa40d9d`). No PR — SM creates it in finish.

**TEA directives closed:** stable route keys (endpoints+name, not index) — deviation logged; exact regex-pinned tokens used in MapOverlay.tsx.

**Handoff:** To Chrisjen Avasarala (Reviewer) for the review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (all mechanical gates green; Dev's tsc-baseline claim independently VERIFIED true) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own pass (see [EDGE] items) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own pass (see [SILENT] items) |
| 4 | reviewer-test-analyzer | Yes | findings | 9 | confirmed 4, dismissed 5 (rationales in assessment) |
| 5 | reviewer-comment-analyzer | Yes | clean | none (every header claim verified against source/spec/server model) | N/A |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own pass + rule-checker #1/#2 (see [TYPE] items) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own pass + rule-checker #10 (see [SEC] items) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own pass (see [SIMPLE] items) |
| 9 | reviewer-rule-checker | Yes | findings | 2 (13 rules × 47 instances swept) | confirmed 2 at LOW (rule-matching, cannot dismiss; severity downgraded with rationale) |

**All received:** Yes (4 returned — preflight, test-analyzer, comment-analyzer, rule-checker; 5 disabled via settings. Preflight and comment-analyzer each recovered from one transient API failure and were resumed to completion.)
**Total findings:** 6 confirmed, 5 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** server `CartographyTreatmentWire` (messages.py:1733–1745) → MAP_UPDATE payload → App.tsx blind-cast (`as unknown as MapState`, pre-existing pattern at App.tsx:1275) → `GameBoardProps.mapData` (GameBoard.tsx:159) → `renderWidgetContent` → MapWidget (:649) → `treatment?.kind === "raster"` branch → RasterMap `<img src>` + SVG pins → optional `onNodeSelect` callback. Safe because: image_url is server-resolved (never user input), React-escaped attribute rendering, no dangerouslySetInnerHTML/eval anywhere in the diff (preflight: 0).

**Pattern observed:** faithful lift of the OrbitalChartView pan/zoom mechanism — identical wheel clamp/multipliers and panRef delta math at RasterMap.tsx:45–68 vs OrbitalChartView.tsx:96–126. The `?raw` source-guard idiom matches 7+ pre-existing precedents.

**Error handling:** image load failure flips to an explicit `map-panel-raster-error` panel that REPLACES the raster render (RasterMap.tsx onError → imgFailed) — pinned by a test asserting no silent substitute renders. Complies with SOUL No Silent Fallbacks.

### Confirmed findings (none blocking)

| Severity | Tag | Issue | Location | Disposition |
|----------|-----|-------|----------|-------------|
| [MEDIUM] | [EDGE] | Sticky error state: once `imgFailed` is set, a corrected MAP_UPDATE carrying a new `image_url` cannot recover the panel until remount (no state reset on treatment change) | `RasterMap.tsx:37,74` | Delivery finding — follow-up (e.g. reset on `image_url` change or `key={image_url}` at the call site) |
| [MEDIUM] | [TEST] | Pan/zoom (the component's headline interaction) has zero test coverage — wheel clamp and drag delta unverified | `RasterMap.test.tsx` | Delivery finding — coverage follow-up |
| [MEDIUM] | [TEST] | `image_url: null` boundary untested; `src=""` is a known onerror footgun and the null case is what the type explicitly allows | `RasterMap.tsx:108` | Delivery finding — coverage follow-up |
| [MEDIUM] | [TEST]/[SILENT] | The real no-silent-fallback regression guard one layer up is missing: no test mounts MapWidget, fires the image error, and asserts the error panel (component-level `map-overlay` absence assertion is inert) | `MapWidget.test.tsx` | Delivery finding — coverage follow-up |
| [LOW] | [RULE] | Two non-null assertions on `querySelector` results in tests — mechanical match to lang-review #1 (`!` on a runtime-nullable). Rule-matching → confirmed, not dismissible; severity downgraded: test-only, fails loudly in-test, elements guaranteed by the fixture's anchors, one repo precedent | `RasterMap.test.tsx:82,93` | Delivery finding — trivial cleanup (assert existence first or use a throwing helper) |
| [LOW] | [TYPE] | `RasterTreatment.kind: string` — a literal union would let `tsc` catch fixture/routing typos on the exact field MapWidget routes on; counter-argument: the wire is forward-compatible (`kind: str` server-side) and unknown kinds must fall through by design | `MapOverlay.tsx:118` | Delivery finding — type-owner decision, non-blocking |

### Dismissed (with rationale)

- [TEST] `not.toThrow` crash guard "proves nothing beyond didn't crash" — dismissed: it pins the `onNodeSelect?.()` optional-chaining contract, failed in RED for feature-absence, and a no-handler click has no observable state change by design; there is nothing stronger to assert.
- [TEST] bundled style-hints test / [TEST] `for` loop instead of `it.each` — dismissed: cosmetic failure-attribution preferences; assertion lines localize failures, `unmount()` keeps iterations sound.
- [TEST] raw-import guard "redundant with behavioral tests" — dismissed: CLAUDE.md's wiring-test rule explicitly blesses import guards as cheap insurance; the behavioral tests and the import guard fail under different mutation classes.
- [TEST] empty `node_anchors` untested — dismissed: degenerate case is trivially safe (`?? {}` → zero pins) and the 163-3 pack validator enforces anchor coverage for raster worlds server-side.
- [RULE] `as unknown as {default: string}` on `?raw` imports — rule-checker itself judged acceptable-by-convention (mechanically verified redundant-but-harmless against Vite's ambient `*?raw` declaration; 7+ precedents); recorded as observation, not violation.

### Rule Compliance (lang-review typescript.md, rule-by-rule; full sweep by rule-checker, 13 rules × 47 instances)

- **#1 type-safety escapes:** production files (RasterMap.tsx, MapWidget.tsx, MapOverlay.tsx) — zero escapes, VERIFIED. Tests — two `!` violations confirmed at LOW (above); `?raw` casts acceptable by convention.
- **#2 generics/interfaces:** `style_hints: Record<string, unknown>` (not `any`) — compliant; non-readonly props match sibling convention (CartographyMap, MapOverlay). `kind: string` noted under [TYPE] above.
- **#3 enums:** none in diff — N/A.
- **#4 null/undefined:** all 8 instances compliant — `??` used on nullables (`image_url ?? ""`, `node_anchors ?? {}`, `cartography?.routes ?? []`); the one `||` (`!a || !b`) is boolean logic, not defaulting.
- **#5 modules:** `import type` used correctly everywhere; `verbatimModuleSyntax: true` mechanically enforces; tsc clean.
- **#6 React/JSX:** no useEffect; `useCallback([])` correct (ref-only closure); keys content-derived (`regionId`, `from-to-name`) — the plan's `key={i}` was corrected per TEA's directive; no dangerouslySetInnerHTML.
- **#7 async:** `await import(...)` correct in tests; no async production code.
- **#8 test quality:** no `as any` in assertions; mocks match real prop signatures; imports from src.
- **#9 build/config:** no config changes — N/A.
- **#10 input validation:** treatment rides the pre-existing unvalidated blind-cast WS path (App.tsx:1275, unchanged) — no NEW class of unvalidated input; `image_url` used only as img src.
- **#11 error handling:** explicit error state, nothing swallowed — compliant.
- **#12 performance/bundle:** direct file imports, no barrels; `?raw` dynamic imports test-only.
- **#13 fix-regressions:** N/A (single RED→GREEN chain, no fix commits yet).
- **SOUL/CLAUDE.md:** No Silent Fallbacks — compliant (verified + tested); No Stubbing — compliant (fully implemented renderer); Wiring — compliant (production consumer at MapWidget.tsx:4 + tab-reachability test through the REAL production path, independently traced by test-analyzer: GameBoard.tsx:648→MobileTabView); Track B style-hints constraint — compliant (zero genre-string branches, grep-verified).

### Own observations (covering disabled specialists)

1. `[VERIFIED]` [TYPE] Wire-twin fidelity — `RasterTreatment` fields match `CartographyTreatmentWire` (messages.py:1742–1745: kind/image_url/node_anchors/style_hints) field-for-field; UI's `[number, number]` anchor tuples are a compatible narrowing of the wire's `list[float]` per the model's own docstring ("[x, y] image pixels"). Checked against lang-review #2/#10 — no rule requires runtime validation here beyond the established WS-boundary convention.
2. `[VERIFIED]` [EDGE] Raster-masks-automap refuted — the dungeon/room-graph MAP_UPDATE is built by `_build_dungeon_map_payload` (map_emit.py:1025, room_exits :1065), a separate producer from the cartography one that attaches `treatment` (:1202/session_helpers.py:1730), so a dungeon payload never carries a treatment in production; TEA's raster-wins-over-room-graph test is a defensive guard, not a live conflict.
3. `[VERIFIED]` [SEC] No injection surface — img src is server-resolved, React-escapes attributes; onNodeSelect passes an opaque region id to the parent; no user input reaches this render path. Tenant isolation: N/A — single-session UI surface, no tenant-scoped data in the diff.
4. `[VERIFIED]` [SIMPLE] Lean transcription — no dead code, no speculative abstraction; constants (PIN_R, SCALE_MIN/MAX) named; `dragging` state earns its keep (cursor affordance). One borderline: `onNodeSelect` has no production caller at the sole call site — mirrors the established MapOverlay/CartographyMap contract (MapWidget.tsx:147 wires it in the cluster branch) and is plan-specified API; noted as a delivery finding, not scope creep.
5. `[VERIFIED]` [DOC] All header claims true (comment-analyzer verified pan/zoom lift, spec §§, twin claim, task numbers; no stale RED phrasing).
6. `[LOW]` [EDGE] SVG pin `<g onClick>` has no keyboard/role affordance — matches the CartographyMap.tsx:105 precedent, but an a11y follow-up would serve the playgroup (Alex). Delivery finding.
7. `[LOW]` [DOC] Player-facing error copy is dev-speak ("Check the R2 upload…") — useful to Keith, noise to the table; cosmetic copy nit for a future pass.

### Devil's Advocate

Assume this code is broken; what would break it? First, a hostile or buggy server: a treatment with `kind: "raster"` and `image_url: null` renders `src=""` — in some browsers an empty src fires onerror immediately (explicit error panel — correct behavior, but untested; confirmed as a Medium coverage finding), in others it silently no-ops, leaving a blank scan with floating pins. The 163-3 validator makes this unreachable from validated packs, but a hand-authored world in dev bypasses nothing server-side — acceptable, though the missing test means we're asserting this from reasoning, not evidence. Second, a confused player: they click a pin and nothing happens (MapWidget passes no onNodeSelect) — the `cursor: pointer` affordance promises interactivity the production wiring doesn't deliver. That's a genuine UX lie in the current wiring, mitigated only by the fact that pins still communicate location; logged as a finding for the orientation follow-up. Third, a stressed session: the scan 404s mid-session (R2 hiccup), the player sees the error panel, the server later re-emits a good URL — and the panel stays dead until the player switches tabs (mobile unmounts) or reloads. On desktop dockview, panels stay mounted — the error is permanent for the session. That elevated my sticky-state concern to the top Medium. Fourth, malformed anchors (`[1]`, strings) from a hand-edited map.yaml: destructuring yields undefined, React drops the attributes, pins silently stack at origin — a latent silent-degrade, guarded today only by the server validator. Fifth, zoom + drag on a touch device: no touch handlers at all (parity with OrbitalChartView, so not a regression — but the playgroup plays on varied hardware). None of these rise to blocking for THIS story's scope; the sticky-error and coverage gaps are the real deltas and they are logged as findings.

**Handoff:** To Camina Drummer (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the plan's task-13 RasterMap reference impl keys route `<line>`s by array index (`key={i}`) — lang-review #6 flags index keys on lists that can reorder. Route lines are stateless SVG so this is not DOM-observable (no honest RED per the 165-4 doctrine); Dev should key by `route.name` or `${from_id}-${to_id}` when implementing. Affects `sidequest-ui/src/components/map/RasterMap.tsx` (key choice at implementation time). *Found by TEA during test design.*
- **Improvement** (non-blocking): the plan's task-12 test as written is runtime-vacuous — vitest/esbuild strips `import type` + annotations without checking them and this repo has no vitest typecheck mode, so the pure type test passes before the type exists (invalid RED). Replaced with ?raw source guards + the typed literal retained as the `tsc -b` contract. Plan doc still carries the vacuous version. Affects `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md` (task 12 test block, for future plan authors). *Found by TEA during test design.*
- **Question** (non-blocking): RED is a task-ordered cascade — `tsc -b` fails on the new test files until tasks 12–13 land (`RasterTreatment` unexported, `../RasterMap` missing), same as 163-1. Dev should implement strictly in plan order 12→13→14→15, re-running each file per task; the full-suite vitest run + `tsc -b` go green together at task 14/15. Affects `sidequest-ui/src/components/map/` + `widgets/MapWidget.tsx` (sequencing only). *Found by TEA during test design.*
- **Gap** (non-blocking): the plan's task-15 TODO ("confirm the mapData prop name on GameBoardProps") is resolved — `mapData?: MapState | null` exists at `GameBoard.tsx:159` and threads to MapWidget at :649, so the wiring test uses the real prop with no cast. No server-side gap: this story is pure consumption of the 163-1 `treatment` wire block. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-map-raster-tab.test.tsx` (informational). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `tsc -b` has ONE pre-existing error on develop — `GameBoard-fate-inventory-tab.test.tsx(203,29): TS2769 No overload matches this call` — verified identical on the develop baseline (checkout + rebuild); this branch adds zero new tsc errors. Affects `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-inventory-tab.test.tsx` (fixture type drift; needs its own cleanup story or a fix in the Fate-inventory story family). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the plan's task-13 reference impl styles with `var(--text-muted)` and `var(--surface-raised)`, which are defined nowhere in sidequest-ui — future Track A/B UI tasks transcribing that impl should substitute the real tokens (`--surface-2`, `text-muted-foreground/60`). Affects `docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md` (task 13 style tokens, for future transcribers). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): sticky image-error state — once `imgFailed` is set, a corrected MAP_UPDATE with a new `image_url` cannot recover the raster panel until remount (permanent for the session on desktop dockview, where panels stay mounted). Affects `sidequest-ui/src/components/map/RasterMap.tsx` (reset `imgFailed` when `treatment.image_url` changes, or key RasterMap by image_url at the MapWidget call site). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test-coverage follow-ups from the review — (a) pan/zoom wheel-clamp and drag-delta behavior untested; (b) `image_url: null` boundary untested (`src=""` onerror footgun); (c) missing MapWidget-level integration guard: mount MapWidget with a raster mapData, fire the image error, assert `map-panel-raster-error` renders with no silent overlay/room-graph substitute. Affects `sidequest-ui/src/components/map/__tests__/RasterMap.test.tsx` + `widgets/__tests__/MapWidget.test.tsx` (three additional tests). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two `querySelector(...)!` non-null assertions (lang-review #1 match, confirmed at LOW) — assert existence before dereference or use a throwing lookup helper. Affects `sidequest-ui/src/components/map/__tests__/RasterMap.test.tsx` (lines 82, 93). *Found by Reviewer during code review.*
- **Question** (non-blocking): `RasterTreatment.kind: string` vs a literal union — a union catches fixture/routing typos on the exact field MapWidget routes on, but the server wire is deliberately forward-compatible (`kind: str`) and unknown kinds must fall through by design; type-owner call for a future story. Affects `sidequest-ui/src/components/MapOverlay.tsx` (RasterTreatment.kind type). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): pin-click orientation is unwired at the sole production call site — RasterMap's `onNodeSelect` (cursor: pointer promises interactivity) gets no handler from MapWidget's raster branch, unlike the cluster branch's drill-down (MapWidget.tsx:147); wire a region-info/orientation affordance or drop the pointer cursor when no handler. Also: pins have no keyboard/role affordance (matches CartographyMap precedent; a11y follow-up serves the playgroup). Affects `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` + `src/components/map/RasterMap.tsx` (orientation wiring + a11y). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Task-12 type test re-strategized from pure type-import to ?raw source guards + retained typed literal**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md, task 12 test block
  - Spec text: "Create RasterTreatmentType.test.ts ... Run it, SEE it fail — EXPECT type error / fail (RasterTreatment unexported, treatment not on MapState)"
  - Implementation: two ?raw source-guard tests (regex-pin `export interface RasterTreatment` and `treatment?: RasterTreatment` in MapOverlay.tsx source) plus the plan's typed literal kept as a third test
  - Rationale: vitest transpiles with esbuild and never typechecks — the plan's test passes on arrival (types erased), an invalid RED; the ?raw guard is the repo-sanctioned source-level wiring pattern and fails deterministically today, while the typed literal still pins the contract at `tsc -b`
  - Severity: minor
  - Forward impact: Dev must use the exact tokens `export interface RasterTreatment` and `treatment?: RasterTreatment` in MapOverlay.tsx (regex-pinned); any other spelling of the same contract reds the source guards
- **Dropped the plan's `as unknown as` double-casts in tasks 14–15 fixtures**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md, tasks 14–15 test blocks
  - Spec text: "`} as unknown as import(\"@/components/MapOverlay\").MapState`" / "`renderBoard({ mapData: RASTER_MAP } as unknown as Partial<GameBoardProps>)`"
  - Implementation: fixtures typed directly as `MapState`; `renderBoard({ mapData: RASTER_MAP })` uses the real prop
  - Rationale: `GameBoardProps.mapData` exists today (GameBoard.tsx:159) and `treatment` is valid MapState once task 12 lands — the double-cast defeats the type system (lang-review #1) and would hide a wrong-prop regression; the direct typing participates in the intended tsc RED cascade instead
  - Severity: minor
  - Forward impact: none (fixtures typecheck as soon as task 12 lands)

### Dev (implementation)
- **Route lines keyed by endpoints+name instead of array index**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md, task 13 reference impl
  - Spec text: "`routes.map((rt, i) => { ... <line key={i} ...`"
  - Implementation: `key={`${rt.from_id}-${rt.to_id}-${rt.name}`}`
  - Rationale: lang-review #6 (index keys on reorderable lists); TEA flagged this as a Dev directive in Delivery Findings — route identity is stable under list reordering with endpoint+name keys
  - Severity: minor
  - Forward impact: none
- **Theme tokens substituted for the plan's nonexistent CSS variables**
  - Spec source: docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md, task 13 reference impl
  - Spec text: "`text-[var(--text-muted)]` ... `fill={isCurrent ? \"var(--accent)\" : \"var(--surface-raised)\"}`"
  - Implementation: `text-muted-foreground/60` (MapWidget empty-state idiom) and `var(--surface-2)` (CavernActionPanel idiom)
  - Rationale: `--text-muted` and `--surface-raised` are defined nowhere in sidequest-ui (verified by repo-wide grep) — transcribing verbatim ships dead styling; substituted the established tokens used by sibling components
  - Severity: minor
  - Forward impact: none (tests pin structure/testids, not styling tokens)

### Reviewer (audit)
- **TEA: Task-12 type test re-strategized to ?raw source guards + retained typed literal** → ✓ ACCEPTED by Reviewer: vitest/esbuild genuinely never typechecks (no typecheck config, no test-d files — verified), so the plan's pure type test is an invalid RED; the ?raw guards were demonstrably RED pre-implementation and the typed literal preserves the `tsc -b` contract. Sound engineering, honestly labeled.
- **TEA: Dropped the plan's `as unknown as` double-casts in tasks 14–15 fixtures** → ✓ ACCEPTED by Reviewer: `GameBoardProps.mapData` exists (GameBoard.tsx:159, verified) so the cast was never needed; direct typing is lang-review #1 compliant and strictly stronger.
- **Dev: Route lines keyed by endpoints+name instead of array index** → ✓ ACCEPTED by Reviewer: closes TEA's lang-review #6 directive; keys are stable under reorder and unique for content-validated routes.
- **Dev: Theme tokens substituted for the plan's nonexistent CSS variables** → ✓ ACCEPTED by Reviewer: independently re-verified — `--surface-raised`/`--text-muted` appear nowhere in src/; the substitutes match the sibling-component idiom (`var(--surface-2)` in CavernActionPanel.tsx, `text-muted-foreground/60` in MapWidget's empty state).