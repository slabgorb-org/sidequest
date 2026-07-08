---
story_id: "163-2"
jira_key: ""
epic: "163"
workflow: "tdd"
---
# Story 163-2: Weed-whack dead WorldGraph/SubGraph/GraphEdge/Terrain models (plan task 2)

## Story Details
- **ID:** 163-2
- **Title:** Weed-whack dead WorldGraph/SubGraph/GraphEdge/Terrain models (plan task 2)
- **Points:** 1
- **Priority:** p1
- **Type:** chore
- **Repos:** server
- **Workflow:** tdd
- **Stack Parent:** none

## Branch Information
- **Branch Strategy:** gitflow (feat/163-2-weed-whack-dead-cartography-models)
- **Repository:** sidequest-server
- **Base:** origin/develop

## Design Spec
- docs/superpowers/specs/2026-07-08-three-tier-mapping-design.md §2
- docs/superpowers/plans/2026-07-08-mapping-track-a-main-map-treatments.md (Task 2)

## Context
- sprint/context/context-story-163-2.md
- sprint/context/context-epic-163.md

## Acceptance Criteria
1. The five models (Terrain, WorldGraphNode, GraphEdge, SubGraph, WorldGraph) are no longer importable from `sidequest.genre.models` (`hasattr` is False).
2. `CartographyConfig.model_fields` no longer contains `world_graph` or `sub_graphs`; still contains `regions` and `routes`.
3. New test `tests/genre/test_dead_cartography_models_removed.py` exists and passes (`uv run pytest tests/genre/test_dead_cartography_models_removed.py -v -n0`).
4. Loader + models import cleanly (`uv run python -c "import sidequest.genre.loader; import sidequest.genre.models"`); ruff clean on the three touched files.
5. `TerrainScar` (from legends.py) is preserved — verify it is NOT deleted.

## Sm Assessment

**Readiness:** Ready for RED. Merge gate clear (no open PRs in any repo). Branch `feat/163-2-weed-whack-dead-cartography-models` cut off `origin/develop` (server targets develop per repos.yaml). Session + story context + epic context all written.

**Workflow resolution:** Story YAML tags workflow `superpowers` — a superpowers-plan-execution designation, NOT a registered pf workflow (`pf workflow type superpowers` errors). Resolved to `tdd` because the plan's Task 2 is explicitly red→green: "write the failing test → SEE it fail → delete code → make it pass." The exact test body is pre-written in the plan, so the RED phase is transcription, not authorship. This honors both the superpowers-TDD intent and the plan's structure. (Size is 1pt, which would default to `trivial`; `tdd` chosen deliberately for the plan's explicit red/green split.)

**Scope boundary (weed-whack — CLAUDE.md doctrine "prefer aggressive rip-and-rebuild"):** delete FIVE coordinate-free graph models (`Terrain`, `WorldGraphNode`, `GraphEdge`, `SubGraph`, `WorldGraph`) + the `world_graph`/`sub_graphs` fields on `CartographyConfig`, plus their `__init__.py` imports/`__all__` entries. Plan verifies these have NO non-test consumers. `CartographyConfig` (regions + routes) is the graph of record and stays. This is Task 2 ONLY — do NOT pull in Task 3's `MapTreatmentConfig`/`MapProvenance` additions (that's story 163-1).

**Risks for TEA/Dev:**
- `TerrainScar` (from legends.py) is a DIFFERENT symbol — must be preserved. AC5 guards this; don't grep-delete on "Terrain".
- Leave `StrEnum`/`Annotated`/`Literal` imports that surviving models still use — `NavigationMode` needs `StrEnum`.
- Test is a reflection-based tripwire (interrogates runtime types/fields, not source text) — a CLAUDE.md-sanctioned exception to the "no content-in-unit-tests" rule since it tests CODE structure, not content invariants.
- Pre-existing: full parallel server test runs can deadlock on OTEL span-count tests — run the new test file with `-n0` as the plan specifies.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Structural deletion with concrete, reflection-checkable invariants — the plan's own Task 2 is red→green.

**Test Files:**
- `sidequest-server/tests/genre/test_dead_cartography_models_removed.py` — reflection-based tripwire (interrogates runtime types/fields, not source text; CLAUDE.md-sanctioned exception per server "No Source-Text Wiring Tests").

**Tests Written:** 3 tests covering 3 ACs (AC1, AC2, AC5)
**Status:** RED confirmed (2 fail, 1 pass) — verified by testing-runner (run_id 163-2-tea-red, 0.78s, `-n0`):
- `test_dead_graph_models_are_gone` → **FAIL** (AC1 — five dead models still present) ✓ expected RED
- `test_cartography_config_has_no_graph_fields` → **FAIL** (AC2 — `world_graph`/`sub_graphs` still on `CartographyConfig`) ✓ expected RED
- `test_terrain_scar_is_preserved` → **PASS** (AC5 — over-reach guard; `TerrainScar` must survive and does) ✓ expected GREEN-from-start

The AC5 preservation guard is a deliberate paranoid addition (Argus): a naive grep-delete on "Terrain" would nuke the distinct `legends.py` `TerrainScar` symbol. This test proves the weed-whack stays surgical. It passes now and must keep passing after Dev's deletion — a regression tripwire, not a RED assertion.

### Rule Coverage

| Rule (python.md) | Applies? | Test / Handling | Status |
|------|----------|-----------------|--------|
| #6 Test quality (no vacuous asserts) | Yes | Self-checked: every assertion is meaningful (`not hasattr`, set membership, identity `is`); no `assert True`, no truthy-only, no skips, no mocks | pass |
| #10 Import hygiene (no star imports) | Yes | Test uses `import ... as models` + explicit symbol import; no `import *` | pass |
| "No Source-Text Wiring Tests" (server CLAUDE.md) | Yes | Reflection tripwire, not `read_text()`/grep — the sanctioned dataclass/type-check exception | pass |
| #1–#5, #7–#9, #11–#13 | No | No new source code, exceptions, I/O, async, deserialization, or boundary input in a test-only RED diff | n/a |

**Rules checked:** 3 of 3 applicable rules have coverage/handling.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Hephaestus) for GREEN — delete the five models + two `CartographyConfig` fields + `__init__.py` imports/`__all__` entries per plan Task 2; then all 3 tests pass and the AC4 CLI import + ruff guards run clean.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/genre/models/world.py` — deleted the five dead graph classes (`Terrain`, `WorldGraphNode`, `GraphEdge`, `SubGraph`, `WorldGraph`) and the orphaned "Hierarchical world graph" section header, plus the `world_graph`/`sub_graphs` fields on `CartographyConfig`.
- `sidequest-server/sidequest/genre/models/__init__.py` — deleted the five imports and five `__all__` entries. Kept `CartographyConfig`, `LegendEntry`, `NavigationMode`, `Region`, `RoomDef`, `Route`, `WorldConfig`, and `TerrainScar`/`FactionGrudge`/`Legend`.

**Diff:** 92 deletions, 0 additions — a pure weed-whack.

**Tests:** 3/3 passing (GREEN) — verified by testing-runner (run_id 163-2-dev-green, 0.55s, `-n0`):
- `test_dead_graph_models_are_gone` → PASS (AC1)
- `test_cartography_config_has_no_graph_fields` → PASS (AC2)
- `test_terrain_scar_is_preserved` → PASS (AC5 — over-reach guard holds)

**AC verification:**
- AC1/AC2/AC5 — covered by the GREEN tests above.
- AC3 — the test file exists and passes.
- AC4 — `import sidequest.genre.loader; import sidequest.genre.models` runs clean (only the pre-existing unrelated `BodyDef` "register" UserWarning); ruff check + format clean on all three touched files.

**Regression:** `tests/genre/ -n0` shows 27 pre-existing failures in `test_162_3_generics_content.py` / `test_162_6_space_opera_bestiary_detriplication.py` (WWN/bestiary content-fixture drift). **Proven pre-existing** by stashing this deletion and re-running those two files — they fail identically on the base branch. Zero cartography-related regressions. Confirmed no non-test consumers of any deleted symbol across `sidequest/`.

**Branch:** feat/163-2-weed-whack-dead-cartography-models (pushed; commit e2a38871 on top of TEA's test commit 37f00bdf)

**Handoff:** To Reviewer (Hermes) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | none (3/3 GREEN, ruff+format+import clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | clean | none | N/A |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; domain self-assessed (no `except`/fallback in a pure deletion) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings; domain self-assessed (3 meaningful reflection asserts, no vacuous/skip) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings; domain self-assessed (orphaned section comment removed with its code; no stale comment left) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings; domain self-assessed (Pydantic model deletion; surviving types unchanged) |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings; domain self-assessed (diff IS a simplification — 92 del/0 add) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings; rules enumerated by hand in Rule Compliance below |

**All received:** Yes (3 enabled subagents returned clean; 6 disabled via `workflow.reviewer_subagents`, domains self-assessed)
**Total findings:** 0 confirmed, 0 dismissed, 1 deferred (non-blocking Improvement — see Delivery Findings)

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` + server CLAUDE.md + SOUL.md, over the full diff (2 source files deleted-from, 1 new test file):

| Rule | Applies? | Verdict | Evidence |
|------|----------|---------|----------|
| #1 Silent exception swallowing | No | compliant | Diff contains zero `except` blocks. |
| #2 Mutable default args | No | compliant | No function/method definitions with defaults added. |
| #3 Type annotation gaps at boundaries | Yes (test fns) | compliant | All 3 test fns annotated `-> None`; no boundary code added. |
| #6 Test quality (no vacuous asserts) | Yes | compliant | `test_dead_cartography_models_removed.py` — every assert is meaningful (`not hasattr`, set membership, identity `is`); RED run proved the asserts discriminate (2 failed when models present); no `assert True`, no skip, no mock. |
| #8 Unsafe deserialization | No | compliant | No pickle/yaml.load/eval/exec/subprocess/json.loads in diff. |
| #10 Import hygiene (no star imports, no unused) | Yes | compliant | Removed 5 now-unused imports (net hygiene gain); `import ... as models` + explicit symbol import, no `import *`; ruff `F401` clean confirms no orphaned import left behind. |
| #11 Input validation at boundaries | No | compliant | No new input-handling/boundary code. |
| Server "No Source-Text Wiring Tests" | Yes | compliant | Test is a reflection tripwire (`hasattr`/`model_fields`), not `read_text()`/grep — the explicitly sanctioned dataclass/type-check exception. |
| SOUL/CLAUDE "No Stubbing / Dead code is worse than no code" | Yes | compliant | Diff removes verified-dead code; leaves no shell. |
| SOUL/CLAUDE "No Silent Fallbacks" | Yes | compliant (see note) | `CartographyConfig.model_config` is `extra="ignore"` (world.py:199), **unchanged** by this diff — a stray `world_graph:`/`sub_graphs:` key in future YAML would be silently dropped. This looseness is pre-existing, not introduced here, and no content sets these keys. Logged as a non-blocking Improvement for a future story. |

## Devil's Advocate

Let me argue this deletion is broken. **First attack — a hidden runtime consumer.** Pydantic fields can be read via `getattr`/`model_dump()` without a lexical `.world_graph` reference, so grep could miss a dynamic reader. Rebuttal: `model_dump()` of a `CartographyConfig` would simply no longer contain the keys; any consumer iterating dumped dicts already tolerates absent optionals (the fields defaulted to `None`), and the security subagent confirmed via `git grep` against the pre-deletion commit that no `.world_graph`/`.sub_graphs` attribute access exists anywhere. **Second attack — legacy serialized state.** A saved DB snapshot might carry a populated `world_graph`. Rebuttal: `CartographyConfig` is a genre-pack config parsed from YAML at load time, not persisted game state; and `extra="ignore"` means a legacy blob carrying the key reloads without error (key dropped). Project memory also records there are no saves to migrate. **Third attack — the test is vacuous.** `hasattr(models, "WorldGraph")` could be structurally false for reasons unrelated to deletion. Rebuttal: the RED run proved discrimination — the same assertions FAILED when the models were present and PASS now; a vacuous test cannot flip. **Fourth attack — over-reach onto `TerrainScar`.** A grep-delete on "Terrain" is the obvious footgun. Rebuttal: `TerrainScar` (legends.py:13) is intact, still imported (__init__.py:92) and exported (__all__:303), and `test_terrain_scar_is_preserved` explicitly guards it — all three subagents independently confirmed. **Fifth attack — a still-used import was collaterally removed.** Rebuttal: `StrEnum` (NavigationMode:16), `Annotated`/`Literal` (RoomExit), `Any` (Region.landmarks) all remain in use; ruff `F401` clean proves no orphan. **Sixth attack — content in a sibling repo declares the field.** Rebuttal: `grep -rE '^\s*(world_graph|sub_graphs)\s*:' sidequest-content/` returns nothing; content is the single source of truth. No break found on any axis.

## Reviewer Assessment

**Verdict:** APPROVED

This is a surgical, verified-dead-code removal (92 deletions, 0 source additions) plus one reflection-tripwire test. The claim underwriting the whole story — "no non-test consumers" — was independently confirmed three ways (my grep, edge-hunter, security's `git grep` against the parent commit) across BOTH the server package and the content repo.

**Data flow traced:** genre-pack `cartography.yaml` → `CartographyConfig` model-validate → (previously) `.world_graph`/`.sub_graphs` optional fields → **no reader anywhere**. Removing the fields changes no live path: no content populates them, `extra="ignore"` tolerates any stray key, and nothing reads them downstream. Safe.

**Observations (tagged):**
- `[VERIFIED]` No dangling reference to any deleted symbol in server or content — evidence: my `grep -rE` over `sidequest-server/sidequest/` + `sidequest-content/` returned none; corroborated by `[EDGE]` (clean) and `[SEC]` (git grep vs `e2a38871^`, clean).
- `[VERIFIED]` `TerrainScar` preserved — legends.py:13 class, __init__.py:92 import, __all__:303 export all intact; `test_terrain_scar_is_preserved` PASSES.
- `[VERIFIED]` No collaterally-orphaned import — `StrEnum`/`Annotated`/`Literal`/`Any` still used (NavigationMode:16, RoomExit:62, Region.landmarks:129); ruff F401 clean.
- `[VERIFIED]` `orchestrator.py:612` + `:2279` `world_graph` mentions are unrelated prose (a deferred `TurnContext` Phase-2 field / lore-filter comment for Story 41-7), not consumers — read directly; not in diff. `[SEC]` independently reached the same conclusion.
- `[SEC]` security clean — deleted models' `extra="allow"`/`extra="forbid"` never guarded a live deserialization path; `CartographyConfig` `extra="ignore"` unchanged. No security control removed.
- `[SIMPLE]` The diff IS the simplification — dead-code removal aligns with "Dead code is worse than no code." (subagent disabled; self-assessed)
- `[TEST]` 3 meaningful reflection assertions, no vacuous/skip; RED run proved discrimination. (subagent disabled; self-assessed)
- `[SILENT]` No swallowed errors / fallbacks introduced — pure deletion, no `except`. (subagent disabled; self-assessed)
- `[DOC]` Orphaned "Hierarchical world graph" banner comment removed with its code; no stale comment left behind. (subagent disabled; self-assessed)
- `[TYPE]` No stringly-typed API or unsafe cast introduced; surviving `CartographyConfig`/`Region`/`Route` types unchanged. (subagent disabled; self-assessed)
- `[RULE]` Full python lang-review enumeration above — all applicable rules compliant. (subagent disabled; enumerated by hand)

**Error handling:** N/A for a deletion; the one relevant posture (`CartographyConfig` `extra="ignore"`) is pre-existing and unchanged — noted as a non-blocking Improvement, not a blocker.

**Handoff:** To SM (Themis) for finish-story.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-08T21:42:27Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-08T21:22:12+00:00 | 2026-07-08T21:25:05Z | 2m 53s |
| red | 2026-07-08T21:25:05Z | 2026-07-08T21:29:25Z | 4m 20s |
| green | 2026-07-08T21:29:25Z | 2026-07-08T21:37:01Z | 7m 36s |
| review | 2026-07-08T21:37:01Z | 2026-07-08T21:42:27Z | 5m 26s |
| finish | 2026-07-08T21:42:27Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings. Plan Task 2's "no non-test consumers" claim was spot-checked at runtime: the five dead symbols are re-exported only from `models/__init__.py`, and `TerrainScar` is a cleanly-distinct `legends.py` symbol. Scope matches the plan exactly.

### Dev (implementation)
- No upstream findings during implementation. The plan's "no non-test consumers" claim held exactly — grep across `sidequest/` for all five symbols (with word-boundary guards separating `Terrain` from `TerrainScar`) returned zero non-test hits, and the only test reference is the tripwire's own string tuple.

### Reviewer (code review)
- **Improvement** (non-blocking): `CartographyConfig.model_config` is `extra="ignore"` (`sidequest/genre/models/world.py:199`), so a stray `world_graph:`/`sub_graphs:` key in a future `cartography.yaml` would be silently dropped rather than failing loud — mild tension with SOUL.md "No Silent Fallbacks." **Pre-existing and out of scope for 163-2** (this diff did not touch the model_config, and no content sets these keys). Affects `sidequest/genre/models/world.py` (a future story could tighten `CartographyConfig` to `extra="forbid"` once the map.yaml treatment layer lands in 163-1). *Found by Reviewer during code review.*

## Impact Summary

**Blocking Issues**: 0
**Non-Blocking Findings**: 1

**Summary**: Story 163-2 successfully removes five coordinate-free graph models (Terrain, WorldGraphNode, GraphEdge, SubGraph, WorldGraph) and their corresponding CartographyConfig fields (world_graph, sub_graphs) from the server codebase. All 5 acceptance criteria verified and passing. The deletion is verified-dead (no consumers in server package or content repo); CartographyConfig (regions + routes) retains full functionality as the authoritative cartography model.

**Non-Blocking Finding**:
- **Improvement**: `CartographyConfig.model_config` uses `extra="ignore"` (pre-existing), so a stray `world_graph:`/`sub_graphs:` YAML key would be silently dropped rather than failing loud. This is out of scope for 163-2 but noted for future tightening when MapTreatmentConfig lands in story 163-1.

**Test Coverage**: 3/3 tests passing (GREEN); all reflected assertions discriminative (proven by RED→GREEN transition)

**Lint & Import Hygiene**: 
- Loader + models import cleanly
- ruff check: all checks passed
- ruff format: 3 files already formatted


## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Added a third test (AC5 preservation guard) beyond the plan's literal two**
  - Spec source: plan `2026-07-08-mapping-track-a-main-map-treatments.md`, Task 2 (test body shows only `test_dead_graph_models_are_gone` + `test_cartography_config_has_no_graph_fields`)
  - Spec text: two test functions given verbatim
  - Implementation: added `test_terrain_scar_is_preserved` asserting `TerrainScar` survives
  - Rationale: AC5 ("TerrainScar preserved") is an explicit acceptance criterion the plan's tests didn't cover; the plan's own risk note warns a grep-delete on "Terrain" could nuke it. This is fuller AC coverage, not a scope change.
  - Severity: minor
  - Forward impact: none — additive; the two plan tests are transcribed verbatim.
- **AC4 (loader/models import cleanly + ruff) verified by CLI, not a unit test**
  - Spec source: plan Task 2, steps at plan lines 100–101; session AC4
  - Spec text: `uv run python -c "import sidequest.genre.loader; import sidequest.genre.models"` and ruff on the three touched files
  - Implementation: left as GREEN-phase toolchain checks for Dev; not duplicated as a pytest test
  - Rationale: import-cleanliness and lint are build-gate concerns the plan already scopes as CLI steps; a redundant pytest import adds no signal and risks pulling heavy loader deps into the unit suite. The test module already imports `sidequest.genre.models`, so package import is exercised.
  - Severity: minor
  - Forward impact: none — Dev runs the CLI guard + ruff in GREEN per plan.

### Dev (implementation)
- **Also deleted the orphaned "Hierarchical world graph" section-header comment**
  - Spec source: plan `2026-07-08-mapping-track-a-main-map-treatments.md`, Task 2 file list
  - Spec text: lists only the five classes (~L102–174) and the two `CartographyConfig` fields (~L299–300) for deletion in `world.py`
  - Implementation: also removed the three-line banner comment (`# --- / # Hierarchical world graph / # ---`) that headed only those now-deleted classes
  - Rationale: the comment described exclusively the deleted section; leaving it would be a dangling header over the next unrelated block (Landmark). "Dead code is worse than no code" (CLAUDE.md No Stubbing).
  - Severity: trivial
  - Forward impact: none — comment-only; the surviving `NavigationMode`/`RoomExit`/`Region` blocks are untouched.

### Reviewer (audit)
- **TEA — Added a third test (AC5 preservation guard)** → ✓ ACCEPTED by Reviewer: fuller coverage of an explicit AC (AC5), not scope creep; the guard passes and directly defends against the plan's own stated grep-delete footgun. Good paranoia.
- **TEA — AC4 verified by CLI, not a unit test** → ✓ ACCEPTED by Reviewer: import-cleanliness + lint are toolchain/build-gate concerns; the plan itself scopes them as CLI steps (lines 100–101) and Dev ran them clean. A redundant pytest import would add no signal.
- **Dev — Also deleted the orphaned section-header comment** → ✓ ACCEPTED by Reviewer: the banner headed only the deleted classes; removing it prevents a dangling comment over the unrelated Landmark block. Confirmed the surviving blocks are untouched (`[DOC]` self-assessment).
- No undocumented deviations found: the diff matches the plan's Task 2 file list exactly (five classes + two fields + imports/`__all__`), plus the two above-logged, above-accepted additions.