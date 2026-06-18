---
story_id: "126-11"
jira_key: null
epic: "126"
workflow: "tdd"
---
# Story 126-11: [NARRATOR] Drama-aware length-limit: scale verbosity cap to narrative weight

## Story Details
- **ID:** 126-11
- **Jira Key:** None
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-18T10:56:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-18T10:02:31Z | 2026-06-18T10:04:40Z | 2m 9s |
| red | 2026-06-18T10:04:40Z | 2026-06-18T10:25:41Z | 21m 1s |
| green | 2026-06-18T10:25:41Z | 2026-06-18T10:39:00Z | 13m 19s |
| review | 2026-06-18T10:39:00Z | 2026-06-18T10:56:33Z | 17m 33s |
| finish | 2026-06-18T10:56:33Z | - | - |

## Sm Assessment

**Story selected and set up by Themis (SM) on 2026-06-18.** Chosen as the cleanest of the
remaining p2 narrator stories from the 2026-06-18 deep-dive (126-10 and 126-8 are in-flight
in other sessions; 126-12 carries an unresolved design-only/`tdd` workflow mismatch).

**Why this story is ready:**
- Dependency 126-9 (thinking-ON latency regression) is DONE, so the clean baseline this work
  needs already exists — no re-measure or blocker resolution required before RED.
- Scope is well-bounded: a single subsystem (the narrator verbosity section), a known anchor
  (`orchestrator.py:1588` `_build_verbosity_section`, plus the static "BREVITY IS KING" in
  `output_style.md`), and a clear lever (wire a drama/weight signal into the cap).
- Single repo (server), 3 points, phased TDD.

**Direction for the pipeline:**
- This serves the single most load-bearing project goal — the narrator must be good enough to
  fool a career GM (Keith). A flat cap that strangles a climactic reveal directly undercuts
  that; SOUL "Cost Scales with Drama" is the governing principle.
- **OTEL is mandatory** (project Observability Principle): emit a span on the chosen verbosity
  tier so the GM panel can verify the weight→cap mapping fired and the narrator isn't just
  winging the length. A drama-aware cap with no OTEL is unverifiable.
- Quiet turns must stay cheap (Cost-Scales-with-Drama cuts both ways — don't widen the floor).

**Jira:** explicitly skipped — story 126-11 carries no Jira key.

**Routing:** phased TDD → handoff to TEA (Argus Panoptes) for the RED phase.

## Delivery Findings

No upstream findings yet.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): `output_style.md` carries a SECOND, static length doctrine that
  will contradict a drama-widened cap. It references the literal `<length-limit>` token
  ("The <length-limit> is a HARD CAP …") and then hard-codes "BREVITY IS KING / Simple
  actions: 2-3 sentences / Combat: 2-4 sentences". When the verbosity section widens to
  ~12 sentences for a climax, the narrator gets two conflicting length instructions in
  the same prompt. Affects `sidequest/agents/narrator_prompts/output_style.md` (must
  defer to the `<length-limit>` cap rather than assert its own fixed sentence counts) —
  the story already names this file, so reconciling it is in-scope for GREEN. *Found by
  TEA during test design.*
- **Improvement** (non-blocking): the drama signal is ALREADY half-wired. `PacingHint`
  (computed every turn from `TensionTracker`) carries both `drama_weight` (0.0–1.0) AND
  `target_sentences` (1–6), but `target_sentences` only drives the SOFT `[PACING]`
  "Target approximately N sentence(s)" directive (`orchestrator.py:2902`), never the
  HARD `<length-limit>` cap. Dev should ride the existing `pacing_hint.drama_weight` into
  the cap (wire-up, not new plumbing) and consider whether the soft `target_sentences`
  directive and the new hard cap should be reconciled to avoid a third length voice.
  Affects `sidequest/agents/orchestrator.py` (`_build_verbosity_section` + its call site
  ~2567). *Found by TEA during test design.*
- **Question** (non-blocking): the OTEL tier span's emit site is left to Dev. The tests
  drive BOTH `_build_turn_context` and `build_narrator_prompt` so either site works, but
  the natural home (alongside `narrator_settings_span` / `pacing_hint_span`) is
  `_build_turn_context` in `session_helpers.py`, with a new
  `sidequest/telemetry/spans/verbosity_tier.py` helper mirroring `narrator_settings.py`.
  *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (TEA Gap #1, blocking): reconciled `output_style.md`'s static brevity
  doctrine to defer to the drama-scaled `<length-limit>` cap — dropped the hardcoded "2-3
  sentences / 2-4 sentences" counts that would contradict a widened climax cap; kept
  "BREVITY IS KING — within the cap" so brevity still governs *within* the room the cap
  grants. Affects `sidequest/agents/narrator_prompts/output_style.md`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): there are now TWO length voices — the SOFT pacing
  `[PACING]` "Target approximately N sentence(s)" directive (`PacingHint.target_sentences`,
  1–6) and the new HARD drama-scaled `<length-limit>` cap. Both ride the same
  `drama_weight`, so they agree in direction, but the soft target (max 6) is now narrower
  than the hard climax cap (12). Not contradictory (soft is a "target", hard is a
  "ceiling"), but a future story could unify them so the narrator hears one length story.
  Affects `sidequest/game/tension_tracker.py` (`narrator_directive`) + `orchestrator.py`.
  *Found by Dev during implementation.*
- **Verified** (non-blocking): the new `narrator.verbosity_tier` span is additive (one
  emit per `build_narrator_prompt`). Regression-scanned `tests/agents/` (1991 passed) and
  the prompt/span candidates — no exact-span-count assertion broke. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_resolve_verbosity_cap` silently coerces an unknown
  verbosity mode to `standard` (no log, no raise, no span flag), and the span then emits
  the raw (invalid) mode string while the cap is drawn from `standard` — a span/cap
  divergence in the very lie-detector the story relies on. Production-unreachable today
  (`narrator_verbosity` is a validated 3-member `StrEnum`), so non-blocking; the real risk
  is a future enum member added without a `_VERBOSITY_CAP_TABLE` entry silently degrading.
  Recommend failing loud (raise on unknown mode) or recording a `mode_fallback` span attr.
  Affects `sidequest/agents/orchestrator.py:1595-1596`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two length voices now coexist — the SOFT pacing
  `[PACING]` "Target approximately N sentence(s)" directive (max ~5–6) and the new HARD
  drama cap (up to 14 at climax). At a climax the soft target may suppress the narrator
  from using the widened cap, partially dampening the feature's intent. A follow-up should
  reconcile them so the narrator hears one length story (also flagged by Dev). Affects
  `sidequest/game/tension_tracker.py` + `sidequest/agents/orchestrator.py`.
  *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Drama scaling pinned by direction + anchor, not literal tier values**
  - Rationale: AC-2 marks those numbers "e.g." — pinning them would make any reasonable Dev tuning (11 vs 12, multiplicative vs additive) a false failure. Direction + anchor gives full RED teeth without brittle magic-number coupling.
  - Severity: minor
  - Forward impact: Reviewer should treat the exact tier values as a tuning choice, not an AC violation.
- **"Base + scale all modes" composition (verbose/concise participate); chosen by Mortal**
  - Rationale: the AC scope was ambiguous; Mortal explicitly chose "Base + scale all modes" (2026-06-18) over "standard-only" and "standard+verbose, concise fixed". This honors SOUL "Cost Scales with Drama" universally and keeps the Story 82-2 player-control + vocabulary features intact.
  - Severity: minor
  - Forward impact: Dev must scale all three modes (not just standard) and must NOT let drama alter the vocabulary section.
- **Concrete tier bands + per-mode cap table chosen within AC-2's "e.g." latitude**
  - Rationale: AC-2/AC-3 explicitly call for named "tiers", so discrete bands (not a continuous curve) match the spec and give the span a clean `tier` name. The literals are AC-2's own examples; standard matches them exactly, other modes mirror the same quiet/climax ratio.
  - Severity: minor
  - Forward impact: band thresholds + cap values are a single-table tuning point; changing them is data-only, no logic change.
- **Updated the 82-2 concise marker (cross-test change)**
  - Rationale: concise@quiet now renders "Maximum 3 sentences" (the cap is drama-scaled), so the fixed "Maximum 4 sentences" literal is stale. The style line is a stronger, number-free discriminator that still proves the concise choice flows through; the test's intent is preserved.
  - Severity: minor
  - Forward impact: none — the 82-2 suite stays green and still tests slider→prompt wiring.

## Design Deviations

No deviations yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Drama scaling pinned by direction + anchor, not literal tier values**
  - Spec source: context-story-126-11.md, AC-2
  - Spec text: "Climactic/confrontation turns allow longer narration (e.g., 12 sentences / 1200 chars); quiet/exploration turns apply tighter caps (e.g., 6 sentences / 600 chars); normal turns use baseline (8 / 800)."
  - Implementation: tests assert *direction* (high > base > quiet, monotonic), the *per-mode base anchor* (exact develop literals when drama underivable), and *mode ordering*, but NOT the exact "12/1200, 6/600" literals.
  - Rationale: AC-2 marks those numbers "e.g." — pinning them would make any reasonable Dev tuning (11 vs 12, multiplicative vs additive) a false failure. Direction + anchor gives full RED teeth without brittle magic-number coupling.
  - Severity: minor
  - Forward impact: Reviewer should treat the exact tier values as a tuning choice, not an AC violation.
- **"Base + scale all modes" composition (verbose/concise participate); chosen by Mortal**
  - Spec source: context-story-126-11.md, AC-1/AC-2 (silent on verbosity-mode composition)
  - Spec text: the ACs only ever name "the flat *standard* cap (8/800)"; they do not say how drama composes with an explicit `concise`/`verbose` choice.
  - Implementation: drama scales EVERY verbosity mode around its own base (concise 4/400, standard 8/800, verbose 10/1000); mode ordering concise<standard<verbose preserved at each drama level; vocabulary axis untouched. Pinned by `test_verbose_mode_scales_with_drama`, `test_concise_mode_scales_with_drama`, `test_mode_base_ordering_preserved_under_drama`, `test_drama_does_not_change_vocabulary_section`.
  - Rationale: the AC scope was ambiguous; Mortal explicitly chose "Base + scale all modes" (2026-06-18) over "standard-only" and "standard+verbose, concise fixed". This honors SOUL "Cost Scales with Drama" universally and keeps the Story 82-2 player-control + vocabulary features intact.
  - Severity: minor
  - Forward impact: Dev must scale all three modes (not just standard) and must NOT let drama alter the vocabulary section.

### Dev (implementation)
- **Concrete tier bands + per-mode cap table chosen within AC-2's "e.g." latitude**
  - Spec source: context-story-126-11.md, AC-2
  - Spec text: "Define weight tiers … map weight tiers to cap variants (e.g., 'climactic' → 12/1200; 'quiet' → 6/600; 'normal' → 8/800)."
  - Implementation: 3 discrete tiers (`quiet`/`normal`/`climax`) selected by drama bands (<0.34, 0.34–0.67, ≥0.67); per-mode cap table concise (3/300, 4/400, 6/600), standard (6/600, 8/800, 12/1200), verbose (8/800, 10/1000, 14/1400) in `_VERBOSITY_CAP_TABLE`.
  - Rationale: AC-2/AC-3 explicitly call for named "tiers", so discrete bands (not a continuous curve) match the spec and give the span a clean `tier` name. The literals are AC-2's own examples; standard matches them exactly, other modes mirror the same quiet/climax ratio.
  - Severity: minor
  - Forward impact: band thresholds + cap values are a single-table tuning point; changing them is data-only, no logic change.
- **Updated the 82-2 concise marker (cross-test change)**
  - Spec source: tests/server/test_verbosity_vocabulary_turn_context_wiring.py (ADR-049, Story 82-2)
  - Spec text: `_CONCISE_MARKER = "Maximum 4 sentences"` — asserted the concise section reaches the prompt.
  - Implementation: changed the marker to the drama-invariant concise style line `"Action and consequence only"`.
  - Rationale: concise@quiet now renders "Maximum 3 sentences" (the cap is drama-scaled), so the fixed "Maximum 4 sentences" literal is stale. The style line is a stronger, number-free discriminator that still proves the concise choice flows through; the test's intent is preserved.
  - Severity: minor
  - Forward impact: none — the 82-2 suite stays green and still tests slider→prompt wiring.

### Reviewer (audit)
- **TEA: direction-not-literals pinning** → ✓ ACCEPTED: AC-2 marks the numbers "e.g."; pinning direction + per-mode base anchor + ordering is the correct, robust contract. The implementation's literals (standard 6/8/12) match AC-2's examples anyway.
- **TEA: "Base + scale all modes" composition (Mortal's choice)** → ✓ ACCEPTED: matches the user's explicit 2026-06-18 decision; verified the cap table preserves concise<standard<verbose at every drama level and leaves vocabulary untouched.
- **Dev: concrete tier bands + per-mode cap table** → ✓ ACCEPTED: single-table tuning point, KeyError-proof (every mode carries quiet/normal/climax), standard tier matches AC-2 examples exactly.
- **Dev: updated 82-2 concise marker** → ✓ ACCEPTED: feature-driven and unavoidable — concise@quiet now renders "Maximum 3 sentences"; the new `"Action and consequence only"` discriminator is number-free and stronger, and the 82-2 suite stays green (verified). The test's slider→prompt intent is preserved.
- **UNDOCUMENTED — unknown-verbosity silent fallback (inherited):** `_resolve_verbosity_cap` defaults an unrecognized mode to `standard` with no log/raise (orchestrator.py:1595-1596). Not logged by TEA/Dev as a deviation. This mirrors the pre-126-11 `_build_verbosity_section` "Default: standard (also handles unknown values)" behavior, so it is *inherited*, not introduced — but it is a No-Silent-Fallbacks gap. Severity: M (production-unreachable; see [SEC] finding). Flagged as a non-blocking delivery finding, not a reject.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New narrator behavior (drama-aware length cap) — pure RED-phase coverage.

**Test Files:**
- `sidequest-server/tests/server/test_drama_aware_length_limit.py` — 14 tests covering
  all 5 ACs + the verbose/concise/language coverage Mortal directed.

**Tests Written:** 14 tests covering 5 ACs (+ Mortal's verbosity-mode & vocabulary directive)
**Status:** RED — `10 failed, 4 passed` (`uv run pytest -n0 tests/server/test_drama_aware_length_limit.py`)

The 4 PASS are intentional regression anchors (assert the unchanged develop baseline so
Dev can't silently drift it); the 10 FAIL are the unimplemented drama-scaling behaviors.

| AC | Behavior | Test(s) | Status |
|----|----------|---------|--------|
| AC1/AC2 | cap scales with drama (high>base>quiet, monotonic) | `test_high_drama_widens_cap_beyond_baseline`, `test_low_drama_tightens_cap_below_baseline`, `test_cap_scales_monotonically_with_drama` | failing |
| AC5 | underivable drama → exact baseline (no silent drift) | `test_underivable_weight_renders_baseline_cap` | passing (anchor) |
| AC3 | `narrator.verbosity_tier` OTEL span (tier/weight/cap_sentences/cap_chars) | `test_verbosity_tier_span_emitted_with_caps` | failing |
| AC3 | span caps MATCH rendered prompt (lie detector) | `test_tier_span_caps_match_rendered_prompt` | failing |
| AC4 | drama flows tracker→bridge→prompt cap | `test_end_to_end_high_drama_session_widens_prompt_cap`, `test_end_to_end_quiet_drama_session_tightens_prompt_cap` | failing |
| Mortal | verbose/concise scale around their base; ordering preserved | `test_verbose_mode_scales_with_drama`, `test_concise_mode_scales_with_drama` | failing; `test_mode_base_ordering_preserved_under_drama`, `test_*_base_unchanged_when_drama_underivable` | passing (anchors) |
| Mortal | language (vocabulary) untouched by drama | `test_drama_does_not_change_vocabulary_section` | failing (length sanity) |

### Rule Coverage

| Rule (lang-review/python.md) | Test(s) / treatment | Status |
|------|---------|--------|
| Test Quality (§"Test Quality") — no vacuous asserts, no skips, distinct paths | all 14 assert specific values (tuples/inequalities); dead placeholder removed in self-check | covered |
| No Silent Fallbacks (CLAUDE.md critical) | `test_underivable_weight_renders_baseline_cap` + per-mode base anchors assert the EXACT documented base, not a silent snap | covered |
| OTEL Observability (CLAUDE.md principle) | AC3 span tests + span↔prompt cross-check | covered |
| No Source-Text Wiring Tests (CLAUDE.md) | every assertion is behavioral (drive real builder, read rendered text/span) — zero source greps | covered |

**Rules checked:** the structural Python checks (bare except, mutable defaults, type
annotations, resource cleanup) apply to Dev's *production* code and are enforced by the
review-phase lang-review gate — they are not behaviorally testable in a RED suite without
forbidden source-grepping, so no per-check test is owed at this phase.
**Self-check:** 1 vacuous/dead helper found and removed (`_cap_at` placeholder in the
ordering test); 0 remaining vacuous assertions.

**Handoff:** To Dev (Hephaestus the Smith) for implementation. Wire
`pacing_hint.drama_weight` into `_build_verbosity_section`'s cap for all three modes,
emit the `narrator.verbosity_tier` span, and reconcile `output_style.md`'s static
brevity doctrine (Delivery Finding #1, blocking).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/orchestrator.py` — added `_VERBOSITY_CAP_TABLE`, `_drama_tier`,
  `_resolve_verbosity_cap`; `_build_verbosity_section(verbosity, cap_sentences, cap_chars)`
  now injects the drama-scaled cap; the prompt-build call site resolves the cap from
  `pacing_hint.drama_weight`, emits the `verbosity_tier` span, and renders with it.
- `sidequest/telemetry/spans/verbosity_tier.py` (new) — `narrator.verbosity_tier` span
  helper + SPAN_ROUTES route (component `narrator`), mirroring `narrator_settings.py`.
- `sidequest/telemetry/spans/__init__.py` — surface the new span via star-import.
- `sidequest/agents/narrator_prompts/output_style.md` — reconcile the static brevity
  doctrine to defer to the drama-scaled cap (TEA Gap #1, blocking — resolved).
- `tests/server/test_verbosity_vocabulary_turn_context_wiring.py` — update the 82-2
  concise marker to the drama-invariant style line (feature-driven test update).

**Tests:** 14/14 drama-aware GREEN; 5/5 ADR-049 (82-2) GREEN; `tests/agents/` 1991 passed,
0 failed (after the output_style brevity reconciliation); prompt/span regression
candidates 9 passed / 17 skipped. No span-count regressions from the additive span.

**Branch:** `feat/126-11-drama-aware-length-limit` (pushed to origin)

**All ACs met:** AC1/AC2 (cap scales with drama), AC3 (`narrator.verbosity_tier` span,
caps single-sourced with the prompt), AC4 (drama flows tracker→bridge→prompt), AC5
(underivable→exact baseline), plus Mortal's directive (verbose/concise scale around their
base; vocabulary/language untouched).

**Handoff:** To Reviewer (Hermes Psychopompos) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (19 tests pass, lint/format/pyright clean) | N/A |
| 2 | reviewer-edge-hunter | Yes | error (stalled 600s, no result) | n/a | domain assessed by Reviewer directly — see [EDGE] |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer ([DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 (1 Medium, 1 Low) | confirmed 1 (non-blocking), dismissed 0, 1 info-only |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — assessed by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Rule Compliance done by Reviewer ([RULE]) |

**All received:** Yes (preflight + security returned; edge-hunter errored and its domain was assessed directly; 6 disabled)
**Total findings:** 1 confirmed (Medium, non-blocking), 0 dismissed, 1 info-only (Low)

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A clean, well-scoped "wire up what exists" change — the already-computed
`pacing_hint.drama_weight` is routed into the narrator's hard `<length-limit>` cap, the
player's verbosity mode sets the base, drama scales it per a single data table, and an
OTEL span records the decision. All five ACs met plus Mortal's verbose/language directive.
19 story tests green, `tests/agents/` green (1991), lint/format/pyright clean. One
non-blocking Medium finding (an inherited silent fallback on an unreachable path) and one
non-blocking coherence note — neither rises to High/Critical.

**Data flow traced:** `TensionTracker.drama_weight()` (clamped 0–1) → `PacingHint.drama_weight`
(session_helpers `_build_turn_context`) → `TurnContext.pacing_hint` → `build_narrator_prompt`
reads `context.pacing_hint.drama_weight` (None-guarded) → `_resolve_verbosity_cap(mode, drama)`
→ `(tier, cap_sentences, cap_chars)` → single-sourced into BOTH the `verbosity_tier_span`
AND `_build_verbosity_section(...)` render. Safe: drama_weight is clamped upstream so the
cap path never sees out-of-range input; span and prompt caps are computed once and cannot
diverge on any reachable path.

**Observations:**
- [VERIFIED] StrEnum mode lookup is correct — `str(NarratorVerbosity.concise) == "concise"`
  (verified empirically); concise/verbose scale around their OWN base, not a silent
  fall-through to standard. evidence: orchestrator.py:1594 `mode = str(verbosity)` + the
  resolution table (`concise None=4/400, 1.0=6/600`).
- [VERIFIED] Nested-table lookup is KeyError-proof — every mode in `_VERBOSITY_CAP_TABLE`
  carries `quiet`/`normal`/`climax`; the None branch uses `["normal"]` (present in all).
  evidence: orchestrator.py:1561-1565 + runtime assertion.
- [EDGE] (self-assessed; subagent errored) Band edges 0.34/0.67 partition correctly;
  out-of-range (-0.5→quiet, 1.5→climax) and NaN→`normal` degrade gracefully and are
  unreachable in production (`TensionTracker.drama_weight()` returns `_clamp01(...)`,
  verified `with_values(5,-3)→1.0`). No crash path found. evidence: orchestrator.py:1576-1582.
- [SEC] Confirmed (Medium, non-blocking): unknown-verbosity silent fallback to `standard`
  at orchestrator.py:1595-1596 — matches the No-Silent-Fallbacks `<critical>` rule, so
  CONFIRMED not dismissed; downgraded to Medium because the input is a validated 3-member
  StrEnum (production-unreachable) and the silent-default is inherited from the pre-126-11
  `_build_verbosity_section`. Recommend fail-loud follow-up (delivery finding filed).
- [SEC] Info-only (Low): f-string injection of cap numbers is architecturally foreclosed
  — `cap_sentences`/`cap_chars` are ints from a constant table, never user content. No action.
- [TEST] (self-assessed; analyzer disabled) Tests assert specific tuples/inequalities, no
  vacuous `assert True`/truthy-only checks, no `@pytest.mark.skip`, the mode-ordering loop
  tests three DISTINCT modes (not one path), and the dead `_cap_at` placeholder was removed
  in TEA's self-check. Behavioral discipline honored (no source greps). VERIFIED good.
- [DOC] (self-assessed; analyzer disabled) Docstrings on the new span helper and resolver
  are accurate; the call-site comment correctly explains the span-then-register ordering;
  `output_style.md` prose is coherent and now defers to the cap. No stale/misleading docs.
- [TYPE] (self-assessed; type-design disabled) All new functions fully annotated
  (`_drama_tier(float)->str`, `_resolve_verbosity_cap(str, float|None)->tuple[str,int,int]`,
  `_build_verbosity_section(str,int,int)->str`). Minor: the tier is a bare `str` rather than
  a `Literal`/enum — a cosmetic type-tightening opportunity, Low, not worth blocking.
- [SIMPLE] (self-assessed; simplifier disabled) Data-driven table + band resolver is the
  minimal shape; no dead code, no over-engineering. The `with span(): pass` empty-block is
  the ESTABLISHED idiom in this codebase (`narrator_settings_span`/`pacing_hint_span` use
  it identically in session_helpers.py) — consistent, not a smell.
- [SILENT] (self-assessed; hunter disabled) No try/except in the diff; the only swallow-like
  path is the unknown-mode fallback, captured as the [SEC] finding above.
- [RULE] Rule Compliance enumeration below.

### Rule Compliance (.pennyfarthing/gates/lang-review/python.md — all 13 checks)
1. Silent exceptions — PASS (no try/except in diff; unknown-mode fallback tracked as [SEC], not exception-swallowing).
2. Mutable default args — PASS (`_VERBOSITY_CAP_TABLE` is a module constant, not a default arg; no mutable defaults).
3. Type annotations at boundaries — PASS (every new fn + the span CM fully annotated).
4. Logging coverage/correctness — PASS with note (no error logging added; the one error-ish path is the [SEC] unknown-mode fallback, which the finding recommends logging/raising).
5. Path handling — PASS (no path ops).
6. Test quality — PASS (assessed under [TEST]; specific assertions, no vacuous/skip).
7. Resource leaks — PASS (span uses `with`; no open/connect/lock leaks).
8. Unsafe deserialization — PASS (none).
9. Async pitfalls — PASS (sync span CM inside async fn is fine; no blocking I/O, no missing await).
10. Import hygiene — PASS (explicit `verbosity_tier_span` import; the `from .verbosity_tier import *` matches the file's per-module star-import convention with `# noqa`).
11. Input validation — PASS with note (the [SEC] unknown-mode boundary; validated enum upstream).
12. Dependency hygiene — PASS (no dep changes).
13. Fix-introduced regressions — PASS (the output_style brevity reconciliation re-scanned; no new issues).

### Devil's Advocate
Suppose this code is broken. The most dangerous claim is "drama now scales the cap" — does
it actually reach the player, or is it theater? I traced it: the cap genuinely flows into
the rendered `<length-limit>` and the span is single-sourced, so the mechanism is real, not
improvised — and the OTEL span lets the GM panel confirm it fired. But a confused *narrator*
is the real risk: at a climax the prompt now contains BOTH "HARD LIMIT max 12 sentences" and
the soft pacing "Target approximately 5 sentences." A stressed LLM may anchor on the smaller
number and never use the room the story fought for — so the feature could under-deliver in
exactly the climactic moments it targets. That is real, but it is a tuning/coherence gap
(filed non-blocking), not a correctness break; the cap IS widened and nothing regresses. A
malicious or buggy caller passing a bogus verbosity string gets silently downgraded to
standard with a misleading span — but that caller must first defeat the StrEnum validation
that guards every production path, so it is unreachable today; the genuine hazard is a future
maintainer adding a 4th verbosity mode and forgetting the table, which would silently behave
as standard. I filed that as a fail-loud recommendation. What about a quiet turn rendering a
3-sentence concise cap — too strangling? No: that is the explicit, user-chosen design
("quiet stays cheap"), pinned by tests and Mortal's decision. What about the empty
`with span(): pass`? It looks like a mistake but is the house idiom; the span fires on enter
and closes on exit, and the section is correctly registered after. Stressed filesystem,
huge inputs, race conditions: none apply — this is pure in-memory string assembly with no
I/O, no shared mutable state, no concurrency. The code survives the adversarial pass.

**Error handling:** No exceptions introduced; the one silent path (unknown mode) is the
confirmed non-blocking [SEC] finding with a fail-loud recommendation. Null/None drama is
explicitly handled (→ baseline). evidence: orchestrator.py:2620-2623.

**Pattern observed:** Data-driven cap table + band resolver + single-source span/render —
clean and refactor-stable. orchestrator.py:1561-1599.

**Handoff:** To SM (Themis the Just) for finish-story.