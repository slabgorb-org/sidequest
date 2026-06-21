---
story_id: "157-3"
jira_key: null
epic: "157"
workflow: "tdd"
---
# Story 157-3: [ENGINE] NPC walk-on origin-stamp + authored-cast staging on region entry (Seam 2)

## Story Details
- **ID:** 157-3
- **Jira Key:** none (epic-157 is a no-jira epic)
- **Workflow:** tdd
- **Stack Parent:** 157-2 (zone_eligibility core + factions tag + creature inject filter; merged on server develop via PR #1002, commit 0f199b0f)
- **Repos:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T02:07:36Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-21T01:10:36Z | 2026-06-21T01:33:17Z | 22m 41s |
| green | 2026-06-21T01:33:17Z | 2026-06-21T01:43:35Z | 10m 18s |
| review | 2026-06-21T01:43:35Z | 2026-06-21T01:52:18Z | 8m 43s |
| green | 2026-06-21T01:52:18Z | 2026-06-21T02:02:16Z | 9m 58s |
| review | 2026-06-21T02:02:16Z | 2026-06-21T02:07:36Z | 5m 20s |
| finish | 2026-06-21T02:07:36Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): the keystone wiring test calls `register_cast_staging_observer()` directly and fires the real `frontier_hook.notify_region_transition`, proving the observer stages cast through the live dispatch — but it does NOT trigger full FastAPI startup (which would require Postgres/daemon I/O). Dev MUST call `register_cast_staging_observer()` from a process-lifetime `@app.on_event("startup")` handler in `sidequest/server/app.py` (alongside the existing idempotent-registration block ~line 159), or the observer is never registered in production and no cast stages in a real game. Affects `sidequest/server/app.py` (add the startup call). *Found by TEA during test design.*
- **Question** (non-blocking): staging is NOT gated on `world_is_zoned` in these tests — entering any region with `binding.kind=="npc"` entities stages its cast (the spec's "right cast appears" half is framed independently of zoning; only the origin-stamp is the zoned half). If Dev intends to gate staging to zoned worlds, that's a behavior change from these tests — log a deviation and confirm against the spec. Affects `sidequest/game/region_cast_staging.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): `NpcPoolMember` requires a `drawn_from` source tag; the established authored value is `"world_authored"` (npc_pool.py). Tests assert on `name` only (not `drawn_from`) to avoid over-coupling, but Dev should stamp staged members `drawn_from="world_authored"` for forensic provenance. Affects `sidequest/game/region_cast_staging.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): TEA's blocking finding is RESOLVED — `register_cast_staging_observer()` is wired into `app.py` startup with a symmetric shutdown unregister; staged members carry `drawn_from="world_authored"` (TEA's provenance suggestion) and staging is intentionally not zoned-gated (TEA's open Question, resolved per spec). No remaining upstream gaps from this story. *Found by Dev during implementation.*
- **Gap** (non-blocking): the full suite carries 3 PRE-EXISTING failures unrelated to this story — `tests/server/test_app.py::test_create_app_uses_build_llm_client_by_default` (LLM-factory hermeticity baseline) and the two `tests/game/test_barsoom_cast_beat_live_content.py::test_barsoom_caster_sees_cast_spell_in_live_combat[...]` (barsoom magic content). VERIFIED pre-existing: all three fail identically on the base branch with every 157-3 change stashed. Reviewer/verify should not attribute these to this story. Affects nothing in 157-3's diff. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Reworked Round-Trip 1 — R1/R2/R3 all resolved. The origin-stamp is now wired through `mark_active_from_narration` → `websocket_session_handler.py:1264` (3 new wiring tests on the production path); the unknown-region skip logs a warning; the docstring overclaim is corrected. A second pre-existing cluster surfaced during the wider canary: `tests/server/dispatch/test_pregen_fail_loud_90_5.py` (3) + `test_pregen_combat_gate.py::test_seed_manual_generates_encounters_when_combat_enabled` + `test_sealed_letter_dispatch_integration.py::test_legacy_beat_selection_path_still_works` — VERIFIED pre-existing (fail identically on base with rework stashed); `seed_manual`/beat-selection are not touched by this story. *Found by Dev during rework.*

### Reviewer (code review)
- **Gap** (blocking): the walk-on origin-stamp (sub-part A) has no production caller — `mark_active(*, faction=)` is never invoked with a faction. The zoned-world activation path `mark_active_from_narration` (called from `websocket_session_handler.py:1264`) must resolve the current region's `controlled_by` and pass it. Affects `sidequest/server/dispatch/monster_manual_inject.py` (the `mark_active_from_narration` signature + call site) and the activating handler (needs the snapshot's region/faction in scope). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `stage_region_cast`'s region-None and cartography-None early returns emit no log/span — a narrator-authored misspelled region id silently stages nothing. Add a `logger.warning` on the unknown-region path. Affects `sidequest/game/region_cast_staging.py`. *Found by Reviewer during code review.*
- **Conflict** (non-blocking): the `region_cast_staging` docstrings claim staging "stages nothing rather than raising" on an unresolvable pack, but `load_genre_pack_cached` raises `GenreNotFoundError` on an unknown genre (loader.py:2783) — only the world/cartography-missing path returns None. Correct the docstring (or guard the genre resolution). Practically unreachable since `genre_slug` is server-set. Affects `sidequest/game/region_cast_staging.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, R5, re-review): `_origin_stamp_faction` returns None on the split-party (`len(active) > 1`) path with no distinct reason-code log — a walk-on left unstamped in a split-party turn is indistinguishable on the GM panel from an unzoned-world no-stamp. Only reachable when `perspective` is None (the call site passes a concrete acting PC). A future polish could add a `logger.debug(... reason=split_party ...)`. Not a blocker — behavior is correct. Affects `sidequest/server/dispatch/monster_manual_inject.py`. *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Two test files instead of the plan's single `tests/server/test_region_cast_staging.py`**
  - Spec source: plan Task 3 ("Test: `sidequest-server/tests/server/test_region_cast_staging.py`")
  - Spec text: one test file under `tests/server/`
  - Implementation: `tests/game/test_npc_origin_stamp.py` (sub-part A) + `tests/game/test_region_cast_staging.py` (sub-part B), both under `tests/game/` to mirror the modules under test (`game/monster_manual.py`, new `game/region_cast_staging.py`) and the sibling `tests/game/test_zone_eligibility.py`.
  - Rationale: independent RED signals — sub-part A fails with a precise `TypeError`, sub-part B with `ModuleNotFoundError`; splitting keeps the origin-stamp tests runnable even before the new module exists.
  - Severity: trivial
  - Forward impact: none (Dev implements the same two seams; file location is cosmetic).
- **Pack-resolution seam assumed to be `load_genre_pack_cached`**
  - Spec source: plan Task 3 + context-story-157-3.md ("resolve the pack/cartography from the snapshot it is handed")
  - Spec text: "resolve cartography from `snapshot.genre_slug`/`world_slug` via the pack loader cache"
  - Implementation: staging tests monkeypatch `load_genre_pack_cached` at BOTH `sidequest.genre.loader` and the used site `sidequest.game.region_cast_staging` (raising=False) and rely on the existing `zone_eligibility.cartography_for(snapshot, pack)` accessor (`pack.worlds[slug].cartography`) — verified to resolve a synthetic pack.
  - Rationale: the frontier observer signature carries no pack, so the pack must be resolved from the snapshot slugs; `load_genre_pack_cached` is the documented process-lifetime cache. If Dev resolves the pack a different way, patch one of the two targets so the synthetic pack is returned.
  - Severity: minor
  - Forward impact: Dev should resolve the pack via `load_genre_pack_cached(snapshot.genre_slug)` (or make the resolver patchable at the used site) so the behavioral/cross-fire tests hit the synthetic pack.
- **Registration entry-point pinned as `register_cast_staging_observer()`**
  - Spec source: plan Task 3 ("Register once at startup: `register_frontier_observer(stage_region_cast)`")
  - Spec text: register the observer once at startup
  - Implementation: tests require `region_cast_staging.register_cast_staging_observer()` — an idempotent wrapper that registers `stage_region_cast` once — rather than a bare inline `register_frontier_observer(...)` call.
  - Rationale: gives a refactor-stable, unit-testable wiring seam (mirrors how the look-ahead worker wraps its registration in `session_integration`); the idempotency test pins the uvicorn-`--reload` double-register guard.
  - Severity: minor
  - Forward impact: Dev exposes `register_cast_staging_observer()` and calls it from server app startup (see blocking Delivery Finding).
- **`cast_staged` span attribute key pinned as `npc_names`**
  - Spec source: spec § OTEL ("`zone_eligibility.cast_staged` — authored NPCs push-staged on region entry (count + names)")
  - Spec text: "count + names"
  - Implementation: the span-attribute test asserts `region` and an `npc_names` list attribute carrying the staged names (mirrors how the Seam-1 test pins `content_factions`/`active_factions` by key).
  - Rationale: a concrete forensic key the GM panel can depend on; chosen to match the plan's `zone_eligibility_cast_staged_span(region, npc_names)` signature.
  - Severity: minor
  - Forward impact: Dev emits the span with a `region` attr and an `npc_names` list attr.

### Dev (implementation)
- **Added a symmetric `@app.on_event("shutdown")` unregister — beyond the plan's "register once at startup"**
  - Spec source: plan Task 3 + TEA blocking Delivery Finding
  - Spec text: "Register once at startup: `register_frontier_observer(stage_region_cast)`"
  - Implementation: paired the startup registration with `_unwire_region_cast_staging` (shutdown) that calls `unregister_frontier_observer(stage_region_cast)`.
  - Rationale: `frontier_hook._OBSERVERS` is process-global. MEASURED that a lifespan-firing test (`with TestClient(create_app())`) leaves the observer registered after the context exits — which would break `tests/dungeon/test_session_lifecycle_wiring.py`'s exact `registered_observer_count() == 1`/`== 0` assertions when it shares an xdist worker. A symmetric shutdown teardown (every other app.py startup handler has one) ties the observer to the app lifespan and prevents the leak. Verified: registered inside lifespan, 0 after exit; full canary (3439 passed) shows the frontier wiring test green.
  - Severity: minor
  - Forward impact: none — production still registers for the whole serving lifetime; only adds clean teardown.
- **`cast_staged` span emitted inline via `Span.open`, not a `zone_eligibility_cast_staged_span()` helper**
  - Spec source: TEA Assessment item 3 / plan ("`zone_eligibility_cast_staged_span(region, npc_names)` emitter")
  - Spec text: a dedicated span-emitter helper
  - Implementation: emitted inline with `Span.open(SPAN_ZONE_ELIGIBILITY_CAST_STAGED, {"region":..., "npc_names":...})`.
  - Rationale: exactly mirrors the Seam-1 sibling `zone_eligibility.filtered`, which is emitted inline in `monster_manual_inject.py` (no helper). No test requires the helper; minimalist-discipline — the span fires with the pinned attrs either way.
  - Severity: trivial
  - Forward impact: none.
- **Staged NPC display name resolved from `entity.label` (not `binding.ref` or `authored_npcs`)**
  - Spec source: spec § Seam 2, plan Task 3 ("materialize/activate the bound NPC")
  - Spec text: stage the region's `binding.kind=="npc"` cartography entities
  - Implementation: the staged `NpcPoolMember.name` is the entity's `label` (the player-facing display name); `binding.ref` is the pointer, `label` is the name a player sees.
  - Rationale: the frontier observer has only the snapshot + cartography (no manual/authored_npcs), so it stages directly from the entity; `label` is the display name. Staging is intentionally NOT gated on `world_is_zoned` (resolving TEA's non-blocking Question) — the spec frames "the right cast appears" independently of zoning; only the origin-stamp is the zoned half.
  - Severity: minor
  - Forward impact: content authors must give region npc-bound entities a player-facing `label`; the `binding.ref` remains the pointer used by other seams.

#### Dev (rework — Round-Trip 1, review R1)
- **Origin-stamp faction resolved INSIDE `mark_active_from_narration` (single-faction-only), not at the call site**
  - Spec source: plan Task 3 ("Caller in inject passes the current region's `controlled_by`") + Reviewer R1
  - Spec text: the caller passes the region's `controlled_by`
  - Implementation: `mark_active_from_narration` gained `*, snapshot, pack, perspective` and resolves the faction via a private `_origin_stamp_faction` helper (`zone_eligibility.active_factions(perspective=...)`, stamping ONLY when exactly one faction resolves); the `websocket_session_handler` call site passes `snapshot`/`sd.genre_pack`/`_acting_for_render_trigger`.
  - Rationale: the plan's "caller passes controlled_by" is satisfied (the websocket handler is the caller), but the resolution lives in `mark_active_from_narration` so the Reviewer-requested wiring test can drive the production function (not a raw `mark_active` unit). Single-faction-only (vs. an arbitrary pick from a split-party union) avoids mis-stamping a walk-on in a multi-PC, multi-zone turn — `len(active) == 1` is the only deterministic, correct case.
  - Severity: minor
  - Forward impact: none — unzoned worlds / unresolvable regions / split-party (>1) stamp nothing (back-compatible); legacy 3-arg callers keep no-stamp behavior.

### Reviewer (audit)
- **TEA: two test files instead of one** → ✓ ACCEPTED by Reviewer: cosmetic; both files run and fail/pass independently.
- **TEA: pack-resolution via `load_genre_pack_cached`** → ✓ ACCEPTED by Reviewer: matches the implementation and the `cartography_for` accessor. Caveat noted as a finding — `load_genre_pack_cached` *raises* `GenreNotFoundError` (loader.py:2783), it does not return None, so the implementation's "never raises" claim is only true for the world/cartography-missing path.
- **TEA: registration seam `register_cast_staging_observer()`** → ✓ ACCEPTED by Reviewer: a clean, unit-testable wiring seam; idempotent.
- **TEA: `cast_staged` span attr key `npc_names`** → ✓ ACCEPTED by Reviewer: concrete forensic key, mirrors the Seam-1 `filtered` attribute-pinning.
- **Dev: symmetric `@app.on_event("shutdown")` unregister** → ✓ ACCEPTED by Reviewer: correct lifecycle hygiene and a genuine catch — without it the process-global observer leaks and breaks `test_session_lifecycle_wiring`'s exact-count assertions. Verified `unregister_frontier_observer` is exported.
- **Dev: inline `Span.open` not a helper** → ✓ ACCEPTED by Reviewer: matches the Seam-1 sibling exactly.
- **Dev: `entity.label` for the staged name + staging not zoned-gated** → ✓ ACCEPTED by Reviewer: reasonable; `label` is the player-facing name and the spec frames "right cast appears" independently of zoning.
- **UNDOCUMENTED — origin-stamp caller wiring omitted:** The plan (Task 3: "Caller in inject passes the current region's `controlled_by`") and the story context (Sub-part A: "Caller: `monster_manual_inject.py` passes the region's `controlled_by`") both scoped the production caller change into 157-3. The implementation added the `faction=` parameter to `mark_active` but did NOT update any caller — `mark_active_from_narration` (monster_manual_inject.py:677, the production activation path called from `websocket_session_handler.py:1264`) still calls `mark_active(name, current_location)` with no faction. Neither TEA nor Dev logged this omission. The origin-stamp (sub-part A) therefore never fires in production. Severity: **HIGH** (see Reviewer Assessment finding R1). → ✓ RESOLVED in rework Round-Trip 1: caller wired + production-path wiring test added.

#### Reviewer (re-review audit)
- **Dev (rework): origin-stamp faction resolved inside `mark_active_from_narration` (single-faction-only)** → ✓ ACCEPTED by Reviewer: satisfies the plan's "caller passes controlled_by" (the websocket handler is the caller); resolving inside the function enables the production-path wiring test; `len(active) == 1`-only is the correct deterministic rule (no arbitrary pick on a split-party union). Verified backward-compatible (43/43 existing inject tests pass).

## Notes

**Design Reference (ORCHESTRATOR repo, not server):**
- Spec: `docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md` (§ "Seam 2 — NPCs")
- Plan: `docs/superpowers/plans/2026-06-20-faction-zone-content-eligibility.md` (§ "Task 3" — RED tests verbatim)
- ADR: `docs/adr/152-faction-zone-scoped-content-eligibility.md`
- Full enriched context: `sprint/context/context-story-157-3.md`

**Path correction:** `frontier_hook` lives at `sidequest/dungeon/frontier_hook.py` (NOT `game/`).

**Seam 2 Scope:**
- NPC walk-on origin-stamp: tag authored NPCs with their eligibility faction/zone origin as they spawn
- Authored-cast staging on region entry: filter authored cast (cartography-homed NPCs) by region faction on world load
- Depends on Seam 1 (157-2): zone_eligibility core + factions tag + creature inject filter already merged

**Related Modules:**
- sidequest-server/sidequest/game/zone_eligibility.py (created in 157-2)
- sidequest-server/sidequest/telemetry/spans/zone_eligibility.py (created in 157-2)

## TEA Assessment

**Tests Required:** Yes
**Reason:** ENGINE story — two new behavioral seams (origin-stamp + cast staging) with OTEL.

**Test Files:**
- `sidequest-server/tests/game/test_npc_origin_stamp.py` — sub-part A: generated walk-on origin-stamp via `MonsterManual.mark_active(..., faction=)` (4 tests)
- `sidequest-server/tests/game/test_region_cast_staging.py` — sub-part B: authored-cast staging on region entry, `zone_eligibility.cast_staged` span, cross-fire concurrency guard, and frontier-dispatch wiring (8 tests)

**Tests Written:** 12 tests covering the story's two ACs + OTEL + wiring + concurrency.
**Status:** RED (failing — ready for Dev), verified directly:
- File 1 → `TypeError: MonsterManual.mark_active() got an unexpected keyword argument 'faction'` (all 4) — the feature is genuinely absent.
- File 2 → `ModuleNotFoundError: No module named 'sidequest.game.region_cast_staging'` (collection error) + `SPAN_ZONE_ELIGIBILITY_CAST_STAGED` undefined.
- Fixture builders (`Region`/`LocationEntity`/`CartographyConfig`/`GameSnapshot`/`NpcPoolMember`) independently verified to construct, and `zone_eligibility.cartography_for` resolves the synthetic pack — so RED is feature-absence, not malformed fixtures.

**What Dev must create (the contract these tests pin):**
1. `MonsterManual.mark_active(self, name, location, *, faction: str | None = None)` — origin-stamp `npc.factions = [faction]` only when `faction` is truthy AND `npc.factions` is empty, on the same matched entry that goes ACTIVE.
2. `sidequest/game/region_cast_staging.py` with `stage_region_cast(*, snapshot, pc_name, from_region, to_region) -> None` (the frontier observer) and `register_cast_staging_observer() -> None` (idempotent single registration). Staging: resolve pack from `snapshot.genre_slug` via `load_genre_pack_cached`, read `cartography.regions[to_region].entities` where `binding.kind == "npc"`, materialize each into `snapshot.npc_pool` as `NpcPoolMember(name=..., drawn_from="world_authored")`, idempotently; emit `zone_eligibility.cast_staged` (region + `npc_names`).
3. `SPAN_ZONE_ELIGIBILITY_CAST_STAGED = "zone_eligibility.cast_staged"` in `sidequest/telemetry/spans/zone_eligibility.py`, added to `FLAT_ONLY_SPANS`, plus a `zone_eligibility_cast_staged_span(region, npc_names)` emitter.
4. Wire `register_cast_staging_observer()` into `sidequest/server/app.py` startup (see blocking Delivery Finding).

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #6 Test quality — meaningful assertions | every test asserts a specific value (names/factions/span attrs), not bare truthiness | passing-by-construction (self-checked) |
| OTEL Observability Principle | `test_staging_emits_cast_staged_span`, `test_no_cast_staged_span_when_region_has_no_authored_cast`, `test_cast_staged_span_is_flat_only_registered` | failing (RED) |
| Every Test Suite Needs a Wiring Test | `test_real_region_transition_stages_cast_end_to_end` (real `notify_region_transition` dispatch), `test_register_cast_staging_observer_is_idempotent` | failing (RED) |
| No Source-Text Wiring Tests | wiring asserted via real frontier dispatch + registry membership + OTEL — zero source greps | satisfied |
| #2 Mutable default arguments | `mark_active(..., faction=None)` pinned (no mutable default); staging idempotency test guards against shared-state accumulation | failing (RED) |

**Rules checked:** 5 of the applicable lang-review rules / project principles have test coverage (most of python.md's 13 checks target error-handling/IO/async surfaces this pure-logic story doesn't touch).
**Self-check:** 0 vacuous assertions — no `assert True`, no bare-truthy `assert result`, no `let _`-style no-ops; every assertion pins a concrete value with a failure message.

**Handoff:** To Dev (Inigo) for implementation (GREEN).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/game/monster_manual.py` — `mark_active(self, name, location, *, faction=None)`: origin-stamp `npc.factions=[faction]` only when `faction` is truthy AND `factions` is empty (backward compatible; existing 2-positional callers unaffected).
- `sidequest-server/sidequest/telemetry/spans/zone_eligibility.py` — added `SPAN_ZONE_ELIGIBILITY_CAST_STAGED = "zone_eligibility.cast_staged"` and registered it in `FLAT_ONLY_SPANS` (persisted forensic event, like its `filtered` sibling).
- `sidequest-server/sidequest/game/region_cast_staging.py` *(new)* — `stage_region_cast` (frontier observer: resolves pack from snapshot slugs via `load_genre_pack_cached`, stages `binding.kind=="npc"` region entities into `snapshot.npc_pool` as `world_authored` members idempotently, emits `cast_staged`) + `register_cast_staging_observer` (idempotent).
- `sidequest-server/sidequest/server/app.py` — `@app.on_event("startup")` registers the observer (production wiring) + symmetric `@app.on_event("shutdown")` unregister (prevents process-global registry leak).

**Tests:** 13/13 passing (GREEN) — `tests/game/test_npc_origin_stamp.py` (4) + `tests/game/test_region_cast_staging.py` (9).

**Regression check:** Targeted canary of 3442 tests (`tests/game/` + `tests/server/dispatch/test_zone_eligibility_seam.py` + `tests/dungeon/test_session_lifecycle_wiring.py` + 2 lifespan-firing app tests in one `-n0` process) → 3439 passed, 3 failed. All 3 failures VERIFIED PRE-EXISTING (fail identically on base with all changes stashed): the `test_app` LLM-factory hermeticity baseline + 2 barsoom magic-content tests. The leak-risk `test_session_lifecycle_wiring` passed in the same process as a lifespan-firing app test — the shutdown teardown holds.

**Branch:** `feat/157-3-npc-walkon-origin-stamp` (pushed to origin; commit `ce2d2dbe`).

**Self-review:** Wired end-to-end (observer fires through the real `notify_region_transition` dispatch + registered at app startup); follows the Seam-1 sibling patterns (inline `Span.open`, `FLAT_ONLY_SPANS`); all ACs met; fail-soft on unresolvable pack/region (no crash on a pre-bind session) per No Silent Fallbacks (returns without staging rather than masking a real config error — the load validator in 157-7 is the loud gate).

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

_(Re-review — Round-Trip 1; 3 enabled subagents re-run on the rework diff. Round-1 results are preserved in the superseded assessment below.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 17/17 story GREEN; 43/43 backward-compat; lint+format PASS | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (R2/R3 confirmed RESOLVED; 1 new LOW split-party reason-code log; R4 pre-existing not worsened) | confirmed 1 (LOW, non-blocking), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (all 3 new-boundary concerns clean) | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via settings)
**Total findings:** R1/R2/R3 from Round 1 all VERIFIED FIXED; 1 new LOW (non-blocking observability nicety), 0 dismissed, 0 deferred

## Reviewer Assessment (Round 1 — REJECTED, superseded by the re-review below)

**Verdict (Round 1):** REJECTED

The authored-cast staging half (sub-part B) is well-built, fully wired, and clean. But the **walk-on origin-stamp half (sub-part A) is not wired into production** — the story ships a method nothing calls. That is a half-wired feature, which the project's CLAUDE.md rules explicitly forbid.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **R1 — Origin-stamp has no production caller.** `mark_active(*, faction=)` is implemented + unit-tested, but the only production caller, `mark_active_from_narration` (called from `websocket_session_handler.py:1264`), invokes `mark_active(name, current_location)` with NO faction. The walk-on origin-stamp never fires in a real game. The plan (Task 3) and story context both scoped the caller change into 157-3. Violates "Verify Wiring, Not Just Existence", "No Half-Wired Features", and "Every Test Suite Needs a Wiring Test". | `sidequest/server/dispatch/monster_manual_inject.py:677` (+ `mark_active_from_narration` signature) and `websocket_session_handler.py:1264` | Wire the zoned-world activation path to resolve the current region's `controlled_by` (via `zone_eligibility`) and pass it to `mark_active(..., faction=...)`. Add a wiring/integration test: a zoned world + a narration that activates a generated walk-on → assert the walk-on's `factions` is origin-stamped to the region's faction (fixture-driven + the production `mark_active_from_narration` path, not a direct `mark_active` unit call). |
| [MEDIUM] | **R2 — `region`-None silent skip with no signal.** [SILENT] When `to_region` is not a key in `cartography.regions` (e.g. a narrator-authored / misspelled region id from a `WorldStatePatch`, which is NOT validated by the load-time validator in 157-7), `stage_region_cast` returns with no log and no span. The operator cannot distinguish "region has no authored cast" from "region id doesn't match cartography." The OTEL Observability Principle wants subsystem decisions visible. | `sidequest/game/region_cast_staging.py:69` (`if region is None: return`) | Add a `logger.warning("zone_eligibility.cast_staged.skip reason=unknown_region world=%r to_region=%r", ...)` on the region-None path. |
| [LOW] | **R3 — `load_genre_pack_cached` raises; docstring overclaims fail-soft.** [DOC] The module docstring + `stage_region_cast` docstring say an "unresolvable pack/world/cartography stages nothing rather than raising," but `load_genre_pack_cached(snapshot.genre_slug)` raises `GenreNotFoundError` (loader.py:2783) on an unknown genre — only the world/cartography-missing path returns None. In production `genre_slug` is always a valid server-set slug (confirmed by [SEC]), so the raise is unreachable in practice, but the docstring is inaccurate and there is a latent hot-path crash if the precondition is ever violated. | `sidequest/game/region_cast_staging.py:1-32, 56-66` | Correct the docstrings to scope the fail-soft to the world/cartography-missing path; OR (defensive) wrap the genre resolution and log+return on `GenreNotFoundError`. The cartography-None path could also take a `logger.debug`. |
| [LOW] | **R4 — `mark_active` silent no-op on name mismatch (pre-existing, amplified).** [SILENT] If the fuzzy name match fails, `mark_active` returns with no signal — and now the `faction` stamp is silently dropped too. Pre-existing behavior; the new faction path raises the stakes (a missed stamp means the walk-on stays cross-zone eligible). | `sidequest/game/monster_manual.py:286-305` | Not blocking; consider returning a `bool` (matched?) so the caller (once R1 is wired) can log a miss. Address opportunistically during the R1 rework. |

### Observations (≥5)
- [HIGH][RULE] R1 origin-stamp wiring gap — `faction` param has zero non-test consumers. `grep -rn "mark_active(.*faction" sidequest/` → only the definition. Sub-part A is inert in production.
- [MEDIUM][SILENT] R2 region-None silent skip (no log/span) — confirmed by silent-failure-hunter (high confidence) and my own read of `region_cast_staging.py:67-70`.
- [LOW][DOC] R3 docstring vs `load_genre_pack_cached` raise — evidence: loader.py:2783 `raise GenreNotFoundError`; docstring at region_cast_staging.py says "rather than raising."
- [LOW][SILENT] R4 mark_active no-op (pre-existing) — monster_manual.py:286 fuzzy loop returns nothing on no-match.
- [VERIFIED] Sub-part B staging is fully wired — `register_cast_staging_observer()` (region_cast_staging.py) is called from `app.py:_wire_region_cast_staging` (startup) and the wiring test `test_real_region_transition_stages_cast_end_to_end` fires the REAL `frontier_hook.notify_region_transition`. Evidence: app.py:159-166 + region_cast_staging.py:101. Complies with "Every Test Suite Needs a Wiring Test" for sub-part B.
- [VERIFIED] Observer leak prevented — `app.py:_unwire_region_cast_staging` (shutdown) calls `unregister_frontier_observer(stage_region_cast)`; [preflight] confirmed both symbols exported; I independently measured 0 observers after lifespan exit.
- [VERIFIED][SEC] Security clean — `snapshot.genre_slug` is server-set from the Postgres sessions row (not player-controlled), `entity.label` is server-authored YAML, `to_region` is None-guarded, entity loop is bounded by authored content. No injection / traversal / DoS path. Evidence: security subagent's 4-concern analysis + GenreLoader.find() `is_dir()` guard.
- [VERIFIED] Idempotency correct — `existing` set computed once and updated in-loop dedups both intra-region duplicates and re-entry. Evidence: region_cast_staging.py:72-83; test `test_staging_is_idempotent_on_reentry`.

### Rule Compliance (python.md + CLAUDE.md/SOUL.md)
- **#1 Silent exception swallowing:** COMPLIANT — no try/except in the diff; observer raises propagate (frontier_hook is loud by design).
- **#2 Mutable default arguments:** COMPLIANT — `faction: str | None = None` (no mutable default); `staged: list[str] = []` is a local, not a default arg.
- **#3 Type annotation gaps:** COMPLIANT — all new public functions fully annotated (`stage_region_cast`, `register_cast_staging_observer`, `mark_active`).
- **#4 Logging coverage:** PARTIAL — the cast-staged path logs (region_cast_staging.py:88); the two skip paths (region-None, cartography-None) do NOT log → R2/R3.
- **#8 Unsafe deserialization:** COMPLIANT — loader uses `yaml.safe_load` ([SEC] confirmed lines 166/199/289/...); no pickle/eval/exec.
- **#11 Input validation:** COMPLIANT — `to_region` None-guarded; `genre_slug` server-set ([SEC]).
- **Verify Wiring, Not Just Existence / No Half-Wired Features:** VIOLATION for sub-part A (R1) — the `faction` param has no non-test consumer. COMPLIANT for sub-part B.
- **OTEL Observability Principle:** COMPLIANT for the staged path (`cast_staged` span + FLAT_ONLY registration); PARTIAL for the skip paths (R2).

### Devil's Advocate
Argue this code is broken. The most damning case is R1: a reviewer who only reads the tests sees 13 green and a clean `mark_active(..., faction=...)` and concludes the origin-stamp works. It does not. In a live game, the narrator introduces a generated walk-on ("a fishwife haggles at the Lilliput dock"); `mark_active_from_narration` flips her to ACTIVE — with `faction=None`, because nobody threaded the region's `controlled_by` through. Her `factions` stays empty. Three voyages later the same fishwife is eligible to resurface in Houyhnhnm-land — the exact cross-zone bleed epic-157 exists to kill. The unit tests pass because they call `mark_active(faction=...)` directly, a path no production code travels; this is the textbook "tests pass because the component works in isolation, but it isn't wired" failure the CLAUDE.md wiring rules were written to catch. Worse, the Dev assessment asserts "Wired end-to-end" — true only for sub-part B, which makes the gap easy to miss. Second, a confused content author: they author a region's NPC cast but typo the region id in a narrator-driven transition; `stage_region_cast` silently stages nothing (R2) with no warning, and the author has no signal short of a GM-panel span hunt — they'll conclude "staging is broken" when it's a content typo. Third, a stressed precondition: if `genre_slug` is ever malformed (a stub snapshot, an uninstalled pack mid-session), `load_genre_pack_cached` raises mid-`notify_region_transition`, which does not swallow — crashing the player's region move, despite a docstring promising it "stages nothing rather than raising" (R3). None of these are caught by the current suite. R1 is dispositive on its own: half the story does nothing.

**Dispatch tags present:** [EDGE] none confirmed (edge-hunter disabled; I assessed boundaries myself — `to_region` empty/unknown covered by R2). [SILENT] R2, R4. [TEST] none (test-analyzer disabled; tests verified adequate for what they cover, but miss the R1 wiring path — folded into R1). [DOC] R3. [TYPE] none (type-design disabled; annotations verified compliant). [SEC] clean (verified). [SIMPLE] none (simplifier disabled; code is minimal, no over-engineering seen). [RULE] R1 (Verify-Wiring / No-Half-Wired-Features).

**Handoff:** Back to TEA (Fezzik) for a failing wiring test on the origin-stamp production path, then Dev to wire the caller (R1) and address R2/R3 logging.

## Dev Assessment (Rework — Round-Trip 1)

**All Reviewer findings addressed:**
- **R1 [HIGH] — origin-stamp wiring (FIXED):** `mark_active_from_narration` now accepts `*, snapshot, pack, perspective`, resolves the acting PC's zoned region `controlled_by` via `_origin_stamp_faction` (`zone_eligibility.active_factions`, stamping only when exactly one faction resolves), and threads it to `mark_active(faction=...)`. The production call site `websocket_session_handler.py:1264` now passes `snapshot=snapshot, pack=sd.genre_pack, perspective=_acting_for_render_trigger`. Added 3 wiring tests that drive the production `mark_active_from_narration` path (TDD: written failing first, verified RED, then GREEN): zoned-world stamp, unzoned no-stamp, legacy 3-arg back-compat.
- **R2 [MED] — silent region skip (FIXED):** `stage_region_cast` logs `logger.warning(... reason=unknown_region ...)` on the unknown-region path and `logger.debug(... reason=no_cartography ...)` on the no-cartography path. Added `test_staging_warns_on_unknown_region`.
- **R3 [LOW] — docstring overclaim (FIXED):** corrected `stage_region_cast`'s docstring — `load_genre_pack_cached` raises `GenreNotFoundError` on an unknown genre (fail-loud per No Silent Fallbacks); only the world/cartography-missing path stages nothing. Did NOT add a swallow (genre_slug is server-set and always valid; masking it would violate No Silent Fallbacks).
- **R4 [LOW] — mark_active no-op:** left as-is (pre-existing, out of scope; the new faction path inherits the existing fuzzy-match-or-no-op contract). Noted for a future story.

**Files Changed (rework):**
- `sidequest/server/dispatch/monster_manual_inject.py` — `mark_active_from_narration` signature + `_origin_stamp_faction` helper.
- `sidequest/server/websocket_session_handler.py` — call site passes snapshot/pack/perspective.
- `sidequest/game/region_cast_staging.py` — R2 logging + R3 docstring.
- `tests/game/test_npc_origin_stamp.py` — 3 production-path wiring tests.
- `tests/game/test_region_cast_staging.py` — unknown-region warning test.

**Tests:** 17/17 story tests GREEN (13 + 4 rework). Lint + format clean. `test_monster_manual_inject.py` (existing `mark_active_from_narration` coverage) passes — signature change is backward compatible.

**Regression check:** Canary of ~478 tests across `tests/game/` + `tests/server/dispatch/` + the leak-risk `test_session_lifecycle_wiring`. 5 failures, ALL VERIFIED PRE-EXISTING (fail identically on base with the rework stashed): `test_pregen_fail_loud_90_5.py` (3), `test_pregen_combat_gate.py::test_seed_manual_generates_encounters_when_combat_enabled`, `test_sealed_letter_dispatch_integration.py::test_legacy_beat_selection_path_still_works` — `seed_manual`/beat-selection are untouched by this story.

**Branch:** `feat/157-3-npc-walkon-origin-stamp` (pushed; rework commit `4b59670f`).

**Handoff:** Back to Reviewer (Westley) for re-review.

## Reviewer Assessment

**Verdict:** APPROVED (re-review, Round-Trip 1)

The Round-1 blocker (R1) and both non-blocking findings (R2/R3) are verified fixed; the rework introduced no regressions and one minor non-blocking observability nicety.

**Round-1 findings — verification:**
- **R1 [HIGH] — FIXED & VERIFIED.** The origin-stamp now has a real production caller. `mark_active_from_narration(*, snapshot, pack, perspective)` resolves the acting PC's zoned region `controlled_by` via `_origin_stamp_faction` and threads it to `mark_active(faction=...)`; the production call site `websocket_session_handler.py:1264` passes `snapshot`/`sd.genre_pack`/`_acting_for_render_trigger`. The new wiring test `test_mark_active_from_narration_origin_stamps_walkon_in_zoned_world` drives the **production** function and is non-vacuous (verified RED — `TypeError` — on the pre-rework code). `_origin_stamp_faction`'s `len(active) == 1`-only rule is correct: it never makes an arbitrary pick on a split-party union. [preflight] confirms 43/43 existing `test_monster_manual_inject.py` pass — the keyword-only signature is backward compatible — including `test_websocket_session_handler_wires_monster_manual_inject` (the call-site glue is itself covered).
- **R2 [MED] — FIXED.** `stage_region_cast` now emits `logger.warning(... reason=unknown_region ...)` on the region-None path and `logger.debug(... reason=no_cartography ...)` on the cartography-None path; `test_staging_warns_on_unknown_region` pins it. [SILENT] confirmed resolved.
- **R3 [LOW] — FIXED.** The docstring no longer overclaims fail-soft — it correctly states `load_genre_pack_cached` raises `GenreNotFoundError` on an unknown genre (fail-loud per No Silent Fallbacks). Dev correctly chose NOT to add a swallow (genre_slug is server-set/valid; a swallow would mask a real misconfiguration). [DOC] confirmed resolved.

**New finding (non-blocking):**
- [LOW][SILENT] **R5 — split-party origin-stamp suppression has no reason-code log.** `_origin_stamp_faction` returns None when `len(active) > 1` (a split party with `perspective=None`, both PCs in different zoned regions) with no distinct log — the `monster_manual.npc_activated` line shows `faction=None` but not *why*. Confidence medium; severity LOW: the behavior is correct (deterministic no-stamp is the right call), the case is only reachable when `perspective` is None (the call site passes a concrete acting PC, so it is ≤1 in normal play), and the activation is already logged. Recorded as a non-blocking Delivery Finding for a future polish — not a blocker. `sidequest/server/dispatch/monster_manual_inject.py` (`_origin_stamp_faction`).

**Data flow traced:** player turn → narrator narration → `mark_active_from_narration(snapshot, pack, perspective=acting PC)` → `_origin_stamp_faction` resolves the acting PC's own region `controlled_by` (server-authored YAML, never player input — [SEC] clean) → `mark_active(faction=...)` stamps only an empty `factions` → feeds the Seam-1 zone filter next inject. Safe: the stamp is internal engine state carrying only the PC's own region faction; no cross-zone leak.
**Pattern observed:** the resolution helper mirrors `zone_eligibility`'s permissive, server-owned-input design; the wiring test mirrors the sibling Seam-1 fixture-driven pattern — `region_cast_staging.py` + `monster_manual_inject.py:705`.
**Error handling:** unresolvable perspective/region → `∅` → no stamp (safe); unknown genre → `GenreNotFoundError` (fail-loud, server-set slug so unreachable); unknown region in staging → warning + skip.

**Dispatch tags:** [EDGE] none (disabled; boundaries — split-party >1, unzoned, unresolvable region — assessed and handled). [SILENT] R2 fixed, R5 new LOW. [TEST] none (disabled; wiring test verified non-vacuous + 43/43 backward-compat). [DOC] R3 fixed. [TYPE] none (disabled; new annotations on `mark_active_from_narration`/`_origin_stamp_faction` verified correct). [SEC] clean (re-verified — perspective is server-resolved, no new untrusted boundary). [SIMPLE] none (disabled; `_origin_stamp_faction` is minimal). [RULE] R1 (Verify-Wiring) now COMPLIANT — `faction` has a production caller with a wiring test.

**Rule Compliance (delta):** "Verify Wiring, Not Just Existence" / "No Half-Wired Features" — now COMPLIANT (R1 wired + tested). "#4 Logging coverage" — improved (R2 skip paths now log); the one remaining gap (R5 split-party reason code) is LOW/non-blocking. All other rules remain compliant as in Round 1.

**Handoff:** To SM (Vizzini) for finish-story.