---
story_id: "126-37"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-37: [ENGINE] De-nativize Fate confrontation RESOLUTION — extend fate_conflict to the downstream dial guards (apply_beat suppression + advance_confrontation refusal + narration_apply beat-drop)

## Story Details
- **ID:** 126-37
- **Jira Key:** (none — sprint YAML only)
- **Workflow:** tdd
- **Stack Parent:** 126-30 (de-nativize SEATING)
- **Repos:** server (sidequest-server)
- **Points:** 3
- **Priority:** p2
- **Branch Strategy:** gitflow (feat/{STORY_ID}-{SLUG})
- **Branch:** feat/126-37-fate-conflict-downstream-dial-guards

## Story Context

This story extends the de-nativization of Fate confrontations from 126-30's **seating** phase to the **resolution** phases. Under the Fate Core binding (ADR-144), confrontations seated with `ruleset=='fate'` must use Fate mechanics exclusively — no native beat mechanics should apply downstream.

**Key files affected:**
- `sidequest/server/game/confrontation.py` — apply_beat() and advance_confrontation() functions
- `sidequest/server/game/narration_apply.py` — narrator beat-selection logic
- `sidequest/server/dispatch/fate_conflict.py` — may need new OTEL events

**Invariants:**
- Sealed-commit loop unchanged (ADR-129/151)
- NPC rolls stay server-side (126-7/126-8)
- No hybrid seating (Fate and native are mutually exclusive)

## Sm Assessment

**Scope confirmed.** This is the resolution-phase half of the Fate de-nativization that 126-30 started at seating. The title *is* the spec: three downstream dial guards keyed on `fate_conflict` — apply_beat suppression, advance_confrontation refusal, and narration_apply beat-drop. Server-only, 3pts, refactor, TDD.

**Workflow choice:** tdd (phased) — confirmed from YAML, not overridden. This touches live resolution paths (`confrontation.py`, `narration_apply.py`), so RED-first is the right discipline; the gates that suppress native mechanics must be pinned by failing tests before any code moves.

**Doctrine flag for downstream (ADR-143 + SOUL "Bind the Ruleset, Don't Balance It"):** native dial mechanics are *removed* from the Fate path, not tuned to coexist. If TEA/Dev catch themselves converting, gating, or balancing a native beat against Fate — stop. The test should assert native beats are *suppressed/dropped* under `ruleset=='fate'`, not that they produce a balanced outcome.

**Cross-ruleset guardrail:** every suppression test needs a WN/native counterpart proving native confrontations still fire native mechanics. This is the wiring test — without it we can't tell suppression from a global no-op.

**OTEL:** per the project observability principle, each suppression decision (beat suppressed, advance refused, beat dropped) must emit a watcher event so the GM panel can confirm the guard engaged rather than the narrator silently improvising. Flagged for Dev.

**Merge gate:** clear (no open PRs, nothing in progress). No stack-ready block — parent 126-30 already merged.

**Routing:** → TEA (Amos Burton) for RED.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Engine refactor touching three live resolution guards — RED-first per the SM routing; each guard needs a Fate-suppress test + a cross-ruleset native-keep pin (AC-4).

**Test Files:**
- `tests/game/test_126_37_apply_beat_fate_conflict.py` — guard #1: `beat_kinds.apply_beat` must short-circuit (no dial move, `skipped_reason` set, no deltas, no tags) + emit `beat_suppressed_fate_conflict`; cross-ruleset pin keeps the native dial advancing + `metric_advance`.
- `tests/agents/tools/test_126_37_advance_confrontation_fate_conflict.py` — guard #2: the `advance_confrontation` tool must refuse `win_condition=fate_conflict` (ERROR_RECOVERABLE, dial frozen, `tool.confrontation.refused_fate_conflict`), mirroring the `hp_depletion` guard; cross-ruleset pin keeps dial_threshold advancing.
- `tests/server/test_126_37_narration_apply_fate_conflict_beat_drop.py` — guard #3: `_apply_narration_result_to_snapshot` must DROP native beat selections for a Fate conflict (no `beat_applied`, dial frozen) + emit `conflict_beat_dropped_dial_blocked` (sibling of `contest_beat_dropped_dial_blocked`); cross-ruleset pin applies the beat on dial_threshold.

**Tests Written:** 8 tests (4 Fate-suppression + 4 cross-ruleset pins) covering AC-1, AC-2, AC-3, AC-4.
**Status:** RED confirmed (testing-runner 126-37-tea-red): 4 Fate-suppression tests FAIL on assertions, 4 pins PASS, zero collection/import errors.

**Established precedents each guard mirrors** (Dev: copy the shape, gate on `win_condition == "fate_conflict"`):
- apply_beat → `dial_suppressed_hp_depletion` block in `beat_kinds.py` (~line 625)
- advance_confrontation → `refused_hp_depletion` guard in `agents/tools/advance_confrontation.py` (~line 203)
- narration_apply → `contest_beat_dropped_dial_blocked` branch in `narration_apply.py` (~line 5915); the new guard keys on `enc.win_condition == "fate_conflict"` (a Fate conflict seats with `resolution_mode == beat_selection`, so it currently falls into the `else: _legacy_beat_path = True` arm).

**HOW-agnostic notes (for green-phase tightening, per the 126-30 workflow):** the three OTEL markers (`beat_suppressed_fate_conflict`, `tool.confrontation.refused_fate_conflict`, `conflict_beat_dropped_dial_blocked`) are the chosen GM-panel marker names; Dev may finalize the exact strings as long as each stays a distinct, `fate_conflict`-gated suppression/refusal/drop op. The hard RED assertions are behavioral (dials frozen, beat not applied) and survive renames.

### Rule Coverage

The Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) is a Dev self-review rubric; the one check that drives TEST design is #6 (test quality), enforced on my own tests:

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 no vacuous assertions | all 8 — assert specific values (metric `==0`/`==2`/`==4`, status enum, exact `op` strings, exact `beat_id`) | self-checked clean |
| #6 mock-patch where used | `monkeypatch.setattr(beat_kinds, "_watcher_publish")` + `(narration_apply, "_watcher_publish")` | patched at use-site |
| #6 no skips / distinct paths | no `@pytest.mark.skip`; each test exercises a distinct guard path (Fate vs dial cross-ruleset) | clean |
| Wiring test (CLAUDE.md) | all 3 files drive the REAL production functions (apply_beat, registered tool handler, `_apply_narration_result_to_snapshot`); OTEL-marker asserts prove the guard engaged | covered |
| OTEL Observability (CLAUDE.md / SM flag) | each guard asserts its suppression/refusal/drop event fires (lie-detector) | covered |

**Rules checked:** lang-review is Dev-side; #6 + the project's wiring/OTEL rules are the TEST-design-relevant rules and all have coverage.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement the three guards.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/beat_kinds.py` — guard #1 (belt): `apply_beat` short-circuits for `enc.win_condition == "fate_conflict"` alongside the existing `encounter_resolved`/`neutral_actor`/`withdrawn_actor` early returns — emits `beat_suppressed_fate_conflict`, returns `ApplyResult(deltas=None, skipped_reason="fate_conflict_suppressed")` before any delta/tag/resolution work.
- `sidequest/agents/tools/advance_confrontation.py` — guard #2: refuses `win_condition == "fate_conflict"` (mirrors the `hp_depletion` guard) → `ToolResult.error(recoverable=True)` + `tool.confrontation.refused_fate_conflict`.
- `sidequest/server/narration_apply.py` — guard #3 (suspenders): an `if enc.win_condition == "fate_conflict"` branch heads the resolution_mode dispatch chain (existing `sealed_letter_lookup` `if`→`elif`), drops the narrator's native beat selections + emits `conflict_beat_dropped_dial_blocked` (mirrors `contest_beat_dropped_dial_blocked`), sets `_legacy_beat_path = False`.

**Approach:** Minimal — each guard clones an established `win_condition`/`resolution_mode`-keyed precedent, gated on `fate_conflict`. No native mechanic tuned/converted (ADR-143/144: REMOVED from the Fate path). NPC resolution, the sealed-commit loop, and the UI were not touched (AC-3 invariants preserved). OTEL marker names match TEA's pinned strings exactly (no rename).

**Tests:** 8/8 new 126-37 tests GREEN; 55 precedent/neighbor tests GREEN (apply_beat hp_depletion, advance_confrontation, narration_apply wiring, 126-30 seating, hp_depletion). Ruff check + format clean on all three changed files. Re-verified GREEN after rebasing onto origin/develop (the 150-3 commit also touched narration_apply.py; auto-merged cleanly, guard #3 intact).
**Branch:** feat/126-37-fate-conflict-downstream-dial-guards (rebased onto origin/develop @ 33970ff4)

**Full-suite state (honest):** A full `uv run pytest` shows 88 pre-existing failures + 3 errors across ~34 files, ALL in the in-flight epic-108 WWN/WN-combat area (tests sending combat beats `committed_blow`/`strike`/… that 108-3 stripped). **None are 126-37 and none are my changes** (my guards are `fate_conflict`-gated; the failures are WN/hp_depletion paths) — they are red on `origin/develop` too (predate this branch's merge-base e93b4084). Filed as tech-debt **story 125-8** per Keith. One instance fixed here as a courtesy: `tests/genre/test_classes_yaml_loader.py` (synthetic classes.yaml hardcoded the stripped `[strike,brace,break_contact]` → `[]`, which the loader exempts for WN classes per 108-7).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review. Reviewer note: the 88 WWN-combat failures are out of 126-37 scope (tracked in 125-8) — review the 3 guards + the 8 story tests + the one stale-fixture fix.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: 55 passed/0 failed; lint clean; 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 4 (1 high-conf, 3 low) | confirmed 2 (LOW), deferred 2 (LOW notes) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 1 (LOW/doc), dismissed 1 (false positive) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 (LOW consistency note) | dismissed 1 (mirrors production precedent) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 3 confirmed (all LOW), 2 dismissed (with rationale), 2 deferred (LOW coverage notes)

## Reviewer Assessment

**Verdict:** APPROVED

The three `win_condition=='fate_conflict'` guards are correct, doctrine-compliant, fully tested, and GREEN. Zero Critical/High findings. The confirmed findings are all LOW-severity test/doc hygiene on tangential surfaces (a stale line-number in a test docstring; a missing one-line assertion on the *courtesy* stale-fix; minor coverage nits) — none touch the story's deliverable.

### Rule Compliance (exhaustive — 17 rules / 62 instances via rule-checker + my own read)

- **ADR-143/144 "Bind the Ruleset, Don't Balance It"** — COMPLIANT across all 3 guards. `beat_kinds.apply_beat` returns `ApplyResult(deltas=None, skipped_reason="fate_conflict_suppressed")` before any delta/tag/resolution work (REMOVED, not balanced). `advance_confrontation` returns `ToolResult.error` without reading/writing the dial (frozen, not tuned). `narration_apply` sets `_legacy_beat_path=False` so the apply_beat loop (line 6139) never runs (dropped, not applied). This is the load-bearing project rule and it is satisfied exactly.
- **No Silent Fallbacks / OTEL Observability** — COMPLIANT. Each guard emits a signal: `beat_suppressed_fate_conflict` (watcher), `tool.confrontation.refused_fate_conflict` (tool-registry span), `conflict_beat_dropped_dial_blocked` (watcher + logger.warning).
- **No Source-Text Wiring Tests** — COMPLIANT. All 3 test files drive the REAL production functions (apply_beat, registered tool handler, `_apply_narration_result_to_snapshot`); no `read_text()` source grep.
- **lang-review #1 silent-exceptions / #4 logging / #6 test-quality / #13 regressions** — COMPLIANT. No swallowed exceptions; `logger.warning` uses lazy `%r/%d` (not f-string), correct level for a recoverable drop; no vacuous assertions; monkeypatch patched-where-used; the `if→elif` conversion introduces no regression (verified mutually-exclusive seating below).
- **#2/#5/#7/#8/#9/#10/#11/#12** — N/A or compliant (no mutable defaults, no path/resource/deserialization/async/import/dependency surface in the diff).

### Observations

- `[VERIFIED]` **Dispatch-chain ordering is safe** — `encounter_lifecycle.py:1643` sets `seat_as_fate_conflict = is_fate and cdef.resolution_mode not in (contest, sealed_letter_lookup)`. So `win_condition=="fate_conflict"` is NEVER co-stamped with contest/sealed_letter resolution modes. The new `if enc.win_condition=="fate_conflict"` heading the chain (with sealed_letter `if`→`elif`) therefore cannot steal a contest/sealed-letter/table/opposed encounter — they are mutually exclusive by construction. Resolves preflight's one eyebrow.
- `[VERIFIED]` **`beat_kinds` guard placement** — `beat_kinds.py:594` fires after the `resolved/neutral/withdrawn` early returns and BEFORE `_normalize_overrides`/dial/tag work, so no native mechanic executes for a Fate conflict. Independent of the downstream `hp_depletion` dial-suppress (different win_condition). evidence: source 582-611.
- `[VERIFIED]` **`advance_confrontation` guard placement** — placed after the `hp_depletion` refusal and before `opposed_check`; `fate_conflict`/`hp_depletion`/`dial_threshold` are mutually-exclusive `win_condition` values, no overlap. Dial never touched (frozen). evidence: source 217-238.
- `[RULE][LOW] dismissed` — rule-checker flagged `advance_confrontation` using `ctx.otel_span.set_attribute` instead of `_watcher_publish` (cross-guard inconsistency). DISMISSED: it mirrors the in-production `refused_hp_depletion`/`refused_resolved`/`refused_opposed_check` guards in the same function exactly — the tool-registry span IS the GM-panel-visible channel for this tool. Consistency-with-precedent over cross-guard uniformity.
- `[DOC][LOW] confirmed` — `test_126_37_apply_beat_fate_conflict.py:10` docstring cites `narration_apply.py:6061` for the apply_beat call; line 6061 is now an unrelated arg and the real call is `narration_apply.py:6139` (shifted by this story's edits + the 150-3 rebase). Stale citation; CLAUDE.md discourages exact line numbers. Non-blocking — logged as a Delivery Finding.
- `[TEST][LOW] confirmed` — `tests/genre/test_classes_yaml_loader.py` (the courtesy stale-fix) sets `encounter_beat_choices: []` but no longer asserts the field, so the empty-list-exemption claim is unpinned. A one-liner (`assert all(c.encounter_beat_choices == [] for c in pack.classes)`) would close it. Non-blocking (the test's primary load-3-classes assertions still hold; this fix is outside 126-37's ACs). Logged as a Delivery Finding.
- `[TEST][LOW] dismissed` — comment-analyzer's "logger.warning fires on empty gated_selections" is a FALSE POSITIVE: the outer guard `narration_apply.py:5541` (`... and gated_selections`) requires a non-empty list to enter the block, so "dropped 0" cannot occur. The contest sibling's inner `if gated_selections:` is redundant defensiveness, not a required guard.
- `[TEST][LOW] deferred` — two coverage notes (advance_confrontation PIN uses `genre_pack=None` so the opposed_check guard stands down silently; the zero-selection narration path is unpinned but safe via the 5541 outer guard). Improvements, not gaps in the shipped behavior.

### Dispatch tags (disabled subagents assessed by Reviewer)

- `[EDGE]` (disabled) — Reviewer edge pass: empty-selection path (safe via outer guard), mutually-exclusive win_condition values (verified), `if→elif` boundary (verified no regression). No edge defects.
- `[SILENT]` (disabled) — Reviewer silent-failure pass: all 3 guards fail loud (error/drop + OTEL signal); no swallowed exceptions, no empty except, no silent fallback. Clean.
- `[TYPE]` (disabled) — no new types/signatures; guards are string comparisons on a validated `StructuredEncounter.win_condition` Literal. Clean.
- `[SEC]` (disabled) — no new input boundary; `win_condition` and `gated_selections` come from the already-validated snapshot. No injection/auth/secret surface. Clean.
- `[SIMPLE]` (disabled) — guards are minimal and clone established precedents; no over-engineering, no dead code. Clean.
- `[TEST]`, `[DOC]`, `[RULE]` — see Observations above (subagents enabled).

### Devil's Advocate

Assume this code is broken. Where would it bite? First attack: **the `if→elif` conversion**. If a Fate conflict could *also* carry `resolution_mode == sealed_letter_lookup` or `contest`, my new `if` would hijack it and drop legitimate sealed-letter/contest commits — silently breaking a dogfight or a Fate Contest. I chased this: `encounter_lifecycle.py:1643` proves `seat_as_fate_conflict` is explicitly `False` for contest and sealed_letter modes, so `win_condition=="fate_conflict"` and those modes are mutually exclusive at the only seating chokepoint. The attack fails — but it would succeed if a future story ever stamped `fate_conflict` on a contest/sealed seat, so this guard's safety is *coupled* to that seating invariant (noted for the seating story). Second attack: **a confused narrator on a Fate conflict** keeps emitting `beat_selection`s every turn. Result: each turn the drop branch fires, logs a warning, emits watcher events, and the conflict still resolves via FATE_ACTION — no dial movement, no crash, just GM-panel noise. Acceptable; the lie-detector is doing its job. Third attack: **a caller invokes `apply_beat` directly on a Fate conflict from some non-narration path** (a future subsystem). The belt catches it — early return, no mutation, suppression event. Good. Fourth attack: **the stressed-filesystem / malformed-state angle** — `enc.win_condition` is a validated Literal, `gated_selections` comes from the validated snapshot, so a garbage value can't reach the comparison; an unexpected `win_condition` simply doesn't match `"fate_conflict"` and falls through to existing behavior. Fifth: **does the `advance_confrontation` refusal strand a turn?** No — it returns `recoverable=True`, the narrator proceeds on prose, and the 4dF engine owns resolution. The one thing the devil *does* surface: the safety of guard #3 rests on the seating mutual-exclusivity invariant — if that ever changes, this guard needs a co-update. That's a forward-coupling note, not a current defect. Net: no Critical/High emerges.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T08:13:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T06:48:06Z | 2026-06-20T06:50:22Z | 2m 16s |
| red | 2026-06-20T06:50:22Z | 2026-06-20T07:06:17Z | 15m 55s |
| green | 2026-06-20T07:06:17Z | 2026-06-20T08:04:32Z | 58m 15s |
| review | 2026-06-20T08:04:32Z | 2026-06-20T08:13:10Z | 8m 38s |
| finish | 2026-06-20T08:13:10Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The narrator may still be OFFERED native `available_beats` in the prompt for a `fate_conflict` encounter — guard #3 drops any resulting selection at resolution time, so there's no mechanical leak, but suppressing the beat menu in the prompt-build for Fate conflicts would be a cheaper, cleaner complement (saves tokens, removes the temptation). Affects the narrator prompt-state builder (the `available_beats` selector section). Out of test scope for 126-37. *Found by Dev during implementation.*
- **Question** (non-blocking): Per AC-5, the full live-narrator pulp_noir/annees_folles Fate-conflict-to-harm-resolution e2e (asserting only `fate.*` spans, no `beat_selected`/`beat_applied`/`confrontation_advanced`) is deferred to sq-playtest per TEA's logged deviation — the three guards are each pinned at their real production entry point with deterministic fixtures. Recommend a sq-playtest pass confirms the composed live path. *Found by Dev during implementation.*

### TEA (test design)
- **Gap** (non-blocking): The story context's file paths are approximate — the three guards do NOT live at `sidequest/server/game/confrontation.py` (no such file). Real locations: guard #1 `sidequest/game/beat_kinds.py::apply_beat` (~line 556; mirror the `dial_suppressed_hp_depletion` block ~625), guard #2 `sidequest/agents/tools/advance_confrontation.py::advance_confrontation` (~line 147; mirror the `refused_hp_depletion` guard ~203), guard #3 `sidequest/server/narration_apply.py` (~line 5915, the `cdef.resolution_mode` dispatch chain; mirror the `contest_beat_dropped_dial_blocked` branch). *Found by TEA during test design.*
- **Improvement** (non-blocking): Guards #1 (apply_beat) and #3 (narration_apply drop) are belt-and-suspenders — on the narrator path the drop (#3) fires first so apply_beat is never reached for a Fate conflict, but the apply_beat short-circuit (#1) is still required as the belt for any other caller and is pinned directly by `test_apply_beat_suppressed_for_fate_conflict`. Implement BOTH; do not collapse #1 into #3. *Found by TEA during test design.*
- **Question** (non-blocking): `narration_apply.py:6466 _resolve_dial_threshold_and_phase` already early-returns for `win_condition != "dial_threshold"` (so it is inert for `fate_conflict` today) — no new guard needed there, but Dev should confirm no OTHER post-turn sweep advances a fate_conflict dial. *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): `tests/genre/test_classes_yaml_loader.py::test_classes_yaml_loads_entries` (the courtesy 108-3 stale-fix) sets `encounter_beat_choices: []` but asserts nothing about the field, so the empty-list-exemption claim the docstring makes is unpinned. Add `assert all(c.encounter_beat_choices == [] for c in pack.classes)`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `tests/game/test_126_37_apply_beat_fate_conflict.py:10` docstring cites `narration_apply.py:6061` for the apply_beat call, but the call is now at `narration_apply.py:6139` (shifted by this story + the 150-3 rebase). Fix the number or drop it (CLAUDE.md discourages exact line citations; prefer `~6139`). *Found by Reviewer during code review.*
- **Question** (non-blocking): guard #3's safety is coupled to the seating invariant `encounter_lifecycle.py:1643` (`seat_as_fate_conflict` excludes contest/sealed_letter). If a future story ever stamps `win_condition="fate_conflict"` on a contest/sealed-letter seat, the new `if`-heads-the-chain branch would hijack it — the seating story must co-update this guard. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

3 deviations

- **Guard #3 implemented as a resolution-time beat-DROP, not a prompt-time available_beats suppression**
  - Rationale: the story TITLE ("narration_apply beat-drop") and TEA's authoritative test (`test_narration_apply_drops_native_beats_for_fate_conflict`) both specify drop-at-resolution, which is higher authority than the context's Phase-3 prose (spec hierarchy: session scope + TEA tests > story context). Drop-at-resolution is also the robust placement: it mirrors the live `contest_beat_dropped_dial_blocked` precedent and defends against an LLM hallucinating a stray beat even when none is offered — exactly the lie-detector case. Prompt-side suppression alone could not catch that.
  - Severity: minor
  - Forward impact: the narrator may still be OFFERED native beats in the prompt for a Fate conflict (cosmetic waste, no mechanical effect — the drop guard neutralizes any selection). Logged as a non-blocking Improvement finding for a possible follow-up; out of test scope here.
- **AC-5 full pulp_noir e2e playtest scoped down to component-level OTEL assertions**
  - Rationale: a full Fate-conflict-to-harm-resolution e2e needs a live narrator (LLM) turn loop — non-hermetic, slow, flaky — which belongs to the sq-playtest harness (the 150-x ping-pong log referenced in context), not the deterministic pytest suite. Driving each guard's real production function with fixtures proves the de-nativization at the engine boundary, which is what the unit suite can verify.
  - Severity: minor
  - Forward impact: the live-path e2e (only-Fate-spans on a real pulp_noir conflict) remains a sq-playtest acceptance check, not a server unit test; Reviewer should confirm the three guards compose so a real conflict never reaches `apply_beat` on the narrator path.
- **apply_beat suppression pinned to a full short-circuit (skipped_reason + no deltas), not an hp_depletion-style partial dial-skip**
  - Rationale: ADR-143/144 doctrine ("REMOVED, not balanced") + the SM-assessment flag direct the test to assert full removal of the native beat under Fate, not a balanced/partial outcome. Pinning the short-circuit prevents a Dev from copying the hp_depletion partial-suppress shape, which would leave native tag/resolution side-effects on the Fate path.
  - Severity: minor
  - Forward impact: Dev must place the Fate-conflict guard as an early return alongside the existing `encounter_resolved` / `neutral_actor` / `withdrawn_actor` returns, emitting the suppression event before any delta computation.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Guard #3 implemented as a resolution-time beat-DROP, not a prompt-time available_beats suppression**
  - Spec source: context-story-126-37.md, Technical Approach Phase 3 ("Narration-Apply Beat-Drop")
  - Spec text: "When building the narrator prompt state (the section that instructs 'pick a beat from available_beats'), check if the active encounter is Fate-bound. If Fate: do NOT include the available_beats selector in the narrator prompt."
  - Implementation: the guard drops the narrator's native beat SELECTIONS in the `_apply_narration_result_to_snapshot` dispatch chain (an `if enc.win_condition == "fate_conflict"` branch that fires before the legacy `apply_beat` loop, emitting `conflict_beat_dropped_dial_blocked`), rather than removing the `available_beats` selector from the narrator PROMPT.
  - Rationale: the story TITLE ("narration_apply beat-drop") and TEA's authoritative test (`test_narration_apply_drops_native_beats_for_fate_conflict`) both specify drop-at-resolution, which is higher authority than the context's Phase-3 prose (spec hierarchy: session scope + TEA tests > story context). Drop-at-resolution is also the robust placement: it mirrors the live `contest_beat_dropped_dial_blocked` precedent and defends against an LLM hallucinating a stray beat even when none is offered — exactly the lie-detector case. Prompt-side suppression alone could not catch that.
  - Severity: minor
  - Forward impact: the narrator may still be OFFERED native beats in the prompt for a Fate conflict (cosmetic waste, no mechanical effect — the drop guard neutralizes any selection). Logged as a non-blocking Improvement finding for a possible follow-up; out of test scope here.

### TEA (test design)
- **AC-5 full pulp_noir e2e playtest scoped down to component-level OTEL assertions**
  - Spec source: context-story-126-37.md, AC-5
  - Spec text: "Verify end-to-end: drive a Fate conflict to harm resolution in pulp_noir/annees_folles; confirm OTEL spans show only Fate mechanics (fate.action_resolved, ...), NO native beat spans (beat_selected, beat_applied, confrontation_advanced)."
  - Implementation: Each of the three guards is exercised through its REAL production entry point with deterministic fixtures — `beat_kinds.apply_beat` (unit), the registered `advance_confrontation` tool handler (real registry dispatch), and `_apply_narration_result_to_snapshot` (real narration-apply pipeline with `synthetic_two_dial_pack`). Each asserts the native beat is suppressed/dropped (no `metric_advance` / `beat_applied`) and the Fate-suppression marker fires, plus a cross-ruleset (dial_threshold) pin. No live-narrator websocket pulp_noir session is spun up in the unit suite.
  - Rationale: a full Fate-conflict-to-harm-resolution e2e needs a live narrator (LLM) turn loop — non-hermetic, slow, flaky — which belongs to the sq-playtest harness (the 150-x ping-pong log referenced in context), not the deterministic pytest suite. Driving each guard's real production function with fixtures proves the de-nativization at the engine boundary, which is what the unit suite can verify.
  - Severity: minor
  - Forward impact: the live-path e2e (only-Fate-spans on a real pulp_noir conflict) remains a sq-playtest acceptance check, not a server unit test; Reviewer should confirm the three guards compose so a real conflict never reaches `apply_beat` on the narrator path.
- **apply_beat suppression pinned to a full short-circuit (skipped_reason + no deltas), not an hp_depletion-style partial dial-skip**
  - Spec source: context-story-126-37.md, Technical Approach Phase 1 + AC-3
  - Spec text: "If Fate: short-circuit apply_beat and return early (no native beat application)" / "The native dial/beat mechanics are REMOVED for Fate, not tuned to coexist."
  - Implementation: `test_apply_beat_suppressed_for_fate_conflict` asserts `result.skipped_reason is not None`, `result.deltas is None`, and no tags created — a total short-circuit, stronger than the `hp_depletion` path (which computes deltas then skips only the dial mutation while HP/resolution still run).
  - Rationale: ADR-143/144 doctrine ("REMOVED, not balanced") + the SM-assessment flag direct the test to assert full removal of the native beat under Fate, not a balanced/partial outcome. Pinning the short-circuit prevents a Dev from copying the hp_depletion partial-suppress shape, which would leave native tag/resolution side-effects on the Fate path.
  - Severity: minor
  - Forward impact: Dev must place the Fate-conflict guard as an early return alongside the existing `encounter_resolved` / `neutral_actor` / `withdrawn_actor` returns, emitting the suppression event before any delta computation.

### Reviewer (audit)
- **Dev — Guard #3 as resolution-time beat-DROP, not prompt-time suppression** → ✓ ACCEPTED by Reviewer: the story title ("narration_apply beat-drop") and TEA's authoritative test outrank the context's Phase-3 prose (spec hierarchy). Drop-at-resolution mirrors the live `contest_beat_dropped_dial_blocked` precedent and is the only placement that catches an LLM-hallucinated stray beat. Verified: implemented at `narration_apply.py:5564`, sets `_legacy_beat_path=False`, emits the watcher event. The prompt-side suppression remains a logged non-blocking Improvement — correct deferral.
- **TEA — AC-5 full pulp_noir e2e scoped down to component-level OTEL assertions** → ✓ ACCEPTED by Reviewer: a live-narrator e2e is non-hermetic and belongs to sq-playtest, not the unit suite. Each guard is exercised through its REAL production entry point with deterministic fixtures + cross-ruleset pins — that proves the de-nativization at the engine boundary, which is what pytest can verify. The live-path check is correctly deferred to sq-playtest (re-flagged by Dev as a non-blocking Question).
- **TEA — apply_beat suppression pinned to a full short-circuit (skipped_reason + no deltas), not an hp_depletion-style partial skip** → ✓ ACCEPTED by Reviewer: this is the doctrine-correct reading of ADR-143/144 ("REMOVED, not balanced"). Verified the impl matches: `beat_kinds.py:594` returns `ApplyResult(deltas=None, skipped_reason="fate_conflict_suppressed")` before any delta/tag/resolution work — stronger than the partial hp_depletion dial-skip, exactly as the test pins.
- **Reviewer audit — no UNDOCUMENTED deviations found.** The diff matches the story title and ACs; the three guards, their tests, and the one courtesy stale-fix are all accounted for in TEA/Dev deviations or this audit.