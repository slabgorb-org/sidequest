---
story_id: "73-1"
jira_key: ""
epic: "73"
workflow: "tdd"
---
# Story 73-1: Convert negotiation + scandal to opposed_check (+ per-confrontation ADR-093 balance pass)

## Story Details
- **ID:** 73-1
- **Epic:** 73 — Confrontation Engine Hardening
- **Jira Key:** (none — personal project)
- **Workflow:** tdd
- **Priority:** p2
- **Story Type:** bug
- **Points:** 5
- **Repos:** sidequest-content, sidequest-server
- **Branches:** 
  - `feat/73-1-negotiation-scandal-opposed-check` (sidequest-server)
  - `feat/73-1-negotiation-scandal-opposed-check` (sidequest-content)
- **Stack Parent:** 73-3 (depends_on, status:done — PR #539 merged)

## Epic Context

Epic 73 — Confrontation Engine Hardening — is a follow-up to the 59-8 social_duel opposed_check fix. The epic hardens the confrontation family by:
1. Converting negotiation + scandal to opposed_check (this story)
2. Adding trial withdraw/concede resolution beats + opposed_check (73-2)
3. Fixing advance_confrontation lost-update (73-3, **DONE**)
4. Making CritSuccess beat-kind impact legible (73-4)
5. Suppressing re-fired confrontation_initiated span noise (73-5)

**Dependency:** 73-3 (advance_confrontation lost-update fix) is merged as of PR #539. This story can proceed.

## Acceptance Criteria

From epic-73.yaml:
1. **negotiation resolves via opposed_check** — NPC stats enter the target difficulty calc (not frozen opponent dial)
2. **scandal resolves via opposed_check** — same mechanism as negotiation
3. **ADR-093 balance bands applied + documented** — per-archetype balance pass with documented balance bands (narrative weight / difficulty)
4. **OTEL spans emitted** — both archetypes' resolution paths emit spans legible in GM dashboard
5. **Tests cover both paths** — integration tests against the real packs (caverns_and_claudes, space_opera, etc.)

## Design Notes

- **ADR-093** (Confrontation Difficulty Calibration v1) provides the balance bands for opposed_check calibration
- **ADR-102** (Tool-Use Protocol for Structured Output) governs the tool-use shape for opposed_check resolution
- **Prior art:** social_duel conversion to opposed_check in 59-8 (reference implementation); negotiation and scandal follow the same pattern
- **OTEL observability:** every subsystem decision must emit spans; GM-panel verification is the lie detector
- **No silent fallbacks:** if NPC stats can't be resolved, fail loudly — don't freeze dial as silent default

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-31T03:51:28Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30T00:00:00Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[TEA / Improvement / non-blocking]** RED committed on server branch (2 new test files, 17 tests; 12 fail for the right reasons, 5 are regression guards on already-satisfied invariants). Server commit on `feat/73-1-negotiation-scandal-opposed-check`.
- **[TEA / Question / non-blocking → for Dev]** Scandal head-start decision is pinned to the context's *documented default*: `test_scandal_exposure_keeps_head_start` requires `opponent_metric.starting > player_metric.starting` (asymmetry moves from finish line to start line) AND `test_scandal_thresholds_recalibrated_to_7_7` requires both thresholds == 7. If Dev instead argues the fiction needs unequal *finish lines*, that is an ADR-093 v2 / guardrail-amendment escalation (per AC-2) — do NOT silently relax the test; bounce to SM.
- **[TEA / Improvement / non-blocking → for Dev]** The dial-advance tests assert `opponent_metric.current > 0` (not an exact value) deliberately — the per-side tier/counteract DC formula in `_resolve_opposed_check_branch` is intricate (playtest 2026-05-06 rule). The load-bearing assertions are (a) the `encounter.opposed_roll_resolved` span fired and (b) the opponent dial advanced from its own roll. Conversion is content-only (`tea_and_murder/rules.yaml`): flip `resolution_mode`, add `opponent_default_stats` (≤10) keyed by each beat's `stat_check`, recalibrate scandal dials, add `resolution: true` to `weather_it`. No server code change expected — keep `test_confrontation_calibration.py` green (it activates for tea_and_murder once converted).
- **[TEA / Gap / non-blocking]** Workflow bookkeeping drift: SM's `pf handoff complete-phase`/`marker` calls errored on missing positional args, so the recorded phase stayed `setup`/owner `sm` while the relay launched TEA. I caught up the setup→red transition during my exit. Flagging so SM is aware the marker chain needs the explicit STORY_ID/WORKFLOW/PHASE args in this `pf` version.
- **[Dev / Gap / non-blocking]** The RED commit's server test file imported a non-existent helper `tests._helpers.recording.recording_watcher` (TEA hallucination) — the file errored at collection so its 15 tests never actually ran as RED; only the 2 integration tests were truly RED. GREEN corrected the harness: the real OTEL span-capture API is the `otel_capture` fixture in `tests/integration/conftest.py` (NOT available under `tests/server`). Re-split so content/seating/fail-loud tests live in `tests/server` (no span capture) and the opposed-dice + span tests live in `tests/integration` with `otel_capture`.
- **[Dev / Improvement / non-blocking]** CONFIRMED content-only: no server change was needed. The opposed_check branch (`_resolve_opposed_check_branch`) correctly applies each side's beat to its own-side dial via `apply_beat` (`own_metric = player_metric if actor.side=='player' else opponent_metric`). Runtime-verified: opponent `deflect` Success → exposure +2, containment 0 (scandal's asymmetric metric names route correctly). The story's "content-only, no server change" assumption held.
- **[Dev / Improvement / non-blocking]** Full server suite (corrected — an earlier figure in this finding was a garbled-tool-output artifact): **8178 passed, 2 failed, 1428 skipped**. The 2 failures are `tests/cli/validate/test_pack_validator.py::TestContentValidation::test_all_live_packs_pass_content_validation` and `tests/cli/validate/test_pack_validator_crossref.py::test_all_live_packs_pass_cross_reference_lint`. Both fail with `missing required directory 'assets/images/portraits'`/`'poi'` **for all 10 packs identically** (plus an unrelated `five_points` history.yaml trope-id refs) — a pre-existing R2-asset-hosting condition (assets live in R2, not on disk in this checkout), NOT caused by this confrontation-YAML change (tea_and_murder fails exactly like the 9 untouched packs; the edit touches no asset dirs). NOTE: do NOT set `SIDEQUEST_GENRE_PACKS` when running the server suite — it overrides the hermetic `tests/fixtures/packs/` that `tests/server/conftest.py` installs and produces ~4-6 false social_duel/confrontation failures. The relevant 73-1 tests resolve content via hardcoded relative paths, not that env var.

### TEA (test verification)

- **Improvement** (non-blocking): Dev's "do NOT set `SIDEQUEST_GENRE_PACKS`" warning (above) no longer reproduces. I ran the full server suite both WITH and WITHOUT the env var and got the SAME outcome — the 2 pre-existing asset-dir reds and **zero** false social_duel/confrontation failures. Setting it is strictly better: it un-skips `tests/genre/test_confrontation_calibration.py` (the AC-3 coverage — `test_opposed_check_thresholds_calibrated_to_7[tea_and_murder]` + parity/floor checks, 22 passed). Affects future quality-gate runs (`sidequest-server` env handling) — the hermetic-fixture conflict Dev hit appears to have been a transient earlier-branch state. *Found by TEA during test verification.*

### Reviewer (code review)

- No upstream findings. The change is content + test only, fully within story scope; every AC was independently verified against the live `tea_and_murder` pack (not just via the test assertions). The 2 full-suite reds are the documented R2-asset-hosting baseline, not this story. *Found by Reviewer during code review.*
- **Process** (non-blocking): the `pf handoff complete-phase` atomic session-update dropped the `## Architect Assessment` heading and did a blunt global `Phase: verify → review` string-replace (it rewrote even the body of the Architect Assessment and the freshly-written TEA Assessment). I restored the heading. Matches the existing TEA/Dev workflow-tooling-drift findings above — flagging for SM/tooling awareness. *Found by Reviewer during code review.*

## Architect Assessment

**Phase:** finish · **Verdict:** PASS (all ACs addressed, no undocumented spec drift)

Reviewed the GREEN implementation (content commit `be8c213`, server commit `c42faaef`) against the 6 derived ACs in `sprint/context/context-story-73-1.md`.

| AC | Requirement | Addressed by | Status |
|----|-------------|--------------|--------|
| AC-1 | negotiation → opposed_check, two-sided, opponent_default_stats covers Cunning/Nerve, 7/7 | `rules.yaml` negotiation block + `test_negotiation_is_opposed_check_with_opponent_stats`, `…thresholds_calibrated_to_7`, `test_negotiation_opponent_dial_advances_on_opposed_roll` | ✅ |
| AC-2 | scandal → opposed_check, opponent_default_stats covers Cunning/Pride/Nerve, **deliberate** asymmetric-dial recalibration to 7/7 with head start moved to start line | `rules.yaml` scandal block (inline-documented decision; containment 5→7, exposure 8→7, exposure.starting 0→3) + `test_scandal_thresholds_recalibrated_to_7_7`, `test_scandal_exposure_keeps_head_start` | ✅ |
| AC-3 | both pass the ADR-093 calibration guardrail (≤10 stats, 7/7) | `tests/genre/test_confrontation_calibration.py` green for tea_and_murder + dedicated ceiling tests | ✅ |
| AC-4 | each confrontation RESOLVABLE — terminal push resolves on any tier; `scandal.weather_it` gains `resolution: true` | `rules.yaml` weather_it flag + `test_scandal_resolves_on_weather_it` (all tiers), walk_away regression guard | ✅ |
| AC-5 | `encounter.opposed_roll_resolved` span fires | `test_{negotiation,scandal}_opponent_dial_advances_on_opposed_roll` via `otel_capture` | ✅ |
| AC-6 | opponent stat sourcing fails loud; no-Other handled (ADR-116) | complete `opponent_default_stats` + `test_{negotiation,scandal}_with_no_other_fails_loud`, seating tests | ✅ |

**Spec-fidelity notes:**
- The AC-2 central judgment call landed on the context's documented *default and expected outcome* (both thresholds 7, head start as start-line asymmetry). No guardrail amendment / ADR-093-v2 escalation was needed — correct call, in scope.
- Confirmed **content-only** as the spec assumed: no server/engine change. Runtime-verified that the existing `_resolve_opposed_check_branch` + `apply_beat` route each side to its own-side dial correctly even with scandal's asymmetric metric *names* (containment/exposure) — the earlier "metric-routing bug" was a garbled-tool-output phantom, not real.
- Scope boundaries honored: trial (73-2), advance_confrontation (73-3), push CritSuccess (73-4), re-fired span (73-5), social_duel/auction all untouched.
- No undocumented drift. The one deliberate divergence (scandal threshold recalibration) is documented inline in `rules.yaml` and in the AC docstrings — see Design Deviations.

**Hand to TEA (verify):** lint/typecheck/full-suite quality pass. Pre-existing full-suite reds (2 pack-validator asset-dir checks, all packs, R2-hosting) are out of scope — do not chase.

## TEA Assessment

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`tea_and_murder/rules.yaml`, `test_negotiation_scandal_opposed_check.py`, `test_negotiation_scandal_resolve.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings (1 medium, 2 low) | Test-helper duplication across the unit/integration pair (`_pack()`, `_make_npc()`, `_push_beat()`) — each self-flagged as intentional parallel-structure mirroring the `social_duel` precedent. |
| simplify-quality | clean | No naming/dead-code/readability/architecture issues. |
| simplify-efficiency | clean | No over-engineering; parametrization, helpers, and OTEL span capture all justified. |

**Applied:** 0 high-confidence fixes (none were high-confidence).
**Flagged for Review:** 1 medium — `_make_npc()` could move to a shared helper, but test files are deliberately non-DRY and the `social_duel` precedent defines it inline too; left as-is (canonical pattern). Not applied.
**Noted:** 2 low — `_pack()` / `_push_beat()` extraction candidates; left local for test-layer readability. Not applied.
**Reverted:** 0 (no simplify commit — nothing applied, so no regression risk to check).

**Overall:** simplify: clean (no fixes applied — only intentional, precedent-backed test duplication flagged)

### Quality Checks

- **Lint (ruff):** clean — `All checks passed!` on both changed test files.
- **Full server suite (WITH `SIDEQUEST_DATABASE_URL` + `SIDEQUEST_GENRE_PACKS`):** **8179 passed, 2 failed, 1427 skipped.**
- **Pre-existing reds (out of scope, per Architect baseline):** `test_all_live_packs_pass_content_validation` + `test_all_live_packs_pass_cross_reference_lint`. **Measured cause:** both fail purely on `missing required directory 'assets/images/portraits'`/`'poi'` — identically across **all 10 packs** (R2-hosted assets, not on disk). `tea_and_murder` fails exactly like the 9 untouched packs; **zero** errors reference `negotiation`/`scandal`/`resolution_mode`/thresholds. Confirmed present in BOTH env configs (with/without `GENRE_PACKS`) → not introduced by this change.
- **No new failures** vs. the documented baseline.
- **Story's own tests:** 25/25 pass (12 unit + parametrized integration), including the `encounter.opposed_roll_resolved` OTEL span assertions (AC-5) and the no-Other fail-loud guards (AC-6).
- **AC-3 calibration coverage:** `tests/genre/test_confrontation_calibration.py` — 22 passed with content env, incl. `test_opposed_check_thresholds_calibrated_to_7[tea_and_murder]`.

**Handoff:** To Reviewer (Colonel Potter) for code review.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

- **[Dev/Architect] scandal dial recalibration (in-scope, spec-sanctioned).** What changed: scandal's `containment` threshold 5→7, `exposure` threshold 8→7, and `exposure.starting` 0→3. What the spec said: the original content authored asymmetric *thresholds* (5/8) as the gossip's head start. Why: ADR-093 v1 owns the opposed_check threshold (must be symmetric 7/7; the calibrated tie band + `test_confrontation_calibration.py` assume it). Per AC-2's documented default, the fiction's head start was preserved by moving the asymmetry to the *start line* (exposure starts at 3) rather than the finish line. This is the expected outcome named in the context's Assumptions, not a silent test relaxation — documented inline in `rules.yaml` and in the AC docstrings. Asymmetric thresholds remain ADR-093 v2 territory (not introduced here).

### TEA (verify)
- No deviations from spec. Verify phase applied no code or test changes: simplify produced zero high-confidence findings (the only flags were precedent-backed test-helper duplication, left intentionally), so no fixes were applied and no simplify commit was made. The quality gate ran against the existing GREEN implementation unchanged.

### Reviewer (audit)
- **[Dev/Architect] scandal dial recalibration (5/8 thresholds → 7/7, exposure.starting 0→3)** → ✓ **ACCEPTED by Reviewer.** This is the spec-sanctioned path, not silent drift. Verified directly against `rules.yaml`: ADR-093 v1 owns the opposed_check threshold and requires symmetric 7/7 (enforced by `test_confrontation_calibration.py`, which now activates for tea_and_murder and passes — `test_opposed_check_thresholds_calibrated_to_7[tea_and_murder]`). The gothic head start is genuinely preserved — `exposure.starting=3 > containment.starting=0` (`test_scandal_exposure_keeps_head_start`). The asymmetry moved from finish line to start line, exactly as AC-2's documented default prescribes. Asymmetric *thresholds* correctly deferred to ADR-093 v2 (not introduced). Inline-documented in `rules.yaml` lines 423–434 and in the AC docstrings. No guardrail amendment was needed or smuggled in.
- No undocumented deviations found. I enumerated every changed field in `rules.yaml` (resolution_mode, opponent_default_stats, both metric thresholds/starts, weather_it.resolution) against the 6 ACs and the context spec — all are either an AC requirement or the one logged, accepted deviation above.

### Architect (reconcile)

**Existing-entry verification:** The `[Dev/Architect] scandal dial recalibration` entry above was checked field-by-field and is accurate — its spec source resolves, its quoted intent matches the context, and its implementation description matches the live `rules.yaml`. The `### TEA (verify)` and `### Reviewer (audit)` subsections are likewise accurate. No corrections needed.

**Definitive deviation manifest (self-contained — boss can audit from this entry alone):**

- **Scandal dial recalibration — asymmetry moved from finish line to start line.**
  - **Spec source:** `sprint/context/context-story-73-1.md`, AC-2 ("scandal converts to opposed_check with a DELIBERATE asymmetric-dial decision") and the Assumptions section.
  - **Spec text (quoted):** "the default and expected outcome is both==7 with the head-start moved to `starting`, because v1 calibration owns the threshold and this story is not chartered to introduce asymmetric-threshold support into the guardrail … The asymmetry moves from *unequal finish lines* to *unequal start lines*."
  - **Implementation:** In `sidequest-content/genre_packs/tea_and_murder/rules.yaml`, scandal's `containment.threshold` 5→7, `exposure.threshold` 8→7, and `exposure.starting` 0→3 (`containment.starting` stays 0). `resolution_mode: opposed_check` and `opponent_default_stats: {Cunning:10, Pride:10, Nerve:10}` added; `weather_it` gains `resolution: true`.
  - **Rationale:** ADR-093 v1 owns the `opposed_check` threshold and requires symmetric 7/7 (the calibrated tie-band assumes equal finish lines, enforced by `tests/genre/test_confrontation_calibration.py::test_opposed_check_thresholds_calibrated_to_7`). The gossip's authored head start is preserved by start-line geometry (`exposure.starting=3 > containment.starting=0`) instead of an unequal finish line.
  - **Severity:** minor — this is the context's *documented default*, i.e. a deviation from the *prior authored content*, not from the spec. No guardrail amendment introduced.
  - **Forward impact:** Asymmetric-*threshold* support remains ADR-093 v2 / "Forward debt" (explicitly deferred, not introduced here). No impact on sibling stories 73-2 (trial), 73-4 (CritSuccess legibility), 73-5 (span noise); social_duel/auction untouched.

- No additional deviations found. (AC-deferral cross-check: no ACs were deferred — all 6 derived ACs are DONE per the spec-check and review assessments — so that step is a no-op.)

## Subagent Results

Per `pf settings get workflow.reviewer_subagents`: only `preflight` is enabled in this project; the other 8 diff-based specialists are disabled via settings. Disabled specialists are pre-filled as Skipped — their domains were assessed by the Reviewer directly (see Rule Compliance + Observations) and do not block the gate.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | success | 0 (GREEN: 8179 pass / 2 pre-existing baseline reds / 1427 skip; ruff clean; 0 smells; baseline_deviation: false) | confirmed 0, dismissed 0 — independently corroborates the Reviewer's own measurement |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — boundary paths assessed by Reviewer ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — fail-loud paths assessed by Reviewer ([SILENT] below) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality assessed by Reviewer ([TEST] below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — docs/comments assessed by Reviewer ([DOC] below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — schema/type assessed by Reviewer ([TYPE] below) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — security assessed by Reviewer ([SEC] below) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity already covered by TEA verify-phase simplify fan-out ([SIMPLE] below) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — project rules enumerated by Reviewer ([RULE] below) |

**All received:** Yes (1 enabled specialist returned; 8 disabled via settings and pre-filled as Skipped)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Rule Compliance

Project rules sources: `SOUL.md`, `CLAUDE.md` (server + content), `.pennyfarthing/gates/lang-review/python.md` (13 checks). No `.claude/rules/` dir exists. The changed files are 1 YAML config + 2 Python test files (no production code), so the applicable rules are content-correctness, the SOUL/CLAUDE principles, and the python checklist's test-relevant items (#5 path, #6 test-quality, #8 deserialization, #10 imports).

**SOUL/CLAUDE — No Silent Fallbacks (load-bearing here):** Enumerated EVERY beat's `stat_check` against each confrontation's `opponent_default_stats`:
- negotiation beats {persuade=Cunning, threaten=Nerve, concede_point=Cunning, walk_away=Nerve} → stats {Cunning, Nerve} → declared {Cunning:10, Nerve:10}. **Complete — no fail-loud gap in normal play.** ✓
- scandal beats {deflect=Cunning, counter_accusation=Pride, confide=Cunning, weather_it=Nerve} → stats {Cunning, Pride, Nerve} → declared {Cunning:10, Pride:10, Nerve:10}. **Complete.** ✓
- The fail-loud (`resolve_opponent_modifier` raises on a missing stat) is the *intended* No-Silent-Fallback behavior; the content is complete so it never fires in authored play. Compliant.

**ADR-093 calibration:** opposed_check thresholds must be symmetric 7/7 and `opponent_default_stats` ≤10. negotiation 7/7, scandal 7/7; all stat values exactly 10 (→ +0 modifier, challenge from dial/DC geometry not stat inflation). ✓

**ADR-116 (a confrontation requires an Other):** seating + no-Other fail-loud verified by `test_{negotiation,scandal}_seats_other_as_opponent_via_location_fallback` and `test_{negotiation,scandal}_with_no_other_fails_loud` (raises `NoOpponentAvailableError`). ✓

**OTEL Observability Principle:** the converted path routes through `_resolve_opposed_check_branch` and fires `encounter.opposed_roll_resolved`; `test_{negotiation,scandal}_opponent_dial_advances_on_opposed_roll` asserts the span fires (lie-detector present, AC-5). ✓

**Crunch in the Genre, Flavor in the World:** mechanics live in the genre pack's `rules.yaml`, not engine code — correct layer; confirmed content-only (no production server change). ✓

**python.md #5 path-handling:** test path uses `pathlib.Path(...).resolve()`. ✓ **#6 test-quality:** no `assert True`/vacuous assertions; `monkeypatch.setattr` targets `narration_apply` where the symbol is *used* (correct target); parametrized `_ALL_TIERS` tests the genuine per-tier resolution contract (not a redundant same-path repeat); `skipif` guards carry reasons. ✓ **#8 deserialization:** no pickle/eval; YAML loaded via the genre loader (not test-introduced). ✓ **#10 imports:** explicit, no star imports; function-local imports in `_make_npc` avoid import-time coupling. ✓

## Observations

1. `[VERIFIED]` opponent_default_stats completeness — evidence: `rules.yaml:179-181` (negotiation Cunning/Nerve) and `:419-422` (scandal Cunning/Pride/Nerve) cover every beat `stat_check` at lines 194-228 / 444-469. Complies with SOUL "No Silent Fallbacks". **Highest-value check — this is the whole point of the conversion.**
2. `[VERIFIED]` ADR-093 7/7 calibration — evidence: `rules.yaml:188/192` (negotiation 7/7), `:438/442` (scandal 7/7); all opponent_default_stats == 10 ≤ ceiling.
3. `[RULE]` head-start preserved as start-line asymmetry, not finish-line — evidence: `rules.yaml:191` (negotiation opp starting 3) and `:441` (scandal exposure starting 3) vs player starting 0. Honors AC-2's documented default and keeps ADR-093 symmetric thresholds.
4. `[SILENT]` terminal push resolves on ANY tier — evidence: `weather_it.resolution: true` (`:476`) and `walk_away.resolution: true` (`:228`); `test_scandal_resolves_on_weather_it[Fail/CritFail/Tie/Success]` proves no frozen-dial soft-lock (the 59-8 class). No swallowed/silent non-resolution.
5. `[EDGE]` no-Other instantiation fails loud — evidence: `test_{negotiation,scandal}_with_no_other_fails_loud` expects `NoOpponentAvailableError` (ADR-116). Boundary (empty roster) handled by raising, not by seating a one-sided contest.
6. `[TEST]` opposed-dice path is exercised for real, not shallow — evidence: `_drive_opposed` monkeypatches `_roll_d20_server_side→18` (opponent Success) with `opposed_player_d20=3` (player Fail), then asserts opponent dial advances from ITS OWN roll (`> 0`) while player dial stays 0, AND the span fired. This is the mechanical inverse of the playtest bug.
7. `[DOC]` inline comments are accurate and load-bearing — evidence: `rules.yaml:166-184, 411-434, 470-475` explain the 59-8 unfairness, the ADR-093 recalibration, and the fail-loud rationale; all match the actual field values. Not stale, not over-documented.
8. `[TYPE]` schema correctness — evidence: `resolution_mode: opposed_check` maps to `ResolutionMode.opposed_check` (import + assertion in `test_*_is_opposed_check_with_opponent_stats`); `opponent_default_stats` is a str→int map; `resolution: true` is a bool beat flag. Loads cleanly (preflight + 8179 passing tests confirm no schema rejection).
9. `[SEC]` no security surface — content YAML + test-only Python; no user input, no SQL, no deserialization of untrusted data, no shell. N/A by construction.
10. `[SIMPLE]` simplicity confirmed — TEA's verify-phase simplify fan-out (reuse/quality/efficiency) returned clean with 0 high-confidence findings; the only flags were intentional, precedent-backed test-helper duplication.

## Devil's Advocate

Let me argue this is broken. **First attack — the fail-loud is a landmine in live play.** If a future author adds a scandal beat that rolls, say, `Passion`, without updating `opponent_default_stats`, `resolve_opponent_modifier` will raise mid-confrontation and blow up a player's session. Is that acceptable? Yes — it is the *designed* No-Silent-Fallback behavior, and it is caught at authoring time: `test_*_is_opposed_check_with_opponent_stats` computes `beat_stats - set(stats)` and fails the suite if any beat stat is uncovered. So the landmine is guarded by a tripwire that fires in CI, not in play. Acceptable. **Second attack — the integration test fakes the dice.** `_drive_opposed` monkeypatches `_roll_d20_server_side` and hand-feeds `opposed_player_d20=3`. Could the opposed path be broken in a way the fake hides? The fake only fixes the d20 *values*; the routing (`_resolve_opposed_check_branch`), the per-side dial attribution (`own_metric = player if side==player else opponent`), the tier computation, and the span emission all run for real against the real pack cdef. The assertion that the OPPONENT's dial advanced from the opponent's own roll while the player's stayed at 0 is exactly the bug-inverse, and it cannot pass if attribution is wrong. Acceptable. **Third attack — the test fixture sets stats to 12, above the ADR-093 ceiling of 10.** Does that smuggle a calibration violation? No — 12 is in the *test's* synthetic `per_actor_state`, deliberately chosen so the modifier resolves cleanly regardless of `opponent_default_stats`; the *content* stats are 10, verified separately and by `test_confrontation_calibration.py`. The 12 tests the dice path, not the ceiling. Acceptable. **Fourth attack — a confused author reads "both thresholds 7" and thinks the gossip lost its advantage.** The inline comment (`:423-434`) and the `test_scandal_exposure_keeps_head_start` name both explain the start-line geometry explicitly, and the comment is co-located with the values. Low confusion risk. **Fifth attack — stressed filesystem / malformed YAML.** The pack loads through pydantic models with `extra="forbid"` semantics elsewhere in the codebase; a typo'd field would fail loud at server load, and the 8179-passing suite (which loads the real pack many times) demonstrates it parses. No new finding from the devil's advocate pass — the design anticipated each attack.

## Reviewer Assessment

**Verdict:** APPROVED

This is a clean, narrow, content + test-only change that generalizes the 59-8 social_duel opposed_check fix to its two `tea_and_murder` siblings (negotiation, scandal). Every one of the 6 derived ACs is satisfied and independently verified against the live pack — not merely asserted by the tests.

**Data flow traced:** player/opponent intent → `instantiate_encounter_from_trigger` seats the Other `opponent`-side (or raises `NoOpponentAvailableError` if none — ADR-116) → each beat routes through `_resolve_opposed_check_branch` → the opponent rolls d20+modifier (modifier from `opponent_default_stats`, all ≤10) → `apply_beat` advances each side's *own* dial → `encounter.opposed_roll_resolved` span fires (GM-panel lie-detector). Safe because the opponent's dial can no longer freeze and no delta is narrator-fiat.

**Pattern observed:** mechanics correctly authored in the genre pack's `rules.yaml` (Crunch in the Genre), mirroring the social_duel recipe — at `sidequest-content/genre_packs/tea_and_murder/rules.yaml:159-231` (negotiation) and `:406-477` (scandal).

**Error handling:** No Silent Fallbacks honored — `opponent_default_stats` completely covers every beat `stat_check` (enumerated above); the missing-stat fail-loud is guarded by a CI tripwire. Terminal pushes carry `resolution: true` (no frozen-dial soft-lock). No-Other fails loud.

**Subagent dispatch:** `[SILENT]` `[EDGE]` `[TEST]` `[DOC]` `[TYPE]` `[SEC]` `[SIMPLE]` `[RULE]` — only `reviewer-preflight` was enabled (project settings); it returned GREEN with zero baseline deviation. The 8 disabled specialists' domains were each assessed directly by the Reviewer (tagged inline in Observations / Rule Compliance) and surfaced no Critical/High issues.

**Quality gate:** ruff clean; full suite 8179 passed / 2 pre-existing R2-asset-hosting baseline reds (measured: every pack fails identically; zero relation to this YAML edit) / 1427 skipped; story's 25 tests green incl. AC-5 span + AC-6 fail-loud; AC-3 calibration 22 passed for tea_and_murder.

**Handoff:** To SM (Hawkeye) for finish-story. **Reviewer does not merge** — SM creates + merges the per-subrepo PRs in the finish phase.