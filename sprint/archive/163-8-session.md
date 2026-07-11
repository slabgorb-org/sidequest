---
story_id: "163-8"
jira_key: ""
epic: ""
workflow: "spdd"
---
# Story 163-8: Region-change-block integration test harness — drive _execute_narration_turn end-to-end so weather.zone_changed / location_description / dungeon_map / relationships emit call sites (websocket_session_handler.py ~2568-2610) are wiring-guarded (163-6 re-review follow-up)

## Story Details
- **ID:** 163-8
- **Jira Key:** (none — Jira not integrated for this story)
- **Workflow:** spdd
- **Repos:** server
- **Branch:** feat/163-8-region-change-harness
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T21:18:08Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T20:24:47.428926+00:00 | 2026-07-10T20:29:07Z | 4m 19s |
| red | 2026-07-10T20:29:07Z | 2026-07-10T20:52:28Z | 23m 21s |
| green | 2026-07-10T20:52:28Z | 2026-07-10T21:01:38Z | 9m 10s |
| review | 2026-07-10T21:01:38Z | 2026-07-10T21:18:08Z | 16m 30s |
| finish | 2026-07-10T21:18:08Z | - | - |

<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T20:30:49Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T20:53:44Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T20:53:44Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T20:53:44Z"/>
</skills-invoked>

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings (setup phase).

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): two pre-existing failures in `sidequest-server/tests/server/test_companion_brain_telemetry_passthrough.py` (`test_emit_endpoint_forwards_session_slug_and_severity_to_hub`, `test_emit_endpoint_daemon_path_unchanged` — event-type mismatch, `'render_assets.mount_remounted' != 'companion_brain_decide'`). Verified failing serially in isolation (`-n0`) on this fresh develop-cut branch with the 163-8 file not involved.
  Affects `tests/server/test_companion_brain_telemetry_passthrough.py` (ADR-154 companion-brain telemetry ingestion — needs its own fix story).
  *Found by TEA during test design.*
- **Question** (non-blocking): on a region-change turn the actor-keyed room-change branch also calls `_maybe_emit_location_description` with the free-text `character_locations` value, firing `location_description.no_source` alongside the region branch's `location_description.emitted` — GM-panel noise that could read as a content gap.
  Affects `sidequest/server/websocket_session_handler.py` (possibly key that branch on resolved region ids, or accept the noise as a deliberate loud-skip).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `tests/server/dispatch/test_pregen_bestiary_90_1.py::test_seed_manual_populates_encounters_for_wwn_world[evropi]` is flaky under xdist — failed in the parallel 163-8-dev-green run, passes in isolation (`-n0`, 25s; verified directly, not just the runner's claim). Heavy pregen test; likely resource contention.
  Affects `tests/server/dispatch/test_pregen_bestiary_90_1.py` (needs isolation or a serial marker — separate story).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): review-process hazard confirmed this story — multiple reviewer subagents mutation-testing the SAME production file concurrently in the shared worktree contaminate each other's test runs (the rule-checker's one-off `test_turn_reaches_site_map_emit_call_site` failure exactly matched the test-analyzer's concurrent removal of `_maybe_emit_dungeon_map`; settled by 15/15 + 23/23 clean reruns and no `seed_pc_regions` call site on the driven path).
  Affects `pennyfarthing-dist/agents/reviewer-*.md` process (mutation testing by review subagents should be serialized or isolated to a worktree).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): the harness pins real glenross content facts (region ids, display names, zone bindings) in a SERVER test — a content-side rename/rezone of `castle_ross`/`the_glenross_arms` breaks the server suite. Constants are centralized at the top of the test file for a one-line fix, and `_content_required` guards absence but not drift. Accepted per the 153-23 precedent; flagging so a future content edit isn't surprised.
  Affects `sidequest-server/tests/integration/test_region_change_emit_wiring_163_8.py` + `sidequest-content/.../glenross/cartography.yaml` (rename both sides together).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Guard tests are green-on-arrival, not failing RED**
  - Spec source: spdd workflow red phase / superpowers:test-driven-development
  - Spec text: "Write failing tests covering each AC" / "watch it fail"
  - Implementation: all 6 harness tests PASS on the branch — the 163-6 wiring they guard is already merged (server#1136); the story is the missing wiring GUARD, not missing wiring. Failure capability proven by mutation instead: each of the four guarded call sites was temporarily unwired (`sed` no-op swap in the handler) and the matching test confirmed FAILING with its intended diagnostic, then the source restored (`git checkout --`, tree verified clean).
  - Rationale: a green regression guard in a verification story is correct, not a smell (162-7 precedent); fake-RED tests against live wiring would be dishonest.
  - Severity: minor
  - Forward impact: Dev's green phase has no failing tests to turn green — it becomes a verification pass (run the file, confirm 6/6, no production change needed).
- **SITE_MAP guarded via loud-skip call-site proof, not a full SITE_MAP emit**
  - Spec source: story title ("dungeon_map ... emit call sites are wiring-guarded")
  - Spec text: guard the `_maybe_emit_dungeon_map` call site in the per-turn block
  - Implementation: glenross declares no sites, so a seated PC yields a silent world-scene return by design; the test instead leaves `pc_regions` unseeded and asserts the emitter's OP1 guard `dungeon.map_skipped(reason=no_pc_region)` — deterministic proof the production block called the emitter. The full SITE_MAP body is 164-4's unit-tested territory.
  - Rationale: the honest per-turn observable on a site-less world; deleting the call site kills the test, which is exactly the guarded regression.
  - Severity: minor
  - Forward impact: a site-world harness variant asserting `dungeon.map_emitted` is the natural extension if a future story wants the full body guarded end-to-end.
- **Fixture keeps dial rules; quests/fate/cartography emits in the same block not guarded**
  - Spec source: story title (names exactly four call sites)
  - Spec text: "weather.zone_changed / location_description / dungeon_map / relationships emit call sites"
  - Implementation: the graft keeps the session fixture's light `RulesConfig()` (dial) rather than tea_and_murder's real fate binding, so `_maybe_emit_fate_state` no-ops; `_maybe_emit_quests`/`_maybe_emit_cartography_map` ride the same block but are outside the four named sites (cartography MAP_UPDATE does fire in the drives — observed, not asserted).
  - Rationale: scope discipline — the story names four sites; the fate path has its own stories (118-x/151).
  - Severity: minor
  - Forward impact: none for this story; the harness helpers are reusable if a later story extends the guard set.

### Dev (implementation)
- No deviations from spec. Green was the verification pass TEA's green-on-arrival deviation predicted: zero production code written (the 163-6 wiring the tests guard is already live on develop), 6/6 story tests confirmed with fresh testing-runner evidence, lint/format clean, branch pushed. Minimalist discipline: no code beyond what the tests demand — and the tests demanded none.

### Reviewer (audit)
- **TEA: "Guard tests are green-on-arrival, not failing RED"** → ✓ ACCEPTED by Reviewer: the mutation evidence is the load-bearing substitute for watch-it-fail, and I did not take it on faith — I independently re-ran two of the four call-site mutations (weather, relationships: each kills exactly its test, tree restored clean), and the test-analyzer subagent independently reproduced ALL four plus both negative-gate mutations (always-true `_region_changed`, removed zone-unchanged guard) plus a whole-block deletion proving the `narrator.region_patch_check` anchor isolates harness failure from wiring failure. That is stronger failure-mode evidence than a conventional RED provides.
- **TEA: "SITE_MAP guarded via loud-skip call-site proof, not a full SITE_MAP emit"** → ✓ ACCEPTED by Reviewer: on site-less glenross the seated-PC path returns silently BY DESIGN (verified `_maybe_emit_dungeon_map` world-scene branch), so the OP1 `no_pc_region` skip is the only deterministic observable; the mutation check proves deleting the call site kills the test, which is the guarded regression. The full-body site-world variant is correctly deferred (164-4 owns the emit body).
- **TEA: "Fixture keeps dial rules; quests/fate/cartography emits in the same block not guarded"** → ✓ ACCEPTED by Reviewer: scope matches the story title's four named call sites; the fate emit has its own story lineage (118-x/151) and grafting real fate rules would have dragged unrelated turn machinery into this harness.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: verified zero production diff (`git diff develop...HEAD` = one test file), fresh green evidence, branch pushed and tracking.

## Sm Assessment

**Setup verified (2026-07-10):**
- Session at orchestrator root `.session/163-8-session.md` (symlink to `sprint/.session/`) — confirmed.
- Story context at `sprint/context/context-story-163-8.md` — confirmed, canonical `context-story-` prefix.
- Feature branch `feat/163-8-region-change-harness` exists in `sidequest-server` and is checked out there; base is `develop` per repos.yaml (gitflow). Orchestrator remains on `main` — no stray branch.
- Jira: skipped by design — this project does not use Jira (Keith, 2026-06-14). Keyless story is the normal state.
- Workflow field in epic YAML said `superpowers` (unregistered alias, recurring on epics 163/164); normalized to `spdd` via `pf sprint story update 163-8 --workflow spdd` BEFORE sm-setup, so the session was born saying `spdd` in all three places. Routing: spdd (phased) → next agent TEA (red phase).

**Scope for TEA (red):**
- This is the 163-6 re-review follow-up. Parent story (weather zones: `Region.weather_zone`, region-aware bootstrap, on-move re-gen) merged as server#1136 + content#529. The re-review found the region-change emit block in `sidequest-server/sidequest/server/websocket_session_handler.py` (~lines 2568–2610) has no integration coverage: the `weather.zone_changed`, `location_description`, `dungeon_map`, and `relationships` emit call sites are only unit-tested in isolation, violating "Every Test Suite Needs a Wiring Test."
- Deliverable: an integration test harness that drives `_execute_narration_turn` end-to-end (real handler path, not a unit shim) and asserts those four emits fire from their production call sites on a region change. The harness itself is the story — it should be reusable for future on-move emit guards.
- Acceptance criteria live in `sprint/context/context-story-163-8.md`. TEA owns turning them into failing tests; line numbers above are as-of-163-6-merge and may have drifted — locate by emit call site, not line number.

## TEA Assessment

**Tests Required:** Yes
**Reason:** the harness IS the story — the 163-6 re-review found the region-change emit block unit-tested only in isolation, violating "Every Test Suite Needs a Wiring Test".

**Test Files:**
- `sidequest-server/tests/integration/test_region_change_emit_wiring_163_8.py` — 6 integration tests driving the REAL `_execute_narration_turn` against the real shipped glenross world (tea_and_murder, region-mode, two authored climate zones). Commit `0d4ecb05` on `feat/163-8-region-change-harness`.

**Tests Written:** 6 tests covering the 4 guarded call sites + 2 negative invariants:
1. `test_region_change_turn_fires_weather_zone_changed` — glen_floor→highland_pass crossing fires exactly one `weather.zone_changed` (from/to/region fields) AND re-samples `sd.weather_state`.
2. `test_same_zone_region_change_does_not_refire_weather` — real region change within one zone: no event, state untouched (negative invariant).
3. `test_region_change_turn_emits_location_description` — LOCATION_DESCRIPTION frame for the NEW region (payload.region_id/region_name/prose from real content) + `location_description.emitted` event.
4. `test_unchanged_region_holds_the_region_change_gate` — same-region scene drift: no location emit, no weather re-gen (negative invariant).
5. `test_turn_emits_relationships_roster` — RELATIONSHIPS frame with the seeded encountered NPC + `relationships.emitted` OTEL span (otel_capture).
6. `test_turn_reaches_site_map_emit_call_site` — `dungeon.map_skipped(no_pc_region)` proves the per-turn `_maybe_emit_dungeon_map` call site executes (see deviation for why the loud skip is the honest observable on site-less glenross).

**Status:** GREEN-ON-ARRIVAL (deliberate — see Design Deviations). The 163-6 wiring is live; these are regression guards. **Mutation-verified:** each of the four call sites was temporarily unwired in the handler and the matching test FAILED with its intended diagnostic, then source restored (tree clean). Every test also anchors on `narrator.region_patch_check` (fires every region-mode turn) so a harness failure is distinguishable from an unwired emit.

**Suite state (testing-runner, RUN_ID 163-8-tea-red):** 14,960 passed / 341 skipped (DB-convention skips) / 2 failed — both pre-existing in `test_companion_brain_telemetry_passthrough.py`, verified failing in isolation without this story's file (logged as a non-blocking Delivery Finding).

### Rule Coverage

Tests-only diff — the applicable python lang-review checks are self-applied to the new file:

| Rule | How covered | Status |
|------|-------------|--------|
| #6 test quality | every test asserts concrete field values/frames (no truthy-only, no vacuous); mocks patched where USED (`map_emit._watcher_publish`, `wsh._watcher_publish`, handler-module sidecar watcher); skips carry reasons (`_content_required`) | pass |
| #3 annotations | module-internal test helpers (exempt class); public surface none | pass |
| #5 path handling | pathlib throughout (`world_dir / "weather.yaml"`) | pass |
| #9 async pitfalls | all coroutines awaited; AsyncMock for async seams | pass |
| #10 import hygiene | explicit imports, no cycles (module-local lazy imports mirror house style) | pass |
| #1/#2/#4/#7/#8/#11/#12 | no production code, no resources/deserialization/user input/deps in diff | n/a |

**Rules checked:** 5 of 5 applicable lang-review rules have coverage
**Self-check:** 0 vacuous tests found

**Handoff:** To Dev (Naomi Nagata) for the green phase — expected to be a verification pass: run the new file (6/6) + `uv run ruff check`/`format --check` (both clean at commit `0d4ecb05`), confirm no production change is needed, and carry the two pre-existing companion-telemetry failures as the separate finding they are.

## Dev Assessment

**Implementation Complete:** Yes (verification pass — no production code required; see Dev deviation entry)
**Files Changed:**
- `sidequest-server/tests/integration/test_region_change_emit_wiring_163_8.py` — the 163-8 harness (authored by TEA in red, commit `0d4ecb05`; green added no code)

**Tests:** 6/6 story tests passing (fresh testing-runner evidence, RUN_ID `163-8-dev-green`: suite 14,959 passed / 341 convention skips / 3 failed — 2 known pre-existing companion-telemetry failures + 1 xdist flake in `test_pregen_bestiary_90_1[evropi]`, verified passing in isolation and logged as a Dev finding; none related to this story). Lint + `ruff format --check` clean on the story file.
**Branch:** `feat/163-8-region-change-harness` (pushed to origin, tree clean, tracking set)

**Handoff:** To Reviewer (Chrisjen Avasarala) for the review phase. Review focus: the harness is the deliverable — judge the guard quality (mutation evidence in the TEA assessment), the green-on-arrival deviation rationale, and the scope choices logged as TEA deviations (SITE_MAP loud-skip observable, dial-rules graft).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — tree clean, 6/6 pass, lint/format clean, zero debug code, branch pushed |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | none (1 informal note) | confirmed 0, dismissed 0, deferred 0 — independently mutation-verified all 4 call-site guards + both negative gates + anchor isolation; noted inert `sd.local_dm` stub (recorded as [SIMPLE] LOW observation below) |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — every cited helper/event/field/region/zone cross-checked against production + content; "(RED)" label is house phase-naming convention |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 0 violations / 18 rules / 61 instances + 1 operational observation | confirmed 0 violations; the one-off site-map test failure investigated by Reviewer and attributed to concurrent subagent mutation contamination (evidence below), NOT a test defect — recorded as a process Delivery Finding |

**All received:** Yes (4 returned, 5 disabled via settings)
**Total findings:** 0 confirmed rule/quality violations, 0 dismissed, 0 deferred; 3 Reviewer LOW observations recorded in the assessment

## Reviewer Assessment

**Verdict:** APPROVED

**Scope reviewed:** one added file, `sidequest-server/tests/integration/test_region_change_emit_wiring_163_8.py` (518 lines, tests only, commit `0d4ecb05` on `feat/163-8-region-change-harness`, base develop). No production diff.

### Observations

1. `[VERIFIED]` **All four guarded call sites mutation-kill exactly their own test.** Evidence: my independent re-runs (weather mutation → only `test_region_change_turn_fires_weather_zone_changed` failed; relationships mutation → only `test_turn_emits_relationships_roster` failed; tree `git status --porcelain` = 0 after each restore) corroborating TEA's four documented mutations; `[TEST]` the test-analyzer independently reproduced all four PLUS mutations of the two negative gates (always-true `_region_changed`; removed zone-unchanged guard) PLUS whole-region-block deletion proving the `narrator.region_patch_check` anchor separates harness failure from unwiring. Complies with "Every Test Suite Needs a Wiring Test" and "Verify Wiring, Not Just Existence".
2. `[VERIFIED]` **Data flow traced end-to-end through production seams.** Player action → stubbed narrator result (`location="Castle Ross"` — the sanctioned LLM-boundary stub) → real `narration_apply._resolve_heading_to_cartography` → `snapshot.current_region`/`pc_regions` advance (narration_apply.py:4556-4563) → handler region block (websocket_session_handler.py:2540-2608) → `map_emit._maybe_regenerate_weather_on_region_change` reads the real glenross `Region.weather_zone` → `weather.zone_changed` with from/to zones; LOCATION_DESCRIPTION and RELATIONSHIPS asserted at the real broadcast seam (`sd._room.broadcast`). Only LLM/validator/sidecar collaborators are stubbed — the hermetic boundary the 152-5 house pattern prescribes.
3. `[VERIFIED]` `[RULE]` **Zero violations across 18 rules / 61 instances** (13 python lang-review checks + 5 project doctrine rules). Notable: patch-where-used verified against both modules' import-time `_watcher_publish` bindings; no source-text wiring assertions (grep-verified); PackNotFound → reasoned loud skips; pathlib throughout; all async seams AsyncMock'd and awaited.
4. `[VERIFIED]` `[DOC]` **Every documentary claim in the file is true now**: helper names, event names/fields, region ids, zone bindings, display names, cited sibling files and story numbers all cross-checked against production source and shipped glenross content by the comment-analyzer.
5. `[LOW]` **Cross-repo content coupling** at test_region_change_emit_wiring_163_8.py:75-83 — the guard pins real glenross region/zone facts in the server suite; a content rename breaks server CI. Accepted (153-23 precedent, constants centralized, `_content_required` guards absence); logged as a Delivery Finding so content authors aren't surprised.
6. `[LOW]` `[SIMPLE]` **Inert scaffolding**: `sd.local_dm = _fake_local_dm()` in `_arm_handler_for_turn` — `local_dm` is not read on this turn path (grep-verified by test-analyzer). Harmless copy-over from the 153-23 pattern; optional polish for a future touch, not worth a rework cycle.
7. `[LOW]` **Process, not code**: the rule-checker's single unreproducible failure of `test_turn_reaches_site_map_emit_call_site` was investigated and attributed to concurrent mutation testing by a sibling review subagent in the shared worktree (failure signature exactly matches `_maybe_emit_dungeon_map` removal, which the test-analyzer was performing in that window; no `seed_pc_regions` call site exists on the driven turn path — verified against session.py:1684 and all 6 production call sites; 15/15 Reviewer stress runs + 23/23 rule-checker reruns + every suite run clean). Logged as a process Delivery Finding.

### Rule Compliance

Tests-only diff; per-rule enumeration delegated to reviewer-rule-checker (18 rules × 61 instances, table in its result) and spot-verified by me: #1 silent-exceptions (6/6 `except PackNotFound` → reasoned skip — compliant), #2 mutable defaults (13/13 signatures clean), #3 boundary annotations (private-helper exemption applies; present annotations correct), #5 pathlib (2/2), #6 test quality (6/6 tests concrete-value assertions, patch-where-used, no unreasoned skips), #9 async (7/7 awaited), #10 imports (no stars/cycles; cross-test-module `_npc` import has house precedent in test_relationships_emit.py), #4/#7/#8/#11/#12/#13 n/a to this diff; doctrine: No Silent Fallbacks / No Stubbing (test doubles ≠ production stubs) / Wiring Test / No Source-Text Wiring / hermeticity — all compliant.

### Devil's Advocate

Argue this harness is a false comfort. First: it guards a solo, single-seat drive. The emit block runs inside the per-connection dispatch of a shared-world broadcast — in multiplayer, `_maybe_emit_dungeon_map` keys on each connection's `player_id` and the frames fan out per-socket. Nothing here proves the MP fan-out delivers the region-change frames to every seat; a regression that broke peer delivery (the exact class of the 2026-04-30 pingpong bug) would sail through these guards. Second: the SITE_MAP guard proves the call site is *reached*, not that a site world actually gets its map — the full emit body's only integration proof is deferred, so a breakage in `_load_site_map_context` under a real site world is invisible here. Third: green-on-arrival guards have never caught a real regression — the mutation evidence is synthetic; the first genuine test comes the day someone refactors the handler, and if the refactor renames `narrator.region_patch_check`, all six tests fail at the anchor with a message blaming the *harness precondition* — a stressed developer might read that as "the harness rotted" and weaken it rather than fix the rename. Fourth: content coupling means Jade renaming a Scottish village breaks server CI in a repo she doesn't work in. Fifth: `weather_state`/`weather_generator` are seated directly rather than through bootstrap — if 163-6's bootstrap wiring regressed, these tests stay green while production sessions have no generator at all (bootstrap is 163-6's own covered territory, but the seam between them is a gap). Weighing: every one of these is either explicitly out of the story's four-call-site scope (MP fan-out, site-body emit, bootstrap), mitigated (centralized constants, anchor message explicitly says "harness precondition, not the guarded emit"), or inherent to guard tests as a class. None is a Critical/High defect in THIS diff. The verdict stands — but the MP-fan-out gap is real enough to note for the epic's backlog grooming.

**Data flow traced:** player action → real heading-resolution region advance → region-change emit block → watcher events + typed frames at the broadcast seam (safe because the only stubs are the LLM/validator/sidecar hermetic boundary).
**Pattern observed:** house production-turn harness (153-23 lineage) extended with the anchor-assertion isolation trick at test_region_change_emit_wiring_163_8.py:238-256 — worth reusing.
**Error handling:** PackNotFound → loud reasoned skip (6 sites); negative gates mutation-pinned; no swallowed exceptions.
**Handoff:** To SM (Camina Drummer) for finish-story.

## Sm Finish State (2026-07-10 — awaiting Keith's merge)

- **PR #1137** (`slabgorb-org/sidequest-server`, `feat/163-8-region-change-harness` → `develop`) created by finish preflight, refs verified (head/base correct), `mergeable: MERGEABLE / CLEAN`, head sha `0d4ecb05`.
- **Agent merge denied** by the auto-mode classifier (agent-reviewed PR needs a human merge — expected per the 158-40 precedent). The `pf sprint story update 163-8 --status in_review` fallback was ALSO denied (classifier associated it with the merge denial), so the YAML status flip is pending too.
- **Resume instructions (after Keith merges #1137):** run `/pf-sm` → finish flow: verify `gh pr view 1137 --json state,mergedAt` shows MERGED; `pf sprint story finish 163-8`; verify archive + YAML status=done; server repo local hygiene (`git checkout develop && git pull --ff-only && git branch -d feat/163-8-region-change-harness`); commit orchestrator sprint bookkeeping on main (`chore(sprint): complete 163-8`). Merge convention: squash (`--squash`), matching develop's `(#NNN)` history.
- Orchestrator working tree deliberately holds uncommitted bookkeeping (sprint YAML verdict/workflow fields, context files, sidecar updates) for the single post-merge finish commit.