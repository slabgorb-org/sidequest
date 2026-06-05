---
story_id: "82-4"
jira_key: "none"
epic: "82"
workflow: "tdd"
---
# Story 82-4: Make four-tier Resolver the production resolution path or narrow ADR-121 (consumer + provenance OTEL)

## Story Details
- **ID:** 82-4
- **Jira Key:** none
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T11:44:51Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T10:39:03.983243+00:00 | 2026-06-05T10:40:54Z | 1m 50s |
| red | 2026-06-05T10:40:54Z | 2026-06-05T10:49:28Z | 8m 34s |
| green | 2026-06-05T10:49:28Z | 2026-06-05T11:33:34Z | 44m 6s |
| review | 2026-06-05T11:33:34Z | 2026-06-05T11:41:37Z | 8m 3s |
| green | 2026-06-05T11:41:37Z | 2026-06-05T11:43:22Z | 1m 45s |
| review | 2026-06-05T11:43:22Z | 2026-06-05T11:44:51Z | 1m 29s |
| finish | 2026-06-05T11:44:51Z | - | - |

## Sm Assessment

Setup complete and gate-verified. Story 82-4 (5pts, p2, tdd/phased) targets sidequest-server only.

- **Session file:** created with workflow/phase/repo fields.
- **Story context:** `sprint/context/context-story-82-4.md` written and validated (standalone context-story file present — TEA's entry gate satisfied).
- **Branch:** `feat/82-4-resolver-four-tier-production-path` created in sidequest-server off `develop` (per repos.yaml).
- **Jira:** explicitly skipped — story carries no Jira key (consistent with sprint YAML).
- **Story status:** moved to in-progress via pf CLI.

Story shape note for TEA: this is a DECISION + FIX story — either wire `Resolver.resolve_merged` (four-tier merge, genre/resolver.py) into the production resolution path with provenance OTEL, or formally narrow ADR-121 to the two-tier shim and remove the dead path. Tests must pin the chosen path's wiring (non-test consumer), not just unit behavior. Routing to TEA (Amos Burton) for RED phase.

## TEA Assessment

**Tests Required:** Yes

**Decision recorded (AC-1):** **NARROW ADR-121 to the two-tier shim.** Code evidence:
- `Resolver`/`resolve_merged`/`resolve` have **zero** production consumers (only grep hit is the unrelated `AsideResolver`) and zero test callers.
- Content ships **no** four-tier file layout: no `{axis}.yaml` at global/genre/world tiers; culture dirs hold flat `{culture}.yaml` corpus files, not `cultures/{culture}/{axis}.yaml`.
- The production path (chargen_mixin:~391 → `archetype/shim.resolve_archetype`) merges *different schemas per tier* via pair-constrained lookup — structurally inexpressible as a `LayeredMerge` same-type document walk.
- Survivors are genuinely live: `LayeredMerge` (base of `ArchetypeResolved`), `MergeStrategy`, `_apply_strategy`, provenance wire types (`archetype_provenance` rides the wire; span events emit `source_tier`).

**Test Files:**
- `tests/genre/test_82_4_resolver_narrowing.py` (new) — 10 tests: 5 removal-contract (RED), 3 survivor guards, 2 wiring pins (runtime-identity tripwire + end-to-end provenance through the real shim)
- `tests/genre/test_resolver.py` (pruned) — removed `ResolutionContext`/`Resolved` imports + their 2 tests (symbols slated for deletion); 14 tests remain green

**Tests Written:** 10 new covering 4 ACs (decision-evidence, narrow-branch dead-code removal, wiring, observable provenance)
**Status:** RED (5 failing — confirmed by testing-runner: 44 passed / 5 failed, failures exactly the removal contract; shim + resolver regression suites fully green; no collection errors)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Stubbing / no unmarked dead code | 5 removal-contract tests (`*_removed_from_module`, `*_no_longer_exports_dead_walk`) | failing (RED) |
| Verify Wiring, Not Just Existence | `test_chargen_mixin_calls_the_shim_resolver` (runtime identity, not source grep) | passing (pin) |
| Every Test Suite Needs a Wiring Test | `test_shim_resolution_carries_tier_annotated_provenance` (end-to-end through real `resolve_archetype`) | passing (pin) |
| No Source-Text Wiring Tests | all assertions reflection/behavior-based; zero `read_text()` | self-check pass |
| OTEL Observability | provenance `source_tier` pinned here; span-event assertions already live in test_45_6 | passing (pin) |
| Py #3 type annotations at boundaries | all new tests fully annotated (`-> None`) | pass |
| Meaningful assertions (no vacuous) | every test asserts concrete values/identities; no `let _`-equivalents, no always-true | self-check pass |

**Rules checked:** 7 applicable rules covered; remaining lang-review rules (exception swallowing, mutable defaults, path handling) target prod code Dev writes — none applies to a deletion story's test surface.
**Self-check:** 0 vacuous tests found.

**Implementation notes for Dev (Naomi):**
1. Delete `Resolver`, `ResolutionContext`, `Resolved`, `_load_tier` from `sidequest/genre/resolver.py`; drop the four package exports in `sidequest/genre/__init__.py` (`__all__` + import). Module docstring should describe what remains (LayeredMerge machinery).
2. Fix stale shim docstring ("OTEL emission is omitted...") — the caller emits span events.
3. Rewrite ADR-121 in the **orchestrator repo** (narrow to two-tier shim; update frontmatter/DRIFT) — AC-3, Reviewer-verified.
4. Do NOT touch `LayeredMerge`/`MergeStrategy`/`_apply_strategy`/provenance types/`ArchetypeResolved` — survivor guards will catch over-removal.
5. Full server-test green required (AC-4).

**Handoff:** To Dev for implementation

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server, `feat/82-4-resolver-four-tier-production-path`, pushed):**
- `sidequest/genre/resolver.py` — removed `Resolver`, `ResolutionContext`, `Resolved`, `_load_tier` (the dead four-tier walk); kept `LayeredMerge`/`MergeStrategy`/`_apply_strategy`; module docstring rewritten with the 82-4 narrowing history (−255 net lines)
- `sidequest/genre/__init__.py` — dropped the three dead exports from import + `__all__`
- `sidequest/genre/archetype/shim.py` — corrected stale "OTEL emission is omitted" docstring (caller emits `character_creation.archetype_resolved`/`_failed` span events); noted shim is the production path per narrowed ADR-121

**Files Changed (orchestrator, `feat/82-4-narrow-adr-121`, pushed — AC-3):**
- `docs/adr/121-layered-content-resolution.md` — rewritten to the narrowed scope: amendment note with the audit evidence, Decision section now = merge machinery + provenance types + two-tier shim as the production path; "What was deliberately removed (82-4)" section documents the reintroduction bar (content layout + production consumer must arrive together); frontmatter `implementation-status: partial → live`, pointer updated
- `docs/adr/DRIFT.md`, `docs/adr/README.md`, `CLAUDE.md` — regenerated via `scripts/regenerate_adr_indexes.py` (ADR-121 leaves the partial/drift list)

**Tests:** 49/49 story+regression tests passing; the 5 removal-contract tests went RED→GREEN. Full server suite: 10667 passed / 344 skipped / 12 failed — **all 12 failures proven pre-existing**: re-run serially with my prod changes stashed (branch base = develop + TEA's tests), identical failure set with and without the 82-4 change. Zero regressions from this story. Lint (`ruff check`/`format`) and `pyright` clean on changed files (0 errors).
**Branch:** `feat/82-4-resolver-four-tier-production-path` (pushed); orchestrator docs on `feat/82-4-narrow-adr-121` (pushed)

**AC status:**
- AC-1 (decision recorded with code evidence): TEA's assessment + ADR-121 amendment note — NARROW
- AC-2 (if-wired branch): n/a — narrow branch taken
- AC-3 (ADR-121 rewritten, no unmarked dead code): done — dead walk deleted (not marked), ADR rewritten, indexes regenerated
- AC-4 (wiring test + full server green): wiring pins in test_82_4_resolver_narrowing.py; full suite green modulo 12 proven-pre-existing develop failures (flagged in findings)

**Handoff:** To Chrisjen (Reviewer) for code review

### Rework Round 1 (review findings — all four [LOW] fixed)

Commit `7d1319d` (pushed): (1) `ruff format` applied to `tests/genre/test_82_4_resolver_narrowing.py` — `--check` now passes; (2) `resolved.py` class docstring rewritten to "Archetype value produced by the two-tier shim (world funnel → genre fallback)"; (3) `test_resolver.py` module docstring drops `Resolved[T]`; (4) coverage cross-references added to the new test file's docstring (error paths → `test_archetype_shim.py`; production invocation + OTEL span proof → `test_45_6_chargen_archetype_gate.py`). Verification: 57/57 tests green (story files + `test_models/test_archetype.py`), `ruff check`/`format --check` clean, tree clean. No prod logic touched — docstrings and formatting only.

**Handoff (r1):** Back to Chrisjen (Reviewer)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (ruff format fail) | confirmed 1 |
| 2 | reviewer-edge-hunter | Yes | findings | 4 | confirmed 1, dismissed 2, deferred 1 |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | dismissed 1, deferred 2 |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 2, dismissed 3 |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (5 enabled returned; 4 disabled via settings)
**Total findings:** 4 confirmed, 6 dismissed (with rationale), 3 deferred

**Decisions in detail:**
- **CONFIRMED [RULE]** preflight: `ruff format --check` fails on `tests/genre/test_82_4_resolver_narrowing.py` — re-verified first-hand (`1 file would be reformatted`).
- **CONFIRMED [EDGE]** `sidequest/genre/archetype/resolved.py:18` — class docstring still says "Archetype value after four-tier resolution"; made false by this very story. Story-caused doc drift; AC-3's spirit is eliminating four-tier claims.
- **CONFIRMED [TEST]** `tests/genre/test_resolver.py:1` — module docstring still inventories `Resolved[T]`, deleted by this story.
- **CONFIRMED [TEST]** new test file should cross-reference where the missing coverage lives: error paths (forbidden pairing/unknown axis) → `test_archetype_shim.py`; production-invocation + span proof → `test_45_6_chargen_archetype_gate.py`. Two comment lines; closes the "this file reads as the full contract" gap flagged at medium confidence.
- **DISMISSED [EDGE]** shim.py:135 `<unknown>` provenance sentinel (funnels w/o world): unreachable from both production callers — chargen passes `world=sd.world_slug` always (chargen_mixin:391-399); namegen only builds `funnels` inside `if args.world:` (namegen.py:265-270). Defensive label on an impossible path; not in this diff.
- **DISMISSED [EDGE]** APPEND-on-None TypeError: failing loud on a `None` list is *correct* under No Silent Fallbacks — silently coercing `None → []` (the suggestion) would itself be a silent fallback. Pre-existing, not in diff.
- **DEFERRED [EDGE]** model_validator re-run hazard on future LayeredMerge subclasses: latent, zero current instances; noted in Delivery Findings as a docstring hardening candidate.
- **DISMISSED [SILENT]** chargen catch-and-return-None: the claim "the caller receives no signal" is factually incomplete — the Story 45-6 gate detects the partial state and **rejects the chargen commit** with typed ERROR `code="chargen_archetype_unresolved"` (chargen_mixin:368, docstring + gate tests). Loud, gated, observable.
- **DEFERRED [SILENT]** shim `fallback_name = rpg_role` silent default (shim.py:178): real No-Silent-Fallbacks tension but pre-existing and outside this diff — recorded as a Delivery Finding (content-validator/OTEL warning candidate), not a blocker for a deletion story.
- **DEFERRED [SILENT]** `extra.get("merge", "replace")` default: pre-existing; explicitly documented as a known gap with named mitigation in the rewritten ADR-121 Consequences; enforcement (`__init_subclass__`) is a new design decision out of story scope.
- **DISMISSED [TEST]** rename-residual-risk (Resolver2 would pass): accepted residual for a name-level deletion story; the ADR's reintroduction bar (consumer + content must arrive together) is the real guard; test docstring already records the contract.
- **DISMISSED [TEST]** `__all__`-check redundancy: subagent's premise is wrong — a stale `__all__` entry over a deleted attribute does NOT fail at module import, only at `from pkg import *`; the dual check catches exactly that stale-entry state. Defensive, not redundant.
- **DISMISSED [TEST]** identity-pin-not-invocation: invocation + OTEL span proof already exist in `tests/server/test_45_6_chargen_archetype_gate.py` (`test_gate_helper_has_production_consumer`, `test_evaluated_span_fires_on_ok_resolved_with_state_attr`) — suite-level wiring rule satisfied; cross-reference comment required (see confirmed finding above).

### Rule Compliance

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| No Stubbing / dead code worse than no code | `Resolver`/`ResolutionContext`/`Resolved`/`_load_tier` fully deleted, not marked; runtime check shows no dead syms in package | compliant |
| No Silent Fallbacks | Removal eliminates a loud-failure surface, introduces no fallback; survivor `"replace"` default + shim `fallback_name` default are pre-existing, documented in ADR, deferred | compliant (in-diff) |
| Verify Wiring / Wiring Test | identity tripwire + end-to-end shim drive in new file; production invocation + span proof in test_45_6 | compliant |
| No Source-Text Wiring Tests | all new assertions reflection/identity/behavior-based; zero `read_text()` on prod source | compliant |
| OTEL Observability | no subsystem wired (deletion); existing `character_creation.archetype_resolved` span is the surface, pinned by tests; ADR Observability section rewritten to name it | compliant |
| Py #1 silent exceptions | no new try/except in diff | compliant |
| Py #2 mutable defaults | no new defs with mutable defaults | compliant |
| Py #3 annotations at boundaries | all new test functions annotated; prod diff is deletions | compliant |
| Py #6 test quality | no vacuous assertions found by analyzer or me; 2 doc-accuracy items confirmed | compliant w/ confirmed LOW fixes |
| Py #8 unsafe deserialization | 3× `yaml.safe_load` on inline literals in tests; removed `_load_tier` used safe_load; no degradation [SEC clean] | compliant |
| Py #10 import hygiene | `__all__` updated in lockstep with imports; verified at runtime | compliant |

### Review Observations

1. **[VERIFIED]** Package export integrity — `python -c` runtime check: every `__all__` name resolves (`missing exports: NONE`), no dead symbols (`dead syms present: NONE`). Complies with Py #10 + No Stubbing.
2. **[VERIFIED]** Error types not orphaned — `GenreLoadError`/`SchemaValidationError` retain 62 references; `loader.py:103-141` still raises both. Removal stranded nothing.
3. **[VERIFIED]** Data flow traced — player raw pair → `_resolve_character_archetype` (chargen_mixin:391) → axis validation (shim.py:99-102, loud `GenreValidationError` on unknown ids) → forbidden-pair rejection (shim.py:109-114) → `apply_archetype_resolved` lockstep provenance → `archetype_provenance` rides the wire (`protocol/models.py` references `Provenance` directly from `protocol.provenance`, NOT through deleted `Resolved` — no wire regression) [SEC].
4. **[VERIFIED]** In-flight branch safety — fetched and diffed both live sister-clone branches (`feat/83-2-culture-self-match-named-people-group`, `feat/87-2-wwn-classes-chargen`) against develop: zero references to the deleted symbols. The deletion cannot break their rebases.
5. **[VERIFIED]** ADR-121 rewrite quality — amendment note carries the audit evidence; Decision section now matches the code I reviewed (shim as production path, machinery + provenance as survivors); frontmatter `partial → live` is accurate post-deletion; DRIFT/README/CLAUDE.md regenerated consistently (ADR-121 absent from drift table). Title-vs-H1 mismatch matches existing corpus convention (ADR-118/120 use short H1s).
6. **[RULE]** `ruff format --check` fails on the new test file — must be formatted before the PR exists.
7. **[EDGE]** `resolved.py:18` stale "four-tier resolution" docstring — story-caused.
8. **[TEST]** `test_resolver.py:1` stale `Resolved[T]` docstring inventory — story-caused.

### Devil's Advocate

Assume this deletion is broken. The nastiest failure mode for removing a public symbol is a consumer I can't grep: dynamic import, string-keyed registry, or serialized class path. I checked all three — no `import_module`/`getattr` resolution against `sidequest.genre` for these names, no registry entries, and old saves can't rehydrate `Resolved`: `archetype_provenance` on the wire model references `protocol.provenance.Provenance` directly, and Postgres saves store provenance as plain JSON validated against that unchanged type. Second attack: a live branch in a sister clone mid-flight that imports the walk — real risk in this dual-clone shop, so I fetched and diffed both active branches (83-2, 87-2): zero hits. Third: the ADR rewrite could overclaim — saying "live" while something is still drifting. I re-read the regenerated DRIFT table; ADR-121 is gone from it, and the narrowed claims match code I verified line-by-line. Fourth: the survivor guards could be hollow — but `test_layered_merge_machinery_survives_narrowing` asserts actual merge *behavior* (replace + append outcomes), not importability. What the devil actually found: the story's own hygiene standard isn't fully met by the story itself — it rewrites ADR-121 and the shim docstring to kill the four-tier claim, yet leaves "after four-tier resolution" sitting on the *one surviving subclass* (`resolved.py:18`) and a deleted symbol in a test module's inventory docstring. Plus an unformatted file that fails the repo's own format gate. None of this is dangerous; all of it is exactly the class of drift this epic exists to eliminate. Fix it now, while the context is hot.

## Reviewer Assessment r1 (REJECTED — superseded by r2 below)

**Verdict (r1, superseded):** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW] | `ruff format --check` fails on new test file | `tests/genre/test_82_4_resolver_narrowing.py` | `uv run ruff format tests/genre/test_82_4_resolver_narrowing.py` |
| [LOW] | Stale "four-tier resolution" class docstring — made false by this story | `sidequest/genre/archetype/resolved.py:18` | Reword to two-tier shim reality (e.g. "Archetype value produced by the two-tier shim (world funnel → genre fallback) on the LayeredMerge framework.") |
| [LOW] | Stale module docstring inventories deleted `Resolved[T]` | `tests/genre/test_resolver.py:1` | Drop the `Resolved[T]` mention |
| [LOW] | New test file presents as the narrowed contract but doesn't point at the error-path and production-invocation coverage | `tests/genre/test_82_4_resolver_narrowing.py` (file docstring) | Add cross-reference comment: error paths → `test_archetype_shim.py`; production invocation + OTEL span proof → `test_45_6_chargen_archetype_gate.py` |

**Nature of rejection:** format/docs-only — no Critical/High, no logic, no test-semantics changes. Route: **green rework to Dev** (per lint/format-only rule), not TEA. The substance of the story — the decision, the evidence, the deletion, the test design, the ADR rewrite — is excellent work; the rejection is strictly "finish wiping the fingerprints": this story's purpose is eliminating false four-tier claims, and two survive in docstrings it owns.

**Data flow traced:** player chargen pair → axis validation → forbidden-pair gates → shim resolution → lockstep provenance apply → wire (`archetype_provenance` via `protocol.provenance`, untouched by deletion — safe because the deleted `Resolved` wrapper was never on the wire path)
**Pattern observed:** correct deletion hygiene at `sidequest/genre/__init__.py:74-79` — import block and `__all__` pruned in lockstep, verified at runtime, with the removal annotated in the `__all__` comment
**Error handling:** removal eliminates `GenreLoadError`/`SchemaValidationError` raisers in `resolver.py`; both types remain live via `loader.py:103-141`; shim failure path is loud (`GenreValidationError`) and the 45-6 gate converts partial state into a typed, blocking ERROR frame (chargen_mixin:368)
**Handoff (r1):** Back to Dev (Naomi) for the four [LOW] mechanical fixes; expedited re-review on return

## Reviewer Assessment

**Verdict:** APPROVED

**Round 2 — rework verification (commit `7d1319d`, verified first-hand, not from Dev's claims):**
- [RULE] `ruff format --check` now passes on `tests/genre/test_82_4_resolver_narrowing.py` — fixed.
- [EDGE] `resolved.py:18` now reads "Archetype value produced by the two-tier shim (world funnel → genre fallback)" — the last false four-tier claim is gone.
- [TEST] `test_resolver.py:1` docstring no longer inventories deleted `Resolved[T]` — fixed.
- [TEST] Coverage cross-references added (error paths → `test_archetype_shim.py`; production invocation + OTEL span proof → `test_45_6_chargen_archetype_gate.py`) — fixed.
- Rework diff audited: 3 files, +12/−5, docstrings and formatting only; the sole prod-file change is one docstring line (verified by filtering the diff for non-docstring lines — empty). 49/49 story tests green.

**Round 1 findings basis (full fan-out, carried forward):** [EDGE] edge-hunter 4 findings (1 confirmed→fixed, 2 dismissed with line-level evidence, 1 deferred); [SILENT] silent-failure-hunter 3 (1 dismissed — the 45-6 gate emits a typed blocking ERROR `chargen_archetype_unresolved`, chargen_mixin:368; 2 deferred to Delivery Findings); [TEST] test-analyzer 5 (2 confirmed→fixed, 3 dismissed with rationale); [SEC] security clean (yaml.safe_load only, no wire regression — `archetype_provenance` references `protocol.provenance.Provenance` directly, never the deleted `Resolved`); [DOC] comment-analyzer disabled via settings — doc-accuracy covered by my own pass (3 stale-docstring catches, all fixed); [TYPE] type-design disabled — type surface is pure deletion, runtime export check passed; [SIMPLE] simplifier disabled — the diff IS a simplification (−255 net prod lines); [RULE] rule-checker disabled — Rule Compliance table above covers the 11 applicable rules, all compliant.

**Verdict rationale:** Decision (NARROW) independently re-verified on all three evidence legs; deletion clean at runtime; in-flight branches (83-2, 87-2) unaffected; ADR-121 rewrite accurate and indexes regenerated; wiring + observability pinned; zero regressions (12 full-suite failures proven pre-existing via stash baseline). No Critical/High at any point; all four r1 [LOW]s fixed and verified.

**Data flow traced:** player chargen pair → axis validation (loud) → forbidden-pair gates (loud) → shim resolution → lockstep provenance apply → `archetype_provenance` on the wire (safe because the deleted wrapper was never on the wire path)
**Pattern observed:** lockstep import/`__all__` pruning with runtime verification at `sidequest/genre/__init__.py:74-77`
**Error handling:** shim failures raise typed `GenreValidationError`; chargen converts partial state to typed blocking ERROR via the 45-6 gate; no swallowed paths introduced
**Handoff:** To SM for finish-story — **two branches to PR/merge:** server `feat/82-4-resolver-four-tier-production-path` (base develop) + orchestrator `feat/82-4-narrow-adr-121` (base main)

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The shim module docstring claims "OTEL emission is omitted in this Python port" but the production caller (`chargen_mixin._resolve_character_archetype`) emits `character_creation.archetype_resolved`/`archetype_resolution_failed` span events. Affects `sidequest/genre/archetype/shim.py` (stale docstring line ~11 — correct it during the 82-4 cleanup). *Found by TEA during test design.*
- **Gap** (non-blocking): The ADR-121 rewrite (narrow to two-tier shim) is an orchestrator-repo docs deliverable (`docs/adr/121-layered-content-resolution.md` + DRIFT.md/frontmatter) — not testable from the server suite; Reviewer must verify it landed. Affects `docs/adr/121-layered-content-resolution.md` (rewrite to describe the shim as production reality; drop the four-tier "live" claim). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (blocking — for develop, not this story): 12 pre-existing test failures on current `develop`, proven unrelated to 82-4 (identical failure set with the 82-4 prod changes stashed). Affects `tests/protocol/test_enums.py::test_message_type_complete_count`, `tests/agents/test_61_12_output_format_compaction.py::test_output_only_prose_under_byte_budget`, `tests/server/test_narration_clue_discovery_wiring.py` (5), `tests/agents/tools/test_apply_world_patch.py::test_active_stakes_path_applies`, `tests/server/test_yield_handler_outbound.py::test_yield_multi_pc_partial_emits_active_confrontation`, plus 3 more (likely introduced by a recent develop merge — #678/#681/#682 window; needs a patch story or owner-session fix). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_genre_fallback` silently substitutes the raw `rpg_role` id as the archetype display name when `constraints.fallback_name(rpg_role)` is unconfigured — a content author gets archetypes named after raw role ids with no warning. Affects `sidequest/genre/archetype/shim.py:171-173` (emit an OTEL warning event, e.g. `archetype_fallback_unconfigured`, or add a pack-validator check that every rpg_role has a `fallback_name`). Pre-existing; out of 82-4 scope. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `LayeredMerge.merge` reconstructs via `type(self)(**merged)`, which would re-run any future subclass's `model_validator` on already-merged data, and undeclared merge strategies silently default to `replace` — both latent (sole subclass is clean + wired-tested) and documented in ADR-121 Consequences; consider `__init_subclass__` declaration enforcement if a second LayeredMerge subclass ever lands. Affects `sidequest/genre/resolver.py` (LayeredMerge docstring/load-time check). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Decision branch selected: NARROW (not wire) — tests pin removal, not four-tier wiring**
  - Spec source: context-story-82-4.md, AC-1/AC-2/AC-3 ("either route production resolution through Resolver.resolve_merged ... OR formally narrow ADR-121")
  - Spec text: "A decision is recorded (with code evidence): adopt the four-tier Resolver as the production path, or narrow ADR-121 to the two-tier shim."
  - Implementation: RED tests enforce the NARROW branch — removal contract for `Resolver`/`ResolutionContext`/`Resolved`/`_load_tier` + survivor guards + shim wiring pins. No tests drive `resolve_merged` into production.
  - Rationale: code evidence is one-sided — zero production/test consumers of the walk; no genre pack ships `{axis}.yaml` tier files at any tier (cultures are flat `{name}.yaml` corpus files); the shim's tiers are different schemas (base/constraints/funnels) doing pair-constrained lookup, which `LayeredMerge` same-type merge cannot express. Wiring would require a content redesign across 11 packs — far beyond 5 points and would create stub infrastructure with no data (No Stubbing).
  - Severity: minor (the AC explicitly authorizes this branch; "deviation" is the branch selection itself)
  - Forward impact: Dev deletes the four symbols + package exports, corrects the stale shim docstring, and rewrites ADR-121 in the orchestrator repo. The wiring-test AC clause "fails on current code if the four-tier path is chosen" is moot on the narrow branch — RED is supplied by the 5 removal-contract tests instead.
- **No new OTEL emission required — existing span events are the observable surface**
  - Spec source: context-epic-82.md, Conventions ("every story emits OTEL/watcher events for the subsystem decision it wires")
  - Spec text: "every story emits OTEL/watcher events for the subsystem decision it wires (OTEL Observability Principle)"
  - Implementation: tests pin the already-emitting surface (`character_creation.archetype_resolved` span event with `source`/`source_tier`/`weight` attrs, asserted in tests/server/test_45_6_chargen_archetype_gate.py; provenance shape pinned in test_82_4_resolver_narrowing.py) rather than requiring a new emission.
  - Rationale: the narrow branch wires no new subsystem — it removes a dead one. The decision's observable is the shim's existing tier-annotated provenance + span events, which are already GM-visible. Adding a duplicate emission would be noise.
  - Severity: minor
  - Forward impact: none — if Reviewer disagrees, a `resolver.narrowed` one-shot span at load time is the natural addition.

### Dev (implementation)
- **ADR-121 retitled and re-statused as part of the rewrite**
  - Spec source: context-story-82-4.md, AC-3
  - Spec text: "ADR-121 is rewritten to describe the two-tier shim as the production reality and resolve_merged is removed or explicitly marked non-production (no unmarked dead code)"
  - Implementation: beyond the body rewrite, frontmatter title changed (drops "Global→Genre→World→Culture Merge") and `implementation-status` flipped `partial → live`; DRIFT.md/README/CLAUDE.md indexes regenerated via `scripts/regenerate_adr_indexes.py`, removing ADR-121 from the drift list. Orchestrator changes shipped on a separate branch `feat/82-4-narrow-adr-121` (story REPOS field lists only sidequest-server; orchestrator docs follow the established docs-PR path).
  - Rationale: leaving status `partial` with a pointer to 82-4 would be stale the moment 82-4 merges; the narrowed ADR accurately describes a fully live system, and ADR-088 makes frontmatter the index source of truth, so the title must reflect the narrowed claim.
  - Severity: minor
  - Forward impact: Reviewer must review/merge two PR-able branches (server + orchestrator); SM finish flow should reference both.
- **Removal chosen over "explicitly marked non-production"**
  - Spec source: context-story-82-4.md, AC-3 ("removed or explicitly marked non-production")
  - Spec text: "resolve_merged is removed or explicitly marked non-production (no unmarked dead code)"
  - Implementation: full deletion of `Resolver`/`ResolutionContext`/`Resolved`/`_load_tier` (the AC's first option), per TEA's RED contract.
  - Rationale: project principle "Dead code is worse than no code" + user's standing weed-whack preference; marking would preserve 280 lines of unreachable code behind a comment.
  - Severity: minor (AC-sanctioned option)
  - Forward impact: none — recoverable from git history / Rust reference repo; reintroduction bar documented in the ADR amendment.

### Reviewer (audit)
- **TEA: Decision branch selected NARROW (not wire)** → ✓ ACCEPTED by Reviewer: independently re-verified all three evidence legs (zero consumers via runtime + grep; no four-tier content layout; heterogeneous per-tier schemas) — the evidence is one-sided and the AC explicitly authorizes the branch.
- **TEA: No new OTEL emission required** → ✓ ACCEPTED by Reviewer: the deletion wires no subsystem; existing `character_creation.archetype_resolved` span events + wire provenance are the observable surface, and the rewritten ADR-121 Observability section now names them as such. A duplicate emission would be noise.
- **Dev: ADR-121 retitled and re-statused as part of the rewrite** → ✓ ACCEPTED by Reviewer: leaving `partial` + a pointer at a finished story would be instant drift; verified the regenerated DRIFT table no longer lists ADR-121 and the new title matches the narrowed claim. Title-vs-H1 short form matches corpus convention (ADR-118/120).
- **Dev: Removal chosen over "explicitly marked non-production"** → ✓ ACCEPTED by Reviewer: AC-sanctioned first option; runtime check proves clean removal; in-flight branches (83-2, 87-2) verified untouched by the deletion.