---
story_id: "158-38"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-38: Pronoun/POV localizer residuals after 158-8/14 — verb-agreement stays 3rd-person-singular after name->you swap (does you / grips); solo resume/replay still drops the POV swap entirely

## Story Details
- **ID:** 158-38
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/158-38-pov-localizer-residuals

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T22:15:08Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T20:59:11.932257+00:00 | 2026-06-25T21:02:18Z | 3m 6s |
| red | 2026-06-25T21:02:18Z | 2026-06-25T21:21:58Z | 19m 40s |
| green | 2026-06-25T21:21:58Z | 2026-06-25T22:03:42Z | 41m 44s |
| review | 2026-06-25T22:03:42Z | 2026-06-25T22:15:08Z | 11m 26s |
| finish | 2026-06-25T22:15:08Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

No upstream findings

### TEA (test design)
- **Improvement** (non-blocking): The replay comment at `connect.py:1477` ("byte-identical to what the live player received") is stale/misleading. Verified during test authoring: the projection cache is written from the pre-swap projection decision (`emitters.py` `_cache_decision`, ~line 613, runs *before* the per-recipient `_apply_pov_swap` at ~line 659), so the cache holds the canonical 3rd-person prose, NOT what the player received live. Affects `sidequest/handlers/connect.py` (comment should be corrected when the replay swap lands).
  *Found by TEA during test design.*
- **Gap** (non-blocking): There are THREE replay reconstruction sites that re-emit stored prose and ALL lack the POV swap — the cache-replay loop (`connect.py` ~1531 `_build_message_for_kind`), the legacy event-log fallback (`connect.py` ~1575), and the tail-backfill (`views.backfill_last_narration_block`). The RED tests pin the tail-backfill (the solo/fresh-browser resume path). Dev should localize at all three via a single shared helper so the main-loop sites are covered too. Affects `sidequest/handlers/connect.py` + `sidequest/server/views.py`.
  *Found by TEA during test design.*
- **Question** (non-blocking): Solo-mode cache-row population for resume is unverified. `project_emitter = author_player_id is not None` (`emitters.py:456`), so a solo turn (no `author_player_id`) writes no per-player projection_cache row, and `read_narration_backfill` INNER-JOINs projection_cache by player_id — a solo player could get zero backfill rows. The 2026-06-24 finding is solo, so dev must confirm where solo-resume narration is actually reconstructed (cache vs legacy event-log fallback) and ensure the swap is applied on *that* path. Affects `sidequest/game/pg/narrative.py::read_narration_backfill` + the legacy fallback in `connect.py`.
  *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (non-blocking): TEA's Gap is closed — `localize_replay_message` is wired into all three replay sites (backfill + both `connect.py` branches). TEA's solo-resume Question is mitigated: the localizer runs identically in the cache-replay loop and the legacy event-log fallback, so whichever path a solo resume takes is covered. The exact solo cache-row behavior still merits a future `_handle_connect` integration test. Affects `sidequest/handlers/connect.py`, `sidequest/server/views.py`, `sidequest/server/emitters.py`.
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): `tests/agents/test_use_mutation_tool.py::test_refusal_payload_round_trips` is flaky under pytest-xdist parallelism — it fails only in a full parallel `tests/agents/` run and passes alone, whole-file, and in the full suite run serially (`-n0`). Confirmed pre-existing: it also fails in parallel with this story's source changes stashed (the new test file merely shifts xdist worker co-location). Same class as the documented OTEL parallel-pollution. Affects `tests/agents/test_use_mutation_tool.py` (needs test isolation hardening; unrelated to this story).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): The full `tests/server/` suite has ~60 pre-existing failures even serially (turn-pipeline / dispatch / chargen wiring fixtures — `test_turn_span_wiring`, `test_turn_record_wiring`, `test_tension_tracker_turn_wiring`, `test_player_turn_author`, `test_scenario_bind`, `test_narration_seam_recovery`, …), matching the documented WWN-content-vs-server-fixture drift. Verified this story adds ZERO new failures: a baseline run with the source stashed (62 fail) vs with the fix (60 fail) shows an empty `in-mine-not-in-baseline` set; the count drifts 59/60/62 across identical-source runs (flaky pre-existing fixtures). Affects `tests/server/**` wiring fixtures (need a content/fixture reconciliation; out of scope here).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): PRE-EXISTING `_visibility` sidecar leak on the resume/replay path. The replay reconstruction rebuilds `NarrationPayload` with `visibility_sidecar` populated and there is no egress-strip on the replay send path (the live fan-out strips it in `_deliver_fanout`, emitters.py:168). The reconnecting client receives `_visibility` (anchor_pc, visible_to, fidelity, pov_strategy) on replayed NARRATION. Confirmed by reviewer-security (CWE-200) AND confirmed PRE-EXISTING + byte-neutral to this story (both `_build_message_for_kind` and `localize_replay_message` serialize identical `_visibility`). Severity Medium (server-side metadata to an already-authorized content recipient; not cross-player secret content). Affects `sidequest/handlers/connect.py` + `sidequest/server/views.py` replay send paths — needs ONE egress-strip covering ALL replay frames (swapped + un-swapped + non-NARRATION), mirroring `_deliver_fanout`'s `_visibility.pop`. The narrow per-swap fix in `localize_replay_message` would be incomplete (no-op/un-swapped frames still leak), so this wants a dedicated follow-up rather than a one-liner here.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Pass 10 (subject-aux inversion) optional hardening — gate on `had_subject_swap` instead of `name_swap_occurred`, and use `text.rstrip().endswith("?")` instead of `"?" in text`, to fully close the narrow (cosmetic, unreproduced) over-fire windows the edge-hunter flagged. Affects `sidequest/agents/pov_swap.py` Pass 10 (no behavior change for any current test; defensive only).
  *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Facet 2 pinned at the tail-backfill seam, not via a full `_handle_connect` reconnect**
  - Rationale: `backfill_last_narration_block` is a real, importable production reconstruction site that hits the reported 2026-06-24 path; standing up `_handle_connect` would be a large, fragile harness for the same assertion. The main cache-replay loop + legacy fallback are covered by a Delivery Findings Gap recommending a shared helper.
  - Severity: minor
  - Forward impact: Dev must apply the localization at all three replay sites (not only the backfill) so the main-loop reconnect path is also fixed; a follow-up harness for `_handle_connect` would close the residual coverage gap.
- **No dedicated replay skip-span (pov_swap_skipped) test on the new path**
  - Rationale: Avoids an over-engineered fixture for a guard already exercised on the shared helper; the origin marker (the new requirement) is pinned on the fired-swap span.
  - Severity: minor
  - Forward impact: If the dev wants belt-and-suspenders, add a replay skip-span test; otherwise the shared `_apply_pov_swap` skip spans carry over once origin is threaded.
- **Subject-auxiliary inversion gated on an interrogative clause ("?" present)**
  - Rationale: Subject-auxiliary inversion only occurs in questions; in declaratives "you" after an aux is the object/predicate, and conjugating there ("It are you") is wrong. The "?" gate is the correct scope for the inversion case, not a reduction of real coverage. All four cited repros are questions.
  - Severity: minor
  - Forward impact: none — a hypothetical declarative subject-aux inversion (literary/archaic, no genre prose produces it) would not be re-agreed; no test or playtest needs it.
- **Replay localization applied at all three reconstruction sites, not only the tested backfill seam**
  - Rationale: AC-2 + the "make 5 connections, not 3" rule — the main reconnect loop is the live-resume path; fixing only the tail-backfill would leave it broken. This is completeness, not a deviation from the requirement.
  - Severity: minor
  - Forward impact: none — additive; the connect-loop sites would benefit from a future `_handle_connect` integration harness (TEA deviation noted the absence).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **Facet 2 pinned at the tail-backfill seam, not via a full `_handle_connect` reconnect**
  - Spec source: context-story-158-38.md, AC-2 ("Replayed narration events apply _apply_pov_swap on reconnect")
  - Spec text: "When a NARRATION message is rebuilt from cache/storage during connect replay, apply POV localization per recipient before sending"
  - Implementation: The RED integration test drives the real `views.backfill_last_narration_block` reconstruction (the production tail-backfill that a solo/fresh-browser resume traverses) rather than standing up the full `_handle_connect` async reconnect (no existing test harness exercises it, and solo per-player cache-row population is unverified — see Delivery Findings Question).
  - Rationale: `backfill_last_narration_block` is a real, importable production reconstruction site that hits the reported 2026-06-24 path; standing up `_handle_connect` would be a large, fragile harness for the same assertion. The main cache-replay loop + legacy fallback are covered by a Delivery Findings Gap recommending a shared helper.
  - Severity: minor
  - Forward impact: Dev must apply the localization at all three replay sites (not only the backfill) so the main-loop reconnect path is also fixed; a follow-up harness for `_handle_connect` would close the residual coverage gap.
- **No dedicated replay skip-span (pov_swap_skipped) test on the new path**
  - Spec source: context-story-158-38.md, AC-2 ("log narration.pov_swap_skipped/narration.second_person_swap spans on replay path with origin='replay'")
  - Spec text: "Lie-detector OTEL: log narration.pov_swap_skipped/narration.second_person_swap spans on replay path with origin='replay' marker"
  - Implementation: Pinned only the `narration.second_person_swap` origin='replay' span (the swap-fired case). The `pov_swap_skipped` origin='replay' case is not separately pinned because constructing a skip scenario (pc-not-in-snapshot / empty-pronouns) through the backfill seam is contrived; the skip-reason spans are already covered for the shared `_apply_pov_swap` by the 158-14 suite.
  - Rationale: Avoids an over-engineered fixture for a guard already exercised on the shared helper; the origin marker (the new requirement) is pinned on the fired-swap span.
  - Severity: minor
  - Forward impact: If the dev wants belt-and-suspenders, add a replay skip-span test; otherwise the shared `_apply_pov_swap` skip spans carry over once origin is threaded.

### Dev (implementation)
- **Subject-auxiliary inversion gated on an interrogative clause ("?" present)**
  - Spec source: context-story-158-38.md, AC-1 ("all verbs conjugated to 2nd-person form, not just the immediate verb")
  - Spec text: "After a name→you swap, all verbs conjugated to 2nd-person form, not just the immediate verb following the subject"
  - Implementation: The new Pass 10 only re-agrees a leading irregular auxiliary (`does/has/is/was`) before a swapped `you` when the clause contains `?`. A declarative `<aux> you` (object position — "It is you.", "the dragon has you in its claws") is left untouched.
  - Rationale: Subject-auxiliary inversion only occurs in questions; in declaratives "you" after an aux is the object/predicate, and conjugating there ("It are you") is wrong. The "?" gate is the correct scope for the inversion case, not a reduction of real coverage. All four cited repros are questions.
  - Severity: minor
  - Forward impact: none — a hypothetical declarative subject-aux inversion (literary/archaic, no genre prose produces it) would not be re-agreed; no test or playtest needs it.
- **Replay localization applied at all three reconstruction sites, not only the tested backfill seam**
  - Spec source: context-story-158-38.md, AC-2 ("Replayed narration events apply _apply_pov_swap on reconnect") + TEA Delivery Findings Gap
  - Spec text: "When a NARRATION message is rebuilt from cache/storage during connect replay, apply POV localization per recipient before sending"
  - Implementation: Added a shared `emitters.localize_replay_message` and wired it into `views.backfill_last_narration_block` (the RED-tested seam) AND both `connect.py` reconnect branches (cache-replay loop + legacy event-log fallback). The RED test pins only the backfill; the connect-loop sites are covered by reuse of the same helper.
  - Rationale: AC-2 + the "make 5 connections, not 3" rule — the main reconnect loop is the live-resume path; fixing only the tail-backfill would leave it broken. This is completeness, not a deviation from the requirement.
  - Severity: minor
  - Forward impact: none — additive; the connect-loop sites would benefit from a future `_handle_connect` integration harness (TEA deviation noted the absence).

### Reviewer (audit)
- **TEA: Facet 2 pinned at the tail-backfill seam** → ✓ ACCEPTED by Reviewer: the backfill IS a real production reconstruction site, and Dev went further and wired the shared helper into all three replay sites, so the seam choice is sound.
- **TEA: No dedicated replay skip-span test** → ✓ ACCEPTED by Reviewer: the skip-reason spans are exercised on the shared `_apply_pov_swap` by the 158-14 suite; the new `origin='replay'` marker is pinned on the fired-swap span. Reasonable.
- **Dev: Inverted-aux gated on an interrogative ("?") clause** → ✓ ACCEPTED by Reviewer: subject-aux inversion only occurs in questions, so the gate is correct scope. Edge-hunter raised narrow over-fire concerns (mid-clause "?", `name_swap_occurred` vs `had_subject_swap`); I reproduced none of them as actual corruption — all probes left the irregular aux untouched because the eligible aux never aligned immediately before an object-`you`. Cosmetic-only and narrow; acceptable for v1 (optional hardening filed as a non-blocking finding).
- **Dev: Replay localization applied at all three reconstruction sites** → ✓ ACCEPTED by Reviewer: this closes the TEA Gap and is the correct, complete wiring (backfill + both connect.py branches).
- **UNDOCUMENTED (pre-existing, not introduced here): the replay send path lacks the `_visibility` egress-strip** that the live fan-out applies (`_deliver_fanout` pops `_visibility`). The rebuilt `NarrationPayload` carries `visibility_sidecar` to the wire. Verified this is PRE-EXISTING — `_build_message_for_kind` already populated `visibility_sidecar` before this story, and `localize_replay_message` is byte-identical on `_visibility` (proven: both serialize the same `_visibility`). Not a deviation introduced by 158-38; filed as a non-blocking Delivery Finding for a dedicated replay-egress-strip follow-up. Severity: Medium (server-side metadata to an already-authorized content recipient).

## Sm Assessment

**Story:** 158-38 (3pt, p3, tdd). Server-only follow-up closing two residual skip-paths from DONE 158-8/158-14 (the `_apply_pov_swap` / pronoun-localizer work).

**Scope — two concrete, independently-reproducible defects:**
1. **Verb-agreement residual** — the name→`you` swap fixes the noun but leaves the governing verb 3rd-person-singular: "Which way *does you* mean to go" (→ "do you"); "You check the anchor then *grips* the rope and swing" (→ "grip"). Coordinated/secondary verb positions are not re-agreed after the swap. Lives in the localizer (`pov_swap.py` `_conjugate` / `swap_to_second_person`, invoked from `emitters.py` `_apply_pov_swap`).
2. **Solo resume/replay residual** — `_apply_pov_swap` runs at live-emit only. The ADR-133 full-replay mirror (reconnect path in `connect.py`) re-emits stored 3rd-person prose without re-applying the swap for the resuming acting player (Zeppo-touches-flame vs live "You touch flame"). `narrative_log` empty; history reconstructed from stored turn events holding the un-swapped form.

**Routing:** Phased TDD → next agent **tea** (red phase). Both defects are deterministic string/replay behavior with an existing test file (`test_pov_swap.py`) establishing the API contract — well-suited to failing-test-first. Context doc `sprint/context/context-story-158-38.md` carries file locations, root-cause hypotheses, and three draft ACs.

**Cautions for downstream agents:**
- Verb re-agreement must NOT over-apply to nouns/adjectives that happen to follow the swapped pronoun — the red tests should pin both the fix and the non-regression.
- The replay fix must apply the *same* guards and OTEL spans as the live emit path, not a parallel ad-hoc swap.
- Both are cosmetic/immersion (no mechanical state), so keep the blast radius inside the localizer + replay emit; do not touch stored turn-event prose.
- No Jira key — Jira steps skipped by design.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** Two reproducible behavioral defects; both deterministic and unit/integration-testable.

**Test Files:**
- `tests/agents/test_pov_swap_158_38_verb_agreement.py` — Facet 1 unit tests against the real `swap_to_second_person` (pure string transform; no harness).
- `tests/server/test_pov_swap_replay_158_38.py` — Facet 2 integration tests driving the real `views.backfill_last_narration_block` reconstruction (3-PC MP room, Postgres-backed event log + projection cache; mirrors `test_narration_pov_emission.py`).

**Tests Written:** 16 tests covering 3 ACs — 10 RED defect pins + 6 GREEN guards.
**Status:** RED (verified twice — direct `pytest -n0` and the `testing-runner` subagent: 10 failed, 6 passed, matching expectation exactly).

Facet 1 (AC-1, verb-agreement), 13 tests:
- RED (8): bare `then <verb>` coordination not conjugated (`then grips`→want `then grip`, full 2026-06-23 repro + minimal + she/her); subject-auxiliary inversion not agreed (`does you`→`do you` full repro + parametrized does/has/was + sentence-initial `Is`→`Are` capitalization).
- GREEN guards (5): bare-then does not touch a noun-governed verb (`then the gate slams`); bare-then is clause-local (NPC clause untouched); existing `and then` / `, then` adverb-skip still work; inverted-aux does not overreach to a non-PC subject (`the gate does its work`).

Facet 2 (AC-2, resume/replay), 3 tests:
- RED (2): Carl's own card replays 3rd-person ("Carl plants a boot") instead of "You plant a boot"; no `narration.second_person_swap` span with `origin='replay'` fires on the backfill path.
- GREEN guard (1): a non-anchor recipient (Donut, whose PC isn't in the prose) still reads 3rd-person on replay — pins against over-swapping.

AC-3 (no regression): existing `tests/agents/test_pov_swap.py` + `test_pov_swap_158_8_finding_pins.py` + `test_pov_swap_otel.py` all green (96 passed) at the RED commit; the new guards lock the boundaries the fix must not cross.

### Rule Coverage

| Rule (python lang-review / project) | Test(s) | Status |
|------|---------|--------|
| #6 Test quality — meaningful assertions, no vacuous truthy checks | all 16 (exact-string / fragment / span-attribute asserts) | enforced |
| #6 Parametrized cases test distinct paths | `test_inverted_auxiliary_mid_sentence_agrees` (does/has/was — 3 irregular-aux paths) | covered |
| No Silent Fallbacks / OTEL Observability (CLAUDE.md) | `test_resume_replay_emits_second_person_swap_span_with_replay_origin` (replay path must emit the lie-detector span, not silently ship stored prose) | failing (RED) |
| Wiring test (CLAUDE.md "every suite needs a wiring test") | `tests/server/test_pov_swap_replay_158_38.py` drives the real production `backfill_last_narration_block` end-to-end (not a reimplementation) | failing (RED) |
| #1 No silent swallow on the new replay code | covered indirectly via the origin='replay' span requirement | n/a (dev) |

**Rules checked:** 6 of 8 python lang-review checks apply to test-only changes; #6 (test quality) and the project OTEL/wiring rules are the load-bearing ones and are covered. #2/#5/#7/#8 (mutable defaults / validated constructors / resource leaks / deserialization) are implementation-side and belong to the dev's green phase.
**Self-check:** 0 vacuous tests — every test asserts an exact string, a specific fragment + its negation, or a named span with a specific attribute value. No `assert True`, no bare truthy `assert result`.

**Handoff:** To Hephaestus the Smith (Dev) for the green phase.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/pov_swap.py` (+64) — Facet 1. Pass 9b: bare `then <verb>` coordination (clause-local, `had_subject_swap`-gated, verb/pronoun-heuristic — leaves noun-governed verbs and NPC clauses alone). Pass 10: subject-auxiliary inversion (`does/has/is/was` before a swapped `you`) gated on a `?` in the clause so declarative object-`you` is untouched. Added an `origin` arg to `swap_to_second_person` and stamped it on the `narration.second_person_swap` span.
- `sidequest/server/emitters.py` (+59) — Facet 2. Added `origin: str = "live"` to `_apply_pov_swap` (threaded onto the skip/projected spans + the swap call). New `localize_replay_message(message, *, recipient_player_id, view, snapshot)` — re-applies the per-recipient POV swap to a rebuilt replay message via the shared `_apply_pov_swap` with `origin="replay"`; no-op for non-narration / no-anchor / recipient-absent.
- `sidequest/server/views.py` (+15) — wired `localize_replay_message` into `backfill_last_narration_block` (builds view/snapshot once, localizes each rebuilt message for the resuming player).
- `sidequest/handlers/connect.py` (+30/-2) — wired `localize_replay_message` into BOTH reconnect replay branches (cache-replay loop + legacy event-log fallback) via a shared `_localize_replay` closure; corrected the stale "byte-identical to what the live player received" cache comment.

**Tests:** GREEN.
- New: 16/16 pass (`test_pov_swap_158_38_verb_agreement.py` 13/13, `test_pov_swap_replay_158_38.py` 3/3) — verified by the `testing-runner` subagent (158-38-dev-green) and direct runs.
- No regression: existing `test_pov_swap.py` (80), `test_pov_swap_158_8_finding_pins.py` (8), `test_pov_swap_otel.py` (5), `test_narration_pov_emission.py` (42) all pass (154 total in the POV blast radius).
- Full `tests/agents/` serial: 2210 passed, 2 skipped.
- Full `tests/server/` serial: **zero new failures** vs the source-stashed baseline (empty `in-mine-not-in-baseline` diff). The ~60 pre-existing turn-pipeline/chargen-fixture failures are content-drift, unrelated to this story (see Delivery Findings).
- Lint clean (ruff); pyright adds zero new errors on the four changed files.

**Branch:** feat/158-38-pov-localizer-residuals (pushed; 2 commits — RED tests + GREEN fix)

**AC coverage:** AC-1 (verb-agreement) ✓; AC-2 (resume/replay swap + `origin='replay'` lie-detector span, applied at all three replay reconstruction sites) ✓; AC-3 (no regression — existing 158-8/158-14 suites green, no over-application) ✓.

**Handoff:** To Hermes Psychopompos (Reviewer) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells, 154 tests pass | N/A (confirmed clean) |
| 2 | reviewer-edge-hunter | Yes | findings | ~14 (1 high, 4 medium, rest low/self-resolved) | confirmed 0, dismissed 3, deferred 4 (non-blocking hardening) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 7 | reviewer-security | Yes | findings | 1 (_visibility replay leak) | confirmed 1 (Medium, pre-existing, deferred) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`, self-assessed by reviewer)
**Total findings:** 1 confirmed (Medium, pre-existing, deferred), 3 dismissed (with evidence), 6 deferred (non-blocking hardening/nits)

### Rule Compliance (python lang-review checklist + SOUL/CLAUDE rules)

Enumerated against every changed symbol in the diff:
- **#1 Silent exception swallowing** — COMPLIANT. No bare `except` / `except: pass` added. `_apply_pov_swap`'s skip paths each emit a `narration.pov_swap_skipped` OTEL span (now also stamped `origin`). `localize_replay_message`'s `model_validate` is intentionally **fail-loud** (no swallow) — consistent with the No Silent Fallbacks rule. (Edge-hunter suggested wrapping it in try/except-return-original; I REJECT that suggestion because it would BE a silent fallback, violating the rule — and the failure mode is unreachable since `swap_to_second_person` never returns empty on non-empty input, verified: `"Carl."`→`"You."`.)
- **#2 Mutable default arguments** — COMPLIANT. The only new default is `origin: str = "live"` (immutable). No list/dict/set defaults.
- **#3 Type annotations at boundaries** — COMPLIANT. `localize_replay_message(message: object, *, recipient_player_id: str, view: SessionGameStateView, snapshot: GameSnapshot) -> object`; `swap_to_second_person(..., origin: str = "live")`; nested subs annotated (`(m: re.Match) -> str`, `(msg: object) -> object`).
- **#4 Logging** — N/A. No new logging; error paths are fail-loud raises, not logged-and-swallowed.
- **#5 Path handling** — N/A. No path manipulation in the diff.
- **#6 Test quality** — COMPLIANT. The 16 new tests assert exact strings / fragment+negation / named-span-attribute; no `assert True`, no bare-truthy asserts, parametrized cases hit distinct irregular-aux paths (does/has/was). (test_analyzer disabled; self-verified.)
- **#7 Resource leaks** — N/A. No file/connection/lock handling.
- **#8 Unsafe deserialization** — COMPLIANT. `model_validate` is pydantic with `extra="forbid"`; no pickle/yaml.load/eval.
- **OTEL Observability (CLAUDE.md)** — COMPLIANT. Replay swap emits `narration.second_person_swap` with `origin='replay'`; skip/projected spans stamped with `origin` — the lie-detector can distinguish replay from live.
- **ADR-105 `_visibility` egress (`_visibility` must never reach the client)** — VIOLATION on the replay path, but PRE-EXISTING (not introduced by this diff; `localize_replay_message` is byte-neutral on `_visibility`). Confirmed Medium, deferred to a dedicated follow-up (Delivery Findings). Not dismissed.
- **No Source-Text Wiring Tests (CLAUDE.md)** — COMPLIANT. The replay wiring test drives the real production `backfill_last_narration_block`, not a source-grep.

### Observations

- [VERIFIED] Facet 1 verb-agreement is correct and bounded — evidence: `pov_swap.py` Pass 9b (`\bthen\s+(\w+)`) and Pass 10 (`\b(\w+)\s+(you|You)\b`) both reuse the `had_subject_swap`/`name_swap_occurred` clause-local gates and the `_looks_like_verb`/`_is_pronoun` guards; 13/13 verb tests pass including the 5 non-regression guards (noun-governed verb, NPC-clause, and-then/comma-then untouched). Complies with the No-over-application requirement (AC-3).
- [VERIFIED] Pass 10 capitalization is correct — evidence: `"Is Carl ready?"` → `"Are you ready?"` (lowercase `you`) and `"Are the gates open? Is Carl ready?"` → `"...Are you ready?"`. The inverted subject is never sentence-initial (the aux is), so Pass 2/3 yield lowercase `you` and `_conjugate` capitalizes only the sentence-initial aux.
- [VERIFIED] `localize_replay_message` no-op identity check is sound — evidence: `_apply_pov_swap` returns the SAME `payload_dict` object on every early-return (lines 299-348) and a fresh `{**payload_dict, "text": swapped}` only on the swap path; `swapped_dict is payload_dict` reliably detects the no-op. Footnotes/seq/visibility round-trip through `model_dump(by_alias=True)`→`model_validate` (verified for the success case).
- [VERIFIED] Data flow traced — resuming player input → reconnect → `read_narration_backfill`(player_id) / cache-replay loop → `_build_message_for_kind` → `localize_replay_message(recipient_player_id=resuming player)` → `_apply_pov_swap` targets `view.character_of(resuming player)` → 2nd-person prose only for the resumer's OWN PC. Recipient targeting is correct (confirmed by reviewer-security: `session._current_player_id` / `player_id` is the resuming player, never another).
- [VERIFIED] Zero regression — evidence: full `tests/server/` source-stashed baseline (62 fail) vs with-fix (60 fail), empty `in-mine-not-in-baseline` diff; 154 POV-blast-radius tests pass; `tests/agents/` serial 2210 pass.
- [SEC][RULE] `_visibility` sidecar reaches the reconnecting client on the replay path (CWE-200; ADR-105 egress rule) — CONFIRMED but PRE-EXISTING and byte-neutral to this diff; Medium severity (server metadata to an authorized viewer). Deferred to a replay-egress-strip follow-up (Delivery Findings).
- [EDGE] Pass 10 narrow over-fire windows (mid-clause `?`; `name_swap_occurred` vs `had_subject_swap`) — DEFERRED as optional hardening; no realistic prose reproduced an actual corruption (all probes left the irregular aux untouched). Cosmetic-only.
- [EDGE] Pass 9b double-pass after Pass 8/9 — DISMISSED: the `conjugated == word` no-op guard makes it safe (`_conjugate` is idempotent on already-base forms; verified `and then grip`/`, then fire` untouched).
- [EDGE] Pass 10 "Are You" capital claim (high) — DISMISSED with evidence (disproven above; the inverted subject is never sentence-initial).
- [SILENT] (subagent disabled — self-assessed) No swallowed errors introduced; `_apply_pov_swap` skip paths emit OTEL spans; `localize_replay_message` fail-loud by design. The connect/views None-guards return the message unchanged when no view/snapshot exists (consistent with the live path's snapshot-None no-op) — acceptable, not a silent error.
- [TEST] (subagent disabled — self-assessed) New tests assert real behavior (exact strings, span attributes), include the per-recipient non-anchor guard; gap: footnote round-trip through `localize_replay_message` is not directly pinned by a test (verified manually here) — non-blocking.
- [DOC] (subagent disabled — self-assessed) Comments are accurate; the stale `connect.py:1477` "byte-identical" comment was correctly updated by Dev. New passes carry clear docstrings.
- [TYPE] (subagent disabled — self-assessed) `origin: str` is a stringly-typed enum-ish param (acceptable for an OTEL attribute; values "live"/"replay"); `message: object` is appropriately broad for a replay-message wrapper, narrowed via `isinstance(message, BaseModel)`.
- [SIMPLE] (subagent disabled — self-assessed) No over-engineering; `localize_replay_message` is a thin reuse of `_apply_pov_swap`. The shared `_localize_replay` closure avoids duplicating the localization across the two connect branches.
- [RULE] ADR-105 `_visibility` egress violation (pre-existing) is the only rule finding — see [SEC] above.

### Devil's Advocate

Argue the code is broken. **Attack 1 — the `_visibility` leak is worse than "metadata."** A determined client on a multiplayer table reconnects and now reads `_visibility.visible_to` and `anchor_pc` on every replayed NARRATION. If a future story ships per-recipient *filtered* narration (visible_to a subset), the replay path would hand the reconnecting client the server's visibility decision for content it can see — and if `read_narration_backfill`'s `include=1` filter ever drifts, the sidecar would be the canary that leaked first. Counter: today narration is `visible_to:"all"` and the projection filter gates `include=1` before localization, so the recipient is authorized to the content; the leaked fields are not another player's secret. Still, it violates a stated rule — hence Confirmed+Deferred, not dismissed. **Attack 2 — Pass 10 corrupts real prose.** A narrator writes a rhetorical mid-clause question with the PC as object: "Carl steadies himself — does the void want you? — and steps." After swap the clause carries `?` and an object `you`; if an irregular aux landed immediately before `you`, Pass 10 would mis-conjugate it. I probed analogues ("does involve you?", parenthetical "(was it real?) ... watches you") and none mis-fired because the eligible aux never sat immediately before the object `you`. The window is real but I could not weaponize it into a visible defect, and the blast radius is one cosmetic word in narration (no mechanical state). **Attack 3 — replay crashes on a malformed payload.** `localize_replay_message` calls `model_validate` unguarded; a corrupt cache row with an extra key would raise and abort the reconnect replay. Counter: the dict comes from `model_dump(by_alias=True)` of a just-validated payload plus a single `text` substitution — no extra keys are introduced, and `extra="forbid"` would only bite on upstream corruption that would already have failed `_build_message_for_kind`. Failing loud here is correct per No Silent Fallbacks. **Attack 4 — footnotes vanish on swapped replay.** The localizer rebuilds the payload after fact-id minting; if `model_dump`/`model_validate` dropped footnotes, reconnect would silently lose discovery badges. I verified a populated `Footnote` survives the round-trip. **Conclusion:** the only attack that lands is the pre-existing `_visibility` leak, which this story does not introduce or worsen.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** resuming player's reconnect → `read_narration_backfill(player_id)` / cache-replay loop → `_build_message_for_kind` → `localize_replay_message(recipient_player_id = resuming player)` → `_apply_pov_swap` targets the resumer's OWN PC → 2nd-person prose only for that player (safe because recipient targeting uses the resuming player's id; perception `include=1` filtering runs before localization).

**Pattern observed:** shared-helper reuse — `localize_replay_message` wraps the live-path `_apply_pov_swap` with `origin="replay"`, wired into all three replay reconstruction sites (`views.backfill_last_narration_block` + both `connect.py` branches via the `_localize_replay` closure). Mirrors the live fan-out exactly. `sidequest/server/emitters.py:357` / `views.py:328` / `connect.py:1512`.

**Error handling:** fail-loud `model_validate` (No Silent Fallbacks compliant); `_apply_pov_swap` skip paths emit `narration.pov_swap_skipped` spans with `origin`; None view/snapshot guarded with a no-op return consistent with the live path. `emitters.py:411`.

**Dispatch tags:** [EDGE] Pass-10/9b edge windows — 3 dismissed (disproven), 4 deferred (cosmetic hardening). [SEC] `_visibility` replay leak — confirmed Medium, pre-existing, byte-neutral, deferred. [RULE] ADR-105 egress — same pre-existing finding. [SILENT] none introduced (fail-loud by design). [TEST] real assertions; footnote-round-trip coverage gap noted (non-blocking). [DOC] accurate, stale comment fixed. [TYPE] sound. [SIMPLE] thin reuse, no over-engineering.

**Severity summary:** no Critical/High introduced by this diff. The one confirmed finding (`_visibility` replay leak) is PRE-EXISTING, byte-neutral to this change, Medium severity, and deferred to a dedicated replay-egress-strip follow-up. AC-1/AC-2/AC-3 all met; 16/16 new tests green; zero regression.

**Handoff:** To Themis the Just (SM) for finish-story.