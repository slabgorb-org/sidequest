---
story_id: "158-30"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-30: Dogfight lifecycle — region drift must not resurrect a resolved/reaped duel (ADR-153 Plan 2)

## Story Details
- **ID:** 158-30
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/158-30-dogfight-region-drift-lifecycle (sidequest-server, gitflow)
- **Branch Strategy:** gitflow (feat/{STORY_ID}-{SLUG})

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-27T13:30:33Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T13:01:24+00:00 | 2026-06-27T13:04:25Z | 3m 1s |
| red | 2026-06-27T13:04:25Z | 2026-06-27T13:13:02Z | 8m 37s |
| green | 2026-06-27T13:13:02Z | 2026-06-27T13:21:50Z | 8m 48s |
| review | 2026-06-27T13:21:50Z | 2026-06-27T13:30:33Z | 8m 43s |
| finish | 2026-06-27T13:30:33Z | - | - |

## Sm Assessment

**Routing:** Picked up as the next story in epic 158 per Citizen request. Two p1 stories were open (158-30, 158-41); 158-30 wins as the direct continuation of the just-landed ADR-153 work — Plan 1 (the firewall, 158-31) merged in the last commit, and this story is Plan 2 (lifecycle), whose own description says "build Plan 1 first." 158-41 (general narrator max_turns robustness) is more orthogonal and can follow. No `depends_on`, no Jira key (consistent with the epic-158 arc). Merge gate clear: 0 in-progress, 0 in-review, clean tree.

**What this story fixes:** A dogfight that has RESOLVED (active=False) gets resurrected the *same turn* it's reaped. At turn start `encounter.husk_reaped` correctly clears the resolved encounter, but later that same turn `encounter.continued_same_region_drift` (location-label drift, e.g. Kestrel→Cold Contact) re-attaches it and resets `structured_phase` Resolution→Setup. The player is soft-locked into ship-maneuver beats while on foot in a derelict, Enter disabled. Two lifecycle rules disagree (husk_reaped clear vs drift keep-alive) and drift wins.

**Required behavior:** `continued_same_region_drift` must carry over **only a LIVE encounter** — never re-attach a resolved/reaped one — and must respect the `created_turn` fresh-this-turn exemption, so a finished dogfight stays finished. The fix makes husk_reaped win for resolved/reaped encounters (e.g. a one-turn `husk_reaped_this_turn` marker the drift check honors).

**For TEA (Igor):** Full technical approach + AC1–AC8 are in `sprint/context/context-story-158-30.md`, sourced from ADR-153 Plan 2 (lifecycle). Server-only change. Per CLAUDE.md: include a wiring test (drift path is reachable from production turn-start, not just unit-tested), OTEL assertions on the lifecycle decision (husk_reaped vs drift keep-alive), and no stubs/silent fallbacks. The deterministic clear is the loud, observable behavior — emit a span when a reaped encounter is *prevented* from drifting back.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New lifecycle behavior (a transient marker field + a seater guard + an observable refusal event) — a textbook TDD target.

**Test Files:**
- `sidequest-server/tests/server/dispatch/test_dogfight_husk_no_resurrect.py` — reap→re-seat lifecycle guard, driven through the real production seater

**Tests Written:** 4 tests covering AC1, AC4, AC5, AC7 + the created_turn turn-keying exemption
**Status:** RED (3 failing for feature-absent reasons, 1 passing as a turn-keying regression guard) — verified by testing-runner

| Test | AC | Today | Why |
|------|----|-------|-----|
| `test_reaped_dogfight_does_not_reseat_same_turn` | AC4 | **FAIL** | re-seat currently succeeds; `result is None` fails (the soft-lock repro) |
| `test_fresh_dogfight_still_seats_when_not_reaped_this_turn` | AC5 + AC1 | **FAIL** | `AttributeError`: `GameSnapshot.husk_reaped_this_turn` not defined yet |
| `test_reaped_marker_from_prior_turn_does_not_block_later_seat` | exemption | PASS | no guard today → seats trivially; locks the fix to `(type, turn)` keying |
| `test_reseat_refusal_emits_observable_watcher_event` | AC7/AC8 | **FAIL** | no `reseat_refused_husk_reaped` event fires today |

**Regression check:** `test_encounter_husk_reap.py` (4) + `test_dogfight_default_opponent.py` (1) → **5/5 pass** with the new file present; clean collection, no import/fixture errors.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #6 test-quality (no vacuous assertions; spy patches the module-local `_watcher_publish` — correct target, where-used not where-defined) | self-check across all 4 tests | pass (self-check clean) |
| #1 silent-exceptions → SOUL/CLAUDE.md **No Silent Fallbacks** (AC8): the refusal must be observable, never silent | `test_reseat_refusal_emits_observable_watcher_event` | failing (RED) |

**Rules checked:** 2 of 13 lang-review rules apply to this test design. The remaining 11 (#2 mutable defaults, #3 type annotations, #4 logging, #5 path handling, #7 resource leaks, #8 deserialization, #9 async, #10 imports, #11 input validation, #12 deps, #13 fix-regressions) are dev-implementation concerns — the expected fix adds a pydantic field + an in-function guard with one watcher emit, touching no I/O, async, deserialization, or path handling, so there is no test-design surface for them. Dev's self-review will run them against the implementation diff.
**Self-check:** 0 vacuous tests found (every assertion checks a specific value; no `assert True`, no truthy-on-always-None, no `let _ =`).

**Handoff:** To Dev (Ponder Stibbons) for implementation — AC1 (field on `GameSnapshot`), AC2 (stamp in `reap_resolved_encounter_husk`), AC3 (turn-keyed guard + `reseat_refused_husk_reaped` emit in `instantiate_encounter_from_trigger`). The four tests are the GREEN target; do not weaken the turn-keying test.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/session.py` — AC1: added `GameSnapshot.husk_reaped_this_turn: tuple[str, int] | None = Field(default=None, exclude=True)`. Transient per-turn marker; `exclude=True` keeps it out of `model_dump_json` (non-durable, matching the established S5 transient-queue pattern at lines 1117–1125).
- `sidequest-server/sidequest/server/dispatch/encounter_lifecycle.py` — AC2: `reap_resolved_encounter_husk` stamps `(enc.encounter_type, turn)` immediately before `snapshot.encounter = None`. AC3: `instantiate_encounter_from_trigger` gained a turn-keyed guard right after the resolved-same-type guard — if `husk_reaped_this_turn` matches `(encounter_type, turn_manager.interaction)` it emits a `reseat_refused_husk_reaped` state_transition (component=encounter) and returns `None`.

**Design notes:**
- The marker is keyed by `(type, turn)`, so the created_turn exemption is preserved by construction — a later-turn duel has a mismatched turn and seats normally. No explicit turn-boundary clear is needed: each reap re-stamps, and `exclude=True` prevents persistence, so a stale marker can never leak across resume or across turns as a false block.
- The refusal is observable (OTEL watcher event), never silent — satisfies AC7/AC8 and CLAUDE.md No Silent Fallbacks.
- Minimal change: a field + a stamp + an in-function guard. No new abstractions, no refactor of adjacent code.

**Tests:** 4/4 passing (GREEN), verified by testing-runner. Regression: 139 encounter/dogfight/lifecycle dispatch tests pass; wider sweep 4039 passed / 0 failed (66 skipped; one parallel-only dice-resolution isolation flake unrelated to this change, passes serially). ruff clean. pyright: my added lines (session.py:889, encounter_lifecycle.py:210/1577/1587) introduce zero new errors — all reported errors are pre-existing elsewhere in the files.
**Branch:** feat/158-30-dogfight-region-drift-lifecycle (pushed)

**Handoff:** To verify/review phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN 4/4, 139 regression, ruff clean, 0 new pyright, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by Reviewer directly (turn-keying boundary verified) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 1 (LOW, non-blocking), dismissed 2 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — test quality verified by Reviewer (see Rule Compliance #6) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — comments verified accurate by Reviewer |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — type design verified by Reviewer (see Rule Compliance #3) |
| 7 | reviewer-security | Yes | findings | 1 | confirmed 1 (MEDIUM, non-blocking → follow-up) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — change is already minimal (field + stamp + guard) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — full python.md enumeration done by Reviewer (Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents` and pre-filled)
**Total findings:** 2 confirmed (both non-blocking), 2 dismissed (with rationale), 0 deferred, 0 blocking

## Reviewer Assessment

**Verdict:** APPROVED

**Summary:** A minimal, correct, well-wired lifecycle guard — a field + a stamp + an in-function guard. Functional correctness is verified end-to-end (two independent wiring traces below). The two confirmed findings are non-blocking observability/defense-in-depth refinements that match existing accepted codebase patterns; both are routed to delivery findings for a follow-up. No Critical or High issues.

**Data flow traced (wiring #1 — the turn axis):** `websocket_session_handler.py:794` calls `reap_resolved_encounter_husk(snapshot, is_dice_replay=..., turn=snapshot.turn_manager.interaction)` at turn start → the stamp writes `(enc.encounter_type, turn)` → the seater guard reads `snapshot.turn_manager.interaction`. The producer and consumer read the **same** turn value live, so the guard genuinely fires in production (not a test-only no-op). Safe.

**Data flow traced (wiring #2 — the seating chokepoint):** A fresh encounter is written to `snapshot.encounter` at exactly two sites (`encounter_lifecycle.py:1657` table path, `:2180` dial/sealed-letter path) — **both inside `instantiate_encounter_from_trigger`, both after the guard at :1577**. A repo-wide grep across `server/` and `agents/subsystems/` confirms there is no other fresh-encounter write site (`narration_apply.py`'s `continued_same_region_drift` only mutates `.resolved`/`.outcome`/`.structured_phase` on an already-live encounter — guarded by `active_encounter is not None and not resolved` at :4838 — it never constructs one). Therefore a duel reaped this turn cannot be re-seated through any path. The reported symptom (a *fresh* encounter reset to *Setup*) is only producible by the seater, which is now guarded. Fix correctly located.

**Pattern observed:** `husk_reaped_this_turn: tuple[str,int] | None = Field(default=None, exclude=True)` (session.py:889) follows the established transient-field pattern (the S5 queues at session.py:1135-1136). The stamp-before-clear ordering (encounter_lifecycle.py:210 → :211) is correct: the marker is written before the slot is nulled.

**Error handling:** The guard returns `None` *with* an observable `reseat_refused_husk_reaped` watcher event (encounter_lifecycle.py:1583) — never a silent return. Satisfies AC7/AC8 and the No-Silent-Fallbacks doctrine.

### Observations

- [VERIFIED] Production turn-axis wiring — evidence: `websocket_session_handler.py:794` passes `turn=snapshot.turn_manager.interaction`; guard at `encounter_lifecycle.py:1579` compares the same field. Complies with the story's turn-keying contract.
- [VERIFIED] Seater is the sole fresh-encounter chokepoint — evidence: grep shows `snapshot.encounter = <fresh>` only at `encounter_lifecycle.py:1657` and `:2180`, both after the guard at `:1577`. Universal coverage.
- [VERIFIED] Created_turn exemption is turn-keyed, not type-only — evidence: guard requires `reaped[0]==encounter_type AND reaped[1]==interaction` (`encounter_lifecycle.py:1578-1581`); `test_reaped_marker_from_prior_turn_does_not_block_later_seat` exercises a later-turn seat. No over-blocking of fresh duels.
- [VERIFIED] Non-durable on the normal save path — evidence: `Field(exclude=True)` (session.py:889) keeps the key out of `model_dump_json` (snapshot.py:83); a normal save→load round-trips to `None`. (See [SEC] for the crafted-save caveat.)
- [VERIFIED] Test suite is its own wiring test — evidence: all 4 tests in `test_dogfight_husk_no_resurrect.py` drive the real `instantiate_encounter_from_trigger`, not a mock; assertions check specific values (no vacuous asserts), and the watcher spy patches the module-local `_watcher_publish` (correct target).
- [SILENT] **Confirmed LOW (non-blocking):** dogfight force-dispatch double-signals a husk-reap refusal — `dogfight.py:169-178` emits a generic `dogfight_dispatch_rejected(reason="not_seated")` span in addition to the accurate `reseat_refused_husk_reaped` from the seater. The seat genuinely failed, so `not_seated` is true (not a *false* signal), just less specific, and it only triggers if a dogfight *verb* is used the same turn after a reap (the reported repro was a non-combat action, which never reaches this path). Routed to a delivery finding (Improvement).
- [SILENT] Dismissed: `confrontation.py:156` discards the seater's `None` return → `SubsystemOutput()` "phantom success." Rationale: pre-existing contract (the resolved-same-type guard at :1566 already returned `None` through this same call site); observability is delivered by the watcher event, which IS the lie-detector per CLAUDE.md OTEL doctrine — not the `SubsystemOutput`.
- [SILENT] Dismissed: dice-replay path skips the stamp. Rationale: by-design — on `is_dice_replay=True` the reap returns early and **keeps** the encounter (never clears it), so there is no cleared-but-re-seatable window to protect; documented in the reap docstring.
- [SEC] **Confirmed MEDIUM (non-blocking):** `exclude=True` governs serialization output, not validation input — `GameSnapshot.model_validate({"husk_reaped_this_turn": [...]})` *would* populate the field (config is `extra="ignore"`). A crafted/corrupted `snapshot_json` row could restore a stale marker and block the first seat on resume. **Not reachable on the normal path** (the key is never written); exploitation requires direct Postgres write access (a far larger compromise) or an adjacent migration/importer bug, and the effect is a transient, self-healing single-seat block (next turn the interaction advances and the marker goes stale). The **identical** structural exposure already exists for the two pre-existing sibling transient fields (session.py:1135-1136), so this story faithfully followed the accepted pattern rather than introducing a new defect. The proper hardening — a shared `@model_validator(mode="after")` that zeroes ALL transient markers on load — is cross-cutting and belongs in a follow-up, not bolted onto this one field. Routed to a delivery finding (Improvement).
- [TYPE] (subagent disabled) Verified by Reviewer: the new field is fully annotated (`tuple[str,int] | None`); the guard tuple-unpacks `reaped[0]/reaped[1]` after a `None` check — no unsafe access. No stringly-typed regression.
- [DOC] (subagent disabled) Verified by Reviewer: the three new comment blocks accurately describe the behavior (stamp-before-clear, turn-keying, exclude=True non-durability) and match the code. No stale/misleading comments.
- [SIMPLE] (subagent disabled) Verified by Reviewer: the change is already minimal — no dead code, no over-engineering, no abstraction beyond what the tests demand.
- [RULE] (subagent disabled) Verified by Reviewer: full python.md enumeration in Rule Compliance below — clean.

### Rule Compliance (python.md lang-review, enumerated against the diff)

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Silent exception swallowing | PASS | No try/except added; the guard returns `None` WITH a watcher event (encounter_lifecycle.py:1583). |
| 2 | Mutable default arguments | PASS | No new params; field uses `Field(default=None, ...)`, not a mutable default. |
| 3 | Type annotation gaps at boundaries | PASS | New field annotated `tuple[str,int] | None`; guard lives in an already-typed public fn. |
| 4 | Logging coverage/correctness | PASS (minor note) | Reap logs + watcher; the new guard emits a watcher event but no `_log.info`. Consistent with the sibling resolved-same-type guard (:1566), which emits neither — the watcher event is the required observability. A `_log.info` would be a nicety, not a requirement. |
| 5 | Path handling | N/A | No filesystem paths in the diff. |
| 6 | Test quality | PASS | 4 tests, specific assertions, correct monkeypatch target, no `assert True`/vacuous/always-None checks; the turn-keying test is a meaningful over-block guard. |
| 7 | Resource leaks | N/A | No file/socket/lock/db handles opened. |
| 8 | Unsafe deserialization | PASS (see [SEC]) | No pickle/yaml.load/eval. The marker is built from engine values; the deserialization caveat is the crafted-save [SEC] finding, not an unsafe-loader. |
| 9 | Async/await pitfalls | N/A | Seater and reap are sync; no async added, no blocking call introduced. |
| 10 | Import hygiene | PASS | No new imports — reuses module-local `Field` and `_watcher_publish`. |
| 11 | Input validation at boundaries | PASS | Marker values are engine-controlled (`encounter_type` str, `turn` int), not network input. |
| 12 | Dependency hygiene | N/A | No dependency changes. |
| 13 | Fix-introduced regressions | PASS | 139 lifecycle regression tests + 4039-test wide sweep green; 0 new pyright errors. |

### Devil's Advocate

Argue the code is broken. **First attack — the no-op fix.** If the production reap caller passed a `turn` that differed from `turn_manager.interaction`, the stamp and the guard would key on different integers, the guard would never match, and the bug would persist in production while all four tests passed (they pass `turn=interaction`). I treated this as the primary threat and traced it: `websocket_session_handler.py:794` passes `turn=snapshot.turn_manager.interaction` verbatim — the axes align. Refuted with evidence. **Second attack — the misplaced guard.** The story prose blames `continued_same_region_drift`, but the guard is in the seater. If the real resurrection re-attached the encounter by directly assigning `snapshot.encounter` (bypassing the seater), the guard would sit on a dead path. I grepped every `snapshot.encounter = <fresh>` write in `server/` and `subsystems/`: only two sites exist, both inside the guarded seater; the drift ladder never constructs an encounter. The symptom (fresh encounter in *Setup* phase) is itself a fingerprint of the seater, since the drift keep-alive preserves phase. Refuted. **Third attack — over-blocking.** A guard keyed on type alone would block a legitimately-new duel after a same-turn reap; the turn key prevents this, and a dedicated test proves a later-turn seat succeeds. **Fourth attack — the confused player / corrupted state.** What if a save is hand-edited? The [SEC] finding is exactly this: a crafted `snapshot_json` could inject a stale marker because pydantic `exclude` doesn't gate validation input. But this needs DB-write access or an adjacent bug, the blast radius is one self-healing seat-block, and it's the same exposure two existing fields already carry — proportionate to MEDIUM/non-blocking, not a release blocker. **Fifth attack — a stressed turn counter.** Could `interaction` ever reset or wrap, causing a stale marker to false-match a future turn? `turn.py` makes `interaction` monotonic (only `record_interaction` mutates it, always `+= 1`), so a stale `(type, N)` can never match a later turn. The honest conclusion: the functional core is sound and well-wired; the only real residue is defense-in-depth hardening best handled cross-cuttingly in a follow-up.

**Handoff:** To SM (Captain Carrot Ironfoundersson) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No upstream findings during test design. The two prerequisite merges (Plan 1 #1084 frame-default seating, 158-29 #1085) are present on the branch's `develop` base, the seater chokepoint (`instantiate_encounter_from_trigger`) is the universal seating path the guard belongs on, and the existing husk-reap / dogfight-seating suites are green. The fix is well-scoped and the AC code snippets match the real function shapes (verified `reap_resolved_encounter_husk` ~line 142, `instantiate_encounter_from_trigger` ~line 1486, resolved-same-type guard at line 1560).

### Dev (implementation)
- No upstream findings during implementation. The AC code snippets matched the real function shapes exactly, the non-durable requirement had an established `exclude=True` precedent in the same model, and GREEN landed with no source-side surprises. One observation for the reviewer (non-blocking, not a finding): `husk_reaped_this_turn` is intentionally never explicitly cleared at a turn boundary — staleness is handled by `(type, turn)` keying plus `exclude=True`, and each reap re-stamps. This is by design, not an omission.

### Reviewer (code review)
- **Improvement** (non-blocking): `exclude=True` prevents transient markers from being *written* to the save but does NOT prevent them being *restored* if a `snapshot_json` row already contains the key (pydantic `exclude` is serialization-only; `GameSnapshot` config is `extra="ignore"`). A crafted/corrupted save could restore a stale `husk_reaped_this_turn` and block the first encounter seat on resume. Affects `sidequest-server/sidequest/game/session.py` (add a shared `@model_validator(mode="after")` that zeroes ALL transient `exclude=True` markers — `husk_reaped_this_turn`, `pending_magic_auto_fires`, `pending_magic_confrontation_outcome` — on load, making the "never durable" invariant self-enforcing). Cross-cutting; not specific to this story. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): a husk-reap re-seat refusal during a dogfight force-dispatch emits a generic `dogfight_dispatch_rejected(reason="not_seated")` span in addition to the accurate `reseat_refused_husk_reaped` event, giving the GM panel two reads of one refusal. Affects `sidequest-server/sidequest/agents/subsystems/dogfight.py` (~line 169 — check `snapshot.husk_reaped_this_turn` and emit `reason="husk_reaped"` instead of the generic `not_seated` when that is the cause). Reachable only when a dogfight verb is used the same turn after a reap. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Seated the repro through the real production seater, not the context's illustrative helper**
  - Rationale: drives the actual production path (faithful repro + inherent wiring coverage), and avoids inventing a fixture helper that isn't in the tree
  - Severity: minor
  - Forward impact: none — same observable contract (reaped duel must not re-seat)
- **AC5 test also pins AC1 (field exists + defaults None)**
  - Rationale: one fewer trivial test; the field default is a precondition of "fresh seats with no marker," so asserting it here is natural and makes AC5 RED-for-the-right-reason today (AttributeError until AC1 lands)
  - Severity: minor
  - Forward impact: Dev must add the field (AC1) for this test to reach its seating assertion
- **Added a turn-keying exemption test not in the context's enumerated list**
  - Rationale: locks the fix to `(type, turn)` keying; a guard keyed on type alone would wrongly block here. This is the paranoid edge the prose calls out but the enumerated tests didn't cover. It's added coverage, not a reduction.
  - Severity: minor
  - Forward impact: Dev's guard must compare turn, not just type (the context's AC3 snippet already does)
- **AC6 (integration regression suite) verified by running existing suites, not a new test**
  - Rationale: writing a new test for "the old tests still pass" would be redundant; the run IS the check
  - Severity: minor
  - Forward impact: Dev/verify must re-run the husk/seat/dogfight suites after implementing

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Seated the repro through the real production seater, not the context's illustrative helper**
  - Spec source: context-story-158-30.md, AC4
  - Spec text: example used `enc = seat_live_dogfight(snapshot)` then `enc.resolved = True`
  - Implementation: `seat_live_dogfight` does not exist; I seat via the real `instantiate_encounter_from_trigger` (Plan-1 frame-default opponent) then resolve, in a `_seat_and_resolve_dogfight` helper
  - Rationale: drives the actual production path (faithful repro + inherent wiring coverage), and avoids inventing a fixture helper that isn't in the tree
  - Severity: minor
  - Forward impact: none — same observable contract (reaped duel must not re-seat)
- **AC5 test also pins AC1 (field exists + defaults None)**
  - Spec source: context-story-158-30.md, AC5
  - Spec text: AC5 example only asserts a fresh dogfight seats (`result is not None`)
  - Implementation: AC5 test additionally asserts `snapshot.husk_reaped_this_turn is None`, folding AC1's field-default into the same behavioral test
  - Rationale: one fewer trivial test; the field default is a precondition of "fresh seats with no marker," so asserting it here is natural and makes AC5 RED-for-the-right-reason today (AttributeError until AC1 lands)
  - Severity: minor
  - Forward impact: Dev must add the field (AC1) for this test to reach its seating assertion
- **Added a turn-keying exemption test not in the context's enumerated list**
  - Spec source: context-story-158-30.md, "The Fix: One-Turn Reaped Marker" + AC5 (created_turn exemption)
  - Spec text: "Keyed by turn so a stale marker from a prior turn is inert"
  - Implementation: added `test_reaped_marker_from_prior_turn_does_not_block_later_seat` — reap on turn N, advance to N+1, assert a fresh dogfight still seats
  - Rationale: locks the fix to `(type, turn)` keying; a guard keyed on type alone would wrongly block here. This is the paranoid edge the prose calls out but the enumerated tests didn't cover. It's added coverage, not a reduction.
  - Severity: minor
  - Forward impact: Dev's guard must compare turn, not just type (the context's AC3 snippet already does)
- **AC6 (integration regression suite) verified by running existing suites, not a new test**
  - Spec source: context-story-158-30.md, AC6
  - Spec text: "Run the existing husk-reap and encounter-seating tests to verify no regression"
  - Implementation: AC6 is a regression-run instruction, not a new test to author; testing-runner ran `test_encounter_husk_reap.py` + `test_dogfight_default_opponent.py` → 5/5 pass with the new file present
  - Rationale: writing a new test for "the old tests still pass" would be redundant; the run IS the check
  - Severity: minor
  - Forward impact: Dev/verify must re-run the husk/seat/dogfight suites after implementing

### Dev (implementation)
- No deviations from spec. AC1/AC2/AC3 implemented as written in context-story-158-30.md. The field's non-durability (AC1) uses `Field(default=None, exclude=True)` — the context required "not written to save files" without prescribing the mechanism, and `exclude=True` is the codebase's established transient-field pattern (session.py:1124–1125), so this is the faithful implementation, not a deviation. The AC2 stamp and AC3 guard match the context's code snippets (turn-keyed `(type, turn)` comparison, `reseat_refused_husk_reaped` watcher emit).

### Reviewer (audit)
- **Stamp the reaped (type, turn) before clearing; turn-keyed seater guard** → ✓ ACCEPTED by Reviewer: correctness verified by two independent wiring traces (production reap caller passes `turn=interaction`; the seater is the sole fresh-encounter chokepoint). Minimal and well-located.
- TEA deviation 1 (real production seater vs illustrative `seat_live_dogfight` helper) → ✓ ACCEPTED: more faithful repro + inherent wiring coverage; the named helper never existed.
- TEA deviation 2 (AC5 also pins AC1 field-default) → ✓ ACCEPTED: natural precondition, reduces a trivial extra test, still RED-for-the-right-reason pre-fix.
- TEA deviation 3 (added turn-keying exemption test) → ✓ ACCEPTED: added coverage that locks the `(type, turn)` invariant; not a reduction.
- TEA deviation 4 (AC6 verified by running suites, not a new test) → ✓ ACCEPTED: AC6 is a regression-run instruction; a "the old tests still pass" test would be redundant.
- Dev "no deviations" → ✓ ACCEPTED: implementation matches the context snippets; `exclude=True` is the faithful mechanism for the AC1 non-durable requirement.
- **UNDOCUMENTED — none.** No spec divergence escaped TEA/Dev logging. The [SEC] crafted-save caveat is a defense-in-depth property of the chosen pattern, not a spec deviation (AC1's "never restored" holds for the normal path).