---
story_id: "71-32"
jira_key: null
epic: "71"
workflow: "tdd"
---
# Story 71-32: World-level scenario discovery + world-aware binding

> **NOTE (reconstructed 2026-05-30):** This session file was accidentally overwritten by the `testing-runner` subagent (run `71-32-dev-green-rework`), which wrote its test report to the session path. Reconstructed from agent context. See the Reviewer/Dev process Delivery Finding. Content below is faithful to the pre-clobber state plus the green-rework round.

## Story Details
- **ID:** 71-32
- **Epic:** 71 (Playtest bugfix — uncovered findings, 2026-05-27)
- **Jira Key:** None (Jira disabled for this project)
- **Workflow:** tdd
- **Depends On:** 71-19 (Glenross ADR-053 scenario authoring — completed)
- **Points:** 5
- **Priority:** P2
- **Repos:** sidequest-server, sidequest-content

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended |
|-------|---------|-------|
| setup | 2026-05-30 | 2026-05-30T11:04:24Z |
| red | 2026-05-30T11:04:24Z | 2026-05-30T11:27:11Z |
| green | 2026-05-30T11:27:11Z | 2026-05-30T11:39:19Z |
| spec-check | 2026-05-30T11:39:19Z | 2026-05-30T11:42:05Z |
| verify | 2026-05-30T11:42:05Z | 2026-05-30T11:46:16Z |
| review | 2026-05-30T11:46:16Z | 2026-05-30T11:57:10Z (REJECTED → green-rework) |
| green (rework r1) | 2026-05-30T11:57:10Z | - |

## Sm Assessment

**Setup verdict:** Ready for RED. Well-scoped follow-up to 71-19. Three load-bearing facts:
- Loader auto-discovers scenarios ONLY at genre-pack root (`loader.py:1273`); `World` had no scenario field.
- `bind_scenario` was world-AGNOSTIC (`scenario_bind.py:45`) — bound `next(iter(pack.scenarios))`, a No-Silent-Fallbacks violation in waiting.
- Two repos: server teaches loader/bind world-level discovery; content relocates `the_morning_train` to `worlds/glenross/scenarios/`.
- Architecture decision §Fallback: Option A (explicit absence, no fallback). Jira intentionally skipped.

## TEA Assessment

**Tests Required:** Yes — core engine behavior change, fully testable.
**Test File:** `sidequest-server/tests/server/test_scenario_bind.py` (extended).
**Tests Written:** 9 new (AC1–AC4). RED verified clean (`71-32-tea-red-2`): 13 collected → 4 pre-existing PASS, 9 new FAIL, 0 errored; all failures genuine AssertionError/AttributeError.

| Class | Tests | AC |
|-------|-------|----|
| TestWorldModelScenarioField | 1 | AC1 |
| TestBindSelectsActiveWorld | 2 | AC2 |
| TestBindNoSilentFallback | 2 | AC3 |
| TestBindOtelWorldAware | 2 | AC4 |
| TestLoaderWorldLevelDiscovery | 2 | AC1/AC5(mech) |

**Fixture discipline:** All hermetic — synthetic two-world pack via re-keying a scaffold `World` under `_WORLD_A`/`_WORLD_B`; loader test on `tmp_path` via `_load_single_world`. No assertions on real content layout (Operator directive).
**Rule Coverage:** No Silent Fallbacks, OTEL Observability, No Source-Text Wiring Tests, Verify-Wiring — all covered; python lang-review #2/#3/#6 pass; 0 vacuous tests.
**Status:** RED — handed to Dev.

## Dev Assessment

**Implementation Complete:** Yes — the full TEA spine, all four parts.

**Files Changed:**
- `sidequest-server/sidequest/genre/models/pack.py` — added `World.scenarios: dict[str, ScenarioPack] = Field(default_factory=dict)` (AC1) with no-fallback docstring.
- `sidequest-server/sidequest/genre/loader.py` — `_load_single_world` discovers `worlds/<w>/scenarios/` via `_load_subdirectories(world_path, "scenarios", _load_single_scenario)`, passes `scenarios=` to `World(...)`. Empty dir → `{}`.
- `sidequest-server/sidequest/server/dispatch/scenario_bind.py` — reads `pack.worlds[world_slug].scenarios`; returns `None` for scenario-less OR unknown world with no pack-level fallback (AC2/AC3); emits `scenario.bind_skipped` (`genre`/`world`/`reason`) on that path (AC4). Success keeps `scenario.initialized`. Zero call-site changes (both `chargen_mixin.py` callers already pass `world_slug`).
- `sidequest-server/tests/server/test_scenario_bind.py` — `_attach_world_scenario` helper; migrated 2 pre-existing tests to world-level injection.
- `sidequest-content/genre_packs/tea_and_murder/` — `git mv scenarios/the_morning_train → worlds/glenross/scenarios/the_morning_train` (AC5).

**Fallback decision:** Option A (explicit absence, no silent fallback).
**Tests:** 13/13 story; regression sweep 94 pass/5 skip/0 fail; full suite 9170 pass/6 pre-existing-unrelated fail. Live: `tea_and_murder` → `worlds["glenross"].scenarios == ["the_morning_train"]`, pack-level `[]`; pulp_noir pack-level intact.
**Branch:** `feat/71-32-world-scenario-discovery` (server + content, pushed).
**Handoff:** To Reviewer.

### Dev rework (round 1 — post-review)
Addressed all five Reviewer green-rework items + a pyright cleanup:
1. **[DOC]** Rewrote `scenario_bind.py` MODULE docstring to the world-aware contract (removed "pick the first [pack] scenario" + the "return None silently" bullet; now states world-scoped binding + `scenario.bind_skipped` emission + pack-level not consulted).
2. **[TYPE]** Removed the 6 stale `# type: ignore[attr-defined]` on `world.scenarios` (field now declared). Kept the unrelated `_session_data`/`confidence` ignores.
3. **[LINT]** Hoisted `import copy` to module top-level; removed all 4 inline `import copy as _copy`.
4. **[DOC]** Reframed stale RED-era "Today: …" comments (RED block header, `TestWorldModelScenarioField`, `_two_world_pack` docstring, `test_skip_emits…` docstring) to GREEN framing; updated `caverns_pack` fixture docstring.
5. **[TEST]** Added `assert attrs["reason"] == "no_world_scenario"` (skip test) and `assert attrs["guilty_npc"] == "gardener"` (initialized test).
6. **[TYPE bonus]** Added `assert sd is not None` guards in the 3 dispatch helpers — pyright on the file went 15 → 5 errors. The remaining 5 are **pre-existing**, in untouched code (`_pg_isolation` psycopg `execute` overload line 90; `handle_message` GameMessage-union arg-type in `_connect`/`_walk_and_confirm`), unrelated to 71-32.

**Rework tests:** 13/13 story + 47/47 regression sweep (`71-32-dev-green-rework`), ruff clean. **Handoff:** To Reviewer (re-review).

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected (1 behavioral side-effect; implementation correct).
Verified the diff against every AC: AC1–AC5 ALIGNED; AC4 exceeds spec (distinct event names + `reason` vs a `bound` bool). AC6 aligned *as written* (pulp_noir scenarios still LOAD) — but "loads" ≠ "binds":
- **Mismatch (Behavioral, Major):** pulp_noir loses scenario *binding*. `bind_scenario` now reads only world-level; pulp_noir's `annees_folles` world has no `scenarios/` dir, so pulp_noir binds nothing (previously bound `midnight_express`). Only shipping pack affected.
- **Recommendation: D — Defer.** A code fallback would violate AC3. Correct fix is content: migrate pulp_noir scenarios to `worlds/annees_folles/scenarios/` in a follow-up story (logged as Delivery Finding).
**Decision:** Proceed to review — implementation is architecturally correct; the pulp_noir consequence is the intended Option-A trade-off, to be *tracked* not *blocked*.

**Spec-check re-pass (post green-rework r1):** Re-verified — `bind_scenario` binding logic is byte-identical to the prior spec-check (`git diff 44c4e9c..HEAD` on the file shows only docstring/comment changes); the rework introduced **no spec drift**. AC4 coverage is now *stronger* (added `reason` + `guilty_npc` event-attribute assertions), and the previously-contradictory module docstring is corrected. Spec Alignment: unchanged (AC1–AC5 aligned; AC6 pulp_noir-binding follow-up still tracked). Proceed to verify.

## TEA Assessment (verify)

**Status:** GREEN (13/13, `71-32-tea-verify`).
**Simplify:** reuse 4 findings (1 medium overlay-extract = out-of-scope pre-existing; 3 low no-action); quality 2 medium (both stale docs I introduced — APPLIED, commit `67a839e`); efficiency clean.
**Applied:** 2 docstring fixes. **Deferred:** overlay-helper extraction (pre-existing). **Reverted:** 0.

**Verify re-pass (post green-rework r1):** The green-rework delta (`67a839e..HEAD`) is **doc/test/assert-only** — module docstring + test docstrings/comments/`import copy` hoist/type-ignore removal/2 OTEL asserts/3 `assert sd is not None` guards. The first verify already fanned out reuse/quality/efficiency on the substantive code; a second full fan-out on docstring changes is disproportionate, so I did a targeted check instead: ruff clean; green confirmed by the rework run `71-32-dev-green-rework` (13/13 story + 47/47 regression sweep). No new complexity/duplication introduced (the changes *remove* dead suppressors and inline imports). **Overall:** simplify: clean (rework). **Quality Checks:** passing. **Handoff:** To Reviewer (re-review). *(Note: did not re-invoke testing-runner here — it clobbered this session file on the prior run; see Delivery Finding.)*

## Subagent Results

_Round 2 (re-review of green-rework r1). All 9 re-run on the rework delta `/tmp/71-32-rework.diff`. Round-1 results are summarized in the Reviewer Assessment history below._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | tests 13/13 GREEN, ruff clean, pyright 5 errors = pre-existing fingerprint (no new) | confirmed 0 |
| 2 | reviewer-edge-hunter | Yes | clean | none — production logic byte-identical (only docstring) | N/A |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A |
| 4 | reviewer-test-analyzer | Yes | clean | none — both new asserts verified correct (`reason`/`guilty_npc`), guards sound | N/A |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (line 779 stale RED class docstring) + confirmed all 5 round-1 doc fixes landed | confirmed 1 (LOW, non-blocking) |
| 6 | reviewer-type-design | Yes | clean | none — type-ignore removal correct, `assert sd is not None` narrowing sound | N/A |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Yes | clean | none — changes only remove dead suppressors/inline imports | N/A |
| 9 | reviewer-rule-checker | Yes | clean | none — both round-1 findings (#10 import, #6 type:ignore) resolved; no new violations; remaining ignores legitimate (`confidence` union, `_session_data` private) | confirmed 0 |

**All received:** Yes (9 re-run, 1 with a finding)
**Total findings:** 1 confirmed (LOW, non-blocking), 0 dismissed, 0 deferred. All five round-1 fixes verified landed.

## Reviewer Assessment

**Verdict:** APPROVED (round 2 — re-review of green-rework r1).

**Round 2 summary:** All nine specialists re-run on the rework delta. **Every round-1 finding verified resolved** by comment-analyzer/rule-checker/type-design/simplifier: module docstring corrected, 6 stale `world.scenarios` type-ignores removed, `import copy` hoisted, RED "Today:" comments reframed, and the two OTEL assertions (`reason`/`guilty_npc`) confirmed correct by test-analyzer. Preflight: 13/13 green, ruff clean, pyright = pre-existing 5-error fingerprint (no new). Edge/silent/type/security/simplifier: clean — production logic is byte-identical (docstring-only delta).

**One residual finding (non-blocking):**
- `[LOW] [DOC]` — `TestLoaderWorldLevelDiscovery` class docstring (test_scenario_bind.py:~779) still carries RED-phase wording ("Fails in RED … passes once both land"). I reframed the section comment in rework r1 but missed this class docstring. It is a historical TDD-provenance note on a now-passing test — not production, not behavior-contradicting. **Decision: approve + log as a trivial sweep** (see Delivery Finding). Per the blocking rule LOW does not block, and re-looping the full TDD pipeline for one test-docstring line is disproportionate. This is a deliberate severity distinction from round 1 (which rejected a MEDIUM *production* docstring that contradicted behavior, plus a 5-item cluster).

**Data flow / pattern / error handling / wiring:** unchanged from round 1 and re-affirmed — `[VERIFIED]` no silent fallback (`scenario_bind.py:74-97` reads only `world.scenarios`); `[VERIFIED]` OTEL both paths (`scenario.initialized` + `scenario.bind_skipped` with `reason`); `[VERIFIED]` wiring (`chargen_mixin.py:871,1055` + dispatch/loader tests); `[VERIFIED][SEC]` safe_load, no eval/exec, loader paths from filesystem.

**Dispatch tags (round-2 confirmed clean / round-1 resolved):** `[EDGE]` clean · `[SILENT]` clean · `[TEST]` clean (asserts correct) · `[DOC]` 1 LOW residual · `[TYPE]` clean (ignores removed) · `[SEC]` clean · `[SIMPLE]` clean · `[RULE]` clean.

**Handoff:** To SM for finish (via spec-reconcile). One LOW doc sweep logged as non-blocking.

---
### Reviewer Assessment — Round 1 (history)

**Verdict:** REJECTED → green-rework (round 1) — quality bar; no Critical/High correctness or security defects. **[RESOLVED in Dev rework round 1; re-reviewed and APPROVED in round 2 above.]**

Implementation correct, tested (13/13), wired (2 chargen call sites + dispatch test), spec-aligned, zero correctness/security/behavior defects. Rejected on a cluster of confirmed lint/doc/dead-code issues, worst = a production module docstring contradicting behavior.

| Severity | Issue | Location | Fix |
|----------|-------|----------|-----|
| [MEDIUM] [DOC]/[EDGE] | Module docstring contradicts behavior ("pick first [pack] scenario"; "return None silently") | `scenario_bind.py:5-21` | Rewrite to world-aware contract + bind_skipped emission |
| [LOW] [TYPE]/[TEST]/[RULE] | Stale `# type: ignore[attr-defined]` on world.scenarios | test file | Remove; pyright clean |
| [LOW] [SIMPLE]/[RULE] | Inline `import copy as _copy` | test file | Hoist to top |
| [LOW] [DOC] | Stale RED "Today:" comments | test file | Reframe to GREEN |
| [LOW] [TEST] | OTEL `reason`/`guilty_npc` assertions missing | test file | Add asserts |

`[VERIFIED]` No silent fallback (`scenario_bind.py:74-97` reads only `world.scenarios`). `[VERIFIED]` OTEL both paths. `[VERIFIED]` Wiring (`chargen_mixin.py:871,1055` + dispatch/loader wiring tests). `[VERIFIED][SEC]` `safe_load`, no eval/exec, loader paths from filesystem not user input. `[VERIFIED]` `World.scenarios` declared `Field`, tripwire uses `model_fields`.
**Dismissed:** `-> None` "missing" (false positive, line 157 has it); NonRecordingSpan (matches existing convention, prod has parent span, OTEL test wraps span); `world.scenarios=None` (unreachable); empty world_slug (observable, upstream); premature-abstraction (used twice).
**Deferred:** `_load_subdirectories` generic typing (pre-existing); unknown_world info→warning; multi-scenario-per-world signal; world_slug REST validation (pre-existing); reason Literal/StrEnum.
**Devil's Advocate:** considered NonRecordingSpan event-loss, pulp_noir dark, stray-file silent-skip, multi-scenario truncation, stale docs — only stale docs (5) land as the reject basis; rest non-blocking/pre-existing/intended.
**Handoff:** Back to Dev for green-rework. `[Dev completed rework round 1.]`

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): `bind_scenario`'s `world_slug` already required kw-only but body ignored it; both call sites already pass it — Dev changes zero call sites. Affects `scenario_bind.py`. *Found by TEA during test design.*
- **Gap** (non-blocking): AC5/AC6 not asserted in server suite (moved out to avoid content coupling, Operator directive); verify content-side. Affects `sidequest-content/genre_packs/tea_and_murder/`. *Found by TEA during test design.*

### Dev (implementation)
- **Confirmation** (non-blocking): AC5 verified live (glenross carries the_morning_train; pack-level empty); AC6 verified (pulp_noir pack-level loads). Empty leftover `tea_and_murder/scenarios/` dir removed. *Found by Dev during implementation.*
- **Gap** (non-blocking): full server suite has 6 pre-existing failures (missing corpus files, missing asset dirs) in `test_audit_namegen_corpora.py`/`test_pack_validator*.py` — unrelated to 71-32. *Found by Dev during implementation.*

### Architect (spec-check)
- **Gap** (non-blocking, **needs follow-up story**): pulp_noir loses scenario *binding* (world `annees_folles` has no world-level scenarios). Intended Option-A consequence. **Recommend SM file:** "Migrate pulp_noir scenarios to `worlds/annees_folles/scenarios/`". Affects `sidequest-content/genre_packs/pulp_noir/`. *Found by Architect during spec-check.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_load_subdirectories` returns `dict[str, Any]`; a generic signature would type-thread all 3 call sites. Pre-existing. Affects `loader.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): stray non-dir file under `worlds/<w>/scenarios/` is silently skipped (no log). Pre-existing helper behavior. Affects `loader.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking, **process bug**): the `testing-runner` subagent wrote its run report to the session file path `.session/71-32-session.md`, clobbering the pipeline's assessments (reconstructed by Dev). The testing-runner must write run results to a run-scoped path, never the session file. Affects the testing-runner subagent definition / its output target. *Found by Dev during green-rework (after a testing-runner clobber).*
- **Improvement** (non-blocking, LOW — trivial sweep): `TestLoaderWorldLevelDiscovery` class docstring (`tests/server/test_scenario_bind.py:~779`) still says "Fails in RED … passes once both land" — stale TDD-provenance wording that rework r1 missed. Approved over (not blocked) per the LOW-doesn't-block rule; recommend a 2-line reframe in a trivial chore. Affects `sidequest-server/tests/server/test_scenario_bind.py`. *Found by Reviewer during re-review (round 2).*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Hermetic loader test instead of real-content assertions**
  - Spec source: context-story-71-32.md, AC5+AC6
  - Spec text: "Integration test: A multi-world pack … loads; binding glenross loads the morning-train scenario" / "pulp_noir … pack-level scenarios still load"
  - Implementation: loader discovery tested via `_load_single_world` on a synthetic `tmp_path` world; real packs not loaded by the server suite; AC5/AC6 delegated to content-repo verification.
  - Rationale: Operator directed (twice) tests must not point at real content; content coupling is fragile.
  - Severity: minor
  - Forward impact: AC5/AC6 verification lives content-side (captured as Delivery Finding).
- **Prescribed OTEL event name for the no-bind decision**
  - Spec source: context-story-71-32.md, AC4; session AC9
  - Spec text: "emit an OTEL span indicating which world's scenario was bound (or none)"
  - Implementation: absence path emits `scenario.bind_skipped` (`world`/`genre`/`reason`); success keeps `scenario.initialized`.
  - Rationale: a behavior assertion needs a concrete event name; mirrors existing naming.
  - Severity: minor
  - Forward impact: Dev emits `scenario.bind_skipped` (done).

### Dev (implementation)
- **Updated two pre-existing tests' scenario-injection site from pack-level to world-level**
  - Spec source: TEA RED suite + AC2/AC3
  - Spec text: pre-existing `test_seeds_matching_npc_beliefs_and_emits_event` and `test_confirmation_binds_injected_scenario` injected at `pack.scenarios`
  - Implementation: both inject via `_attach_world_scenario(...)` at `pack.worlds[world_slug].scenarios`; intent (belief seeding; bind wiring) unchanged.
  - Rationale: the contract change makes pack-level injection a no-op; the only alternative (pack-level fallback) violates AC3.
  - Severity: minor
  - Forward impact: none — intent preserved, all tests green.

### Reviewer (audit)
- **TEA — hermetic loader test** → ✓ ACCEPTED: Operator-directed, sound; real `tmp_path` wiring; AC5/AC6 correctly delegated.
- **TEA — prescribed `scenario.bind_skipped` name** → ✓ ACCEPTED: implemented as specified; mirrors `scenario.initialized`.
- **Dev — migrated 2 tests to world-level injection** → ✓ ACCEPTED: setup-only, not assertion-weakening; the only correct fix (a fallback would violate AC3).
- No undocumented spec deviations beyond the above (the pulp_noir side-effect was documented by Architect during spec-check).

### Architect (reconcile)

Verified the TEA and Dev deviation entries above — all six fields present and accurate against the code and `sprint/context/context-story-71-32.md`. Promoting two spec-vs-implementation gaps into the formal manifest so the audit is self-contained:

- **pulp_noir loses scenario *binding* as a side effect of world-only binding**
  - Spec source: context-story-71-32.md, AC6 ("No backward-incompatibility break for pulp_noir") and §Scope-Boundaries / §Backward-Compatibility
  - Spec text: "pulp_noir keeps its pack-level scenarios. This must keep passing — it catches a Dev who rips out pack-level discovery while adding world-level." (AC6 intent) and "Pulp_noir scenarios remain pack-level for now; pack-level discovery is preserved for them."
  - Implementation: pack-level **discovery** is preserved (pulp_noir's `midnight_express`/`the_warehouse` still LOAD into `GenrePack.scenarios`), satisfying AC6 as literally written. BUT `bind_scenario` now reads **only** `pack.worlds[world_slug].scenarios`; pulp_noir's sole world `annees_folles` ships no `worlds/annees_folles/scenarios/`, so pulp_noir now **binds no scenario at session start** (it previously bound `midnight_express` via the old world-agnostic `next(iter(pack.scenarios))`). pulp_noir is the only shipping pack with pack-level-only scenarios (tea_and_murder was migrated by this story).
  - Rationale: this is the intended, accepted consequence of Option A (explicit absence, no silent fallback). Restoring pulp_noir binding via a pack-level fallback would directly violate AC3 and the No Silent Fallbacks principle. "Loads ≠ binds" is the precise gap: AC6 guards loading; binding is the casualty.
  - Severity: major (behavioral change to a shipping pack) — but **deferred, not blocked**.
  - Forward impact: **a follow-up content story is required** — "Migrate pulp_noir scenarios to `worlds/annees_folles/scenarios/`" (same shape as 71-32's Glenross move). Until then pulp_noir's world legitimately declares no scenario. Recommend SM file it at finish. Tracked in Delivery Findings (Architect spec-check).

- **OTEL no-bind decision encoded as a named event + `reason`, not a `bound: bool` attribute**
  - Spec source: context-story-71-32.md, AC4
  - Spec text: "Driving a bind emits one watcher span carrying `world_slug`, `genre_slug`, `scenario_id` (or `None`), and `bound: bool`."
  - Implementation: success emits `scenario.initialized` (with `scenario_id`/`world`/`genre`/`guilty_npc`); absence emits a **distinct** `scenario.bind_skipped` event (with `world`/`genre`/`reason` ∈ {`no_world_scenario`,`unknown_world`}). The decision is encoded in the event *name* + a `reason` discriminator rather than a single event with a `bound` boolean.
  - Rationale: distinct event names + a `reason` are strictly more legible for the GM panel (it can filter on the event name and see *why* nothing bound, distinguishing an unknown world from an empty one) — the spec's intent ("the absence decision must be observable") is exceeded, not weakened.
  - Severity: minor (test-asserted, intent met-and-exceeded).
  - Forward impact: none — any downstream span consumer keys on `scenario.bind_skipped` / `scenario.initialized` + attributes; no `bound` boolean exists to depend on.

No further undocumented deviations. No ACs were deferred or descoped (AC1–AC6 all addressed; AC5/AC6 verification split between server suite and content-side per the TEA deviation).

---

## Story Context (summary)

Full design narrative is committed at `sprint/context/context-story-71-32.md` (the canonical context doc). Key points preserved here for the audit:
- **Problem:** loader discovered scenarios only at pack root; `bind_scenario` was world-agnostic (`next(iter(pack.scenarios))`) — a latent cross-world bleed + No-Silent-Fallbacks violation once a pack has >1 world/scenario (tea_and_murder: glenross + blackthorn_moor).
- **Solution:** `World.scenarios` field; loader discovers `worlds/<w>/scenarios/`; `bind_scenario` binds `pack.worlds[world_slug].scenarios` only; relocate `the_morning_train` under `worlds/glenross/`.
- **Fallback decision:** Option A (explicit absence, no pack-level fallback) — per No Silent Fallbacks.
- **Key files (verified):** `models/pack.py:119` (World), `loader.py:1273` (discovery), `scenario_bind.py:45` (bind, already took `world_slug`), `chargen_mixin.py:871,1055` (the two callers).
- **OTEL:** `scenario.initialized` (success) + `scenario.bind_skipped` (absence).
- **References:** ADR-053 (Scenario System); story 71-19 (Glenross scenario authoring).