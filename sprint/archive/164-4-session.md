---
story_id: "164-4"
jira_key: ""
epic: "164"
workflow: "spdd"
---
# Story 164-4: RISKY: scene context replaces surface|deep + DUNGEON_MAP→SITE_MAP cutover (plan tasks 7–8)

## Story Details
- **ID:** 164-4
- **Jira Key:** (not configured)
- **Workflow:** spdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** spdd
**Phase:** finish
**Phase Started:** 2026-07-10T09:58:26Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-10T08:45:21Z | 2026-07-10T08:48:07Z | 2m 46s |
| red | 2026-07-10T08:48:07Z | 2026-07-10T09:00:47Z | 12m 40s |
| green | 2026-07-10T09:00:47Z | 2026-07-10T09:40:49Z | 40m 2s |
| review | 2026-07-10T09:40:49Z | 2026-07-10T09:52:25Z | 11m 36s |
| red | 2026-07-10T09:52:25Z | 2026-07-10T09:55:16Z | 2m 51s |
| green | 2026-07-10T09:55:16Z | 2026-07-10T09:56:45Z | 1m 29s |
| review | 2026-07-10T09:56:45Z | 2026-07-10T09:58:26Z | 1m 41s |
| finish | 2026-07-10T09:58:26Z | - | - |

## Sm Assessment

**Story:** 164-4 — RISKY: scene context replaces surface|deep + DUNGEON_MAP→SITE_MAP cutover (plan tasks 7–8). 5 pts, p1, type refactor.

**Workflow routing:** Sprint YAML tags this `superpowers`, which is NOT a registered pf workflow. Per settled Keith decision (`sm-decisions.md`, 2026-07-08), the 163/164/165 mapping-track stories run as **spdd** (setup→red→green→review→finish). Set up as spdd. Do not re-ask.

**Repos:** server only. Branch `feat/164-4-scene-context-site-map-cutover` created off `develop` (server branches off develop, not main).

**Scope (from plan `docs/superpowers/plans/2026-07-08-mapping-track-b-site-system.md` tasks 7–8):**
- IN — **Task 7 (RISKY map-arbitration cutover):** per-connection scene context (`world | site:<id>`) replaces the binary surface|deep `_descent_phase` arbitration; dissolve the beneath_sunden fence (`region_projection.applies_to`).
- IN — **Task 8 (RISKY protocol cutover):** `DUNGEON_MAP → SITE_MAP` — one cutover, no alias.
- OUT: UI SITE_MAP handling + scene-keyed mapData + breadcrumb (that's 164-5 / plan task 9), archetype catalog schema + materialization (164-6 / tasks 10–12), tavern+vault content (164-7 / tasks 13–14), and everything under plan §Follow-ups.
- Risk-sequencing constraint from the plan: **Sünden must stay green at every merge point.** 164-8's `sunden_descend_trace` playtest gate passed post-164-3; this story must not regress it.

**Prerequisites:** 164-1 (SiteRegistry), 164-2 (enter/exit resolvers + guard), 164-3 (router targets + movement-ladder cutover + Sünden frontier migration) all done and merged to develop.

**ACs:** None recorded in sprint YAML — TEA to define during RED from plan tasks 7–8, per the pattern used on prior mapping-track stories.

**Load-bearing carryover for TEA (from 164-3 dev-gotchas, 2026-07-09):**
1. **Cutover blast radius:** 164-3's cutover required retargeting ~21 pre-existing seam tests that encoded the OLD contract ("same behavioral contract" — retarget, don't delete). The gotcha note says explicitly: *164-4 (DUNGEON_MAP→SITE_MAP) will have the same shape of blast radius.* Expect existing tests asserting `DUNGEON_MAP` to need translation to `SITE_MAP` with the behavioral assertions preserved.
2. `test_message_type_complete_count` is a stale count test that THIS plan legitimately updates (plan §Global Constraints, Task 8) — updating it is in-scope, not a dodge.
3. Known pre-existing failures, do not attribute to this work: ~13 server tests fail vs content `develop` (WWN migration + seaboard promotion); OTEL span-count tests deadlock under `-n auto` — run affected files with `-n0`.
4. The "51 CartographyTreatmentWire ValidationErrors" noise that 164-3/165-3 kept flagging is RESOLVED (stale conftest fixture, fixed via 163-7) — don't re-chase it.

**Wiring reminder:** Per project doctrine, the suite needs at least one wiring test proving SITE_MAP is emitted from a real dispatch/broadcast path in production code — not just unit tests on payload shapes.

## TEA Assessment

**Tests Required:** Yes
**Reason:** RISKY double cutover (map arbitration + protocol rename) — no chore bypass conceivable.

**ACs (defined by TEA from plan tasks 7–8, none in sprint YAML):**
- **AC-1 (Task 7):** `sidequest.server.scene_context.resolve_scene_context(*, sd, snapshot, player_id)` returns frozen `SceneContext`: `("world", None)` for cartography regions / unseated connections / site-less worlds / unknown namespaces; `("site", <id>)` for owner-namespaced nodes (registry-only, no store IO) and legacy un-namespaced frontier nodes (store membership).
- **AC-2 (Task 7 cutover):** the beneath_sunden fence dissolves — ANY world with a declared site emits the site map when this connection's PC is in the site's graph, and the cartography emit stands down loudly for that connection. World-scene and unseated-skip behavior unchanged.
- **AC-3 (Task 8):** `DUNGEON_MAP → SITE_MAP` one cutover, no alias: `MessageType.SITE_MAP`, `SiteMap*` classes with `site_id`/`site_name`/`archetype`/`extent` (empty-string defaults), registry + validation roundtrip, old symbols GONE, `len(MessageType)` stays 59.
- **AC-4 (wiring):** the emitted frame carries the owning site's descriptor fields, is labeled `SITE_MAP`, and `dungeon.map_emitted` fires (OTEL, GM-panel visible).

**Test Files:**
- `tests/server/test_scene_context.py` — 8 tests, AC-1 (RED: ModuleNotFoundError until Task 7)
- `tests/protocol/test_site_map_message.py` — 6 tests, AC-3 (RED: ImportError until Task 8)
- `tests/server/test_site_map_emit_cutover.py` — 4 tests, AC-2/AC-4: 2 RED cutover tests + 2 GREEN guards (world-scene path + unseated loud-skip must survive the cutover)
- `tests/protocol/test_enums.py` — retargeted wire-string test to SITE_MAP + count-test docstring changelog (count stays 59)

**Tests Written:** 18 new + 1 retargeted, covering 4 ACs
**Status:** RED verified via testing-runner (`-n0`): 2 collection errors (feature-missing modules), 3 assertion failures (all feature-missing reasons), 2 guards + all 5 old-contract `test_descent_phase_map_switch.py` tests + 78 remaining enum tests PASS. Zero deviations from expected outcomes.

**Honesty split (the 165-3/165-4 convention):** the 2 guards in `test_site_map_emit_cutover.py` and the old-contract descent-phase suite pass on RED by design — they pin what the cutover must NOT break. The red-drivers are the 2 collection errors + 3 assertion failures.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 mutable defaults / shared state | `test_site_fields_default_empty`, `test_explored_shape_preserved_through_rename` (default_factory lists/dicts fresh per instance) | failing (RED) |
| #3 type annotations at boundaries | all test helpers annotated; `resolve_scene_context` keyword-only contract pinned by call shape | failing (RED) |
| #6 test quality | self-check done — every assert checks a specific value/set; no `assert True`, no bare truthy on always-truthy, no assertion-free tests | n/a (meta) |
| #10 import hygiene / no alias | `test_dungeon_map_symbols_are_gone` (no lingering re-exports), `test_message_type_site_map_wire_string` (enum member gone) | failing (RED) |
| Type-design: immutability invariant | `test_scene_context_is_frozen` (FrozenInstanceError) | failing (RED) |
| Wiring doctrine (CLAUDE.md) | `test_site_map_emit_cutover.py` — fixture-driven behavior tests through the REAL emit functions + OTEL span asserts; no source-text greps | 2 failing / 2 guards |
| OTEL principle | `dungeon.map_emitted` + loud `cartography.map_skipped` / `dungeon.map_skipped(no_pc_region)` asserted | failing (RED) + guards |

**Rules checked:** 6 of 13 lang-review checks applicable to test-design scope have coverage; the remainder (silent exceptions, resource leaks, async, deserialization, paths, logging levels, deps) bite Dev's implementation diff and are re-checked at verify/review.
**Self-check:** 0 vacuous tests found.

**Load-bearing note for Inigo (Dev):** do NOT transcribe the plan's `resolve_scene_context` snippet — it has a dead loop and a suspicious `entrance_id=pc_region` call (details in Delivery Findings + tea-gotchas 2026-07-10). The scene-context tests pin outcomes only. The fence-dissolution test deliberately avoids stubbing `_load_dungeon_map_context`; if your implementation keeps that seam, the test still exercises the real gate. Blast-radius retarget list is in Delivery Findings.

**Handoff:** To Inigo Montoya (Dev) for GREEN.

### TEA Rework Assessment (round-trip 1, 2026-07-10)

**Scope:** Reviewer HIGH only — the palette degrade must be LOUD.
**Test added:** `tests/server/test_site_map_emit_cutover.py::test_missing_theme_palette_degrade_is_loud` — drives the REAL `_load_site_map_context` on the tavern-world fixture: pins that the degrade STAYS (ctx loads, null palette KeyErrors) and RED-drives the `dungeon.theme_palette_missing` watcher event with `world` + `site_id` fields.
**RED verified:** testing-runner — 4/5 pass, the new test fails exactly on `assert missing` (event list empty); no fixture crash, degrade mechanics intact. Committed `771c8a1c`.
**Deviations:** none this round (`### TEA (test design)` entries from round 0 stand as stamped).
**Note for Dev:** the reviewer's fix spec names the span `dungeon.theme_palette_missing` with fields `{world, site_id}`, component `dungeon` + an info-level log line. No `SPAN_ROUTES` entry needed if emitted via the same `_watcher_publish` path the sibling skips use (they aren't in SPAN_ROUTES either — verify `test_routing_completeness.py` stays green).
**Handoff:** To Inigo Montoya (Dev) for the loud catch.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server, branch `feat/164-4-scene-context-site-map-cutover-r2` — note the `-r2`, see deviations):**
- `sidequest/server/scene_context.py` — NEW: frozen `SceneContext` + `resolve_scene_context` (namespace-first, legacy-frontier store membership) + `cartography_for` helper
- `sidequest/game/sites/registry.py` — two accessors: `has_sites` property, `frontier_sites()`
- `sidequest/protocol/enums.py` — `DUNGEON_MAP` → `SITE_MAP` (rename, count stays 59)
- `sidequest/protocol/messages.py` — `SiteMap{Exit,Location,Payload,Message}` + `site_id`/`site_name`/`archetype`/`extent` (empty defaults); union + `_KIND_TO_MESSAGE_CLS` updated
- `sidequest/server/websocket_handlers/map_emit.py` — `_descent_phase` DELETED; `_load_dungeon_map_context` → `_load_site_map_context(sd, site)` (per-site store load, `ThemePaletteMissingError` → null palette for non-themed site worlds, legacy-entrance marker fallback); `_build_site_map_payload` stamps site fields; `_maybe_emit_dungeon_map` gates on scene context (loud `world_scene` skip on site worlds, silent no-op on site-less worlds, `dungeon.map_emitted` span gains `site_id`), emits `SITE_MAP`; `_maybe_emit_cartography_map` stands down on `site_scene`
- Comment-accuracy sweeps: `region_projection.py`, `prompt_framework/core.py`, `websocket_session_handler.py`, `handlers/connect.py`
- Blast-radius retargets (behavioral contracts preserved): `test_descent_phase_map_switch.py` (rewritten, 5 intents kept), `test_dungeon_map_per_pc.py`, `test_region_projection_wiring.py`, `test_themes_world_tier.py`, `test_kind_to_message_cls_relocation.py`, comment fixes in `test_cartography_map_emit.py`/`test_region_bearings.py`
- +2 labeled coverage tests in `test_scene_context.py` (ported from the abandoned branch)

**Tests:** All 19 TEA red-drivers + guards GREEN. Targeted story files: 131/131 (incl. 8 DB-backed wiring tests against the REAL pack + REAL Postgres store). Full suite: **14,877 passed / 341 skipped / 1 failed** — the 1 failure is the known pre-existing content-baseline `test_beneath_sunden_room_binding_107_2` (WWN migration), not attributable. Post-`ruff format` re-verified 131/131. `ruff check`: my files clean; 4 pre-existing errors in untouched files (finding logged).

**Branch:** `feat/164-4-scene-context-site-map-cutover-r2` (pushed). The un-suffixed name is occupied on origin by the abandoned 2026-07-09 attempt — preserved untouched, see Conflict finding.

**OTEL:** span names preserved (`dungeon.map_emitted`/`dungeon.map_skipped`/`cartography.map_skipped` — no SPAN_ROUTES change needed); `map_emitted` gains `site_id`, skip reasons now `world_scene`/`site_scene`/`unknown_site` (+ existing `no_pc_region`/`empty_map`).

**Handoff:** To Westley (Reviewer) for review. PR should target `develop` from the `-r2` branch.

### Dev Rework Assessment (round-trip 1, 2026-07-10)

**Fix:** the `except ThemePaletteMissingError` branch in `_load_site_map_context` now emits `_watcher_publish("dungeon.theme_palette_missing", {world, site_id}, component="dungeon")` + an info-level log before substituting the null palette. The degrade behavior is unchanged — only the silence was removed. 14 insertions, one file.
**Tests:** rework RED test now GREEN; verified 34/34 across the cutover suite, scene-context, scene-switch, per-PC, themes world-tier, and `test_routing_completeness.py` (the new event needs no SPAN_ROUTES entry — same `_watcher_publish` path as the sibling skips). `ruff` clean.
**Commits:** `771c8a1c` (RED, TEA) + `4c6f6fdf` (fix) pushed to `feat/164-4-scene-context-site-map-cutover-r2`.
**Deviations:** none this round.
**Handoff:** Back to Westley (Reviewer) for re-review of the rework delta.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer directly |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 | confirmed 2 (1 HIGH, 1 LOW-as-designed note), downgraded 1 (medium→low w/ rationale), deferred 1 (low, future guard) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer directly |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer directly |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer directly |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1 (low-confidence doc note — same root as silent-failure #1, folded into the HIGH) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer directly |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Rule Compliance section below is the manual equivalent |

**All received:** Yes (3 enabled returned: preflight clean, silent-failure 4 findings, security 1 note; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (1 HIGH + 2 informational-as-designed), 1 dismissed-by-downgrade (with rationale), 1 deferred

### Rule Compliance

Manual rule-by-rule pass over the diff (rule-checker subagent disabled) against `.pennyfarthing/gates/lang-review/python.md` + CLAUDE.md/SOUL.md:

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| #1 silent exceptions | `except ThemePaletteMissingError` (map_emit.py `_load_site_map_context`) — the ONLY new except | **VIOLATION** (as No-Silent-Fallbacks, see [SILENT] HIGH below): typed catch, but silently substitutes a default with zero log/span, against the exception's own documented contract |
| #2 mutable defaults | `_build_site_map_payload(site=None)`, payload `default_factory` lists | compliant |
| #3 type annotations | `resolve_scene_context`, `cartography_for`, `_load_site_map_context`, registry accessors — all annotated, keyword-only where public | compliant |
| #4 logging coverage/levels | `empty_map`/`unknown_site` warn, `world_scene`/`site_scene`/`no_pc_region` info — correct classification; EXCEPT the palette catch (no log at all) | violation folded into [SILENT] HIGH |
| #5 path handling | no new path construction (pre-existing `session_world_dir` call site) | compliant |
| #6 test quality | 21 new/ported tests — specific assertions, labeled guards/coverage tests, no vacuous asserts; gap: no test on the palette-miss branch | gap folded into [SILENT] HIGH fix |
| #7 resource leaks | none introduced (pool-managed repo, pre-existing) | compliant |
| #8 unsafe deserialization | none (pydantic `model_validate` in tests only) | compliant |
| #9 async pitfalls | no async changes | compliant |
| #10 import hygiene | `scene_context.__all__` present; lazy import documented (cycle avoidance); no star imports; no alias re-exports (tested) | compliant |
| #11 input validation | `site_id`/`entrance_id` → parameterized SQL (verified `pg/dungeon.py:434` binds `%s`); no new user-input boundary | compliant |
| #12 dependency hygiene | untouched | compliant |
| #13 fix regressions | n/a (no fix round yet) | n/a |

### Devil's Advocate

Assume this cutover is broken. Where would it bleed? First, the palette catch: beneath_sunden ships a real `themes/` directory today. Suppose a future content re-org (exactly like the ADR-140 world-tier move that test file pins!) misplaces it — the deep map silently degrades to raw region ids ("exp003.r1" instead of "The Bone Crypt"), no span, no log, and the GM panel shows a healthy `dungeon.map_emitted`. Keith would ship a degraded Sünden to the playgroup and the lie detector would say all-clear. That is precisely the failure class the No-Silent-Fallbacks rule exists to catch, and the exception's own docstring forbids this fallback. Confirmed as the HIGH. Second, the double scene resolution: the two emits resolve the scene independently within one turn; if `pc_regions` mutated between them (mid-turn patch), one emit could ship a site frame AND the cartography frame ship too — the clobber bug reborn. In today's dispatch order both run after patches settle, so it's theoretical, but worth a note (the old `_descent_phase` had the identical double-read shape, so no regression). Third, a declared-but-empty bounded site yields NO map frame at all that turn — loud skip, UI keeps the stale frame; acceptable only because 164-6's one-transaction materialization closes it; if 164-6 slips, a tavern could enter blind. Fourth, the UI listens for DUNGEON_MAP until 164-5 — merging this alone dark-screens the Map tab on Sünden; epic sequencing must hold 164-5 adjacent. None of these four except the first is actionable in this diff — and the first is.

## Reviewer Assessment

**Verdict:** APPROVED (round-trip 1 — initial verdict REJECTED on the [HIGH] below; fix verified 2026-07-10, see Re-review)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT] [RULE] → **FIXED** (`4c6f6fdf`) | `except ThemePaletteMissingError → _EmptyPalette()` was a silent fallback: zero log/zero span, contradicted the exception's documented "fail loud, never an empty-palette silent fallback (CLAUDE.md)" contract (`sidequest/dungeon/themes.py:271`), regressed the old fail-loud behavior, could not distinguish "legit themeless tavern world" from "Sünden themes/ vanished", and the branch was untested | `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (`_load_site_map_context`, palette catch) | DONE — TEA RED test `test_missing_theme_palette_degrade_is_loud` (`771c8a1c`, verified failing on the missing event); Dev emits `dungeon.theme_palette_missing` `{world, site_id}` component=dungeon + info log (`4c6f6fdf`). Null-palette degrade preserved. |

### Re-review (round-trip 1, 2026-07-10)

Delta since REJECT: exactly 2 commits (`771c8a1c` RED test, `4c6f6fdf` 14-line fix). Verified by direct diff read:
- **[VERIFIED]** The catch now emits `_watcher_publish("dungeon.theme_palette_missing", {"world": sd.world_slug, "site_id": site.site_id}, component="dungeon")` + `logger.info` with lazy `%s` formatting (rule #4 level classification correct: normal-state degrade → info, not warning) — `map_emit.py` `_load_site_map_context` palette catch. Complies with No Silent Fallbacks + the exception's contract: the fallback remains, the silence is gone.
- **[VERIFIED]** Honest red-green: testing-runner recorded the RED failing exactly on `assert missing` (events empty, no fixture crash), then GREEN 34/34 across the cutover suite + scene-context + scene-switch + per-PC + themes world-tier + `test_routing_completeness.py` (the new event needs no SPAN_ROUTES entry — same `_watcher_publish` path as the sibling skip events).
- **[VERIFIED]** No scope creep in the delta: one production file, 14 insertions, comment cites the finding.
- All round-0 non-blocking observations stand as logged (Delivery Findings); no new findings from the delta.

**Verdict: APPROVED.**

**Non-blocking observations (confirmed, no fix required this round):**
- `[SILENT]` [LOW] Site-less-world skip is silent by design — docstring-argued, matches pre-cutover behavior; accepted doctrine call.
- `[SILENT]` [LOW] `cartography_for`'s `.get(world_slug)` collapses "no cartography" and "world_slug not in pack" — downgraded from medium: identical chain pre-exists in this same file (`_maybe_emit_cartography_map` `is_region_mode` block) and world binding is validated at connect; noted as future-guard improvement.
- `[SILENT]` [LOW] `getattr(sd, "dungeon_repository", None)` fallback — required field today, deliberately tested never-crash path; deferred with the hunter's one-time-warning suggestion if partial sessions ever appear.
- `[SEC]` [VERIFIED] No injection: `site_id`/`entrance_id` bind as SQL parameters (`pg/dungeon.py:434-458`, `%s` placeholders, session-scoped) — complies with rule #11. No new privacy leak: the four payload fields are world content metadata; explored-list sharing is ADR-036 doctrine.
- `[SEC]` [VERIFIED] No new path construction — `session_world_dir`/`load_theme_palette` call sites pre-date the diff (CWE-22/59 n/a).
- `[EDGE]` [VERIFIED] Boundary cases pinned by tests: unseated (`no_pc_region` loud), seated-no-region, unknown namespace never fabricates a scene, empty frontier store → world, frozen SceneContext. [EDGE][LOW]: PC in a site scene whose namespaced node is missing from the stored graph ships a 0-explored frame (span carries `discovered_regions=0` — visible); closed structurally by 164-6.
- `[TEST]` [VERIFIED] 21 new/ported tests, honest RED/guard/coverage labeling, real-store DB wiring test (`test_dungeon_map_frame_is_emitted_to_ui` drives the real pack + real Postgres store end-to-end); gap on the palette branch is the HIGH's test half.
- `[DOC]` [VERIFIED] Comment sweep accurate (module docstrings, enum/message comments, 5 stale comment sites updated); [DOC][LOW] `_maybe_emit_dungeon_map` name + `dungeon.map_*` span names now serve sites — kept deliberately so the `sunden_descend_trace` span assertions survive; B4-polish naming debt.
- `[TYPE]` [VERIFIED] Frozen `SceneContext` with `Literal` kind (tested `FrozenInstanceError`); payload site fields as plain wire strings (protocol tier correctly avoids importing genre Literals); no alias re-exports (tested).
- `[SIMPLE]` [LOW] Scene resolved independently in both emits + registry built twice in the site path — ~1 extra graph query per Sünden deep turn vs pre-cutover; acceptable now, candidate for a per-turn scene memo when Task 9/164-5 touches this seam.
- `[RULE]` Rule Compliance table above — 12 of 13 checks compliant; #1/#4/#6 fold into the single HIGH.

**Data flow traced:** free-text player action → movement dispatch (164-3) → `pc_regions` patch → narration-turn emits → `resolve_scene_context` (seats → perspective → registry/store) → parameterized SQL (`pg/dungeon.py:434`) → typed pydantic `SiteMapMessage` → `emit_fn` broadcast. Safe: no user text reaches SQL or filesystem; fog filtered by graph membership per site.
**Pattern observed:** good — the mutual-exclusion invariant now lives in ONE resolver consumed by both emits (`scene_context.py:47`), replacing two divergent gate implementations; the loud-skip taxonomy (`world_scene`/`site_scene`/`unknown_site`/`empty_map`/`no_pc_region`) is GM-panel-legible.
**Error handling:** every skip path instrumented EXCEPT the palette catch (the HIGH); `unknown_site` defends the impossible branch loudly without crashing a live turn (map_emit.py `_maybe_emit_dungeon_map`).
**Wiring:** verified — `websocket_session_handler.py:239-240` imports survive the cutover; the real-store wiring test drives the emit through the `websocket_session_handler` import path and the frame reaches `emit_fn` labeled `SITE_MAP`.

**Handoff:** Back to Fezzik (TEA) for a RED span test on the palette-miss branch, then Inigo (Dev) for the loud-catch fix. Everything else stands — the rework is surgical.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Plan Task 7's embedded `resolve_scene_context` snippet is known-buggy — a dead `sites_for_node("")` loop (the plan itself flags it) and a suspicious `repo.load_map(entrance_id=pc_region, ...)` call (feeds a non-entrance region as `entrance_id`; store keying is `load_map(*, entrance_id, site_id=DEFAULT_SITE_ID)` per `sidequest/game/pg/dungeon.py:87`).
  Affects `sidequest-server/sidequest/server/scene_context.py` (Dev must hand-verify the frontier-membership branch rather than transcribe the snippet; the RED tests pin outcomes, not plumbing).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): The cutover blast radius for GREEN — old-contract tests that will go red and need RETARGETING (same behavioral contract, not deletion): `tests/server/test_descent_phase_map_switch.py` (5 tests — `DUNGEON_MAP` label + `deep_phase` reason asserts + the `_stub_deep_ctx` seam if `_load_dungeon_map_context` dies), `tests/dungeon/test_dungeon_map_per_pc.py`, `tests/dungeon/test_region_projection_wiring.py`, plus the plan's own straggler sweep `grep -rn "DungeonMap\|DUNGEON_MAP" sidequest/ tests/`.
  Affects `sidequest-server/tests/` (retarget during GREEN, mirroring the 164-3 pattern).
  *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (non-blocking): A stale remote branch `feat/164-4-scene-context-site-map-cutover` (tip `d57a24ce`, 2026-07-09) holds an ABANDONED parallel implementation of this exact story — same design, older develop base (pre-163-7/165-4), no PR, never tracked in the sprint. My work pushed as `…-cutover-r2`; the stale branch is preserved untouched and its two unique coverage pins were ported.
  Affects `origin/feat/164-4-scene-context-site-map-cutover` (Keith should delete it once this story's PR merges).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): Re-run the `sunden_descend_trace` playtest gate post-merge (the 164-8 pattern) to satisfy plan Task 7's live-verify step — confirm `dungeon.map_emitted` now fires with `site_id=frontier` under a site scene and the surface cartography stands down in the deep.
  Affects `scenarios/sunden_descend_trace.yaml` (run it; no file change).
  *Found by Dev during implementation.*
- **Gap** (non-blocking): The UI still listens for `DUNGEON_MAP` until 164-5 (plan Task 9) cuts the client over — the Map tab will not render the renamed frame in the interim. Known epic sequencing; flagging so the cutover chain isn't half-shipped to a playtest before 164-5 lands.
  Affects `sidequest-ui/src` (story 164-5 scope).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): 4 pre-existing lint errors in files this story never touched (`tests/dungeon/conftest.py` E402 ×3, `tests/telemetry/test_tactical_telemetry_sink.py` I001, auto-fixable) — left alone per scope discipline.
  Affects `sidequest-server/tests/dungeon/conftest.py` (E402s) and `sidequest-server/tests/telemetry/test_tactical_telemetry_sink.py` (`ruff check --fix` for the I001).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The `ThemePaletteMissingError → _EmptyPalette` catch in `_load_site_map_context` is a silent fallback — no log, no watcher span, untested — violating No Silent Fallbacks and the exception's own fail-loud contract; a vanished Sünden `themes/` dir would degrade the deep map invisibly.
  Affects `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (emit a `dungeon.theme_palette_missing` watcher event + log in the catch; TEA adds the RED span test first).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Scene context is resolved independently in both map emits (plus the site-path graph load) — ~1 extra Postgres graph query per Sünden deep turn vs pre-cutover; a per-turn scene memo is a clean follow-up when 164-5/Task 9 touches this seam.
  Affects `sidequest-server/sidequest/server/websocket_handlers/map_emit.py` (optional memoization; no change this round).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `cartography_for`'s `.get(world_slug)` collapses "world has no cartography" and "world_slug not in pack" — same pre-existing pattern as the rest of the module, but a connect-time invariant assert or one-time warning would make a stale-binding bug loud.
  Affects `sidequest-server/sidequest/server/scene_context.py` (future guard, not this round).
  *Found by Reviewer during code review.*
- No new findings during re-review (round-trip 1); the blocking Gap above is resolved by `771c8a1c` + `4c6f6fdf`.
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Self-contained doubles instead of the plan's shared `sunden_sd` fixtures**
  - Spec source: plan §Task 7 step 1 (test skeleton with `sunden_sd`/`sunden_snapshot_*` fixtures, "reuse the `_SessionData`/snapshot doubles from the existing `map_emit` tests")
  - Spec text: test skeleton implies shared/conftest fixtures and two test cases
  - Implementation: `tests/server/test_scene_context.py` builds its own content-free helpers (same shape as `test_descent_phase_map_switch.py`) and covers 8 cases (world/site/legacy-frontier/unseated/no-sites/unknown-namespace/entrance-anchor/frozen)
  - Rationale: no such shared fixtures exist to reuse; the plan's 2-case skeleton under-covers the resolver's branchy contract (namespaced vs legacy-frontier vs inert registry)
  - Severity: minor
  - Forward impact: none — strictly more coverage, same contract
- **Cartography stand-down span reason left unpinned**
  - Spec source: plan §Task 7 step "rewire `_maybe_emit_cartography_map`" + existing contract (`cartography.map_skipped` reason=`deep_phase`)
  - Spec text: "replace the `_descent_phase == 'deep'` gate with `.kind == 'site'`: ...stand down..." — no new reason string named
  - Implementation: `test_cartography_stands_down_in_site_scene_on_non_sunden_world` asserts the skip event fires but not its `reason` value
  - Rationale: pinning the old `deep_phase` label would force a misleading name onto the generalized gate; Dev chooses the label (e.g. `site_phase`) and retargets the sunden tests' reason asserts in the same pass
  - Severity: minor
  - Forward impact: Dev must keep the stand-down LOUD (event asserted); reason string is theirs to name
- **Old-contract (blast-radius) tests intentionally left un-retargeted in RED**
  - Spec source: plan §Task 7 step "Update any `_descent_phase`-asserting test to the scene-context outcome" / §Task 8 straggler sweep
  - Spec text: those update steps sit in the plan's implementation sequence (after the rewiring steps)
  - Implementation: RED adds only new-contract tests + the two `test_enums.py` retargets; `test_descent_phase_map_switch.py` et al. still pass green against the old contract
  - Rationale: retargeting them before the cutover exists would big-bang the suite red with no driver; 164-3 ran the identical split (Dev retargeted ~21 tests during GREEN, recorded in dev-gotchas 2026-07-09)
  - Severity: minor
  - Forward impact: GREEN must retarget the files listed in Delivery Findings; the finish-gate suite run will catch any straggler

### Dev (implementation)
- **Branch renamed to `feat/164-4-scene-context-site-map-cutover-r2`**
  - Spec source: session file, SM assessment (branch `feat/164-4-scene-context-site-map-cutover`)
  - Spec text: "Branch `feat/164-4-scene-context-site-map-cutover` created off `develop`"
  - Implementation: pushed as `feat/164-4-scene-context-site-map-cutover-r2`; the original name is occupied on origin by an ABANDONED parallel implementation of this story (`d57a24ce`, 2026-07-09, no PR / no session / sprint never updated) which is preserved untouched
  - Rationale: force-pushing over another session's unmerged work is destructive; a suffixed branch loses nothing and blocks nothing
  - Severity: minor
  - Forward impact: SM/Reviewer must PR from the `-r2` branch; the stale branch needs a Keith decision to delete after merge (Delivery Finding)
- **Plan Task 7's `_maybe_build_runtime_cavern_payload` / `load_masks(site_id=…)` change NOT made**
  - Spec source: plan §Task 7 step "Generalize the runtime cavern fence"
  - Spec text: "In `_maybe_build_runtime_cavern_payload` (:113) … replace the `applies_to(...)` gate with a site-scene check … call `load_masks(site_id=ctx.site_id)`"
  - Implementation: function untouched — the actual code has NO `applies_to` fence there; it gates on `sd.dungeon_store`, which is dead in production (the 165-3 dead-gate caveat documented in the function docstring), and is exercised only by fixtures
  - Rationale: the plan describes a fence that does not exist at that site; rewiring a dead path is the store-unification follow-up's job (plan's own "least-churn / minimal change" note points the same way), and TEA's tests deliberately pin nothing there
  - Severity: minor
  - Forward impact: the Plan-7 store-unification follow-up should add `site_id` keying to `load_masks` when it revives that path
- **Plan's embedded `resolve_scene_context` snippet not transcribed**
  - Spec source: plan §Task 7 embedded code
  - Spec text: (snippet with the dead `sites_for_node("")` loop and `repo.load_map(entrance_id=pc_region, …)`)
  - Implementation: hand-verified resolver — namespace-first, `":" not in pc_region` guard before the frontier loop, `entrance_id=site.entrance_node_id` on the store probe; two small public accessors added to `SiteRegistry` (`has_sites`, `frontier_sites()`)
  - Rationale: TEA flagged the snippet as known-buggy; tests pin outcomes and all pass
  - Severity: minor
  - Forward impact: none — same contract, correct plumbing
- **`_descent_phase` deleted; old switch suite rewritten in place under its old filename**
  - Spec source: plan §Task 7 ("replace `_descent_phase` body to delegate — but simpler: gate at the two call sites")
  - Spec text: plan offered delegate-or-replace; the abandoned 2026-07-09 branch renamed the test file to `test_scene_map_switch.py`
  - Implementation: `_descent_phase` deleted outright (its only caller was the cartography gate — dead code after the cutover); `tests/server/test_descent_phase_map_switch.py` keeps its filename with all 5 behavioral intents retargeted (world_scene / site_scene reasons, SITE_MAP label)
  - Rationale: No Stubbing/dead-code doctrine; keeping the test filename minimizes churn and preserves git history
  - Severity: minor
  - Forward impact: none
- **Sünden live playtest verification deferred to the epic's playtest-gate mechanism**
  - Spec source: plan §Task 7 step "Verify Sünden: `just playtest-scenario sunden_descend_trace`"
  - Spec text: "confirm the deep map still emits … and the surface cartography stands down in the deep"
  - Implementation: not run in this phase (no server up; 14 live narrator turns of API spend). Covered instead by the REAL-pack + REAL-store DB wiring test (`test_dungeon_map_frame_is_emitted_to_ui`: entrance → SITE_MAP frame, room_type=entrance, span asserted) and the full scene-switch suite
  - Rationale: e2e live playtests are dedicated gate stories in this epic (164-8 gated 164-3 the same way); recommended as the post-merge gate in Delivery Findings
  - Severity: minor
  - Forward impact: SM/Keith should re-run `sunden_descend_trace` as the merge gate for the cutover chain
- **Two coverage tests added during GREEN (normally TEA lane)**
  - Spec source: TEA test files (this story)
  - Spec text: TEA's 8 scene-context cases
  - Implementation: ported 2 extra pins from the abandoned branch (seated-PC-no-region; sd lacking the `dungeon_repository` attr — the 165-3 dead-attribute trap shape), labeled as pass-on-GREEN coverage tests per the 165-3 honesty convention
  - Rationale: preserves the abandoned branch's marginal coverage before its deletion; saves a Reviewer round-trip
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA: Self-contained doubles instead of the plan's shared fixtures** → ✓ ACCEPTED by Reviewer: no such shared fixtures existed; 8 cases > the plan's 2; contract identical.
- **TEA: Cartography stand-down span reason left unpinned** → ✓ ACCEPTED by Reviewer: Dev chose `site_scene` and pinned it in the retargeted suite — the deviation resolved exactly as intended.
- **TEA: Old-contract (blast-radius) tests left un-retargeted in RED** → ✓ ACCEPTED by Reviewer: mirrors the 164-3 split; all retargets landed in GREEN and pass.
- **Dev: Branch renamed to `…-r2`** → ✓ ACCEPTED by Reviewer: correct non-destructive handling of the abandoned remote branch; force-push would have destroyed unmerged work.
- **Dev: `_maybe_build_runtime_cavern_payload` / `load_masks(site_id=…)` change NOT made** → ✓ ACCEPTED by Reviewer: verified independently — that function carries no `applies_to` fence (it gates on the dead `sd.dungeon_store`, per its own 165-3 docstring caveat); the plan text is stale; rewiring a dead path belongs to store-unification.
- **Dev: Plan's embedded resolver snippet not transcribed** → ✓ ACCEPTED by Reviewer: the snippet contains a dead loop and a mis-keyed store call; the shipped resolver is behaviorally pinned by 10 tests.
- **Dev: `_descent_phase` deleted; test file rewritten under its old name** → ✓ ACCEPTED by Reviewer: dead code after the cutover (single caller removed); all 5 behavioral intents preserved and passing.
- **Dev: Sünden live playtest deferred to the epic's gate mechanism** → ✓ ACCEPTED by Reviewer: consistent with the 164-8 precedent; the real-store DB wiring test covers the seam server-side; the post-merge `sunden_descend_trace` gate finding stands and should be honored before the cutover chain is called done.
- **Dev: Two coverage tests added during GREEN** → ✓ ACCEPTED by Reviewer: labeled per the 165-3 honesty convention; ports value from the abandoned branch before its deletion.
- **UNDOCUMENTED (added by Reviewer): silent `ThemePaletteMissingError → _EmptyPalette` fallback.** Spec (CLAUDE.md No Silent Fallbacks; `ThemePaletteMissingError` docstring: "fail loud, never an empty-palette silent fallback") says fail loudly; code silently substitutes a null palette with no log/span. Not logged as a deviation by Dev. Severity: H — this was the REJECT finding. → ✓ RESOLVED (round-trip 1): `771c8a1c` RED test + `4c6f6fdf` loud-catch fix, verified in Re-review.

Track superpowers skills invoked during this phase.

<!-- Agents: append skills invoked below this line. Do not edit other agents' entries. -->
<skills-invoked>
<skill name="test-driven-development" phase="red" at="2026-07-10T08:49:07Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T09:01:53Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T09:32:40Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T09:33:05Z"/>
<skill name="test-driven-development" phase="red" at="2026-07-10T09:53:11Z"/>
<skill name="test-driven-development" phase="green" at="2026-07-10T09:56:00Z"/>
<skill name="verification-before-completion" phase="green" at="2026-07-10T09:56:00Z"/>
<skill name="requesting-code-review" phase="green" at="2026-07-10T09:56:00Z"/>
</skills-invoked>