---
story_id: "158-42"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-42: Quest tracker: region quest marks completed before its objective is met; quest mint/complete emits no OTEL

## Story Details
- **ID:** 158-42
- **Jira Key:** (none)
- **Epic:** 158
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T18:21:18Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T17:41:00Z | 2026-06-27T17:42:38Z | 1m 38s |
| red | 2026-06-27T17:42:38Z | 2026-06-27T18:00:26Z | 17m 48s |
| green | 2026-06-27T18:00:26Z | 2026-06-27T18:08:03Z | 7m 37s |
| review | 2026-06-27T18:08:03Z | 2026-06-27T18:17:08Z | 9m 5s |
| green | 2026-06-27T18:17:08Z | 2026-06-27T18:19:52Z | 2m 44s |
| review | 2026-06-27T18:19:52Z | 2026-06-27T18:21:18Z | 1m 26s |
| finish | 2026-06-27T18:21:18Z | - | - |

## Sm Assessment

**Routing:** Phased TDD workflow on sidequest-server. Setup complete → handing to TEA (RED).

**Scope (2 pts, contained):** Two coupled defects in the quest subsystem, surfaced by the 2026-06-27 beneath_sunden playtest (Harpo):

1. **Premature completion (state bug).** Region-anchor quest `Below the Tended Rows — exp001.r0` flips `quest_log['dungeon:exp1'].status=completed` on region *entry*, with its objective ("find the seed-gallery … and the way down past it") unmet. Completion must gate on actual objective satisfaction, not arrival.
2. **Silent quest writes (observability gap).** Timeline rounds 1–5 carry zero `QUEST_*` events — both mint and completion are silent state writes, violating the OTEL principle ("the GM panel is the lie detector"). Quest mint and completion must emit watcher events.

**Boundaries:**
- UI↔store fidelity is confirmed correct (Quests tab matches `quest_log` exactly) — this is NOT a rendering bug. TEA should not write UI tests.
- Sibling 158-43 (authored quest never mints) is OUT OF SCOPE — separate story.

**Acceptance criteria for RED to cover:**
1. Quest does NOT transition to `completed` on region entry while objective unmet.
2. Quest mint emits an OTEL/watcher event; quest completion emits an OTEL/watcher event.
3. Regression guard: a quest whose objective IS satisfied still completes normally.

**Evidence:** Full repro + ground truth at `~/Projects/sq-playtest-pingpong.md`. Story context at `sprint/context/context-story-158-42.md`.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Two coupled state/observability defects in the expansion-quest subsystem — needs behavioral RED.

**Test Files:**
- `sidequest-server/tests/dungeon/test_expansion_quest_premature_complete.py` — 4 tests, driven through the REAL production seam (`seed_expansion_quest` + `make_expansion_quest_observer` wired via `notify_region_transition`).

**Tests Written:** 4 tests covering 3 ACs.
**Status:** RED (3 failed, 1 passed — verified via testing-runner, `uv run pytest -n0`).

- `test_entering_anchor_region_does_not_complete_reach_deep_quest_on_entry` → **FAIL** (AC-1): single-region expansion (anchor==entry); entering it flips the quest to `completed` (the beneath_sunden repro). Asserts it stays `active`.
- `test_quest_mint_emits_watcher_span` → **FAIL** (AC-2 mint): the projection into `quest_log` emits no `dungeon.quest.minted` span (only `frontier.region_transition` seen).
- `test_quest_mint_span_fires_once_not_on_idempotent_reprojection` → **FAIL** (AC-2 mint, idempotence): zero mint spans exist, so "exactly one" fails.
- `test_reach_deep_completes_on_genuine_descent_and_emits_resolved_span` → **PASS** (AC-3 regression + AC-2 completion + wiring): two-region descent still completes and fires `dungeon.quest.resolved`. Green guard the fix must preserve.

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|------|---------|--------|
| #6 test quality (meaningful assertions, no vacuous) | all 4 — assert concrete status strings / span names / `expansion_id` / counts | enforced |
| OTEL Observability Principle (CLAUDE.md) | mint-span ×2 (RED) + resolved-span (PASS) | failing/passing |

**Rules checked:** #6 is the only lang-review check that applies to RED test code; #1–#5, #7–#13 are GREEN-phase Dev-implementation concerns (the mint-span emit path must clear #1 silent-exceptions / #4 logging when authored). Flagged for Dev.
**Self-check:** 0 vacuous assertions found (every test asserts a specific value; the regression guard asserts completed-status + closed ledger thread + a named span with `expansion_id`).

**Handoff:** To Dev (Naomi Nagata) for implementation. The fix has a genuine design fork on the precise reach_deep exit condition — see the Question in Delivery Findings; the RED is HOW-agnostic so a faithful fix in either direction goes green.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/telemetry/spans/dungeon_quest.py` — new `dungeon.quest.minted` span (`SPAN_QUEST_MINTED` + `quest_minted_span` contextmanager + SPAN_ROUTES registration, `component=dungeon`), the player-visible-mint event between `bound` (seed) and `resolved` (complete).
- `sidequest-server/sidequest/dungeon/expansion_quest.py` — (1) `reconcile_dungeon_quests_into_log` fires `quest_minted_span` around the first projection of each quest into `quest_log`; (2) `resolve_expansion_quests` gains optional `skip_expansion_ids` (default empty); (3) `make_expansion_quest_observer` computes the expansions minted on the current transition and passes them as `skip_expansion_ids`, so a `reach_deep` beat cannot fire on the same step that mints the quest.

**Tests:** 4/4 new GREEN; 21/21 expansion-quest regression GREEN; 422/422 telemetry GREEN (447 total, 0 fail) — verified via testing-runner `uv run pytest -n0`.

**ACs:**
- AC-1 (no completion on entry): GREEN — observer skips resolving newly-minted quests; single-region (anchor==entry) repro stays `active`.
- AC-2 (mint + completion emit watcher events): GREEN — `dungeon.quest.minted` (new, on projection) + existing `dungeon.quest.resolved` (on completion), both routed to the GM panel.
- AC-3 (legitimate completion preserved): GREEN — two-region descent to the deeper anchor still completes + fires `dungeon.quest.resolved`; blessed e2e + direct resolve unit tests unchanged.

**Design fork (TEA Question) resolved:** chose interpretation (a) "don't resolve on the mint transition" over (b) "strictly deeper than anchor" — see Design Deviations. Lint + format clean (ruff).

**Branch:** feat/158-42-quest-premature-complete-otel (pushed)

**Handoff:** To verify/review.

### Dev rework — round 1 (review findings)
Addressed all 3 blocking Reviewer findings (all mechanical, no logic change):
- `ruff format` applied to the RED-phase test file (was committed unformatted) → `ruff format --check` now clean on all 3 changed files.
- `dungeon_quest.py` module docstring: "Two spans" → three (added `dungeon.quest.minted`).
- `resolve_expansion_quests` `skip_expansion_ids` docstring: reworded to state the skip is unconditional across signature kinds (motivating case `reach_deep`), matching the code.
- Bonus (non-blocking Reviewer Improvement): added a defensive-parse-guard comment on the observer's `except ValueError`.
Non-blocking test-tightening recommendations (idempotence self-transition, fuller span-attribute asserts, local-literal vs import) left for TEA — behavior is correct and covered.
Re-verified: 14/14 quest tests green; ruff format --check + ruff check clean. Pushed `f160bfe2`. No new design deviations.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format) | confirmed 1 (blocking), tests/lint/types clean |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 1 (non-blocking), deferred 4 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 2 (blocking-doc), dismissed 1, deferred 1 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 violation + 2 advisory | confirmed 0 blocking, deferred 3 |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed-blocking (1 format gate failure + 2 doc inaccuracies), 8 non-blocking/deferred, 1 dismissed

## Reviewer Assessment

**Verdict:** APPROVED (round 2 — after green rework `f160bfe2`)

**Round 2 re-review (2026-06-27):** All 3 round-1 blocking findings are resolved — `ruff format --check` clean on all 3 changed files, `ruff check` clean, `dungeon_quest.py` module docstring now lists "Three spans", and the `skip_expansion_ids` docstring now states the skip is unconditional across signature kinds. The rework was docstring/format/comment only — zero logic change — so the round-1 subagent findings stand: zero Critical/High, all remaining items non-blocking (Delivery Findings for TEA tightening). Tests green (quest + e2e + regression). **Data flow traced:** region transition → `notify_region_transition` → `make_expansion_quest_observer` → `reconcile_dungeon_quests_into_log` (mint span) + `resolve_expansion_quests(skip_expansion_ids=newly_minted)` → `quest_log[qid].status`; safe because a quest minted this transition is excluded from resolution, so it cannot self-complete on entry. **Pattern observed:** OTEL-span lie-detector wiring (`dungeon.quest.minted`/`.resolved`) + optional-param backward-compat at `expansion_quest.py`. **Error handling:** defensive parse-guard documented; no swallowed user-facing errors. **Handoff:** To SM (Camina Drummer) for finish-story.

---
**Round 1 verdict: REJECTED** (history preserved)

The fix is functionally correct — 447/447 tests green, all three ACs met, the observer-level gate is sound and minimal, and the design fork was resolved with documented rationale. But the branch **fails `ruff format --check`** on the test file (a hard merge/quality-gate blocker), and two docstrings now misdescribe the code. All are cheap, mechanical fixes; routing back to Dev (green rework). No Critical/High logic defects found.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW·blocking] | `ruff format --check` fails (3 hunks: two long `notify_region_transition(...)` lines + a list-comp). Will fail `just check-all` / CI / the finish gate. | `tests/dungeon/test_expansion_quest_premature_complete.py` | `uv run ruff format tests/dungeon/test_expansion_quest_premature_complete.py`, re-commit |
| [LOW·blocking] | `[DOC]` Module docstring says "Two spans" but there are now three (mint added). | `sidequest/telemetry/spans/dungeon_quest.py:2-11` | List all three; add `dungeon.quest.minted` (first projection into quest_log). |
| [LOW·blocking] | `[DOC]` `resolve_expansion_quests` `skip_expansion_ids` docstring says only "a reach_deep beat must NOT fire", but the guard at the `expansion_id in skip` check is unconditional across signature kinds. Code is correct; doc is narrower than behavior. | `sidequest/dungeon/expansion_quest.py` skip docstring | Reword: "no beat fires for a quest minted this transition" (or list all kinds). |

### Rule Compliance (python lang-review checklist, applied to the diff)

- **#1 Silent exceptions:** `except ValueError: continue` in the observer's `newly_minted_exp_ids` loop — `[VERIFIED]` narrow catch (ValueError only, not bare/Exception) on keys this same module produces (`_DUNGEON_QUEST_PREFIX` + `int(expansion_id)`), pre-filtered by `startswith`. Structurally unreachable; internal data, not user input. `[RULE]` rule-checker rated advisory under No-Silent-Fallbacks (a corrupt payload would silently skip the guard) — **deferred, non-blocking** (degenerate corrupt-state path; acceptable for game state). Recommend a comment noting it's a defensive parse-guard.
- **#2 Mutable defaults:** `[VERIFIED]` `skip_expansion_ids=None` (not `set()`), `signature_kind=""` — compliant.
- **#3 Type annotations:** `[VERIFIED]` `quest_minted_span` fully annotated (`-> Iterator[trace.Span]`); new `skip_expansion_ids: set[int] | None` annotated; test `# type: ignore[assignment]` carry specific codes.
- **#4 Logging / #5 Path / #8 Deserialize / #9 Async / #11 Input-validation / #12 Deps:** N/A — diff touches none (OTEL spans are the observability channel, internal game state only).
- **#6 Test quality:** `[TEST]` all assertions are specific value/count checks (no `assert True`, no unfiltered truthy). `assert minted` is pre-filtered by span name → meaningful existence check. One non-blocking weakness confirmed (idempotence self-transition, below).
- **#7 Resource leaks:** `[RULE]` `_store()` uses `sqlite3.connect(":memory:")` without a context manager — pattern match, but in-memory DB, GC-reclaimed at scope exit; **deferred, non-blocking** (mirrors the existing `test_expansion_quest_resolve.py::_store()` pattern, so consistent with the suite).
- **#10 Import hygiene:** `[VERIFIED]` explicit named imports, no star, no new cycle (`expansion_quest → dungeon_quest → _core/span`, no back-ref); `__all__` updated.
- **#13 Fix-regression meta:** `[VERIFIED]` `skip = skip_expansion_ids or set()` behaves correctly for None/empty/non-empty; no new bug class.

### Observations
- `[VERIFIED]` Premature-completion gate is correct: observer diffs `quest_log` keys around `reconcile` and skips newly-minted expansions in `resolve_expansion_quests` — single-region (anchor==entry) stays `active`, two-region descent still completes. Evidence: `expansion_quest.py` observer `before_ids`/`newly_minted_exp_ids` + the `if ... in skip: continue` guard; AC-1 and AC-3 tests both pass.
- `[VERIFIED]` Mint span wired end-to-end: `quest_minted_span` fires inside the `if existing is None:` projection branch only → idempotent (one span per first projection); registered in `SPAN_ROUTES` (`component=dungeon`) so the GM panel sees it. Evidence: `dungeon_quest.py` route + `reconcile` block; `test_quest_mint_emits_watcher_span` green.
- `[VERIFIED]` Backward-compat preserved: `skip_expansion_ids` defaults empty, so the per-turn handshake (`websocket_session_handler.py:1623`) and the direct-call unit tests in `test_expansion_quest_resolve.py` are unaffected — 21/21 regression green.
- `[TEST]` (non-blocking, confirmed) The idempotence test's second call is a self-transition `exp003.r0→exp003.r0`, which the production caller (`session.py` guards `to_region != prev`) never generates — so it doesn't exercise the real repeated-visit idempotency path (`r1→r0` return). The mint-once behavior IS correct and covered by the other tests; the test is weak, not wrong. Recommend TEA tighten to a genuine `r0→r1→r0`.
- `[TEST]` (non-blocking, deferred) Mint-span test asserts `expansion_id` but not `quest_id`/`signature_kind`; resolved-span test asserts `expansion_id` but not `resolving_event`. The route extracts all of them. Recommend pinning the full attribute set the GM panel routes on.
- `[TEST]` (non-blocking, deferred) `SPAN_QUEST_MINTED` is a local string literal in the test while `SPAN_QUEST_RESOLVED` is imported from production — a rename would silently diverge. Recommend importing from `dungeon_quest`.
- `[DOC]` (dismissed) Observer docstring item 3 names only `reach_deep` — pre-existing wording (not introduced by this diff; 158-17 already added big_bad to the prose). Out of scope; not a regression.

Subagent dispatch tags present: `[EDGE]` (disabled), `[SILENT]` (disabled), `[TEST]` confirmed, `[DOC]` confirmed, `[TYPE]` (disabled), `[SEC]` (disabled), `[SIMPLE]` (disabled), `[RULE]` deferred.

### Devil's Advocate
Argue this code is broken. The strongest case: the `except ValueError: continue` silently swallows a parse failure on an expansion-id key. Imagine a future change that stores a composite quest id (e.g. `dungeon:exp1.sub2`) — `int("1.sub2")` raises ValueError, the expansion is omitted from `newly_minted_exp_ids`, the skip-guard doesn't apply, and the very premature-completion bug this story fixes silently returns for that quest, with no log and no span to show the GM panel anything went wrong. That contradicts the OTEL "lie-detector" doctrine: a subsystem decision (skip-or-not) failed invisibly. Second angle: the skip logic keys on `quest_log` key *diffing*. If `reconcile` ever became non-idempotent or another observer mutated `quest_log` between `before_ids` capture and the diff, `newly_minted_exp_ids` would be wrong — but `reconcile` is the only writer in that window and is idempotent, so this is theoretical. Third: a multi-expansion jump (`exp1→exp5`) mints exp1..5 and skips all of them this transition; if a player legitimately *descended past* exp1's deep anchor in that jump, exp1's reach_deep won't fire on the jump and (per the chosen semantics) may never fire — but Dev already logged this single-region/jump-languish edge as a Question for Keith, so it's a known, documented limitation, not a hidden bug. Conclusion: no Critical/High emerges; the ValueError-swallow is the only item worth a defensive comment, and it's already deferred as advisory. The blocking issues remain mechanical (format + doc accuracy).

**Handoff:** Back to Dev (Naomi Nagata) for green rework — format the test file, fix the two docstrings. Re-verify `ruff format --check` clean + tests green, then re-hand to review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): the exact `reach_deep` "exit condition" ("the way down past it") is under-specified. Two viable fixes — (a) don't resolve a reach_deep quest on the same transition that mints it, or (b) resolve only when the PC reaches a region *strictly deeper* than the anchor/start. (b) changes the blessed e2e happy path (which completes on reaching the deeper anchor). Note a single-region expansion (anchor==entry) PROVES a seed-time anchor-selection-only fix is insufficient — the gate must be at resolve/observer time. Affects `sidequest/dungeon/expansion_quest.py` (`resolve_expansion_quests` / `make_expansion_quest_observer`) and possibly `tests/dungeon/test_expansion_quest_e2e.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the existing `tests/dungeon/test_expansion_quest_resolve.py::test_reach_deep_resolves_on_arrival` encodes resolve-on-arrival — correct for `resolve_expansion_quests` in isolation, but it reads as endorsing the bug. If Dev's gate lands inside that function, update it; if the gate lands in the observer, it stays green. Affects `tests/dungeon/test_expansion_quest_resolve.py`. *Found by TEA during test design.*
- **Gap** (non-blocking): sibling 158-43 (authored `the_unspent_hold` quest never mints from `pending_quest_offers`) is the other half of the playtest finding and is explicitly out of scope here. Affects the `record_quest`/quest_offer mint path. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): with the "reach the deepest chamber" semantics preserved, a *genuinely single-region* expansion's `reach_deep` quest never auto-completes by descent (no deeper chamber within it). If the intended UX is "complete when the player descends PAST the expansion into a deeper one," that needs a depth-aware resolve (`reached region depth_score > anchor depth_score`, plumbed into `resolve_expansion_quests`) — a larger change deferred here. Affects `sidequest/dungeon/expansion_quest.py`. Decision for Keith — adjacent to TEA's reach_deep Question. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): the test file fails `ruff format --check` (3 hunks) and will break `just check-all`/CI/the finish gate. Affects `tests/dungeon/test_expansion_quest_premature_complete.py` (run `uv run ruff format` and re-commit). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the idempotence test's second call is a self-transition (`exp003.r0→exp003.r0`) that the production caller never generates (it guards `to_region != prev`), so it doesn't exercise the real repeated-visit path; the resolved/mint span tests pin only `expansion_id`, not `resolving_event`/`quest_id`/`signature_kind`; and `SPAN_QUEST_MINTED` is a local literal vs imported. Affects `tests/dungeon/test_expansion_quest_premature_complete.py` (TEA tightening — non-blocking, behavior is correct & covered). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `except ValueError: continue` parse-guard in the observer silently skips a malformed `dungeon:expN` key — structurally unreachable today, but under No-Silent-Fallbacks a corrupt payload would invisibly drop the premature-completion guard for that expansion. Affects `sidequest/dungeon/expansion_quest.py` (add a defensive comment, or fail-loud). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (1 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** 1 BLOCKING items — see below

**BLOCKING:**
- **Gap:** the test file fails `ruff format --check` (3 hunks) and will break `just check-all`/CI/the finish gate. Affects `tests/dungeon/test_expansion_quest_premature_complete.py`.

- **Improvement:** the idempotence test's second call is a self-transition (`exp003.r0→exp003.r0`) that the production caller never generates (it guards `to_region != prev`), so it doesn't exercise the real repeated-visit path; the resolved/mint span tests pin only `expansion_id`, not `resolving_event`/`quest_id`/`signature_kind`; and `SPAN_QUEST_MINTED` is a local literal vs imported. Affects `tests/dungeon/test_expansion_quest_premature_complete.py`.
- **Improvement:** the `except ValueError: continue` parse-guard in the observer silently skips a malformed `dungeon:expN` key — structurally unreachable today, but under No-Silent-Fallbacks a corrupt payload would invisibly drop the premature-completion guard for that expansion. Affects `sidequest/dungeon/expansion_quest.py`.

### Downstream Effects

Cross-module impact: 3 findings across 2 modules

- **`tests/dungeon`** — 2 findings
- **`sidequest/dungeon`** — 1 finding

### Deviation Justifications

5 deviations

- **OTEL mint span name pinned as a TEA-chosen contract (`dungeon.quest.minted`)**
  - Rationale: a deterministic span assertion needs one concrete name; the bound/resolved family is the natural GM-panel-routed home. Per the 126-30/126-37 doctrine, pin concrete + invite Dev to finalize.
  - Severity: minor
  - Forward impact: if Dev renames, update the two mint-span assertions in `tests/dungeon/test_expansion_quest_premature_complete.py`.
- **Completion-side OTEL (AC-2) covered by the EXISTING `dungeon.quest.resolved` span, not re-authored**
  - Rationale: Don't-Reinvent / No-Stubbing — the resolved span is live and routed; duplicating it is dead work.
  - Severity: minor
  - Forward impact: none.
- **reach_deep AC-3 regression pinned to the existing e2e "complete on reaching the deeper anchor" contract**
  - Rationale: over-pinning one mechanism would falsely-fail a faithful fix; aligning with the existing e2e keeps the contract consistent.
  - Severity: minor
  - Forward impact: if Dev adopts "strictly deeper than anchor" semantics, both this test and `test_expansion_quest_e2e.py` need conscious updates.
- **reach_deep premature-completion fix: chose "skip resolution on the mint transition" (TEA Question interpretation a), not "strictly deeper than anchor" (b)**
  - Rationale: minimal and satisfies every test, incl. the two-region regression and the blessed e2e (which complete on reaching the deeper anchor). Interpretation (b) was rejected — it breaks that blessed "reach the deepest chamber = complete" contract and the observer has no reached-region depth lookup to implement it cleanly.
  - Severity: minor
  - Forward impact: a genuinely single-region expansion's `reach_deep` quest stays `active` until a later transition re-reaches its anchor (it has no deeper chamber within it to descend to). "Complete on descending PAST the expansion" would need a depth-aware resolve — flagged as a Delivery Finding for Keith's call.
- **Mint span name honored TEA's `dungeon.quest.minted` contract**
  - Rationale: the bound/resolved family is the natural GM-panel-routed home; no reason to diverge from the TEA contract.
  - Severity: minor
  - Forward impact: none.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **OTEL mint span name pinned as a TEA-chosen contract (`dungeon.quest.minted`)**
  - Spec source: context-story-158-42.md, AC-2
  - Spec text: "Quest mint and completion each emit a watcher event (e.g. quest.minted / quest.completed) … asserted via OTEL span, not a source-grep."
  - Implementation: tests assert a span named `dungeon.quest.minted` on the projection path (mirrors the existing `dungeon.quest.bound`/`dungeon.quest.resolved` family + SPAN_ROUTES home). The AC says "e.g.", so the exact name is TEA-chosen.
  - Rationale: a deterministic span assertion needs one concrete name; the bound/resolved family is the natural GM-panel-routed home. Per the 126-30/126-37 doctrine, pin concrete + invite Dev to finalize.
  - Severity: minor
  - Forward impact: if Dev renames, update the two mint-span assertions in `tests/dungeon/test_expansion_quest_premature_complete.py`.
- **Completion-side OTEL (AC-2) covered by the EXISTING `dungeon.quest.resolved` span, not re-authored**
  - Spec source: context-story-158-42.md, AC-2
  - Spec text: "Quest mint and completion each emit a watcher event."
  - Implementation: the completion span already fires through `resolve_expansion_quests`; I assert it once on a legitimate two-region descent rather than authoring a new completion span. Only the MINT span is net-new RED.
  - Rationale: Don't-Reinvent / No-Stubbing — the resolved span is live and routed; duplicating it is dead work.
  - Severity: minor
  - Forward impact: none.
- **reach_deep AC-3 regression pinned to the existing e2e "complete on reaching the deeper anchor" contract**
  - Spec source: context-story-158-42.md, AC-1 / AC-3
  - Spec text: "it completes only when its objective's real exit condition (e.g. 'the way down past it') is met" / "a quest whose objective IS satisfied still transitions to completed."
  - Implementation: the premature-completion RED is HOW-agnostic ("not completed on entry"); the AC-3 regression asserts completion on reaching the genuinely deeper anchor region (matching `test_expansion_quest_e2e.py`). The precise "deeper-than-anchor vs not-on-mint-transition" rule is left to Dev (see Delivery Finding Question).
  - Rationale: over-pinning one mechanism would falsely-fail a faithful fix; aligning with the existing e2e keeps the contract consistent.
  - Severity: minor
  - Forward impact: if Dev adopts "strictly deeper than anchor" semantics, both this test and `test_expansion_quest_e2e.py` need conscious updates.

### Dev (implementation)
- **reach_deep premature-completion fix: chose "skip resolution on the mint transition" (TEA Question interpretation a), not "strictly deeper than anchor" (b)**
  - Spec source: context-story-158-42.md AC-1/AC-3 + TEA Delivery-Findings Question
  - Spec text: "it completes only when its objective's real exit condition (e.g. 'the way down past it') is met" — TEA flagged the exact rule as a fork (a vs b).
  - Implementation: the observer diffs `quest_log` keys around `reconcile_dungeon_quests_into_log` to find quests minted this transition and passes them as `skip_expansion_ids` to `resolve_expansion_quests`; a `reach_deep` beat cannot fire on the step that first projects the quest.
  - Rationale: minimal and satisfies every test, incl. the two-region regression and the blessed e2e (which complete on reaching the deeper anchor). Interpretation (b) was rejected — it breaks that blessed "reach the deepest chamber = complete" contract and the observer has no reached-region depth lookup to implement it cleanly.
  - Severity: minor
  - Forward impact: a genuinely single-region expansion's `reach_deep` quest stays `active` until a later transition re-reaches its anchor (it has no deeper chamber within it to descend to). "Complete on descending PAST the expansion" would need a depth-aware resolve — flagged as a Delivery Finding for Keith's call.
- **Mint span name honored TEA's `dungeon.quest.minted` contract**
  - Spec source: TEA Design Deviation (OTEL mint span name), context-story-158-42.md AC-2
  - Spec text: "tests assert a span named `dungeon.quest.minted` … the AC says 'e.g.', so the exact name is TEA-chosen."
  - Implementation: implemented exactly `dungeon.quest.minted` (no rename), registered in SPAN_ROUTES alongside `dungeon.quest.bound`/`.resolved` (`component=dungeon`, `op=quest_minted`).
  - Rationale: the bound/resolved family is the natural GM-panel-routed home; no reason to diverge from the TEA contract.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA: OTEL mint span name `dungeon.quest.minted` (TEA-chosen contract)** → ✓ ACCEPTED: consistent with the existing `dungeon.quest.bound`/`.resolved` family and SPAN_ROUTES routing; Dev implemented it verbatim.
- **TEA: completion-side OTEL reuses existing `dungeon.quest.resolved`, only mint is net-new** → ✓ ACCEPTED: correct application of Don't-Reinvent; the resolved span already fires + routes (verified in `dungeon_quest.py` + e2e).
- **TEA: AC-3 regression pinned to the existing e2e "complete on reaching the deeper anchor" contract** → ✓ ACCEPTED: keeps the blessed `test_expansion_quest_e2e.py` contract intact; the HOW-agnostic premature assertion is the right call given the fork.
- **Dev: chose interpretation (a) "skip resolution on the mint transition" over (b) "strictly deeper than anchor"** → ✓ ACCEPTED: (a) satisfies every test incl. the two-region regression and the direct resolve unit tests; (b) would break the blessed e2e and needs depth plumbing the observer lacks. Minimal and correct. The single-region/jump languish edge is documented as a Question for Keith — appropriate (not silently chosen).
- **Dev: mint span name honored TEA's `dungeon.quest.minted` contract (no rename)** → ✓ ACCEPTED: honoring the TEA contract is the right move; no divergence.
- No undocumented deviations found. NOTE for the green rework: the `skip_expansion_ids` docstring describes the skip as `reach_deep`-specific while the code skips all signature kinds for newly-minted expansions — this is a doc/code mismatch (flagged in the Reviewer Assessment severity table), not an unlogged behavioral deviation.