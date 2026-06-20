---
story_id: "152-3"
jira_key: ""
epic: "152"
workflow: "tdd"
---
# Story 152-3: [TEST] Restore the chargen class-surface tests

## Story Details
- **ID:** 152-3
- **Jira Key:** (none — YAML-tracked story)
- **Workflow:** tdd
- **Stack Parent:** 152-2 (complete — stack root)
- **Type:** bug
- **Repos:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T21:21:01Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T20:46:13.635876+00:00 | 2026-06-20T20:48:55Z | 2m 41s |
| red | 2026-06-20T20:48:55Z | 2026-06-20T21:01:51Z | 12m 56s |
| green | 2026-06-20T21:01:51Z | 2026-06-20T21:13:08Z | 11m 17s |
| review | 2026-06-20T21:13:08Z | 2026-06-20T21:21:01Z | 7m 53s |
| finish | 2026-06-20T21:21:01Z | - | - |

## SM Assessment

**Setup complete — routing to TEA (Fezzik) for RED phase.**

- **Story shape:** Test-restoration + surface-reconciliation under epic-152 (WN full action set). Architect triage (2026-06-20) classifies the `[None x6]` failures in `test_cc_chargen_e2e` (4) and `test_class_signature_wiring` (6) as a **STALE TEST, not a production regression**. No engine change is required; the work is test-side.
- **Dependency:** `depends_on 152-2` — verified `done` (server PR #996 merged). The epic-152 action-set surface is now settled, so the assertions can be reconciled against it.
- **Two-part root cause (per design doc `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md`):**
  1. `_build_character`'s chargen walk naively requires EVERY choice-scene to contain a `class_hint==target_class` choice, so it dies on `the_trade` (6 background choices, no class_hint). It never adapted to the 120-1 reconciliation that added `the_trade` alongside `the_calling`. Class-selection content is INTACT (`char_creation.yaml:23/29/35`).
  2. The tests assert de-nativization-coupled surface (`committed_blow` in `class_moves`; Mage `class_moves` populated from `encounter_beat_choices`). Under the synthesized WN action set, a WN class carries no per-class combat beats (`encounter_beat_choices -> []` per 108-7) — the combat menu is the WWN action set (attack/cast/Total Defense/Fighting Withdrawal), not per-class beats.
- **Intended fix (for Dev in GREEN, defined by TEA in RED):** (1) make the walk pick the class choice on `the_calling` and a background choice on `the_trade` (and any future choice-scene) rather than assuming a single class scene; (2) reconcile the `class_moves`/signature assertions to the de-nativized surface.
- **Scope:** server-only, no content changes. Jira skipped (no integration; YAML-tracked).
- **Risk to TEA:** the RED assertions are the deliverable here — make sure the reconciled assertions pin the *new* surface (WWN action set, empty per-class beats), not the old de-nativization-coupled one, or GREEN will chase a stale target.

## TEA Assessment

**Tests Required:** Yes (test-restoration / surface-reconciliation — no production code touched)
**Reason:** N/A

**Test Files:**
- `tests/integration/test_class_signature_wiring.py` — **edited by TEA (RED).** Reconciled the
  stale pre-de-nativization `class_moves` assertions to the epic-152 / ADR-143 surface.
- `tests/integration/test_cc_chargen_e2e.py` — **left unchanged by TEA.** Its assertions
  (`char_class`, ablative HP, kit, archetype, `qualifying_classes`) are already
  de-nativization-correct; its only break is the shared brittle walk → owned by Dev/GREEN.

**What I changed (assertion reconciliation only):**
- Added a module-level `_COMBAT_BEAT_IDS` denylist (`committed_blow, strike, attack, cast_spell,
  brace, break_contact`).
- Warrior test: replaced `assert "committed_blow" in move_ids` (stale — committed_blow was a
  *native* combat beat, stripped by 108-3) with the de-nativized invariant: committed_blow is
  ABSENT, no per-class combat beat appears at all, `class_moves` still resolves the surviving
  chase/negotiation DIAL beats (non-empty + every move provenance-traceable to the class's own
  `encounter_beat_choices` + every label resolves).
- Mage test: strengthened the same way (cast is the WN `cast` action gated by the `cast_spell`
  class_filter — story 152-2 — not a per-class encounter beat).
- Updated the stale section-header comment + docstrings that claimed "class_moves carry the
  Warrior's combat beats" / "committed_blow appears in class_moves".
- Signature-pair (`{Killing Blow, Veteran's Luck}`, `{Read the Worked Stone}`) and
  pronoun-agnostic prose assertions: **unchanged** — measured intact.

**Tests Written:** 0 net-new; 2 assertion blocks reconciled covering AC-2. AC-1/AC-3 (the walk
reaching confirmation, all 11 tests green) land in GREEN once Dev fixes the walk.
**Status:** RED (10 fail at the brittle 2-choice-scene walk on `the_trade`; 1 pass —
`test_e2e_qualifying_classes_observable_from_pack`, which is walk-independent).

**Why still RED with reconciled assertions:** the runtime failure is at the walk
(`_build_character` / `_drive_chargen`: `assert idx is not None` assumes EVERY choice-scene is the
class scene, so it dies on `the_trade`'s 6 background choices → `[None×6]`). My reconciled
assertions are never reached in RED. I verified their *logic* out-of-band against the real
`party_member_from_character` → `sheet.class_moves` path with a corrected walk — **all 11
reconciled predicates pass** (Warrior + Mage signature/denylist/provenance/label checks). So the
GREEN target is proven reachable; Dev only needs the walk fix.

### Dev / GREEN handoff — the walk fix (both files)

In `_build_character` (test_class_signature_wiring.py) and `_drive_chargen` (test_cc_chargen_e2e.py),
the choice-scene loop must stop assuming a single class scene. On a choice-scene, if a choice's
`mechanical_effects.class_hint == target_class` pick it (the_calling); otherwise pick a valid
background choice (e.g. index 0) instead of asserting (the_trade — and any future choice-scene).
The background choice sets `background`/`focus_id`/`skill_grants` only (no `class_hint`), so it does
not affect `char_class`, kit, archetype, or `class_moves` — every existing assertion stays valid for
any background pick. **No production code changes** (AC-4); the fix is entirely in the two test
helpers.

### Rule Coverage

| Rule (CLAUDE.md / lang-review) | Test(s) | Status |
|--------------------------------|---------|--------|
| Wiring test (real pack → loader → builder → views → protocol sheet) | `test_warrior_chargen_yields_signature_pair_in_state_mirror`, `test_mage_chargen_yields_read_worked_stone_signature` | RED (walk) |
| No vacuous assertions (denylist guarded by non-empty + provenance, not bare `not in`) | both reconciled blocks | RED (walk) |
| No source-text wiring asserts | n/a — behavior asserted via resolved `sheet.class_moves`, not source grep | ok |
| Bind-don't-balance surface (no per-class combat beat under WN) | `_COMBAT_BEAT_IDS` denylist asserts | RED (walk) |

**Rules checked:** wiring, vacuous-assertion, no-source-text, ADR-143 surface — all covered.
**Self-check:** 0 vacuous tests introduced; the `not in` denylist is paired with a non-empty +
provenance-subset assertion so it cannot pass on an empty `class_moves`.

**Handoff:** To Dev (Inigo Montoya) for the walk fix.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed (test-only; no production code):**
- `tests/integration/test_class_signature_wiring.py` — walk fix in `_build_character`: on a
  choice-scene with no `class_hint==target_class` choice (the_trade), pick the first choice instead
  of asserting. (TEA's assertion reconciliation already committed in RED.)
- `tests/integration/test_cc_chargen_e2e.py` — same walk fix in `_drive_chargen`, PLUS world-merged
  equipment for the heal-potion test (see deviation).

**The walk fix (AC-1):** both helpers stopped assuming every choice-scene is the class scene. The
class choice is taken on `the_calling`; any non-class choice-scene (the_trade's six background
choices — `background`/`focus_id`/`skill_grants`, no `class_hint`) takes index 0. Background does
not affect class/kit/archetype/class_moves, so every existing assertion holds for any pick.

**Second root, found in GREEN (the heal-potion test):** once the walk reached confirmation,
`test_e2e_warrior_kit_always_includes_exactly_one_heal_potion` still failed — the Warrior's kit was
all `wwn_*` items, no `potion_healing`. Root: the 106-4 heal guarantee was relocated from the genre
tier to the **beneath_sunden world tier** (120-1/120-4, ADR-140/145 — the Potion of Mending has no
WWN SRD analog; the genre `equipment_tables.yaml` literally documents `guaranteed_grants: {}` "the
WWN-pure genre baseline grants nothing"). The test built with genre-only `pack.equipment_tables`, so
the world-tier guarantee never fired. **Content is correct-by-design; the test was stale.** Fixed by
giving `_drive_chargen` an optional `world_slug` that world-merges via the **production**
`resolve_equipment_tables` (exactly what `connect.py:942` does at real chargen); the heal test now
loads `beneath_sunden`. Measured: all 25 warriors get exactly one heal. This makes the test a
*stronger* wiring test — it now exercises the real production world-merge path it previously bypassed.

**Tests:** 11/11 passing (GREEN) — `test_cc_chargen_e2e.py` (5) + `test_class_signature_wiring.py`
(6). Verified via testing-runner (`152-3-dev-green-confirm`). All ACs met: AC-1 (walk reaches
confirmation), AC-2 (TEA's de-nativized class_moves assertions — now reached and passing), AC-3 (both
files green; class selection + Calling signatures + pronoun-agnostic prose all still asserted), AC-4
(no production code changed — the heal fix calls an existing production function).

**Blast radius:** confined to the two files; `_build_character`/`_drive_chargen` are module-local
helpers with no external importers, and no production code changed → no broader-suite regression risk.
**Branch:** `feat/152-3-restore-chargen-class-tests` (pushed).

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 11/11 green, ruff check + format clean, 0 smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 | confirmed 1 (downgraded to Medium, non-blocking), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test-quality assessed by Reviewer directly) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A — no auth/tenant/secret/injection surface |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rule compliance assessed by Reviewer directly) |

**All received:** Yes (3 enabled returned, 6 disabled pre-filled)
**Total findings:** 1 confirmed (Medium, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

Test-only change across two integration files; no production code touched (verified
`git diff develop...HEAD`). The walk fix and the de-nativized class_moves reconciliation are
correct and green; the one substantive finding (silent-fallback) is a latent test-robustness
improvement that does not block.

### Observations (8)

1. **[VERIFIED]** Walk fix is correct for current content — `the_calling` carries all three
   `class_hint`s (`caverns_and_claudes/char_creation.yaml:23/29/35`), so `idx` is always found there
   and the new `idx = 0` branch fires ONLY on `the_trade` (a background scene whose choices carry no
   `class_hint`), where picking the first choice is correct. Evidence: diff + content; no current
   wrong-class masking exists.
2. **[SILENT] [MEDIUM, non-blocking]** The `if idx is None: idx = 0` fallback (both
   `_build_character` and `_drive_chargen`) does not distinguish a *background* choice-scene from a
   *class-selection* scene that is merely missing the target class. The original `assert idx is not
   None` failed loud on "target class absent from this scene"; the new code silently picks choice 0
   and the pre-existing last-wins late-injection masks it, so a future content refactor that drops a
   Calling from `the_calling` could pass while the walk is wrong. **Confirmed, not dismissed** (it
   aligns with the critical "No Silent Fallbacks" rule). **Downgraded to Medium / non-blocking**
   because: it is test-helper code (not production config-masking), the path is **provably
   unreachable** as a wrong-class mask with current content (obs. 1), and the test is green and
   correct today. Recommended (non-blocking) follow-up: gate the loud assert on a
   "scene-is-class-selection" discriminator (`any(c.mechanical_effects and
   c.mechanical_effects.class_hint for c in scene.choices)`) and keep `idx = 0` only for
   class-neutral scenes — preserves the protective signal the original assert provided. Recorded as a
   Delivery Finding below.
3. **[VERIFIED] [TEST]** The reconciled class_moves assertions are NON-vacuous — `assert move_ids`
   (non-empty) is paired with the `_COMBAT_BEAT_IDS` denylist, a provenance subset
   (`move_ids <= set(class_def.encounter_beat_choices)`), and a label-resolution check, so the
   denylist cannot pass on an empty `class_moves`. This closes the exact vacuous-`not in` trap. Evidence:
   `test_class_signature_wiring.py` Warrior block (≈197–223) and Mage block (≈244–258).
4. **[VERIFIED]** The `world_slug` fix mirrors production — `resolve_equipment_tables(pack,
   world_slug)` is exactly the call at `sidequest/handlers/connect.py:942`; the heal-potion test now
   exercises the real world-merge path it previously bypassed, and the world-tier `guaranteed_grants`
   (beneath_sunden Potion of Mending) deterministically yields exactly one heal (measured 25/25).
5. **[VERIFIED]** Blast radius confined to the two files — `_build_character` / `_drive_chargen` are
   module-local with no external importers (the other `_build_character` in
   `test_114_10_four_pack_fate_gear.py:57` is a separate local function). No production code changed,
   so no broader-suite regression risk. Evidence: grep + git diff.
6. **[SEC]** Clean (reviewer-security) — `world_slug` is a literal at every call site, used only as a
   dict key + OTEL string; `CONTENT_ROOT` is anchored to `__file__` with hardcoded segments; no auth,
   tenant, secret, or injection surface. MagicMock stubs the repositories.
7. **[DOC]** Comments/docstrings updated accurately — the stale "class_moves carry the Warrior's
   combat beats" / "committed_blow appears in class_moves" prose was corrected to the de-nativized
   reality, and the `_COMBAT_BEAT_IDS` constant + heal-test docstring document the ADR-143 / world-tier
   rationale precisely. No stale/misleading comments introduced.
8. **[VERIFIED]** Lint + format + tests green (reviewer-preflight) — `ruff check` clean,
   `ruff format --check` clean, 11/11 pass.

### Tag coverage

`[EDGE]` skipped (disabled). `[SILENT]` obs. 2 (confirmed, Medium/non-blocking). `[TEST]` obs. 3
(reviewer assessed directly — test_analyzer disabled). `[DOC]` obs. 7 (reviewer assessed directly —
comment_analyzer disabled). `[TYPE]` skipped (disabled) — only new annotation is `world_slug: str |
None = None`, correct. `[SEC]` obs. 6 (clean). `[SIMPLE]` skipped (disabled) — diff is minimal, no
over-engineering observed. `[RULE]` reviewer assessed directly (rule_checker disabled) — see Rule
Compliance.

### Rule Compliance (python lang-review checklist + CLAUDE/SOUL)

- **#1 Silent exception swallowing** — no try/except added by the diff. The control-flow `idx = 0`
  fallback is the subject of obs. 2 (the "No Silent Fallbacks" angle) — confirmed Medium/non-blocking.
- **#2 Mutable default args** — none; `world_slug: str | None = None` is an immutable default.
- **#3 Type annotations at boundaries** — the new param is annotated; helpers are private (exempt).
- **#4 Logging** — n/a (no logging added).
- **#5 Path handling** — `CONTENT_ROOT` unchanged, static, anchored to `__file__`; no new path logic.
- **#6 Test quality** — no `assert True`, no bare truthy-only checks (the `assert move_ids` is guarded
  by denylist+provenance — obs. 3), no new skips, no mock-target issues, parametrized prose test
  unchanged (distinct cases). COMPLIANT.
- **#7 Resource leaks / #8 Unsafe deserialization** — none.
- **CLAUDE "Every Test Suite Needs a Wiring Test" / "Verify Wiring"** — the heal test now hits the
  real `resolve_equipment_tables` production path (stronger wiring). COMPLIANT.
- **CLAUDE "No Source-Text Wiring Tests"** — assertions are on resolved `sheet.class_moves` /
  inventory, not source greps. COMPLIANT.
- **SOUL "Bind, Don't Balance" (ADR-143)** — the de-nativized assertions correctly pin "no per-class
  combat beat under WN," reinforcing the doctrine. COMPLIANT.

### Devil's Advocate

Assume this is broken. The loudest attack is obs. 2: the review is approving a change that *deletes a
loud assert*. A malicious or careless future content edit — reorder `the_calling`, split it, drop the
Mage Calling, or move class selection into a later scene — could make `_drive_chargen(target_class=
"Mage")` silently pick choice 0 (a non-Mage), and the last-wins late-injection would still stamp
`char_class="Mage"`, so even `test_e2e_chargen_produces_classed_mage` would pass on a walk that never
actually selected Mage. The test suite would then green-light a chargen flow that no real player could
reproduce. That is a genuine erosion of the wiring test's purpose, and it is why I confirmed (did not
dismiss) the finding. What stops it from blocking: with the *current* content the branch is
unreachable as a wrong-class mask (the_calling provably offers all three Callings), the change is
confined to test helpers, and the green suite is correct today — so the risk is latent, not live. A
confused author reading the helper might also assume `idx = 0` is "safe everywhere," which the
recommended discriminator would document away. Second attack: does world-merging equipment in the heal
test leak world items into the *other* tests' genre-only assertions? No — `world_slug` defaults to
`None`, so only the heal test merges; `test_e2e_chargen_produces_classed_mage`'s genre-only subset
assertion is untouched and still passes (verified preflight). Third: does calling
`resolve_equipment_tables` emit an OTEL span that could blow up in a test with no watcher session? No —
preflight is green and the production path tolerates a session-less publish. No new blocking issue
surfaced; the devil's advocate reinforces obs. 2 as a worthwhile non-blocking follow-up.

**Data flow traced:** `world_slug="beneath_sunden"` → `resolve_equipment_tables(pack, slug)` →
world-merged `guaranteed_grants` → `CharacterBuilder.with_equipment_tables` → `character.core.inventory`
→ heal assertion (safe: literal slug, static content root, no untrusted input).
**Pattern observed:** non-vacuous assertion design (denylist + provenance + non-empty) at
`test_class_signature_wiring.py:197–223`.
**Error handling:** the `idx = 0` fallback replaces a loud assert — confirmed as obs. 2 (Medium,
non-blocking).

**Handoff:** To SM for finish-story.

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Improvement** (non-blocking): The brittle "find the class choice or assert" walk is duplicated
  across `_build_character` (test_class_signature_wiring.py) and `_drive_chargen`
  (test_cc_chargen_e2e.py). Affects both files (Dev must fix BOTH; a shared walk helper would
  prevent the next recurrence — but extraction is out of this story's scope). *Found by TEA during
  test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The 2026-06-20 design-doc triage attributed all 4
  `test_cc_chargen_e2e` failures to the brittle walk, but
  `test_e2e_warrior_kit_always_includes_exactly_one_heal_potion` had a SECOND, distinct stale root —
  the genre→world relocation of the 106-4 heal guarantee (120-4 / ADR-140). Affects
  `docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md` (future chargen-test triage should
  check the equipment genre/world tier, not just the walk). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The chargen-walk fallback `if idx is None: idx = 0` (in
  `_build_character` and `_drive_chargen`) discards the original loud `assert idx is not None`
  wholesale instead of narrowing it. Affects `tests/integration/test_class_signature_wiring.py` +
  `tests/integration/test_cc_chargen_e2e.py` (gate the loud assert on a
  scene-is-class-selection discriminator — `any(c.mechanical_effects and c.mechanical_effects.class_hint
  for c in scene.choices)` — and keep `idx = 0` only for class-neutral scenes; preserves the
  protective signal per "No Silent Fallbacks"). Latent/test-only — unreachable with current content
  (the_calling offers all three Callings), so non-blocking. *Found by Reviewer during code review.*

## Design Deviations

No deviations recorded at setup.

### TEA (test design)
- **Reconciled assertions strengthened beyond a bare `committed_blow not in` flip**
  - Spec source: context-story-152-3.md, AC-2
  - Spec text: "class_moves / signature assertions reflect the de-nativized WN combat surface ... not the pre-strip committed_blow/per-class beat model — assertions updated, not deleted"
  - Implementation: Beyond flipping `committed_blow in` → `not in`, added a `_COMBAT_BEAT_IDS` denylist assertion (no per-class combat beat of any kind) plus a provenance-subset assertion (`class_moves ⊆` the class's own `encounter_beat_choices`) and a non-empty + label-resolution check, for both Warrior and Mage
  - Rationale: A bare `not in committed_blow` would pass vacuously on an empty `class_moves`; the denylist + non-empty + provenance + label set pins the real de-nativized invariant (combat removed, chase/negotiation DIAL beats survive and wire) without over-coupling to specific beat ids
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Heal-potion test reconciled to the world tier (beyond the literal walk fix)**
  - Spec source: context-story-152-3.md, AC-3 + AC-4; design doc 2026-06-20-wn-full-action-set-design.md
  - Spec text: "test_cc_chargen_e2e and test_class_signature_wiring are green" (AC-3); the triage attributed all 4 test_cc_chargen_e2e failures to the brittle walk
  - Implementation: After the walk fix, `test_e2e_warrior_kit_always_includes_exactly_one_heal_potion` still failed on a SECOND stale root the triage missed — the 106-4 heal guarantee was relocated from genre to the beneath_sunden WORLD tier (120-1/120-4, ADR-140/145), and the test built with genre-only equipment. Gave `_drive_chargen` an optional `world_slug` that world-merges via the production `resolve_equipment_tables` (mirrors connect.py:942); the heal test now loads beneath_sunden. No production code changed.
  - Rationale: Content is correct-by-design (genre baseline grants nothing; heal is world-tier bespoke, no WWN SRD analog). The faithful fix is to exercise the real production world-merge path, not weaken the assertion — making it a stronger wiring test. AC-3 requires the file green, so the fix is in-scope; AC-4 preserved (no production change — calls an existing function).
  - Severity: minor
  - Forward impact: none — confined to the test file; sibling tests stay genre-only.

### Reviewer (audit)
- **TEA: Reconciled assertions strengthened beyond a bare `committed_blow not in` flip** → ✓ ACCEPTED
  by Reviewer: the strengthening (denylist + non-empty + provenance subset + label resolution) is
  exactly what makes the de-nativized assertion non-vacuous — sound, and aligned with the
  no-vacuous-assertion rule.
- **Dev: Heal-potion test reconciled to the world tier (beyond the literal walk fix)** → ✓ ACCEPTED
  by Reviewer: content is correct-by-design (heal is world-tier bespoke, no WWN SRD analog); driving
  the test through the production `resolve_equipment_tables` path is the faithful fix and a stronger
  wiring test, not an assertion weakening. In-scope per AC-3 (file must be green); AC-4 preserved (no
  production code changed — calls an existing function).
- **No undocumented deviations found.** The `idx = 0` walk fallback matches TEA's handoff spec
  ("otherwise pick a valid background choice, e.g. index 0"); its over-broadness is captured as a
  non-blocking code-review finding above, not a spec deviation.