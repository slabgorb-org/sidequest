---
story_id: "158-12"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-12: Remove the LLM from dungeon curate — deterministic materialization, narrator owns creature prose

## Story Details
- **ID:** 158-12
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T11:12:08Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T09:43:08Z | 2026-06-23T09:45:25Z | 2m 17s |
| red | 2026-06-23T09:45:25Z | 2026-06-23T10:02:33Z | 17m 8s |
| green | 2026-06-23T10:02:33Z | 2026-06-23T10:45:57Z | 43m 24s |
| review | 2026-06-23T10:45:57Z | 2026-06-23T10:58:23Z | 12m 26s |
| green | 2026-06-23T10:58:23Z | 2026-06-23T11:03:55Z | 5m 32s |
| review | 2026-06-23T11:03:55Z | 2026-06-23T11:12:08Z | 8m 13s |
| finish | 2026-06-23T11:12:08Z | - | - |

## Sm Assessment

**Story:** Deletion-led refactor (3pt, server). Remove the Haiku LLM from the dungeon
materializer's Stage-3 curate pass; promote the already-shipping deterministic path
(`assemble_region → _creatures_from_manifest → _append_authored_creatures`) to the
**only** path; retire the Amendment-A retry/deadline/degrade ladder + its two curate
failure spans. The narrator already renders seated creatures — **no narrator code is
needed.**

**Design authority (locked):** ADR-106 **Amendment C** (2026-06-23), committed to
orchestrator `main` at `docs/adr/106-runtime-procedural-jaquaysed-megadungeon.md`. The
amendment matches this story's ACs 1:1. Implement exactly what is written — no
improvisation past the amendment. Full technical approach + the 7 ACs are in
`sprint/context/context-story-158-12.md` (pre-authored, authoritative — do not regenerate).

**RED phase targets (TEA — verify by OTEL spans + behavior, NOT source-text grep, per
server CLAUDE.md § No Source-Text Wiring Tests):**
1. **Seed-determinism** (AC 2): materialize one expansion band twice from one
   `campaign_seed`; assert committed `region_population` mutations (creatures + `big_bad`,
   incl. HP + threat) are byte-identical.
2. **Clean curate span** (AC 3): driving a real materialize emits one
   `dungeon.materialize.curate` span per region with `curated=true`, and **zero**
   `dungeon.curate.parse_failed` / `dungeon.curate.degraded` spans are reachable.
3. **Authored-binding survival** (AC 4): a region with an authored
   `encounter_creatures` binding (`entrance → gnaw_swarm`) still surfaces that creature
   via `_append_authored_creatures` through the real materialize → commit →
   `region_population` path.
4. Keep the existing wiring test green (AC 6):
   `tests/dungeon/test_materializer_wiring.py`.

**Test-isolation gotchas (carry into RED/GREEN):**
- A `materialize()` test using a real `genre_slug` + synthetic `world_slug` writes rooms
  into the REAL content pack via `_resolve_world_dir` (gitignored → git stays clean), then
  poisons a later same-session `load_genre_pack` with `GenreLoadError`. **Monkeypatch
  `_resolve_world_dir` to tmp** (prefer a conftest fixture).
- Full parallel `tests/server/` deadlocks ~18 OTEL span-count tests (pre-existing). Run
  the touched span/materialize files serially with `-n0`.
- AC 3 says coordinate the two removed failure spans with any telemetry **span-registry
  count test** — expect a count assertion to need updating in
  `sidequest/telemetry/spans/dungeon_materialize.py`'s registry.

**Scope guard:** AC 7 (sync collapse — `_stage_curate` → sync, ~3 `await materialize`
sites) is recommended + in-scope, but may split to a fast-follow if the ripple is larger
than scoped. **AC 1–6 (the LLM removal) ship regardless.** Out of scope: lookahead-race
a/b fix, cookbook affinity re-tuning, the Map UI gap, any narrator changes.

**Branch:** `feat/158-12-deterministic-dungeon-curate` (sidequest-server, off `develop`).
No Jira (project's jira field is null). Verdict: **routing to TEA for RED.**

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): the two curate-failure spans are *routed*, not flat-only.
  `SPAN_DUNGEON_CURATE_PARSE_FAILED` / `SPAN_DUNGEON_CURATE_DEGRADED` are registered in
  `SPAN_ROUTES` at `sidequest/telemetry/spans/dungeon_materialize.py:162` and `:178` (not
  in `FLAT_ONLY_SPANS`). Dev MUST delete the constant **and** its `SPAN_ROUTES[...] =
  SpanRoute(...)` registration together: leaving the route raises `NameError` at import;
  leaving the constant breaks `tests/telemetry/test_routing_completeness.py::test_every_span_is_routed_or_explicitly_flat`
  (it enumerates every `SPAN_*` constant and fails on a route-less one). This is the AC3
  "coordinate with any telemetry span-registry test" point — confirmed exact test + that
  the spans are routed. *Found by TEA during test design.*
- **Gap** (non-blocking): `tests/dungeon/test_153_26_curate_authored_content.py` tests the
  Amendment-A retry/deadline/degrade ladder this story RETIRES (deadline degrade, per-region
  budget, `MAX_BAND_DEADLINE_S` clamp, dangling/malformed authored-binding on the *degrade*
  path). Most of it goes obsolete once the LLM + degrade ladder are removed — Dev must
  delete/rewrite that suite in GREEN, keeping only the authored-binding-survival intent
  (now exercised on the deterministic MAIN path by 158-12 AC4). *Found by TEA during test design.*
- **Improvement** (non-blocking): `dungeon.curate.authored_bind_failed` (`:197`) and
  `monster_manual.room_bound` are NOT removed — `_append_authored_creatures` moves to the
  main path and keeps emitting both (loud-but-graceful broken binding; authored bind
  success). Only `parse_failed` + `degraded` retire. Don't over-delete. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): AC7 sync-collapse fast-follow — `_stage_curate` is now sync, but `materialize` and the look-ahead worker stay `async def` (no internal `await`) to avoid rippling ~50 `await materialize(...)` call sites. Affects `sidequest/dungeon/materializer.py`, `lookahead_worker.py`, `session_integration.py` (a separate story collapses the coordinator + worker to sync per Amendment C). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the look-ahead breadth>1 test lost its concurrency-probe assertion (`assert probe["max"] == 1`) — it could only observe interleaving via a suspending curate LLM call, which no longer exists; the serial-ordering teeth (`lookahead == [2,3,4]`, no expansion_id collision) are intact. Affects `tests/dungeon/test_lookahead_worker.py` (a deterministic concurrency probe could be added if the worker ever runs expansions concurrently). *Found by Dev during implementation.*
- **Question** (non-blocking): 2 pre-existing pyright `reportArgumentType` errors (`DungeonStore` vs `DungeonRepository` protocol) at the `materialize(...)`/`register_lookahead_worker(...)` call sites in `lookahead_worker.py:377` / `session_integration.py:222` — NOT introduced by this change (the removed `claude_client` param is unrelated); pre-existing duck-typing noise. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): an unexpected exception in `_stage_curate` (e.g. from `pack.effective_bestiary()`) exits the curate span untagged. Affects `sidequest/dungeon/materializer.py:1139-1201` (add an outer `except Exception` that tags `curated=false`+`reason` then re-raises). *Found by Reviewer during code review.*
- **Improvement** (blocking): stale "degrade"/"Amendment A" wording on the deterministic main path. Affects `sidequest/dungeon/materializer.py` docstring `:964-987` + ERROR logs `:1004-1011`,`:1031-1037` (reword to "main path", drop "degrade"/"Amendment A"). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `"assemble: {exc}"` curate-span reason prefix covers theme/look/assemble failures. Affects `sidequest/dungeon/materializer.py:1192` (broaden the prefix). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC3 verified at expansion scope, not "per region"**
  - Spec source: context-story-158-12.md, AC-3
  - Spec text: "emits one `dungeon.materialize.curate` span per region with `curated=true`"
  - Implementation: test asserts ≥1 `dungeon.materialize.curate` span and that EVERY such span is `curated=true` (plus zero `parse_failed`/`degraded`). The coordinator opens ONE curate span per expansion band (covering all regions); Amendment C does not instruct splitting it per-region.
  - Rationale: asserting "exactly one span per region" would be brittle and contradict the actual one-span-per-band architecture; "all curate spans clean, no failure spans" is the behavior the AC is protecting.
  - Severity: minor
  - Forward impact: if Dev chooses to emit a per-region curate span, the test still passes (it checks all such spans are clean).
- **AC2 verified as committed-payload byte-identity, not docstring text**
  - Spec source: context-story-158-12.md, AC-2
  - Spec text: "the `RegionCuration` docstring note that curation 'deliberately breaks byte-reproducibility' (`:514`) is reversed in code and comment"
  - Implementation: the determinism test asserts two same-seed runs produce byte-identical committed `region_population` payloads; it does NOT assert on the docstring/comment text.
  - Rationale: asserting on source comment text is a forbidden source-text test (server CLAUDE.md). The behavior the reversed docstring claims (seed-reproducible) IS tested; the comment edit is a Reviewer/lint concern.
  - Severity: minor
  - Forward impact: Reviewer should confirm the `:514` comment was reversed; tests do not gate it.
- **AC7 (sync collapse) deliberately not asserted**
  - Spec source: context-story-158-12.md, AC-7
  - Spec text: "`_stage_curate` becomes synchronous (no `await`)… this AC may be split to a fast-follow"
  - Implementation: tests tolerate sync OR async `materialize` via `_run_materialize` (awaits iff awaitable); no test asserts `_stage_curate`/`materialize` are synchronous.
  - Rationale: AC7 is explicitly separable; a blocking sync-assertion would wrongly fail the story if Dev defers the ripple. AC 1–6 ship regardless.
  - Severity: minor
  - Forward impact: if AC7 is split out, no 158-12 test needs changing.

### Dev (implementation)
- **AC7 sync collapse deferred to a fast-follow (only `_stage_curate` made sync)**
  - Spec source: context-story-158-12.md, AC-7
  - Spec text: "`_stage_curate` becomes synchronous (no `await`). The `materialize` coordinator and the lookahead worker collapse to synchronous calls; the ~3 `await materialize(...)` sites are updated. If Dev finds the ripple larger than scoped, this AC may be split to a fast-follow."
  - Implementation: `_stage_curate` is now sync. `materialize` and the look-ahead worker stay `async def` (calling `_stage_curate` without `await`), so the ~50 `await materialize(...)` call sites across the test suite + 2 production sites are unchanged.
  - Rationale: the ripple is far larger than "~3 sites" (47 `await materialize` in test_materializer.py alone). The spec explicitly permits splitting AC7. RUF029 (async-without-await) is not in the ruff select set, so an awaitless `async def materialize` is lint-clean. AC 1–6 ship intact.
  - Severity: minor
  - Forward impact: a fast-follow story collapses `materialize` + the worker to sync and updates the `await` sites. Module/function docstrings already note this.
- **Deleted three obsolete curate test suites; ported the live invariant**
  - Spec source: context-story-158-12.md, Technical Approach item 5 ("remove the curate-LLM fake injection")
  - Spec text: "tests/dungeon/ — remove the curate-LLM fake (ToolingLlmClient-shaped) injection; … keep the wiring test (AC 6)."
  - Implementation: deleted `test_153_26_curate_authored_content.py` (Amendment-A retry/deadline/degrade ladder), `test_92_2_scratch_curate_local.py` (SCRATCH/Ollama curate path), and `test_61_9_dungeon_purpose_wiring.py` (asserted `build_llm_client(purpose="tool")` is called — now never called). The still-live broken-authored-binding loud-but-graceful invariant (Reviewer-153-26 HIGH) was PORTED to `test_158_12` on the deterministic main path (dangling-id + malformed-YAML cases).
  - Rationale: these suites test removed mechanisms; deleting without porting would orphan the live "a homebrew binding typo must not crash the connect" invariant, so it moved to the surviving suite.
  - Severity: minor
  - Forward impact: none — coverage preserved on the new path.

### Reviewer (audit)
- **TEA: AC3 verified at expansion scope** → ✓ ACCEPTED: one curate span per band is the actual architecture; "all curate spans clean + zero failure spans" is the right behavioral assertion. Amendment C did not mandate per-region spans.
- **TEA: AC2 byte-identity not docstring text** → ✓ ACCEPTED: source-comment assertions are forbidden (server CLAUDE.md); the determinism *behavior* is what matters and is tested. (Reviewer confirmed the `:514`/`RegionCuration` comment reversal landed in code.)
- **TEA: AC7 not asserted** → ✓ ACCEPTED: AC7 is explicitly separable; `_run_materialize` tolerating sync/async is the correct hedge.
- **Dev: AC7 sync collapse deferred (only `_stage_curate` sync)** → ✓ ACCEPTED: the ripple (47 `await materialize` in test_materializer alone) genuinely exceeds the "~3 sites" estimate; the spec permits splitting; awaitless `async def` is lint-clean (RUF029 not selected) and documented. AC 1–6 ship intact.
- **Dev: deleted three obsolete curate suites; ported the live invariant** → ✓ ACCEPTED: 153-26 (degrade ladder), 92-2 (SCRATCH curate), 61-9 (`build_llm_client(purpose="tool")`) tested removed mechanisms; the live broken-binding loud-but-graceful invariant was correctly ported to test_158_12 on the main path (verified green).
- **UNDOCUMENTED (Reviewer)** — none. The stale "degrade" wording + untagged-span are code-quality findings (in the severity table), not spec deviations.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Deletion-led refactor that fixes an intermittent correctness defect (non-deterministic region materialization). Determinism + clean-span + authored-survival are behavioral guarantees that need tests.

**Test File:**
- `sidequest-server/tests/dungeon/test_158_12_deterministic_curate.py` — 6 tests covering AC1–AC5 (AC6/AC7 covered transitively; see deviations).

**Tests Written:** 6 tests covering 5 ACs (AC6 via the no-LLM materialize→Pg→region_population wiring tests; AC7 intentionally not gated).
**Status:** RED — verified `5 failed, 1 passed` (`uv run pytest -n0 -v tests/dungeon/test_158_12_deterministic_curate.py`).

Each RED failure is for the RIGHT contract reason (not a broken test file — confirmed by testing-runner):
- `test_stage_curate_signature_drops_claude_client` → `AssertionError: _stage_curate still accepts 'claude_client'` (AC1 reflection tripwire).
- `test_materialize_runs_with_no_llm_client` → `TypeError: materialize() missing … 'claude_client'` (AC1 behavior).
- `test_materialize_is_seed_deterministic` → `TypeError: … 'claude_client'` (AC2 — real byte-identity teeth post-fix).
- `test_curate_span_is_clean_no_failure_spans` → `TypeError: … 'claude_client'` (AC3).
- `test_authored_binding_survives_deterministic_materialize` → `TypeError: … 'claude_client'` (AC4).
- `test_curation_error_carveout_i_retained` → **PASS** (AC5 GREEN regression guard — `_creatures_from_manifest` still raises `CurationError` on a missing-`cr` row and an unknown `cr_band` big_bad).

**Why RED-via-"claude_client required" is the honest contract signal:** on develop the per-expansion Haiku call is *mandatory* (`materialize` requires the client; `_stage_curate` rejects `None`). Every behavior Amendment C promises — determinism, clean curate span, authored survival on the main path — is unreachable until the LLM is removed. Post-fix each test carries independent behavioral teeth (byte-identity, span attrs, roster contents, loud carve-out), so the suite is not satisfied by the signature change alone.

### Rule Coverage

| Rule (server CLAUDE.md / lang-review python.md) | Test(s) | Status |
|---|---|---|
| No Silent Fallbacks / #1 silent-exceptions (loud failure retained) | `test_curation_error_carveout_i_retained` | passing (guard) |
| No Source-Text Wiring Tests → OTEL span assertions | `test_curate_span_is_clean_no_failure_spans` | failing (RED) |
| No Source-Text Wiring Tests → sanctioned reflection tripwire | `test_stage_curate_signature_drops_claude_client` | failing (RED) |
| Every Test Suite Needs a Wiring Test (real materialize→Pg→region_population) | `test_materialize_runs_with_no_llm_client`, `test_authored_binding_survives_deterministic_materialize` | failing (RED) |
| #9 async-pitfalls (await only awaitables; AC7 sync tolerance) | `_run_materialize` helper (all materialize-driven tests) | failing (RED) |
| #6 test-quality (meaningful assertions, no vacuous) | self-check across all 6 tests | n/a (self-check) |

**Rules checked:** 6 of the applicable lang-review/CLAUDE.md rules have test coverage or self-check. The remaining lang-review checks (#2 mutable-defaults, #5 path-handling, #7 resource-leaks, #8 unsafe-deser, #10–13) target production deletion code and are the Dev/Reviewer GREEN-phase concern.
**Self-check:** 0 vacuous tests found (every test asserts a specific value: signature params, JSON byte-identity, span `curated`/absence, roster membership, `pytest.raises(CurationError)`).

**Test-isolation notes carried into the suite:**
- `_resolve_world_dir` is monkeypatched to tmp in the authored-binding test (else the commit's `rooms/<id>.yaml` emit pollutes the REAL caverns_and_claudes pack and poisons sibling `load_genre_pack` tests).
- Run the touched files with `-n0` (full parallel `tests/server/` deadlocks ~18 OTEL span-count tests, pre-existing).

**Handoff:** To Dev (Hephaestus) for GREEN — delete the LLM from `_stage_curate` per Amendment C; the 5 RED tests flip GREEN, the carve-out guard stays GREEN. Mind the two Delivery Findings (routed-span coordinated removal; retire the 153-26 ladder suite).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (production — `sidequest-server`):**
- `sidequest/dungeon/materializer.py` — `_stage_curate` is sync + deterministic (`assemble_region → _creatures_from_manifest → _append_authored_creatures` per region); dropped `claude_client` from `_stage_curate` + `materialize`; deleted `_build_curation_prompt`, `_parse_curation_verdict`, `_classify_parse_failure`, `_degrade_region`, the `asyncio.timeout` retry ladder, and `CURATE_DEADLINE_S`/`MAX_BAND_DEADLINE_S`; `RegionCuration` is now seed-reproducible (`raw_seed_reproducible=True`, `uncurated_regions` always empty); `CurationError` retained for carve-out (i); docstrings reversed.
- `sidequest/dungeon/session_integration.py` — removed the curate-only `build_llm_client(purpose="tool")` + its import + the `claude_client=` threading to `materialize` / `register_lookahead_worker`.
- `sidequest/dungeon/lookahead_worker.py` — dropped `claude_client` from the worker handle + `register_lookahead_worker` + the `materialize(...)` call.
- `sidequest/telemetry/spans/dungeon_materialize.py` — retired `dungeon.curate.parse_failed` / `dungeon.curate.degraded` (constants + `SPAN_ROUTES` registrations + helper fns + `__all__`); kept `dungeon.curate.authored_bind_failed` (now main-path).

**Files Changed (tests):**
- `tests/dungeon/test_158_12_deterministic_curate.py` — added two main-path broken-authored-binding loud-but-graceful tests (ported from 153-26) + `logging` import. **8 tests, all GREEN.**
- `tests/dungeon/test_materializer.py` — deleted the two LLM-curate test classes (`TestStageCurate`, `TestStageCurateRobustness`) + all curate-LLM fakes; stripped `claude_client=` from surviving `materialize` calls; fixed the span-ordering test's `_stage_curate` stub to sync; fixed the span-registration test.
- Deleted: `test_153_26_curate_authored_content.py`, `test_92_2_scratch_curate_local.py`, `test_61_9_dungeon_purpose_wiring.py` (obsolete — see Design Deviations).
- 8 importer test files + `tests/integration/conftest.py` — stripped `claude_client=` kwargs, `build_llm_client` monkeypatches, deleted-fake imports, and the obsolete `_stub_dungeon_curate_client` autouse fixture.

**AC status:** AC1 ✅ (no LLM/`claude_client` in curate path; `build_llm_client` feeder gone) · AC2 ✅ (same seed ⇒ byte-identical committed `region_population`) · AC3 ✅ (curate span `curated=true`, zero `parse_failed`/`degraded`; `test_routing_completeness` green) · AC4 ✅ (authored `gnaw_swarm` survives on the main path + `monster_manual.room_bound`) · AC5 ✅ (`CurationError` carve-out (i) retained) · AC6 ✅ (`test_materializer_wiring.py` + region_population wiring green) · AC7 ⏸ deferred to fast-follow (see Design Deviations).

**Tests:**
- `tests/dungeon/` (full, `-n0`): **477 passed, 0 failed.**
- `tests/telemetry/` (span consumers): **420 passed.**
- `tests/dungeon/test_158_12_deterministic_curate.py`: **8 passed.**
- `tests/integration/` dungeon-touching: 13 passed, collection clean (538).
- ruff check + format (touched files): clean. Pyright: 2 pre-existing protocol-typing errors, not introduced.
- The earlier full-suite 3× `dungeon.persist.*` span failures were pre-existing order-dependent OTEL-provider bleed (pass in isolation; the full `-n0` dungeon run is now green because the deleted curate tests no longer install/tear down a provider mid-suite).

**Branch:** `feat/158-12-deterministic-dungeon-curate` (sidequest-server, pushed).

**Handoff:** To Reviewer (Hermes) for review. Note for Reviewer: confirm the `RegionCuration` byte-reproducibility comment reversal landed; AC7's awaitless `async def materialize` is intentional (RUF029 not selected) and deferred per the spec's separability clause.

### Dev Rework (round 1 — addressing Reviewer findings)

All three Reviewer findings fixed (commit `bf9bad3b`):
- **[MEDIUM] untagged curate span** → added an outer `except Exception as exc:` in `_stage_curate` (`materializer.py`) that sets `curated=False` + `reason=f"unexpected: {exc}"` before re-raising — mirrors the typed handlers so the GM-panel lie-detector never goes dark on an error path. **Added regression test** `test_unexpected_exception_tags_curate_span_before_propagating` (monkeypatches the per-region body to raise `RuntimeError`, drives real `materialize`, asserts the curate span is `curated=false` and the exception still propagates loud).
- **[LOW] stale "degrade"/"Amendment A" wording** → reworded `_append_authored_creatures` docstring + both authored-bind ERROR logs (`:1004`, `:1031`), the `_creatures_from_manifest` docstring, and the carve-out (i) `CurationError` messages — all now reflect the deterministic **main path** (no "degrade", no "Amendment A").
- **[LOW] broad reason prefix** → `"assemble: {exc}"` → `"region-build: {exc}"` (covers theme-missing / look-resolution / assemble).

**Tests after rework:** `tests/dungeon/test_158_12_deterministic_curate.py` **9 passed**; full `tests/dungeon/` + `tests/telemetry/` **898 passed**; ruff clean. **Handoff:** back to Reviewer (Hermes) for re-review.

## Round-1 Subagent Results (superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (lint clean; 897 passed dungeon+telemetry; 8/8 contract) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 1 MEDIUM + 3 LOW (+7 verified-safe) | confirmed 3, dismissed 1, deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (assessed manually — see [SILENT] below) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (assessed manually — see [TEST] below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (assessed manually — see [DOC] below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed manually — see [TYPE] below) |
| 7 | reviewer-security | Yes | findings | 2 LOW | confirmed 1, dismissed 1, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed manually — see [SIMPLE] below) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (assessed manually — see [RULE] below) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents`, assessed manually)
**Total findings:** 4 confirmed (1 MEDIUM, 3 LOW), 2 dismissed (with rationale), 0 deferred

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md`)

- **#1 silent-exceptions** — `_stage_curate`'s `except (ValueError, CurationError)` both re-raise (no swallow). `_append_authored_creatures`'s `except RoomCreatureBindingError` logs ERROR + emits a span + returns (loud-but-graceful, documented) — not silent. **One gap:** an *unexpected* exception (outside those three types) escapes `_stage_curate` with the span untagged — see MEDIUM finding. Otherwise compliant.
- **#3 type-annotations** — `_stage_curate` params + return (`RegionCuration`) annotated; `materialize` annotated. Compliant.
- **#4 logging** — degrade ERROR logs removed with the degrade ladder; the authored-bind-failure ERROR logs retained. **Wording stale** (say "degrade"/"Amendment A" on the main path) — see LOW finding. Levels correct (ERROR for the caught authoring error).
- **#6 test-quality** — the 8 `test_158_12` tests assert specific values (byte-identity, span `curated`/absence, roster membership, `pytest.raises`); no vacuous assertions. `[TEST]` (subagent disabled, assessed manually): GREEN, and the deleted suites tested removed mechanisms; the live broken-binding invariant was ported. Compliant.
- **#9 async-pitfalls** — `_stage_curate` is sync; `materialize` calls it without `await` (correct — no un-awaited coroutine). `materialize` stays `async def` awaitless (AC7-deferred, documented; RUF029 not selected). No missing-await bug. Compliant.
- **#10 import-hygiene** — unused imports removed (ruff clean); no star-import regressions. Compliant.

### Observations

- `[VERIFIED]` CurationError carve-out (i) is loud + span-tagged — `materializer.py:1181` raises inside the loop `try`, caught at `:1194` which sets `curated=False`+`reason` before re-raising; transaction aborts, no corrupt manifest shipped. Complies with No-Silent-Fallbacks.
- `[VERIFIED]` sync `_stage_curate` called without `await` returns a real `RegionCuration` (`materializer.py:1964`); no coroutine escapes; `materialize` async-for-compat is documented.
- `[VERIFIED]` `[EDGE]` removed-symbol cleanup is complete — `SPAN_DUNGEON_CURATE_{PARSE_FAILED,DEGRADED}`, their helpers, `SPAN_ROUTES` registrations, `__all__`, `CURATE_DEADLINE_S`/`MAX_BAND_DEADLINE_S`, `claude_client`/`build_llm_client` gone from `sidequest/dungeon/`; `test_routing_completeness` green; only unrelated `world_materialization.parse_failed`/`history.parse_failed` remain (different spans).
- `[MEDIUM]` `[EDGE]` `[SILENT]` an unexpected exception from `_append_authored_creatures` / `pack.effective_bestiary()` (`materializer.py:1020`, outside the inner `try`) escapes `_stage_curate` with the curate span **untagged** (`span.set_attribute("curated", …)` at `:1208` is past the try). The ValueError/CurationError handlers tag-before-raise; an unexpected exception should too (OTEL lie-detector consistency). Low production reachability (real packs well-behaved), cheap one-line fix.
- `[LOW]` `[SEC]` `[DOC]` `[EDGE]` stale "degrade"/"Amendment A" wording in `_append_authored_creatures` — docstring (`:964-987`) + **two** ERROR logs (`:1004-1011`, `:1031-1037`). The function is now the deterministic **main path**, not a degrade fallback; a broken authored binding on the happy path logs "dungeon curate degrade … (ADR-106 Amendment A …)", misleading operators on a telemetry-honesty surface. Flagged independently by security + edge.
- `[LOW]` `[EDGE]` the `span.set_attribute("reason", f"assemble: {exc}")` prefix (`:1192`) labels theme-missing + look-resolution + assemble failures all as "assemble:" — GM-panel legibility nit.
- `[LOW]` `[EDGE]` empty `expansion.new_nodes` yields an empty `RegionCuration` with `curated=True` — **dismissed**: the design stage guarantees ≥1 node; not reachable in production and not introduced by this change.
- `[LOW]` `[SEC]` path-join without traversal check (`room_creature_binding.py:60`) — **dismissed**: pre-existing (not in this diff); `world_slug`/`room_id` are server-side game-state/pack config, never player WebSocket input.
- `[TYPE]` (disabled, assessed manually): `RegionCuration` now hard-codes `curated=True`/`raw_seed_reproducible=True`/`uncurated_regions=frozenset()` on the only return — consistent with the span; `uncurated_regions` retained as an always-empty field for the attach/commit contract (documented). No stringly-typed regressions.
- `[SIMPLE]` (disabled, assessed manually): −2300 net test lines + −460 production; the deletion is the simplification. `uncurated_regions`/`raw_seed_reproducible` are kept (not dead) for the downstream contract. No over-engineering introduced.
- `[RULE]` (disabled, assessed manually): see Rule Compliance above — the only rule gap is the #1/#4 untagged-span + stale-log wording, captured as findings.

### Devil's Advocate

Suppose this code is broken. The most dangerous claim it makes is "materialization is now honest and deterministic," and the seams where that claim could be a lie are exactly the error paths. Start there. The curate span is the GM-panel's lie-detector for this subsystem; the whole story exists to make it trustworthy. Yet on one reachable error path — an unexpected exception from a homebrew pack object whose `effective_bestiary()` misbehaves — the span never gets a `curated` attribute at all. An operator watching the panel would see a curate span that simply *stops*, with no `curated=false`, no `reason`, while the connect crashes underneath. That is the precise failure the ValueError/CurationError handlers were written to prevent, and the new code only half-applies the pattern. A confused content author (Jade, per CLAUDE.md, is now a non-Keith author shipping homebrew packs) is the realistic trigger: a malformed pack is exactly the "exotic implementation" the edge-hunter named, and the authoring surface is supposed to tolerate homebrew. Second, consider the operator reading `~/.sidequest/logs`: a broken authored binding on the *normal* path now prints "dungeon curate **degrade** … ADR-106 **Amendment A**: loud, but the turn proceeds, no table freeze." There is no degrade. Amendment A is retired. The log actively tells the operator a falsehood about which mechanism fired — in a story whose entire purpose is to stop the curate stage from lying. A stressed filesystem (unreadable room YAML) routes through `resolve_room_creatures`' `OSError→RoomCreatureBindingError` wrap (verified safe), so that case is graceful — but it still emits the misleading "degrade" log. Third, the empty-`new_nodes` path produces a `curated=True` span over zero regions; a malicious or buggy upstream that emptied the expansion would be reported as a *successful* curation of nothing. The design stage should prevent it, but the curate stage trusts that invariant silently rather than asserting it. None of these are data-corruption or security holes — the behavior is correct, the determinism is real, the transaction aborts loudly on the genuinely bad inputs. But three of them degrade the exact observability honesty this story sells, and two are one-line fixes. For a change whose value proposition is "trust the lie-detector now," shipping a lie-detector that can go dark on an error path and print stale "degrade" prose on its main path is worth a bounce.

## Round-1 Reviewer Assessment (REJECTED — superseded by round 2 below)

**Verdict:** REJECTED (round 1 — addressed by Dev rework, see round 2)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] | Unexpected exception escapes `_stage_curate` with the curate span untagged (no `curated`/`reason`) — inconsistent with the ValueError/CurationError tag-before-raise handlers; weakens the OTEL lie-detector on an error path (the story's own domain). | `sidequest/dungeon/materializer.py:1139-1201` (`pack.effective_bestiary()` at `:1020` is outside the inner try) | Add an outer `except Exception as exc:` in `_stage_curate` that sets `span.set_attribute("curated", False)` + a `reason` (e.g. `f"unexpected: {exc}"`) then `raise` — mirroring the existing handlers. |
| [LOW] | Stale "degrade"/"Amendment A" wording on the now-**main** path — misleads operators on a telemetry surface this story is meant to make honest. Double-flagged (security + edge). | `materializer.py` docstring `:964-987`, ERROR logs `:1004-1011` and `:1031-1037` | Reword to reflect the deterministic main path (no "degrade", no "Amendment A"): a broken authored binding is dropped loud-but-graceful on the main curate path. |
| [LOW] | `reason` prefix `"assemble: {exc}"` covers theme-missing + look-resolution + assemble failures — GM-panel legibility. | `materializer.py:1192` | Use a prefix that fits all three (e.g. `"region-build: {exc}"`) or branch the prefix. |

**Dismissed (with rationale):** empty-`new_nodes` (design-stage invariant guarantees ≥1 node; not reachable, not introduced here); path-join traversal hygiene (`room_creature_binding.py:60` — pre-existing, not in this diff; inputs are server-side config, never player WebSocket input).

**Verified strengths:** carve-out span-tagging correct; YAML/dangling-id paths graceful; sync `_stage_curate` correct; symbol cleanup complete; determinism + clean-span behavior proven by 8 green contract tests + 897 green dungeon/telemetry tests.

**Routing:** Findings are observability-wording + a one-line defensive catch-all (no new testable logic contract) → **green rework (Dev)**, not red. AC 1–6 behavior is correct and stays; this is polish on the curate stage's own honesty surface.

**Handoff:** Back to Dev (Hephaestus) for the green rework.

## Subagent Results

(Round 2 — re-review of the green rework, delta `18b00e01..bf9bad3b`.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (ruff clean; 898 passed dungeon+telemetry; 9/9 contract incl. new catch-all test) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Yes | clean | none (clause ordering correct, all 3 handlers re-raise, BaseException bypasses, no double-set, rewrites textual) | confirmed 0, dismissed 0, deferred 0 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (assessed manually — the new `except Exception` re-raises; not a swallow) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (assessed manually — the new regression test asserts span `curated=false` + exception propagation) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (assessed manually — the rework IS the stale-comment fix; verified no "degrade"/"Amendment A" remains on the main path) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed manually — no type changes in the rework) |
| 7 | reviewer-security | Yes | clean | none (re-raise confirmed; no new sensitive data in reworded logs) | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed manually — +10 lines catch-all + 1 test; no over-engineering) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (assessed manually — the rework closes the #1/#4 gaps from round 1) |

**All received:** Yes (3 enabled subagents returned CLEAN; 6 disabled via settings, assessed manually)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred — all three round-1 findings resolved.

## Reviewer Assessment

**Verdict:** APPROVED

**Round-1 findings — all resolved (verified):**
- `[MEDIUM]` `[EDGE]` `[SILENT]` untagged curate span on unexpected exception → fixed by the `except Exception` catch-all (`materializer.py:1205-1215`) that tags `curated=false`+`reason` then `raise`s; rev2-edge confirmed correct clause ordering + BaseException bypass + no swallow; **new regression test** `test_unexpected_exception_tags_curate_span_before_propagating` asserts the span is tagged `curated=false` AND the exception still propagates loud.
- `[LOW]` `[SEC]` `[DOC]` stale "degrade"/"Amendment A" wording → fixed across `_append_authored_creatures` + `_creatures_from_manifest` docstrings, both authored-bind ERROR logs, and the carve-out (i) messages; now reflect the deterministic main path. rev2-security confirmed logs echo only the same `region_id`/`world_slug`/`exc` (no new leakage).
- `[LOW]` `[EDGE]` broad `"assemble:"` reason prefix → `"region-build:"` (covers theme/look/assemble); rev2-edge confirmed cosmetic span-attribute change, no control-flow effect.

**Data flow traced:** an unexpected per-region failure (e.g. malformed homebrew pack) → `_stage_curate` `except Exception` tags the `dungeon.materialize.curate` span `curated=false` → re-raises → `materialize` aborts the txn loud. Safe: the lie-detector never goes dark, nothing is swallowed (3/3 handlers `raise`).
**Pattern observed:** tag-before-raise consistency across all three exception handlers — `materializer.py:1190-1215`.
**Error handling:** loud + observable on every path (ValueError/CurationError/unexpected); loud-but-graceful only for the caught `RoomCreatureBindingError` (authored-binding typo), which is the documented "no table freeze" contract.
**Specialist tags incorporated:**
- [EDGE] No new boundary/path issues — clause ordering + re-raise + BaseException bypass verified (rev2-edge clean).
- [SEC] No security concerns — the catch-all re-raises (no swallow); reworded logs leak no new data (rev2-security clean).
- [TEST] No test concerns — regression test `test_unexpected_exception_tags_curate_span_before_propagating` added; 9/9 green (manual; test-analyzer disabled).
- [SILENT] No swallowed errors — all three exception handlers end in `raise` (manual; silent-failure-hunter disabled).
- [DOC] No stale docs — the round-1 stale "degrade"/"Amendment A" wording was the fix; verified none remain on the main path (manual; comment-analyzer disabled).
- [TYPE] No type concerns — the rework introduces no type changes (manual; type-design disabled).
- [SIMPLE] No over-engineering — +10-line catch-all + 1 test (manual; simplifier disabled).
- [RULE] No rule violations — round-1 python.md #1/#4 gaps closed (manual; rule-checker disabled).

**Verification:** ruff clean; `tests/dungeon/` + `tests/telemetry/` **898 passed**; `test_158_12` **9 passed**; deviation audit complete (all 5 TEA/Dev deviations ACCEPTED, round 1); the `RegionCuration` byte-reproducibility comment reversal confirmed in code.

**Handoff:** To SM (Themis) for finish-story.

### Reviewer (code review — round 2)
- No upstream findings during round-2 re-review. All three round-1 findings resolved; behavior unchanged, observability honesty restored on the curate stage's main path. *Found by Reviewer during code review.*