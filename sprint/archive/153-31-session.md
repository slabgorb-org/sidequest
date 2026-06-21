---
story_id: "153-31"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 153-31: [BENEATH_SUNDEN-DARKNESS-STATUS-COSMETICS] environmental darkness status should not tier as severity Wound and should stamp the real created_turn (not 0)

## Story Details
- **ID:** 153-31
- **Jira Key:** (none)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-21T14:16:14Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T13:50:28Z | 2026-06-21T13:52:15Z | 1m 47s |
| implement | 2026-06-21T13:52:15Z | 2026-06-21T14:10:45Z | 18m 30s |
| review | 2026-06-21T14:10:45Z | 2026-06-21T14:16:14Z | 5m 29s |
| finish | 2026-06-21T14:16:14Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): Stale module docstring in `environment_clock.py`. The module-level docstring (lines 18–20, "Sentinel-text identification — the darkness status is found/removed by its sentinel `text`") describes the OLD identity scheme; the code has keyed reconcile on the structured `source` (`DARKNESS_STATUS_SOURCE`), not `text`, since the source field was added. Affects `sidequest/agents/subsystems/environment_clock.py` (module docstring should say identity-by-`source`). Pre-existing drift, out of scope for 153-31's cosmetic field fix. *Found by Dev during implementation.*
- **Improvement** (non-blocking): 6 pre-existing pyright errors in `environment_clock.py` at lines 117/135 (`_emit_light_tick`/`_emit_light_relit` `object`→`float`/`int` coercion) and 193/204 (`_run_relight` accesses `core.inventory` / passes `core` to `_clear_darkness_penalty` while `core` is typed `CreatureCore | None`). All in functions untouched by this story; my edited sites are type-clean. Affects `sidequest/agents/subsystems/environment_clock.py` (narrow the `core` Optional or assert non-None). Pre-existing, out of scope. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Corroborate Dev's two pre-existing findings — the module-level docstring drift (`environment_clock.py` lines 18–20 still claim identity-by-`text`; code keys on `source`) and the 6 pre-existing pyright errors in `_emit_light_*`/`_run_relight`. Both confirmed by the preflight specialist and verified independently; neither is in this story's edited surface. A future `environment_clock` touch-up should fix the docstring and narrow the `core: CreatureCore | None` Optional in `_run_relight`. Affects `sidequest/agents/subsystems/environment_clock.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. AC-1 explicitly permits "either an existing non-injury tier or a new dedicated environmental tier"; reusing `StatusSeverity.Scratch` is a spec-sanctioned design choice (rationale in Dev Assessment), not a deviation. `created_turn` stamped exactly as AC-2 specifies (`snapshot.turn_manager.interaction`). No new OTEL per AC-5.

### Reviewer (audit)
- **Dev "No deviations from spec"** → ✓ ACCEPTED by Reviewer: AC-1 text explicitly sanctions reusing an existing non-injury tier; `Scratch` is a legitimate in-spec choice, well-justified. `created_turn` and the no-new-OTEL decision match AC-2/AC-5 verbatim. Agrees with author reasoning.
- **Undocumented behavioral nuance (not a spec deviation, noted for completeness):** `Wound`→`Scratch` newly subjects the darkness penalty to `clear_scratch_on_scene_end` (status_clear.py:128), where `Wound` was exempt. The Dev DID document this (Dev Assessment rationale #3) and it is benign — the penalty is re-asserted on the next unlit tick and the authoritative clear keys on `source`, so removal cannot regress. Not flagged; severity LOW; acceptable.

## Sm Assessment

**Routing:** New work, picked up via `/pf-work 153-31`. 1-pt `trivial` (phased) bug, server-only. Board clear (no blocking PRs, no Jira). Handing off to Dev (Agent Smith) for the implement phase.

**Scope (cosmetic, two fields):** In `sidequest-server/sidequest/agents/subsystems/environment_clock.py` → `_ensure_darkness_penalty`, the darkness `Status` is built with `severity=StatusSeverity.Wound` (an ambient light penalty reading as a bodily injury) and no `created_turn` (defaults to `0`). Fix both. The −2 `roll_modifier`, `source='environment_clock'`, and the light-floor/relight apply/remove conditions are UNCHANGED. Full spec: `sprint/context/context-story-153-31.md` (5 ACs).

**Design decision for Dev (justify in the PR):** severity — reuse an existing non-injury tier (`Scratch`, the lightest scene-bounded tier) vs. add a dedicated environmental tier to `StatusSeverity` (`game/status.py`). Reuse-first doctrine favors `Scratch` UNLESS its recovery cadence ("lifts at scene end") is semantically wrong for an ambient state that should lift on relight. **Hard constraint:** whatever tier is chosen, the relight-clear path must still remove the penalty (no silent persist — see context Technical Notes). `created_turn` — stamp `snapshot.turn_manager.interaction` (canonical monotonic marker the sibling status sites use).

**Test obligations:** update the fixture in `tests/server/test_environment_clock_injection.py` (~L366) that hard-codes `StatusSeverity.Wound`; keep `test_environment_clock` + `test_environment_clock_otel` green (the `light.tick` span with `penalty_applied=True` is the AC-5 wiring proof — reuse it, do NOT add new OTEL; cosmetic-field carve-out applies).

## Dev Assessment

**Implementation Complete:** Yes

**Design decision — severity tier: reused `StatusSeverity.Scratch`** (did NOT add a new enum value). Rationale:
1. `Scratch` is the lightest, scene-bounded, NON-injury tier — semantically "a minor transient ambient penalty," which is exactly what a darkness penalty is. It is no longer the injury tier (`Wound`).
2. The "lifts on relight" lifecycle the spec worried about is enforced by the `source`-keyed reconcile — `_clear_darkness_penalty` and the lit-region/above-floor reconcile all key on `Status.source == DARKNESS_STATUS_SOURCE`, which is **severity-independent**. So no tier needs to encode "lifts on relight," and the AC-1 hard constraint (relight removal must not regress) holds for any severity. Verified: `test_penalty_cleared_when_region_lit`, `test_relight_*`, and `test_llm_emitted_relight_engages_through_live_bank` all stay green.
3. The only severity-keyed recovery path is `status_clear.clear_scratch_on_scene_end` (sweeps `{Scratch, Boon}`). With `Scratch`, a scene-end sweep clears the darkness penalty — which is benign: it is re-asserted on the next unlit `environment_clock` tick, so it can never wrongly persist. No "silent persist" risk.
4. Reuse-first doctrine + Dev minimalist discipline: adding an enum value would have rippled into `status_clear`, narrator status rendering, `query_character`, and reference-page projection for a cosmetic fix. Not warranted.

**created_turn:** stamped `snapshot.turn_manager.interaction` (the canonical monotonic forensic marker the sibling status sites — `apply_status`, `post_resolution_lethality`, `dice` — use), threaded into `_ensure_darkness_penalty(core, *, created_turn)`. No longer the implicit `0`.

**Cosmetic-only invariants held:** `roll_modifier=-2`, `source='environment_clock'`, and the light-floor/relight apply+remove conditions are unchanged.

**Files Changed:**
- `sidequest/agents/subsystems/environment_clock.py` — `_ensure_darkness_penalty`: `severity` `Wound`→`Scratch`, added `created_turn` param stamped from `snapshot.turn_manager.interaction`; docstring rewritten to explain the Scratch/non-injury choice and the source-keyed (severity-independent) clear.
- `tests/agents/subsystems/test_environment_clock.py` — new `test_darkness_penalty_is_not_a_wound_and_stamps_current_turn` (pins AC-1: `severity != Wound`, `is Scratch`; AC-2: `created_turn == 3` on a turn-3 snapshot; AC-3: `roll_modifier`/`source` unchanged); added `StatusSeverity` import.
- `tests/server/test_environment_clock_injection.py` — relight fixture updated `Wound`→`Scratch` + `created_turn` to mirror the new mint (keeps the "exactly as the burn path mints it" comment honest).
- `tests/agents/test_narrator_sees_light_state.py` — `_darkness_status()` helper updated `Wound`→`Scratch` + `created_turn` so it no longer enshrines the old shape (asserts on text, stays green).

**Tests:** 40/40 passing (GREEN) across the 4 affected files under `-n0` (deterministic).
- `light.tick` AC-5 wiring proof intact: `test_burn_to_zero_emits_light_tick_with_penalty` (penalty_applied=True) green.
- Full-suite regression: stash-baseline = **269 failed / 13349 passed / 117 errors**; with my change = **267 failed / 13352 passed / 117 errors**. **Zero net new failures** (failures down, passes up). The 267/117 are pre-existing environmental / in-flight-sprint reds (epic-108 WN-combat known-red, epic-157 zone work, integration tests needing a live daemon/chargen), confirmed unrelated — the 3 that matched a `status|light` filter are MP-reconnect / chargen-wiring / lore-rag tests, none touching severity.

**Lint/format/types:** `ruff check` + `ruff format --check` clean on all 4 changed files (import sort + format applied, scoped to changed files). `pyright` on `environment_clock.py`: 6 errors, all pre-existing in untouched functions (`_emit_light_*`, `_run_relight`); my edited sites are type-clean. Logged both pre-existing items as non-blocking Delivery Findings.

**Branch:** `feat/153-31-darkness-status-cosmetics` (pushed)

**Handoff:** To review phase (The Merovingian / Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (40/40 green, ruff clean, format clean, 0 new pyright) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none (0 violations across 6 rule classes) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (2 enabled returned clean; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 0 dismissed, 2 deferred (pre-existing non-blocking: module-docstring drift + 6 pre-existing pyright errors — both out of scope, logged to Delivery Findings)

**Disabled-domain self-assessment** (since 7 specialists are off, I assessed their domains myself — see tags in the Assessment below): EDGE, SILENT, TEST, DOC, TYPE, SIMPLE, RULE all covered by direct Reviewer analysis of a 51-line/4-file cosmetic diff.

## Rule Compliance

Enumerated `.pennyfarthing/gates/lang-review/python.md` (13 checks) against every changed line:

- **#1 Silent exception swallowing** — N/A. No `try/except`/`suppress` added. The keyword-only `created_turn` raises `TypeError` loudly if a future caller omits it (no silent default). COMPLIANT.
- **#2 Mutable default arguments** — COMPLIANT. `created_turn: int` is an immutable scalar, keyword-only, no default. No new mutable defaults.
- **#3 Type annotation gaps at boundaries** — COMPLIANT. `_ensure_darkness_penalty(core: CreatureCore, *, created_turn: int) -> bool` is fully annotated. (Private helper — exempt anyway, but annotated.)
- **#4 Logging coverage/correctness** — N/A. No logging in the diff; no sensitive data.
- **#5 Path handling** — N/A. No path manipulation.
- **#6 Test quality** — COMPLIANT. New test `test_darkness_penalty_is_not_a_wound_and_stamps_current_turn` asserts SPECIFIC values (`severity is StatusSeverity.Scratch`, `created_turn == 3`, `roll_modifier == DARKNESS_PENALTY`, `source == DARKNESS_STATUS_SOURCE`) — no vacuous `assert result`. It sets `turn_manager.interaction = 3` to prove the stamp is the real turn (would catch a regression to 0). The 3 fixture edits mirror the production mint. No skips, no mock-target errors.
- **#7 Resource leaks** — N/A. No resource acquisition.
- **#8 Unsafe deserialization** — N/A. No pickle/eval/yaml/subprocess (security specialist confirmed).
- **#9 Async/await pitfalls** — COMPLIANT. `_ensure_darkness_penalty` is sync; the async caller `run_environment_clock_dispatch` does no blocking I/O in the changed lines; no new `gather`/`await`.
- **#10 Import hygiene** — COMPLIANT. One explicit import added (`from sidequest.game.status import StatusSeverity` in the test), ruff-sorted; no star/circular imports.
- **#11 Input validation at boundaries** — N/A. `created_turn` is a server-internal monotonic int; `DARKNESS_STATUS_TEXT`/`_SOURCE` are server constants. No user input crosses this surface (security specialist confirmed).
- **#12 Dependency hygiene** — N/A. No dependency changes.
- **#13 Fix-introduced regressions** — COMPLIANT. The fix introduces no broad except, no wrong type, no one-path-only validation. Pydantic `Status` enforces `created_turn: int` and `severity: StatusSeverity` at construction.

## Devil's Advocate

Let me argue this code is broken. **Attack 1 — the scene-end sweep.** By moving the darkness penalty from `Wound` to `Scratch`, I have placed it in `clear_scratch_on_scene_end`'s `{Scratch, Boon}` kill-set. A malicious or merely unlucky sequence: PC at light=0 in a dark region, an encounter resolves (scene end) → the −2 darkness penalty is swept. If the next turn is NOT a time-advancing turn in an unlit region (e.g. a pure social beat, or the `environment_clock` dispatch is somehow not injected), the PC now fights/acts in pitch dark with NO penalty — a mechanical advantage the spec did not intend. **Rebuttal:** the penalty is state-reconciled, not event-minted; `inject_environment_clock` fires on every time-advancing turn and re-asserts at the floor, and a non-advancing beat in the dark is exactly the kind of moment where a −2 roll modifier wouldn't be consulted anyway (no roll). The window is at most one beat, deterministically closed, and is identical in spirit to the pre-existing "premature clear heals only until the next unlit tick" contract the old `Wound` docstring already acknowledged. So: a real behavioral change, but not an exploit and not a correctness break. **Attack 2 — created_turn lies under a stale snapshot.** If `snapshot.turn_manager` were a detached/zeroed copy, `created_turn` would be wrong again. **Rebuttal:** `turn_manager` is `default_factory=TurnManager` (never None) and the same `snapshot.turn_manager.interaction` is the canonical marker used by session.py:1559/1790 — if it were stale, far more than this status would be wrong. **Attack 3 — a confused author reads the stale module docstring** (lines 18–20, "identification by sentinel text") and "fixes" the clear path to match text, breaking the source-keyed reconcile. **Rebuttal:** real risk, but pre-existing drift unrelated to this diff; logged as a non-blocking finding for a future touch-up. **Attack 4 — the new test is tautological.** Does it actually pin the fix? Setting `interaction = 3` and asserting `created_turn == 3` would FAIL on the old code (which stamped 0), and `severity is Scratch` would FAIL on the old `Wound`. So the test genuinely red-greens the change. No tautology. Conclusion: nothing rises above LOW.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** unlit time-advancing turn → `run_environment_clock_dispatch` burns `light` to floor → `_ensure_darkness_penalty(core, created_turn=snapshot.turn_manager.interaction)` mints a `Status(severity=Scratch, created_turn=<real turn>, roll_modifier=-2, source='environment_clock')` → status surfaces to the player as a non-injury ambient penalty and is cleared on relight/lit-region (by `source`, severity-independent) or swept at scene end (re-asserted next unlit tick). Safe: no user input enters this path; both new field values are server-internal (enum constant + monotonic int).

**Pattern observed:** correct reuse of the existing `StatusSeverity` taxonomy + sibling `created_turn=turn_manager.interaction` stamping pattern (mirrors `apply_status.py`, `post_resolution_lethality.py`, `dice.py`) — `sidequest/agents/subsystems/environment_clock.py:56-63, 277`.

**Error handling:** keyword-only `created_turn` (no default) makes omission a loud `TypeError`, not a silent 0 — consistent with No Silent Fallbacks. Pydantic `Status` validates types at construction.

**Findings by source (all 8 dispatch domains covered):**
- `[SEC]` (specialist, clean): no injection/deserialization/auth/info-leak surface; `created_turn` not user-controlled; `DARKNESS_STATUS_TEXT/_SOURCE` server constants — no ADR-047 exposure. Confirmed clean.
- `[EDGE]` (disabled — Reviewer-assessed): boundary cases enumerated — second tick at floor (idempotent guard unchanged), enter-already-at-0 (`test_starts_unlit_at_zero...` green), scene-end sweep then re-assert (Devil's Advocate Attack 1). No unhandled path. LOW only.
- `[SILENT]` (disabled — Reviewer-assessed): no swallowed errors or silent fallbacks introduced; clear-path keys on `source` and is unchanged. Clean.
- `[TEST]` (disabled — Reviewer-assessed): new test asserts specific values and would fail on the pre-fix code (Devil's Advocate Attack 4); fixtures mirror production; AC-5 `light.tick`/`penalty_applied=True` wiring proof stays green. Clean.
- `[DOC]` (disabled — Reviewer-assessed): `_ensure_darkness_penalty` docstring accurately rewritten; **pre-existing** module-docstring drift (lines 18–20) noted as non-blocking finding. LOW, out of scope.
- `[TYPE]` (disabled — Reviewer-assessed): edited sites type-clean (preflight confirmed 0 new pyright); 6 pyright errors all pre-existing in untouched functions. LOW, out of scope.
- `[SIMPLE]` (disabled — Reviewer-assessed): minimal change, no over-engineering; reuse-first (no new enum value) is the simplest correct option. Clean.
- `[RULE]` (disabled — Reviewer-assessed): all 13 python lang-review checks COMPLIANT/N-A (see Rule Compliance). Clean.

**Observations (≥5):**
1. `[VERIFIED]` Relight removal does not regress — `_clear_darkness_penalty` filters on `source != DARKNESS_STATUS_SOURCE` (environment_clock.py:72), severity-independent; AC-1 hard constraint held. Complies with the context's "relight removal must not regress."
2. `[VERIFIED]` `created_turn` is the real turn — `snapshot.turn_manager.interaction` (environment_clock.py:277) is the canonical monotonic marker (session.py:1559/1790); `turn_manager` is `default_factory` so never None.
3. `[VERIFIED]` Idempotency preserved — early-return guard `any(s.source == DARKNESS_STATUS_SOURCE ...)` (environment_clock.py:65) unchanged; `test_reaching_zero_applies_darkness_penalty_once` green.
4. `[LOW]` Scene-end sweep now clears the darkness Scratch (status_clear.py:128) where Wound was exempt — benign (re-asserted next unlit tick), documented by Dev, not a regression.
5. `[LOW]` Pre-existing module-docstring drift (environment_clock.py:18–20) + 6 pre-existing pyright errors — out of scope, logged as non-blocking Delivery Findings.
6. `[VERIFIED]` No security surface — security specialist clean across 6 rule classes; cosmetic-field change only.

**No Critical or High findings.** Both enabled specialists returned clean; my independent pass and Devil's Advocate surfaced only LOW/VERIFIED items. The change does exactly what AC-1/AC-2/AC-3 require, holds the cosmetic-only invariants (AC-4 idempotence/relight, AC-5 OTEL wiring proof), and is in-spec.

**Handoff:** To SM (Morpheus) for finish-story.