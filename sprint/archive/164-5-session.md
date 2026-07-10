---
story_id: "164-5"
jira_key: ""
epic: "164"
workflow: "spdd"
---
# Story 164-5: UI: SITE_MAP handling + scene-keyed mapData + breadcrumb — fixes 158-36 (plan task 9)

## Story Details
- **ID:** 164-5
- **Jira Key:** (not configured)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T12:45:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T11:49:44+00:00 | 2026-07-10T11:53:09Z | 3m 25s |
| red | 2026-07-10T11:53:09Z | 2026-07-10T12:07:15Z | 14m 6s |
| green | 2026-07-10T12:07:15Z | 2026-07-10T12:36:12Z | 28m 57s |
| review | 2026-07-10T12:36:12Z | 2026-07-10T12:45:30Z | 9m 18s |
| finish | 2026-07-10T12:45:30Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA for RED.**

- **Story:** UI half of the Track B site-system cutover. Server contract (164-1..164-4) is fully merged; the client still speaks `DUNGEON_MAP` with a single clobberable `mapData` slot. This story cuts the UI to `SITE_MAP`, splits `mapData` into scene-keyed state, and adds the drill-out breadcrumb — the structural fix for **158-36**.
- **Workflow:** `superpowers` label resolves to **spdd** (phased), matching sibling 164-4. Setup → red → green → review → finish.
- **Repo:** sidequest-ui only. Branch `feat/164-5-site-map-ui-scene-mapdata-breadcrumb` off develop.
- **Jira:** not configured in this environment — claim explicitly skipped (not an error).
- **Context:** enriched at `sprint/context/context-story-164-5.md` with the authoritative sources (plan **task 9** is the spec — exact files, line anchors, failing-test seed), the concrete UI surface, high-level ACs, and the **critical Track A scope guardrail** (MapWidget/map_emit are shared — touch only the site-scene branch + breadcrumb; leave orrery/cartography/RasterMap treatment alone).
- **Risk flag for TEA/Dev:** plan labels task 9 a **RISKY CUTOVER**. Watch for `DUNGEON_MAP`/`dungeonMap` stragglers (`grep -rn` in `src/`) and keep drill-out **view-only** (does not move the party). Include a wiring/reachability test (Map tab renders the breadcrumb when `siteMap` is set) per the wire-first invariant.

**Next agent:** tea (RED) — convert the 6 acceptance criteria in the context into failing tests, starting from the `siteMap.test.tsx` seed in plan task 9.

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T12:05:16Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T12:10:25Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T12:10:25Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T12:10:25Z"/>
</skills-invoked>

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — verified by testing-runner, all 5 files fail for the right reason)

**Test Files:**
- `src/lib/__tests__/siteMap.test.ts` (new) — AC-2: `isSiteMapPayload` guard + `siteMapToMapState` carries `site_id/site_name/archetype/extent` into `MapState`; x/y defaults; 158-6 label disambiguation survives the rename.
- `src/types/__tests__/site-map-message-type-164-5.test.ts` (new) — AC-1: `MessageType.SITE_MAP` present, `DUNGEON_MAP` **removed** (cutover, not coexistence).
- `src/components/GameBoard/widgets/__tests__/MapWidget.siteMap.test.tsx` (new) — AC-4: `siteMap` prop foregrounds the site room graph; `map-site-breadcrumb` names the site + world region; `map-drill-out` is view-only (reveals world map, no party move); no breadcrumb when no active site.
- `src/__tests__/site-map-wiring-164-5.test.tsx` (new) — AC-3/AC-5: SITE_MAP frame → real App → `siteMap` state → MapWidget room graph + breadcrumb (reachability through MobileTabView Map tab); world MAP_UPDATE and SITE_MAP coexist — drill-out reveals the un-clobbered world.
- `src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx` (modified) — repointed the 158-6 fixture import `dungeonMapToMapState` → `siteMapToMapState` (`@/lib/siteMap`).
- **Retired** (deleted): `src/types/__tests__/dungeon-map-message-type-153-25.test.ts`, `src/__tests__/dungeon-map-wiring-153-25.test.tsx` — their contract (DUNGEON_MAP exists) is exactly what the cutover removes; keeping them makes green impossible.

**Tests Written:** 18 assertions across 4 new suites covering all 6 ACs. Committed `417a137`.

### Rule Coverage (TypeScript lang-review — applicable checks)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 type-predicate has real runtime validation | `isSiteMapPayload` reject-cases (siteMap.test.ts) | failing (module missing) |
| #4 null/undefined handling | `isSiteMapPayload rejects null/undefined/non-object` | failing |
| #6 React/JSX render + event handler | MapWidget.siteMap.test.tsx (breadcrumb render, drill-out click) | failing |
| #8 test quality (meaningful assertions, no `as any` in assertions) | self-review, all suites | pass |
| #10 input validation at the API boundary (SITE_MAP payload) | `isSiteMapPayload rejects missing site_id/site_name` | failing |

**Rules checked:** 5 of the 13 lang-review checks are applicable to a message-adapter + component feature (the rest — enums/async/build-config/bundle — don't apply). All 5 have coverage.
**Self-check:** 0 vacuous tests (no `let _ =`, no `assert(true)`, no always-None `is-none`). Every assertion is behavioral.

**Handoff:** To Dev (Inigo Montoya) for GREEN — implement `src/lib/siteMap.ts`, `MessageType.SITE_MAP` (drop `DUNGEON_MAP`), scene-keyed `worldMap`/`siteMap` state in App.tsx, and the MapWidget `siteMap` prop + breadcrumb. Keep drill-out view-only; leave Track A orbital/cartography branches untouched.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 306 files / 2552 tests passing (GREEN) — verified by testing-runner. Typecheck (`tsc --noEmit`) clean. Changed files lint-clean (2 pre-existing lint findings unrelated to this story remain: App.tsx `currentRound` useCallback warning and Dashboard `useForensicSource.ts` set-state-in-effect error — both outside my diff hunks).
**Branch:** `feat/164-5-site-map-ui-scene-mapdata-breadcrumb` (pushed; commits `417a137` tests, `2002a4b` impl, `302cd31` review fixes).

**Files Changed (source):**
- `src/types/protocol.ts` — `MessageType.DUNGEON_MAP` → `SITE_MAP` (cutover; name removed).
- `src/lib/siteMap.ts` (new; `dungeonMap.ts` deleted) — `SiteMapPayload`/`SiteMapState` carry `site_id/site_name/archetype/extent`; `isSiteMapPayload` rejects missing OR empty `current_location`/`explored`/`site_id`/`site_name` (No Silent Fallbacks); 158-6 label disambiguation preserved.
- `src/App.tsx` — single `mapData` slot → scene-keyed `worldMap` (MAP_UPDATE) + `siteMap` (SITE_MAP); MAP_UPDATE clears `siteMap` (exit-heal); `TACTICAL_GRID` `patchScene` patches whichever slot holds the room (site first, world fallback); `[site-map]` consumption marker; both slots reset on leave.
- `src/components/GameBoard/widgets/MapWidget.tsx` — `siteMap` prop foregrounds the site room graph + a view-only drill-out/drill-in breadcrumb; drill state resets during render when the active site changes; Track A orbital/cartography branches untouched.
- `src/components/GameBoard/GameBoard.tsx` — threads `siteMap` prop to MapWidget + memo deps.

**Test changes (rename-follow / TDD-for-review-bug):** ported the orphaned 158-6 `dungeonMap.test.ts` → `siteMap-disambiguation.test.ts` (TEA missed this importer of the renamed module); added the SITE_MAP→MAP_UPDATE exit-heal regression + empty-string guard cases.

**AC status:** AC-1 (SITE_MAP present, DUNGEON_MAP gone) ✅ · AC-2 (adapter carries site metadata + guard) ✅ · AC-3 (scene coexistence + exit-heal, no clobber either way) ✅ · AC-4 (foreground + view-only breadcrumb) ✅ · AC-5 (breadcrumb reachable through the real App) ✅ · AC-6 (vitest + lint green on changed files) ✅. TEA's TACTICAL_GRID Delivery Finding resolved (scene-aware `patchScene`); the `[site-map]` marker Improvement finding also implemented.

**Handoff:** To Reviewer (Westley) for formal review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN: 306 files / 2552 tests, tsc clean, no lint errors in changed files, no smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — assessed manually |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 5 (1 Medium non-blocking, 4 Low), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed manually |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed manually |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed manually |
| 7 | reviewer-security | Yes | findings | 3 | confirmed 3 (2 pre-existing/out-of-scope, 1 Low), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — assessed manually |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — assessed manually |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 8 confirmed (0 blocking — no Critical/High), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** untrusted inbound `SITE_MAP` WS frame → `App.tsx:1296` `isSiteMapPayload(msg.payload)` runtime guard (rejects malformed/empty loudly via `console.warn` + `return`) → `siteMapToMapState` → `setSiteMap` → `GameBoard siteMap` prop → `MapWidget` site branch → `Automapper` room graph + breadcrumb. Safe: the only DOM-rendered payload fields (`site_name`, region name, room `name`) reach the DOM as React-escaped JSX/SVG text children — no `dangerouslySetInnerHTML`, no injection path ([SEC] confirmed).

**Observations (tagged by source):**
- `[SILENT]` **[MEDIUM, non-blocking]** The site branch (`MapWidget.tsx:269-324`) has no empty-state fallback: `toExploredRooms(siteMap)` returns `[]` when no discovered room carries `room_exits`, and the branch still renders `<Automapper rooms={[]}/>` (a blank SVG) under a confident "You are inside ⟨site⟩" breadcrumb — whereas the sibling non-site branch falls back to `MapOverlay` when its room graph is empty. **Verified unreachable in current content:** `_build_site_map_payload` (server) builds `room_exits` from every non-hidden edge touching a region, incl. edges to undiscovered rooms, so a megadungeon entrance always has exits → non-empty graph. Becomes reachable with the **bounded single-room archetypes (tavern/vault) in 164-6/164-7** — those should add the empty-state guard. Captured as a Delivery Finding.
- `[SILENT]` **[LOW]** `App.tsx:1284` `setSiteMap(null)` on MAP_UPDATE is logged asymmetrically: the SITE_MAP *apply* emits a `[site-map] applied…` marker but the *clear* logs nothing. The exit-heal invariant is verified safe (both server emitters gate on `scene.kind` — `_maybe_emit_cartography_map:1266` and `_maybe_emit_dungeon_map:1155` — so MAP_UPDATE never arrives in a site scene, incl. connect/resume), so misfire risk is very low, but a companion `[site-map] cleared by MAP_UPDATE` marker would make the destructive transition observable. Non-blocking nicety.
- `[SILENT]`/`[EDGE]` **[LOW]** `isSiteMapPayload` type-checks `current_location` but not emptiness, and doesn't validate `explored[]` element shape. An empty `current_location` degrades to "first room highlighted as current" (`MapWidget.tsx:271-272`) — a pre-existing default pattern also used by the non-site branch. Server contract sends a non-empty `pc_region`, so not reached in practice.
- `[SEC]`/`[TYPE]` **[LOW]** `isSiteMapPayload` doesn't validate `region`/`archetype`/`extent` though `SiteMapPayload` types them as required strings — the runtime guard is narrower than the asserted type. Harmless now (`archetype`/`extent` have no consumer; `region` unused in the site branch); tighten before those fields get a consumer.
- `[SEC]` **[LOW, pre-existing, out of scope]** `MAP_UPDATE` (`App.tsx:1276`) and `TACTICAL_GRID` (`:1327`) payloads are blind-cast (`as unknown as MapState` / `as NonNullable<…>`) with no runtime guard. Security confirmed these are **pre-existing** (only the `setMapData`→`setWorldMap` setter was renamed; the TACTICAL_GRID cast was restructured into `patchScene` with identical logic) — not introduced by this diff. A future hardening pass could add `isMapUpdatePayload`; not this story's scope.
- `[EDGE]` **[VERIFIED]** Exit-heal correctness — traced both server emitters; MAP_UPDATE and SITE_MAP are mutually exclusive per emit (each gates on `resolve_scene_context`), so clearing `siteMap` on MAP_UPDATE cannot evict a live site. Evidence: `map_emit.py:1266-1278` (cartography stands down in a site scene) + `map_emit.py:1155-1173` (site emit stands down in a world scene).
- `[SIMPLE]` **[LOW]** The drilled-out world view hardcodes `<MapOverlay>` (`MapWidget.tsx:311`) rather than reusing the non-site routing (which sends room-graph `mapData` to the Automapper). Only matters if `worldMap` ever carries `room_exits` while a site is active — impossible post-164-4 (MAP_UPDATE is cartography-only), so correct today; a latent coupling if the world-scene contract ever changes.
- `[TEST]` **[VERIFIED / gap]** Strong integration coverage: SITE_MAP→App→MapWidget wiring, exit-heal (SITE_MAP→MAP_UPDATE), coexistence, wire-shape, breadcrumb, drill-out view-only, guard (incl. empty), full 158-6 disambiguation. Untested behaviors: the render-phase drill-reset on re-enter, and `patchScene` TACTICAL_GRID-into-site — both covered by construction but not by a dedicated test. Non-blocking.
- `[DOC]` **[VERIFIED]** Comments are thorough and accurate; each cites the server contract / ADR / bug it addresses. No stale or misleading docs. The one historical mention of `DUNGEON_MAP` in `protocol.ts:19` is provenance ("renamed from DUNGEON_MAP"), not a straggler.
- `[TYPE]` **[VERIFIED]** `SiteMapState = MapState & {siteId; siteName; archetype; extent}` intersection is sound; `patchScene<T extends MapState>` preserves the descriptor fields via `{...prev, explored}`; `tsc --noEmit` clean.
- `[RULE]` **[VERIFIED]** AC-1 cutover complete — `MessageType` has only `SITE_MAP`; No Silent Fallbacks honored on the new SITE_MAP boundary (guard + loud reject). See Rule Compliance below.

### Rule Compliance (TypeScript lang-review + CLAUDE.md)

- **No Silent Fallbacks (CLAUDE.md, CRITICAL):** SITE_MAP boundary — **COMPLIANT** (`isSiteMapPayload` rejects missing/empty `site_id`/`site_name`/`current_location`(type)/`explored`, loud `console.warn`+`return`). Gaps: empty `current_location` and empty-site-graph degrade silently (Low/Medium findings above) — confirmed, not dismissed, scoped as non-blocking + Delivery Findings.
- **#10 input-validation at API boundary:** SITE_MAP **COMPLIANT** (runtime guard before use). MAP_UPDATE/TACTICAL_GRID **VIOLATION but pre-existing** (blind cast) — not introduced here.
- **#6 react-jsx (XSS):** **COMPLIANT** — all payload text is React-escaped; no `dangerouslySetInnerHTML`.
- **#1 type-safety-escapes:** one `as unknown as MapState` (pre-existing, commented) and one `as NonNullable<…>` (pre-existing, commented); no new `as any`. **COMPLIANT** for the diff.
- **#4 null/undefined:** `??` used correctly throughout (`siteMap?.siteId ?? null`, `mapData?.region ?? …`); no `||`-on-falsy bugs. **COMPLIANT.**
- **Wiring (CLAUDE.md "Verify Wiring"):** `siteMap` is threaded App→GameBoard prop→memo deps→MapWidget, and the wiring test drives the real App end-to-end. **COMPLIANT.**
- **Tenant isolation:** N/A — this is a client-side render diff with no tenant/auth model.

### Devil's Advocate

Assume this code is broken. What breaks it? **A malformed server frame:** a `SITE_MAP` with `explored: []` or rooms lacking `room_exits` passes the guard (guard only checks `explored` is an array, not that it yields a graph) and renders a blank Automapper under a confident breadcrumb — the SF-3 finding. A career GM staring at "You are inside The Deep" above an empty box would rightly distrust the whole map. Today the server never emits that for megadungeons, but the bounded archetypes are one story away, and the guard won't catch it. **A confused server invariant:** the entire exit-heal rests on "MAP_UPDATE never fires in a site scene." I verified both emitters gate on scene kind, so it holds — but if a future multiplayer race or reconnect-replay ever emitted a stale MAP_UPDATE mid-site, the player's site map would vanish with zero log trace (SF-4). The apply logs; the clear doesn't. **A stressed render:** empty `current_location` silently promotes an arbitrary "current room" — wrong-but-plausible, the worst kind. **A type liar:** `SiteMapPayload` promises `region`/`archetype`/`extent` are strings; the guard never checks them, so the type is aspirational, not enforced — a trap for the next dev who trusts it and renders `archetype`. **What a malicious server can't do:** inject script — React escaping holds, confirmed across MapWidget/Automapper/MapOverlay. None of these are crashes or security holes, and none are reachable in current content — but they are exactly the latent silent-defaults the project's No-Silent-Fallbacks rule exists to surface, so they're documented as findings for the follow-on stories rather than swept under an approval. The core cutover — the reason this story exists — is correct: scene-keyed state, the exit-heal, the guard, the breadcrumb, and Track A left untouched.

**Verdict rationale:** All 6 ACs met; 2552 tests green; typecheck + changed-file lint clean; the exit-heal (a review-caught Critical from the green phase) is fixed and regression-tested; XSS clean; No-Silent-Fallbacks honored on the new boundary. The confirmed findings are all Low or Medium-non-blocking (unreachable in current content or pre-existing), captured as Delivery Findings for 164-6/164-7. No Critical or High → **APPROVED.**

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the `TACTICAL_GRID` handler currently patches the single `mapData` slot. After the scene split, it must patch whichever scene holds the room (prefer `siteMap`, fall back to `worldMap`) or cavern grids inside a site silently stop rendering. Affects `sidequest-ui/src/App.tsx` (`TACTICAL_GRID` handler ~:1303 — repoint from `setMapData` to the correct scene slot). Outside the 6 ACs so not covered by a dedicated failing test; Dev to implement per plan task 9, Reviewer to verify. *Found by TEA during test design.*
- **Improvement** (non-blocking): the retired 153-25 DUNGEON_MAP handler emitted a `[dungeon-map] applied …` console marker so playtests could confirm the client RECEIVED the frame. The SITE_MAP tests don't require it. If frame-receipt observability is still wanted, Dev should re-add a `[site-map]` marker in the new handler. Affects `sidequest-ui/src/App.tsx` (SITE_MAP handler). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): TEA created `siteMap.test.ts` but left the pre-existing `src/lib/__tests__/dungeonMap.test.ts` (the adapter's 158-6 unit test) importing the deleted `@/lib/dungeonMap` — a full-suite import failure. Resolved by porting it to `siteMap-disambiguation.test.ts`. Future frame/module renames: `grep` for ALL importers of the module, not just the message-type/wiring tests. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the site-branch is ordered below the orbital branches in MapWidget, so a hypothetical future orbital world that also declares a site would render the orrery, not the site map. Not a regression (today's sites are non-orbital-world content; keeps Track A untouched). If orbital worlds ever host sites, revisit the branch order. Affects `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): the site branch renders a blank `<Automapper rooms={[]}/>` under a confident "You are inside ⟨site⟩" breadcrumb when a SITE_MAP passes the guard but yields no room graph (no discovered room has `room_exits`) — the sibling non-site branch falls back to `MapOverlay` in that case, the site branch has no fallback. Unreachable for current megadungeon content (entrances always have edges), but the **bounded single-room archetypes (tavern/vault) in 164-6/164-7** can hit it. Affects `sidequest-ui/src/components/GameBoard/widgets/MapWidget.tsx` (add an empty-state guard in the site branch, mirroring the sibling). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the exit-heal `setSiteMap(null)` on MAP_UPDATE (`App.tsx:1284`) logs nothing, while the SITE_MAP apply logs a `[site-map] applied…` marker — asymmetric observability of a destructive transition whose whole correctness rests on the mutually-exclusive-scene server invariant. A companion `[site-map] cleared by MAP_UPDATE` marker would make an invariant violation (MP race / reconnect-replay) diagnosable. Affects `sidequest-ui/src/App.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `isSiteMapPayload` validates `site_id`/`site_name` but not `region`/`archetype`/`extent`, though `SiteMapPayload` types all three as required strings — the runtime guard is narrower than the asserted type. Harmless now (no consumers), but tighten the guard (or mark those fields optional) before `archetype`/`extent` get a consumer. Affects `sidequest-ui/src/lib/siteMap.ts`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, pre-existing): `MAP_UPDATE` and `TACTICAL_GRID` payloads are still blind-cast with no runtime guard (unlike the new SITE_MAP path). Pre-existing (only the setter was renamed / the cast restructured), so out of scope here, but a future hardening pass should add an `isMapUpdatePayload` guard mirroring `isSiteMapPayload`. Affects `sidequest-ui/src/App.tsx`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Stricter `isSiteMapPayload` guard than the plan seed**
  - Spec source: plan task 9 (`docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md`), the `isSiteMapPayload` seed test
  - Spec text: seed only implies `current_location` + `explored` are validated (mirrors the retired `isDungeonMapPayload`)
  - Implementation: the guard test also requires `site_id` and `site_name` to be present strings; a frame missing either is rejected
  - Rationale: No Silent Fallbacks — the breadcrumb and scene-keying are the whole feature; a SITE_MAP that can't name its site would render "You are inside undefined". Drop it loudly instead.
  - Severity: minor
  - Forward impact: Dev's `isSiteMapPayload` checks 4 fields, not 2
- **Deleted the 153-25 DUNGEON_MAP contract tests instead of leaving them alongside**
  - Spec source: plan task 9 — "adapt the existing dungeonMap test"
  - Spec text: adapt (not necessarily delete) the existing DUNGEON_MAP tests
  - Implementation: removed `dungeon-map-message-type-153-25.test.ts` + `dungeon-map-wiring-153-25.test.tsx`, wrote SITE_MAP successors
  - Rationale: those files assert `DUNGEON_MAP` exists — exactly the contract the cutover removes (AC-1). Keeping them makes green impossible; "adapt" here means "replace with the SITE_MAP contract".
  - Severity: minor
  - Forward impact: none
- **No dedicated test for `TACTICAL_GRID` scene-keyed routing**
  - Spec source: plan task 9 — "`TACTICAL_GRID` patches into whichever map holds the room (prefer `siteMap`, fall back to `worldMap`)"
  - Spec text: TACTICAL_GRID must route to the correct scene slot after the split
  - Implementation: no failing test written for it; captured as a non-blocking Delivery Finding instead
  - Rationale: outside the 6 ACs; a full cavern-grid-inside-a-site render test would balloon this 3-pt RED scope. Flagged for Dev to implement + Reviewer to verify.
  - Severity: minor
  - Forward impact: Dev must repoint the TACTICAL_GRID handler; Reviewer should confirm cavern grids still render inside a site

### Dev (implementation)
- **Added the site-scene exit-heal (clear `siteMap` on a world-scene MAP_UPDATE) — behavior beyond the RED tests**
  - Spec source: the 6 ACs / TEA RED tests (enter + coexistence + drill-out) + review finding
  - Spec text: AC-3 "world map and active site map coexist … no clobber"; the RED tests never exercised the SITE_MAP→MAP_UPDATE exit
  - Implementation: MAP_UPDATE handler now calls `setSiteMap(null)`; added a wiring test for the exit-heal
  - Rationale: an early code-review (requesting-code-review skill) found the scene split dropped the self-heal the single slot had — the Map tab stayed stranded on a site after the party left (inverse of the 158-36 bug). The server's mutually-exclusive scene arbitration makes a MAP_UPDATE the authoritative "back on the surface" signal.
  - Severity: was Critical (now fixed + regression-tested)
  - Forward impact: none — completes AC-3 in both directions
- **Hardened `isSiteMapPayload` to also reject EMPTY `site_id`/`site_name` (beyond TEA's "missing" contract)**
  - Spec source: TEA's guard test (rejects MISSING site_id/site_name)
  - Spec text: reject a frame that can't name its site
  - Implementation: guard also rejects empty strings (`.length > 0`); added empty-string unit tests
  - Rationale: review Minor #2 + No Silent Fallbacks — an empty `site_name` renders "You are inside " (blank), defeating the guard's own intent
  - Severity: minor
  - Forward impact: none (stricter; the server contract never emits empty)
- **Touched test files during the green phase (ported the orphaned unit test + added regression tests)**
  - Spec source: agent lanes — TEA owns tests, Dev makes them pass
  - Spec text: Dev writes code to pass TEA's tests
  - Implementation: ported `dungeonMap.test.ts` → `siteMap-disambiguation.test.ts` (rename-follow of the module I deleted) and added the exit-heal + empty-string tests
  - Rationale: the orphan was a byproduct of my module rename (a mechanical importer update); the exit-heal test is TDD-for-a-review-found-bug, which the test-driven-development skill mandates (bug → failing test first)
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA: Stricter `isSiteMapPayload` guard than the plan seed** → ✓ ACCEPTED: sound — directly serves the CRITICAL No Silent Fallbacks rule; the load-bearing new fields must be validated.
- **TEA: Deleted the 153-25 DUNGEON_MAP contract tests** → ✓ ACCEPTED: correct — those tests assert `DUNGEON_MAP` exists, exactly the contract AC-1 removes; "adapt" for a cutover means replace-with-new-contract. Successors present and green.
- **TEA: No dedicated `TACTICAL_GRID` scene-routing test** → ✓ ACCEPTED: Dev implemented the `patchScene` fan-out correctly (verified by reading; both slots patched, no-op-on-miss). The behavior is sound; the coverage gap is noted as a non-blocking observation, not a blocker.
- **Dev: Added the site-scene exit-heal beyond the RED tests** → ✓ ACCEPTED: this fixed a real Critical (Map tab stranded on a left site). Verified the underlying server invariant (mutually-exclusive scene emit) makes the heal safe, and it is regression-tested. Exemplary review-early/TDD-the-fix.
- **Dev: Hardened `isSiteMapPayload` to reject EMPTY `site_id`/`site_name`** → ✓ ACCEPTED: fully honors the guard's own fail-loud intent (No Silent Fallbacks); no test regressions.
- **Dev: Touched test files during green (ported orphan + added regression tests)** → ✓ ACCEPTED: the port was a mechanical rename-follow of a module Dev deleted (preserving real 158-6 coverage TEA would otherwise have lost), and the exit-heal test is TDD-for-a-bug, which the workflow mandates. In-lane.

## SM Finish — Awaiting Merge (in_review)

**Status:** `in_review`. Review APPROVED (Westley). Finish preflight passed.

**Open PR (hand merge to Keith):**
- **sidequest-ui PR #457** → base `develop`, head `feat/164-5-site-map-ui-scene-mapdata-breadcrumb` (head OID `923b8b1`). **mergeable: CLEAN.** https://github.com/slabgorb-org/sidequest-ui/pull/457
- NOT merged by agent: the auto-mode classifier refuses agent merges of agent-reviewed PRs (sm-gotchas 158-40). Merge is Keith's.
- **develop-conflict resolved:** develop had advanced 16 commits (Track A RasterMap landed, touching MapWidget/App/GameBoard). Merged origin/develop into the branch — only a two-line import collision needed resolving (keep both `SiteMapState` + `RasterMap`); routing bodies auto-merged, site branch fires before the raster branch. Re-verified GREEN: **318 files / 2607 tests**, site-map + RasterMap suites pass together, tsc clean (merge commit `923b8b1`).

**Resume after Keith merges #457 → develop:**
1. Run `/pf-sm` (or `/pf-work 164-5`) — state will be FINISH_STATE.
2. `pf sprint story finish 164-5` (archives this session, moves the story to `done`, updates `sprint/current-sprint.yaml`). **Verify #457 is actually MERGED first** (`gh pr view 457 --json state,mergedAt` — sm-gotchas 159-5: finish's merge step can no-op and mark the story done while code isn't on develop).
3. Delete the feature branch (finish can't delete the checked-out branch): `cd sidequest-ui && git checkout develop && git pull && git branch -d feat/164-5-site-map-ui-scene-mapdata-breadcrumb && git push origin --delete feat/164-5-site-map-ui-scene-mapdata-breadcrumb`.
4. Commit the archive/sprint-YAML changes to orchestrator `main` (rebase if non-ff).

**Follow-up delivery findings** (non-blocking, for 164-6/164-7 — the bounded tavern/vault archetypes): empty-site-graph blank-map fallback in the MapWidget site branch; `[site-map] cleared` companion log; tighten `isSiteMapPayload` for `region`/`archetype`/`extent` before they get a consumer; future `isMapUpdatePayload` guard.