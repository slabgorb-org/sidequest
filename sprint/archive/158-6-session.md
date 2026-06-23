---
story_id: "158-6"
jira_key: ""
epic: "158"
workflow: "trivial"
---
# Story 158-6: Map deep-view gives distinct region nodes distinct labels (dedupe duplicate 'The Drowned Cavern')

## Story Details
- **ID:** 158-6
- **Jira Key:** (none)
- **Points:** 2
- **Workflow:** trivial
- **Repos:** ui
- **Type:** bug fix
- **Stack Parent:** none

## Summary

The Map tab deep-view is rendering cartography region-graph nodes with duplicate, incorrect labels. Every distinct region node reads "The Drowned Cavern" (a POI/scene title that lives *within* a region, not the region's own identifier), and the rendered node count is less than the expected `discovered_regions` count, indicating label-keyed collapsing.

This is a follow-up to sidequest-ui #1047, which wired the Map deep-view to render the procedural-deep region graph. The rendering works, but node labeling is incorrect.

## Technical Approach

**Root-cause hypothesis (from driver forensics):**
- The engine logs show `region.entry_skipped_sub_location entry='The Drowned Cavern' current_region='exp001.r2'` — the scene title is a sub-location/POI within the region, not the region's own label.
- The Map view is reading a POI/scene title field (e.g., from `current_sub_location` or a similar state field) onto region nodes, instead of reading the region's distinct identifier/label.
- If nodes are keyed by label in the renderer, all regions with the same current POI title collapse into one rendered node.

**Acceptance Criteria:**
1. Each distinct region node displays its own DISTINCT label — the region identifier or a region-specific name field, NOT the POI scene title.
2. The number of rendered region nodes equals `discovered_regions` (no label-keyed collapsing or deduping loss).

**Likely component to investigate:**
- `src/components/` or `src/screens/` Map tab / DUNGEON_MAP deep-view region-graph rendering code.
- Check where region node labels are sourced: ensure they read region.id / region.name / region.label (distinct per region), not a shared POI/scene title.
- Check whether nodes are keyed by region.id (correct) or by label (incorrect).

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-23T06:24:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T06:07:06Z | 2026-06-23T06:09:32Z | 2m 26s |
| implement | 2026-06-23T06:09:32Z | 2026-06-23T06:19:39Z | 10m 7s |
| review | 2026-06-23T06:19:39Z | 2026-06-23T06:24:11Z | 4m 32s |
| finish | 2026-06-23T06:24:11Z | - | - |

## Sm Assessment

**Routing decision:** Phased `trivial` workflow (setup → implement → review → finish). Single repo (`ui`), 2pt UI bug fix — trivial is the correct lane; no TDD ceremony needed for a label-sourcing fix that lands in a React component.

**Scope is bounded and confirmed:**
- This is a pure follow-up to UI #1047 (deep-view region-graph rendering already landed and works). The defect is *labeling*, not rendering.
- Driver forensics pin the root cause precisely: "The Drowned Cavern" is a POI/sub-location scene title (`region.entry_skipped_sub_location entry='The Drowned Cavern' current_region='exp001.r2'`), being painted onto distinct region nodes instead of each region's own identifier/label.
- Two observable, testable defects: (1) duplicate labels → distinct labels per region; (2) rendered node count < `discovered_regions` → counts match (label-keyed collapse).

**Why no cross-repo coordination:** The fix is entirely UI-side. The engine already exposes distinct region ids and `discovered_regions`; the bug is the client reading the wrong field / keying nodes by label. No server or content change is required. Dev should confirm the region-node component sources labels from `region.id`/`region.name` and keys by `region.id`, not by the shared POI title.

**Handoff target:** Dev (implement phase). Reviewer follows; I (SM) finish.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The duplicate-label root cause lives in the server, not the UI — `_build_dungeon_map_payload` labels every region with `palette.get(node.theme).display_name`, a THEME name shared across all regions of one theme, while `RegionNode` carries no per-region human name (only `id`/`expansion_id`/`theme`). Affects `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (`_build_dungeon_map_payload`) — if a more meaningful per-region label is ever wanted (e.g. theme + depth/bearing), it belongs there. The UI now disambiguates client-side (tabletop "Cavern 1/2/3" numbering), which is sufficient and the correct scope for this `ui` story; no server change is required to close 158-6.
- **Question** (non-blocking): The driver's "node count < `discovered_regions`" is expected server behavior — the DUNGEON_MAP frame ships deep nodes only (`discovered = [r for r in discovered_regions if r in graph.nodes]`), correctly excluding surface regions. If the table ever wants a single unified surface+deep map node count, that is a server/projection question (`map_emit.py`), not a UI one. No action needed for 158-6.

### Reviewer (code review)
- **Improvement** (non-blocking): Confirms the Dev finding — the durable home for the duplicate-label root cause is server-side (`sidequest-server/.../map_emit.py` `_build_dungeon_map_payload`, where `name = palette.get(node.theme).display_name`). The UI disambiguation is the correct scope for this `ui` story and fully closes 158-6; a future server story could give procedural regions a richer per-region label (theme + depth/bearing) if the table wants more than ordinals.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **AC2 scoped to "no UI label-collapse", not "deep node count == total discovered_regions"**
  - Rationale: The driver's "node count < discovered_regions" is not a UI collapse. The server (`map_emit.py _build_dungeon_map_payload`) intentionally ships only deep nodes — `discovered = [r for r in discovered_regions if r in graph.nodes]` — so surface regions (ropefoot/the_dropmouth), which are always in `discovered_regions` since you start above the rope, are correctly excluded from the DUNGEON_MAP frame (fog-of-war + surface/deep split, per `_descent_phase`). The UI never receives them in that frame and must not invent them. The premise's "indicating label-keyed collapsing" was the wrong diagnosis; the real, fixable defect was the duplicate *labels*, which is fully addressed.
  - Severity: minor
  - Forward impact: none — no sibling story depends on the deep frame carrying surface nodes. See the Delivery Finding documenting the server-side count behavior.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-ui/src/lib/dungeonMap.ts` — added `disambiguateRegionLabels`; `dungeonMapToMapState` now numbers duplicate region labels ("The Drowned Cavern 1/2/3") in payload order, keyed off the distinct `id`, leaving `id`/`connections`/`room_exits` (graph topology) untouched.
- `sidequest-ui/src/lib/__tests__/dungeonMap.test.ts` — NEW unit suite (5 tests): numbers duplicates, leaves singletons alone, never collapses node count, preserves graph topology, stable as the discovered set grows.
- `sidequest-ui/src/components/GameBoard/widgets/__tests__/MapWidget.test.tsx` — added a render-wiring test proving the disambiguated labels reach the on-screen Automapper `<text>` nodes via the real adapter → MapWidget → Automapper path.

**Root cause:** Server labels each deep region by its shared *theme* display name (`map_emit.py _build_dungeon_map_payload`), so distinct regions (`exp001.r2`, `exp002.r3`) with one theme all arrive labeled "The Drowned Cavern". The UI rendered the duplicate `name` verbatim. Fix disambiguates client-side in the deep-view adapter — renderer-agnostic (applies to the MapState the Automapper *and* MapOverlay consume).

**Tests:** 21/21 passing across the touched suites (dungeonMap 5, MapWidget 12, dungeon-map-wiring-153-25 e2e 4). Lint clean; typecheck clean for changed files (one pre-existing unrelated error in `GameBoard-fate-inventory-tab.test.tsx`, untouched).

**AC status:** AC1 (distinct labels) — met. AC2 (no label-keyed collapse) — met and verified; the "count < discovered_regions" premise was a misdiagnosis (server surface/deep fog-of-war split, documented above).

**Branch:** feat/158-6-map-deepview-distinct-region-labels (pushed)

**Handoff:** To review (Reviewer / Westley).

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **AC2 scoped to "no UI label-collapse", not "deep node count == total discovered_regions"**
  - Spec source: .session/158-6-session.md, AC-2 ("The number of rendered region nodes equals `discovered_regions` (no label-keyed collapsing or deduping loss)")
  - Spec text: "the rendered node count is less than the expected `discovered_regions` count, indicating label-keyed collapsing"
  - Implementation: Verified the UI never collapses nodes by label — `dungeonMapToMapState` → `toExploredRooms` → Automapper all key nodes by the distinct region `id`, never by `name`. The fix preserves every node the frame carries (unit test: "never collapses nodes — node count equals the discovered set"). I did NOT make the deep-map node count equal the *total* `discovered_regions`.
  - Rationale: The driver's "node count < discovered_regions" is not a UI collapse. The server (`map_emit.py _build_dungeon_map_payload`) intentionally ships only deep nodes — `discovered = [r for r in discovered_regions if r in graph.nodes]` — so surface regions (ropefoot/the_dropmouth), which are always in `discovered_regions` since you start above the rope, are correctly excluded from the DUNGEON_MAP frame (fog-of-war + surface/deep split, per `_descent_phase`). The UI never receives them in that frame and must not invent them. The premise's "indicating label-keyed collapsing" was the wrong diagnosis; the real, fixable defect was the duplicate *labels*, which is fully addressed.
  - Severity: minor
  - Forward impact: none — no sibling story depends on the deep frame carrying surface nodes. See the Delivery Finding documenting the server-side count behavior.

### Reviewer (audit)
- **AC2 reinterpretation (Dev)** → ✓ ACCEPTED by Reviewer: I independently verified the server source — `map_emit.py:861` `discovered = [r for r in discovered_regions if r in nodes]` excludes surface regions from the deep frame by design (fog-of-war + surface/deep split per `_descent_phase`). Making the deep map render surface nodes would be a *defect*, not a fix. The Dev's reading — "AC2 means the UI must not collapse nodes by label" — is the correct, satisfiable interpretation, and the unit test "never collapses nodes" pins it. The original AC's "indicating label-keyed collapsing" was a misdiagnosis; the real defect (duplicate labels) is fixed. No undocumented deviations found.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (GREEN) | 25 tests pass, 0 smells, lint+typecheck clean, tree clean | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (`workflow.reviewer_subagents.edge_hunter=false`); edge cases assessed by Reviewer directly — see [EDGE] in assessment |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (`test_analyzer=false`); test quality assessed by Reviewer directly — see [TEST] |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (`comment_analyzer=false`); docs assessed by Reviewer directly — see [DOC] |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (`type_design=false`); types assessed by Reviewer directly — see [TYPE] |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (`simplifier=false`); complexity assessed by Reviewer directly — see [SIMPLE] |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (`rule_checker=false`); rule compliance enumerated by Reviewer directly — see Rule Compliance + [RULE] |

**All received:** Yes (3 enabled subagents returned clean/GREEN; 6 disabled via `workflow.reviewer_subagents` and assessed directly)
**Total findings:** 0 from subagents; 2 LOW from Reviewer's own analysis (both non-blocking). 0 confirmed blocking, 0 dismissed, 0 deferred.

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A surgical, correctly-scoped UI fix. The deep-view DUNGEON_MAP adapter (`dungeonMapToMapState`) now disambiguates region labels that the server emits as a shared theme `display_name`, numbering duplicates "The Drowned Cavern 1/2/3" while leaving graph topology (`id`/`connections`/`room_exits`) untouched. Three enabled subagents (preflight, silent-failure, security) returned clean/GREEN; the six disabled subagents' domains were assessed directly below.

**Observations (≥5):**
1. `[VERIFIED]` Root cause is accurate. `sidequest-server/.../map_emit.py:871` sets `display = palette.get(node.theme).display_name` and `:861` filters `discovered` to graph nodes only. Distinct regions sharing a theme get the same label; the `id` stays distinct. Dev's diagnosis matches the source.
2. `[VERIFIED]` Correct scoping. `disambiguateRegionLabels` is called *only* from `dungeonMapToMapState` (`dungeonMap.ts:88`), which App.tsx invokes *only* on the `DUNGEON_MAP` branch (`App.tsx:1290`). The `MAP_UPDATE` surface-cartography branch (`App.tsx:1270`) is untouched — surface labels and every non-dungeon world are unaffected.
3. `[VERIFIED][SEC]` No injection/leak. The rewritten `name` flows to `Automapper.tsx:528` `<text>{rm.name}</text>` — a React-escaped JSX child, no `dangerouslySetInnerHTML`. The ordinal is a numeric `Map` counter; region `id`s are deliberately NOT incorporated (no `exp001.r2` leak). Security subagent concurs (clean).
4. `[VERIFIED][SILENT]` No silent fallback. The two `?? 0` expressions are `Map.get()` counter initialisation (absent key == count 0), immediately incremented — not error suppression. Malformed frames are already rejected loudly upstream (`App.tsx:1282` `isDungeonMapPayload` guard + `console.warn`). Silent-failure subagent concurs (clean).
5. `[VERIFIED][TYPE]` Type-clean. No `as any` / `as unknown as` / `@ts-ignore`; `??` (not `||`) used so a legitimate empty-string name wouldn't misroute; `<= 1` correctly treats a unique name as no-collision. Return type preserved (`DungeonMapLocation[]`). Typecheck clean for changed files.
6. `[VERIFIED][TEST]` Tests are real, not vacuous. The unit suite asserts concrete output arrays (numbering, singleton-untouched, no node-collapse, topology preservation, append-stability); the MapWidget test is a true render-wiring test (`getByText("The Drowned Cavern 1")` + `queryByText("The Drowned Cavern")` absent), proving the label reaches the on-screen SVG via the real adapter→MapWidget→Automapper path. Satisfies CLAUDE.md "Every Test Suite Needs a Wiring Test."
7. `[VERIFIED][DOC]` The docstring is accurate and load-bearing — it cites the exact server source of the shared label and explains the ordering/stability contract. No stale or misleading comments.
8. `[VERIFIED][SIMPLE]` Minimal and idiomatic. Two O(n) passes, no over-engineering, no dead code. The simplest implementation that meets the AC.
9. `[VERIFIED][RULE]` See Rule Compliance below — no project-rule violations.
10. `[EDGE][LOW]` Theoretical re-collision: if a theme `display_name` already ended in " N" coinciding with another node's numbered form, numbering could reintroduce a duplicate label. Non-blocking — theme display names are prose ("The Drowned Cavern", "The Rope Gallery"), worst case is a cosmetic label (no crash, no topology break). Edge-hunter was disabled; assessed directly.
11. `[LOW]` Numbering order tracks the server's `discovered_regions` ordering; if that ever shuffled, labels would renumber but stay DISTINCT — the AC ("distinct labels") holds regardless. Non-blocking.

### Rule Compliance
Project rules checked against the diff (CLAUDE.md, SOUL.md, lang-review/typescript.md):
- **No Silent Fallbacks (CLAUDE.md):** COMPLIANT — `?? 0` is counter init, not fallback; malformed frames rejected loudly upstream. (1 helper, 1 adapter — both checked.)
- **No Stubbing (CLAUDE.md):** COMPLIANT — fully implemented, no placeholders.
- **Every Test Suite Needs a Wiring Test (CLAUDE.md):** COMPLIANT — the MapWidget render test exercises the real production render path.
- **TS — no type-safety escapes (lang-review #1):** COMPLIANT — no `as any`/`as unknown as`/`@ts-ignore`/unchecked `!` in the diff.
- **TS — `??` vs `||` (lang-review #4):** COMPLIANT — `??` used for counter defaults (the one place it matters).
- **TS — `Map.get()` result used without undefined check (lang-review #4):** COMPLIANT — every `.get()` is guarded with `?? 0`.
- **TS — `key={index}` on reorderable lists (lang-review #6):** N/A in production; the Automapper keys by `rm.id` (unchanged). Test JSX uses no index keys.
- **SOUL "Tabletop First":** COMPLIANT and on-theme — numbering duplicate rooms ("Cavern 1/2/3") is the literal tabletop-DM convention.

### Devil's Advocate
Let me argue this code is broken. First attack: a malicious or buggy server sends an `explored` array where every entry has `name: ""` (empty string). The helper counts `""` → N, then renders "` 1`", "` 2`" — labels that are just a leading space and a number. Ugly, but not a crash, and a blank label was already unreadable before this change; the numbering is strictly an improvement and React renders it safely. Second attack: the server sends 10,000 regions to force a render storm. The helper is O(n) and adds negligible cost over the pre-existing `.map`; the real render cost is the Automapper SVG, which this change doesn't touch — so this is not a new DoS vector (security subagent agreed). Third attack — the genuinely interesting one: the server emits names that are *already* numbered, e.g. two entries named "The Drowned Cavern" plus one named "The Drowned Cavern 1". The two collide and become "...1" and "...2", and now there are TWO "The Drowned Cavern 1" labels — the fix reintroduced the very duplicate it set out to remove. I flagged this as `[EDGE][LOW]`. Why it doesn't block: the upstream label source is `palette.get(node.theme).display_name`, authored prose theme names that do not end in bare integers, so the collision cannot arise from real content; and even under a hostile payload the failure mode is a cosmetic repeated label, not a crash, data loss, or broken navigation (the graph still joins on `id`). Fourth attack: a confused user sees "The Drowned Cavern 2" and thinks it is a different *place* than "The Drowned Cavern 1" — but they ARE different regions (distinct ids, distinct map nodes), so the numbering communicates exactly the truth the player needs to navigate. Fifth: does this break the surface map or other worlds? No — the helper only runs inside the DUNGEON_MAP adapter; MAP_UPDATE and every non-dungeon world bypass it entirely (verified at the call sites). Conclusion: no blocking defect; the one real edge case is content-impossible and cosmetically-bounded.

**Data flow traced:** server `DUNGEON_MAP` frame → `App.tsx` `isDungeonMapPayload` guard → `dungeonMapToMapState` → `disambiguateRegionLabels` (rewrites `name` only) → `MapState.explored` → `MapWidget` → `toExploredRooms` (joins on `id`) → `Automapper` `<text>{rm.name}</text>` (React-escaped). Safe end to end.
**Pattern observed:** Renderer-agnostic disambiguation at the data-adapter boundary (`dungeonMap.ts:88`) — the distinct label rides the `MapState` both the Automapper and MapOverlay consume. Good placement.
**Error handling:** Malformed frames rejected loudly upstream (`App.tsx:1282`); the helper has no failure mode to swallow.

**Handoff:** To SM for finish-story.