---
story_id: "158-27"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-27: Orbital course/clock dispatch is inert in play — clear course intent leaves plotted_course=null + clock_t_hours frozen despite 153-5 wiring (SWN-ORBITAL-COURSE-INERT)

## Story Details
- **ID:** 158-27
- **Jira Key:** (none — Jira integration not configured)
- **Workflow:** tdd (phased)
- **Stack Parent:** none
- **Repo:** sidequest-server
- **Branch:** feat/158-27-orbital-course-inert
- **Type:** bug
- **Points:** 3
- **Priority:** p2

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-25T18:59:07Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-25T18:32:58Z | 2026-06-25T18:34:31Z | 1m 33s |
| red | 2026-06-25T18:34:31Z | 2026-06-25T18:46:05Z | 11m 34s |
| green | 2026-06-25T18:46:05Z | 2026-06-25T18:52:58Z | 6m 53s |
| review | 2026-06-25T18:52:58Z | 2026-06-25T18:59:07Z | 6m 9s |
| finish | 2026-06-25T18:59:07Z | - | - |

## Sm Assessment

### Problem Summary

Playtest finding (pingpong 2026-06-25, coyote_star SWN). A clear course intent ('plot a course to the Broken Drift, lay in the burn') leaves `plotted_course` null. The IntentRouter DOES classify+dispatch the course intent (153-5 #1026 wired it), but the engagement EFFECT does not land.

UPDATE (cont.2 session): `clock_t_hours` DID advance 0.0→1.0 across the session (generic per-turn/beat advance), so the clock primitive is NOT frozen — the gap is specifically the COURSE half: `plotted_course` stays null, no Hohmann transit engaged (ADR-130).

### Root Cause

The intent router successfully classifies course-of-action intents (e.g., 'plot a course to X') via 153-5 wiring, but when the `dispatch_engagement` dispatcher runs the effect for the `course` subsystem, it fails to write `plotted_course` to the game state. The orbital subsystem (`sidequest-server/sidequest/orbital/`) is where the course model and Hohmann transit engine live.

The clock subsystem (generic per-turn/beat advance) is working correctly, so the issue is isolated to the COURSE engagement effect. The story explicitly depends on 158-26 (dispatch_engagement watcher fix) to verify the course mismatch is visible on the GM panel.

### Technical Approach

1. **Identify the course engagement effect**: Locate the dispatch handler that runs when an `intent_kind==course` event fires; this is the executor that should write `plotted_course` to the snapshot.
2. **Verify the engagement runs**: Check dispatch logs / OTEL spans to confirm the course effect is being invoked (not skipped or ignored).
3. **Write plotted_course on effect execution**: Ensure the effect handler correctly extracts course metadata from the intent (destination region/coordinates) and writes a `PlottedCourse` object to `game_state.orbital.plotted_course`.
4. **Engage Hohmann transit**: Upon writing `plotted_course`, compute and store the approximate transit time/fuel delta per ADR-130's Hohmann transit model (beat-driven time advance).
5. **Verify via OTEL**: The `dispatch_engagement` watcher (once 158-26 lands) should emit the `dispatch_engagement.course.matched` span when the effect succeeds, and `dispatch_engagement.course.mismatch` if the effect fails to land.

### Acceptance Criteria

- After a player submits a course-of-action intent (e.g., 'plot a course to the Broken Drift, lay in the burn'), `game_state.orbital.plotted_course` is populated with the destination and bearing.
- A Hohmann transit is engaged, with the transit time computed and stored in the state (ADR-130 beat-driven model).
- The `dispatch_engagement.course.matched` OTEL span fires on successful course dispatch, confirming the effect ran to completion.
- Manual playtest on coyote_star SWN session verifies course intent lands, plotted_course is visible on the GM panel, and transit begins.

## TEA Assessment

**Tests Required:** Yes
**Test Files:**
- `sidequest-server/tests/agents/subsystems/test_course_destination_label_resolution.py` — course destination label/case/article resolution, driven through the REAL `run_dispatch_bank` (wiring-honest, never a source grep).

**Tests Written:** 7 (5 new-behavior + 2 guards) covering the 4 ACs below.
**Status:** RED — verified with `pytest -n0`: **5 failed, 2 passed**. The 5 failures fire for the right reason (a label destination is rejected as `unknown_destination` → `course.plot.rejected`, `plotted_course` stays null). The 2 passes are intentional guards, not vacuous: the canonical-id regression guard and the No-Silent-Fallbacks loud-reject invariant already hold and must keep holding. The existing 153-5 suite (`test_course_clock_dispatch_wiring.py`) is fully green (9 passed).

### Refined Root Cause — corrects the SM hypothesis (read this first, White Rabbit)

The SM Root Cause above ("the effect handler … **fails to write** `plotted_course`") is **imprecise and will send you to the wrong line.** I traced the whole path:

- `run_course_dispatch` (`sidequest/agents/subsystems/course.py`) **does** write `snapshot.plotted_course = course` (line ~105) and **does** advance the clock by the TRAVEL beat (line ~119) — *when it reaches them.*
- The subsystem **is** registered in the bank (`__init__.py:_register_defaults` → `("course", run_course_dispatch)`), the bank **does** thread `orbital_content` into the handler, the production caller (`websocket_session_handler.py:1005`) **does** pass `_session.orbital_content`, and `party_body_id` **is** bound on connect (`bind_region_scope("far_landing","init")` — coyote_star's `cartography.starting_region: far_landing` is a real body). All of that is green and proven by the 153-5 suite.

**The actual gap is destination resolution, one step *before* the write.** Line ~81 does a bare exact-key lookup: `dest_body = bodies.get(destination)`. But the IntentRouter is an LLM: a player who says *"plot a course to the Broken Drift"* yields `destination` carrying the **human label / phrasing** — `"Broken Drift"` / `"BROKEN DRIFT"` / `"the Broken Drift"` — never the internal snake_case id `broken_drift` (coyote_star `orbits.yaml`: `broken_drift:` with `label: "BROKEN DRIFT"`). The exact lookup misses → `unknown_destination` → `course.plot.rejected` → `plotted_course` stays null, and the clock only moves on the generic per-turn beat. The 153-5 suite hid this because every dispatch it builds names the canonical id directly (`destination="red_prospect"`).

### The Fix (GREEN) — where to put it

Resolve `destination` to a canonical body id **before** `bodies.get`, in `course.py`'s `run_course_dispatch`. Match, in order: (1) exact id, (2) case-insensitive id, (3) case-insensitive match against each body's `label`, tolerating a leading article (`"the "`). On success, construct `PlottedCourse(to_body_id=<canonical id>, …)` — the **canonical id**, never the echoed label (the id is what joins `party_body_id` on arrival and feeds the 158-26 watcher). On no match across id *and* labels, keep the existing LOUD `course.plot.rejected` (No Silent Fallbacks). Reuse helpers if any exist in `orbital/` — there are none today, so a small local resolver in `course.py` is the contained fix (Don't Reinvent does not apply; nothing to reuse).

**OTEL note (recommended, not test-gated):** the accept/reject spans already exist, so the OTEL gate is satisfied. Consider recording *how* it resolved (e.g. a `resolved_via=exact_id|label|article` attribute on the `course.plot` span) so the GM panel can see the resolution path — small touch, aligns with the OTEL lie-detector principle. I deliberately did **not** hard-assert the attribute name in a test to avoid over-coupling the implementation.

### Acceptance Criteria (TEA-defined; the sprint YAML had none)

1. A course dispatch whose `destination` is a body's **label** (e.g. `"RED PROSPECT"`) resolves to that body, commits a `PlottedCourse` with `to_body_id` == the **canonical id**, fires `course.plot`, does **not** fire `course.plot.rejected`, and advances `clock_t_hours` by the computed travel ETA.
2. Label resolution is **case- and leading-article tolerant**: `"RED PROSPECT"`, `"Red Prospect"`, `"red prospect"`, and `"the Red Prospect"` all resolve to the same body. (The article case is the literal playtest phrasing — *"the Broken Drift"*.)
3. **Regression:** a canonical body id (`"red_prospect"`) still plots and advances the clock (the 153-5 path is not broken).
4. **No Silent Fallbacks:** a destination matching neither any body id nor any label still emits `course.plot.rejected`, plots no phantom course, and moves neither clock nor party.

### Rule Coverage

| Rule (SOUL / CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks — tolerance must not become a fuzzy guess; unknown still fails LOUD | `test_course_unknown_destination_still_rejects_loud` | passing (guard) |
| Wiring proven by behavior + OTEL spans, never source grep | all 5 drive the REAL `run_dispatch_bank` + assert `course.plot` / `course.plot.rejected` | 5 failing |
| The Zork Problem — natural-language destination, not a keyword/id | label/case/article cases | failing |
| Don't break existing coverage (153-5 canonical-id path) | `test_course_canonical_body_id_still_resolves` | passing (guard) |

**Rules checked:** 4 of 4 applicable. **Self-check:** 0 vacuous tests — every test asserts on `plotted_course.to_body_id`, span presence/absence, and/or clock advance; the 2 passing guards assert real invariants, not always-true conditions.

**Handoff:** To Dev (the White Rabbit) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/agents/subsystems/course.py` — added `_normalize_destination` + `_resolve_body_id` helpers; `run_course_dispatch` now resolves `destination` to a canonical body id (exact id → normalized id → case/article-tolerant label) **before** plotting, commits the canonical id as `PlottedCourse.to_body_id`, and threads `resolved_via` to the accepted span. Unknown destinations still reject LOUD. Module docstring updated for 158-27.
- `sidequest-server/sidequest/telemetry/spans/course.py` — `emit_course_plot_accepted` gains an optional `resolved_via` attribute (`exact_id|normalized_id|label`) on the `course.plot` span (GM-panel observability per the OTEL principle + TEA's recommendation). Backward-compatible — the other caller (`narration_apply.py`) is unaffected.

**Tests:** 16/16 passing (GREEN) — 7 new (`test_course_destination_label_resolution.py`) + 9 existing 153-5 wiring (`test_course_clock_dispatch_wiring.py`). Broader sweep (`tests/orbital`, `tests/agents/subsystems`, `tests/handlers/test_course_intent_wired.py`, `tests/integration/test_orbital_e2e.py`): **662 passed**. `ruff check` + `ruff format --check` clean; `pyright` 0 errors on the changed files.

**Branch:** feat/158-27-orbital-course-inert (pushed)

### Implementation Notes
- Root cause confirmed exactly as TEA traced it: the bare `bodies.get(destination)` exact-match rejected the LLM-emitted human label. The fix is the contained resolver TEA specified — the (already-correct) write and clock-advance are untouched, and no wiring changed.
- `_resolve_body_id` is most-specific-first (exact id → normalized id → label) so a real id never loses to a coincidental label collision. `_normalize_destination` folds case, underscores, a leading `"the "`, and whitespace, mapping the player's phrasing, the snake_case id, and the authored label onto one comparable form.
- Every resolution-derived consumer now uses the canonical id: `PlottedCourse.to_body_id`, the quest-anchor `source` check, the TRAVEL beat `trigger`, and the `SubsystemOutput` `to_body`.
- TEA AC #4 (manual coyote_star playtest — "plotted_course visible on the GM panel, transit begins") is a live-session check, not reproducible in the unit suite; deferred to Reviewer/SM. The unit + e2e coverage proves the engine engages on a label burn; the 158-26 watcher is what surfaces it on the panel.

**Handoff:** To next phase (verify/review per the marker).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (all gates GREEN) | 0 issues, 6 observations | N/A — corroborates assessment |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings; edges assessed by Reviewer ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings; silent-fallback assessed by Reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings; test quality assessed by Reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings; docs assessed by Reviewer ([DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings; types assessed by Reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | clean | 0 findings | N/A — confirmed clean |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings; complexity assessed by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings; rules assessed by Reviewer ([RULE] + Rule Compliance) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents`, pre-filled as Skipped and assessed by Reviewer)
**Total findings:** 0 confirmed blocking, 0 dismissed, 3 LOW observations noted (non-blocking)

## Reviewer Assessment

**Verdict:** APPROVED

**Summary.** A surgical, correct fix for the inert-burn playtest finding. `run_course_dispatch` resolved the dispatched `destination` with a bare exact-key lookup (`bodies.get`); since the IntentRouter is an LLM, the player's "the Broken Drift" arrives as the human label/phrasing, not the snake_case id `broken_drift`, so the burn was rejected as `unknown_destination` and `plotted_course` stayed null. The new `_resolve_body_id` (exact id → normalized id → label, all via a single `_normalize_destination` fold) maps the human destination to the canonical id before plotting, commits the **canonical** id, and still fails LOUD on a genuine miss. Both enabled specialists returned clean/GREEN; my independent trace agrees.

**Data flow traced:** `dispatch.params["destination"]` (LLM-/player-originated) → `_resolve_body_id` → `resolved_id` → `bodies[resolved_id]` / `compute_eta_and_dv` / `PlottedCourse.to_body_id` / TRAVEL beat `trigger` / `SubsystemOutput.to_body`. Safe: the string reaches only `str` methods and dict-key equality — no SQL/eval/subprocess/regex/path sink (confirmed by [SEC]). A miss returns `(None, None)` → `course.plot.rejected` → early return (no phantom course).

**Pattern observed:** symmetric normalization — the same `_normalize_destination` fold is applied to the destination, the body id, AND the label, so all three meet on one comparable form (`course.py` `_resolve_body_id`). This is the right shape for natural-language resolution (the Zork Problem) and keeps the article-stripping consistent on both sides.

**Error handling:** top-of-function guards (`malformed_destination`, `no_orbital_tier`, `no_party_anchor`) are unchanged; the new resolver adds an empty-target guard (`if not target: return None, None`) so `"the "` / whitespace cannot silently match; a true miss preserves the loud `course.plot.rejected` (`course.py` resolution block).

### Observations (9; all 8 dispatch tags covered)

1. `[VERIFIED]` **No Silent Fallbacks preserved** — `_resolve_body_id` returns `(None, None)` on miss → `run_course_dispatch` emits `course.plot.rejected` and returns early; empty/whitespace/`"the "` folds to `""` → guarded. Complies with CLAUDE.md "No Silent Fallbacks." Corroborated by [SILENT]/[SEC].
2. `[SEC]` **Security clean** (reviewer-security, status: clean, 0 findings) — destination reaches only `.lower/.replace/.split/.startswith` + dict equality; `resolved_via` is one of three hard-coded literals (no PII); `available_ids` in the rejected span is authored world data, not secrets, and that path is unchanged by this diff.
3. `[VERIFIED]` **Canonical-id consistency** — `resolved_id` flows to `bodies[resolved_id]`, the quest-anchor `source` check, `PlottedCourse.to_body_id`, the beat `trigger`, and `SubsystemOutput.to_body`. No echoed label leaks into persistent state. Preflight independently noted the quest_anchors move (`destination` → `resolved_id`) *fixed a latent bug* — a label-resolved burn would otherwise mis-classify QUEST_OBJECTIVE provenance.
4. `[EDGE]` (edge-hunter disabled — Reviewer) **Loop ordering** — `_resolve_body_id` checks each body's normalized id then label in one interleaved pass. Under a *cross-body* collision (body A normalized-id == target AND body B label == target), the earlier-iterated body wins. I enumerated all 21 coyote_star bodies: the only id↔label coincidences (`the_counter`/"THE COUNTER", `last_drift`/"Last Drift") are **same-body** — no cross-body collision exists. LOW, non-blocking; both preflight and security flagged and dismissed the same line.
5. `[TYPE]` (type-design disabled — Reviewer) **Loose `Mapping[str, object]`** on `_resolve_body_id` avoids a runtime `BodyDef` import; `.label` is read via `getattr(..., None)` + `isinstance(label, str)` (defensive, pyright-clean). Could be `Mapping[str, BodyDef]` under TYPE_CHECKING for static typing, but the current form is safe and handles label-less bodies (e.g. `turning_hub`). LOW, acceptable.
6. `[TEST]` (test-analyzer disabled — Reviewer) The 7 tests assert on `plotted_course.to_body_id` (canonical id), span presence/absence, and clock-by-ETA — meaningful, no `assert True`/bare-truthy, no skips; driven through the REAL `run_dispatch_bank` (wiring-honest). Parametrize covers 4 natural label forms + a canonical-id regression guard + a loud-reject invariant guard. Acceptable gap: no test pins the `resolved_via` *value* (intentional per TEA, to avoid coupling) — the value is exercised behaviorally.
7. `[DOC]` (comment-analyzer disabled — Reviewer) Module docstring updated for 158-27; both helpers carry accurate docstrings; the inline "quest_anchors hold body ids, not labels" comment matches the code; the telemetry `resolved_via` docstring is accurate. No stale/misleading comments.
8. `[SIMPLE]` (simplifier disabled — Reviewer) Two small focused helpers; `_normalize_destination` reused 3× inside `_resolve_body_id`. No dead code, no over-engineering, minimal per the GREEN contract.
9. `[RULE]` (rule-checker disabled — Reviewer) All applicable Python lang-review checks pass — see Rule Compliance below.

### Rule Compliance (Python lang-review checklist, enumerated against the diff)

| # | Rule | Verdict |
|---|------|---------|
| 1 | Silent exception swallowing | Compliant — no `try/except` added |
| 2 | Mutable default args | Compliant — defaults are `None`/scalar (`resolved_via=None`); no `[]`/`{}`/`set()` defaults |
| 3 | Type annotations at boundaries | Compliant — both helpers fully annotated (params + `tuple[str \| None, str \| None]`); `resolved_via: str \| None = None`. (`Mapping[str, object]` loose but annotated — see [TYPE]) |
| 4 | Logging coverage/correctness | N/A — no logging added; subsystem observability is OTEL (`course.plot`/`.rejected`); no log f-strings |
| 5 | Path handling | N/A — no path manipulation |
| 6 | Test quality | Compliant — meaningful asserts, no vacuous truth, no unjustified skips |
| 7 | Resource leaks | N/A — no file/socket/lock/db |
| 8 | Unsafe deserialization | Compliant — no pickle/yaml.load/eval/exec/subprocess (confirmed [SEC]) |
| 9 | Async/await pitfalls | Compliant — new helpers are sync pure functions, no blocking I/O inside the async handler, no missing `await` |
| 10 | Import hygiene | Compliant — `from collections.abc import Mapping` (stdlib, used in annotation); no star/circular imports |
| 11 | Security input validation | Compliant — LLM/player destination validated by normalization + equality against authored content; no SQL/path/regex (confirmed [SEC]) |
| 12 | Dependency hygiene | N/A — no dependency changes |
| 13 | Fix-introduced regressions | Compliant — no broad except, correct types, all resolution paths covered; orbital sweep 649 green |

### Devil's Advocate

Let me argue this is broken. **Claim 1 — the resolver is a fuzzy guesser that will plot the wrong course.** If "the Broken Drift" resolves by stripping "the" and folding case, then a confused player typing a partial or wrong name could be silently routed somewhere plausible. *Rebuttal:* every branch is strict `==` equality on the *fully* normalized form — there is no substring/prefix/edit-distance matching. "Broken" alone normalizes to "broken" and matches no body's full normalized id or label, so it rejects LOUD. The tolerance is exactly casing + underscores + a leading article + whitespace, nothing more. **Claim 2 — article-stripping eats real names.** A body literally named "The Counter" (`the_counter`) would lose its article and become unreachable. *Rebuttal:* normalization is symmetric — `the_counter`'s id folds to "counter" and its label "THE COUNTER" folds to "counter", and a player's "the Counter" also folds to "counter", so they meet. "theater"-style false positives are avoided because the prefix check requires the full `"the "` token (with trailing space), not the letters "the". **Claim 3 — cross-body collision plots the wrong destination.** Genuinely possible in principle (interleaved id/label loop, first-match-wins). *Rebuttal:* I enumerated coyote_star's 21 bodies; no cross-body id↔label collision exists, and exact-id always wins at step 1. It is a documented LOW, not a present bug; a future world authoring such a collision is a content concern, not this fix's. **Claim 4 — a stressed/empty input crashes or phantom-plots.** *Rebuttal:* empty/`None`/non-str destination is caught by the pre-existing `malformed_destination` guard; an all-whitespace or `"the "` string folds to `""` and hits `if not target: return None, None` → loud reject; `bodies[resolved_id]` can never `KeyError` because `resolved_id` is either an exact key or a key yielded by iterating `bodies`. **Claim 5 — the OTEL change breaks the other caller.** *Rebuttal:* `resolved_via` is an optional param defaulting to `None`; `narration_apply.py` does not pass it and the attribute is simply omitted (verified by [SEC] and [PREFLIGHT]). The devil finds only the documented LOW cross-body edge — nothing blocking.

**Handoff:** To SM (the Mad Hatter) for finish-story.

## Delivery Findings

<!-- Append-only. Each agent owns its own subsection. -->

### TEA (test design)
- **Improvement** (non-blocking): The SM Root Cause ("the effect handler fails to write `plotted_course`") is imprecise — the handler writes `plotted_course` and advances the clock correctly once it reaches those lines. The real defect is the exact-match destination lookup (`bodies.get(destination)`) rejecting the LLM-emitted human label before the write. Affects `sidequest-server/sidequest/agents/subsystems/course.py` (add label/case/article-tolerant resolution before `bodies.get`, set `PlottedCourse.to_body_id` to the canonical id). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. TEA's root-cause correction was confirmed by the code trace; the fix landed exactly where TEA pointed and no further upstream issues surfaced.

### Reviewer (code review)
- No upstream findings. The one LOW observation (cross-body normalized id↔label collision in `_resolve_body_id`) is in-file and has zero current impact (no such collision in coyote_star); it is documented in the Reviewer Assessment as a non-blocking note, not an upstream defect. A future world that authored such a collision would be a content concern, not an engine one.

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** The SM Root Cause ("the effect handler fails to write `plotted_course`") is imprecise — the handler writes `plotted_course` and advances the clock correctly once it reaches those lines. The real defect is the exact-match destination lookup (`bodies.get(destination)`) rejecting the LLM-emitted human label before the write. Affects `sidequest-server/sidequest/agents/subsystems/course.py`.

### Downstream Effects

- **`sidequest-server/sidequest/agents/subsystems`** — 1 finding

### Deviation Justifications

3 deviations

- **AC scope is destination resolution, not a missing write**
  - Rationale: code trace shows the write + Hohmann clock advance already execute when the handler reaches them (proven green by the 153-5 suite); the inert burn is caused solely by the exact-match lookup rejecting human-named destinations
  - Severity: minor
  - Forward impact: none — the AC outcome ("a course intent populates `plotted_course` + engages transit") is identical to the SM's; only the fix location moves
- **Article-tolerance (`"the Red Prospect"`) is a hard AC**
  - Rationale: the literal playtest input carried an article; the router may pass it through, so the handler must not strand the burn on it (the Zork Problem — natural language, not keyword id)
  - Severity: minor
  - Forward impact: if Dev/Reviewer judge article-stripping out of scope, drop the `[the Red Prospect]` parametrize case — the other 6 tests still fully pin the fix
- **Added an optional `resolved_via` attribute to the shared `course.plot` emitter**
  - Rationale: satisfies the project OTEL lie-detector principle (every subsystem decision observable) — the resolution path is a new decision this fix introduces, and TEA explicitly recommended recording it
  - Severity: minor
  - Forward impact: none — optional param, backward-compatible; the other caller (`narration_apply.py`) does not pass it

## Design Deviations

### TEA (test design)
- **AC scope is destination resolution, not a missing write**
  - Spec source: 158-27 session `## Sm Assessment` → Root Cause / Technical Approach (steps 3–4)
  - Spec text: "it fails to write `plotted_course` to the game state" / "Ensure the effect handler … writes a `PlottedCourse`"
  - Implementation: tests target label→canonical-id resolution upstream of the (already-correct) write, not the write itself
  - Rationale: code trace shows the write + Hohmann clock advance already execute when the handler reaches them (proven green by the 153-5 suite); the inert burn is caused solely by the exact-match lookup rejecting human-named destinations
  - Severity: minor
  - Forward impact: none — the AC outcome ("a course intent populates `plotted_course` + engages transit") is identical to the SM's; only the fix location moves
- **Article-tolerance (`"the Red Prospect"`) is a hard AC**
  - Spec source: 158-27 story title + `## Sm Assessment` Problem Summary
  - Spec text: "plot a course to **the** Broken Drift, lay in the burn"
  - Implementation: a parametrized case requires the handler to tolerate a leading `"the "` on the destination label
  - Rationale: the literal playtest input carried an article; the router may pass it through, so the handler must not strand the burn on it (the Zork Problem — natural language, not keyword id)
  - Severity: minor
  - Forward impact: if Dev/Reviewer judge article-stripping out of scope, drop the `[the Red Prospect]` parametrize case — the other 6 tests still fully pin the fix

### Dev (implementation)
- **Added an optional `resolved_via` attribute to the shared `course.plot` emitter**
  - Spec source: 158-27 session `## TEA Assessment` → "The Fix (GREEN)" OTEL note
  - Spec text: "Consider recording how it resolved (e.g. a `resolved_via=…` attribute on the `course.plot` span) … recommended, not test-gated"
  - Implementation: added `resolved_via: str | None = None` to `emit_course_plot_accepted` (`telemetry/spans/course.py`) and pass `exact_id|normalized_id|label` from `course.py`; no test asserts the attribute
  - Rationale: satisfies the project OTEL lie-detector principle (every subsystem decision observable) — the resolution path is a new decision this fix introduces, and TEA explicitly recommended recording it
  - Severity: minor
  - Forward impact: none — optional param, backward-compatible; the other caller (`narration_apply.py`) does not pass it
- I kept article-tolerance (`"the Red Prospect"`) as a hard requirement rather than dropping it (the option TEA flagged): all 4 parametrized cases pass, faithful to the literal playtest phrasing "the Broken Drift".

### Reviewer (audit)
- **TEA — "AC scope is destination resolution, not a missing write"** → ✓ ACCEPTED by Reviewer: the code trace and the green 153-5 suite prove the write/clock-advance were never missing; the exact-match lookup is the real defect. The AC outcome is identical to the SM's framing — only the fix location moved. Sound.
- **TEA — "Article-tolerance (`the Red Prospect`) is a hard AC"** → ✓ ACCEPTED by Reviewer: faithful to the literal playtest input and aligned with the Zork Problem (natural language, not keyword id). The implementation strips the article *symmetrically* from destination, id, and label, so it is principled, not a hack. The `"the "`-token check (not the letters "the") correctly avoids eating "theater"-style names.
- **Dev — "Added an optional `resolved_via` attribute to the shared `course.plot` emitter"** → ✓ ACCEPTED by Reviewer: satisfies the project OTEL lie-detector principle (the resolution path is a new subsystem decision); backward-compatible optional param; the other caller (`narration_apply.py`) is unaffected (confirmed by [SEC] and [PREFLIGHT]). Good observability add, no scope creep.
- **Dev — "kept article-tolerance"** → ✓ ACCEPTED by Reviewer: consistent with the accepted TEA #2.
- **Undocumented deviations:** none. I diffed the code against the spec sources; every divergence from the SM's original framing was logged by TEA or Dev.