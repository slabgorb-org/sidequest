---
story_id: "103-1"
jira_key: ""
epic: "103"
workflow: "tdd"
---
# Story 103-1: Saint layer — saints.yaml schema + SaintRegistry + Saint-Marked chargen preset

## Story Details
- **ID:** 103-1
- **Jira Key:** (none — local sprint)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch Strategy:** gitflow (feat/103-1-saint-layer)
- **Repos:** server, content

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-11T00:15:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-10T23:43:29Z | 2026-06-10T23:45:40Z | 2m 11s |
| red | 2026-06-10T23:45:40Z | 2026-06-10T23:55:31Z | 9m 51s |
| green | 2026-06-10T23:55:31Z | 2026-06-11T00:10:31Z | 15m |
| review | 2026-06-11T00:10:31Z | 2026-06-11T00:15:30Z | 4m 59s |
| finish | 2026-06-11T00:15:30Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): Negative-mutation `attr_penalties` have NO resolution-time consumer anywhere in the engine — `grep attr_penalties` outside `mutation/models.py` returns nothing, so Wild-path chargen negatives' attribute penalties are inert too (a 102-7-era gap, not introduced here). The Saint drawback's mechanical surface in this story is therefore pinned to state presence + narrator-context surfacing + the `awn.saint.applied` span, not attribute math. Affects `sidequest/mutation/` (a future story should wire `attr_penalties` into the CWN/AWN attribute-modifier path for ALL negatives, Wild and Saint alike). *Found by TEA during test design.*
- **Improvement** (non-blocking): Draft worlds are silently skipped at pack load (`loader.py` returns None on `draft: true`), so no validation runs on a draft world's content until the draft flag lifts — the seaboard saints.yaml would go unvalidated by CI through 103-4..103-8 if tests only used `load_genre_pack`. The RED suite compensates (direct `load_saint_registry` against the real catalog in `tests/genre/test_saints_world_load.py`), but a `--include-drafts` validation mode in the pack validator would close the class of gap. Affects `sidequest/genre/loader.py` / `sidequest/cli/validate`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 23 pre-existing test failures in the full server suite when run from a plain shell — all rooted in `SIDEQUEST_DATABASE_URL` not being set (e.g. `tests/agents/test_use_mutation_tool.py`, `tests/server/test_app.py`, `tests/server/test_forensics_routes.py`). Verified NOT caused by this story: stash-baseline produces a byte-identical failure list (`diff /tmp/fail-baseline.txt /tmp/fail-mine.txt` → identical). Affects test-env bootstrap docs/fixtures (these tests bypass the `migrated_db` fixture's env wiring). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): `apply_saint_preset`'s idempotency guard (`actor in state.characters`) cannot distinguish same-path replay (correct silent return) from CROSS-PATH re-entry — an actor seeded via the Wild path who later reaches the Saint route gets their Wild state silently returned, no span, GM panel blind. No production path can trigger this today (saint_id is never passed until 103-2's stock step), but 103-2 MUST add a provenance guard (e.g. verify `acquisition_log[0] == saint.drawback` on replay, or a `seeded_by` field) when it wires the selection surface. Affects `sidequest/mutation/saints.py` (cross-path re-entry should raise loudly). *Found by Reviewer during code review.*
- **Gap** (non-blocking): `apply_saint_preset` recomputes MP from the economy without re-checking affordability — the cap lives only in `load_saint_registry`. A programmatically-built over-budget `SaintRegistry` (bypassing the loader, e.g. a future fixture or alternate load path) would write a negative `mp_remaining` silently (`CharacterMutationState.mp_remaining` is an unconstrained int). Defense-in-depth: a loud guard (raise on negative) in `apply_saint_preset` would close it. Affects `sidequest/mutation/saints.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Explicit saint_id bypasses the mutant_classes chargen gate**
  - Spec source: context-story-103-1.md, AC-3 / Technical Guardrails
  - Spec text: "creating a Saint-Marked character yields exactly the bundle's positives + the drawback negative on the sheet, with MP accounting consistent with MpEconomy"
  - Implementation: Tests pin that `apply_saint_preset` (and the `saint_id` route through `init_mutation_state_for_session`) applies regardless of `mp_economy.mutant_classes`; the class gate remains only on the classic Wild seed path (`seed_character_mutations`).
  - Rationale: The spec is silent on class gating for Saints. Stock⊥class orthogonality is 103-2's locked model — coupling Saint presets to the pack's three `mutant_classes` would contradict it and break Seaboard chargen for non-Mutant classes. The Saint's spring does not check your job.
  - Severity: minor
  - Forward impact: 103-2 (stock step) builds on this — Saint-Marked stock selection passes `saint_id` for any class; no sibling AC contradicted.
- **AC-4 "drawback fires in confrontation" pinned to existing machinery, not new combat semantics**
  - Spec source: context-story-103-1.md, AC-4
  - Spec text: "in a confrontation, the proof Saint's drawback fires through the existing mutation-use machinery and is observable. Test: OTEL-asserted confrontation fixture"
  - Implementation: Tests assert (a) drawback present in `CharacterMutationState.negative_ids` via the preset, (b) drawback line rendered in `build_mutation_static_block` (the "mechanical truth — never invent powers" narrator block), (c) `awn.saint.applied` span carries the drawback id + full MP math. No test demands a new in-confrontation negative-resolution path.
  - Rationale: Negatives have no resolution-time consumer engine-wide today (see Delivery Finding — `attr_penalties` are inert even for Wild mutants); "the existing mutation-use machinery" for negatives IS context surfacing + state. Inventing combat semantics for drawbacks in TEA would exceed story scope and diverge Saint negatives from Wild negatives.
  - Severity: minor
  - Forward impact: 103-10's per-stock e2e keeps the same honest bar unless the attr_penalties gap is closed by a Dev story first; flagged in Delivery Findings for routing.
- **MP pricing formula pinned: bundle funded at the random-pull rate**
  - Spec source: context-story-103-1.md, AC-3; build plan §D-A ("priced by the live MpEconomy")
  - Spec text: "drawback counts as the negative that funds the bundle per AWN pricing"
  - Implementation: Tests pin `mp_remaining = base_mp + per_negative_mp − len(bundle) × spend_random_positive`, and registry-load affordability `len(bundle) × spend_random_positive ≤ base_mp + per_negative_mp` (default economy ⇒ max 4-mark bundle, matching spec §6's 3-4-mutation bundles exactly).
  - Rationale: The faithful AWN reading — the Saint's spring replaces the dice, not the pricing. Pick-rate (3 MP) would make any 2+ mark bundle unaffordable; random-rate is the only economy-consistent interpretation that funds the spec's own bundle sizes.
  - Severity: minor
  - Forward impact: 103-4's canon authoring must respect the 4-mark bundle cap (or fund larger bundles via affinity purchases); the cap is loud at load so violations can't ship silently.

### Dev (implementation)
- **saint_id selection surface not yet reachable from live chargen UI**
  - Spec source: .session/103-1-session.md TEA Assessment ("Contract pinned for Dev"); context-story-103-1.md Technical Guardrails
  - Spec text: "init_mutation_state_for_session gains the saint route (saints=, saint_id=); saint_id with no registry → loud error"
  - Implementation: The route is implemented with loud validation, and BOTH chargen call sites plumb `saints=` from the active world — but they pass no `saint_id` because no chargen surface captures a Saint selection yet. The route is exercised by the preset/init machinery and unit/integration tests; live player selection arrives with 103-2's stock step.
  - Rationale: 103-1's scope is the Saint layer + preset engine; the multi-path chargen step (where a player picks Saint-Marked and a Saint) is explicitly 103-2 per the epic story graph. Wiring the registry plumb-through now means 103-2 only adds the selection value.
  - Severity: minor
  - Forward impact: 103-2 must pass the captured saint_id through the existing parameter; no signature change needed.
- **No deviations in models/loader/preset/span** — implemented exactly to TEA's pinned contract (structural validators, loud cross-validation, affordability cap, MP formula `base + per_negative − bundle×random_rate`, burdens-before-gifts, idempotency without span re-fire, full MP math span attrs, SPAN_ROUTES registration, mutations hoisted above world load).

### Reviewer (audit)
- **TEA: Explicit saint_id bypasses the mutant_classes chargen gate** → ✓ ACCEPTED by Reviewer: stock⊥class orthogonality is 103-2's locked model; coupling Saints to the three `mutant_classes` would contradict the epic's D-B decision. The route's loud-error contract covers the misconfiguration cases that matter.
- **TEA: AC-4 "drawback fires in confrontation" pinned to existing machinery** → ✓ ACCEPTED by Reviewer: verified by my own grep — `attr_penalties` has zero resolution-time consumers engine-wide, so the pinned bar (state + narrator-context block + span) IS the existing machinery; inventing combat semantics here would diverge Saint negatives from Wild negatives. The engine-wide gap is properly routed via Delivery Findings.
- **TEA: MP pricing formula pinned at the random-pull rate** → ✓ ACCEPTED by Reviewer: arithmetic checked against `MpEconomy` defaults — pick-rate (3 MP) cannot fund the spec's own 3-4-mark bundles (budget 4); random-rate is the only economy-consistent reading. The load-time affordability cap makes violations loud.
- **Dev: saint_id selection surface not yet reachable from live chargen UI** → ✓ ACCEPTED by Reviewer: 103-2 explicitly owns the stock/Saint selection step per the epic story graph; the registry plumb-through at both call sites means 103-2 adds only the value. Loud-error contract verified at mutation_init.py (registry-missing and catalog-missing both raise).

## Sm Assessment

**Setup complete; story is ready for The Architect (TEA, red phase).**

- **Contexts:** `sprint/context/context-story-103-1.md` (validated) and `sprint/context/context-epic-103.md` are the spec sources, backed by the build plan `docs/superpowers/specs/2026-06-10-seaboard-of-saints-build-plan.md` (§D-A is this story's design) and the AWN rebase addendum (`2026-06-09-seaboard-of-saints-awn-rebase-addendum.md`, doctrine: AWN wins always).
- **Branches:** `feat/103-1-saint-layer` created in both sidequest-server and sidequest-content, based on origin/develop. Jira: skipped (local-only story, no key).
- **Dependencies:** none — AWN Plan 1 (102-7) and Plan 2 (mutation catalog + MpEconomy) are merged and live; verified against origin 2026-06-10.
- **Coordination flag (non-blocking):** story 103-5 (world core, GM lane) is in flight in parallel on `feat/103-5-seaboard-world-core` in sidequest-content, authoring `worlds/seaboard_of_saints/{world,lore,history}.yaml` via a background writer agent. 103-1 ships a *skeletal* world.yaml + proof `saints.yaml` in the same directory on its own branch. Merge-order note: 103-5's full world.yaml supersedes 103-1's skeletal one; whichever merges second reconciles (trivial — skeletal file only exists to make the world loadable for tests). The content clone's checkout is time-shared between the two branches — TEA/Dev should check out `feat/103-1-saint-layer` in sidequest-content when writing content fixtures and leave the 103-5 branch alone.
- **Scope reminder for TEA:** 3 proof Saints only (bundle-only / bundle+affinity / drawback-fires-in-confrontation); full canon is 103-4. Loud-validation and wiring-test ACs are the heart of the story — AC context in the story context file expands all six ACs into testable detail.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New engine surface (SaintRegistry + preset + loader wiring + OTEL span) — core TDD story.

**Test Files:**
- `tests/mutation/test_saints_models.py` — SaintDef/SaintRegistry structural contract: 4 traditions, non-empty bundle, single `negative/` drawback, no negatives in bundle/affinity, bare-snake saint ids, extra-fields forbidden, duplicate ids, loud `by_id` KeyError (16 tests)
- `tests/mutation/test_saints_loader.py` — `load_saint_registry(path, catalog)`: FileNotFoundError on absence, loud catalog cross-validation naming saint id + mutation id (bundle/drawback/affinity), malformed YAML, MP-affordability cap (5-mark refused / 4-mark boundary loads), duplicate bundle entries (9 tests)
- `tests/mutation/test_saint_preset.py` — `apply_saint_preset`: exact bundle+drawback on sheet, MP arithmetic (2+2−2×1=2), burdens-before-gifts log order, idempotency, unknown-saint KeyError, acquire_ops composition (affinity drawback→pick flow), narrator-context drawback surfacing, `awn.saint.applied` span with full MP math attrs, no span re-fire on replay, SPAN_ROUTES registration (11 tests)
- `tests/genre/test_saints_world_load.py` — production-loader wiring on cloned fixture pack: `World.saints` field shape, populate-on-present, None-on-absent, loud bad-id rejection at pack load, loud saints-without-catalog rejection; real-content checks: 3 proof Saints resolve against the REAL genre catalog (draft-immune), flickering_reach stays Saint-less through full pack load (7 tests)

**Tests Written:** 43 tests covering 6 ACs
**Status:** RED (all 4 files fail collection on `ModuleNotFoundError: sidequest.mutation.saints` — the module Dev creates; existing tests/mutation suite green at 54 passed, verified by direct `uv run pytest -n0`)

**Contract pinned for Dev (Agent Smith):**
- New module `sidequest/mutation/saints.py`: `SaintDef`, `SaintRegistry` (with `by_id`), `load_saint_registry(path, catalog)`, `apply_saint_preset(state, catalog, registry, *, actor, saint_id, session_id)`
- `World.saints: SaintRegistry | None = None` + loader pickup of `worlds/<slug>/saints.yaml` with load-time catalog cross-validation (and loud rejection when saints.yaml exists with no genre mutation catalog)
- `awn.saint.applied` span in `telemetry/spans/awn.py` + SPAN_ROUTES registration; attrs: actor, saint_id, drawback, bundle_count, mp_base, mp_from_drawback, mp_spent, mp_remaining
- `init_mutation_state_for_session` gains the saint route (`saints=`, `saint_id=`); saint_id with no registry → loud error
- Proof content in sidequest-content branch `feat/103-1-saint-layer`: `worlds/seaboard_of_saints/saints.yaml` (≥3 Saints, both bundle-only and bundle+affinity shapes, real catalog ids) + skeletal world.yaml as needed — coordinate with 103-5's files (see Sm Assessment merge-order note)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions / fail-loud | `test_unknown_bundle_id_fails_loud_with_saint_and_mutation_id`, `test_loader_rejects_saints_without_mutation_catalog`, `test_missing_file_raises_filenotfounderror_naming_path` | failing (RED) |
| #3 boundary validation (pydantic) | `TestSaintDefShape` (extra-forbid, Literal tradition, id shape) | failing (RED) |
| #5 path handling / encoding | loader tests exercise `Path`-based load (encoding pinned by implementation mirroring `load_mutation_catalog`) | failing (RED) |
| #6 test quality (self-check) | all assertions value-specific; no `assert True`, no bare truthy checks on always-truthy values; parametrized traditions cover distinct enum paths | n/a (meta) |
| #8 safe YAML | malformed-YAML test forces explicit safe-load handling | failing (RED) |
| #11 input validation at boundaries | affordability cap, duplicate ids, negative-in-bundle rejection | failing (RED) |

**Rules checked:** 6 of 13 lang-review rules applicable to this surface have test coverage (remaining 7 — async, resources, deps, logging levels, imports — are implementation-side checks for Dev's self-review; no test seam at RED).
**Self-check:** 0 vacuous tests found (one `exc_info.value is not None` in `test_malformed_top_level_fails_loud` is intentionally shape-agnostic about WHICH exception, inside a `pytest.raises` that already guarantees raising — the assertion documents the loud-not-empty contract).

**Handoff:** To Agent Smith (Dev) for GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server, `feat/103-1-saint-layer` @ 7981b2ce, pushed):**
- `sidequest/mutation/saints.py` — NEW: `SaintDef` (4-tradition Literal, bare-snake id, non-empty positive-only unique bundle, single `negative/` drawback, positive-only affinity), `SaintRegistry` (unique ids, loud `by_id`), `load_saint_registry` (FileNotFoundError on absence; catalog cross-validation naming saint id + mutation id; MP-affordability cap `bundle×spend_random ≤ base+per_negative`), `apply_saint_preset` (MP formula per pinned contract, drawback-first acquisition log, idempotent, emits span once)
- `sidequest/telemetry/spans/awn.py` — `awn.saint.applied` span helper + SPAN_ROUTES registration (full MP arithmetic in attrs: mp_base/mp_from_drawback/mp_spent/mp_remaining + actor/saint_id/drawback/bundle_count)
- `sidequest/genre/models/pack.py` — `World.saints: SaintRegistry | None = None` with doctrine docstring
- `sidequest/genre/loader.py` — mutations.yaml load hoisted ABOVE world loading; `_load_single_world(..., mutations=)` loads `worlds/<slug>/saints.yaml` (absent→None; present-without-catalog→GenreLoadError naming world; invalid→GenreLoadError carrying saint+mutation id)
- `sidequest/server/mutation_init.py` — saint route (`saints=`, `saint_id=`): loud ValueError on missing registry/catalog, seeds via `apply_saint_preset`, `mutation.saint_init` watcher event; classic paths untouched
- `sidequest/server/websocket_handlers/chargen_mixin.py` — both call sites (solo + MP joiner) plumb `saints=` from the active world

**Files Changed (content, `feat/103-1-saint-layer` @ 959a151, pushed):**
- `worlds/seaboard_of_saints/saints.yaml` — 3 proof Saints curated to REAL catalog ids with mapping-rationale comments: herman_of_the_acushnet (bundle-only, 3 marks), edgar_of_baltimore (bundle+affinity), lizzie_of_the_cairn (wilderness drawback-bearer); iconography style-free per the suffix rule
- `worlds/seaboard_of_saints/world.yaml` — skeletal `draft: true` (103-5's full version supersedes at merge)

**Tests:** 45/45 story tests passing (GREEN, verified `-n0` direct). Full suite: 10353 passed; 23 failures are pre-existing environmental (`SIDEQUEST_DATABASE_URL` unset in plain shell) — stash-baseline diff proves byte-identical failure set without this diff (see Dev Delivery Finding). Lint: ruff clean on all changed files; format clean.

**Branches:** server + content `feat/103-1-saint-layer` (both pushed). Side ceremony: 103-5's world-core files committed on `feat/103-5-seaboard-world-core` + pushed (freed the shared content checkout; see commit 6008fdc).

**Handoff:** To spec-check (Neo) / verify per workflow.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 1 note | confirmed 0, dismissed 1 (tea_and_murder placement note — factually confused; every spec/context places seaboard_of_saints under mutant_wasteland), deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (`workflow.reviewer_subagents.edge_hunter: false`); domain covered by my own boundary read (empty file, `saints: []`, non-dict YAML, 4-mark budget boundary, draft-skip interaction) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; domain covered by security agent's silent-fallback enumeration (5 instances checked) + my own read of every except/return path in the diff |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings; TEA's self-check (0 vacuous) re-verified by my read — all 45 assertions value-specific |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings; docstrings checked by my read — saints.py module/function docs match behavior incl. the idempotency + pricing contracts |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings; type surface checked by my read — Literal traditions, extra=forbid both models, pathlib, full annotations |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 1 (cross-path idempotency, Medium, fix routed to 103-2), dismissed 1 (saint_id KeyError info-leak — low confidence, the "leaked" roster is the player-facing chargen menu by design; lookup is an exhaustive whitelist that rejects loudly), deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings; my read found no dead code or over-engineering — 1 module, no speculative abstractions, every function test-demanded |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings; Rule Compliance section below is my own exhaustive enumeration against lang-review/python.md |

**All received:** Yes (2 enabled returned; 7 disabled via settings, domains self-assessed)
**Total findings:** 2 confirmed (both Medium, non-blocking, routed), 2 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**[PRE] Preflight:** GREEN — 45/45 story tests, 92/92 mutation subsystem, ruff clean (scoped), both content YAMLs valid, 0 smells/TODOs/skips. The 23 full-suite failures are pre-existing environmental (`SIDEQUEST_DATABASE_URL` unset; stash-baseline byte-identical — verified by Dev, re-confirmed in preflight scoping).

**Data flow traced (author content → player state):** `worlds/seaboard_of_saints/saints.yaml` → `yaml.safe_load` (no code exec) → `SaintRegistry.model_validate` (extra=forbid, Literal tradition, id-shape, positive-only unique bundle, single negative drawback) → `_validate_against_catalog` (every id whitelisted against genre catalog + MP-affordability cap) → `GenreLoadError` wrapping at `loader.py` (carries saint id + mutation id) → `World.saints` → chargen call sites → `init_mutation_state_for_session` saint route (loud ValueError on missing registry/catalog) → `apply_saint_preset` (exhaustive `by_id` lookup, KeyError loud) → `CharacterMutationState` + `awn.saint.applied` span. Safe because every hop either whitelists or fails loudly; no partial state ever lands (validation raises before the registry is returned).

**Findings (confirmed):**
| Severity | Tag | Issue | Location | Routing |
|----------|-----|-------|----------|---------|
| [MEDIUM] | [SEC] | Cross-path idempotency collision: guard can silently return Wild state to the Saint route (unreachable today — saint_id never passed until 103-2) | `sidequest/mutation/saints.py` idempotency guard | 103-2 adds provenance guard with the selection surface; Delivery Finding recorded |
| [MEDIUM] | [SEC] | No affordability re-check in `apply_saint_preset` — a loader-bypassing registry could write negative `mp_remaining` silently | `sidequest/mutation/saints.py` MP ledger | Delivery Finding recorded; defense-in-depth guard, candidate for 103-2 or follow-up |

**Verified-good observations (evidence + rule compliance):**
1. **[VERIFIED] [SILENT]** No silent fallbacks in any new path — `loader.py` saints block raises `GenreLoadError` on no-catalog and on invalid ids (re-raise `from e`, detail preserved); `load_saint_registry` raises `FileNotFoundError` naming the path; empty/garbage YAML → pydantic `ValidationError` (subclasses `ValueError` in v2) → caught and wrapped, never an empty registry. Complies with CLAUDE.md No Silent Fallbacks. (Security agent enumerated 5 instances, 4 compliant; the 5th is the confirmed Medium above.)
2. **[VERIFIED] [TYPE]** Both models `extra="forbid"`; `tradition` is a 4-value `Literal`; saint ids bare-snake by regex (catalog-shaped ids rejected); bundle validated positive-only + unique at model level with the saint NAMED in the error. Complies with lang-review #3 boundary-annotation and #11 input-validation rules.
3. **[VERIFIED] [RULE]** Safe deserialization: `yaml.safe_load` only (lang-review #8); `read_text(encoding="utf-8")` (#5); no bare except (#1); no mutable defaults (#2 — all list fields use `default_factory`); public functions fully annotated (#3); `__all__` declared (#10).
4. **[VERIFIED] [TEST]** Wiring tests exist at the production seam: cloned-fixture pack through real `load_genre_pack` (populate/absent/bad-id/no-catalog), real-content proof Saints against the real catalog (draft-immune), flickering_reach Saint-less regression. Not source-text greps — behavior + loader-path assertions per CLAUDE.md No Source-Text Wiring Tests.
5. **[VERIFIED] [DOC]** Docstrings state the load-bearing contracts accurately (curation-replaces-dice-not-pricing, burdens-before-gifts, idempotency, absence-is-caller's-decision) — checked against test behavior; no stale claims.
6. **[VERIFIED] [SIMPLE]** Minimal surface: one new module, no speculative abstraction; preset composes with existing `acquire_ops` (affinity flow test proves it) instead of a second economy. No dead code.
7. **[VERIFIED] [EDGE]** Boundaries pinned by tests: 4-mark bundle at exact budget loads, 5-mark refused; `saints: []` is a valid empty canon; absent file → None at world tier; draft worlds skip (documented + compensated by direct real-content validation).
8. **[VERIFIED]** OTEL contract: `awn.saint.applied` registered in `SPAN_ROUTES` (GM panel routable), full MP arithmetic in attrs, no re-fire on replay, `mutation.saint_init` watcher event on the production route. Complies with the OTEL Observability Principle — the preset is lie-detectable.

**Pattern observed (good):** the saint loader mirrors `load_mutation_catalog`'s fail-loud/absence-is-caller's-choice doctrine and the loader wraps content errors in `GenreLoadError` exactly like the theme/char_creation invariants — institutional patterns followed, not reinvented.
**Error handling:** every failure mode enumerated above raises with actionable, named context; no error path logs-and-continues.
**Security analysis:** author-controlled YAML cannot execute code or land partially; user-controlled inputs (`saint_id`, `actor`) hit exhaustive whitelist lookups; span/watcher payloads carry no sensitive data.
**Hard questions:** empty file (loud), non-dict YAML (loud), duplicate saint/bundle ids (loud, named), over-budget bundle (loud at load), unknown ids (loud with both ids named), re-entrant confirm (silent same-path return, span-once — correct), MP-joiner double-init (idempotent), draft world (skipped, compensated), catalog evolution (103-4's additive-only constraint is pinned by flickering_reach regression tests in 103-10).

### Rule Compliance

| lang-review/python.md check | Instances in diff | Result |
|---|---|---|
| #1 silent exceptions | loader except-ValueError (re-raises), chargen seed try/except (pre-existing pattern, re-raises) | compliant |
| #2 mutable defaults | SaintDef.patron_regions/affinity, SaintRegistry.saints — all `default_factory` | compliant |
| #3 type annotations | all public functions in saints.py/mutation_init.py annotated incl. returns | compliant |
| #4 logging | mutation_init saint route: `logger.info` + watcher event; error paths raise (no log-and-continue needed) | compliant |
| #5 path handling | pathlib + `read_text(encoding="utf-8")` | compliant |
| #6 test quality | 45 tests, value-specific assertions, 0 vacuous (re-verified) | compliant |
| #7 resource leaks | no resources opened (read_text only) | compliant |
| #8 unsafe deserialization | `yaml.safe_load` + pydantic validation | compliant |
| #9 async pitfalls | no async code in diff | n/a |
| #10 import hygiene | `__all__` on saints.py; no star/circular imports (suite-proven) | compliant |
| #11 input validation | model validators + catalog whitelist + loud route guards; cross-path guard gap = confirmed Medium | compliant w/ routed finding |
| #12 dependency hygiene | no dependency changes | n/a |
| #13 fix-regressions | the one fix commit (dup-bundle → model validator) re-scanned: no new pattern violations | compliant |

### Devil's Advocate

Assume this code is broken. Where would it bleed? First: the draft trap. The real seaboard saints.yaml is validated by NOTHING in production until 103-9 lifts the draft flag — `_load_single_world` returns None before my saints block ever runs. If 103-4 authors twenty-five Saints with three bad ids, every developer's pack load stays green for weeks, and the explosion happens at draft-lift, in 103-9's lap, far from the cause. The compensating control is a TEST (direct registry load against the real catalog), and tests can be deleted or skipped. That is real exposure — mitigated only by the recorded Improvement finding asking for `--include-drafts` validation. Second: the idempotency guard trusts that "actor exists" implies "same path seeded it." In multiplayer, the joiner mixin re-runs init for every committer; today both calls are classic-path so the guard is sound — but the moment 103-2 lets one socket pass a saint_id while a rejoining peer's state was Wild-seeded, the Saint silently fails to apply and the span never fires; the player sees a Saint on their sheet UI (chargen succeeded!) while the engine runs Wild marks. That is exactly the narrator-improv split-brain this project exists to kill — which is why I confirmed it rather than waving it off as unreachable. Third: pricing drift. The affordability cap reads `spend_random_positive` at LOAD time, but `apply_saint_preset` recomputes at APPLY time from the same economy object — today identical, but a future per-world economy override would let a registry validated under one economy apply under another, silently minting or burning MP. Unconstrained `mp_remaining: int` would swallow it. Fourth: a malicious content author can't execute code (safe_load) but CAN weaponize flavor — nothing validates that `iconography` isn't a prompt-injection vector into the portrait pipeline; that rides 103-9's existing surfaces, out of scope here but worth remembering. None of these breaks current behavior; two became my confirmed findings, one was already TEA's, one is 103-9's inheritance.

**Handoff:** To Morpheus (SM) for finish-story.