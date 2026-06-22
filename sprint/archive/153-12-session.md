---
story_id: "153-12"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 153-12: [SWN-RESOLUTION-BEAT-NO-EXIT] resolution beat offers a non-lethal confrontation exit under hp_depletion

## Story Details
- **ID:** 153-12
- **Jira Key:** (none — epic-153 is sprint-tracked, not Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repo:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T09:16:05Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-22T08:15:10+00:00 | 2026-06-22T08:36:08Z | 20m 58s |
| green | 2026-06-22T08:36:08Z | 2026-06-22T09:03:55Z | 27m 47s |
| review | 2026-06-22T09:03:55Z | 2026-06-22T09:16:05Z | 12m 10s |
| finish | 2026-06-22T09:16:05Z | - | - |

## Story Context

Full context document: `sprint/context/context-story-153-12.md`

**Problem:** Under `hp_depletion` combat (WN binding), a ✦-marked resolution beat (e.g. "Fall Back") that succeeds does not end the confrontation. The player commits the beat, receives `ENCOUNTER_BEAT_APPLIED` with `beat=retreat tier=CritSuccess`, but remains trapped in the encounter — no `ENCOUNTER_ENDED` fires.

**Fix Direction:** Wire the resolution-beat success path so a succeeded ✦ resolution beat ends the confrontation as a non-lethal exit under `hp_depletion`.

**Acceptance Criteria:**
1. Succeeded resolution beat ends the confrontation (non-lethal exit).
2. Failed resolution beat does not end the confrontation.
3. Non-lethal exit is distinct from hp-depletion win.
4. WN SRD action economy honored; no native dial invented.
5. Observability: watcher span marks confrontation-end-on-exit.
6. Wiring / integration-test AC.

See `sprint/context/context-story-153-12.md` for full details.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral engine bug (a succeeded ✦ resolution beat does not end a WN
`hp_depletion` confrontation). Reproduced through the real production dispatch.

**Test Files:**
- `tests/integration/test_153_12_swn_resolution_beat_exit.py` — drives the REAL
  space_opera pack through `dispatch_dice_throw` (the production dice seam). 6 tests.

**Root cause (verified during RED):** under `WithoutNumberRulesetModule` +
`win_condition=hp_depletion`, `dice._apply_committed_player_beat` routes every beat
through `_resolve_wn_committed_action` (ADR-143 native-engine cut). That helper resolves
ONLY via the strike→HP channel + `check_hp_depletion`; it has no resolution-beat branch.
A `push`/`retreat` beat carries `damage_channel=none`, so `hp_removed=0`, nobody hits
0 HP, `resolved=False` — and the native `beat_kinds.apply_beat` resolution branch
(which ends the fight on a resolution beat) is removed from the WN path. Fix belongs in
the shared `_resolve_wn_committed_action`.

**Tests Written:** 6 tests covering 6 ACs.

| Test | AC |
|------|----|
| `test_succeeded_resolution_beat_ends_confrontation` | AC1 (+AC6 wiring) — RED |
| `test_succeeded_resolution_beat_closes_the_beat_pool` | AC1 (pool no longer offered) — RED |
| `test_failed_resolution_beat_keeps_confrontation_active` | AC2 — **GREEN guard** (Fail must not exit) |
| `test_resolution_beat_exit_is_nonlethal_and_not_hp_depletion_win` | AC3 + AC4 — RED |
| `test_resolution_beat_exit_emits_resolved_span` | AC5 (OTEL lie-detector) — RED |
| `test_succeeded_resolution_beat_exits_on_legacy_immediate_path` | AC6 (shared seam: legacy path) — RED |

**Status:** RED — 5 failed, 1 passed (`pytest tests/integration/test_153_12_swn_resolution_beat_exit.py`).
The 5 failures assert on the bug (`enc.resolved` stays False / no `encounter.resolved`
span); the captured span trace confirms the real production WN sealed round engaged
(`swn.round.committed` → `encounter.beat_applied` → `encounter.opponent_attack_resolved`
[the erroneous reprisal that should not fire] → `swn.round.resolved`). The 1 GREEN test is
the AC2 tier-gate guard (a CritFail Fall Back correctly does not exit, today and after the fix).

### Rule Coverage

Applicable lang-review rules for a test-authoring (RED) phase — only #6 (Test quality)
governs TEA output; #1–5 target production code Dev writes.

| Rule | Coverage | Status |
|------|----------|--------|
| #6 Test quality — no vacuous asserts | every test asserts a specific value (`is True`/`is False`, HP>0, dial==0, `outcome` regex, span presence); no `assert True`/truthy-only | pass |
| #6 Test quality — no source-text wiring | wiring proven by behavior + OTEL span assertions (`encounter.resolved`/`encounter.beat_applied`), never by grepping source (CLAUDE.md No-Source-Text-Wiring) | pass |
| Wiring test present | full-pipeline test drives `dispatch_dice_throw` (the production seam), not the fix helper in isolation (AC6) | pass |
| OTEL observability | AC5 test asserts the `encounter.resolved` watcher span fires marking the non-lethal exit | pass |

**Rules checked:** 1 of 1 TEA-applicable lang-review rules (#6) has coverage; production
rules #1–5 deferred to Dev's GREEN self-review.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for GREEN — add the tier-gated resolution-beat exit to
`_resolve_wn_committed_action` (see Delivery Findings for the AC2 tier-gate constraint).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/server/dispatch/dice.py` — `_resolve_wn_committed_action`: threaded a new
  `outcome_tier: RollOutcome` parameter through (from the call site in
  `_apply_committed_player_beat`) and added a tier-gated ✦ resolution-beat exit. A
  ✦-marked beat (`beat.resolution`) at `Success`/`CritSuccess` now sets
  `encounter.resolved=True`, `outcome="resolution_beat:<id>"`,
  `structured_phase=Resolution`, and emits an `encounter` `wn_resolution_beat_exit`
  watcher event. HP-depletion still takes precedence (a kill wins over a withdrawal);
  a `Fail`/`CritFail` disengage leaves combat live; no dial is moved (ADR-143).

**Implementation note (design choice):** the exit gates on the explicit `beat.resolution`
flag (the authored ✦ marker — `combat::retreat` and `ship_combat::disengage` both carry
`resolution: true`), NOT on the native push-kind→`deltas.resolution` mapping. The WN-native
path computes no deltas (ADR-143), so the authored flag is the authoritative ✦ signal —
consistent with the story's "✦-marked resolution beat" framing. Honored TEA's tier-gate
finding (Success/CritSuccess only).

**Tests:** 6/6 passing on `tests/integration/test_153_12_swn_resolution_beat_exit.py` (GREEN).
Blast-radius regression sweep (WN combat / dice dispatch / encounter resolution / hp_depletion
/ apply_beat): **100/100 passing** — `test_108_1`, `test_108_8`, `test_106_1/2`,
`test_opponent_reprisal_e2e`, `test_encounter_init_hp_depletion`, `test_apply_beat_hp_depletion`,
`test_hp_depletion`, `test_apply_beat`. Ruff clean; pyright introduces 0 new errors (19
pre-existing in untouched code, identical with the change stashed).

**Full-suite caveat (NOT a regression — see Delivery Findings):** `uv run pytest` reports
156 failures (91 failed + 65 error). ALL are a **pre-existing** Fate-pack-loader validation
error (`genre/loader.py:301`, ADR-144 — Fate packs default to `beat_selection`, which the
Fate validator rejects) affecting `pulp_noir`/`spaghetti_western`/`wry_whimsy` and the
cascading epic-157 zoned-world tests (`gulliver`/`oz`/`wonderland`). Proven independent of
this change: stashing `dice.py` leaves the identical failure set, and the failing path
(pack load) is upstream of the WN-only dispatch seam I touched. Not in 153-12 scope.

**Branch:** `feat/153-12-swn-resolution-beat-no-exit` (pushed to origin).

**Handoff:** To Reviewer (Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (minor smell) | confirmed 1 (LOW), dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via `workflow.reviewer_subagents.edge_hunter` — domain covered by Reviewer directly |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer directly |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 5 (2 MED, 3 LOW), dismissed 0, deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 (LOW), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer directly |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer directly |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain covered by Reviewer directly |
| 9 | reviewer-rule-checker | Yes | findings | 2 (16 rules, 47 instances) | confirmed 2 (both LOW after verify), dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled per settings)
**Total findings:** 10 confirmed (2 MEDIUM, 8 LOW), 0 dismissed, 0 deferred — **zero Critical/High**

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** The implementation is correct and meets all six ACs. The fix is a minimal,
ADR-143-faithful re-introduction of the SRD Disengage result into the shared WN-native
seam (`_resolve_wn_committed_action`), proven by 6 tests through the real production
dispatch and a 100/100 WN-combat/dice/encounter regression sweep. Every finding the
specialists surfaced is test-robustness or cosmetic-doc polish — **none is a correctness
defect, none is Critical/High.** Per the project's severity-based blocking rule, those do
not block; I confirm (do not dismiss) each and log a non-blocking hardening follow-up.

**Data flow traced:** player throws `retreat` (face 20) → `dispatch_dice_throw` resolves
`CritSuccess` → SWN+`hp_depletion` → sealed commit → `run_wn_round` → `_apply_committed_player_beat(outcome_tier=CritSuccess)` → `_resolve_wn_committed_action` → resolution branch fires
(`beat.resolution` ∧ CritSuccess) → `encounter.resolved=True`, `outcome="resolution_beat:retreat"`, `wn_resolution_beat_exit` event → returns `resolved=True` → `_emit_player_beat_resolution_close` fires the durable `encounter.resolved` row carrying the outcome → opponent slot
skipped (`encounter.resolved`). End-to-end correct and non-lethal.

### Observations

- `[VERIFIED][RULE]` **ADR-143 "Bind the Ruleset, Don't Balance It" — clean.** The resolution
  branch (`dice.py:1399-1408`) mutates ONLY `encounter.resolved`/`outcome`/`structured_phase`;
  it does NOT advance `player_metric`/`opponent_metric` (the inert hp_depletion sentinel dials),
  grant tags, or invoke any dial/composure/edge rider. It models the SRD disengage result, not
  a native mechanic. Confirmed by rule-checker rule 16 and my own line trace. This is the
  load-bearing rule for this change and it is satisfied.
- `[VERIFIED][EDGE]` **HP-kill precedence + double-resolve guard.** `not resolved and not encounter.resolved` after `check_hp_depletion` (`dice.py:1399-1401`) means a same-beat kill wins
  over a withdrawal, and an already-resolved encounter can't re-resolve. Opponent reprisals run
  through a different path (`_resolve_opponent_reprisal`), so the exit is player-only — matches
  the story's "opponent resolution beats out of scope."
- `[VERIFIED]` **Tier gate correct.** `outcome_tier in (RollOutcome.Success, RollOutcome.CritSuccess)` (`dice.py:1402-1403`) — Success/CritSuccess end, Fail/CritFail and Tie leave combat
  live (Tie is consistent with native push semantics, which give no resolution at Tie). Pinned
  by `test_failed_resolution_beat_keeps_confrontation_active` (CritFail).
- `[VERIFIED][SILENT]` **No silent fallbacks.** `getattr(beat, "resolution", False)` (`dice.py:1402`)
  is a safe optional-attr read on a BeatDef field with a defined default, not a masked alternative
  code path; no exception handling was added (rule-checker rule 1: 0 violations).
- `[VERIFIED][TYPE]` **Type-clean boundary.** New `outcome_tier: RollOutcome` is fully annotated,
  keyword-only, and the single call site (`dice.py:1747`) passes the matching `RollOutcome`. Pyright:
  0 new errors (19 pre-existing in untouched code).
- `[VERIFIED][SEC]` **No security surface.** `beat_id` in the `f"resolution_beat:{beat_id}"` outcome
  is validated upstream (membership in `cdef.beats` at dispatch entry), `outcome_tier` is enum-gated;
  no injection/auth/tenant concern (rule-checker rule 11: compliant).
- `[MEDIUM][TEST]` **Plain `Success`/`Fail` tiers untested** (test file). Only crit faces (20/1)
  are exercised; AC1's "Success" half is not independently pinned — a hypothetical narrowing of the
  gate to `== CritSuccess` would still pass all six tests. The implementation is correct (the gate
  includes Success); this is a test-coverage gap, not a bug. Non-blocking; logged for hardening.
- `[MEDIUM][TEST]` **`ship_combat::disengage` untested** (test file). The other authored `resolution: true`
  beat routes through the same `_resolve_wn_committed_action` path and is not exercised — a future
  content change to one beat's flag wouldn't be caught. Same code path, so the fix covers it; the
  gap is regression-robustness. Non-blocking; logged for hardening.
- `[LOW][TEST][RULE]` **Tautological dial assertion** (`test file ~365-368`): `current < threshold`
  is trivially true once `current == 0` (the prior assertion). Matches lang-review #6 (vacuous
  assertion) — **confirmed, not dismissed.** Better: assert `threshold == HP_DEPLETION_SENTINEL`
  (proves the dial wasn't moved down). Non-blocking.
- `[LOW][TEST]` **`_RESOLUTION_EXIT_RE` over-matches** (`test file:77`): the alternation includes
  `retreat`, which is also the `beat_id`, so `resolution_beat:retreat` matches twice and a wrong
  `retreat_aborted` would pass. Tighten to `outcome.startswith("resolution_beat:")`. Non-blocking.
- `[LOW][TEST]` **AC5 span test omits a `source` assertion** — would catch a mislabeled seam. Optional.
- `[LOW][DOC]` **`_personal_combat_cdef` docstring says "fail loud" but returns `None` silently**
  (`test file:97`) — the loud assert is in the caller `_require_pack`. Cosmetic; reword. Non-blocking.
- `[LOW][DOC]` **Comment names "Pelä-menäy" but fixture uses `OPPONENT = "Pela"`** (`test file:46`)
  — cosmetic, fixture is self-consistent. Non-blocking.
- `[LOW][RULE]` **`op="wn_resolution_beat_exit"` not in `_KIND_BY_OP`** (`watcher_hub.py:479`) → the
  decision event fires on the live OTEL wire but is not persisted to the durable encounter-events
  table. **Downgraded from MEDIUM after verification:** `_KIND_BY_OP` is a curated allowlist, and
  sibling decision events in the same file (`shock_chip_applied`, `damage_roll_resolved`,
  `unarmed_strike_floor`, `damage_spec_missing`) are also live-wire-only by design. AC5's *durable*
  distinction is carried by the registered `resolved` row (`outcome="resolution_beat:<id>"` →
  `ENCOUNTER_RESOLVED`), which the GM-panel forensic timeline reads. Optional improvement: register
  the op for a durable decision row (ADR-124 forensic completeness). Non-blocking.
- `[LOW][SIMPLE]` **Dead `hasattr(outcome_tier, "value")` guard** (`dice.py:~1419`) — `RollOutcome`
  is `str`+`Enum`, so `.value` always exists. Consistent with existing file idiom (lines 1724, 1831),
  so not a regression, but the `else str(...)` branch is unreachable. Non-blocking.

### Rule Compliance

Checked against `.pennyfarthing/gates/lang-review/python.md` (#1–12) + CLAUDE.md/SOUL.md rules.

| Rule | Instances in diff | Verdict |
|------|-------------------|---------|
| #1 Silent exception swallowing | 0 added (no try/except in new code) | compliant |
| #2 Mutable default args | new param has no default; keyword-only | compliant |
| #3 Type annotations at boundaries | `outcome_tier: RollOutcome` annotated; return `-> ApplyResult` | compliant |
| #4 Logging coverage/correctness | `_watcher_publish` `severity="info"` for a non-error decision | compliant |
| #5 Path handling | no path ops | N/A |
| #6 Test quality | 6 tests assert specific values; **1 tautological assertion** (LOW finding above) | 1 LOW violation (confirmed) |
| #7 Resource leaks | no handles/connections/locks | N/A |
| #8 Unsafe deserialization | no pickle/yaml.load/eval | N/A |
| #9 Async pitfalls | functions are sync | N/A |
| #10 Import hygiene | no new imports (RollOutcome/EncounterPhase pre-imported) | compliant |
| #11 Input validation at boundaries | `beat_id`/`outcome_tier` validated upstream + enum-gated | compliant |
| #12 Dependency hygiene | no dep changes | N/A |
| SOUL/ADR-143 "Bind, don't Balance" | no dial moved, SRD result only | **compliant** (load-bearing) |
| OTEL Observability Principle | decision emits `wn_resolution_beat_exit`; durable `resolved` row | compliant (durability: LOW finding) |
| No Silent Fallbacks | safe optional-attr read, no masked path | compliant |
| No Source-Text Wiring Tests | tests use dispatch + OTEL spans, not source grep | compliant |
| Every suite needs a wiring test | drives production `dispatch_dice_throw`; (handler-level wire test absent — LOW, peer-consistent) | compliant at dispatch seam |

### Devil's Advocate

Suppose this code is broken. The most dangerous failure mode for a *combat-exit* feature is a
**false exit** — ending a fight that should continue — because it hands the player a free escape and
silently voids the threat (worse than the original soft-lock). Could a non-resolution beat trip the
branch? No: it is gated on `getattr(beat, "resolution", False)`, and only the authored `retreat`/`disengage`
beats carry the flag; a `shoot`/`take_cover` beat reads `False` and the branch is skipped (verified by
the 100/100 strike-path regression sweep — no strike test newly resolves). Could a *failed* disengage
escape? No: the `outcome_tier in (Success, CritSuccess)` gate excludes Fail/CritFail/Tie, and the AC2
test pins CritFail-does-not-exit. Could the *opponent's* beat trigger a player exit? No — opponent beats
resolve via `_resolve_opponent_reprisal`, never `_resolve_wn_committed_action`. Could it double-fire and
corrupt the `resolved` state? The `not resolved and not encounter.resolved` guard blocks re-entry, and a
resolved encounter rejects further throws at dispatch (`requires an active encounter`, pinned by the
pool-closed test). Could a same-round HP kill be masked by the disengage? No — `check_hp_depletion`
runs first and sets `resolved=True`, so the resolution branch is skipped (kill precedence). What about a
*confused* author who renames `resolution` to `is_resolution` in content? Then `getattr(...,"resolution",False)`
silently reads False and the exit dies again — that is the regression the `ship_combat`/plain-tier test
gaps fail to guard, which is exactly why I logged them (non-blocking). What about telemetry lying? The
live `wn_resolution_beat_exit` event isn't durable, but the registered `resolved` row carries
`outcome="resolution_beat:<id>"`, so the GM-panel forensic timeline can still distinguish a disengage from
an HP kill — the lie-detector holds. Stressed inputs (None beat, missing stat) raise upstream at dispatch,
not here. Conclusion: the failure modes I can construct are either blocked by the guards or are the
already-logged test-robustness gaps. No new finding emerges; the implementation is sound.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): the native `beat_kinds.apply_beat` resolution branch fires
  on the *unconditional* `beat.resolution=True` flag (any tier), but story AC1/AC2 require
  the WN-native fix to be **tier-gated** (Success/CritSuccess ends; Fail/CritFail does NOT).
  A naive port of the native unconditional behavior into `_resolve_wn_committed_action`
  passes AC1 but FAILS `test_failed_resolution_beat_keeps_confrontation_active` (AC2).
  Gate the exit on `outcome_tier in (Success, CritSuccess)`. Affects
  `sidequest/server/dispatch/dice.py::_resolve_wn_committed_action`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the same dead exit affects BOTH SWN resolution beats —
  `space_opera` authors `combat::retreat` (Fall Back) AND `ship_combat::disengage`, both
  `resolution: true`. The fix in `_resolve_wn_committed_action` is shared by both encounter
  types and by every WN-family pack (swn/wwn/cwn/awn) under `hp_depletion`; no per-beat-id
  special-casing should be needed. *Found by TEA during test design.*
- **Gap** (non-blocking): AC5 asks the exit-reason span to carry `reason=resolution_beat`
  "or equivalent". `_emit_player_beat_resolution_close` already emits `encounter.resolved`
  with `outcome`; the native engine stamps `enc.outcome = "resolution_beat:<id>"`, so
  mirroring that in the WN path makes the exit distinguishable from an hp-depletion win
  with no new span field. Affects `dice.py::_resolve_wn_committed_action`. *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (non-blocking, OUTSIDE 153-12 scope): the full server test suite is RED at
  the baseline — 156 failures (91 failed + 65 error), ALL from a Fate-pack-loader
  validation error (`sidequest/genre/loader.py:301`, ADR-144): Fate-bound packs
  (`pulp_noir`, `spaghetti_western`, `wry_whimsy`) author confrontations that default to
  `beat_selection`, which the Fate validator rejects; the epic-157 zoned-world tests
  (`gulliver`/`oz`/`wonderland`) cascade from the same load failure. Proven pre-existing
  and independent of this story (stashing the `dice.py` change leaves the identical failure
  set). This blocks the `gates/tests-pass` full-suite check for ANY story on this baseline
  until the Fate packs are migrated to `contest`/`conflict`/`table_resolution` resolution
  modes (epic-144/157 work). Affects `sidequest-content/genre_packs/{pulp_noir,
  spaghetti_western,wry_whimsy}/rules.yaml` (add explicit non-dial `resolution_mode` to
  each Fate confrontation) or the validator's strictness. *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): fast test-hardening follow-up for the 153-12 suite —
  (a) add a plain-`Success` and a plain-`Fail` tier test (the gate is `in (Success, CritSuccess)`;
  only crit faces are exercised, so AC1's Success half is unpinned and a `== CritSuccess` narrowing
  would pass); (b) tighten the AC3/AC5 outcome check to `outcome.startswith("resolution_beat:")`
  (the `_RESOLUTION_EXIT_RE` alternation includes `retreat`, which is the `beat_id`, so it
  double-matches); (c) replace the tautological dial assertion (`current < threshold` given
  `current == 0`) with `threshold == HP_DEPLETION_SENTINEL`; (d) add a `ship_combat::disengage`
  exit test (same shared path, currently untested). Affects
  `tests/integration/test_153_12_swn_resolution_beat_exit.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): register `op="wn_resolution_beat_exit"` in `_KIND_BY_OP` so the
  resolution-beat-exit *decision* gets a durable forensic row (ADR-124), not just the live OTEL wire.
  AC5 is already met via the durable `resolved` row (`outcome="resolution_beat:<id>"`), and the new
  op is consistent with sibling live-only events, so this is optional polish. Affects
  `sidequest/telemetry/watcher_hub.py::_KIND_BY_OP`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): remove the dead `hasattr(outcome_tier, "value")` guard in the
  `wn_resolution_beat_exit` watcher payload (`RollOutcome` is `str`+`Enum`; `.value` always exists).
  Matches existing file idiom, so cosmetic. Affects `sidequest/server/dispatch/dice.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec. All six ACs have test coverage; tier representatives use the
  guaranteed-crit faces (20→CritSuccess, 1→CritFail) rather than DC-borderline Success/Fail
  faces — this pins the tier gate deterministically without depending on the computed beat
  DC, and the plain Success/Fail tiers resolve identically per the gate (Spec source:
  context-story-153-12.md AC1/AC2; minor; forward impact: none).

### Dev (implementation)
- No deviations from spec. The fix implements all six ACs as written: tier-gated ✦ exit
  (gated on the authored `beat.resolution` flag + Success/CritSuccess), non-lethal
  `resolution_beat:<id>` outcome distinct from an hp_depletion win, no native dial moved,
  the `wn_resolution_beat_exit` watcher event, and coverage of both the sealed-round and
  legacy-immediate WN paths via the shared `_resolve_wn_committed_action`.

### Reviewer (audit)
- **TEA "No deviations" (crit-face tier representation)** → ✓ ACCEPTED by Reviewer: using
  guaranteed-crit faces (20/1) to pin the tier gate deterministically is a sound choice. Caveat,
  not a reversal: it leaves AC1's plain-`Success` half unexercised (a `== CritSuccess` narrowing
  would pass) — documented by TEA, and logged by me as a non-blocking test-hardening Improvement.
  The choice was disclosed, so it is an accepted documented deviation, not an undocumented gap.
- **Dev "No deviations"** → ✓ ACCEPTED by Reviewer: the implementation matches all six ACs; the
  design choice to gate on the authored `beat.resolution` flag (vs the native push→`deltas.resolution`
  mapping) is correct for the WN-native path, which computes no deltas (ADR-143). Verified against
  the code (`dice.py:1399-1408`).
- No undocumented deviations found. The implementation does not diverge from spec; all gaps surfaced
  in review are test-robustness/observability polish, logged as non-blocking Delivery Findings.