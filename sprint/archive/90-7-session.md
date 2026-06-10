---
story_id: "90-7"
jira_key: ""
epic: "90"
workflow: "tdd"
---
# Story 90-7: WWN scene-harness hydrator — add the dropped Effort half

## Story Details
- **ID:** 90-7
- **Jira Key:** (not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server, content
- **Branch Strategy:** gitflow
  - **Server Branch:** feat/90-7-wwn-effort-hydrator
  - **Content Branch:** feat/90-7-wwn-effort-hydrator

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-10T11:50:55Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T11:32:09Z | 2026-06-10T11:34:05Z | 1m 56s |
| red | 2026-06-10T11:34:05Z | 2026-06-10T11:42:01Z | 7m 56s |
| green | 2026-06-10T11:42:01Z | 2026-06-10T11:46:16Z | 4m 15s |
| review | 2026-06-10T11:46:16Z | 2026-06-10T11:50:55Z | 4m 39s |
| finish | 2026-06-10T11:50:55Z | - | - |

## Sm Assessment

**Story:** 90-7 — WWN scene-harness hydrator. Add the *dropped Effort half* on top of #787's spellcasting-only 90-4. #787 shipped `prepared`/spellcasting + `hp_depletion` hydration but omitted (a) Effort-pool hydration and (b) the GM-panel lie-detector OTEL span.

**What "done" means:**
1. The scene-harness hydrator (ADR-092 dev-gated fixture endpoint) seeds per-character `core.effort` as a **source-keyed `EffortPool`** — the effort block is a source-keyed mapping, `EffortPool.source` derived from the key.
2. Hydration emits a `wwn.magic_hydrated` OTEL span — the lie-detector that proves Effort actually got seeded (per CLAUDE.md OTEL Observability Principle; this is the dev/GM-panel verification surface, not a player feature).
3. **Loud-fail on malformed** effort input — no silent fallback (Development Principles: No Silent Fallbacks).

**Reference implementation:** oq-1's **closed PR #788** is the worked solution + tests. TEA/Dev should mine it for the test shape and the EffortPool source-keying contract — but verify against current `develop` (it was a different clone; APIs may have drifted).

**Why it matters:** Keystone for 90-3's live free-play OTEL proof — a caster can't fire `wwn.spell.cast` in the live proof without Effort seeded first. Serves the Sebastien/Jade "crunch must fire and be legible" requirement, but note the OTEL span here is a **dev/GM-panel** surface, not a Sebastien-facing one.

**Repos:** server (hydrator + OTEL per ADR-092/ADR-126), content (rules/world YAML only if the effort block needs authoring support).

**Routing:** Phased TDD. Next phase RED → The Architect (TEA) writes failing tests covering the three "done" conditions above (Effort seeded + source-keyed, span emitted, loud-fail on malformed).

## TEA Assessment

**Tests Required:** Yes
**Reason:** New per-character hydration branch + new OTEL span — both behavioral, both save-bearing.

**Test Files:**
- `sidequest-server/tests/game/test_scene_harness_hydrator.py` — appended a "Story 90-7" section (12 tests) after the 50-21 encounter tests.

**Tests Written:** 12 tests covering 6 self-defined ACs (story had none).
**Status:** RED — 10 drivers failing, 2 backward-compat guards passing (by design).

### AC → Test map

| AC | Test(s) | RED status |
|----|---------|-----------|
| AC-1 effort→core.effort (source-keyed) | `test_character_effort_block_hydrates`, `test_multiple_effort_sources_hydrate_independently` | failing |
| AC-2 backward-compat default `{}` | `test_missing_effort_block_leaves_core_effort_empty_dict` | **passing (guard)** |
| AC-3 source from key, not in-value | `test_effort_source_derived_from_key_not_in_value` | failing |
| AC-4 loud-fail on malformed | `test_effort_block_not_a_mapping_raises`, `test_effort_pool_value_not_a_mapping_raises`, `test_effort_pool_bad_field_type_raises`, `test_effort_pool_extra_field_rejected` | failing |
| AC-5 multi-PC list path, no bleed | `test_effort_hydrates_under_multi_pc_characters_list` | failing |
| AC-6 wwn.magic_hydrated span (spellcasting OR effort; no non-caster noise) | `test_effort_hydration_emits_wwn_magic_hydrated_span`, `test_spellcasting_hydration_emits_wwn_magic_hydrated_span`, `test_non_caster_emits_no_wwn_magic_hydrated_span` | 2 failing + 1 passing (no-noise guard) |

### Rule Coverage (lang-review / CLAUDE.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks / ADR-092 "Failure is loud" (#1/#11) | 4 loud-fail tests above | failing |
| ValidationError re-wrapped at module boundary (no leak) | `test_effort_pool_bad_field_type_raises`, `test_effort_pool_extra_field_rejected` | failing |
| OTEL span assertion as wiring test (No Source-Text Wiring Tests) | 3 span tests via `_capture_wwn_events` (monkeypatch `_hub.publish_event`) | 2 failing |
| Backward-compat regression lock | `test_missing_effort_block_…`, `test_non_caster_emits_no_…` | passing |

**Rules checked:** 4 applicable rules have test coverage.
**Self-check:** 0 vacuous tests. Every test asserts specific values (pool.source/max/available, span field contents, exception-naming). The 2 passing guards assert real invariants, not tautologies.

**The wiring test (mandatory):** AC-6's span tests drive the real `hydrate_fixture` through the real `_hub.publish_event` handle and assert the emission — the refactor-stable OTEL pattern CLAUDE.md mandates over source-text grep. (The heavier end-to-end "hydrated effort actually fuels a cast" proof belongs to 90-3's live run, out of this story's scope.)

**Implementation pointer for Dev (Agent Smith):** oq-1 closed PR #788 is the worked solution — `gh pr diff 788 --repo slabgorb/sidequest-server`. The effort branch goes in `_hydrate_character` (sidequest/game/scene_harness.py, after the spellcasting block ~line 334): read `data.get("effort")`, validate dict-of-dicts, build `EffortPool(source=str(key), **{k:v for k,v in pool if k!="source"})` into `core_kwargs["effort"]`. The span goes AFTER `core = CreatureCore(**core_kwargs)`, guarded on `core.spellcasting is not None or core.effort`, emitting `actor/has_spellcasting/prepared/casts_per_day/effort_sources=sorted(core.effort)` via module-qualified `_hub.publish_event(..., component="magic", severity="info")`. Add the `EffortPool` import alongside the existing `SpellcastingState` import.

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/scene_harness.py` — (1) added `EffortPool` to the `wwn_magic` import; (2) effort-hydration branch in `_hydrate_character` after the spellcasting block — reads `data.get("effort")`, validates the source-keyed mapping, builds `EffortPool(source=str(key), **{strip in-value source})` into `core_kwargs["effort"]`, loud-fails on every malformed shape; (3) `wwn.magic_hydrated` span after `core` construction, guarded on `core.spellcasting is not None or core.effort`, via module-qualified `_hub.publish_event(..., component="magic")`.

**Tests:** 12/12 GREEN (the 10 RED drivers now pass; the 2 backward-compat guards stay green). Full hydrator file: 125/125. ruff clean, pyright 0 errors.
**Branch:** feat/90-7-wwn-effort-hydrator (commits f73ed043 test + 421831fe impl — local, not yet pushed)

**Followed the test contract exactly** — no extra abstraction. The effort branch mirrors the existing spellcasting branch's loud-fail idiom; the span mirrors the existing `magic.state_hydrated` emitter convention.

**Pre-existing failure (NOT a regression):** `tests/server/test_scene_listing.py::test_scene_harness_post_works_without_dev_scenes_env` fails in this shell with `MissingDatabaseUrlError: SIDEQUEST_DATABASE_URL is not set` (ADR-115 Postgres substrate). Verified it fails identically with my diff stashed — it is an unprovisioned-DB env issue (`just pg-up` not run here), not related to 90-7. The route it exercises is a non-caster fixture, so my span guard never fires on that path.

**Handoff:** To next phase (verify — The Architect).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (125 file tests GREEN, ruff+pyright clean, 0 smells) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (covered by Reviewer directly — see Rule Compliance #6) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A (yaml.safe_load, no injection, no info-leak, dev-gated — all rules compliant) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (lang-review enumerated by Reviewer — see Rule Compliance) |

**All received:** Yes (2 enabled returned, both clean; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 confirmed (Reviewer's own edge-hunt — MEDIUM, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict: APPROVED** — no Critical/High findings. One MEDIUM (non-blocking, documented as a delivery finding + recommended fast-follow).

The diff is small and disciplined (55 lines of source, 391 of tests): an `effort:` hydration branch mirroring the existing spellcasting branch's loud-fail idiom, and a `wwn.magic_hydrated` span mirroring the existing `magic.state_hydrated` emitter. Both subagents returned clean. My own adversarial edge-hunt found one robustness gap (below).

### Observations

- **[MEDIUM][EDGE] Non-string YAML key under a pool leaks a raw `TypeError` past the module boundary — `scene_harness.py:362`.** `EffortPool(source=str(source), **pool_kwargs)` where `pool_kwargs` came from `yaml.safe_load` can contain non-string keys (`high_mage:\n  1: foo` → `{1: 'foo'}`). `**{1: 'foo'}` raises `TypeError: keywords must be strings`, which the `except ValidationError` does NOT catch → it propagates as a raw `TypeError` → HTTP 500, violating the module's stated contract that malformed input fails loud as `FixtureValidationError` → HTTP 422 (ADR-092 "Failure is loud"). **Verified empirically** (probe leaked `TypeError: keywords must be strings`). *Not a silent fallback — it does fail loudly and ships no broken data, which is why severity is MEDIUM not High.* **The sibling spellcasting branch (`scene_harness.py:331`, shipped in #787) has the IDENTICAL gap** (verified — spellcasting probe also leaked TypeError), so this is a pre-existing module-wide pattern my diff faithfully mirrors rather than a novel regression. Cheap module-wide fix: broaden both branches' `except ValidationError` → `except (ValidationError, TypeError)`. Recommended as a fast-follow, not a blocker for 90-7.
- **[VERIFIED] Effort source is authoritative from the key — `scene_harness.py:360-362`.** `pool_kwargs` strips any in-value `source` (`{k: v for k, v in pool_raw.items() if k != "source"}`) and passes `source=str(source)`, so a fixture cannot make the cast-time `core.effort.get(source)` lookup diverge. Covered by `test_effort_source_derived_from_key_not_in_value`. Complies with No-Silent-Fallbacks (the divergence it prevents would be a silent cast-time miss).
- **[VERIFIED] Span fires only on real crunch — `scene_harness.py:378`.** Guard `if core.spellcasting is not None or core.effort:` — `core.effort` is a dict, empty is falsy, so non-casters emit nothing. Covered by `test_non_caster_emits_no_wwn_magic_hydrated_span`. No GM-panel noise on canonical dial fixtures.
- **[VERIFIED] Loud-fail on the three documented malformed shapes — `scene_harness.py:348-366`.** Non-mapping block (348), non-mapping pool value (355), bad field type / extra=forbid typo via re-wrapped `ValidationError` (363). Four tests cover these. (The fourth shape — non-string key — is the MEDIUM above.)
- **[VERIFIED] No new deserialization/path/injection surface — `scene_harness.py:346-390`.** The effort branch reads the already-`safe_load`ed `data` dict (parse at line 109); adds no `yaml.load`, no path ops, no string interpolation into queries/shells. `core.name`/`effort_sources` in the span come from the hydrated `CreatureCore`, flow only to the watcher hub (not the client), endpoint is dev-gated. Concurs with reviewer-security's clean result.
- **[VERIFIED] Tests are non-vacuous — `tests/game/test_scene_harness_hydrator.py`.** Every test asserts specific values (`pool.source`/`max`/`available`, span field contents, exception-message naming). The 2 backward-compat guards assert real invariants (`core.effort == {}`, no span emitted) — they would catch a fabricated-pool or always-emit regression, not tautologies.

### Rule Compliance (lang-review/python.md)

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| #1 Silent exception swallowing | 2 `except ValidationError` blocks (352-366, both re-raise as FixtureValidationError) | Compliant — no swallow; both re-raise loud. (Edge: TypeError not in the catch set — the MEDIUM above.) |
| #3 Type annotations at boundaries | `effort: dict[str, EffortPool]` (353); `_hydrate_character` already annotated | Compliant |
| #6 Test quality | 12 new tests | Compliant — specific assertions, no `assert True`, no skips, no truthy-only checks |
| #8 Unsafe deserialization | none added (reads pre-parsed dict) | Compliant — `yaml.safe_load` at :109 |
| #11 Input validation at boundaries | effort block dict/dict-of-dict validation (348-366) | Compliant (modulo the non-string-key edge) |
| #4 Logging/OTEL | `wwn.magic_hydrated` span, `severity="info"` (389) | Compliant — input-staging event correctly classified `info`, no sensitive data |

### Tags Summary

`[EDGE]` 1 confirmed (Reviewer's own hunt) · `[SEC]` clean (subagent) · `[SILENT]` N/A disabled · `[TEST]` clean (Reviewer direct, Rule #6) · `[DOC]` N/A disabled · `[TYPE]` N/A disabled · `[SIMPLE]` N/A disabled · `[RULE]` clean (Reviewer enumerated lang-review above)

### Devil's Advocate

Let me argue this code is broken. The most promising attack is the `**pool_kwargs` splat — and I found real blood there: a fixture author who writes a YAML integer or boolean key under a pool (`high_mage:\n  1: foo`, or worse a deeply-nested typo) gets an opaque HTTP 500 with a Python `TypeError`, not the clean 422 the whole module promises. A dev staging a deterministic WWN proof would burn time debugging "why is the scene harness 500-ing" when the real answer is a one-character YAML typo — exactly the "hours of debugging why isn't this quite right" the No-Silent-Fallbacks rule exists to prevent. So the contract *is* dented. What saves it from High is that it still fails — nothing broken is hydrated, no caster ships without effort, no silent pass — and the identical behavior already lives in the shipped spellcasting sibling, so 90-7 doesn't regress the baseline. Next: could `commitments` be abused? `EffortPool` accepts a `commitments` list; a fixture could seed `commitments` so `available < max` at hydration. That's untested by 90-7 but it's a *feature* (pre-committed effort), not a bug, and `extra="forbid"` plus the nested `EffortCommitment` model bound its shape. Could the span lie? It reports `len(core.spellcasting.prepared)` and `sorted(core.effort)` straight off the constructed core — if hydration silently dropped a source, the span would under-report and the GM panel would catch the discrepancy, which is the lie-detector working as designed. Could a confused author key two sources that collide? Dict keys are unique by construction; a duplicate YAML key is resolved by `safe_load` before we see it. Could huge input DoS it? The endpoint is dev-gated, single-user, no loop over unbounded external data beyond the fixture the dev wrote. Net: one genuine robustness dent (the TypeError), everything else holds.

### Deviation Audit

- **TEA: "Story has no written ACs; tests serve as the executable AC set."** → ✓ ACCEPTED by Reviewer: the 6 derived ACs faithfully track the story title + the cited oq-1 PR #788; reasonable in the absence of YAML ACs (spec-authority hierarchy — story scope wins).
- **TEA: "Span-emission scope widened to the existing spellcasting path."** → ✓ ACCEPTED by Reviewer: correct call — a lie-detector that covered only effort would leave #787's spellcasting-only fixtures unverifiable. Additive (no existing test asserted span absence); `test_spellcasting_hydration_emits_wwn_magic_hydrated_span` locks it in.
- **Dev: "No deviations from spec."** → ✓ ACCEPTED by Reviewer: implementation matches the test contract and TEA's prescribed span placement; verified at `scene_harness.py:346-390`.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): `wwn.magic_hydrated` is not yet in the OTEL extractor allow-list (`sidequest/telemetry/spans/`), so the GM panel won't surface it even once emitted. Affects `sidequest/telemetry/spans/` (register the new span for GM-panel display). *Found by TEA during test design.* (Same gap #788 flagged.)
- **Gap** (non-blocking): no committed fixture under `scenarios/fixtures/` exercises the `effort:` block — coverage is unit-test-only. A follow-on should author a `combat_wwn_*.yaml` fixture so 90-3's live proof has a deterministic on-disk artifact. Affects `scenarios/fixtures/`. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. (TEA's two findings stand; I confirmed `wwn.magic_hydrated` is absent from `sidequest/telemetry/spans/` — registering it for the GM panel is correctly out of this story's test contract and belongs to the follow-on TEA flagged.)

### Reviewer (audit)
- **Improvement** (non-blocking): a non-string YAML key under an effort pool (or a spellcasting block) leaks a raw `TypeError: keywords must be strings` past the module boundary instead of the contracted `FixtureValidationError` (HTTP 500 vs 422). Affects `sidequest/game/scene_harness.py` (broaden both the effort branch's `except ValidationError` at ~:363 AND the sibling spellcasting branch's at ~:332 to `except (ValidationError, TypeError)`). Pre-existing in the spellcasting branch since #787; 90-7 mirrors it. Cheap module-wide fix worth a fast-follow chore. *Found by Reviewer during review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Story has no written ACs; tests serve as the executable AC set.**
  - Spec source: context-story-90-7.md, "Acceptance Criteria" ("_No acceptance criteria recorded… TEA to define during the RED phase._")
  - Spec text: story title — "seed per-character core.effort (source-keyed EffortPool) and emit wwn.magic_hydrated OTEL"
  - Implementation: Defined 6 ACs (AC-1 effort hydration, AC-2 backward-compat default, AC-3 source-from-key, AC-4 loud-fail, AC-5 multi-PC path, AC-6 span) from the title + oq-1 PR #788 reference; 12 tests encode them.
  - Rationale: No AC text existed to test against; the title + cited reference PR are the authority (spec-authority hierarchy: story scope wins).
  - Severity: minor
  - Forward impact: Dev implements to the test contract; Reviewer should sanity-check ACs against the title, not a written list.
- **Span-emission scope widened to the existing spellcasting path.**
  - Spec source: story title — "emit wwn.magic_hydrated OTEL"
  - Spec text: the span is described as the Effort half's lie-detector.
  - Implementation: `test_spellcasting_hydration_emits_wwn_magic_hydrated_span` requires the span to ALSO fire for #787's spellcasting-only fixtures (the emit condition is `spellcasting is not None OR effort`), matching PR #788's worked impl.
  - Rationale: The lie-detector must cover ALL WWN crunch, not just effort, or a spellcasting-only deterministic fixture stays unverifiable. This makes spellcasting-only fixtures newly emit the span — additive, no existing test asserts its absence.
  - Severity: minor
  - Forward impact: Dev must place the emit after `core` construction guarding on `spellcasting is not None or effort`, not inside the effort branch only.

### Dev (implementation)
- No deviations from spec. Implemented to the test contract exactly: effort branch mirrors the spellcasting loud-fail idiom, span placed after `core` construction guarded on `core.spellcasting is not None or core.effort` (as TEA's deviation #2 prescribed), source derived from the mapping key with stray in-value `source` stripped.