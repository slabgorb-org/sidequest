---
story_id: "121-1"
jira_key: ""
epic: "121"
workflow: "tdd"
---
# Story 121-1: F4a — Fate chargen-seeding spine + pack-content schema

## Story Details
- **ID:** 121-1
- **Jira Key:** (none — personal project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-15T12:57:18Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-15T12:21:35Z | 2026-06-15T12:23:55Z | 2m 20s |
| red | 2026-06-15T12:23:55Z | 2026-06-15T12:34:32Z | 10m 37s |
| green | 2026-06-15T12:34:32Z | 2026-06-15T12:49:45Z | 15m 13s |
| review | 2026-06-15T12:49:45Z | 2026-06-15T12:57:18Z | 7m 33s |
| finish | 2026-06-15T12:57:18Z | - | - |

## Sm Assessment

**Routing:** Story 121-1 (F4a) is the engine gate for epic 121 (F4 — Fate Core content migration, ADR-144). Setup clean — session + context + `feat/121-1-f4a-fate-chargen-spine` branch on sidequest-server (from origin/develop). Workflow `tdd` (phased); next phase **red**, owned by The Architect (TEA). No Jira (personal project).

**Scope confirmed (server-only engine spine — NOT content, NOT the chargen flow):**
- `FateConfig` in `genre/models/rules.py` + `RulesConfig.fate` field + `ruleset_config()` arm (mirror the Swn/Cwn/Awn/Wwn arms).
- `ChargenResources.fate_sheet: FateSheet | None` (`chargen_contribution.py`).
- `FateRulesetModule.seed_chargen_resources` override → builds a populated `FateSheet` (skills + HC/trouble aspects + refresh) from `FateConfig`.
- `builder.py` (~2866) attaches `fate_sheet` onto `CreatureCore`.
- `fate.chargen.seeded` OTEL span.

**Notes for The Architect (TEA), RED phase:**
- The seeding/apply layer is well-defined against the EXISTING `FateSheet` model (F1, merged). F4a only needs the apply + a default/template path. The INTERACTIVE chargen flow (player authors aspects, allocates the skill pyramid, picks stunts) is a SEPARATE story — 121-7/F4a2, design-gated by 121-6 — do not pull it into 121-1.
- **Mandatory wiring test** (server CLAUDE.md): a real fate-bound pack → production builder → PC with a populated FateSheet, AND combat routes to `fate_conflict` not native. OTEL-span or fixture-driven — **never a source-text grep**. Fate registry assertion needs the subprocess pattern (in-process autouse conftest masks it — project memory).
- **Risk to pin with a test:** the builder/chargen path must NOT hard-require d20 stats/classes for a fate pack.
- Depends F1 — DONE & merged (`FateRulesetModule`, `fate_conflict.py`, `fate_sheet.py` exist; `fate` registered in `registry.py`).

**Decision:** Setup complete. Hand to TEA for RED.

## TEA Assessment

**Tests Required:** Yes
**Test Files:**
- `sidequest-server/tests/game/ruleset/test_121_1_fate_chargen_seed.py` — F4a Fate chargen-seeding spine: FateConfig schema + RulesConfig.fate + ruleset_config() arm, ChargenResources.fate_sheet, seed_chargen_resources populated-sheet build, builder fate_sheet attach, fate.chargen.seeded span, and the fate-routes-not-native wiring test.

**Tests Written:** 19 tests across 6 ACs (AC1–AC6).
**Status:** RED — verified by **direct** `uv run pytest -n0` (collection errors on the missing `FateConfig` symbol; `ChargenResources` has no `fate_sheet` attr). Ran directly rather than via testing-runner because that subagent fabricates output (project memory). Supporting scaffolding (CharacterBuilder / CharCreationScene / MechanicalEffects / native build path / `CreatureCore.fate_sheet` defaulting None) verified sound against current code, so Dev's first commit (add `FateConfig`) unblocks the full file cleanly.

### Rule Coverage (python lang-review + project rules)

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (SOUL / swn-cwn validator precedent) | `test_fate_pack_without_fate_block_fails_loud`, `test_fate_config_forbids_unknown_keys` | failing (RED) |
| OTEL Observability (CLAUDE.md — every subsystem decision emits a span) | `TestAC5ChargenSeededSpan` (3 tests) | failing (RED) |
| No Source-Text Wiring Tests (CLAUDE.md) | wiring via module-resolution + builder behavior + InMemorySpanExporter, never `read_text()` | pass (by construction) |
| #6 test-quality (meaningful, non-vacuous asserts) | exact-value asserts on skills/aspects/refresh/span attrs; negatives assert specific `None`/`not isinstance` | pass |

**Rules checked:** No-Silent-Fallbacks, OTEL, no-source-grep wiring, test-quality — all applicable rules have coverage.
**Self-check:** 0 vacuous tests. Fixed a garbled `fate_rules` helper expression (`dict(...) and {...}`) + a missing `fate_refresh` param before commit.

**Handoff:** To Agent Smith (Dev) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/genre/models/rules.py` — `FateConfig` (+ `FateStuntDef`), `RulesConfig.fate` field, `_validate_fate` (fail-loud when ruleset=='fate' & fate None), `ruleset_config()` fate arm (return type widened to `SwnConfig | FateConfig | None`).
- `sidequest/game/chargen_contribution.py` — `ChargenResources.fate_sheet: FateSheet | None` (additive).
- `sidequest/game/ruleset/fate.py` — `FateRulesetModule.seed_chargen_resources` builds a populated `FateSheet` (skills from config, HC+trouble aspects, refresh==fate_points) and emits `fate.chargen.seeded`.
- `sidequest/telemetry/spans/fate.py` — `fate_chargen_seeded_span` + literal `SPAN_ROUTES["fate.chargen.seeded"]` (mirrors the `fate.action.classified` precedent).
- `sidequest/game/ruleset/base.py` — `_generate_attribute_values`: no ability scores → empty pool (the de-d20 invariant).
- `sidequest/game/builder.py` — attach `_res.fate_sheet` onto `CreatureCore`.
- `tests/game/ruleset/test_121_1_fate_chargen_seed.py` — lint-only touch-up of TEA's RED tests (removed unused `random`, sorted imports).

**Tests:** 19/19 passing (GREEN) — verified by **direct** `uv run pytest -n0` (testing-runner fabricates output). All 6 ACs covered, including the de-d20 risk pin (implemented, not descoped).
**Regression:** affected suites (ruleset / chargen+builder / telemetry / WN integration chargen) = 838 passing. The 2 failures (`test_real_neon_character_gets_strain_pool` — neon D3 genre-bespoke gear; `test_cc_chargen_e2e.py` — caverns_and_claudes WWN-port chargen) are **pre-existing content drift**, proven by stashing this work and re-running on base code (both fail identically without F4a). Logged as a Delivery Finding.
**Lint:** `ruff check` clean on all changed files. Ruff-format churn on pre-existing lines was reverted (only my added lines remain) per the no-churn rule; pre-existing format drift left untouched (CI doesn't enforce format).
**Types:** pyright clean on changed code; the `ruleset_config()` widening produced no caller errors (all narrow via isinstance). 2 pre-existing pyright errors in builder.py noted as a Finding.
**Branch:** feat/121-1-f4a-fate-chargen-spine (pushed).

**Handoff:** To The Architect (TEA) for the verify phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | GREEN (813 passed, 1 failed) | 1 pre-existing | confirmed 0, dismissed 0, deferred 1 (neon D3 content drift — pre-existing) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |
| 7 | reviewer-security | Yes | findings | 2 (both LOW) | confirmed 2 (LOW, non-blocking), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings; domain covered first-party by Reviewer |

**All received:** Yes (2 enabled specialists returned — preflight + security; 7 disabled via `workflow.reviewer_subagents` settings, their domains covered first-party by the Reviewer on a small 503-line diff)
**Total findings:** 2 confirmed (both LOW, non-blocking), 0 dismissed, 1 deferred (pre-existing content drift)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** pack `rules.fate.*` (genre YAML) → `FateConfig` (`extra="forbid"`, pydantic-validated, `_validate_fate` fails loud if absent) → `RulesConfig.ruleset_config()` returns the FateConfig for `ruleset=="fate"` → `FateRulesetModule.seed_chargen_resources` reads `skills`/`default_high_concept`/`default_trouble`/`refresh` → builds `FateSheet` → emits `fate.chargen.seeded` → `ChargenResources(fate_sheet=…)` → `CharacterBuilder` attaches to `CreatureCore.fate_sheet`. Safe: every input is genre-authored content (not player free-text), and the aspect-text path is additionally `sanitize_player_text`-wrapped downstream at `fate_projection.py:57-58` (confirmed by [SEC]).

**Observations (≥5):**
1. `[VERIFIED]` No Silent Fallbacks — `_validate_fate` (rules.py:1270) raises `ValueError` when `ruleset=="fate"` and `fate is None`; mirrors the swn/cwn/wwn attribute_map validators. Tested by `test_fate_pack_without_fate_block_fails_loud`.
2. `[VERIFIED]` `[SEC]` de-d20 guard (base.py:302 `if not ability_names: return []`) cannot mask a WN/native misconfig — the swn/cwn/wwn validators require a 6-key attribute_map mapped into `ability_score_names`, so a non-Fate pack with empty `ability_score_names` fails validation before stat-gen. The guard only fires for a genuinely stat-less ruleset (Fate). Confirmed independently by reviewer-security.
3. `[VERIFIED]` `[TYPE]` `ruleset_config()` widening to `SwnConfig | FateConfig | None` (rules.py:1372) is type-safe — pyright clean, all 20 call sites narrow via `isinstance` before touching ruleset-specific fields; a non-Fate pack never receives a FateConfig.
4. `[VERIFIED]` `[RULE]` Fate ladder negativity preserved — `FateConfig.skills`/`refresh` carry no `Field(ge=0)`, honoring ADR-144's negative ladder rungs (and the project memory rule). `extra="forbid"` on both `FateConfig` and `FateStuntDef`.
5. `[VERIFIED]` `[PRE]` OTEL — `fate.chargen.seeded` carries only `skill_count`/`aspect_count`/`refresh` ints + `actor` (no PII/secrets); literal `SPAN_ROUTES` key follows the `fate.action.classified` precedent (routing-completeness lint inspects only `SPAN_*` constants). Tested by `TestAC5ChargenSeededSpan`.
6. `[VERIFIED]` `[TEST]` test quality — 19 tests, all 6 ACs, exact-value asserts (skills/aspects/refresh/span attrs); negatives assert specific `None`/`not isinstance`. No vacuous assertions. The de-d20 risk pin is implemented and green.
7. `[VERIFIED]` `[DOC]` docstrings/comments accurate — ADR citations correct, `del stats, class_def` documented as the de-d20 invariant, no stale comments.
8. `[LOW]` `[SEC]` `FateConfig.refresh` has no `ge=1` lower bound (rules.py:1042) — a pack with `refresh: 0`/negative seeds `fate_points<1`. Degenerate-config-only, content authors set 3; non-blocking. Recommended fast-follow: `Field(default=3, ge=1)` (refresh is a positive resource count, NOT a ladder value — the negative-rung memory rule does not apply). Logged as a delivery finding.
9. `[LOW]` `[SEC]` `[SIMPLE]` `**attrs: Any` on `fate_chargen_seeded_span` (telemetry/spans/fate.py:561) — a **pre-existing** pattern across all fate span emitters; no caller passes extra attrs. Non-blocking; a broader span-hardening cleanup, out of F4a scope. Logged as a delivery finding.
10. `[LOW]` `[EDGE]`/`[SILENT]` the defensive `isinstance(cfg, FateConfig)` guard in `seed_chargen_resources` (fail-loud, raises `FateEconomyError`) is untested and uses an economy-flavored error type for a chargen-config error — a nit. The guard is correct (No Silent Fallbacks); a more specific error type would read better. Non-blocking.

### Rule Compliance (python lang-review + SOUL/CLAUDE)

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 silent exceptions | `seed_chargen_resources` raise; `_validate_fate` raise | compliant — explicit raises, no swallow |
| #2 mutable defaults | `FateConfig` (default_factory dict/list), `_tracer=None` | compliant |
| #3 type annotations at boundaries | `seed_chargen_resources` params/return unannotated | consistent with the unannotated base seam signature (`base.py` `seed_chargen_resources` also unannotated) — not a new violation; LOW consistency note |
| #6 test quality | 19 tests | compliant (exact asserts, no vacuous) |
| #8 unsafe deserialization | FateConfig via pydantic `model_validate` | compliant — no eval/pickle/yaml.load |
| #10 import hygiene | fate.py lazy-imports ChargenResources/FateConfig (WN precedent); sorted imports | compliant |
| No Silent Fallbacks (SOUL) | `_validate_fate`, the cfg-type guard | compliant |
| OTEL Observability (CLAUDE) | `fate.chargen.seeded` + SPAN_ROUTES | compliant |
| No Source-Text Wiring Tests (CLAUDE) | wiring via module-resolution + builder behavior + InMemorySpanExporter | compliant (no `read_text` grep) |
| game↛genre layering | `FateStuntDef`/`FateConfig` defined genre-tier, no `game` import | compliant |

### Devil's Advocate

*Argue this code is broken.* A confused or hostile pack author writes `rules.fate: {}` — every field defaults: empty `skills`, empty aspects, `refresh: 3`. `_validate_fate` only checks `fate is not None`, so this loads, and `seed_chargen_resources` produces a valid-but-hollow sheet: a character Mediocre (+0) at everything, no aspects, three fate points to spend on nothing. Is that a silent fallback the engine should have rejected? Or set `refresh: -2` and the PC starts the session with negative fate points — the economy's `spend_fate_point` will fail loud at zero, but the *seed* never complained. A malicious author could set `Shoot: 99999`; the seed copies it verbatim, and 4dF+99999 trivially beats any opposition — a balance break, though F4a doesn't adjudicate, so it surfaces only at play. What about the shared `base.py` guard — does returning `[]` for empty `ability_names` quietly strip stats from some pack that legitimately wanted them? And the `ruleset_config()` union now admits a FateConfig where 20 call sites previously assumed a SwnConfig-or-None; one un-narrowed `.attribute_map` access would AttributeError at runtime on a Fate pack.

*Why the protections hold.* The `fate: {}` and `refresh<1` degeneracies are explicit author choices producing degenerate-but-valid state, not silent *code* fallbacks — and real content lands in 121-2 (F4b) with authored skills + a content validator. They are captured as LOW findings (#8). The `Shoot: 99999` is a content-balance concern, not an F4a engine bug — Fate inherits the SRD's authoring norms; F4a is the spine. The `base.py` guard is provably dormant for every validated WN/native pack (observation #2). The union widening was verified pyright-clean across all 20 call sites — each narrows via `isinstance` (observation #3). No Critical/High emerges; the residue is three LOW polish items.

**Verdict rationale:** No Critical or High findings. Two LOW security findings (refresh bound, pre-existing `**attrs`) + one LOW Reviewer nit (defensive-guard test/error-type), all non-blocking and logged as delivery findings. All six in-flight deviations audited and ACCEPTED. Tests GREEN (19/19 story; 813 neighbors), lint clean, pyright clean on changed code. The implementation is minimal, correctly layered (game↛genre respected), fails loud, and is OTEL-observable.

**Handoff:** To Morpheus (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Gap** (non-blocking): F4a needs a new `fate.chargen.seeded` OTEL emitter + `SPAN_ROUTES` entry — none exists today. Affects `sidequest/telemetry/spans/fate.py` (add an emitter fn + a literal `SPAN_ROUTES` key, mirroring the `fate.action.classified` literal-key precedent so the routing-completeness lint stays satisfied). *Found by TEA during test design.*
- **Improvement** (non-blocking): `test_fate_pack_builds_without_d20_stats` is the most ambitious assertion — a fate pack with empty `ability_score_names` must build through the production builder. If the builder hard-requires d20 stat-gen beyond F4a's seeding scope, Dev should log a deviation and may descope this single assertion to 121-7 (F4a2). Affects `sidequest/game/builder.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): two real-pack integration tests fail at content load, **independent of F4a** (proven by stashing this work — both fail identically on base): `test_real_neon_character_gets_strain_pool` (neon_dystopia genre inventory carries bespoke gear that the ADR-145 D3 validator rejects) and `test_cc_chargen_e2e.py` (caverns_and_claudes char_creation has no `Warrior`/`Mage` class_hint after the WWN port). Affects `sidequest-content` (neon_dystopia + caverns_and_claudes) — tracked by the epic-114 SRD-inventory migration and the cc WWN-port chargen update, not by 121-1. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `sidequest/game/builder.py` has 2 pre-existing pyright errors (line ~1636 `add_event` attributes type; a `_rolled_stats` list invariance) unrelated to and untouched by F4a. Affects `sidequest/game/builder.py` (a future typing cleanup). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `FateConfig.refresh` accepts `<1` (no lower bound) — a degenerate pack would seed `fate_points<1`. Affects `sidequest/genre/models/rules.py` (recommend `refresh: int = Field(default=3, ge=1)` — refresh is a positive resource count, not a ladder value). Fast-follow or fold into F4b authoring guards. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `fate_chargen_seeded_span` exposes `**attrs: Any` (pre-existing pattern across all fate span emitters) — structurally permits future callers to inject unfiltered attributes into telemetry; no current caller does. Affects `sidequest/telemetry/spans/fate.py` (a broader span-hardening cleanup, out of F4a scope). *Found by Reviewer during code review.*
- **Gap** (non-blocking): the defensive `isinstance(cfg, FateConfig)` branch in `seed_chargen_resources` is untested and raises `FateEconomyError` (an economy-flavored type) for a chargen-config error. Affects `sidequest/game/ruleset/fate.py` (optional: a dedicated error type + a test for the misconfigured-binding path). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 4 findings (2 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Gap:** F4a needs a new `fate.chargen.seeded` OTEL emitter + `SPAN_ROUTES` entry — none exists today. Affects `sidequest/telemetry/spans/fate.py`.
- **Improvement:** `sidequest/game/builder.py` has 2 pre-existing pyright errors (line ~1636 `add_event` attributes type; a `_rolled_stats` list invariance) unrelated to and untouched by F4a. Affects `sidequest/game/builder.py`.
- **Improvement:** `fate_chargen_seeded_span` exposes `**attrs: Any` (pre-existing pattern across all fate span emitters) — structurally permits future callers to inject unfiltered attributes into telemetry; no current caller does. Affects `sidequest/telemetry/spans/fate.py`.
- **Gap:** the defensive `isinstance(cfg, FateConfig)` branch in `seed_chargen_resources` is untested and raises `FateEconomyError` (an economy-flavored type) for a chargen-config error. Affects `sidequest/game/ruleset/fate.py`.

### Downstream Effects

Cross-module impact: 4 findings across 3 modules

- **`sidequest/telemetry/spans`** — 2 findings
- **`sidequest/game`** — 1 finding
- **`sidequest/game/ruleset`** — 1 finding

### Deviation Justifications

6 deviations

- **Default-template aspect seed, not archetype-driven**
  - Rationale: Archetype-driven aspect authoring overlaps the interactive chargen flow (story 121-7/F4a2); the SM Assessment scoped F4a to "the apply layer + a default/template seed path." Keeps F4a focused.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) and 121-2 (F4b) may layer archetype-driven aspect seeding atop this default path.
- **Stunt-catalog field not test-pinned**
  - Rationale: A default-seeded PC takes no stunts (stunt selection is interactive chargen, 121-7); FateConfig may carry a catalog field but F4a's seed does not apply it, so it is not test-gated here.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) consumes the stunt catalog when the player picks stunts.
- **Wiring uses a synthetic fate pack, not real content**
  - Rationale: "REAL builder" = the production `CharacterBuilder`; no fate-bound content pack exists until 121-2 (F4b). Synthetic pack + real builder is the available end-to-end path.
  - Severity: trivial
  - Forward impact: 121-2 (F4b) should add a skipif-gated real-pack chargen integration test (mirror `test_real_neon_character_gets_strain_pool`).
- **De-d20 invariant implemented in the base stat-gen, not descoped**
  - Rationale: This is correct behavior, not a hack — a ruleset with no ability scores has nothing to roll/allocate. F4a's purpose is that fate packs are buildable, so the guard belongs here; it is dormant for every WN/native pack (they always declare ability_score_names).
  - Severity: minor
  - Forward impact: none negative; any future stat-less ruleset inherits the correct empty-pool behavior.
- **Archetype-driven seeding deferred (implemented per TEA's default-template contract)**
  - Rationale: Archetype-driven aspect authoring belongs to the interactive chargen flow (121-7) per the SM scope; see the parallel TEA deviation above.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) / 121-2 (F4b) may layer archetype-driven seeding atop this default path.
- **Stunt catalog added as a typed-but-unconsumed forward contract**
  - Rationale: Honors the story title's "stunt catalog" while keeping the default seed minimal; the field is the contract 121-7 will consume, following the `standoff_rules` typed-but-unconsumed precedent already in rules.py. Not test-gated (per TEA deviation).
  - Severity: trivial
  - Forward impact: 121-7 (F4a2) consumes `stunts` when the player picks stunts at chargen.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Default-template aspect seed, not archetype-driven**
  - Spec source: context-story-121-1.md, AC3 + story title
  - Spec text: "override FateRulesetModule.seed_chargen_resources to build a VALID POPULATED FateSheet from the pack FateConfig + chosen archetype (skills seeded, high-concept/trouble aspect pair, refresh)"
  - Implementation: Tests pin seeding from `FateConfig.default_high_concept` / `default_trouble` (the default-template path), not an archetype→aspect mapping.
  - Rationale: Archetype-driven aspect authoring overlaps the interactive chargen flow (story 121-7/F4a2); the SM Assessment scoped F4a to "the apply layer + a default/template seed path." Keeps F4a focused.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) and 121-2 (F4b) may layer archetype-driven aspect seeding atop this default path.
- **Stunt-catalog field not test-pinned**
  - Spec source: context-story-121-1.md, AC1 + story title
  - Spec text: "add FateConfig ... (per-genre skill list + default ratings, refresh, optional starting-aspect templates, stunt catalog)"
  - Implementation: Tests do not assert a `stunts` field on FateConfig nor stunt seeding on the default sheet.
  - Rationale: A default-seeded PC takes no stunts (stunt selection is interactive chargen, 121-7); FateConfig may carry a catalog field but F4a's seed does not apply it, so it is not test-gated here.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) consumes the stunt catalog when the player picks stunts.
- **Wiring uses a synthetic fate pack, not real content**
  - Spec source: context-story-121-1.md, AC6
  - Spec text: "a pack bound ruleset: fate through the REAL builder produces a PC with a populated FateSheet and combat routes to fate_conflict not native"
  - Implementation: The wiring test drives a synthetically-constructed `ruleset: fate` RulesConfig through the production `CharacterBuilder` (no real fate content pack exists until F4b).
  - Rationale: "REAL builder" = the production `CharacterBuilder`; no fate-bound content pack exists until 121-2 (F4b). Synthetic pack + real builder is the available end-to-end path.
  - Severity: trivial
  - Forward impact: 121-2 (F4b) should add a skipif-gated real-pack chargen integration test (mirror `test_real_neon_character_gets_strain_pool`).

### Dev (implementation)
- **De-d20 invariant implemented in the base stat-gen, not descoped**
  - Spec source: context-story-121-1.md, AC6 + TEA delivery finding (offered descope of `test_fate_pack_builds_without_d20_stats`)
  - Spec text: "the builder/chargen path must NOT hard-require d20 stats/classes for a fate pack"
  - Implementation: Added a guard to `RulesetModule._generate_attribute_values` (base.py): `if not ability_names: return []` — a stat-less ruleset generates no attribute pool. Kept the de-d20 test green rather than descoping it to 121-7.
  - Rationale: This is correct behavior, not a hack — a ruleset with no ability scores has nothing to roll/allocate. F4a's purpose is that fate packs are buildable, so the guard belongs here; it is dormant for every WN/native pack (they always declare ability_score_names).
  - Severity: minor
  - Forward impact: none negative; any future stat-less ruleset inherits the correct empty-pool behavior.
- **Archetype-driven seeding deferred (implemented per TEA's default-template contract)**
  - Spec source: context-story-121-1.md, AC3 + story title ("from the pack FateConfig + chosen archetype")
  - Spec text: "build a VALID POPULATED FateSheet from the pack FateConfig + chosen archetype"
  - Implementation: `seed_chargen_resources` seeds from `FateConfig.default_high_concept` / `default_trouble` (default-template), not an archetype→aspect mapping — matching TEA's RED contract.
  - Rationale: Archetype-driven aspect authoring belongs to the interactive chargen flow (121-7) per the SM scope; see the parallel TEA deviation above.
  - Severity: minor
  - Forward impact: 121-7 (F4a2) / 121-2 (F4b) may layer archetype-driven seeding atop this default path.
- **Stunt catalog added as a typed-but-unconsumed forward contract**
  - Spec source: context-story-121-1.md, AC1 + story title ("stunt catalog")
  - Spec text: "add FateConfig ... (... stunt catalog)"
  - Implementation: Added `FateConfig.stunts: list[FateStuntDef]` (genre-tier, no game→genre layering violation), but F4a's default seed applies no stunts.
  - Rationale: Honors the story title's "stunt catalog" while keeping the default seed minimal; the field is the contract 121-7 will consume, following the `standoff_rules` typed-but-unconsumed precedent already in rules.py. Not test-gated (per TEA deviation).
  - Severity: trivial
  - Forward impact: 121-7 (F4a2) consumes `stunts` when the player picks stunts at chargen.

### Reviewer (audit)
- **Default-template aspect seed, not archetype-driven** (TEA + Dev) → ✓ ACCEPTED by Reviewer: archetype→aspect mapping legitimately belongs to interactive chargen (121-7); the SM scope confined F4a to the default/template seed path. Sound.
- **Stunt-catalog field not test-pinned** (TEA) / **Stunt catalog added as a typed-but-unconsumed forward contract** (Dev) → ✓ ACCEPTED by Reviewer: implementing the field per the story title while leaving it unconsumed is consistent with the `standoff_rules` typed-but-unconsumed precedent in the same file; genre-tier (no game↛genre layering violation). Documented. Sound.
- **Wiring uses a synthetic fate pack, not real content** (TEA) → ✓ ACCEPTED by Reviewer: no fate-bound content pack exists until 121-2 (F4b); "REAL builder" = the production `CharacterBuilder`, which the test does exercise. The forward note to add a skipif-gated real-pack test in F4b is the right follow-up.
- **De-d20 invariant implemented in the base stat-gen, not descoped** (Dev) → ✓ ACCEPTED by Reviewer: the `if not ability_names: return []` guard is correct behavior (a stat-less ruleset has nothing to roll), provably dormant for every validated WN/native pack (the attribute_map validators force non-empty `ability_score_names`), and keeps the de-d20 AC green. Preferable to descoping. Sound.
- No undocumented deviations found by Reviewer — the diff matches the audited deviation set.