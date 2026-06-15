---
story_id: "108-7"
jira_key: ""
epic: "108"
workflow: "tdd"
---
# Story 108-7: WN combat defs go beat-optional

## Story Details
- **ID:** 108-7
- **Jira Key:** (none—SideQuest has no Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/108-7-wn-combat-beat-optional-loader (sidequest-server)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-14T23:58:40Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-14T23:18:34.825678+00:00 | 2026-06-14T23:20:45Z | 2m 10s |
| red | 2026-06-14T23:20:45Z | 2026-06-14T23:37:22Z | 16m 37s |
| green | 2026-06-14T23:37:22Z | 2026-06-14T23:45:59Z | 8m 37s |
| review | 2026-06-14T23:45:59Z | 2026-06-14T23:53:22Z | 7m 23s |
| green | 2026-06-14T23:53:22Z | 2026-06-14T23:55:33Z | 2m 11s |
| review | 2026-06-14T23:55:33Z | 2026-06-14T23:58:40Z | 3m 7s |
| finish | 2026-06-14T23:58:40Z | - | - |

## Story Context

**Summary:** Gate the ≥1-beat ConfrontationDef invariant and the encounter_beat_choices↔combat-beats coupling on the bound ruleset so Without Number packs can author zero combat beats. Unblocks 108-3 (content de-nativize).

**Technical Approach:**

Two loader relaxations, BOTH gated on the bound ruleset (WithoutNumberRulesetModule family) so native packs keep failing loud:

1. **ConfrontationDef zero-beat validator (rules.py ~590):** Today, `ConfrontationDef._validate` unconditionally raises if `not self.beats`. For WN-bound combat (category=combat, win_condition=hp_depletion), this must allow ZERO beats since wn_round.py supplies the action set (attack/move/item-use/cast). The validator only sees the def, not the pack ruleset, so this check likely must MOVE to the loader (genre/loader.py) which knows `rules.ruleset`, to gate correctly on WithoutNumberRulesetModule.

2. **encounter_beat_choices validation (loader.py ~701):** Classes validate `encounter_beat_choices` against the combat beats pool. For WN packs, classes must allow empty/absent `encounter_beat_choices` (WN engine owns the action set). Keep both guards for native packs—zero beats / empty class beat-choices must still raise.

**Acceptance Criteria:**
- [ ] A beatless WN combat def (category=combat, win_condition=hp_depletion) under a bound WithoutNumberRulesetModule loads without error
- [ ] A WN class with no/empty encounter_beat_choices loads without error under WN binding
- [ ] A native pack with zero beats still raises the ≥1-beat error
- [ ] load_genre_pack green for all three WWN packs (beneath_sunden, heavy_metal, elemental_harmony) once 108-3 strips beats and encounter_beat_choices
- [ ] OTEL spans logged proving the WN-gated relaxation fired (rule.wn_beat_optional / class.wn_encounter_beats_optional or similar)

**Refs:** ADR-143, ADR-142, ADR-117 (RulesetModule), wn_round.py, rules.py, loader.py, encounter_beat_choices coupling

**Repos:** server (sidequest-server)

## Sm Assessment

**Routing:** Phased TDD. Setup → **red (TEA/Fezzik)** → green (Dev) → review (Westley) → finish (SM). Server-only, single repo (sidequest-server, branch `feat/108-7-wn-combat-beat-optional-loader` off develop).

**What's well-scoped:** The story names exact seams (rules.py:~590 ConfrontationDef ≥1-beat validator; loader.py:~701 encounter_beat_choices↔combat-beats coupling) and the doctrine that makes this safe — BOTH relaxations gate on the bound `WithoutNumberRulesetModule` family so native packs keep failing loud. This is a *bind-the-ruleset* move (ADR-143/142, SOUL "Bind the Ruleset, Don't Balance It"), not a balance tweak.

**Flags for TEA (where RED tests should bite):**
- **Seam choice is load-bearing.** The pydantic model validator only sees the def, not `rules.ruleset`. The story's own design note says the ≥1-beat check likely must MOVE to `genre/loader.py` to gate on the ruleset. Write the RED tests at the `load_genre_pack` boundary (which has the ruleset in scope), not against `ConfrontationDef` in isolation — an isolated-model test can't express the WN-gating and would couple to the wrong seam.
- **Don't couple unit tests to live content.** Per project rule, build a synthetic WN-bound fixture pack (beatless combat def + classes with empty/absent encounter_beat_choices) for the capability tests. Reserve real WWN slugs (beneath_sunden / heavy_metal / elemental_harmony) for the one integration/wiring test.
- **Today's packs still have beats.** AC4 ("green for all three WWN packs once 108-3 strips them") is forward-looking — 108-3 verifies it, not 108-7. For *this* story the live packs still carry beats and must keep loading (no regression). The NEW capability is proven by the synthetic beatless fixture, not by the real packs yet.
- **Native-still-raises is half the contract.** Every relaxation needs its mirror: a non-WN pack with zero beats / empty class beat-choices must STILL raise loud. Mutation-test both guards so the gate isn't vacuous.
- **OTEL is an AC, not a nicety.** Project doctrine: every backend fix touching a subsystem emits a watcher span so the GM panel can confirm the WN-gated path actually fired. Include a span-assertion test (cf. the without-number module wiring checklist — spans `__init__` re-export + OTEL assertions are the touchpoints reviews catch late).

**No blockers.** No stale session, no Jira (correct), merge gate clear (only open PR #871 is a draft). Handing to Fezzik.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral change to two production loader guards — pure refactor coverage is not enough; the WN-gate (allow under WN / still-raise under native) is the whole point and must be pinned both ways.

**Test File:**
- `sidequest-server/tests/genre/test_wn_beat_optional_loader.py` — 8 tests (committed `d9c93eb5`)

**Tests Written:** 8 tests covering the 5 session ACs (combat goes beatless under WN / classes may omit beat-choices under WN / native still raises / forward-looking AC4 deferred to 108-3 by design / OTEL span).
**Status:** RED — `4 failed, 4 passed` (verified twice via testing-runner, run-id `108-7-tea-red`). The 4 failures are pure feature-absence; the 4 passes are the native-mirror / over-broad / no-regression guards (correct now, must stay correct after GREEN).

| Test | Relaxation / AC | Today | Contract for Dev |
|------|-----------------|-------|------------------|
| `test_denativized_wn_pack_loads` | R1+R2 wiring (the real 108-3 end-state) | RED `GenreLoadError "at least one beat"` | a WN pack with a zero-beat combat def + empty class beat-choices LOADS |
| `test_beatless_native_combat_def_still_raises` | R1 native mirror | PASS (guard) | a **native** zero-beat combat def must STILL raise |
| `test_beatless_wn_social_def_still_raises` | R1 over-broad guard | PASS (guard) | relaxation is **combat/hp_depletion only** — a beatless *social/dial* def under WN must STILL raise |
| `test_wn_combat_def_with_beats_still_loads` | R1 no-regression | PASS (guard) | a beated WN combat def still loads (beats optional, not forbidden) |
| `test_wn_class_empty_encounter_beat_choices_loads` | R2 wiring | RED `PackError "encounter_beat_choices is empty"` | a WN `allowed_classes` class may declare empty beat-choices |
| `test_validate_class_filter_refs_native_still_raises_on_empty` | R2 native mirror | PASS (guard) | native empty beat-choices must STILL raise |
| `test_validate_class_filter_refs_wn_allows_empty` | R2 WN-gate unit | RED `PackError` | same emptied class under wwn must NOT raise |
| `test_denativized_wn_pack_emits_beat_optional_span` | AC5 OTEL | RED (load raises → no span) | loader emits `state_transition` `field="wn_beat_optional"` (`ruleset`, `confrontation_type`) when the WN gate fires |

### Rule Coverage (SideQuest server CLAUDE.md — the HOW checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (the gate must not silently weaken native) | `*_native_still_raises*`, `*_social_def_still_raises` | passing (guard) |
| Every Test Suite Needs a Wiring Test | `test_denativized_wn_pack_loads`, `test_wn_class_empty_encounter_beat_choices_loads` (real `load_genre_pack`) | failing (RED) |
| No Source-Text Wiring Tests | OTEL span + behavior assertions only — zero `read_text()`/grep-on-source | satisfied |
| OTEL Observability Principle (lie-detector on the subsystem decision) | `test_denativized_wn_pack_emits_beat_optional_span` | failing (RED) |
| Test quality — meaningful assertions | self-check: every test asserts on a value/raise; no `assert True`/`is_none`-on-always-None/`let _=` | satisfied |

**Rules checked:** 5 of 5 applicable repo rules have coverage.
**Self-check:** 0 vacuous tests. 1 self-inflicted fixture bug found+fixed during RED verification (cloned pack dir basename must equal the slug, else the loader's `genre_key`↔dirname fail-loud trips — it would have resurfaced in GREEN).

### Implementation contract (so GREEN doesn't fight the tests)
1. **Move** the `if not self.beats` raise OUT of `ConfrontationDef._validate` (rules.py:~588) — the model can't see the ruleset. Keep the rest of that validator (duplicate-id, intent-vocab, AC/dex checks) intact.
2. **Add** a loader-level beat-count gate (loader has `rules.ruleset`) that raises for a zero-beat def UNLESS the pack is WN-family **and** the def is `category=combat` / `win_condition=hp_depletion`. WN gate idiom: `isinstance(get_ruleset_module(rules.ruleset), WithoutNumberRulesetModule)` (true for swn/wwn/cwn/awn). A string-set check `{"swn","wwn","cwn","awn"}` also satisfies the tests.
3. **Gate** `_validate_class_filter_refs`'s empty-`encounter_beat_choices` raise on the same WN check (skip for WN-family).
4. **Emit** the `wn_beat_optional` `state_transition` span via `from sidequest.telemetry.watcher_hub import publish_event` (the function-local import pattern the other loader `_emit_*` helpers use), fields `{field:"wn_beat_optional", ruleset, confrontation_type}`.

**Handoff:** To Inigo Montoya (Dev) for GREEN.

## Delivery Findings

<!-- Append-only. Each agent under its own subheading. -->

### TEA (test design)
- **Gap** (non-blocking): Moving the zero-beat raise out of `ConfrontationDef._validate` removes the *model-level* beat-count guard entirely — any non-loader caller that constructs a `ConfrontationDef` directly and relied on that guard loses it. Affects `sidequest/genre/models/rules.py` (verify no production consumer outside `load_genre_pack` depends on the model raising on zero beats; the loader is the only content constructor, so this is expected, but confirm). *Found by TEA during test design.*
- **Improvement** (non-blocking): R1 and R2 are not independently shippable — stripping a combat def's beats orphans the classes' `encounter_beat_choices` refs (loader.py:~701), so a partial GREEN that implements only R1 will still fail `test_denativized_wn_pack_loads` on the class coupling. Implement both. Affects `sidequest/genre/loader.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** TEA's "model-level guard removed" Gap: the green-phase regression scan (testing-runner, run-id `108-7-dev-green`) found NO other test or production caller that constructs a beatless `ConfrontationDef` and relies on the model raising — every other `beats=[]` in the suite is a dict payload, `SimpleNamespace` fixture, or telemetry record, none of which hit the relocated validator. `load_genre_pack` is the only content constructor; the loader gate now covers it. No upstream action needed.
- **Improvement** (non-blocking): `tests/genre/test_geometry_modifiers.py::_minimal_confrontation` has a now-stale docstring ("Required fields: type/label/category plus at least one beat") — the beat is no longer required at model construction, only at load. The test still passes (its helper always supplies a beat) and the file is outside this PR's diff, so it won't surface in review; flagging so a future reader corrects the comment. Affects `tests/genre/test_geometry_modifiers.py`. *Found by Dev during implementation.*
- **Observation** (non-blocking): `tests/genre/` carries 7 PRE-EXISTING failures unrelated to 108-7 — all `AuthoredNpc` `extra_forbidden` on `location_tags` during world npcs.yaml loading (a content/model schema drift, not in any code path this story touches). Not introduced here. Affects `sidequest/genre/models/authored_npc.py` ↔ world `npcs.yaml` (someone authored `location_tags:` the model forbids). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): The new test file was committed in RED and never linted in GREEN (the green-phase `ruff check` covered only the 3 green-phase-changed files), so a `ruff check` UP035 error + a format reflow shipped undetected. Process note for future TDD stories: GREEN should lint the FULL changed set including TEA's RED-committed files. Affects `tests/genre/test_wn_beat_optional_loader.py` (fix in green-rework). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_emit_wn_beat_optional` rides `publish_event`, which is fire-and-forget — it drops silently if no event loop / no dashboard subscriber is bound (ADR-132). This is identical to the 9 sibling loader load-spans, so it's a property of the watcher bus, not a 108-7 regression; but if load-time spans ever need durable proof, the whole loader-span family (not just this one) should persist via the TelemetrySink/tx path. Affects `sidequest/telemetry/watcher_hub.py` (future watcher hardening, not this story). *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **OTEL span shaped as a `state_transition`/`field` event, not a bespoke event_type, and one span (not two)**
  - Spec source: context-story-108-7.md / session AC5
  - Spec text: "OTEL spans logged proving the WN-gated relaxation fired (rule.wn_beat_optional / class.wn_encounter_beats_optional or similar)"
  - Implementation: One `state_transition` watcher event with `field=="wn_beat_optional"` (matches the existing loader load-span idiom — `world_items`/`world_lore`), required only for the beat-count relaxation; the `encounter_beat_choices` skip is covered behaviorally, no second span.
  - Rationale: Reuses the loader's established span shape (the GM panel already groups `state_transition`/`field`); a separate event_type or a second span would over-instrument a load-time validation for no added lie-detection value.
  - Severity: minor
  - Forward impact: GM-panel span filter keys on `field=="wn_beat_optional"`.
- **AC4 (live WWN packs load) is NOT tested here**
  - Spec source: context-story-108-7.md, AC4
  - Spec text: "load_genre_pack green for all three WWN packs (beneath_sunden, heavy_metal, elemental_harmony) once 108-3 strips them"
  - Implementation: No test points at live content; the live packs still carry beats today, so the assertion is unsatisfiable until 108-3 strips them. Coverage is on the `wwn_test_pack` fixture instead.
  - Rationale: AC4 is forward-looking and is 108-3's verification, not 108-7's; project rule forbids tests pointing at live content.
  - Severity: minor
  - Forward impact: 108-3 must add the live-pack load assertion when it strips beats + encounter_beat_choices.
- **R2 native mirror tests the private `_validate_class_filter_refs` directly, not via `load_genre_pack`**
  - Spec source: context-story-108-7.md (relaxation 2)
  - Spec text: "a native pack with ... empty class beat-choices must still raise"
  - Implementation: `test_validate_class_filter_refs_native_still_raises_on_empty` drives the validator function with real wwn objects re-tagged native via `model_copy`, because no native fixture pack ships a `classes.yaml` (so no full-pack native+classes route exists).
  - Rationale: There is no live native-with-classes fixture; the function-level test is the only way to pin the native side of R2. The R2 *WN* side still has a full-pack wiring test.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Updated a pre-existing model-level test to match the relocated invariant**
  - Spec source: context-story-108-7.md, relaxation 1 ("this check likely must MOVE to the loader")
  - Spec text: "the pydantic model validator only sees the def, NOT the pack ruleset — so this check likely must MOVE to the loader (genre/loader.py)"
  - Implementation: Removed the `if not self.beats: raise` from `ConfrontationDef._validate` (rules.py) and renamed `tests/genre/test_models/test_rules.py::test_rejects_empty_beats` → `test_accepts_empty_beats`, asserting the model now accepts a zero-beat def (the gate moved to `loader.py::_validate_confrontation_beats`).
  - Rationale: The model-level test pinned the OLD invariant the story explicitly relocates; leaving it would make the suite red for an outdated contract. The new test documents the model's new behavior.
  - Severity: minor
  - Forward impact: none — the loader gate (ruleset-aware) is the single enforcement point now; covered by `test_beatless_native_combat_def_still_raises`.

### Reviewer (audit)
- **TEA: OTEL span as `state_transition`/`field`, one span** → ✓ ACCEPTED by Reviewer: matches the established loader load-span idiom (9 sibling spans use the same `state_transition`+`field` shape); one span for the headline relaxation is right-sized. (Note: span uses `component="genre.loader"` while siblings use `"genre"` — flagged as a LOW finding to align in rework, not a deviation problem.)
- **TEA: AC4 (live WWN packs) not tested here** → ✓ ACCEPTED by Reviewer: forward-looking AC genuinely belongs to 108-3; testing live content here is both unsatisfiable today (packs still have beats) and against the no-live-content-in-tests rule. Correctly deferred.
- **TEA: R2 native mirror tests `_validate_class_filter_refs` directly** → ✓ ACCEPTED by Reviewer: no native fixture ships a classes.yaml, so the function-level test (real objects re-tagged via `model_copy`, which skips re-validation) is the only honest way to pin the native side; the WN side still has a full-pack wiring test. Sound.
- **Dev: updated `test_rejects_empty_beats` → `test_accepts_empty_beats`** → ✓ ACCEPTED by Reviewer: the production change (relocating the gate off the model) legitimately invalidates the old model-level assertion; updating it to assert the model's new behavior is correct and the new test is non-vacuous (`assert c.beats == []`). Not a test-weakening — the invariant is still enforced, now at the loader (verified by `test_beatless_native_combat_def_still_raises`).
- **Undocumented divergence found:** none. The diff matches the logged deviations; no silent spec departures.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/genre/models/rules.py` — removed the unconditional `if not self.beats` raise from `ConfrontationDef._validate` (the model can't see the ruleset); left a pointer comment to the loader gate.
- `sidequest/genre/loader.py` — added `_is_without_number(ruleset)` (isinstance `WithoutNumberRulesetModule`), `_validate_confrontation_beats(rules)` (ruleset-aware beat-count gate, called in `load_genre_pack` before `_validate_class_filter_refs`), and `_emit_wn_beat_optional(...)` (the `wn_beat_optional` `state_transition` span); WN-gated the empty-`encounter_beat_choices` raise in `_validate_class_filter_refs`; imported `WinCondition`.
- `tests/genre/test_models/test_rules.py` — `test_rejects_empty_beats` → `test_accepts_empty_beats` (model now accepts empty beats; gate relocated).

**Tests:** 8/8 new tests passing (GREEN); full `tests/genre/` = 958 passed / 50 skipped / 7 pre-existing-unrelated failures (`AuthoredNpc.location_tags`, not in any path this story touches). Regression scan confirmed no other beatless-`ConfrontationDef` construction depends on the removed model raise. `ruff check` + `ruff format --check` clean on all changed files.
**Branch:** `feat/108-7-wn-combat-beat-optional-loader` (pushed, commit `ec3a09d6`).

**Self-review:**
- Wired end-to-end: the gate runs inside the production `load_genre_pack` path (verified by the full-pack `test_denativized_wn_pack_loads` / `test_wn_class_empty_encounter_beat_choices_loads`), not just the isolated validator.
- Follows project patterns: WN-family detection via `get_ruleset_module` isinstance (the established idiom); OTEL span via the loader's `_emit_*` function-local-import shape; fail-loud preserved for native + non-combat defs.
- All 5 session ACs met (AC4 forward-deferred to 108-3 by design — see TEA deviation); OTEL AC5 satisfied.
- Doctrine: this is a *removal* of the native beat requirement from the WN path (bind-the-ruleset), not a balance tweak — no native mechanic tuned (SOUL / ADR-143).

**Round-Trip 1 (review-rework, commit `2b3574bb`):** Addressed all of Westley's findings — (1) BLOCKING lint: fixed UP035 `typing.Iterator` → `collections.abc.Iterator` + `ruff format` in the test file (the file GREEN's lint pass had skipped); (2) LOW: aligned the OTEL span `component` `"genre.loader"` → `"genre"` to match the 9 sibling loader spans; (3) LOW: documented the WN `encounter_beat_choices` empty-vs-stale asymmetry. All behavior-neutral — 28/28 tests still green; `ruff check` + `ruff format --check` now clean on ALL 4 changed files (verified the full set this round, not just the green-phase subset).

**Handoff:** To Westley (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 2 (lint UP035 + format, both in new test file) | confirmed 1 (blocking lint/format) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A — assessed boundaries myself (Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 0 blocking; 1 downgraded LOW (span drop), 1 deferred (doc-gap) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — assessed test quality myself |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — assessed comments myself |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — assessed types myself |
| 7 | reviewer-security | Yes | clean | none | N/A — concur (no auth/injection/DoS surface) |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — assessed complexity myself |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — did Rule Compliance manually |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, pre-filled)
**Total findings:** 1 confirmed blocking (lint/format), 2 confirmed LOW (span component, span-drop), 1 deferred (doc-gap); 0 dismissed.

### Rule Compliance (SideQuest CLAUDE.md / SOUL.md, enumerated against the diff)

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| **No Silent Fallbacks** | `_validate_confrontation_beats` raises `PackError` for every non-WN-combat beatless def (loader.py:718); `_is_without_number` lets `UnknownRulesetError` propagate (registry.py:25); empty-choices raise kept for native (loader.py:756) | ✅ COMPLIANT — fail-loud preserved on every branch |
| **Bind the Ruleset, Don't Balance It** (ADR-143/SOUL) | gate REMOVES the beat requirement from the WN path; no native mechanic tuned/converted/gated-to-fit | ✅ COMPLIANT — removal, not balance |
| **OTEL Observability Principle** | `_emit_wn_beat_optional` emits a `state_transition` span on the gate decision | ✅ COMPLIANT (LOW nit: `component` value differs from siblings — see findings) |
| **Don't Reinvent / Wire Up What Exists** | reuses `get_ruleset_module`+`WithoutNumberRulesetModule` (the established WN idiom) and the loader `_emit_*`/`publish_event` shape | ✅ COMPLIANT |
| **Every Test Suite Needs a Wiring Test** | `test_denativized_wn_pack_loads` + `test_wn_class_empty_encounter_beat_choices_loads` exercise the real `load_genre_pack` | ✅ COMPLIANT |
| **No Source-Text Wiring Tests** | tests assert behavior + the OTEL span via monkeypatch; zero `read_text()`/grep-on-source | ✅ COMPLIANT |
| **No Stubbing / No dead code** | no stubs; `_is_without_number` helper has 2 real call sites | ✅ COMPLIANT |
| **Lint/format clean (project gate)** | `ruff check` UP035 + `ruff format` reflow in `tests/genre/test_wn_beat_optional_loader.py:42` | ❌ VIOLATION — blocks merge (the REJECT basis) |

### Observations

- `[PREFLIGHT]` **[HIGH/blocking — lint]** `ruff check` fails UP035 (`from typing import Iterator` must be `from collections.abc import Iterator`) and `ruff format --check` would reflow, both at `tests/genre/test_wn_beat_optional_loader.py:42`. The project lint gate (`just server-lint` / `check-all`) would reject this. Mechanical, auto-fixable.
- `[MINE]` **[LOW]** OTEL span uses `component="genre.loader"` (loader.py:698) while all 9 sibling loader load-spans use `component="genre"` (lines 976–2377). For consistent GM-panel Subsystems-tab grouping, align to `"genre"`.
- `[SILENT]` **[LOW, downgraded from medium]** `_emit_wn_beat_optional` → `publish_event` is fire-and-forget and drops silently with no bound loop/subscriber (ADR-132). Real, but identical to all 9 sibling loader spans — a watcher-bus property, not a 108-7 regression. The OTEL test proves the *call* fires. Noted as a future watcher-hardening item (delivery finding), not blocking.
- `[SILENT]` **[LOW, deferred]** WN empty-`encounter_beat_choices` `continue` skips that class's missing-ref check, but only for empty lists (a non-empty WN class against a zero-beat pool still fails loud on every ref). Correct by design; a one-line docstring note would help a future migrator. Non-blocking.
- `[SEC]` **[VERIFIED clean]** No injection/DoS/leakage. `rules.confrontations` is a pre-parsed bounded `list[ConfrontationDef]`; `cd.category`/`cd.win_condition`/`rules.ruleset` are pydantic-validated; the span carries only a ruleset slug + authored confrontation type (GM-only, no PII). Concur with reviewer-security.
- `[VERIFIED]` WN gate is precisely scoped: `wn_combat = is_wn and cd.category == "combat" and cd.win_condition == WinCondition.hp_depletion` (loader.py:715–717) — a beatless social/dial def, a beatless combat/`dial_threshold` def, and any beatless native def all still raise. Evidence: `test_beatless_native_combat_def_still_raises` + `test_beatless_wn_social_def_still_raises` green. Complies with ADR-143 + No Silent Fallbacks.
- `[VERIFIED]` Fail-loud on unknown ruleset: `_is_without_number` calls `get_ruleset_module`, which raises `UnknownRulesetError` (registry.py:25) — propagates uncaught. No silent default. (Minor, acceptable: an unknown ruleset now fails at line 2017 instead of the later 2356 — both fail loud.)
- `[VERIFIED]` Wiring: `_validate_confrontation_beats(rules)` is called unconditionally in `load_genre_pack` (loader.py:2017), before `_validate_class_filter_refs`, so classless packs are covered — proven by the no-classes `test_genre` native mirror raising.
- `[TEST]` (analyzer disabled — my assessment): new tests are non-vacuous — real `load_genre_pack`, native mirrors both ways, OTEL span asserted on concrete fields; `test_accepts_empty_beats` asserts `c.beats == []`. No `assert True`/always-None traps.
- `[DOC]` (analyzer disabled — my assessment): new docstrings/comments accurately cite story 108-7 + ADR-143 and the relocation; the only stale comment is in `test_geometry_modifiers.py` (out of diff; Dev already logged it non-blocking).
- `[TYPE]` (type-design disabled — my assessment): `WinCondition` enum comparison is correct (StrEnum), `_is_without_number` returns `bool`, no stringly-typed regression introduced.
- `[SIMPLE]` (simplifier disabled — my assessment): `_is_without_number` de-duplicates the WN check across its 2 call sites — justified DRY, not over-engineering; no dead code.
- `[RULE]` (rule-checker disabled — my assessment): see Rule Compliance table — all SideQuest rules compliant except the lint gate.

### Devil's Advocate

Assume this is broken. The most concrete breakage is real and confirmed: `ruff check` fails on the new test file, so any CI/`check-all` run rejects the branch — the suite is "green" only because the green phase linted three of four changed files and skipped the TEA-committed test. That is the exact class of gap (a file linted by nobody) that ships lint debt. Beyond that: a malicious or fat-fingered pack could set `ruleset:` to garbage — but `get_ruleset_module` raises `UnknownRulesetError`, so that path fails loud rather than silently treating the pack as native (which would be the dangerous outcome, since native would wrongly *reject* a beatless combat def or, worse, a future bug could wrongly *accept* one). A subtler trap: an author writes a genuine combat encounter but mistypes `category: social`; their beatless WN combat def now raises "must have at least one beat," a confusing message for someone who believes they authored combat — but that is correct fail-loud on a real authoring error, not a false negative. Could a beatless def slip through unnoticed? No: the three-way `and` is exhaustive and the social/native mirror tests pin both negative branches. The genuinely unreliable part is the lie detector itself — `publish_event` drops the `wn_beat_optional` span when no dashboard is subscribed (i.e. at server startup, which is exactly when packs load), so a developer asking "did the WN gate actually fire in production?" may find no span and wrongly conclude it didn't. That weakness is real but inherited from every loader load-span and the watcher bus design (ADR-132), not introduced here, so it is a subsystem-wide hardening item rather than a 108-7 blocker. A confused user? A content author who empties `encounter_beat_choices` on a WN class but forgets to strip stale entries gets a loud per-ref `PackError` — good. Net: one true blocker (lint), no correctness or security defects.

## Reviewer Assessment

**Verdict:** REJECTED (lint/format only — green-rework; no correctness, security, or design defects)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] (blocking lint) | `ruff check` UP035 + `ruff format` reflow | `tests/genre/test_wn_beat_optional_loader.py:42` | `from typing import Any, Iterator` → `from typing import Any` + `from collections.abc import Iterator`; then `uv run ruff format tests/genre/test_wn_beat_optional_loader.py` |
| [LOW] (batch with rework) | OTEL span `component` inconsistent with 9 sibling loader spans | `sidequest/genre/loader.py:698` | `component="genre.loader"` → `component="genre"` |
| [LOW] (optional) | Doc-gap: WN empty-vs-stale `encounter_beat_choices` asymmetry | `sidequest/genre/loader.py:~750` | one-line note that a non-empty WN class against a zero-beat pool fails loud per-ref (Dev's discretion) |

**Why not a correctness/security reject:** The relaxation is precisely scoped and fail-loud on every negative branch (verified by the native + social mirror tests); `[SEC]` clean; `[SILENT]` findings are bus-design, not regressions. The ONLY merge blocker is the lint gate — hence **green rework** (back to Dev), not red rework.

**Dispatch tags present:** `[EDGE]` (disabled — covered in Devil's Advocate), `[SILENT]` (2 findings, both LOW/deferred), `[TEST]` (assessed — non-vacuous), `[DOC]` (assessed — clean), `[TYPE]` (assessed — clean), `[SEC]` (clean), `[SIMPLE]` (assessed — clean), `[RULE]` (Rule Compliance table — one lint violation).

**Data flow traced:** pack `rules.yaml` → `_load_rules_config` (pydantic parse, no longer raises on empty beats) → `load_genre_pack` → `_validate_confrontation_beats(rules)` (ruleset-aware gate; raises for native/non-combat beatless, emits span + allows for WN combat) → `_validate_class_filter_refs` (WN-skips empty class choices). Safe: every non-relaxed branch fails loud.

**Handoff:** Back to Inigo Montoya (Dev) for green-rework — fix the lint/format in the test file and align the span `component`; the two LOW nits are quick and the rest of the implementation is approved on the merits.

---

# Round-Trip 2 — Re-review (commit `2b3574bb`)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | 0 — blocker RESOLVED (lint/format/pyright clean, 28/28 green) | confirmed 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A — covered in Round-1 Devil's Advocate (logic unchanged) |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | N/A — all fail-loud checkpoints re-confirmed |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | N/A — tests unchanged except import; assessed |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | N/A — new doc comment reviewed, accurate |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — no type change in rework |
| 7 | reviewer-security | Yes | clean | none | N/A — span change is an inert string literal |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — no complexity added |
| 9 | reviewer-rule-checker | No | Skipped | disabled | N/A — lint rule now compliant |

**All received:** Yes (3 enabled returned; 6 disabled via settings)
**Total findings:** 0 — all 3 Round-1 findings resolved, 0 new.

## Reviewer Assessment

**Verdict:** APPROVED

**Round-1 findings — resolution verified:**
- `[RULE]`/`[PREFLIGHT]` **[was HIGH/blocking]** lint UP035 + format → RESOLVED: `from collections.abc import Iterator`, `ruff check` "All checks passed!", `ruff format --check` "4 files already formatted" across ALL 4 changed files (this round the FULL set was linted, closing the green-phase gap). 28/28 tests green, pyright clean.
- `[SIMPLE]`/mine **[was LOW]** span `component` → RESOLVED: `"genre.loader"` → `"genre"` (loader.py:698), now consistent with the 9 sibling loader load-spans.
- `[SILENT]`/`[DOC]` **[was LOW]** WN `encounter_beat_choices` asymmetry → RESOLVED: documented inline (loader.py:754-759); silent-failure re-pass confirms a non-empty WN class still fails loud per-ref.

**Re-review dispatch tags:** `[EDGE]` (disabled — logic unchanged since Round 1, Devil's Advocate stands), `[SILENT]` (re-ran — clean), `[TEST]` (import-only test change — non-vacuous, 28/28 green), `[DOC]` (new comment accurate), `[TYPE]` (no type change), `[SEC]` (re-ran — clean), `[SIMPLE]` (span literal only, no complexity), `[RULE]` (lint now compliant — the one Round-1 violation is fixed).

**Deviations:** No new deviations introduced by the rework (all changes were responses to Round-1 findings); the four logged deviations remain ACCEPTED (audited Round 1).

**Data flow traced:** pack `rules.yaml` → `_load_rules_config` (parse; model no longer raises on empty beats) → `load_genre_pack` → `_validate_confrontation_beats` (WN-aware gate; raises native/non-combat beatless, emits `wn_beat_optional` span + allows WN combat) → `_validate_class_filter_refs` (WN-skips empty class choices). Every non-relaxed branch fails loud — re-confirmed by silent-failure.
**Pattern observed:** ruleset-aware gate relocated off the model to the loader (the only place `rules.ruleset` is in scope) — the correct seam; reuses `get_ruleset_module`/`WithoutNumberRulesetModule` and the loader `_emit_*` span idiom.
**Error handling:** fail-loud preserved on every branch (PackError for native/non-combat; UnknownRulesetError propagates on bad ruleset) — `sidequest/genre/loader.py:702-720`.

**Handoff:** To Vizzini (SM) for finish-story.