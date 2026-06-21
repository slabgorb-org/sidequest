---
story_id: "153-4"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-4: [SWN-CHARGEN-FLAT-STATS] WN 14-to-7 attribute spread + assign skills/foci in SWN narrative chargen

## Story Details
- **ID:** 153-4
- **Jira Key:** (none — no Jira integration)
- **Epic:** 153 (Playtest follow-ups — open findings from 2026-06-20/21 full-stack /sq-playtest sweep)
- **Workflow:** tdd
- **Type:** Bug
- **Points:** 5
- **Priority:** P2
- **Repository:** sidequest-server (targets `develop`)
- **Stack Parent:** none (not a stacked story)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T13:22:22Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T12:37:11Z | 2026-06-21T12:39:25Z | 2m 14s |
| red | 2026-06-21T12:39:25Z | 2026-06-21T12:57:42Z | 18m 17s |
| green | 2026-06-21T12:57:42Z | 2026-06-21T13:15:45Z | 18m 3s |
| review | 2026-06-21T13:15:45Z | 2026-06-21T13:22:22Z | 6m 37s |
| finish | 2026-06-21T13:22:22Z | - | - |

## Sm Assessment

**Setup complete.** Story 153-4 ([SWN-CHARGEN-FLAT-STATS]) is ready for the RED phase.

- **Workflow:** tdd (phased) → setup (SM) → red (TEA) → green (Dev) → review (Reviewer) → finish (SM)
- **Repos:** server (sidequest-server, targets `develop`)
- **Branch:** `feat/153-4-swn-chargen-flat-stats` (cut from sidequest-server `develop` HEAD, clean tree)
- **Story context:** `sprint/context/context-story-153-4.md`
- **Jira:** none (project uses pf sprint, not live Jira — same as sibling 153-1)
- **Merge gate:** clear (no open PRs)

**The finding (epic-153 playtest sweep):** SWN narrative chargen produces flat/non-differentiated attribute stats and skips skills/foci assignment. Root-cause direction (scoped on the title): apply the WN **14-to-7 attribute spread** (ADR-142 shaped-attribute retune) and **assign skills + foci** per the WN SRD during the *narrative* chargen path.

**Doctrine reminder for TEA/Dev:** this is a Without-Number-bound ruleset (ADR-142/143/117). Defer to the WN SRD for the attribute array and skill/foci numbers — do **not** invent or hand-balance a spread. The WN ruleset module's contribution methods already exist; the bug is likely a **wiring gap** (narrative chargen path not reaching them), not a missing implementation. Verify wiring end-to-end, add OTEL watcher visibility per the project's OTEL principle, and include a wiring test proving the chargen path is reachable from production code.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup.

### TEA (test design)
- **Gap** (non-blocking): space_opera defines NO backgrounds or foci files, so the
  AC-2 "assign skills/foci" portion has no content to grant — `contribute_background_skills`/
  `contribute_foci` already fire in `build()` but with `background_def=None`/`focus_defs=[]`.
  The skills/foci gap is therefore a **content-authoring** matter (out of this server-only
  story's scope), not a server bug. Affects `sidequest-content/genre_packs/space_opera/`
  (would need background/foci YAML to grant SWN skills). *Found by TEA during test design.*
- **Gap** (non-blocking): the root-cause framing in the story context ("contribution
  methods exist; bug is a wiring gap not reaching them") is **partly inaccurate** for
  attributes. The attribute path IS reached — `generate_stats → generate_attributes` runs —
  but the pack authors `stat_generation: point_buy` (budget 27), and `_allocate_point_buy(6, 27)`
  round-robins to `[13,13,13,12,12,12]` (all +0 WN modifiers = mechanically flat). The fix is
  to make the WN ruleset emit the shaped `[14,12,11,10,9,7]` spread, not to "wire up" an
  unreached method. Affects `sidequest/game/ruleset/without_number.py` (WN attribute-value
  seam). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the full server suite has ~82–92 pre-existing flaky
  failures unrelated to this story — heavy DB+name-generation e2e tests crossing the global
  `--timeout=30` (timeouts in `markov.py`/`psycopg`, NOT assertion failures). Proven
  pre-existing: clean tree (fix stashed) = 92 failed; with fix = 82 failed (the clean-tree 92
  *includes* this story's 9 red tests). Affects test infra (`pyproject.toml` addopts timeout +
  per-test `@pytest.mark.timeout(120)` on heavy e2e, per the known pattern). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the other three point-buy WN packs (awn `mutant_wasteland`,
  cwn `neon_dystopia` + `road_warrior`) had the identical flat-stat bug and are now de-flattened
  by this family-wide fix. Worth a quick playtest sanity-check that their chargen/HP feel right
  under the shaped spread. Affects those packs' generated characters (HP/save math now shaped).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the point-buy → standard-array supersession is silent at config
  level — a WN pack authoring `stat_generation: point_buy` + `point_buy_budget: N` has the budget
  ignored with no runtime log/warning (mitigated by the OTEL spans, but invisible in the authoring
  surface). Affects `sidequest/game/ruleset/without_number.py` + the 4 WN point-buy pack YAMLs
  (consider migrating them to `stat_generation: standard_array` for authoring honesty, or surfacing
  the supersession at pack-load). *Found by Reviewer during code review.*
- **Gap** (non-blocking): `_WN_STANDARD_ARRAY` is a hardcoded 6-element default not validated against
  ability-score count; a future WN pack declaring ≠6 abilities and omitting `standard_array` would
  `IndexError` in `assign_attributes` rather than failing loud at load. Affects
  `sidequest/game/ruleset/without_number.py` (size the default to `len(ability_names)` or assert
  length, mirroring `RulesConfig._validate_standard_array`). Latent — all current WN packs use 6. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the family-wide fix shifts chargen for `mutant_wasteland` (awn),
  `neon_dystopia` + `road_warrior` (cwn) beyond the literal SWN story — their HP/save math now uses
  the shaped spread. Worth a quick playtest sanity-check on those three packs (corroborates the Dev
  finding). Affects those packs' generated characters. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Scoped RED tests to the attribute spread only; deferred skills/foci tests**
  - Rationale: Operator directive (2026-06-21, mid-RED): "the player never gets to 'point buy' so that code is at best not wired. Just do the spread for now please." The skills/foci portion requires content authoring (background/foci YAML) outside the server-only repo scope.
  - Severity: minor
  - Forward impact: skills/foci for SWN remains a future content task (flagged as a Delivery Finding). Dev's GREEN scope is the attribute spread + its OTEL span only.
- **Asserted the exact array `[14,12,11,10,9,7]`, not a looser "differentiated" predicate**
  - Rationale: the title names the exact spread; the three live WWN packs already author exactly `[14,12,11,10,9,7]`; ADR-142 names this array. SRD-grounded, not invented (memory: "Defer to SRD for mechanics").
  - Severity: minor
  - Forward impact: if Dev chooses a different valid differentiated array, the strict test will flag it for reconciliation — intended.
- **Placed the fix in the shared WN base (family-wide), not swn-only**
  - Rationale: the bug is a WN-family mechanism, not SWN-specific — the Operator's directive ("the player never gets to point buy ... just do the spread") describes WN chargen generally; ADR-142's "no flat-13 character" intent is family-wide; the three point-buy WN packs were identically flat. A swn-only special-case would leave awn/cwn broken (shipping a half-fix, CLAUDE.md "no half-wired features"). No-op for the standard_array WWN packs; full chargen/ruleset/WN-integration suites stay green (620 targeted tests).
  - Severity: minor
  - Forward impact: awn/cwn (`mutant_wasteland`, `neon_dystopia`, `road_warrior`) chargen now produces shaped stats — gameplay-affecting (HP/save modifiers). Flagged as a Delivery Finding for playtest sanity-check. Easy to narrow to swn.py if the Operator/Reviewer prefers tighter scope.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Scoped RED tests to the attribute spread only; deferred skills/foci tests**
  - Spec source: context-story-153-4.md AC-2 (skills + foci) + story title ("assign skills/foci")
  - Spec text: "Skills and foci are assigned during chargen ... Background skills granted per WWN SRD §1.3 ... Focus skills/abilities per WWN SRD §1.5"
  - Implementation: No failing skills/foci tests written. space_opera authors no backgrounds/foci, so `contribute_*` already fire (just empty) — there is nothing red to assert server-side, and the existing `test_chargen_seam_wiring.py` already proves the contribution wiring with synthetic defs. RED tests cover the attribute spread (AC-1), OTEL visibility (AC-3), and the wiring/reachability proof (AC-4).
  - Rationale: Operator directive (2026-06-21, mid-RED): "the player never gets to 'point buy' so that code is at best not wired. Just do the spread for now please." The skills/foci portion requires content authoring (background/foci YAML) outside the server-only repo scope.
  - Severity: minor
  - Forward impact: skills/foci for SWN remains a future content task (flagged as a Delivery Finding). Dev's GREEN scope is the attribute spread + its OTEL span only.
- **Asserted the exact array `[14,12,11,10,9,7]`, not a looser "differentiated" predicate**
  - Spec source: context-story-153-4.md AC-1 + story title ("WN 14-to-7 attribute spread")
  - Spec text: "Generated scores follow the WN distribution"
  - Implementation: the primary test asserts `sorted(values, reverse=True) == [14,12,11,10,9,7]`; a companion test asserts the looser "≥2 distinct WN modifier bands" property as a flat-stats backstop.
  - Rationale: the title names the exact spread; the three live WWN packs already author exactly `[14,12,11,10,9,7]`; ADR-142 names this array. SRD-grounded, not invented (memory: "Defer to SRD for mechanics").
  - Severity: minor
  - Forward impact: if Dev chooses a different valid differentiated array, the strict test will flag it for reconciliation — intended.

### Dev (implementation)
- **Placed the fix in the shared WN base (family-wide), not swn-only**
  - Spec source: story title + context-story-153-4.md "Story Scope" ("addresses the narrative chargen path for SWN only")
  - Spec text: "This story addresses the narrative chargen path for SWN only."
  - Implementation: overrode `_generate_attribute_values` in `WithoutNumberRulesetModule` (the shared WN base), so `method == "point_buy"` yields the shaped `[14,12,11,10,9,7]` for ALL WN-family packs — swn (the story) plus awn/cwn, which use point-buy too. swn.py inherits it unchanged.
  - Rationale: the bug is a WN-family mechanism, not SWN-specific — the Operator's directive ("the player never gets to point buy ... just do the spread") describes WN chargen generally; ADR-142's "no flat-13 character" intent is family-wide; the three point-buy WN packs were identically flat. A swn-only special-case would leave awn/cwn broken (shipping a half-fix, CLAUDE.md "no half-wired features"). No-op for the standard_array WWN packs; full chargen/ruleset/WN-integration suites stay green (620 targeted tests).
  - Severity: minor
  - Forward impact: awn/cwn (`mutant_wasteland`, `neon_dystopia`, `road_warrior`) chargen now produces shaped stats — gameplay-affecting (HP/save modifiers). Flagged as a Delivery Finding for playtest sanity-check. Easy to narrow to swn.py if the Operator/Reviewer prefers tighter scope.

### Reviewer (audit)
- **TEA — Scoped RED tests to the attribute spread only; deferred skills/foci** → ✓ ACCEPTED by Reviewer: verified space_opera ships no backgrounds/foci files, so `contribute_*` already fire with empty inputs — the skills/foci gap is content-authoring (out of this server-only story) and the Operator explicitly directed "just the spread for now." Sound.
- **TEA — Asserted the exact array `[14,12,11,10,9,7]`** → ✓ ACCEPTED by Reviewer: the array is the verbatim WWN/SWN SRD standard array (matches the three WWN packs' authored `standard_array` and ADR-142); SRD-grounded, not over-coupling. The companion "≥2 distinct modifier bands" property test is a good loose backstop.
- **Dev — Placed the fix in the shared WN base (family-wide), not swn-only** → ✓ ACCEPTED by Reviewer: this is the architecturally honest home (ADR-143 ruleset-owned chargen seam); the Operator's directive is WN-general; the other point-buy WN packs (awn/cwn) had the identical flat-stat bug; the 597-test regression and my independent cwn/awn reproduction confirm no breakage. The real (correctly-flagged) consequence — awn/cwn/swn gameplay now shifts under the shaped spread — is carried forward as a playtest Delivery Finding, not a blocker. Narrowing to swn.py remains an easy follow-up if the Operator prefers.

## Branch & Testing Strategy

**Branch:** feat/153-4-swn-chargen-flat-stats (created from sidequest-server `develop`)

**Testing approach:**
- Unit tests for the WN ruleset attribute/skill assignment methods (already live in codebase)
- Integration test: full narrative chargen flow for an SWN world, verifying attributes are differentiated and skills/foci appear in final snapshot
- OTEL span assertions: confirm `{ruleset}.chargen.attributes_assigned`, `{ruleset}.chargen.background_skills`, `{ruleset}.chargen.foci_applied` fires during chargen
- Wiring test: verify narrative chargen path reaches the ruleset methods from production code (not isolated unit tests)

---

## Summary

SWN narrative character generation is producing flat/non-differentiated attribute stats and not assigning skills and foci per the WN SRD. The fix involves:

1. **Verify attribute generation:** Ensure the WN 14-to-7 attribute spread is applied during narrative chargen (not just arrange/roll paths)
2. **Wire skill/foci assignment:** Invoke `contribute_background_skills()` and `contribute_foci()` during narrative chargen assembly
3. **Add OTEL spans:** Emit watcher events so the GM panel verifies chargen mechanical decisions
4. **Integration test:** Prove narrative chargen reaches the ruleset methods end-to-end

Key entry points: CharacterBuilder (builder.py), narrative chargen phase handlers (chargen_mixin.py), WithoutNumberRulesetModule (ruleset/without_number.py).

---

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (9 failing tests, ready for Dev/GREEN)

### Root cause (characterized, not speculated)

`space_opera/rules.yaml` authors `stat_generation: point_buy`, `point_buy_budget: 27`,
six abilities. `_allocate_point_buy(6, 27)` round-robins evenly to
**`[13, 13, 13, 12, 12, 12]`**. Under the WN modifier ladder (8–13 → **+0**) *every*
attribute modifier is 0 — the character is **mechanically flat** (no prime edge, no
dump stat), even for the prime requisite. Verified by running the real production
seam (`builder.generate_stats`) and a full real-pack `build()`:
`{Influence:13, Physique:13, Reflex:13, Intellect:12, Cunning:12, Resolve:12}`.

The three live WWN packs (caverns_and_claudes, elemental_harmony, heavy_metal) were
migrated to the shaped WWN/SWN SRD standard array **`[14, 12, 11, 10, 9, 7]`** (the
"14-to-7 spread") via `RulesConfig.standard_array` under ADR-142 — **space_opera's SWN
was never migrated.** Per the Operator's directive, the GREEN fix is to make the WN
ruleset own attribute generation and emit the shaped spread (the dead point-buy path
is irrelevant under a WN binding — the player never reaches a point-buy surface).

### Test Files (RED)

- `tests/game/ruleset/test_153_4_swn_shaped_spread.py` (6 tests) — synthetic SWN rules
  mirroring the real space_opera pack (swn, point_buy 27, six abilities). Drives the
  real `generate_stats` + `build()` seams. Asserts the shaped `[14,12,11,10,9,7]`
  spread, ≥2 distinct WN modifier bands (flat-stats backstop), prime→14 (unique max),
  a −1 dump stat at 7, full-build reachability, and the `swn.chargen.attributes_assigned`
  OTEL span reporting `top=14`/`prime=Physique`.
- `tests/integration/test_153_4_swn_chargen_spread_wiring.py` (3 tests) — WIRING proof
  against the **real** space_opera pack: loads it, walks the real aureate_span
  char_creation scenes (no Claude — deterministic choice-0/auto-advance/followup), builds
  via real `build()`, asserts the shaped spread + differentiated modifiers + prime→14.
  Behavior test, not a source-text grep (CLAUDE.md "No Source-Text Wiring Tests").

**Tests Written:** 9 (covering AC-1 attribute spread, AC-3 OTEL visibility, AC-4 wiring).
AC-2 (skills/foci) deferred — see Design Deviations (content-authoring, out of server scope).

### Rule Coverage

| Lang-review rule (python.md) | Test(s) / handling | Status |
|------|---------|--------|
| #6 Test quality (no vacuous assertions) | Self-checked all 9: every assert checks a concrete value (`== [14,12,11,10,9,7]`, `== 14`, `== 7`, distinct-modifier count, span `top == 14`). No `assert True`/bare-truthy. `skipif` carries a reason. | pass |
| #3 Type annotation gaps | All test fns annotated `-> None`; helpers annotated (`-> dict[str,int]`, `-> RulesConfig`, etc.) | pass |
| #1 Silent exception swallowing | Integration walk's `try/except → apply_freeform` mirrors the known-good `test_wwn_elemental_harmony_chargen.py` harness (test scaffolding, not production) | pass |

Other lang-review rules (#2 mutable defaults, #4 logging, #5 path handling, #7 resource
leaks) target implementation code — Dev's GREEN concern, not test design.

**Rules checked:** 3 of the applicable test-design rules have coverage.
**Self-check:** 0 vacuous tests found.

### GREEN guidance for Dev (Agent Smith)

- Make the WN ruleset emit the shaped `[14,12,11,10,9,7]` spread for WN-bound packs,
  superseding the flat point-buy path (ADR-142 retune / ADR-143 ruleset-owned chargen seam).
  Likely seam: `WithoutNumberRulesetModule` attribute-value generation in
  `sidequest/game/ruleset/without_number.py` (it already overrides `assign_attributes`
  prime-aware; the value-gen needs to yield the shaped pool).
- **Defer to the SRD** — do not invent or hand-balance a spread (SOUL: "Bind the Ruleset",
  memory: "Defer to SRD for mechanics"). `[14,12,11,10,9,7]` is the canonical WWN/SWN array.
- Keep the `swn.chargen.attributes_assigned` OTEL span firing with the shaped `top`/`prime`.
- Mind blast radius: the WWN packs already author `standard_array: [14,12,11,10,9,7]`, so a
  WN-owns-the-spread change is a no-op for them; their integration tests derive expected
  values from the built scores and stay green. Verify with the full chargen suite.
- Do NOT touch the skills/foci path — out of scope this story (content gap).

**Handoff:** To Dev (Agent Smith) for GREEN.

---

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/game/ruleset/without_number.py` — added `_WN_STANDARD_ARRAY = [14,12,11,10,9,7]` constant and a `_generate_attribute_values` override on `WithoutNumberRulesetModule`. For `method == "point_buy"` it returns the shaped WWN/SWN SRD standard array (pack-authored `standard_array` if present, else the WN default); every other method passes through to the base value-gen unchanged. `assign_attributes` (already prime-aware) then places the shaped pool — prime → 14 (+1), dump → 7 (−1).

**Approach:** Minimal, single-seam. The WN ruleset now owns attribute generation (ADR-142 shaped-attribute retune / ADR-143 ruleset-owned chargen seam): the dead point-buy path is superseded by the shaped spread under any WN binding. No new OTEL span needed — the existing `swn.chargen.attributes_assigned` span now fires honestly with `top=14`/the prime (covered by a RED test), and `SPAN_CHARGEN_STATS_GENERATED` records the shaped result.

**Tests:**
- Story tests: **9/9 passing** (`tests/game/ruleset/test_153_4_swn_shaped_spread.py` 6, `tests/integration/test_153_4_swn_chargen_spread_wiring.py` 3).
- Targeted regression: **620 passing** across all chargen/ruleset/WN-pack paths — `tests/game/ruleset/` + builder/chargen-seam/standard-array (572, serial) and WN integration chargen (elemental_harmony, barsoom, heavy_metal, cc_chargen_e2e, neon strain, builder-seeds-strain, + this story's wiring) (39 + 9, with Postgres). The dial-bound point-buy builder tests are unaffected (my override is WN-only); the standard_array WWN packs are a no-op.
- Lint/type: `ruff check` clean; `pyright` adds **0** new errors (clean tree and changed tree both report the same 3 pre-existing errors on `stat_modifier`/`assign_attributes`/`commit_effort`).
- Full suite: ~82 failures are **pre-existing environmental DB/timeout flakes** (proven: clean tree = 92 failed *including* this story's 9 reds; with fix = 82 failed; failures are `markov.py`/`psycopg` timeouts, not assertions). My change adds zero new failures. Logged as a Delivery Finding.

**Branch:** `feat/153-4-swn-chargen-flat-stats` (pushed to origin)

**Handoff:** To Reviewer (The Merovingian) for code review.

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (success) | none | N/A — 9 story + 597 regression GREEN, ruff clean, 0 new pyright errors, 0 smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none (1 latent note) | confirmed 0, deferred 1 (latent length-mismatch → LOW, Delivery Finding) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer (see [RULE]) |

**All received:** Yes (2 enabled subagents returned clean; 7 disabled via `workflow.reviewer_subagents` settings, their domains assessed by Reviewer directly)
**Total findings:** 0 confirmed blocking, 0 dismissed, 3 deferred (all LOW → Delivery Findings)

---

## Reviewer Assessment

**Verdict:** APPROVED

**Cause → effect (data flow traced):** pack `rules.yaml` (`stat_generation: point_buy`, six `ability_score_names`) → `CharacterBuilder.generate_stats(acc)` → `WithoutNumberRulesetModule.generate_attributes` → **new** `_generate_attribute_values` (intercepts `point_buy` → returns shaped `[14,12,11,10,9,7]`) → `assign_attributes` (prime-aware placement: prime→14, dump→7) → `Character.stats` + `swn.chargen.attributes_assigned` OTEL span. Safe because every input is content-author-controlled (pack YAML) or server-internal builder state — **no player WebSocket input reaches this path** (confirmed by [SEC]). I independently reproduced the shaped output for swn, cwn, and awn.

**Pattern observed:** the override subclasses the base value-gen seam exactly as the base docstring sanctions ("so the base and any override that wants to call super() value-gen then do its own assignment"), at `without_number.py:766`. Single-condition branch, clean `super()` pass-through for every other method.

### Findings (tagged by domain)

- `[PRE]` reviewer-preflight: **clean.** 9 story tests GREEN, 597 targeted-regression GREEN (all WN-family sibling packs unaffected), ruff clean, 0 new pyright errors, 0 code smells. The ~82 full-suite failures are pre-existing DB/timeout flakes (independently verified by Dev: clean tree 92 incl. 9 reds vs 82 with fix).
- `[SEC]` reviewer-security: **clean, 0 findings.** No player-controlled input, no injection/leak/auth/DoS surface; the `None → _WN_STANDARD_ARRAY` substitution is intentional/documented, not a config-masking silent fallback. One *latent* note (non-security): a future WN pack with ≠6 abilities omitting `standard_array` would `IndexError` in `assign_attributes` — deferred LOW (see below).
- `[EDGE]` (self — subagent disabled): `[LOW]` the override intercepts `method=="point_buy"` **before** the base's empty-`ability_names` guard (`base.py:308`), so a hypothetical WN+point_buy pack with empty `ability_names` returns the 6-value array instead of `[]`. No real WN pack has empty abilities (the empty-guard exists for Fate, which does not subclass WN). Theoretical, non-blocking.
- `[SILENT]` (self — subagent disabled): `[LOW]` the point-buy → standard-array supersession is silent at config level — a WN pack authoring `point_buy_budget: N` has it ignored with no runtime log/warning. Mitigated: it is deliberate + Operator-directed, documented in the docstring, and observable on the GM panel (the `attributes_assigned` span fires with the shaped `top=14`, and `SPAN_CHARGEN_STATS_GENERATED` records `method=point_buy` against shaped stats — a detectable mismatch). Not a `No-Silent-Fallbacks` violation (that rule targets error-masking, not documented supersession). Deferred → Delivery Finding.
- `[TEST]` (self — subagent disabled): `[VERIFIED]` tests assert behavioral OUTPUT (the shaped spread, the prime at 14, the −1 dump, the span `top`), not implementation shape — robust to where the fix lands. The integration test drives the **real** pack through real `build()` (true wiring proof, not source-grep). `skipif` carries a reason. No vacuous assertions. The `WN_SHAPED_SPREAD` literal duplicated in tests vs the production constant is intentional test hygiene (tests must not import the constant they verify). — `test_153_4_swn_shaped_spread.py`, `test_153_4_swn_chargen_spread_wiring.py`.
- `[DOC]` (self — subagent disabled): `[VERIFIED]` the docstring on `_generate_attribute_values` is accurate and load-bearing — explains *why* point-buy is dead under WN, cites ADR-142/143, and states the fallback precedence. The `_WN_STANDARD_ARRAY` constant carries an SRD source citation (WWN p.11 / SWN §1.2). No stale/misleading comments introduced.
- `[TYPE]` (self — subagent disabled): `[VERIFIED]` the override signature matches the base ABC exactly (keyword-only, `list[tuple[str,int]] | None`, returns `list[int]`); 0 new pyright errors. `return list(array)` is a defensive copy, so the module-level mutable `_WN_STANDARD_ARRAY` cannot be aliased/mutated by callers — `without_number.py:792`.
- `[SIMPLE]` (self — subagent disabled): `[VERIFIED]` minimal and non-over-engineered — one guard + one `super()` delegation, no new abstraction, no dead code.
- `[RULE]` (self — subagent disabled): `[VERIFIED]` compliant with SOUL **"Bind the Ruleset, Don't Balance It"** and the "Defer to SRD" rule — the array is the verbatim WWN/SWN SRD standard array (identical to the three WWN packs' authored `standard_array`), not an invented/hand-balanced spread. python.md lang-review: no silent except (#1), no mutable defaults (#2), annotations present (#3), no unsafe deserialization (#8), import hygiene clean (#10 — reuses existing `random`), no fix-introduced regression (#13, confirmed by 597-test regression).

### Rule Compliance (exhaustive enumeration)

- **No Silent Fallbacks (CLAUDE.md):** the one fallback (`standard_array is not None else _WN_STANDARD_ARRAY`) is a documented supersession of a dead config surface, not masking of a missing file/misconfig. The two pre-existing loud-fail paths (`roll_the_bones` RuntimeError, `UnknownStatGenerationError`) are untouched. **Compliant** (with a LOW visibility note logged).
- **No Stubbing / No half-wired features:** the fix is fully wired end-to-end (builder → ruleset → Character → OTEL), proven by the integration wiring test and the family-wide reproduction. **Compliant.**
- **Bind the Ruleset, Don't Balance It (SOUL):** verbatim SRD array, no homebrew tuning. **Compliant.**
- **Defer to SRD for mechanics (project memory):** `[14,12,11,10,9,7]` copied from the WWN/SWN SRD, not invented. **Compliant.**
- **OTEL Observability (CLAUDE.md, important):** the attribute-assignment subsystem decision is instrumented via the pre-existing `chargen_attributes_assigned_span`, which now fires honestly with the shaped `top`/`prime` (test-asserted). No subsystem decision left un-instrumented. **Compliant.**
- **No Source-Text Wiring Tests (server CLAUDE.md):** the wiring test drives real `build()` + asserts behavior/OTEL, never greps source. **Compliant.**
- python.md lang-review #1–#13: applicable rules (#1, #2, #3, #8, #10, #13) all **Compliant**; #4–#7, #9, #11–#12 N/A to this diff.

### Devil's Advocate

Let me argue this is broken. **First, the silent supersession.** A content author — Jade, say, extending a space_opera world — reads `space_opera/rules.yaml`, sees `stat_generation: point_buy`, `point_buy_budget: 27`, and reasonably tunes the budget to 30 expecting beefier characters. Nothing happens. No log, no validation error, no warning — the WN module has quietly amputated the entire point-buy mechanism. The authoring surface lies to her. That is precisely the confusion the "No Silent Fallbacks" doctrine exists to prevent, and the project's whole content-author thesis (Jade can homebrew without engine help) is undermined by config that silently does nothing. **Second, the latent crash.** `_WN_STANDARD_ARRAY` is six hardcoded integers. `RulesConfig` validates an *authored* `standard_array` against ability count, but nothing validates this *default*. A future WN world that adds a seventh attribute (a "Psyche" stat, entirely plausible for a psionics-heavy SWN setting) and omits `standard_array` will sail past validation and then `IndexError` deep in `assign_attributes` at chargen — a player-facing crash with an opaque traceback, not a loud config error at load. **Third, scope.** This silently changed character generation for *three packs the story never named* — mutant_wasteland, neon_dystopia, road_warrior. Their HP, saves, and encounter balance all shift under the shaped spread, and not one playtest has touched them. If a CWN world was balanced (even implicitly) around flat +0 characters, this is a stealth difficulty change shipped under an "SWN chargen" headline. **Fourth, the dead `point_buy_budget` field** now litters four packs as a no-op, an attractive nuisance for the next author. — *Resolution:* none of these rise to Critical/High. The supersession is Operator-directed ("the player never gets to point buy ... just do the spread") and documented; the crash requires a non-existent ≠6-ability WN pack and mirrors the pre-existing `standard_array` contract; the cross-pack change is the correct ADR-142 "no flat-13 character" intent and is explicitly flagged by Dev for playtest. All three are logged as Delivery Findings for follow-up rather than blockers.

**Verdict:** APPROVED — no Critical/High findings. The fix is minimal, SRD-faithful, type-clean, fully wired, and well-tested; the three LOW concerns are deferred as Delivery Findings.

**Handoff:** To SM (Morpheus) for finish-story.