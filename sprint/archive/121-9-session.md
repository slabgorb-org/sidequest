---
story_id: "121-9"
jira_key: "121-9"
epic: "121"
workflow: "trivial"
---
# Story 121-9: F4b test-template hardening

## Story Details
- **ID:** 121-9
- **Jira Key:** 121-9
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-16T02:01:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T01:43:09Z | 2026-06-16T01:44:28Z | 1m 19s |
| implement | 2026-06-16T01:44:28Z | 2026-06-16T01:54:18Z | 9m 50s |
| review | 2026-06-16T01:54:18Z | 2026-06-16T02:01:10Z | 6m 52s |
| finish | 2026-06-16T02:01:10Z | - | - |

## Sm Assessment

**Story:** 121-9 — F4b test-template hardening (server-only, trivial, 2pts).

**Why now:** F4c–F4e (121-3/4/5) will copy the F4b test template across three Fate-pack migrations. Hardening the template *before* it propagates prevents weak/tautological assertions from being duplicated three times. This is the correct sequencing — gate the copies, then do them.

**Scope (from 121-2 Reviewer findings):**
- Strengthen AC5 into a real `fate.chargen.seeded` OTEL wiring assertion (InMemorySpanExporter + injected `_tracer`, against real pulp_noir content).
- De-tautologize `test_fate_sheet_skills_match_pack_config` by pinning a concrete value (e.g. `Investigate == 4`) so a seed truncate/reorder is caught.
- AC4: also assert the BUILT character has no d20 attribute pool (not just pack config).
- Give `_load_pack` / `_build_pulp_noir_character` real return types (`GenrePack` / `Character`) instead of `object`; guard lines 146/161 fate access.
- Reframe the stale "RED today" module docstring.
- Optionally strip the consumer-less `encounter_base_tension` dead config from pulp_noir `rules.yaml`.

**Repo / branch:** sidequest-server, `feat/121-9-f4b-test-template-hardening` off `develop`. No content/UI/daemon touch.

**Routing:** trivial (phased) → implement phase owned by Dev (Hephaestus). Test-hardening on existing code — Dev makes the assertions real and the types honest, then verifies the suite still passes. No Jira (integration not configured; story ID is the key).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `tests/integration/test_121_2_pulp_noir_fate_migration.py` (sidequest-server) — hardened the F4b fate-migration test template per 121-2 Reviewer findings.

**What changed (all six scope items):**
1. **AC5 real-pack OTEL wiring** — added `test_real_pulp_noir_seed_emits_fate_chargen_seeded_span`: InMemorySpanExporter + injected `_tracer` (mirrors F4a's `test_fate_spans`), driving the seed against **real pulp_noir** content and asserting `fate.chargen.seeded` fires with `skill_count`/`aspect_count`/`refresh` pinned to the authored config.
2. **De-tautologized** `test_fate_sheet_skills_match_pack_config` — pins `sheet.skills["Investigate"] == 4` (pulp_noir's signature peak) so a seed truncate/reorder is caught, *then* the full verbatim match.
3. **AC4 on the built character** — added `test_built_character_has_no_d20_attribute_pool` asserting `character.stats == {}` (de-d20 invariant on the PC, not just pack config).
4. **Real return types** — `_load_pack() -> GenrePack`, `_build_pulp_noir_character() -> Character`; added a guarded `_fate_cfg()` accessor for the Optional `fate` block; dropped all now-unneeded `# type: ignore` comments.
5. **Docstring** — reframed the stale "RED today" header: pulp_noir is migrated; these tests are the GREEN regression net and the template F4c–F4e copy.
6. **`encounter_base_tension` strip** — deferred (optional + content-repo; out of server-only scope). See Design Deviations.

Bonus: fixed the type errors that surfaced when the `type: ignore`s came off (Optional `equipment_tables` guard, `FateRulesetModule` narrowing for the `_tracer` kwarg, `span.attributes` None-guard) — the file is now **pyright-clean**, ahead of the sibling F4a test.

**Tests:** 14/14 passing (GREEN), `-n0` serial. Lint clean (ruff). Type clean (pyright: 0 errors).
**Branch:** `feat/121-9-f4b-test-template-hardening` (pushed to origin).

**Handoff:** To review (Reviewer / Hermes Psychopompos).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The sibling F4a test `tests/game/ruleset/test_121_1_fate_chargen_seed.py` still carries the same `# type: ignore` / pyright errors this story cleaned up in the F4b file (untyped `_build_*` helpers, `_tracer` arg on a base-typed module, `span.attributes` None-subscript). Affects `tests/game/ruleset/test_121_1_fate_chargen_seed.py` (apply the same GenrePack/Character typing + module-narrowing + assert-non-None pattern for parity). Out of scope for 121-9. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The neon real-pack sibling `tests/game/test_builder_seeds_strain.py:306` masks the `equipment_tables` Optional with `# type: ignore[attr-defined]`; the guarded-attach pattern used here (`if pack.equipment_tables is not None`) is cleaner. Affects `tests/game/test_builder_seeds_strain.py` (optional follow-up). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Dict-subscript assertions (`sheet.skills["Investigate"]`, `span.attributes["skill_count"]`) raise `KeyError` (pytest ERROR) instead of a clean `AssertionError` (FAILED) when the key is absent on regression — the custom message is also suppressed. Affects `tests/integration/test_121_2_pulp_noir_fate_migration.py` (prefer `.get(key)` so the failure mode is a clean FAILED). LOW severity — tests still go red on regression; only the error *shape* differs. Worth folding in since F4c–F4e (121-3/4/5) copy this template verbatim. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `character.stats == {}` and the `aspect count == 1` checks encode pulp_noir-specific facts (empty d20 pool; non-empty default HC/trouble) that the F4c–F4e copyists will inherit silently. Affects `tests/integration/test_121_2_pulp_noir_fate_migration.py` (a one-line comment on each — "pulp_noir-specific; verify for your pack before copying" — would make the template safer to clone). LOW severity. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The neon real-pack sibling `tests/game/test_builder_seeds_strain.py:306` masks the `equipment_tables` Optional with `# type: ignore[attr-defined]`; the guarded-attach pattern used here (`if pack.equipment_tables is not None`) is cleaner. Affects `tests/game/test_builder_seeds_strain.py`.

### Downstream Effects

- **`tests/game`** — 1 finding

### Deviation Justifications

1 deviation

- **Deferred the optional `encounter_base_tension` dead-config strip**
  - Rationale: The item is explicitly *optional*, and the SM Assessment scoped this story "sidequest-server, ... No content/UI/daemon touch." `encounter_base_tension` lives in the **content** repo (sidequest-content). Doing it would turn a clean server-only 2pt test story into a cross-repo PR. Confirmed it has no runtime consumer in the server beyond the typed `RulesConfig` field declaration (`rules.py:1123`), so it is harmless to leave.
  - Severity: trivial
  - Forward impact: none — purely cosmetic dead config; can be swept in a future content-repo chore. Does not affect F4c-e template copies (they are server-side test files).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Deferred the optional `encounter_base_tension` dead-config strip**
  - Spec source: context-story-121-9.md (title), SM Assessment scope item 6
  - Spec text: "optionally strip the consumer-less encounter_base_tension dead config from pulp_noir rules.yaml"
  - Implementation: Not done. Left `pulp_noir/rules.yaml:99 encounter_base_tension` untouched.
  - Rationale: The item is explicitly *optional*, and the SM Assessment scoped this story "sidequest-server, ... No content/UI/daemon touch." `encounter_base_tension` lives in the **content** repo (sidequest-content). Doing it would turn a clean server-only 2pt test story into a cross-repo PR. Confirmed it has no runtime consumer in the server beyond the typed `RulesConfig` field declaration (`rules.py:1123`), so it is harmless to leave.
  - Severity: trivial
  - Forward impact: none — purely cosmetic dead config; can be swept in a future content-repo chore. Does not affect F4c-e template copies (they are server-side test files).

### Reviewer (audit)
- **Deferred `encounter_base_tension` strip** → ✓ ACCEPTED by Reviewer: sound. The item is explicitly *optional* and lives in sidequest-content; SM scoped this story server-only. Folding a content-repo edit in would create an unnecessary cross-repo PR for a 2pt test story. Confirmed independently that `encounter_base_tension` has no runtime consumer beyond the typed `RulesConfig` field declaration (`rules.py:1123`) — harmless to leave. Correct call.
- No undocumented deviations found. The diff matches the SM-scoped six items (five done, one explicitly deferred with rationale).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (14/14 GREEN, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 3 (Low), dismissed 4 (pre-existing/out-of-diff/already-mitigated) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer directly (see Rule Compliance) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — diff removes type debt, assessed by Reviewer |
| 7 | reviewer-security | Yes | clean | 0 | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — lang-review #6 (test quality) checked by Reviewer |

**All received:** Yes (3 enabled returned: 2 clean, 1 with findings; 6 disabled via settings)
**Total findings:** 3 confirmed (all Low, non-blocking), 4 dismissed (with rationale), 0 deferred

### Edge-hunter triage
- **[EDGE] KeyError vs AssertionError on `sheet.skills["Investigate"]` (line 189)** — CONFIRMED, Low. Real failure-mode nit: on a dropped-skill regression this raises `KeyError` (pytest ERROR) and suppresses the custom message, rather than a clean FAILED. Test still goes red on regression, so not blocking; filed as a non-blocking Delivery Finding because F4c–F4e copy this template.
- **[EDGE] KeyError on `span.attributes["skill_count"/...]` (lines 329-331)** — CONFIRMED, Low. Same class as above (attribute-rename → ERROR not FAILED). Non-blocking; filed.
- **[EDGE] `character.stats == {}` is pulp_noir-specific, not a Fate-universal invariant (line 265)** — CONFIRMED, Low. Correct for pulp_noir; the caution matters only for the F4c–F4e copyists. Filed as non-blocking Delivery Finding.
- **[EDGE] `_has_pulp_noir_content` only catches `PackNotFound` (line 62)** — DISMISSED: function is unchanged by this diff (pre-existing skip gate), and a content-dir `PermissionError` crashing collection is a theoretical edge the whole suite shares; low confidence, out of scope.
- **[EDGE] `_tracer` not on the ABC signature → fragile if type widened (line 296)** — DISMISSED: the code already documents this exact dependency in an inline comment after the `isinstance` narrow ("the base ABC signature omits it"); works today; low confidence.
- **[EDGE] AC2 aspect `count == 1` requires non-empty default HC/trouble (line 197)** — DISMISSED as blocker: the count assertions are pre-existing (this diff only added the `assert sheet is not None` narrowing); the "make it explicit for copyists" point is folded into the second Delivery Finding.
- **[EDGE] chargen walk has no iteration cap → hang on a cyclic scene graph (line 112)** — DISMISSED: inherited verbatim from the F4a/neon `_build_*` mirror pattern, unchanged by this diff; the builder FSM is designed to terminate. Pre-existing, low confidence.

## Reviewer Assessment

**Verdict:** APPROVED

A clean, well-scoped test-hardening diff. One file, test-only, server repo. It does exactly what SM scoped (five items done, one optional content-repo item explicitly deferred with sound rationale) and leaves the file *better-typed* than the sibling F4a test it mirrors.

**Data flow traced:** `find_pack_path("pulp_noir")` → `load_genre_pack` → `GenrePack` → `CharacterBuilder` walk → `Character` + `CreatureCore.fate_sheet`; and the OTEL path: `FateRulesetModule.seed_chargen_resources(_tracer=injected)` → `fate_chargen_seeded_span` → `InMemorySpanExporter`. Both terminate in concrete, value-pinned assertions. Safe — no production code touched, no network/auth/secret surface.

**Pattern observed:** the `_fate_cfg()` guarded accessor (`test_…:71`) centralizes the `RulesConfig.fate: FateConfig | None` narrowing into one fail-loud point — replacing five scattered `# type: ignore[attr-defined]` chains-through-None. Good pattern; complies with No Silent Fallbacks (asserts, doesn't default).

**Error handling:** `_fate_cfg` asserts non-None with a clear message; `_exporter()` builds an isolated per-call `TracerProvider` (no global side-effects); the `next(..., None)` + `assert span is not None` guards the span lookup. The only gaps are the Low `KeyError`-vs-`AssertionError` failure-mode nits below — they degrade error *shape*, not detection.

**Observations:**
- [VERIFIED] De-tautologization is real — `sheet.skills["Investigate"] == 4` pins the actual authored value (confirmed `pulp_noir/rules.yaml` authors `Investigate: 4`), so a seed truncate/reorder is caught independently of the full-dict self-comparison. Evidence: diff:178-184.
- [VERIFIED] `character.stats == {}` is non-vacuous — `generate_stats` delegates to `ruleset.generate_attributes`, which populates the dict for a d20 pack (STR/DEX/…) and returns empty for fate; a regression that synthesized a d20 pool under a fate binding would make this fail. Evidence: `builder.py:2451,3013`, `generate_stats` body.
- [VERIFIED] AC5 span test is a genuine wiring proof, not a source grep — it drives the real seed and inspects the emitted `fate.chargen.seeded` span, pinning `skill_count`/`aspect_count`/`refresh` to `_fate_cfg(pack)`. Complies with CLAUDE.md "No Source-Text Wiring Tests" (uses OTEL span assertion, the sanctioned pattern). Evidence: diff:260-295.
- [VERIFIED] Type debt genuinely removed — `object → GenrePack`/`Character`, all `# type: ignore` dropped, pyright 0 errors (preflight). The file is now cleaner than sibling F4a (Delivery Finding filed for parity). Evidence: preflight pyright run.
- [EDGE] reviewer-edge-hunter returned 7 findings; 3 CONFIRMED (all Low, non-blocking — dict-subscript KeyError-vs-FAILED at diff:189 and diff:329-331, and the pulp_noir-specific `stats == {}` at diff:265), 4 DISMISSED (pre-existing/out-of-diff/already-mitigated). Full per-finding triage in `## Subagent Results → Edge-hunter triage`. None reach Critical/High; the two template-relevant items are filed as non-blocking Delivery Findings for the F4c–F4e copyists.
- [SILENT] (subagent disabled) — assessed directly: no swallowed exceptions; `_fate_cfg` fails loud; `next(..., None)` is immediately asserted non-None. Clean.
- [TEST] (subagent disabled) — assessed against lang-review #6: no `assert True`, no assertion-free tests, skipif carries a reason, no parametrize-same-path. One pre-existing truthy `assert …fate_sheet.skills` at AC5 (diff:257) is a smoke check backed by the dedicated value test — acceptable.
- [DOC] (subagent disabled) — assessed directly: the stale "RED today" docstring is correctly reframed to GREEN/template status; new tests carry intent-explaining comments. Accurate.
- [TYPE] (subagent disabled) — assessed directly: this diff *improves* type design (narrowed returns, guarded Optional, concrete-type narrow for the `_tracer` call). No new stringly-typed surface.
- [SEC] CONFIRMED CLEAN by reviewer-security: no secrets, no shell-out, no path-traversal surface (hardcoded `"pulp_noir"`), in-process OTEL test doubles only.
- [SIMPLE] (subagent disabled) — assessed directly: no over-engineering; `_exporter()`/`_fate_cfg()` helpers each remove duplication. Appropriately minimal.
- [RULE] (rule-checker disabled) — lang-review #6 (test quality) enumerated above; SOUL/CLAUDE No-Silent-Fallbacks and No-Source-Text-Wiring rules both satisfied.

### Rule Compliance (lang-review #6 — test quality, checked exhaustively)
- Vacuous asserts (`assert True`/`assert not False`): none. ✓
- Truthy-only asserts: one pre-existing (`assert …fate_sheet.skills`, diff:257), backed by the dedicated value-pinning test — acceptable, not introduced here. ✓
- `mock.patch` wrong-target: no mocks used. ✓
- Assertion-free tests: none — every test has ≥1 value assertion. ✓
- `@pytest.mark.skip` without reason: skipif carries `reason="pulp_noir pack not on disk"`. ✓
- Parametrized same-path: no `@parametrize`. ✓
- Conftest/isolation: uses the standard `tests._helpers.genre_paths`; `_exporter()` is per-call isolated (no global tracer mutation). ✓

### Devil's Advocate
Argue this is broken. First attack: the OTEL test is a lie — it injects a tracer the *production builder never passes* (`builder.py:2866` calls `seed_chargen_resources` with no `_tracer`), so the test proves the span fires only under a hand-fed tracer, not on the real chargen path. Rebuttal: this is the exact F4a-sanctioned pattern, and the span's production destination (global tracer → GM panel) is an integration concern out of this unit's scope; the test correctly proves the *seed emits the span with correct counts*, which is the regression it guards. Second attack: `character.stats == {}` will detonate the moment a future Fate pack legitimately carries any `stats` entry, and three packs are about to copy this — a built-in time bomb. Rebuttal: real, but Low and filed as a non-blocking Delivery Finding; for pulp_noir it is correct *today*, and the copyists get an explicit caution. Third attack: the dict-subscript KeyErrors mean a regression reports as a pytest ERROR, and a CI dashboard that only greps "FAILED" could miss it. Rebuttal: plausible but thin — ERROR still fails the run and reddens CI; no real pipeline treats ERROR as pass. Fourth attack: a cyclic chargen graph hangs the suite forever (no iteration cap). Rebuttal: inherited, pre-existing, builder-FSM-terminating-by-design; not introduced here. None of these rise to a correctness defect in the changed code. The diff is sound.

**Handoff:** To SM (Themis the Just) for finish-story.