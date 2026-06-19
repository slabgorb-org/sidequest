---
story_id: "126-25"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-25: [SERVER] Wire world-tier Fate gear.yaml into rules.fate.gear_catalog so #945 promotes world-specific found-items

## Story Details
- **ID:** 126-25
- **Jira Key:** (none)
- **Workflow:** tdd
- **Repos:** server
- **Stack Parent:** none

## Story Summary

The #945 Fate item-promoter (game/ruleset/fate_item_promotion.py:match_gained_gear) matches a gained item against `_fate_cfg.gear_catalog`, but `gear_catalog` is loaded from the GENRE tier ONLY. World-tier `worlds/<world>/gear.yaml` is NOT merged, so a world-specific Fate GearDef can never be seen by the promoter.

This blocks 126-21 (Oz silver shoes and other world-specific found items cannot be promoted to aspects). The fix merges world-tier gear.yaml into the effective gear_catalog (by-id, world wins), and surfaces the Phase-2 narrator grants_aspect path.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T13:05:44Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T12:23:30Z | 2026-06-19T12:26:26Z | 2m 56s |
| red | 2026-06-19T12:26:26Z | 2026-06-19T12:45:59Z | 19m 33s |
| green | 2026-06-19T12:45:59Z | 2026-06-19T12:58:42Z | 12m 43s |
| review | 2026-06-19T12:58:42Z | 2026-06-19T13:05:44Z | 7m 2s |
| finish | 2026-06-19T13:05:44Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings.

### TEA (test design)
- **Improvement** (non-blocking): the world-first resolution seam Dev needs already exists at the exact call site — RED capture shows `resolve_inventory` already fires during `_apply_narration_result_to_snapshot` with `world_slug=oz, tier=genre`. Affects `sidequest/server/narration_apply.py:4966-4967` (resolve fate gear the same way `resolve_inventory(pack, snapshot.world_slug)` is already resolved here, instead of reading `pack.rules.fate.gear_catalog` raw). *Found by TEA during test design.*
- **Question** (non-blocking): AC4 (surface narrator `grants_aspect` to the tool-contract vs. split) is a design DECISION, not a fixed behavior — deliberately NOT covered by a RED test (see TEA deviation). Affects the narrator tool-contract / prompt zone (`narration_apply.py:4974` already CONSUMES the field; nothing SETS it). Dev/Architect must decide and record per the SM assessment. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): AC4 resolved by SPLIT — recommend the SM file a follow-up story to surface narrator `grants_aspect` to the narrator tool-contract/prompt (the design doc's dormant Phase-2). Affects the narrator agent's tool definitions / prompt zone (the consumer `narration_apply.py:4974` already reads the field; nothing instructs the narrator it may SET it). Not blocking — AC2's catalog-promoter path is the must-land deliverable and is complete. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `resolve_fate_gear_catalog` emits no observability span on the genre-baseline early-return path, unlike the sibling `resolve_inventory` (which emits `_emit_inventory_resolved(op="resolved")`). AC5 (merge observable) is satisfied; this is a parity nice-to-have so the GM panel can confirm the resolver ran on the common no-world-gear path. Affects `sidequest/game/ruleset/fate_gear.py` (add an `_emit_fate_gear_resolved` before `return genre_gear`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `getattr(world, "gear", []) or []` in the resolver is belt-and-suspenders — after the `world is not None` guard, `world.gear` is always a present list, so a direct `world.gear` would be cleaner and fail loud on a future field removal. Affects `sidequest/game/ruleset/fate_gear.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

Note: Story YAML repos field reads 'server,ui' but SESSION Repos is authoritative: server-only (story 126-25 is SERVER ONLY per the description and the split from 126-21 AC3). UI work deferred to 126-17 (defend tray).

### TEA (test design)
- **AC4 (narrator grants_aspect surfacing) is NOT covered by a RED test**
  - Spec source: context-story-126-25.md, AC4 / story description "ALSO IN SCOPE"
  - Spec text: "either surface grants_aspect to the narrator tool-contract ... or split to its own story with the gap documented; whichever, the decision is recorded"
  - Implementation: no failing test written for AC4; left as a Dev/Architect decision recorded in the assessment + a Delivery Finding
  - Rationale: AC4 is a surface-vs-split DECISION, not a fixed behavior a RED test can pin. The CONSUMPTION of `grants_aspect` is already covered (`tests/server/test_fate_item_promotion_wiring.py::test_narrator_grants_aspect_on_invented_item`); the gap is the narrator being *told* it may set the field — a tool-contract/prompt change that is not behaviorally testable in isolation and may be split out.
  - Severity: minor
  - Forward impact: if Dev surfaces `grants_aspect` to the tool-contract, that change needs its own coverage (verify phase or a follow-up); if Dev splits it, file the follow-up story. Either way the decision must be recorded.
- **Loader test pins "World.gear loads regardless of ruleset" via a dial-bound fixture**
  - Spec source: context-story-126-25.md, AC1
  - Spec text: "worlds/<world>/gear.yaml is loaded ... into the effective Fate gear_catalog for the active world"
  - Implementation: `tests/genre/test_126_25_world_gear_load.py` loads the dial-bound `test_genre` clone (no Fate fixture pack exists) and asserts `World.gear` is populated — pinning an UNCONDITIONAL world-gear load, not a fate-gated one
  - Rationale: mirrors the genre-tier precedent exactly — `GenrePack.gear` is set unconditionally at loader.py:2562 (only the *merge into rules.fate* is fate-gated). Gating the world load on `ruleset=='fate'` would diverge from the genre tier and break this test; the merge stays fate-gated at resolution time (the behavioral suite proves that).
  - Severity: minor
  - Forward impact: Dev must load `World.gear` unconditionally and fate-gate only the effective-catalog merge.

### Dev (implementation)
- **Corrected TEA's `source_gear` assertion in the AC2 test (back-link literal was wrong)**
  - Spec source: tests/server/test_126_25_world_tier_fate_gear_wiring.py (TEA RED), AC2 step 2
  - Spec text: TEA asserted `aspect.source_gear == "narrator:oz_silver_shoes"` (the GearDef *catalog* id)
  - Implementation: changed to `aspect.source_gear == shoes["id"]` (the actual stored inventory-item id). MEASURED: `_narrator_item_dict` (narration_apply.py:4780) always mints the item id from the NAME and ignores a passed `id`; the promoter's documented contract is `source_gear == the inventory item's id`, not the GearDef id. Did NOT change `_narrator_item_dict` (out of scope — no AC requires id-preservation). The match fires by case-folded NAME, the realistic placement-content path (AC3).
  - Rationale: the literal over-specified an unrelated, unchanged behavior; the corrected form is stronger (back-link integrity against the real item). AC2 intent — promote → projection → invokable +2 — is fully met. The existing genre-tier test only passed because its item name slugified to the same string as its id.
  - Severity: minor
  - Forward impact: none — robust even if a later story re-ids matched items to the GearDef stable id (the assertion reads the actual id).
- **AC4 resolved by SPLIT — narrator `grants_aspect` tool-contract surfacing NOT implemented here**
  - Spec source: context-story-126-25.md, AC4 / story "ALSO IN SCOPE"
  - Spec text: "either surface grants_aspect to the narrator tool-contract ... or split to its own story with the gap documented; whichever, the decision is recorded"
  - Implementation: chose SPLIT. Did not touch the narrator tool-contract/prompt. The CONSUMPTION (`narration_apply.py:4974` reads `entry['grants_aspect']`) already exists and is covered by `test_fate_item_promotion_wiring.py::test_narrator_grants_aspect_on_invented_item`; the dormant Phase-2 is the narrator being *told* it may set the field.
  - Rationale: it is a narrator-agent prompt/tool-contract change in a DIFFERENT subsystem with its own design surface (the design doc's named Phase-2); no 126-25 test requires it; AC2 (the must-land catalog-promoter path) is complete and independent. Minimalist discipline — don't add what no AC/test in this story mandates.
  - Severity: minor
  - Forward impact: a follow-up story should surface `grants_aspect` to the narrator tool-contract to activate Phase-2 narrator promotion (recorded as a Delivery Finding for the SM to file).

### Reviewer (audit)
- **SM note (repos server,ui vs server)** → ✓ ACCEPTED by Reviewer: the YAML field is genuinely `server` (verified `pf sprint story field 126-25 repos`); the diff is server-only. No UI surface touched. Correct.
- **TEA: AC4 not covered by a RED test** → ✓ ACCEPTED by Reviewer: AC4 is a surface-vs-split DECISION, not a fixed behavior; pinning it with a RED test would be inappropriate. The consumption path is already covered by `test_narrator_grants_aspect_on_invented_item`. Sound.
- **TEA: loader test pins unconditional world-gear load via a dial fixture** → ✓ ACCEPTED by Reviewer: matches the genre-tier precedent (`GenrePack.gear` loads unconditionally; only the merge is fate-gated). The diff implements exactly this — verified `loader.py` loads `World.gear` outside any ruleset gate, and the merge is reached only behind the FateSheet gate at the call site. Correct and consistent.
- **Dev: corrected TEA's `source_gear` assertion** → ✓ ACCEPTED by Reviewer: independently verified — `_narrator_item_dict` (narration_apply.py:4780) mints the item id from the NAME and ignores a passed `id`; the promoter's contract is `source_gear == the inventory item's id`. The original literal `"narrator:oz_silver_shoes"` was factually wrong; `== shoes["id"]` is the correct, stronger back-link assertion. Did NOT change production behavior (no scope creep). Sound.
- **Dev: AC4 resolved by SPLIT (narrator grants_aspect surfacing deferred)** → ✓ ACCEPTED by Reviewer: the story explicitly permits "split with the gap documented." The narrator tool-contract is a distinct subsystem; AC2 (the must-land catalog-promoter path) is complete and independent; the gap is documented as a Delivery Finding for the SM to file a follow-up. Sound.
- No UNDOCUMENTED deviations found: the diff matches the session's recorded decisions.

## Sm Assessment

**Route:** Fresh server-only story (repos: server), workflow `tdd` (phased). No Jira key (skipped), no `depends_on`, no stale session/archive, no blocking PRs. Branch `feat/126-25-wire-world-tier-fate-gear` created on `develop`. → RED phase, owner TEA.

**This is a wiring story, not a new feature** — the engine (#945 promoter) and the content (Oz `gear.yaml`) both already exist; the world tier just isn't merged into the catalog the promoter reads. Per project doctrine: *wire up what exists, don't reinvent.* The whole point of this story is the end-to-end wiring test (AC2) — a merge unit test alone does NOT satisfy this story.

**Seams TEA/Dev must touch (all server):**
- `game/genre/loader.py:2130` — `_load_gear` reads genre-tier `<pack>/gear.yaml` → `rules.fate.gear_catalog`. World-tier `worlds/<world>/gear.yaml` is the gap.
- `game/ruleset/fate_item_promotion.py:match_gained_gear` — conservative-exact matcher: id → slug → case-folded name. `'Silver'` must NOT bind `'Silver Shoes'`. The test's granted item must resolve to GearDef id `oz_silver_shoes` / name 'The Silver Shoes of the Dead Witch'.
- `narration_apply.py:4967` (catalog match) and `:4974` (consumes `entry.get('grants_aspect')`).

**Precedent to mirror:** the ADR-145 §D3 by-id inventory merge (world wins). Genre catalog stays unpolluted — a wonderland/gulliver session must NOT see `oz_silver_shoes` (AC1 negative assertion; mirror my memory's world-tier merge precedent).

**Content already authored (126-21, inert until this lands), do NOT re-author:** `genre_packs/wry_whimsy/worlds/oz/gear.yaml` (`oz_silver_shoes` → 'Three Steps Home'; `oz_golden_cap` → 'Three Commands of the Winged Monkeys'). It's in the content repo, not in scope for this server story — but the wiring test depends on it loading.

**AC4 decision flagged for Dev/Architect to make and RECORD:** the narrator-side `grants_aspect` surfacing (`narration_apply.py:4974` consumes it, but zero callers set it — dormant Phase-2). Either (a) surface `grants_aspect` to the narrator tool-contract, or (b) split it to its own story with the gap documented. Not the SM's call — but it must not be silently dropped. AC2 (catalog promoter path) is independent of this and is the must-land deliverable.

**OTEL (AC5) is load-bearing here, not optional** — the GM panel is the lie detector. The world-gear merge must emit a span/log naming which world gear ids merged, or we can't tell wiring from improv.

## Acceptance Criteria
1. worlds/<world>/gear.yaml is loaded and its GearDefs merge by-id (world wins) into the effective Fate gear_catalog for the active world; the genre-tier catalog stays unpolluted (a wonderland/gulliver session does NOT see oz_silver_shoes).
2. WIRING TEST (full path, not just the merge): active world=oz, player gains the silver shoes → fate.item_promoted span fires with source=catalog → the 'Three Steps Home' aspect appears on the FateSheet and is invokable in a 4dF resolution. Mirrors the design doc's mandatory end-to-end wiring test.
3. Match robustness: the placement content's granted item (id/name) resolves to GearDef oz_silver_shoes under match_gained_gear's exact discipline; if a placement-content change is needed (stable item id/name), file/coordinate it so the chain actually connects in real play.
4. Phase-2 gap resolved (126-21 AC3): either surface grants_aspect to the narrator tool-contract (activating dormant Phase-2 narrator promotion) or split to its own story with the gap documented; whichever, the decision is recorded and the narrator path is no longer silently dead.
5. OTEL: the world-tier gear merge is observable (span or log: which world gear ids merged into the catalog) so the GM panel can confirm the world artifacts were wired, not just authored.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a (3-pt feature wiring story; full RED suite written)

**Test Files:**
- `tests/server/test_126_25_world_tier_fate_gear_wiring.py` — behavioral, drives the REAL consumer `_apply_narration_result_to_snapshot` (no source-text/wiring-by-grep): world-tier merge promotion (AC2 full path → aspect → FATE_STATE projection → +2 on 4dF), world-wins-by-id (AC1), union-not-replace guard (AC1), world-scoping/no-leak guard (AC1), conservative-exact matcher on the world path (AC3, exact-name RED + partial-name guard), and the merge OTEL watcher event (AC5).
- `tests/genre/test_126_25_world_gear_load.py` — loader wiring (AC1 "is loaded"): `World.gear` model field exists (allowed reflection tripwire), `load_genre_pack` populates `World.gear` from `worlds/<world>/gear.yaml`, absent file → `[]` (No Silent Fallbacks).

**Tests Written:** 10 tests covering ACs 1, 2, 3, 5. AC4 deliberately deferred (decision — see Design Deviations).
**Status:** RED — verified via testing-runner (RUN_ID 126-25-tea-red): 7 fail for the intended reasons (no `World.gear` field; loader reads genre-only; promoter consults `pack.rules.fate.gear_catalog` only; no merge event), 0 collection/import/fixture errors, 0 pack-load defects. 3 guards pass by design (union, no-leak, partial-name rejection) — they prove the genre-tier path is live so the world-tier failures are specifically the missing merge.

### Rule Coverage

Python lang-review is largely a Dev self-review checklist; the load-bearing project rules for a wiring story are CLAUDE.md's. Coverage:

| Rule (source) | Test(s) | Status |
|---------------|---------|--------|
| Verify wiring, not existence — drive the real consumer (CLAUDE.md "No Source-Text Wiring Tests") | `test_world_tier_gear_promotes_to_invokable_aspect_when_world_active` (full path via `_apply_narration_result_to_snapshot`) | failing |
| Every test suite needs a wiring test (CLAUDE.md) | the AC2 end-to-end test + `test_loader_populates_world_gear` (real `load_genre_pack`) | failing |
| OTEL Observability — every subsystem decision emits a span (CLAUDE.md) | `test_world_gear_merge_emits_observable_event` | failing |
| No Silent Fallbacks (SOUL/CLAUDE.md) | `test_loader_absent_world_gear_is_empty` (absence = `[]`, not error) | failing |
| Crunch in genre / Flavor in world — world artifacts scoped to their world | `test_world_gear_does_not_leak_to_a_sibling_world` | passing (guard) |
| Tests must not point at live content (project memory) | both files use synthetic fixtures (`minimal_pack_factory` clone, MagicMock pack) — no wry_whimsy/oz coupling | n/a |
| #6 test quality — meaningful assertions, no vacuous checks (python.md) | self-check below | n/a |

**Rules checked:** the applicable CLAUDE.md/SOUL principles + python.md #6 all have coverage; the remaining python.md checks (#1-5, #7-13) are Dev-side self-review on the implementation diff (none authored by TEA).
**Self-check:** 0 vacuous assertions. Every test asserts specific values (aspect text, `promoted` flag, `ladder_total == 3`, field presence, the merge event payload). The 3 guard tests are non-vacuous — each pins a specific behavior a wrong implementation (REPLACE-not-union, leak, relaxed matcher) would break.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Expected implementation (mirror the ADR-145 §D3 inventory precedent — DO NOT reinvent):
1. Add `World.gear: list[GearDef] = Field(default_factory=list)` (sibling to `World.classes`/`World.seed_tropes`).
2. Loader: read `worlds/<world>/gear.yaml` via the existing `_load_gear(...)` and set `World.gear` — unconditionally, mirroring the genre-tier load at loader.py:2562.
3. A world-first effective-gear resolver (mirror `resolve_inventory(pack, world_slug)`): merge genre `rules.fate.gear_catalog` ∪ `World.gear` by id (world wins), emit a `state_transition` merge event naming `world_slug` + merged gear ids (mirror `_emit_inventory_merged`).
4. Wire it at `narration_apply.py:4966-4967`: pass `snapshot.world_slug` (already in scope) to the resolver instead of reading `pack.rules.fate.gear_catalog` raw.
5. AC4 DECISION (record it): surface narrator `grants_aspect` to the tool-contract, or split to a follow-up story. Not blocking AC2.

## Dev Assessment

**Implementation Complete:** Yes — built exactly to the TEA plan (mirrors the ADR-145 §D3 inventory precedent; nothing reinvented).

**Files Changed (4 source + 1 test, all server):**
- `sidequest/genre/models/pack.py` — added `World.gear: list[GearDef] = Field(default_factory=list)` (world-tier Fate gear CATALOG, sibling to `World.inventory`/`World.classes`).
- `sidequest/genre/loader.py` — load `worlds/<world>/gear.yaml` via the existing `_load_gear(...)` into `World.gear`, UNCONDITIONALLY of ruleset (mirrors the genre-tier `GenrePack(gear=...)`); attached at the `World(...)` build.
- `sidequest/game/ruleset/fate_gear.py` — new `resolve_fate_gear_catalog(pack, world_slug)` (genre ∪ world by id, world wins; falsy/unknown world or no world gear → genre baseline) + `_emit_fate_gear_merged` (`state_transition`/`op=merged` watcher event naming world + merged ids, mirrors `_emit_inventory_merged`). Updated the now-stale module docstring (was "future story").
- `sidequest/server/narration_apply.py` — wired the promotion site (the gained-item path) to call `resolve_fate_gear_catalog(pack, snapshot.world_slug)` instead of reading `pack.rules.fate.gear_catalog` raw.
- `tests/server/test_126_25_world_tier_fate_gear_wiring.py` — corrected one over-specified `source_gear` assertion (see Design Deviations).

**Tests:** 10/10 GREEN (RUN_ID 126-25-dev-green-2). Blast-radius regression run (RUN_ID 126-25-dev-green): 615 passed, 0 regressions across the fate ruleset suite, genre loader, inventory-resolve, stocks-world-load, and telemetry span tests. `ruff check` + `ruff format --check` clean on all changed files.

**ACs:** AC1 (load + by-id merge, world wins, genre unpolluted) ✅ · AC2 (full path → aspect → projection → +2 on 4dF) ✅ · AC3 (conservative-exact matcher on the world path) ✅ · AC4 resolved by SPLIT (decision recorded — follow-up filed as a Delivery Finding) ✅ · AC5 (merge observable via `state_transition` event) ✅.

**Self-review (judgment):** wired to the real consumer (not just a helper) ✓ · follows project patterns (resolve_inventory/effective_bestiary/_emit_inventory_merged) ✓ · No Silent Fallbacks honored (absent file → `[]`, unknown world → genre baseline, both documented) ✓.

**Branch:** feat/126-25-wire-world-tier-fate-gear (pushed)
**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (10/10 GREEN, ruff+pyright clean, 0 smells/debug) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see Edge observations) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (LOW) | confirmed 1 (downgraded to LOW, non-blocking), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see Test observations) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see Doc observations) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see Type observations) |
| 7 | reviewer-security | Yes | clean | none (4 rule classes checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see Simplify observations) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer (see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents` and covered by the Reviewer)
**Total findings:** 0 confirmed blocking, 2 confirmed non-blocking ([LOW]), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Adversarial review of a tight, precedent-faithful server change (520+ lines, mostly tests). The implementation mirrors the ADR-145 §D3 inventory merge (`resolve_inventory`) and the `_emit_inventory_merged` observability pattern, and is wired end-to-end into the real consumer. No Critical/High issues. Two [LOW] non-blocking observations recorded.

**Observations (9):**
- [VERIFIED] **Wired to the real consumer, not half-wired** — `resolve_fate_gear_catalog(pack, snapshot.world_slug)` is called at the production item-gain promotion site (`narration_apply.py:4971`), and `World.gear` is populated by the loader (`loader.py:1887`). The AC2 end-to-end test drives `_apply_narration_result_to_snapshot` (the real path), not a synthetic helper. This is the load-bearing CLAUDE.md "verify wiring" rule — it passes.
- [SEC] [VERIFIED] **Security clean** (subagent, 4 rule classes, 0 violations): world `gear.yaml` loads via `_load_gear` → `_load_yaml_raw` (`yaml.safe_load`, never `yaml.load`/`eval`); `GearDef.model_validate` (extra=forbid) validates at the boundary; the `_emit_fate_gear_merged` span carries only content-authored ids + integer counts (no PII/secrets/paths); no injection/ReDoS surface.
- [SILENT] [LOW] **Genre-baseline path emits no observability span** (`fate_gear.py` early return `if not world_gear: return genre_gear`) — unlike the sibling `resolve_inventory`, which emits `_emit_inventory_resolved(op="resolved")` on its genre-baseline branch. AC5 (the story's OTEL requirement) asks only that the *merge* be observable, which it is (`_emit_fate_gear_merged`); the genre-baseline branch is the unchanged pre-existing passthrough (it never emitted a span before this story). Confirmed at LOW, non-blocking; recorded as an Improvement delivery finding for parity.
- [TYPE] [LOW] **`getattr(world, "gear", []) or []`** (`fate_gear.py`) is belt-and-suspenders — after the `world is not None` guard, `world.gear` is always a present list (`default_factory=list` on a real World; the test doubles pass `gear=`). `world.gear` would be cleaner and fail loud on a future field removal. Harmless defense (silent-failure-hunter concurs); non-blocking.
- [EDGE] [VERIFIED] **Edge cases handled** — `pack is None` → `[]`; `world_slug` None/empty → genre baseline (short-circuit); unknown world → `.get()` None → genre baseline; world with `gear=[]` → genre baseline + no spurious merge event; duplicate ids → dict-merge last-wins (world appended after genre → world wins by id AND by name). Evidence: `fate_gear.py` resolver body lines.
- [TEST] [VERIFIED] **Test quality solid** — behavioral suite drives the real consumer; the 3 guards (union, no-leak, partial-name) are non-vacuous (each pins a distinct wrong-impl failure: REPLACE-not-union, leak, relaxed matcher); the AC5 event filter is specific (`field` contains "gear" AND `world_slug=="oz"` AND `oz_silver_shoes` in fields — the gained-item events carry the name-slug id, not `oz_silver_shoes`, so no false match); the loader test uses the real `load_genre_pack`; the model-field check is the allowed reflection tripwire. No regression: I ran the genre-tier sibling `test_fate_item_promotion_wiring.py` + `test_fate_item_promotion.py` → 16 passed.
- [DOC] [VERIFIED] **No stale comments introduced; one fixed** — the `fate_gear.py` module docstring (was "world-tier merge is a future story") was updated to describe the shipped resolver. New docstrings on `World.gear`, the resolver, and the emit are accurate and reference the precedent. Loader + narration_apply comments accurate.
- [SIMPLE] [VERIFIED] **Minimal, no dead code** — the resolver is as simple as a by-id merge requires; `overridden` is computed solely for the observability event (justified). No over-engineering, no unused symbols.
- [RULE] [VERIFIED] **Python + project rules** — pathlib path (`world_path / "gear.yaml"`), safe_load, full type annotations, no mutable defaults (`Field(default_factory=list)`, keyword-only args), TYPE_CHECKING import avoids a cycle, deferred local imports mirror the `_emit_inventory_merged` precedent. No-Silent-Fallbacks honored (absent file → `[]` documented; malformed → loud `GenreLoadError`). OTEL Observability Principle satisfied for the fix (the merge — the new subsystem decision — emits a span).

**Data flow traced:** narrator declares gained item → `_apply_narration_result_to_snapshot` → (recipient has FateSheet) → `resolve_fate_gear_catalog(pack, snapshot.world_slug)` → genre ∪ world gear by id (world wins) → `promote_gained_item` matches by id/slug/case-folded name → appends `Aspect` to the FateSheet → FATE_STATE projection → invokable +2 on a 4dF roll. Safe: world gear is pydantic-validated at load; the merge is a pure read; the active world comes from `snapshot.world_slug` (same source the adjacent `resolve_inventory` call at line 4915 uses).

### Rule Compliance

| Rule (source) | Instances in diff | Verdict |
|---------------|-------------------|---------|
| No Silent Fallbacks (CLAUDE.md/SOUL.md) | resolver early-return, `_load_gear` absent→[], `getattr` default | Compliant — all documented intentional resolutions; malformed YAML fails loud. (Genre-baseline-span parity gap noted [LOW], not a fallback.) |
| OTEL Observability — subsystem decisions emit spans (CLAUDE.md) | the world merge | Compliant — the new decision (merge) emits `_emit_fate_gear_merged`. Genre-baseline passthrough span is a [LOW] parity nice-to-have. |
| Verify wiring, not existence (CLAUDE.md) | resolver call-site, loader populate | Compliant — real consumer + e2e test. |
| #5 path handling (python.md) | `world_path / "gear.yaml"` | Compliant — pathlib. |
| #8 unsafe deserialization (python.md) | world gear.yaml load | Compliant — `yaml.safe_load` via `_load_gear`. |
| #3 type annotations (python.md) | resolver, emit, field | Compliant — fully annotated; TYPE_CHECKING import. |
| #2 mutable defaults (python.md) | `World.gear`, fn signatures | Compliant — `Field(default_factory=list)`, keyword-only args. |
| #6 test quality (python.md) | both test files | Compliant — meaningful assertions, no vacuous checks (see Test observation). |
| #10 import hygiene (python.md) | TYPE_CHECKING + deferred local imports | Compliant — no star/circular; deferred imports mirror precedent. |
| Crunch in genre / Flavor in world (SOUL.md) | `World.gear` is world-tier CAST/CATALOG, merge fate-gated at resolution | Compliant — world artifact scoped to its world; genre stays the rulebook. |

### Devil's Advocate

Let me argue this is broken. **First attack — the merge silently corrupts the genre catalog for other worlds.** Could a session in world A see world B's gear? No: `resolve_fate_gear_catalog` reads `pack.worlds.get(world_slug)` — only the *active* world's gear merges, and the merge produces a fresh `merged_by_id` dict each call (no mutation of `rules.fate.gear_catalog`). The genre catalog object is never written. The `test_world_gear_does_not_leak_to_a_sibling_world` guard pins this. **Second attack — world-wins is actually genre-wins.** The dict-merge inserts genre first then overwrites with world (`merged_by_id[world_def.id] = world_def`), so world wins on a shared id; the `test_world_gear_wins_over_genre_gear_on_shared_id` test would fail if reversed — it passes. **Third attack — a confused author ships a malformed `worlds/oz/gear.yaml` and the world silently loses its gear.** No: `_load_gear` raises `GenreLoadError` on a non-list or a bad GearDef (pydantic), so pack load fails loud naming the file. Only a truly *absent* file → `[]`, which is the documented common case. **Fourth attack — the matcher promotes the wrong item.** `match_gained_gear` stays conservative-exact (id → slug → case-folded name); 'Silver' does not bind 'The Silver Shoes of the Dead Witch' — the `rejects_partial_name` guard pins it. **Fifth attack — a non-Fate world that ships gear.yaml.** World gear loads regardless of ruleset (by design, mirroring genre-tier), but the merge only runs behind the `recipient_char.core.fate_sheet is not None` gate at the call site, so a non-Fate PC never invokes the resolver — the world gear sits inert, exactly as a non-Fate pack's gear does. **Sixth attack — `snapshot.world_slug` is stale or empty mid-session.** Empty → genre baseline (safe degrade to prior behavior). The same field already drives `resolve_inventory` two lines up, so if it were unreliable, inventory resolution would already be broken. The only thing my devil's advocate surfaces that the review didn't already have is the observability blind spot on the genre-baseline path — already captured as the [LOW] [SILENT] finding. Nothing rises to blocking.

**Handoff:** To SM for finish-story.