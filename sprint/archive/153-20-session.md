---
story_id: "153-20"
jira_key: "153-20"
epic: "153"
workflow: "tdd"
---
# Story 153-20: [TOOTHLESS-DETECTOR-DRIFT] teach the seating toothless-detector about the WN SRD unarmed floor (153-1 follow-up) so it stops false-flagging weaponless WN opponents as invulnerable

## Story Details
- **ID:** 153-20
- **Jira Key:** 153-20
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T12:24:21Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T11:38:20Z | 2026-06-22T11:39:49Z | 1m 29s |
| red | 2026-06-22T11:39:49Z | 2026-06-22T11:59:39Z | 19m 50s |
| green | 2026-06-22T11:59:39Z | 2026-06-22T12:17:07Z | 17m 28s |
| review | 2026-06-22T12:17:07Z | 2026-06-22T12:24:21Z | 7m 14s |
| finish | 2026-06-22T12:24:21Z | - | - |

## Sm Assessment

Setup complete and routing to TEA for the RED phase. This is a well-scoped 2-point TDD
bug in `sidequest-server` (targets `develop`). Full story context already existed at
`sprint/context/context-story-153-20.md` — read it; it is comprehensive (problem statement,
repro/evidence, fix direction, 4 ACs, scope notes). No re-authoring needed.

**What this story is:** the seating-detector sibling of 153-1. 153-1 wired runtime reprisal
damage; this fixes the at-seat toothless-detector (`_opponent_reprisal_damage_resolvable` in
`sidequest/server/dispatch/encounter_lifecycle.py`) which still false-flags a weaponless WN
opponent as invulnerable because it doesn't know about the WN SRD unarmed floor.

**Coordination notes for downstream agents:**
- **Bind the ruleset, don't balance it (ADR-143, SOUL).** AC-1 and the scope notes are
  explicit: the WN unarmed value MUST come directly from the ruleset binding — do NOT author
  or hand-tune an unarmed number. This is the load-bearing constraint; pull the floor from the
  WN SRD binding, not a magic literal.
- **WN-gated, not universal (AC-2).** The new fourth check fires only for `swn`/`wwn`/`cwn`/`awn`
  rulesets. Non-WN (Fate, native) keeps the existing conservative false-toothless bias unchanged.
- **OTEL is an AC, not optional (AC-3/AC-4).** `encounter_opponent_toothless_span` must carry
  `ruleset` and (when the floor applies) `unarmed_floor`. AC-4 requires an integration test
  through the REAL `_opponent_reprisal_damage_resolvable` path (not a mocked wrapper) asserting
  both the `True` return and the populated span field. Extend
  `tests/server/test_opponent_toothless_detector.py`.

**Heads-up (non-blocking):** two open non-draft server PRs exist (#1029 region-lateral-mover,
#1024 dungeon-seam) — Keith's own standalone branches, not pf-managed sprint-story branches and
not tied to any in-progress story, so the merge gate did not block this new work. Flagging for
awareness only.

## TEA Assessment

**Phase:** finish (test design)
**Tests Required:** Yes
**Status:** RED — 29 failing tests, ready for Dev (Agent Smith)

**Test File:** `sidequest-server/tests/server/test_opponent_toothless_detector.py`
(rewritten — the existing BUG-1 file; old tests folded into the new AC matrix and
re-pointed at the new signature). Lint-clean (`ruff check` passes). Committed:
`4fe7fe70 test: failing tests for 153-20`.

**Tests Written:** 29 (across the 4 ACs)
- `test_detector_weaponless_wn_opponent_resolves_unarmed_floor[swn/wwn/cwn/awn]` — **AC-1**:
  the detector returns `True` for a weaponless opponent under each WN sibling (SRD floor).
- `test_detector_weaponless_non_wn_opponent_is_toothless[dial/fate]` — **AC-2**: returns
  `False` under non-WN rulesets (WN-gated, conservative bias preserved).
- `test_detector_authored_opponent_damage_resolves_for_any_ruleset[6]`,
  `…_strike_override_…[6]`, `…_inventory_weapon_…[6]` — slots 1-3 still give teeth under
  every ruleset; the new WN floor is a last resort and must not change existing behavior.
- `test_wn_weaponless_seat_span_carries_ruleset_and_unarmed_floor` — **AC-3/AC-4**: drives the
  REAL `_seed_combat_hp_depletion_to_npcs` → `_opponent_reprisal_damage_resolvable`; span fires
  with `ruleset=="wwn"` and `unarmed_floor == get_ruleset_module("wwn").SRD_UNARMED_DICE` (value
  pulled from the binding, **not** a magic literal — the anti-invention assertion).
- `test_non_wn_weaponless_seat_span_is_toothless_without_floor` — **AC-2/AC-3**: dial pack →
  span carries `ruleset` but NO `unarmed_floor`.
- `test_{opponent_damage_authored,strike_override,armed_opponent}_emits_no_span_under_wn` —
  regression guard: an authored source (slots 1-3) closes the content gap → no span.

**Contract pinned for Dev (the RED defines these):**
1. `_opponent_reprisal_damage_resolvable(cdef, opponent_core, ruleset)` — new `ruleset:
   RulesetModule` param. Fourth check: `isinstance(ruleset, WithoutNumberRulesetModule)` and no
   slot-1..3 source → `True` (the SRD floor). Non-WN with no slot-1..3 → `False`.
2. `_seed_combat_hp_depletion_to_npcs(..., ruleset)` — new **required** `ruleset` param (NOT
   `pack` — see deviation). Resolve the floor + stamp span fields from it.
3. Span `encounter.opponent_toothless` fires whenever the opponent has no authored slot-1..3
   source (the content gap), now carrying `ruleset` (always) and `unarmed_floor =
   ruleset.SRD_UNARMED_DICE` (WN only; omit/empty for non-WN — OTEL drops None attrs).
   Production caller (`encounter_lifecycle.py:1948`) resolves `get_ruleset_module(pack.rules.ruleset)`.

**Where to implement:** `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py`
— detector at lines ~231-267, seeder at ~270-451 (span emission block ~433-451), production
caller passes `ruleset` at ~1948. WN base + floor: `sidequest/game/ruleset/without_number.py`
(`SRD_UNARMED_DICE = "1d2"`, lines ~131-139).

### Rule Coverage

| Rule (CLAUDE.md / SOUL / python lang-review) | Test(s) | Status |
|----|----|----|
| Bind the ruleset, don't invent (ADR-143 / AC-1) — floor from the binding | `…span_carries_ruleset_and_unarmed_floor` asserts `== SRD_UNARMED_DICE` | failing |
| No Silent Fallbacks — WN gate is precise, doesn't leak to non-WN | `…non_wn_opponent_is_toothless[dial/fate]`, `…span_is_toothless_without_floor` | failing |
| OTEL Observability — discriminating span fields | AC-3/AC-4 span tests assert `ruleset` + `unarmed_floor` | failing |
| Wiring (real call path, not mocked) — AC-4 | span tests drive the REAL production seeder→detector→span | failing |
| No Source-Text Wiring Tests | all wiring proven via OTEL span assertions (never `read_text()`) | n/a (compliant) |
| Test quality (lang-review #6) — meaningful, non-vacuous | `is True`/`is False` + specific span-attr equality; no `assert True`/bare truthy | n/a (compliant) |

**Rules checked:** 6 of 6 applicable. **Self-check:** 0 vacuous tests (all assert specific values).

**Handoff:** To Dev (Agent Smith) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 29/29 new tests GREEN. Full blast radius verified: 476 dispatch + WN-combat
integration tests pass; full server suite 13923 passed / 345 skipped with 4 pre-existing
failures (all confirmed NOT mine — see below).
**Branch:** `fix/153-20-toothless-detector-wn-unarmed-floor` (pushed). Commit `(impl)`
on top of the RED commit `4fe7fe70`.

**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` — the fix:
  - Split `_has_authored_reprisal_source(cdef, opponent_core)` (slots 1-3, the content-gap
    check) out of the detector.
  - `_opponent_reprisal_damage_resolvable(cdef, opponent_core, ruleset)` now returns
    `_has_authored_reprisal_source(...) or isinstance(ruleset, WithoutNumberRulesetModule)`
    — a weaponless WN opponent resolves the SRD unarmed floor (AC-1); non-WN keeps the
    conservative `False` (AC-2). Value comes from the binding, never invented (ADR-143).
  - `_seed_combat_hp_depletion_to_npcs(..., ruleset: RulesetModule)` — new required param.
    Span block now fires on `not _has_authored_reprisal_source(...)` (content gap) and
    carries `ruleset` (always), `unarmed_floor` = `ruleset.SRD_UNARMED_DICE` (WN only),
    and `reprisal_resolvable` = the WN-aware detector verdict (AC-3/AC-4).
  - Production caller (`instantiate_encounter_from_trigger`, ~line 1995) resolves
    `get_ruleset_module(pack.rules.ruleset)` (fail-loud via `_raise_missing_ruleset`) and
    passes `ruleset=`.
- `sidequest-server/tests/server/test_opponent_roster_resolution.py` — 3 sibling call
  sites pass `ruleset=get_ruleset_module("wwn")` (genre caverns_and_claudes).
- `sidequest-server/tests/server/dispatch/test_72_8_presence_last_seen_stamp.py` — 1 sibling
  call site passes `ruleset=get_ruleset_module("swn")` (genre space_opera).

**Quality gates:** `ruff check` clean on all changed files; `pyright` at baseline (14
pre-existing errors, **0 new** — verified by stash-compare; the 2 I briefly introduced,
a `_tracer` overload false-positive and a duplicate `npc.core` optional-access, were both
fixed by building span attrs as `dict[str, Any]` and reusing one `opponent_core` local).

**4 full-suite failures — all pre-existing / flaky, NONE caused by this change** (verified):
- `test_beneath_sunden_room_binding_107_2::test_distinct_rooms_bind_distinct_creatures` —
  fails at baseline with my changes stashed (pre-existing).
- `test_watcher_events::test_publish_event_shape`,
  `test_59_30_witnesses::…_count_is_nine…`,
  `test_102_5_wn_tool_narrator_wiring::…production_dispatch` — pass in isolation / at
  baseline; xdist order-dependent flakiness (the known `seed_slug`/xdist pattern).
  None reference `encounter_lifecycle` / the seeder / the detector / ruleset.

**Handoff:** To Reviewer (The Merovingian) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (51 tests GREEN, ruff clean, pyright 14 = baseline, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none (4 rule classes, 11 instances, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — domain assessed by lead (see [RULE]) |

**All received:** Yes (2 enabled subagents returned clean; 7 disabled via `workflow.reviewer_subagents`, their domains assessed by the lead reviewer below)
**Total findings:** 0 confirmed, 0 dismissed, 3 LOW observations (non-blocking, noted below)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `pack.rules.ruleset` (content YAML, server-side) → `get_ruleset_module(slug)`
(fail-loud, `UnknownRulesetError` on miss) → `ruleset` module → `_seed_combat_hp_depletion_to_npcs`
→ `_opponent_reprisal_damage_resolvable` / span attrs. Safe because every value on this path is
server/content-derived (ruleset slug, the `SRD_UNARMED_DICE` class constant, `cdef.confrontation_type`)
— **no player free-text** reaches the new OTEL attributes or the `rationale` string ([SEC] confirms).

**Pattern observed:** behavior-preserving refactor + additive extension at
`sidequest/server/dispatch/encounter_lifecycle.py:232,267,477`. The old detector body was *exactly*
the slots-1..3 check; Dev extracted it verbatim into `_has_authored_reprisal_source` and built the
new `_opponent_reprisal_damage_resolvable = authored OR isinstance(ruleset, WithoutNumberRulesetModule)`
on top. The span gate moved from the old detector to `_has_authored_reprisal_source` — **provably the
same firing set** (`not authored`), so span EMISSION is unchanged; only the detector's *return* (now
True for WN weaponless) and the additive span fields change.

**Error handling:** caller fail-loud at `encounter_lifecycle.py:2007` (`_raise_missing_ruleset` when
`pack`/`pack.rules` absent) + `get_ruleset_module` raises on unknown slug. No try/except swallowing,
no silent default to `dial`. `ruleset.SRD_UNARMED_DICE` is accessed only inside the
`isinstance(..., WithoutNumberRulesetModule)` guard → no AttributeError path.

### Observations (≥5)

- **[VERIFIED]** Detector logic correct — `_opponent_reprisal_damage_resolvable` returns
  `authored OR isinstance(ruleset, WN)`: WN-weaponless→True (AC-1), non-WN-weaponless→False (AC-2),
  authored→True. Evidence: `encounter_lifecycle.py:289-291`. Complies with ADR-143 (value from the
  binding's `SRD_UNARMED_DICE`, never invented).
- **[VERIFIED]** Span emission is regression-free — gate `not _has_authored_reprisal_source(...)`
  (`:472`) is identical to the old `not _opponent_reprisal_damage_resolvable(...)` (slots 1-3), so
  the span fires on the same set; confirmed by the 3 passing "authored → no span" regression tests
  and the still-green heavy_metal/roster minted-stub tests.
- **[SEC]** (security subagent, clean) No injection / No-Silent-Fallbacks surface — all 5 new span
  attrs + `rationale` are server/content-derived; `unarmed_floor=None` is guarded out of `span_attrs`
  by `if unarmed_floor:` (`:486`) so OTEL never receives a None primitive. Confirmed at `:483-487, 494-503`.
- **[SILENT]** (subagent disabled — lead-assessed) No silent fallbacks: ruleset resolution is
  fail-loud (`_raise_missing_ruleset` + `UnknownRulesetError`); no bare `except`, no swallowed errors
  in the diff. `getattr(ruleset, "slug", "")` is a cosmetic span-attr default, not a control-flow fallback.
- **[EDGE]** (subagent disabled — lead-assessed) Boundary paths covered: None-pack → fail-loud;
  unknown slug → raise; a degenerate `ruleset=None` reaching the seeder (cannot in production) would
  `isinstance→False` and degrade to non-WN (no crash). `getattr(cdef,"confrontation_type","")` handles
  the `SimpleNamespace` cdef in test_72_8.
- **[TEST]** (subagent disabled — lead-assessed) 29 tests, all assert specific values
  (`is True`/`is False`, `ruleset=="wwn"`, `unarmed_floor == SRD_UNARMED_DICE` — anti-magic-literal).
  No vacuous assertions. LOW: `not attrs.get("unarmed_floor")` (non-WN test) is marginally weaker than
  `"unarmed_floor" not in attrs` but matches the "absent" intent. Non-blocking.
- **[DOC]** (subagent disabled — lead-assessed) Docstrings/comments updated accurately: the split
  helpers are correctly described; the span-block + caller comments match the code; the pyright-workaround
  comment (`dict[str, Any]`) is truthful. No stale comments.
- **[TYPE]** (subagent disabled — lead-assessed) `_seed_combat_hp_depletion_to_npcs` new param annotated
  `ruleset: RulesetModule`; the detector's `ruleset` is unannotated — consistent with its sibling
  untyped params (`cdef`, `opponent_core`), private-helper exempt (lang-review #3). `span_attrs: dict[str, Any]`
  is the right type to keep the `**spread` off the span helper's `_tracer` overload (pyright at baseline).
- **[SIMPLE]** (subagent disabled — lead-assessed) LOW: inside the `not authored` branch, `resolvable`
  (the detector call) reduces to `isinstance(ruleset, WN)`, the same predicate as `unarmed_floor is not None`
  — a minor redundancy. Justified and documented in the Dev deviation: it is the production consumer that
  keeps the AC-named `_opponent_reprisal_damage_resolvable` wired (else the function is test-only / dead).
  Accepted, not over-engineering — AC-1/AC-4 explicitly name the predicate.
- **[RULE]** (subagent disabled — lead-assessed) Rule-by-rule below: all 13 lang-review checks + SOUL
  doctrine compliant.

### Rule Compliance (python lang-review + SOUL/CLAUDE.md)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Silent exception swallowing | ✓ | No try/except added; ruleset resolution fail-loud |
| 2 | Mutable default args | ✓ | `span_attrs: dict[str,Any] = {...}` is a local, not a default arg |
| 3 | Type annotations at boundaries | ✓ | seeder param annotated; detector is a private helper (exempt), consistent with its other untyped params |
| 6 | Test quality | ✓ | specific-value asserts, no vacuous; 1 LOW noted |
| 7 | Resource leaks | ✓ | span via `with` context manager |
| 10 | Import hygiene | ✓ | real top-level `WithoutNumberRulesetModule` import (used at runtime); non-circular (verified import OK); no star imports |
| 11 | Input validation at boundaries | ✓ | new span attrs server-derived; ruleset slug validated by `get_ruleset_module` |
| 13 | Fix-introduced regressions | ✓ | pyright at baseline 14 (0 new); full suite green except 4 confirmed-pre-existing/flaky |
| SOUL | Bind the Ruleset, Don't Balance It (ADR-143) | ✓ | unarmed floor taken from `SRD_UNARMED_DICE`, never hand-tuned; WN-gated |
| SOUL | No Silent Fallbacks | ✓ | `_raise_missing_ruleset` + `UnknownRulesetError`, no `dial` default |
| CLAUDE | OTEL on every subsystem decision | ✓ | discriminating `ruleset`/`unarmed_floor`/`reprisal_resolvable` span fields |
| CLAUDE | Verify Wiring / no dead code | ✓ | detector wired in production via `reprisal_resolvable`; caller→seeder enforced by required param + heavy_metal instantiate test |

(Checks 4/5/8/9/12 — logging, paths, deserialization, async, deps — N/A to this diff.)

### Devil's Advocate

Let me argue this code is broken. **Claim 1: the WN floor wrongly resurrects an opponent that
content authors deliberately left toothless.** Rebuttal: there is no "deliberately toothless" WN
opponent — under a WN binding the SRD *guarantees* an unarmed 1d2, and 153-1 already made the
*runtime* reprisal deal it. The at-seat detector was simply lying about it. Aligning the detector
with the runtime is the fix, not a behavior change. **Claim 2: the span now misleads the GM — it's
named `opponent_toothless` but fires for a non-toothless WN opponent.** Rebuttal: the span carries
`reprisal_resolvable=True` and `unarmed_floor="1d2"` precisely so the panel reads "floor resolved, not
toothless" — AC-3's whole point. The name is unchanged for consumer compatibility; the fields
disambiguate. **Claim 3: a confused author sees the span fire and thinks combat is broken.** Rebuttal:
the `rationale` string explicitly says "The wwn SRD unarmed floor (1d2) gives it a real reprisal —
author opponent_damage to make the intent explicit." That is the correct nudge (Diamonds-and-Coal:
author intent), not a false alarm. **Claim 4: a malicious/confused caller passes a non-WN pack and the
player becomes invulnerable.** Rebuttal: non-WN weaponless still returns False (toothless) AND still
fires the span — the conservative bias is preserved, and the *runtime* (not this detector) governs
actual damage. **Claim 5: `ruleset.SRD_UNARMED_DICE` could KeyError/AttributeError.** Rebuttal: it is
a class attribute on the WN base, accessed only inside the `isinstance` guard; every WN sibling
inherits it. **Claim 6: OTEL chokes on a None attr.** Rebuttal: `if unarmed_floor:` guards it out of
the dict. Nothing here corrupts state, leaks data, or breaks the runtime combat loop — the change is
confined to a diagnostic predicate + additive span fields, provably behavior-preserving on emission.

**Handoff:** To SM for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): making `ruleset` a required param on `_seed_combat_hp_depletion_to_npcs`
  ripples to 4 existing direct call sites that must each gain `ruleset=get_ruleset_module(...)`.
  Affects `tests/server/test_opponent_roster_resolution.py` (3 calls: lines ~359, ~391, ~418 —
  WN genre, e.g. `get_ruleset_module("wwn")`) and `tests/server/dispatch/test_72_8_presence_last_seen_stamp.py`
  (1 call, line ~184 — space_opera → `get_ruleset_module("swn")`). The full suite will go red on
  these until Dev updates them in GREEN; the failing calls themselves point Dev to each site.
- **Gap** (non-blocking): the production caller wiring (`encounter_lifecycle.py:1948`
  `instantiate_encounter_from_trigger` → resolve `get_ruleset_module(pack.rules.ruleset)` → pass
  `ruleset=`) is NOT covered by a content-independent test here — the repo's WN fixture packs
  author `opponent_damage` on their combats (no weaponless WN combat to seat end-to-end). It is
  enforced by the required-param signature + pyright + the existing (content-gated) instantiate
  WN tests (`tests/integration/test_reprisal_wn_lethality_e2e.py`, `test_wwn_*_dispatch.py`).
  Affects nothing to change — flagging so Dev confirms the caller passes `ruleset` and the
  Reviewer doesn't expect a fixture-pack end-to-end test that the fixtures can't express.
- **Improvement** (non-blocking): the detector's boolean return must remain load-bearing in
  production after the fix (CLAUDE.md "no dead code"). Since the span now fires on the
  separate "no authored slot-1..3 source" condition (not on the detector's return), Dev should
  keep the detector's `True/False` consumed — either gate downstream seating logic on it or
  ride it on the span as a field. Affects `encounter_lifecycle.py` seeder. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (non-blocking): TEA's blocking finding (4 sibling call sites need `ruleset=`) is
  done — `test_opponent_roster_resolution.py` (×3, `get_ruleset_module("wwn")`) and
  `test_72_8_presence_last_seen_stamp.py` (×1, `get_ruleset_module("swn")`) updated; all pass.
- **Resolved** (non-blocking): TEA's "keep the detector return load-bearing" improvement is
  honored — the WN-aware verdict rides the span as `reprisal_resolvable` (the seeder calls
  `_opponent_reprisal_damage_resolvable` with the real ruleset, so the WN branch executes in
  production, not only in tests). The span gate uses the new `_has_authored_reprisal_source`.
- No new upstream findings during implementation.

### Reviewer (code review)
- No upstream findings during code review. The change is self-contained to the seating-diagnostic
  detector + additive OTEL span fields; both enabled subagents (preflight, security) returned clean,
  and the lead-assessed domains (edge/silent/test/doc/type/simple/rule) surfaced only 3 non-blocking
  LOW observations, none requiring rework.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

5 deviations

- **Seeder takes `ruleset: RulesetModule`, not `pack: GenrePack`**
  - Rationale: the hp seeder needs ONLY the ruleset module (to read `SRD_UNARMED_DICE` "directly
  - Severity: minor
  - Forward impact: 4 call sites updated in GREEN (see Delivery Findings); Reviewer may prefer
- **AC-2 "Fate" branch covered at the detector level, not via the seating integration path**
  - Rationale: a Fate-bound pack never reaches `_seed_combat_hp_depletion_to_npcs` — the seating
  - Severity: minor
  - Forward impact: none.
- **AC-4 "real call path" satisfied via the production seeder, not `instantiate_encounter_from_trigger`**
  - Rationale: the repo's WN fixture packs author `opponent_damage` on their combats, so no
  - Severity: minor
  - Forward impact: caller→seeder wiring enforced by required-param + pyright + existing
- **Span fires on the content gap (no authored slot-1..3 source), decoupled from the detector return**
  - Rationale: only way to satisfy "detector returns True for WN weaponless" AND "span fires with
  - Severity: minor
  - Forward impact: none — the span name (`encounter.opponent_toothless`) is unchanged; consumers
- **Added `reprisal_resolvable` span field (not asserted by any test)**
  - Rationale: the seeder's span gate uses `_has_authored_reprisal_source`, so without this the
  - Severity: minor
  - Forward impact: none — additive OTEL attribute; the GM panel gains a "floor-rescued vs toothless"

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Seeder takes `ruleset: RulesetModule`, not `pack: GenrePack`**
  - Spec source: context-story-153-20.md, Fix Direction + AC-4
  - Spec text: "Teach `_opponent_reprisal_damage_resolvable` (or the calling seating path) … if
    the pack's ruleset is a WN family binding …"
  - Implementation: the new param on `_seed_combat_hp_depletion_to_npcs` is the resolved
    `ruleset` module (caller does `get_ruleset_module(pack.rules.ruleset)`), not the whole pack —
    even though the sibling `_seed_fate_opponents` takes `pack`.
  - Rationale: the hp seeder needs ONLY the ruleset module (to read `SRD_UNARMED_DICE` "directly
    from the ruleset binding" per AC-1); the Fate seeder needs the whole pack (FateSheet data).
    Passing the module is the honest minimal interface and minimizes ripple — 4 existing direct
    call sites (one of which has no pack in scope, only a `SimpleNamespace` cdef) get a one-line
    `ruleset=` instead of having to construct/load a pack. Keeps the tests content-independent.
  - Severity: minor
  - Forward impact: 4 call sites updated in GREEN (see Delivery Findings); Reviewer may prefer
    `pack` for surface symmetry — the trade-off is documented here as a conscious choice.
- **AC-2 "Fate" branch covered at the detector level, not via the seating integration path**
  - Spec source: context-story-153-20.md, AC-2
  - Spec text: "For a non-WN ruleset (Fate, native/dial) with the same weaponless opponent, the
    detector still returns `False`."
  - Implementation: AC-2 is tested for both `dial` AND `fate` at the DETECTOR level
    (`test_detector_weaponless_non_wn_opponent_is_toothless[dial/fate]`); the seating-path
    integration test uses `dial` only.
  - Rationale: a Fate-bound pack never reaches `_seed_combat_hp_depletion_to_npcs` — the seating
    block is gated `if cdef.category == "combat" and not is_fate` (Fate combat is a Fate conflict,
    seeded by `_seed_fate_opponents`). Driving the hp seeder with a Fate ruleset would test an
    impossible production state. The detector-level Fate case still pins the predicate honestly.
  - Severity: minor
  - Forward impact: none.
- **AC-4 "real call path" satisfied via the production seeder, not `instantiate_encounter_from_trigger`**
  - Spec source: context-story-153-20.md, AC-4
  - Spec text: "drives a weaponless WN opponent … through the real
    `_opponent_reprisal_damage_resolvable` call path — not a mocked wrapper."
  - Implementation: the integration tests drive the REAL `_seed_combat_hp_depletion_to_npcs`
    (production function, called at `encounter_lifecycle.py:1948`), which calls the real detector
    and real span — no mock. They do not additionally go through `instantiate_encounter_from_trigger`.
  - Rationale: the repo's WN fixture packs author `opponent_damage` on their combats, so no
    weaponless WN combat exists to seat end-to-end through the full trigger path (see Delivery
    Findings). The seeder-direct test IS the real, unmocked detector call path AC-4 asks for.
  - Severity: minor
  - Forward impact: caller→seeder wiring enforced by required-param + pyright + existing
    instantiate WN tests (flagged in Delivery Findings).

### Dev (implementation)
- **Span fires on the content gap (no authored slot-1..3 source), decoupled from the detector return**
  - Spec source: context-story-153-20.md, AC-3 + the existing BUG-1 span gate
  - Spec text: "The span already fires in the existing path — the AC is that it carries the new
    discriminating fields when the WN unarmed case applies."
  - Implementation: the original gate was `if not _opponent_reprisal_damage_resolvable(...)`. Since
    the detector now returns `True` for a weaponless WN opponent (AC-1), gating the span on it would
    suppress the WN diagnostic — contradicting AC-3/AC-4 (span must fire WITH `unarmed_floor`). So the
    span now gates on the new `_has_authored_reprisal_source(...)` (slots 1-3) and carries
    `reprisal_resolvable` (the WN-aware verdict) so the GM panel still sees the engine's True/False.
  - Rationale: only way to satisfy "detector returns True for WN weaponless" AND "span fires with
    unarmed_floor for WN weaponless" simultaneously. Keeps both the detector return and the span
    load-bearing.
  - Severity: minor
  - Forward impact: none — the span name (`encounter.opponent_toothless`) is unchanged; consumers
    that filter by name are unaffected, and the new fields are additive.
- **Added `reprisal_resolvable` span field (not asserted by any test)**
  - Spec source: TEA Delivery Finding (Improvement) — "keep the detector's True/False consumed"
  - Spec text: "ride it on the span as a field"
  - Implementation: the seeder stamps `reprisal_resolvable=<detector verdict>` on the toothless span.
    No test asserts this field.
  - Rationale: the seeder's span gate uses `_has_authored_reprisal_source`, so without this the
    WN-inclusive `_opponent_reprisal_damage_resolvable` call would be dead in production (CLAUDE.md
    "Verify Wiring, Not Just Existence"). This field is the production consumer of the WN-aware verdict.
  - Severity: minor
  - Forward impact: none — additive OTEL attribute; the GM panel gains a "floor-rescued vs toothless"
    discriminator.

### Reviewer (audit)
- **TEA: Seeder takes `ruleset: RulesetModule`, not `pack`** → ✓ ACCEPTED by Reviewer: honest
  minimal interface; the hp seeder needs only the module to read `SRD_UNARMED_DICE`. The
  `_seed_fate_opponents(pack=)` asymmetry is justified (Fate needs FateSheet pack data; this seeder
  does not). Minimizes ripple to the 4 direct call sites. Sound.
- **TEA: AC-2 "Fate" covered at the detector level, not the seating path** → ✓ ACCEPTED by Reviewer:
  Fate combat is gated out of `_seed_combat_hp_depletion_to_npcs` (`not is_fate`); a seating-path
  Fate test would assert an impossible production state. Detector-level `[fate]` parametrization
  pins the predicate correctly.
- **TEA: AC-4 "real call path" via the production seeder, not `instantiate_encounter_from_trigger`** →
  ✓ ACCEPTED by Reviewer: the seeder is real production code (called at `:2008`); the test is unmocked.
  The fixture WN packs all author `opponent_damage`, so no weaponless WN combat can seat end-to-end —
  the caller→seeder link is instead enforced by the required param + the passing heavy_metal instantiate
  test. Reasonable given the fixture constraint.
- **Dev: Span fires on the content gap, decoupled from the detector return** → ✓ ACCEPTED by Reviewer:
  the only way to satisfy AC-1 (detector True for WN weaponless) AND AC-3/AC-4 (span fires WITH
  `unarmed_floor`) simultaneously. Verified behavior-preserving — `not _has_authored_reprisal_source`
  is the identical firing set as the old gate.
- **Dev: Added `reprisal_resolvable` span field (untested)** → ✓ ACCEPTED by Reviewer: it is the
  production consumer that keeps the AC-named `_opponent_reprisal_damage_resolvable` wired (otherwise
  test-only/dead per CLAUDE.md "Verify Wiring"). Additive OTEL attribute, no risk. An untested additive
  span field is acceptable; the field's *presence* is incidental, its discriminator value is covered by
  the `unarmed_floor` assertions.
- No UNDOCUMENTED deviations found — TEA and Dev logged every divergence I identified.