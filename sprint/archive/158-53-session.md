---
story_id: "158-53"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-53: WWN magic cast does not decrement remaining charges (cinder_lance before=2 after=2)

## Story Details
- **ID:** 158-53
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-02T09:01:19Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-01T22:30:23Z | 2026-07-01T22:32:52Z | 2m 29s |
| red | 2026-07-01T22:32:52Z | 2026-07-02T08:39:35Z | 10h 6m |
| green | 2026-07-02T08:39:35Z | 2026-07-02T08:54:51Z | 15m 16s |
| review | 2026-07-02T08:54:51Z | 2026-07-02T09:01:19Z | 6m 28s |
| finish | 2026-07-02T09:01:19Z | - | - |

## Sm Assessment

**Selection:** Picked over `pf sprint work next`'s resolved pick (158-40, a p3 dogfight story chosen only for lowest ID). 158-53 is a p2 with no dependencies; Keith confirmed the priority-correct pick. See sm-gotchas.md — `work next` sorts by ID, not priority.

**Scope:** Single-repo (sidequest-server). WWN-bound magic cast resolves the spell narratively but never decrements the remaining-uses/charges counter, so a caster has effectively infinite casts. Evidence: `test_wwn_scene_harness_fixture_proof` shows cinder_lance before=2, after=2 (should be after=1). This is a mechanics-first regression — exactly what Sebastien/Jade would catch — and the player-facing charge count would sit unchanging.

**Branch:** `feat/158-53-wwn-magic-charge-decrement` off `develop` (server = gitflow). Clean tree.

**For Fezzik (TEA) — RED targets (see context-story-158-53.md for full ACs):**
1. A successful WWN cast (cinder_lance) decrements remaining charges/uses (before=2 → after=1). Assert through the **real** cast path, not an isolated helper.
2. An OTEL watcher span fires on the cast recording the spend (before/after remaining). Per the OTEL principle, the GM panel must be able to verify the decrement fired rather than the narrator improvising it — a silent span is a fail.
3. A wiring test proves the decrement is reachable from production code paths (not just a unit).

**Caveat to confirm at pickup:** diagnosis is from a scoping pass (surfaced 2026-07-01 while scoping the 160-4 green push, unrelated to 160-4). Fezzik should reproduce the before=2/after=2 failure first to confirm the root cause before writing the RED assertion — don't build on a stale premise.

**Doctrine guardrail:** This is a *charge-spend* fix on the bound-WWN path, NOT a combat-balance change. Do not tune, gate, or convert native mechanics against the WWN binding (SOUL.md "Bind the Ruleset, Don't Balance It" / ADR-143). We're making the existing WWN charge counter actually decrement — nothing more.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a

**Test Files:**
- `tests/integration/test_wwn_scene_harness_fixture_proof.py` — rewrote `test_hydrated_wwn_fixture_drives_cast_spell_and_ablates_hp` onto the ADR-143-correct DICE_THROW → run_wn_round → WWN cast spine path; added assertion 6 (span carries `casts_before`/after).
- `tests/game/ruleset/test_wwn_spellcast.py` — added 2 unit tests pinning `casts_before` on the SPEND and REFUSE span branches.

**Tests Written:** 3 failing (1 integration assertion + 2 unit) covering AC #2. The rewritten integration test also regression-guards AC #1/#3 (decrement 2→1 + HP ablation through the real cast path) — those assertions pass on current production.
**Status:** RED — verified by testing-runner (`158-53-tea-red`): **3 failed / 12 passed / 1 skipped**. Every failure is the intended `casts_before` absence (quoted assertion messages confirmed); no import/setup errors, no collateral breakage. Clean RED.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| OTEL span coverage (every subsystem decision emits a span — the lie detector) | integration assertion 6 + `test_span_records_casts_before_on_a_spend`/`_refusal` | failing (RED) |
| No Source-Text Wiring Tests (assert on spans/behavior via the real path, not source text) | all — drive the real DICE_THROW/`resolve_spellcast` seam, assert on `wwn.spell.cast` attrs | ✓ pattern |
| No vacuous assertions (specific-value checks) | new assertions check exact values (`==2`, `==1`, `==0`) | ✓ |
| No Silent Fallbacks (fail loud) | span records refused + before/after; no silent no-op | ✓ |

**Rules checked:** OTEL, no-source-text-wiring, no-vacuous-assertions, no-silent-fallbacks (the applicable python lang-review checks for this change).
**Self-check:** 0 vacuous tests found (every new assertion checks a specific value; no `assert True` / bare `is_none`).

**Handoff:** To Dev (Inigo Montoya) for GREEN. Add `casts_before` to `wwn_spell_cast_span` (signature + attributes dict + `SPAN_ROUTES[SPAN_WWN_SPELL_CAST]` extract in `sidequest/telemetry/spans/wwn.py`) and pass it from BOTH call sites in `sidequest/game/ruleset/wwn.py`: the success path captures the PRE-decrement value (`before = state.casts_remaining` *before* `-= 1`); the `_refuse` path passes `before == state.casts_remaining` (unchanged). **Do NOT** touch the charge-decrement logic — it is already correct. **Do NOT** exempt `cast_spell` from the ADR-143 WN-combat beat drop (doctrine: bind the ruleset, don't balance it — SOUL.md / ADR-143).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/telemetry/spans/wwn.py` — added required kw-only `casts_before` to `wwn_spell_cast_span` (signature + attributes dict) and to the `SPAN_WWN_SPELL_CAST` route extract (the GM-panel typed feed).
- `sidequest/game/ruleset/wwn.py` — `resolve_spellcast`: capture `casts_before` before the `-= 1` decrement (success path) + pass `casts_before == casts_remaining` on the `_refuse` path.

**Tests:** GREEN. Story files 15 passed / 1 skipped (the 3 formerly-RED now pass). Full server suite via testing-runner (`158-53-dev-green`): **13038 passed / 0 regressions / 1709 skipped**. Lint + pyright clean on both changed files.
**Pre-existing failures (NOT regressions):** the full-suite run surfaced 7 failures verified on the parent commit — they map to OTHER open backlog stories (158-54 `awn.mutation.used` span, 158-40 dogfight content, 158-52 bestiary/creature images, a sealed_letter lifecycle test). None touch the cast spine or `wwn_spell_cast_span`.
**Branch:** `feat/158-53-wwn-magic-charge-decrement` (pushed, commit `95e3208a`).

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (GREEN: ruff pass, pyright 0 errors, 15 passed/1 pre-existing skip, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — edge/boundary domain assessed by reviewer directly ([EDGE] below) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 1 (LOW) | confirmed 1 (noted, non-blocking); 0 dismissed |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test-quality domain assessed by reviewer directly ([TEST] below) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — doc/comment domain assessed by reviewer directly ([DOC] below) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type domain assessed by reviewer directly ([TYPE] below) |
| 7 | reviewer-security | Yes | clean | 0 | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — simplicity domain assessed by reviewer directly ([SIMPLE] below) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — rule compliance enumerated by reviewer directly ([RULE] / Rule Compliance below) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` settings, their domains covered by the reviewer)
**Total findings:** 1 confirmed (LOW, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** Player `DICE_THROW(beat_id=cast_spell, spell_id)` → `dispatch_dice_throw` → `run_wn_round` → `_apply_committed_player_beat` → `WwnRulesetModule.resolve_spellcast` → `casts_before = state.casts_remaining` captured *before* `state.casts_remaining -= 1` → `wwn_spell_cast_span(casts_before, casts_remaining)` → span attributes → `SPAN_ROUTES[SPAN_WWN_SPELL_CAST]` extract → GM-panel typed feed. **Safe because** `casts_before` is an `int` snapshot of server-authoritative engine state (`SpellcastingState.casts_remaining`, `extra="forbid"`, mutated only by engine code — never a client payload field), passed as a typed OTEL attribute, never interpolated into a string/command/query.

**Observations (subagent findings tagged by source; disabled domains assessed directly):**
- `[SILENT]` **LOW** — `spans/wwn.py:44` `SPAN_ROUTES` extract defaults `casts_before` via `.get("casts_before", 0)`. **Confirmed as noted, non-blocking.** The emit helper makes `casts_before` a *required* kw-only param, so an omitting caller raises `TypeError` at emission (fail-loud, not silent); `Span.open` only drops `None`-valued attrs and `casts_before` is always a plain `int`. The `.get(key, default)` shape is the pre-existing, repo-wide `SpanRoute.extract` convention (every field on this route + ~55 span files use it). The only path that hits the `0` default is a pre-deploy span replayed through the new extract — a deploy-skew artifact this diff does not create. Optional future hardening (silent-failure-hunter's suggestion): a `-1` sentinel would distinguish a genuinely-absent attribute from a real `casts_before=0` on the no-casts refuse branch. Not required.
- `[SEC]` **VERIFIED clean** — `casts_before` derives exclusively from trusted `state.casts_remaining` (pydantic int, engine-mutated only); no info-leak, injection, or PII. Same value class as the pre-existing `casts_remaining` attribute. Evidence: security subagent full data-flow trace + my own grep of every `casts_remaining` reference.
- `[EDGE]` **VERIFIED** (edge-hunter disabled — reviewer-assessed) — boundary values correct: 0-cast refusal → `casts_before=0, casts_remaining=0`; 1-cast spend → `1→0`; 2-cast spend → `2→1`. No negative/overflow risk — the decrement is guarded by `if state.casts_remaining <= 0: return _refuse(...)` (`wwn.py:119`), so `-= 1` only runs on a value `>= 1`.
- `[TEST]` **VERIFIED, one LOW gap** (test-analyzer disabled — reviewer-assessed) — the 2 unit tests assert exact values (`==2/==1/==0`) on BOTH span branches; the integration test drives the REAL DICE_THROW spine and keeps assertions 1-5 while adding the before/after assertion 6. No vacuous assertions, no wrong monkeypatch target (unit tests pass rng explicitly via `_fixed_rng`; the integration test's global `random.randint` patch is the correct module-level target for the dispatch path — independently confirmed GREEN). **LOW gap:** the refuse span-assert covers only the `casts_remaining=0` branch (before==after==0); the not-prepared / level-too-high refusals (before==after==2) share the identical `_refuse` emit and are not span-asserted. Same code path → not a real risk; non-blocking.
- `[DOC]` **LOW** (comment-analyzer disabled — reviewer-assessed) — the two new unit-test docstrings say "RED until casts_before is wired onto the span"; now GREEN, so the "RED until" phrasing is mildly stale. Cosmetic, non-blocking.
- `[TYPE]` **VERIFIED** (type-design disabled — reviewer-assessed) — `casts_before: int` is a properly-annotated required keyword-only param; the attribute is a plain `int`; pyright reports 0 errors on both files.
- `[SIMPLE]` **VERIFIED** (simplifier disabled — reviewer-assessed) — minimal additive change (14 insertions, 1 deletion in production): one capture line, one param, one attribute, one route key, two call-site args. No abstraction, no dead code, no over-engineering.
- `[RULE]` — see Rule Compliance below (rule-checker disabled — reviewer enumerated).

### Rule Compliance

| Rule (python.md / SOUL / CLAUDE) | Instances in diff | Verdict |
|---|---|---|
| #1 Silent exception swallowing | 0 except blocks added | Compliant (N/A) |
| #2 Mutable default arguments | `casts_before: int` required, no default | Compliant |
| #3 Type annotations at boundaries | public helper param annotated `casts_before: int`; return `-> None` intact | Compliant |
| #6 Test quality | specific-value asserts both branches; the 1 skip is pre-existing with a reason | Compliant (LOW doc note above) |
| #10 Import hygiene | integration test swaps function-local imports; ruff confirms no unused; no star imports | Compliant |
| #11 Security input validation | `casts_before` from trusted engine int, not user input | Compliant |
| SOUL: No Silent Fallbacks | write path fail-loud (required kwarg); extract default = display backfill per repo convention | Compliant (LOW note) |
| CLAUDE: OTEL Observability Principle | change ADDS before/after span coverage — the decrement is now GM-panel-verifiable | Compliant (positive) |
| SOUL/ADR-143: Bind the Ruleset, Don't Balance It | decrement logic + the `wn_combat_beat_dropped_engine_owns_round` guard both UNTOUCHED (verified: diff limited to span wiring) | Compliant |

**Tenant isolation audit:** N/A — single-tenant personal game engine (CLAUDE.md); no tenant-id fields or trait methods handling tenant data in the diff. No fields to privatize.

**Rescope citation independently verified:** ran `test_dice_path_spell_cast_102_2::test_cast_beat_with_spell_id_fires_wwn_cast_spine` → **1 passed** (the engine cast path DOES decrement), and confirmed the `wn_combat_beat_dropped_engine_owns_round` guard exists at `narration_apply.py:6536` (gated on `is_live_wn_combat`) — so the old narrator-beat cast path is dead *by design*, not a regression. The rescope premise holds on inspection, not faith.

### Devil's Advocate

Let me argue this code is broken. **First attack — the capture races the mutation.** `casts_before = state.casts_remaining` is read at line 132, but the span isn't emitted until ~30 lines later; if anything between them touched `casts_remaining`, `casts_before` would be a lie. I traced those lines: only the defender-save d20 roll and damage-dice rolls happen between capture and emit — neither mutates `casts_remaining`. Invariant `casts_before == casts_remaining + 1` holds. **Second attack — a caller forgets the new param and emits a span with a phantom `casts_before`.** Impossible: it's a *required* kw-only arg, so omission is a `TypeError` before the span is born, and grep confirms exactly two callers, both supplying it. **Third attack — the `.get("casts_before", 0)` default silently manufactures a `0`.** This is the one real seam: a span emitted by old code and replayed through the new extract yields `0`, indistinguishable from a legitimate no-casts refusal. But this diff never emits such a span (the write path always sets the value), so the only trigger is deploy-skew replay — an operational edge, not a code defect. A `-1` sentinel would be marginally more honest; 0 is acceptable and matches the sibling `casts_remaining` default. **Fourth attack — the integration-test rewrite quietly weakened coverage.** It swapped the drive path from narrator-beat to DICE_THROW. Did we lose the narrator-beat assertion? No — that path is dead by ADR-143 (the drop guard is tested elsewhere), and the rewrite *strengthened* coverage by driving the real player spine while keeping assertions 1-5 and adding 6. **Fifth attack — a malicious player forges `casts_before`.** The value never originates from client input; it's an engine snapshot the GM panel merely displays. **Fifth-and-a-half — the refuse test only covers the zero-casts branch.** True, and it's the one genuine (LOW) gap: the not-prepared/level-too-high refusals aren't span-asserted — but they route through the identical `_refuse` closure, so behavior is provably identical. None of these rise above LOW. The code does exactly what AC #2 asks and nothing more.

**Verdict:** APPROVED — no Critical/High findings; 1 LOW `[SILENT]` (confirmed, non-blocking) + 2 LOW reviewer notes (test-gap, stale docstring). All ACs met, OTEL principle served, doctrine (ADR-143) respected.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): Story 158-53's filed root cause ("WWN cast never decrements → infinite casts") is stale — the counter decrements on every real player path; the only non-decrementing path (a narrator `cast_spell` beat in a live WN combat) is dropped by ADR-143 #1050 *by design*, so there is no player-facing infinite-cast bug.
  Affects `tests/integration/test_wwn_scene_harness_fixture_proof.py` (rewritten onto the DICE_THROW path) and — for the actual AC #2 deliverable — `sidequest/telemetry/spans/wwn.py` + `sidequest/game/ruleset/wwn.py` (add `casts_before` to the cast span).
  *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. (Context: the full-suite GREEN run surfaced 7 pre-existing failures that map to OTHER open backlog stories — 158-54 `awn.mutation.used` span, 158-40 dogfight content, 158-52 bestiary/creature images — verified on the parent commit, unrelated to this change.)

### Reviewer (code review)
- **Improvement** (non-blocking): the `wwn.spell.cast` `SPAN_ROUTES` extract defaults `casts_before` to `0` (`.get("casts_before", 0)`), which is indistinguishable from a real `casts_before=0` on the no-casts refusal branch. Affects `sidequest/telemetry/spans/wwn.py:44` (a `-1` sentinel would make a genuinely-absent attribute distinguishable, if ever desired — only fires on deploy-skew span replay, not live emits). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the two new unit-test docstrings say "RED until casts_before is wired" (now GREEN — mildly stale phrasing), and the refuse-branch span assertion covers only the zero-casts refusal. Affects `tests/game/ruleset/test_wwn_spellcast.py` (cosmetic; the not-prepared/level-too-high refusals share the same `_refuse` emit path). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** the `wwn.spell.cast` `SPAN_ROUTES` extract defaults `casts_before` to `0` (`.get("casts_before", 0)`), which is indistinguishable from a real `casts_before=0` on the no-casts refusal branch. Affects `sidequest/telemetry/spans/wwn.py:44`.
- **Improvement:** the two new unit-test docstrings say "RED until casts_before is wired" (now GREEN — mildly stale phrasing), and the refuse-branch span assertion covers only the zero-casts refusal. Affects `tests/game/ruleset/test_wwn_spellcast.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest/telemetry/spans`** — 1 finding
- **`tests/game/ruleset`** — 1 finding

### Deviation Justifications

1 deviation

- **Rescoped the RED from a (non-existent) decrement fix to the OTEL before/after span; rewrote the cast drive path narrator-beat → DICE_THROW**
  - Rationale: The story's filed root cause is stale — invalidated by the later ADR-143 #1050 de-nativization (the 158-49 stale-premise pattern). Keith chose "Rescope: fix the stale test" (2026-07-01). A test asserting a decrement that already works would be vacuous; the real deliverable is the OTEL before/after span.
  - Severity: major
  - Forward impact: Dev's GREEN is a small span-attribute add (`casts_before` on `wwn_spell_cast_span` + `SPAN_ROUTES` extract + BOTH call sites in `wwn.py`, captured PRE-decrement on success / == `casts_remaining` on refuse) — NOT a charge-economy change. No production behavior change to the decrement itself.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Rescoped the RED from a (non-existent) decrement fix to the OTEL before/after span; rewrote the cast drive path narrator-beat → DICE_THROW**
  - Spec source: context-story-158-53.md, Problem + AC #1
  - Spec text: "The bound-WWN magic cast path resolves the spell narratively but never decrements the remaining-uses/charges counter" / "decrement the charge/use counter on a successful WWN cast"
  - Implementation: The charge counter ALREADY decrements on every real player cast path (DICE_THROW-in-combat + free-play; proven green by `test_dice_path_spell_cast_102_2`, 11 passing). The failing test drove its cast via a narrator `BeatSelection` through `_apply_narration_result_to_snapshot` — a path ADR-143 (#1050, `wn_combat_beat_dropped_engine_owns_round`) intentionally DROPS for a live WN combat, so the cast never ran (before=2 after=2), by design. Rewrote the scene-harness proof onto the ADR-143-correct DICE_THROW → run_wn_round → cast spine path (assertions 1-5 pass on current production) and anchored the RED on AC #2 (the `wwn.spell.cast` span carrying `casts_before`/after) instead of a non-existent decrement bug.
  - Rationale: The story's filed root cause is stale — invalidated by the later ADR-143 #1050 de-nativization (the 158-49 stale-premise pattern). Keith chose "Rescope: fix the stale test" (2026-07-01). A test asserting a decrement that already works would be vacuous; the real deliverable is the OTEL before/after span.
  - Severity: major
  - Forward impact: Dev's GREEN is a small span-attribute add (`casts_before` on `wwn_spell_cast_span` + `SPAN_ROUTES` extract + BOTH call sites in `wwn.py`, captured PRE-decrement on success / == `casts_remaining` on refuse) — NOT a charge-economy change. No production behavior change to the decrement itself.

### Dev (implementation)
- No deviations from spec. Implemented exactly per the TEA handoff: added `casts_before` to `wwn_spell_cast_span` (signature + attribute + `SPAN_ROUTES` extract) and both `resolve_spellcast` call sites (pre-decrement capture on success; before==after on refuse). The charge-decrement logic and the ADR-143 WN-combat beat drop were left untouched (doctrine: bind the ruleset, don't balance it).

### Reviewer (audit)
- **TEA's rescope (RED narrator-beat → DICE_THROW; anchor on the OTEL before/after span)** → ✓ **ACCEPTED by Reviewer.** Independently verified: the engine cast path decrements (`test_dice_path_spell_cast_102_2::test_cast_beat_with_spell_id_fires_wwn_cast_spine` → 1 passed) and the `wn_combat_beat_dropped_engine_owns_round` guard exists (`narration_apply.py:6536`, gated on `is_live_wn_combat`) — so the old narrator-beat cast path is dead by ADR-143 design, and the story's "infinite casts" premise was stale. Rescoping to the real deliverable (AC #2, the before/after span) is sound and Keith-approved (2026-07-01). The rewritten test is stronger (drives the real player DICE_THROW spine) with no coverage loss.
- **Dev's "no deviations" (implemented exactly to TEA spec)** → ✓ **ACCEPTED by Reviewer.** Confirmed the diff is limited to span wiring: the `casts_remaining -= 1` decrement and the ADR-143 beat-drop guard are untouched (no native-mechanic tuning against the WWN binding). Capture-before-decrement is correct on both branches.
- No undocumented deviations found: the diff touches only the two declared production files; nothing diverged from the session scope without a logged entry.