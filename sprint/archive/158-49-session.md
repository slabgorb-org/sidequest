---
story_id: "158-49"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-49: Forced-dispatch dogfight (158-29/§7) crashes the SWN resolver: WWN STR/DEX default beats from beat_filter handed to SWN attack_params (KeyError stat 'STR') -> ws disconnect + confrontation soft-lock

## Story Details
- **ID:** 158-49
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-28T01:03:29Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-27T23:41:25+00:00 | 2026-06-27T23:44:59Z | 3m 34s |
| red | 2026-06-27T23:44:59Z | 2026-06-28T00:07:45Z | 22m 46s |
| green | 2026-06-28T00:07:45Z | 2026-06-28T00:34:41Z | 26m 56s |
| review | 2026-06-28T00:34:41Z | 2026-06-28T00:46:19Z | 11m 38s |
| red | 2026-06-28T00:46:19Z | 2026-06-28T00:51:01Z | 4m 42s |
| green | 2026-06-28T00:51:01Z | 2026-06-28T00:55:45Z | 4m 44s |
| review | 2026-06-28T00:55:45Z | 2026-06-28T01:03:29Z | 7m 44s |
| finish | 2026-06-28T01:03:29Z | - | - |

## Sm Assessment

**Story:** 158-49 (p1, 3pts, tdd, repo: sidequest-server). Branch `feat/158-49-forced-dispatch-swn-beat-set`, cut from fresh `origin/develop`. Jira disabled (no key). Merge gate clear at setup (no open PRs, nothing in review).

**Rescoped at setup — Keith's ruling 2026-06-27 ("proceed, rescoped").** The story's documented root cause is partially STALE. It records the crash as `KeyError stat 'STR'` because space_opera (SWN) had no STR/DEX in its stat block. But **PR #510 (the 158-51 WN-attribute canonicalization) merged to `origin/develop` at 21:21 the same day**, dropping the flavor names so space_opera now uses canonical STR/DEX/CON/INT/WIS/CHA. This branch includes #510, so `without_number._stat(stats,"STR")` should now resolve — the literal KeyError is very likely already gone. (Two clones briefly shared local id 158-49; the dogfight-crash story kept 158-49, the canonicalization renumbered to 158-51. See archived 158-51 session.)

**Rescoped target (full ACs + code refs in `sprint/context/context-story-158-49.md`):**
1. Forced-dispatch SWN dogfight must NOT crash the websocket or soft-lock the confrontation.
2. The seat must hand the SWN resolver a RULESET-VALID beat/maneuver set (real dogfight maneuvers from `dogfight/interactions_mvp.yaml` — Throttle Up / Break Right / loop / kill_rotation), NOT `beat_filter.py`'s WWN-default combat beats (Total Defense / Fighting Withdrawal / Run, stat_check STR/DEX).
3. If a valid set can't be produced, FAIL LOUD at SEAT time (No Silent Fallbacks), not silently at dice resolution.
4. OTEL watcher span at the forced-dispatch seating decision: which beat/maneuver set was surfaced + which ruleset module is bound (GM-panel lie detector).

**Out of scope (deferred to siblings):** wrong-Other (Gengineered Killer ground creature seated as ship) → 158-34; full relative-position positioning graph → 158-40.

**For Igor (RED phase):** Write the failing test reproducing the forced-dispatch SWN dogfight commit (solo space_opera/coyote_star, verbs intercept/lock/gun/missile → `intent_router.dogfight_forced_dispatch`, ADR-153 §7). Observe what actually happens post-#510 — may no longer crash, may crash on a different path, or may "succeed" while surfacing the wrong (WWN-default) beats. Lock the rescoped ACs into the RED test: no crash/soft-lock, ruleset-valid beat set OR fail-loud-at-seat, plus the OTEL span.

**Decision rationale:** TDD is the right shape here precisely because the crash premise is uncertain post-#510 — the RED test verifies real behavior rather than chasing a documented symptom that may no longer reproduce. Routing to TEA (red), no blockers.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): the documented root cause (`KeyError stat 'STR'`) is stale on LIVE content — #510 canonicalized space_opera to STR/DEX, so the literal crash no longer reproduces there. The RED suite reproduces it deterministically via the deliberately-flavor-keyed `tests/fixtures/packs/swn_test_pack` (158-51 deferred note). The structural bug (a sealed-letter dogfight handed the WN personal-combat menu) is the real target and is stat-name-independent. Affects `sprint/context/context-story-158-49.md` (the "SWN-valid stat_checks (Physique/Reflex/...)" framing is now wrong — canonical SWN has STR/DEX; the discriminator is beat IDENTITY, not stat name). *Found by TEA during test design.*
- **Gap** (non-blocking): the dogfight maneuver commit seam is unsettled — the interaction-table maneuvers (Throttle Up/Break Right/loop/kill_rotation) commit through the sealed-letter path, while the buggy "attack" goes through `dispatch_dice_throw`'s WN-action arm. The AC1/AC4 test commits the first offered beat via `dispatch_dice_throw`; Dev must decide whether 158-49 surfaces maneuvers as dispatch_dice_throw-committable beats or routes them through the sealed-letter seam (and the test's commit seam may follow). Affects `sidequest/server/dispatch/dice.py` + `sidequest/server/dispatch/confrontation.py` + `sidequest/game/beat_filter.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `tests/genre/test_dogfight_content_loading.py::test_dogfight_beats_cover_every_consumed_maneuver` and `::test_dogfight_has_dual_track_metrics` are STALE — they assert the pre-sealed-letter dogfight shape (a `beats:` list covering `maneuvers_consumed`; dual-track player/opponent metrics). #508 dropped the dogfight `beats:` list and made it `hp_depletion`, so both were ALREADY RED on develop before this story (verified by stashing this story's diff — they still fail). 158-49 establishes that the dogfight menu is synthesized from `maneuvers_consumed`, which supersedes the "beats ARE the maneuvers" content convention those tests enforce. Affects `tests/genre/test_dogfight_content_loading.py` (update to assert maneuvers come from the interaction table / drop the dual-track assertion). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the full server suite has ~52 pre-existing/environmental RED tests unrelated to this story (arc-recompute / arc-embedding / tension-tracker / lull-escalation / turn-record / turn-span / clue-discovery / player-turn-author wiring + wwn cast-spell dispatch + the two stale dogfight content-loading tests). Confirmed pre-existing by stashing this story's production diff and re-running — same failures on base; matches the 158-51 session's pre-existing-reds note. None are caused by 158-49. Affects the broad wiring-test harness (a separate triage/cleanup effort). *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking): sealed-letter dogfight maneuver beats receive a fabricated d20-vs-AC `difficulty` (the target's armor class) in the CONFRONTATION payload AND in the `confrontation.beat_dc_authored` OTEL span — a no-roll maneuver shown with a DC it never rolls, polluting the GM-panel lie-detector. Affects `sidequest/server/dispatch/confrontation.py` (skip `difficulty` for `resolution_mode == sealed_letter_lookup` in the per-beat loop at ~439-448, mirroring the `is_item_use_beat` skip). *Found by Reviewer during code review.* (This is the REJECT reason — see Reviewer Assessment.)
- **Improvement** (non-blocking): a sealed_letter_lookup cdef with a missing/empty `interaction_table` only fails at first menu build (`PackError` in `beats_available_for`), not at pack load. Affects `sidequest/genre/models/rules.py` `ConfrontationDef._validate` (add a load-time guard requiring sealed_letter_lookup to carry a non-empty `interaction_table.maneuvers_consumed`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the new `dispatch_dice_throw` rejection echoes player-controlled `payload.beat_id` into the client error string (consistent with existing `unknown beat_id` messages, so not a regression). Affects `sidequest/server/dispatch/dice.py` (optionally use a fixed message + log the beat_id server-side only). *Found by Reviewer during code review.*
- **Round 2 (re-review):** the blocking Conflict above is RESOLVED (the rework skips `difficulty` for sealed-letter maneuvers; regression-locked by the two new tests). The two non-blocking Improvements remain open follow-ups. No new upstream findings during the re-review. *Found by Reviewer during code review (round 2).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC3 (fail-loud-at-seat) given partial/indirect coverage, no dedicated unbuildable-set test**
  - Spec source: context-story-158-49.md, AC "No silent fallback ... fails loud at SEAT time"
  - Spec text: "if the seater cannot build a valid SWN/sealed-letter beat set it fails loud at SEAT time, not at dice-resolution time — the player is never handed an un-committable/crashing menu"
  - Implementation: covered indirectly — the integration test asserts the seated dogfight offers a non-empty menu AND committing the offered beat does not crash at dice time. No dedicated test constructs an "unbuildable beat set" and asserts a loud seat-time rejection.
  - Rationale: the trigger for "unbuildable" is design-dependent (what makes a sealed-letter maneuver set unavailable?); TEA cannot construct the failing input without prejudging Dev's GREEN shape.
  - Severity: minor
  - Forward impact: Dev should add a fail-loud-at-seat assertion once the seat-time validation path exists.
- **Rework (round-trip 1): no new deviations.** The Reviewer HIGH (no-roll sealed-letter maneuver tiles stamped with a fabricated d20 `difficulty`, polluting the `beat_dc_authored` span) is now locked by two new regression tests in `tests/server/dispatch/test_dogfight_swn_beat_set_158_49.py` — `test_dogfight_maneuver_tiles_carry_no_d20_difficulty` (payload tile carries no `difficulty`, the item-use no-DC contract) and `test_dogfight_beat_dc_authored_span_records_no_maneuver_dcs` (the lie-detector span names no maneuver). Both verified RED (`['straight','bank','loop','kill_rotation']` carry stamped DCs; span records `straight=10,bank=10,loop=10,kill_rotation=10`); 3 existing integration tests stay green. No spec deviation introduced. **Dev fix:** skip `difficulty` for `cdef.resolution_mode == ResolutionMode.sealed_letter_lookup` in `build_confrontation_payload`'s per-beat loop (`confrontation.py:~439-448`), mirroring the `is_item_use_beat` skip at line 446.

### Dev (implementation)
- **AC1/AC4 integration test commit seam changed from `dispatch_dice_throw` to the sealed-letter path**
  - Spec source: context-story-158-49.md, AC1 ("Drive the real DICE_THROW dispatch; assert no exception + confrontation advances") + TEA Delivery Finding (Gap, "the dogfight maneuver commit seam is unsettled")
  - Spec text: "committing the first dogfight beat must NOT raise KeyError ... Drive the real DICE_THROW dispatch"
  - Implementation: a sealed-letter dogfight maneuver commits through `resolve_sealed_letter_lookup` (the simultaneous sealed-letter path), NOT `dispatch_dice_throw` — the d20 seam only ever served the (now-suppressed) WN personal-combat beat, and the dogfight gun roll returns from the handler's pending-shot path before reaching `dispatch_dice_throw`. So the AC1/AC4 test (`test_seated_dogfight_offers_committable_maneuvers_no_crash`) was reframed to: (a) assert the offered menu is legal maneuvers (⊆ `maneuvers_consumed`, no personal stat_check), (b) commit the offered maneuver via the REAL `resolve_sealed_letter_lookup` engine and assert it advances, and (c) assert the OLD crash path through `dispatch_dice_throw` is now a LOUD `DiceDispatchError`, never the `KeyError` ws-teardown. The "real DICE_THROW dispatch" is still driven (check c), now asserting a clean loud rejection rather than a successful maneuver commit.
  - Rationale: the AC was written before the maneuver-commit seam was understood (TEA flagged it as a Gap and authorized the adjustment); driving a maneuver through `dispatch_dice_throw` would test a path the architecture never uses.
  - Severity: minor
  - Forward impact: none for 158-49. The full player-facing maneuver SELECTION → submission → sealed-letter resolution flow (and authored maneuver labels) is 158-40's positioning-graph scope.
- **Rework (round-trip 1): no new deviations.** Fixed the Reviewer HIGH by adding `cdef.resolution_mode == ResolutionMode.sealed_letter_lookup` to the existing `is_item_use_beat` difficulty-skip in `build_confrontation_payload` (`confrontation.py`). No-roll maneuver tiles now carry no `difficulty`, and `confrontation.beat_dc_authored` records no maneuver DC (the span still fires). Change is provably scoped: `is_sealed_letter` is False for every non-sealed-letter confrontation, so their difficulty stamping is byte-identical. Both rework tests green; 529-test dogfight/confrontation/beat_filter surface green; ruff clean.

### Reviewer (audit)
- **TEA AC3 (fail-loud-at-seat) partial coverage** → ✓ ACCEPTED by Reviewer: the implementation DOES fail loud (`PackError` on empty `maneuvers_consumed` in `beats_available_for`), so AC3's substance is covered; the deferred *dedicated* unbuildable-set test is a reasonable deferral given the design-dependent trigger. (The rework should fold in the maneuver-DC regression test regardless.)
- **Dev AC1/AC4 test commit seam → sealed-letter path** → ✓ ACCEPTED by Reviewer: the seam analysis is correct — dogfight maneuvers commit via `resolve_sealed_letter_lookup` (narration BeatSelection path), and `dispatch_dice_throw` is reached only by a stray/buggy beat (the gun roll returns from the handler's pending-shot path first, verified at dice_throw.py:329). Driving the real sealed-letter engine + asserting the dice seam loud-rejects is the faithful test, not a weakening. TEA explicitly authorized the seam swap in its Gap finding.
- **Rework (round-trip 1): TEA + Dev both logged "no new deviations"** → ✓ ACCEPTED by Reviewer: confirmed — the rework is the prescribed `is_sealed_letter` difficulty-skip + two regression tests; no spec departure introduced. No undocumented deviations spotted in the rework diff.

## TEA Assessment

**Tests Required:** Yes
**Reason:** bug fix with behavioral ACs (crash, soft-lock, menu correctness, OTEL) — TDD RED.

**Test Files:**
- `tests/game/test_beat_filter_dogfight_158_49.py` — unit RED on `beats_available_for` (root cause: the WN personal-combat synthesis at beat_filter.py:368 gates on `win_condition=="hp_depletion"` and ignores `resolution_mode`) + a `beat_selection` regression guard.
- `tests/server/dispatch/test_dogfight_swn_beat_set_158_49.py` — integration RED on the real surfaces: `build_confrontation_payload` (client menu), the `confrontation.beat_filter` OTEL span, and the `dispatch_dice_throw` commit seam.

**Tests Written:** 7 (5 RED + 2 GREEN guards) covering 4 of 5 rescoped ACs (AC3 partial — see deviations).
**Status:** RED — verified via testing-runner (`uv run pytest -n0`), no setup/collection errors; every failure is on its intended assertion.

Verified failure reasons:
- AC2 unit ×2: `beats_available_for` leaks `['attack','total_defense','fighting_withdrawal','run']` onto the sealed-letter dogfight (one asserts beat identity; one asserts no personal STR/DEX stat_check).
- AC2 integration: `build_confrontation_payload["beats"]` carries the leaked menu.
- AC5 OTEL: `confrontation.beat_filter` span carries no `ruleset` attribute and its `available_beat_ids` leak the WN actions.
- AC1/AC4: `dispatch_dice_throw(beat_id="attack")` → `without_number._stat` → **KeyError: stat 'STR' not in stat block ['Cunning','Intellect','Physique','Reflex','Resolve']** — the EXACT production traceback, reproduced deterministically on the flavor-keyed fixture.

GREEN guards (pass now, must stay green):
- `test_..._is_a_sealed_letter_hp_depletion_combat` — fixture precondition guard.
- `test_ground_combat_still_synthesizes_wn_action_menu` — AC6: the `combat` (beat_selection) cdef keeps the WN attack; the fix must scope to sealed-letter dogfights, not rip out the synthesis.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #6 test quality (no vacuous assertions) | self-check across all 7 tests — every test asserts a specific value/behavior; no `assert True`, no `let _ =`, no always-None truthy | pass |

**Rules checked:** the python lang-review checklist targets production code (silent exceptions, mutable defaults, async pitfalls, etc.) — not applicable to test-only RED files; #6 (test quality) is the applicable rule and is satisfied.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Ponder Stibbons) for GREEN. Suggested fix shape: gate the WN personal-combat synthesis in `beat_filter.beats_available_for` (and the resolution-side / dice-commit twin) on `resolution_mode` so a `sealed_letter_lookup` dogfight is NOT handed the personal-combat menu; surface a ruleset-valid beat set (or fail loud at seat per AC3); add a `ruleset` attribute to the dogfight beat-menu span (AC5). Keep the `combat`/`beat_selection` WN action menu intact (AC6 guard).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/game/beat_filter.py` — new `sealed_letter_maneuver_beat(id)` helper; `beats_available_for` gains an exclusive `sealed_letter_lookup` branch that surfaces the interaction table's `maneuvers_consumed` as display-only beats (id + label, no `kind`/`stat_check`) and returns BEFORE the WN personal-combat synthesis. Fails loud (`PackError`) if the table authors no maneuvers (AC2/AC3/AC4).
- `sidequest/server/dispatch/dice.py` — `dispatch_dice_throw` rejects a `sealed_letter_lookup` beat commit LOUD (`DiceDispatchError`) before the WN-action synthesis, so the old `wn_action_beat("attack")` → `attack_params` → `KeyError` ws-teardown is structurally impossible (AC1; the gun roll never reaches here — the handler's pending-shot path returns first).
- `sidequest/server/dispatch/confrontation.py` — `build_confrontation_payload` records the bound `ruleset` on the `confrontation.beat_filter` span (AC5).
- `tests/server/dispatch/test_dogfight_swn_beat_set_158_49.py` — AC1/AC4 test reframed to the real maneuver-commit seam (see Dev deviation).

**How the fix maps to the rescoped ACs:**
- AC1 (no crash/soft-lock): the menu no longer offers a STR-stat-check beat, and the dice seam loud-rejects any sealed-letter beat — `attack_params` is unreachable for a dogfight.
- AC2 (ruleset-valid menu): the dogfight menu is now the sealed-letter maneuvers (`straight/bank/loop/kill_rotation`), never the WWN-default pool.
- AC3 (fail loud at seat): a sealed-letter cdef with no `maneuvers_consumed` raises `PackError` at menu build, not a silent/empty menu.
- AC4 (advances, no soft-lock): the offered maneuver resolves through `resolve_sealed_letter_lookup`.
- AC5 (OTEL): the beat-filter span carries the `ruleset` discriminator.
- AC6 (regression guard): the `beat_selection` ground-combat WN action menu is untouched (gate is `resolution_mode`, not `win_condition`).

**Tests:** 10/10 story tests GREEN. Full dogfight / beat_filter / confrontation / dice regression surface (560 tests) GREEN. Full server suite: 52 pre-existing/environmental reds (verified pre-existing by stashing the diff — 0 introduced by this story); ruff clean; pyright adds 0 new errors (the 19 in `dice.py` are pre-existing, none in changed lines).
**Branch:** `feat/158-49-forced-dispatch-swn-beat-set` (pushed).

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

_Round 2 (re-review of the rework). The round-1 REJECT row content is noted in the Decision column._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (9/9 story green, ruff pass, 0 smells) | N/A (round 1 also clean) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — covered by reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Yes | clean | none | round-1 HIGH (maneuver DC) now FIXED + re-verified clean |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings — covered by reviewer (see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings — covered by reviewer (see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — covered by reviewer (see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none | round-1 low (beat_id reflection) still non-blocking; rework adds no surface |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — covered by reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings — covered by reviewer (see Rule Compliance) |

**All received:** Yes (3 enabled re-ran CLEAN on the rework; 6 disabled via `workflow.reviewer_subagents`, domains covered by reviewer)
**Total findings:** 0 blocking (round-1 HIGH resolved); 2 non-blocking recommendations logged as Delivery Findings

### Rule Compliance (python lang-review checklist + CLAUDE.md/SOUL.md)

Enumerated every changed function against the applicable rules:

| Rule | Instances checked | Verdict |
|------|-------------------|---------|
| #1 Silent exception swallowing | `beats_available_for` sealed-letter branch; `dispatch_dice_throw` guard; `confrontation.py` ruleset attr | PASS — both new branches FAIL LOUD (`PackError` / `DiceDispatchError`); no bare except, no swallow. The `confrontation.py` `if rules is not None` skip is a legitimate legacy-caller path, not a swallow. |
| #3 Type annotations at boundaries | `sealed_letter_maneuver_beat(maneuver_id: str) -> BeatDef` | PASS — fully annotated. |
| #4 Logging coverage/correctness | new error paths raise typed exceptions caught + logged upstream (`dice_throw.py:381` `logger.warning`) | PASS — client-error path logged at warning (4xx-equivalent), correct level. |
| #6 Test quality | both new test files | PASS — every test asserts a specific value; no `assert True`, no vacuous truthy; precondition guard + regression guard present. One coverage GAP — see [TEST] (no assertion on `difficulty`, which let the HIGH finding through). |
| #11 Input validation at boundaries | `dispatch_dice_throw` (player DICE_THROW) | PASS-with-low-note — the sealed-letter beat commit is now validated + loud-rejected; `payload.beat_id` echoed in the error (see [SEC], low, consistent with the pre-existing `unknown beat_id` message convention). |
| SOUL "Bind the Ruleset, Don't Balance It" | the sealed-letter maneuver menu | PASS — the fix REMOVES the native WN personal-combat scaffolding from the dogfight path (does not balance it against the sealed-letter engine); maneuvers come from the bound interaction table. Doctrine-compliant. |
| CLAUDE.md "No Silent Fallbacks" | both branches | PASS — loud `PackError`/`DiceDispatchError`. |
| CLAUDE.md OTEL Observability Principle | the new `ruleset` span attr + the `beat_dc_authored` span | **PASS (round-2 — round-1 VIOLATION fixed)** — the rework skips `difficulty` for sealed-letter maneuvers, so `beat_dc_authored` no longer records fabricated maneuver DCs (it fires with no maneuver in `beat_difficulties`); the `ruleset` discriminator is recorded on `beat_filter`. Regression-locked by `test_dogfight_beat_dc_authored_span_records_no_maneuver_dcs`. |

## Reviewer Assessment

**Verdict:** APPROVED (round-trip 1 re-review — the round-1 REJECT recorded below is RESOLVED)

**Round 2 re-review (2026-06-28):** The single blocking finding from round 1 — fabricated d20 DCs stamped on no-roll sealed-letter maneuver tiles, polluting the `confrontation.beat_dc_authored` lie-detector — is FIXED. `build_confrontation_payload` now skips `difficulty` for `sealed_letter_lookup` maneuver beats (`if is_sealed_letter or is_item_use_beat(beat_def.id): continue`), and the span fires with no maneuver in `beat_difficulties`. All three enabled specialists re-ran CLEAN on the rework diff (preflight 9/9 story tests green + ruff pass + 0 smells; silent-failure CLEAN — confirmed `resolution_mode` is a single cdef field so a sealed-letter cdef holds all-maneuver beats holistically, and the span still fires unconditionally; security CLEAN — the change REMOVES a spurious field, the opposite of leakage, no new exception path). The TEA red-rework added the two regression tests that close the [TEST] coverage gap that let the bug through. The fix is provably scoped: `is_sealed_letter` is `False` for every non-sealed-letter confrontation → byte-identical behavior. All round-1 VERIFIED observations (no ws-teardown — `DiceDispatchError` caught at handler:380; `BeatDef` None-serialization; Bind-the-Ruleset doctrine; AC6 guard green) still hold. The two non-blocking recommendations (load-time sealed-letter validator; `beat_id` error reflection) remain logged as Delivery Findings for follow-up. **Tags 8/8 present:** [EDGE][SILENT][TEST][DOC][TYPE][SEC][SIMPLE][RULE] — see this round's clean specialist re-runs + the round-1 observations below (still valid).

---

**Round 1 verdict (HISTORY — now resolved): REJECTED.** The core fix was correct and the p1 crash/soft-lock genuinely resolved (verified end-to-end). But the change introduced a player-facing wrong number AND polluted the OTEL lie-detector — a blocking quality defect with a trivial, precedent-backed fix in this story's own file. Sin is treating code like it doesn't matter; a known-false DC on a no-roll tile matters.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT] [RULE] | Sealed-letter maneuver beats (no `stat_check`, no d20) flow through the `_offer_dc` loop and get the target's **armor class stamped as `difficulty`** (`offer_difficulty` returns `target_core.armor_class` ignoring `stat_check` — without_number.py:173). Every dogfight maneuver tile (`straight/bank/loop/kill_rotation`) carries a meaningless d20-vs-AC number it never rolls (the maneuver resolves by interaction-table lookup), AND the `confrontation.beat_dc_authored` span records these fabricated DCs — polluting the GM-panel lie-detector (CLAUDE.md OTEL Observability Principle). | `sidequest/server/dispatch/confrontation.py:439-448` | Skip `difficulty` for sealed-letter maneuver beats, exactly as item-use beats are skipped at line 446 (`if is_item_use_beat(beat_def.id): continue`). Add `or cdef.resolution_mode == ResolutionMode.sealed_letter_lookup` to that skip (a sealed-letter maneuver is a no-roll commit — same category as item-use; absent `difficulty` is the UI's "no dice tray" signal). The `beat_dc_authored` span's `beat_difficulties` then correctly omits the maneuvers. |

**Confirmed observations (5+):**
- [HIGH][SILENT][RULE] Fabricated maneuver DCs — the blocking finding above. Confirmed independently: `_offer_dc` else-branch (confrontation.py:432-435) → `WithoutNumberRulesetModule.offer_difficulty` (without_number.py:173) returns AC, ignores stat_check; the per-beat loop (confrontation.py:439-448) stamps it on every non-item-use beat including the new maneuvers.
- [SILENT][LOW→noted] `beat_filter.py:382` `maneuvers = list(table.maneuvers_consumed) if table is not None else []` — the `else []` collapses a missing-interaction_table into the same empty-list path as an authored-but-empty `maneuvers_consumed`. **Not a silent fallback** (the very next line raises `PackError` loudly either way), so non-blocking; but the message doesn't distinguish "no table" from "empty list," and there is no load-time `ConfrontationDef._validate` guard requiring a sealed_letter_lookup cdef to carry a non-empty interaction_table. Recommendation (non-blocking): a load-time validator would catch this at pack load, not first player action. Logged as a Delivery Finding.
- [SEC][LOW] `dice.py:400-407` — the new `DiceDispatchError` echoes player-controlled `payload.beat_id` (`!r`) back to the sender via `_error_msg`. No XSS (typed JSON transport), no cross-user leak (own input), no crash. **Consistent with the pre-existing `unknown beat_id {payload.beat_id!r}` messages** in the same file (dice.py:442), so not a regression. Non-blocking; harden later if desired.
- [VERIFIED][SEC] The new `raise DiceDispatchError` does NOT create a new ws-teardown: it is caught at `handlers/dice_throw.py:380` (`except DiceDispatchError`) → `_error_msg("Dice throw failed: …")` at :400, connection preserved. The OLD crash was an UNHANDLED `KeyError` (not a `DiceDispatchError`) that propagated to `ws.unexpected_error` → teardown. The fix genuinely converts an unhandled teardown into a handled client error — evidence: dice_throw.py:366 (call) inside try, :380 (catch), :400 (graceful return). Complies with "client errors should not tear down the connection."
- [VERIFIED][EDGE][TYPE] `kind=None`/`stat_check=None` maneuver `BeatDef` serializes safely — `payload["beats"] = [b.model_dump(mode="json") for b in beats_for_payload]` (confrontation.py:323); pydantic dumps None fields without error, and the AC2 payload test passes through this path. `BeatDef.kind`/`stat_check` are `Optional` by model design (display-only-stub precedent: Fate Contest beats). No downstream `.kind.value` unguarded deref in the changed path.
- [VERIFIED][RULE] SOUL "Bind the Ruleset, Don't Balance It" — the fix REMOVES the native WN personal-combat synthesis from the sealed-letter dogfight path (early return before the `is_wn_binding` block) rather than tuning it; maneuvers are sourced from the bound interaction table. Doctrine-compliant. The `beat_selection` ground-combat WN menu is untouched (AC6 guard test green).
- [TEST] Test quality is good (meaningful assertions, fixture-real cdefs, precondition + regression guards). **Coverage gap that let the HIGH finding through:** `test_dogfight_payload_excludes_wn_personal_combat_menu` asserts beat IDs but never inspects `payload["beats"][n]["difficulty"]`. The red-rework should add an assertion that a sealed-letter maneuver tile carries NO `difficulty` key (mirroring the item-use no-DC contract).
- [DOC] `sealed_letter_maneuver_beat` docstring cites `tests/genre/test_dogfight_content_loading.py` for the "beats ARE the maneuvers" convention — that test is now stale (the dogfight `beats:` list was dropped; the convention moved to `maneuvers_consumed`). Minor; tidy the reference when the stale test is updated (already logged as a Dev finding).
- [SIMPLE] No unnecessary complexity. The early-return branch and the dice guard are minimal and direct; the `sealed_letter_maneuver_beat` factory mirrors `wn_action_beat`/`wn_cast_beat`. No dead code, no over-engineering.

**Data flow traced:** player DICE_THROW (`beat_id`) → `DiceThrowHandler.handle` → (pending-shot path returns first for gun rolls) → `dispatch_dice_throw` → sealed-letter cdef → **loud `DiceDispatchError`** → caught at handler:380 → client error message. Safe: no teardown, no `attack_params` reach. Maneuver SELECTION flow: `build_confrontation_payload` → `beats_available_for` → maneuver beats from `maneuvers_consumed` → payload (✗ currently with bogus `difficulty`).

### Devil's Advocate

Argue this code is broken. The most damning case is the one confirmed above: the change trades a loud crash for a quiet lie. Before, a dogfight that reached the d20 path crashed — ugly, but honest and impossible to miss. Now the dogfight presents four maneuver tiles each wearing a "DC 16" badge that is pure theater: the sealed-letter engine never consults it, yet a mechanics-first player (Sebastien, Jade — the exact audience this project is built for) will read "DC 16" and reason about odds that do not exist. Worse, the `beat_dc_authored` OTEL span — the very instrument Keith uses to verify the engine isn't improvising — now emits `straight=16,bank=16,loop=16,kill_rotation=16`, fabricated numbers with no resolver behind them. The lie-detector has been taught to lie. That is the deepest possible violation of the project's stated ethos, and it is introduced by a story whose entire purpose was to stop the dogfight from faking mechanics.

What else could break? A misconfigured pack: a sealed_letter_lookup cdef with no interaction_table reaches `beats_available_for` and raises `PackError` at the first player menu build rather than at pack load — a content author discovers the gap mid-session, not at startup (non-blocking, but the load-time guard is the right place). A confused author reading `sealed_letter_maneuver_beat`'s docstring is pointed at a now-failing test as the authority for a convention that test no longer encodes. A hostile player sending a 1 MiB `beat_id` gets it reflected back in an error string — bounded by the frame limit, their own input, no leak, but unnecessary. None of these are blocking; the DC fabrication is. The fix is three lines and the precedent (item-use skip) sits four lines above the bug with a comment explaining precisely why no-roll beats must not carry a DC. There is no excuse to ship it.

**Handoff (round 2):** To SM (Captain Carrot) for finish-story — all blocking findings resolved, all gates green. (Round 1 handed back to TEA/Dev for the now-completed rework.)