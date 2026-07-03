---
story_id: "158-54"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-54: awn.mutation.used OTEL span never fires for mutant_wasteland mutations

## Story Details
- **ID:** 158-54
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Branch:** feat/158-54-awn-mutation-used-span
- **Branch Strategy:** gitflow (feat/158-54-awn-mutation-used-span)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-03T06:49:18Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-02T23:26:14Z | 2026-07-02T23:28:37Z | 2m 23s |
| red | 2026-07-02T23:28:37Z | 2026-07-03T06:14:31Z | 6h 45m |
| green | 2026-07-03T06:14:31Z | 2026-07-03T06:27:54Z | 13m 23s |
| review | 2026-07-03T06:27:54Z | 2026-07-03T06:39:30Z | 11m 36s |
| red | 2026-07-03T06:39:30Z | 2026-07-03T06:43:45Z | 4m 15s |
| green | 2026-07-03T06:43:45Z | 2026-07-03T06:47:23Z | 3m 38s |
| review | 2026-07-03T06:47:23Z | 2026-07-03T06:49:18Z | 1m 55s |
| finish | 2026-07-03T06:49:18Z | - | - |

## Sm Assessment

**Story:** 158-54 — `awn.mutation.used` OTEL span never fires for mutant_wasteland (Ashes Without Number) mutations (3 pts, p2, bug, tdd/phased, repo: sidequest-server).

**Problem (diagnosis unconfirmed — confirm at pickup):** Two existing tests assert the span and fail — `test_103_10_seaboard_e2e` and `test_102_7_mutant_wasteland_mutations_live`. Pre-existing full-suite failure surfaced 2026-07-01 during the 160-4 scoping pass; unrelated to 160-4. The first job of RED is to pin the fork the story leaves open: **(a)** the mutation effect applies but only the span is missing → emit it on the use decision; or **(b)** the mutation-use path itself is dark → the effect must apply AND the span must fire. Do not assume (a); the scoping pass explicitly did not confirm which.

**Why it matters:** OTEL is the lie-detector (CLAUDE.md OTEL Observability Principle). Without the span, we cannot distinguish an engaged mutation effect from narrator improvisation. Payload must identify component + mutation + actor.

**Fix direction (Dev's call):** Trace the AWN mutation-use path and wire the span at the use decision. Note 158-53 just landed the analogous WWN spellcast span work (server #1103) and 158-50 the course-dispatch wiring (server #1106) — this story is in the same half-wired-telemetry family; prefer the established span patterns over inventing new ones (Don't Reinvent — Wire Up What Exists).

**Wiring test (mandatory, per CLAUDE.md + story):** A mutation use in a mutant_wasteland world must produce the `awn.mutation.used` span via the real path — asserted through span emission, not source-grep, not a synthetic emit in the test. The two named failing tests going green via the real path is the acceptance spine.

**Scope discipline:** AWN mutation span/effect path only. The two named tests plus any new wiring test. No dogfight (158-49/158-40 territory), no course/clock (just closed as 158-50), no unrelated test-suite hygiene (that's 158-55).

## TEA Assessment

**Tests Required:** Yes

**Diagnosis (the story's open fork, now pinned):** fork **(b)** — the in-combat mutation-use path is DARK, not merely span-less. Measured 2026-07-03: the engine is green everywhere it's reachable (use_ops + awn.* spans: 4 unit tests pass; freeplay `magic_working` route: 8 pass; chargen/saint/stock spans: pass). The ONLY in-combat route ever built was the narrator-apply beat path (102-7), and ADR-143 de-nativization now drops all stray narrator beats in a live WN-family hp_depletion combat (`awn` IS WN-family per `is_live_wn_combat`; the drop was observed live: `wn_combat_beat_dropped_engine_owns_round` in the failing test's log). The dice path — which OWNS a live WN round — has NO mutation route: `DiceThrowPayload` and `WnSealedCommit` carry `spell_id` but no `mutation_id`, and `_apply_committed_player_beat` has the WWN cast spine + strike channels, zero mutation branches. A committed `mutant_ability` beat resolves today as a bare WIS strike — generic damage, no Strain, no usage tick, no span. This is the 158-53 WWN-cast disease exactly, except the dice-path route the cast already had (102-2/152-2) was never built for mutations.

**GREEN direction (Dev):** build the dice-path mutation route mirroring 102-2 — thread `mutation_id` through `DiceThrowPayload` → `WnSealedCommit` → route `mutation_resolution`-marked beats in `_apply_committed_player_beat` through `sidequest.mutation.use_ops.use_mutation` (the SAME spine the freeplay/narrator routes call; wire a save_resolver — use_ops raises without one when the mutation has save.stat). Add the dispatch-time shape guards (mirror the cast guards' placement + loudness). Do NOT exempt mutation beats from the ADR-143 drop; do NOT delete the narrator-apply route (still live for non-hp_depletion confrontations).

**Test Files:**
- `tests/integration/test_dice_path_mutation_use_158_54.py` (NEW) — the dice-path contract: use spine + Strain (happy path), face-independence, three loud malformed-commit guards, unowned-refusal engagement. Real mutant_wasteland + heavy_metal packs, skipif content absent. Pyright-clean.
- `tests/integration/test_102_7_mutant_wasteland_mutations_live.py` (REWIRED) — the live proof now drives `dispatch_dice_throw`; 6 sibling content/chargen tests untouched and green.
- `tests/integration/test_103_10_seaboard_e2e.py` (REWIRED) — the Saint-Marked capstone's confrontation leg now drives the dice seam; chargen/save-cycle assertions untouched.

**Tests Written:** 6 new + 2 rewired, covering all 3 ACs (AC-1 span+payload: happy path + capstone; AC-2 effect-applies: Strain arithmetic + usage economy + refusal engagement; AC-3 the two named tests via the real path).
**Status:** RED (verified by testing-runner, RUN_ID 158-54-tea-red: 7 failed / 18 passed / 1 skipped; post-pyright-fix re-run 6/6 new still fail). Every failure is honest: 6× `ValidationError: mutation_id — Extra inputs are not permitted` (the missing protocol field), 1× `DID NOT RAISE DiceDispatchError` (today's silent bare-strike dispatch — the disease itself). The capstone SKIPs locally (no test PG database) and goes RED-then-GREEN in the full-suite env.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 silent exceptions (No Silent Fallbacks in product) | `test_mutation_beat_commit_without_mutation_id_is_loud`, `test_mutation_id_on_unmarked_beat_is_loud`, `test_mutation_id_on_non_awn_ruleset_is_loud` — pin loud TYPED rejections over silent generic-strike resolution | failing (RED) |
| #4 logging/observability (OTEL doctrine) | happy path + capstone pin `awn.mutation.used` w/ actor+mutation_id; refusal test pins `awn.mutation.refused` w/ reason | failing (RED) |
| #6 test quality (no vacuous asserts) | self-checked: exact span counts, attr values, Strain arithmetic before/after, `match=` audited (no embedded paths in DiceDispatchError; no tmp_path in suite) | done |
| #3 type annotations / pyright | new suite pyright-clean (HpPool ctor, fail-loud `_strain_current` accessor); 9 legacy errors verified pre-existing on develop baseline | done |

**Rules checked:** 4 of 4 applicable lang-review rules have coverage (remaining rules target product code Dev writes — Reviewer re-checks on the GREEN diff)
**Self-check:** 0 vacuous tests found; every negative assertion (`assert not _spans(...)`) is paired with a positive in the same test

**Handoff:** To Dev (Inigo Montoya) for implementation

### Red rework round 1 (2026-07-03, post-review)

**Scope:** Westley's single [HIGH] — the mutation guard block lacks the cast guard's `opposed_check` rejection clause.
**Probe first (stale-premise discipline):** confirmed empirically before pinning — a scratchpad drive of `dispatch_dice_throw` with a valid, owned `mutation_id` on the real pack's combat cdef mutated to `resolution_mode: opposed_check` returned `opposed_pending=True`, strain unchanged, NO raise. Mechanism verified in code: `wn_sealed_round = not opposed_pending and ...` (dice.py:755) — the opposed defer skips both the WN walk and `apply_beat`, so the spine is silently unreachable. Reviewer's finding CONFIRMED.
**Test added:** `test_mutation_beat_on_opposed_check_confrontation_is_loud` (same suite) — seats the real combat normally, flips the seated cdef to `opposed_check` post-seat (the misconfigured-homebrew scenario; `load_genre_pack` is uncached so the mutation cannot leak), asserts `pytest.raises(DiceDispatchError, match="opposed_check")` + strain unchanged + zero used-spans.
**Status:** RED verified — the new test fails `DID NOT RAISE DiceDispatchError` (the honest reason); the six sibling tests stay green; file pyright-clean (0 errors), ruff clean. Commit `bdb6eef4`.
**Dev direction:** add the opposed_check rejection inside the mutation guard block (mirror dice.py:500-507), and per the Reviewer's fix guidance consider factoring the twice-derived `is_awn_mutation` gate (dice.py:541 vs 1876) into one helper so the copies cannot drift.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/protocol/dice.py` — `DiceThrowPayload.mutation_id: str | None` (the `spell_id` transport twin; docstring documents the picker contract)
- `sidequest/game/encounter.py` — `WnSealedCommit.mutation_id: str | None` (rides the sealed round; optional-with-default so pre-158-54 persisted saves load unchanged)
- `sidequest/server/dispatch/dice.py` — (1) dispatch-time shape guards after the cast guards: `mutation_id` on an unmarked beat or non-awn ruleset → loud `DiceDispatchError`; a `mutation_resolution`-marked awn beat commit with no `mutation_id` → loud `DiceDispatchError` (kills the silent bare-strike resolution); (2) `_apply_committed_player_beat` gains `mutation_id` param + the mutation spine block beside the cast spine — function-local import of `_resolve_mutation_for_beat` (narration_apply), driven by a `BeatSelection` with the engine's premise target; runs regardless of `outcome_tier` (the power fires, the target saves)
- `sidequest/server/dispatch/wn_round.py` — `seal_wn_commit` threads `mutation_id` into the ledger; the round walk passes `commit.mutation_id` to the apply
- Plus one isolated hygiene commit (`7745140e`): two pre-existing develop ruff findings auto-fixed (see deviation log)

**One spine, three entry points:** the dice path calls the SAME `_resolve_mutation_for_beat` the narrator apply path uses (which itself wraps `use_ops.use_mutation`, shared with freeplay `magic_working`) — no re-implementation, ownership/limit/strain refusals recorded on `awn.mutation.refused` by the spine. The ADR-143 drop is untouched; the narrator-apply route is untouched (still live for non-hp_depletion confrontations).

**Tests:** 13/13 passing in the story suites (6 new dice-path + 7 in the rewired 102-7 live file). Full server suite via testing-runner (RUN_ID 158-54-dev-green): 13,139 passed / 2 failed / 1,709 skipped — zero failures in dice/wn_round/encounter/protocol; the 2 failures are pre-existing beneath_sunden content gates, verified failing on develop without this diff (logged as a Delivery Finding). The 103-10 capstone still SKIPs locally (no test PG); its confrontation leg now drives the live seam and greens in the full env. Lint clean on all changed files; pyright: 0 new errors (dice.py 19 pre-existing = 19 after; other files 0).

**Branch:** feat/158-54-awn-mutation-used-span (pushed)

**Handoff:** To Fezzik (TEA) for verify (tdd: green → review — Westley takes the review phase per workflow)

### Green rework round 1 (2026-07-03, post-review)

**Fix (commit `73b155aa`):** exactly the Reviewer's prescription, no deviations —
- `sidequest/server/dispatch/dice.py` mutation guard block gains the opposed_check clause (mirror of the cast guard at ~500): a `mutation_resolution` beat commit on an `opposed_check` cdef raises `DiceDispatchError` ("...opposed_check confrontation... No Silent Fallbacks") before any state mutation. Missing-mutation_id and opposed_check checks now nest under one `if is_awn_mutation_beat:` for cast-guard structural parity.
- The twice-derived gate is factored into `_is_awn_mutation_beat(beat, pack)` (module-level, used by both the dispatch guards and the apply spine) — addressing the Reviewer's drift-risk guidance; the [DOC] note resolves with it (the "cast-guard contract, retold" comment is now accurate, and the comment block documents the third clause).

**Verification:** story suites 14/14 GREEN (-n0), including the new `test_mutation_beat_on_opposed_check_confrontation_is_loud`; cast suite + tests/server/dispatch/ + seaboard e2e: 535 passed, 1 xdist flake (`test_59_23_materialize_other` — passes serially, was green in this session's full-suite run; unrelated SWN ship combat). Ruff clean, pyright 19=19 pre-existing (0 new).

**Handoff:** Back to Westley (Reviewer) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (all mechanical checks pass; pre-existing issues confirmed unchanged) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own trace (beat-less path, item-use path, direct-apply path) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 (1 high, 1 low) | confirmed 2 (high → [HIGH] blocking; low → folded into fix guidance) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer's own read of the 6-test suite |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — Reviewer note: the mutation-guard comment overstates its cast parity (folded into the [HIGH]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — Reviewer verified the two new optional fields (typed, extra=forbid, save-compatible default) |
| 7 | reviewer-security | Yes | findings | 1 (low) | confirmed 1 as non-blocking Delivery Finding (unbounded mutation_id persisted before catalog check — pre-existing spell_id-shape parity) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — Reviewer notes the duplicated is_awn_mutation gate (low) in fix guidance |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Reviewer performed the rule-by-rule enumeration below |

**All received:** Yes (3 enabled returned: 1 clean, 2 with findings; 6 disabled via settings)
**Total findings:** 3 confirmed (1 blocking, 2 non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [SILENT] | Mutation guard block omits the `opposed_check` loud rejection its cast twin carries. A `mutation_resolution` beat committed on an AWN `opposed_check` confrontation passes dispatch validation, then resolves via `narration_apply._resolve_opposed_check_branch` (plain `apply_beat`, both sides) — the use spine never runs: no `awn.mutation.used`/`.refused` span, no Strain, silent bare stat throw. This is the story's own bug class reopened for one gate combination, and the cast precedent (dice.py:500-507, added in 102-2's review round: "would pass validation and then SILENTLY skip the spine") shows the project already ruled this guard mandatory even with "no current content ships the combination." Unreachable with shipped content today (mutant_wasteland rules.yaml declares zero opposed_check) — but content authors add confrontations without touching engine code (the Jade doctrine), so content-unreachability is not a defense. Matches CLAUDE.md No Silent Fallbacks; cannot be dismissed. | `sidequest/server/dispatch/dice.py:541-560` | Add `if is_awn_mutation_beat and cdef.resolution_mode == ResolutionMode.opposed_check: raise DiceDispatchError(...)` inside the mutation guard block (mirror the cast clause), and pin it with a test (synthetic AWN opposed_check cdef + marked beat → loud raise). While there, consider factoring the twice-derived `is_awn_mutation` gate (dice.py:541, dice.py:1876) into one helper so the two copies cannot drift — the drift is exactly how this hole appeared. |

**Observations (beyond the blocker):**
1. `[VERIFIED] [SEC]` Identity and economy are server-side end-to-end — `character_name` resolves from the authenticated `player_id` via `snapshot.player_seats` (handlers/dice_throw.py, 118-9 anti-spoof), `use_mutation` ownership keys off `actor.name`, Strain lands on the actor's own core. A client's `mutation_id` selects WHICH, never WHOSE. Complies with lang-review #11 identity-boundary intent.
2. `[VERIFIED] [EDGE]` The beat-less throw path raises loudly (dice.py:369-374) BEFORE the guards — no silent `mutation_id` drop there; the item-use intercept seals `mutation_id=None` explicitly, exact parity with `spell_id`'s shipped shape. The legacy no-initiative immediate path passes `mutation_id` on the direct `_apply_committed_player_beat` call, so both WN resolution paths route the spine.
3. `[SEC]` (low, non-blocking) `mutation_id` carries no length bound and catalog membership is validated only in the spine, AFTER `seal_wn_commit` persists the raw client string into `encounter.wn_commits` — the cast path validates the catalog at dispatch, before sealing. Pre-existing shape parity with `spell_id`'s missing length bound; folded into the existing TEA Improvement finding (dispatch-time catalog check) as corroboration.
4. `[VERIFIED] [TEST]` The 6-test suite asserts exact span counts, attr values, and Strain arithmetic; face-independence and refusal-engagement are pinned; the two rewired integration proofs keep their original save-cycle/chargen assertions. No vacuous assertions found. Gap: no test covers the opposed_check combination (the blocker's test comes with the fix).
5. `[VERIFIED] [TYPE]` Both new fields are `str | None = None` on `extra=forbid` pydantic models — typed end-to-end, pre-158-54 persisted saves load unchanged (default), no stringly-typed drift beyond the id-string idiom the codebase already uses for spell_id.
6. `[DOC]` The mutation-guard comment claims "the 102-2 cast-guard contract, retold" — overstated while the opposed_check clause is missing; becomes accurate once the [HIGH] fix lands (fold the comment check into that fix).
7. `[SIMPLE]` Diff is minimal and precedent-shaped; the only duplication is the twice-derived `is_awn_mutation` gate flagged in the fix guidance. No over-engineering.
8. `[RULE]` Rule-by-rule enumeration below; one violation class (the [HIGH]), one partial (#11 length bound, non-blocking parity gap).
9. `[EDGE]` (non-blocking) Dice-path mutation refusals are span-only — the GM panel sees `awn.mutation.refused`, but no round message tells the PLAYER why nothing happened (Sebastien-legibility). Matches the narrator-route contract; logged as a Delivery Finding for a UI/narration follow-up.

### Rule Compliance

| Check (python lang-review) | Instances in diff | Judgment |
|---|---|---|
| #1 silent exceptions / silent fallbacks | 2 new guards + 8 spine refusal branches + the opposed_check gap | Guards raise typed pre-mutation: compliant. Spine refusals all span-emitting (verified `_resolve_mutation_for_beat` narration_apply.py:560-628): compliant. **The opposed_check combination is the one silent path: VIOLATION → [HIGH]** |
| #2 mutable defaults | 2 new fields, 2 new params | `str \| None = None` throughout: compliant |
| #3 type annotations | 2 fields, 2 params, guard locals | Annotated; pyright 19=19 pre-existing, 0 new: compliant |
| #4 logging/observability | use spine + refusals | `awn.mutation.used`/`.refused` on every decision; dispatch raises carry no pre-raise span, parity with cast guards: compliant |
| #5 path handling | none in diff | n/a |
| #6 test quality | 6 new + 2 rewired tests | Exact-value asserts, paired negatives, no vacuous patterns: compliant |
| #7 resource leaks | none in diff | n/a |
| #8 unsafe deserialization | 1 boundary field | pydantic-validated, extra=forbid, no eval/pickle: compliant |
| #9 async pitfalls | none (sync dispatch) | n/a |
| #10 import hygiene | 2 function-local imports | Mirrors the documented cast-precedent local-import rationale (heavy module): compliant |
| #11 input validation at boundaries | mutation_id | Typed + shape-guarded; **no length bound, catalog check deferred past persistence: PARTIAL (non-blocking, pre-existing spell_id parity)** |
| #12 dependency hygiene | no dep changes | n/a |
| #13 fix-introduced regressions | ruff hygiene commit | Pure `ruff --fix` output, re-scanned: compliant |

### Devil's Advocate

Assume this diff is broken and I must prove it. The strongest attack is the one the silent-failure hunter landed: the guard block advertises full cast parity while silently lacking the opposed_check arm, and the project's own history says that omission bites — 102-2's reviewer forced the identical clause onto the cast path even though no content shipped the combination, because "content-unreachable" rots the moment a homebrew author (Jade, tomorrow) writes an AWN confrontation with `resolution_mode: opposed_check` and a mutation-marked beat. When it rots, it rots silently: the exact zero-span, zero-Strain improv this story was funded to kill. That is a blocking finding, and I blocked on it. Second attack: the `save_resolver=lambda stat, target: "fail"` the dice spine inherits from the narrator route means the TARGET never saves on any dice-path mutation — every save-vs mutation lands at full effect, a player-favorable mechanical bias. It is documented v1 ("opposed-save dice wiring rides a later plan"), span-visible (`save_result="fail"`), and pre-existing behavior reused — not new in this diff — so it stays an observation, but the follow-up story should be tracked before a playtest reads it as combat imbalance. Third attack: a refused mutation is invisible to the refused player (span-only) — a confused player mashes the button, pays nothing, sees nothing, and calls it a bug; logged as a finding. Fourth: could the round walk double-fire the spine for one commit? No — one commit per actor (loud double-commit guard), one walk slot per token, and the narrator-beat route is dropped in live WN combat, so the two entry points cannot both fire for the same event. Fifth: malformed unicode/huge mutation_id — survives to the persisted ledger (observation 3) but injects nowhere. The blocker stands alone, and it is enough.

**Data flow traced:** player browser → WS `DICE_THROW` → `DiceThrowPayload.mutation_id` (pydantic, extra=forbid) → dispatch guards (shape vs beat marker + ruleset) → `seal_wn_commit` → `WnSealedCommit` (persisted) → round walk → `_apply_committed_player_beat` → `BeatSelection` sidecar → `_resolve_mutation_for_beat` → `use_mutation` (ownership/limit/strain vs server-resolved actor) → spans + Strain on actor's own core. Safe at every hop except the one silent branch named above.
**Pattern observed:** good — the one-spine-N-entry-points reuse (dice.py:1882-1899 mirrors dice.py:1812-1829); bad — hand-duplicated gate derivation (dice.py:541 vs dice.py:1876).
**Error handling:** typed `DiceDispatchError` pre-mutation at dispatch; span-recorded refusals in the spine; loud unknown-beat and beat-less raises upstream.
**Wiring:** server contract live and driven end-to-end by tests through `dispatch_dice_throw`; UI mutation picker is a tracked follow-up (TEA finding) — field optional, current clients unaffected.

**Handoff:** Back to TEA (red rework) — the finding is testable: pin the opposed_check loud rejection, then Dev adds the guard clause.

### Re-review round 1 (2026-07-03)

**Verdict:** APPROVED

**Delta reviewed** (commits `bdb6eef4` + `73b155aa`, read line-by-line): TEA's guard test (probe-confirmed the silent skip: `opposed_pending=True`, no raise, strain unchanged) and Dev's fix — the opposed_check clause inside the mutation guard block (message mirrors the cast clause including the No-Silent-Fallbacks citation and carries "opposed_check" for the test's match), plus the `_is_awn_mutation_beat` helper replacing both hand-duplicated derivations (identical boolean expression, verified; docstring records the drift lesson).

**[HIGH] resolution verified empirically:** story suites 14/14 GREEN (-n0) including `test_mutation_beat_on_opposed_check_confrontation_is_loud`; ruff clean; pyright 19=19 pre-existing (0 new); working tree clean. Guard ordering checked: missing-mutation_id reported before opposed_check (cast-guard parity); a marked beat on a non-awn opposed cdef with mutation_id still rejects via the cross-ruleset guard; without mutation_id it correctly falls through as a native beat (non-awn packs don't own mutation semantics). The [DOC] observation resolves with the fix (the "cast-guard contract, retold" comment is now accurate). The `[SIMPLE]` gate-duplication observation resolves via the helper. The three non-blocking Delivery Findings stand as logged follow-ups.

**Handoff:** To Vizzini (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The dice-path mutation route needs a UI half — the confrontation overlay must offer a mutation picker (the spell-picker twin, 102-2) so the client can send `mutation_id` on the commit. That is a sidequest-ui story outside 158-54's server scope.
  Affects `sidequest-ui` (CavernActionPanel/overlay commit payload — new story needed).
  *Found by TEA during test design.*
- **Gap** (non-blocking): `tests/server/test_102_7_mutation_beat_use_ops.py` pins the narrator-apply mutation route with fixtures that do NOT trip `is_live_wn_combat` (default win_condition) — that route is now unreachable in a live AWN hp_depletion COMBAT (ADR-143 drop) but remains the live route for non-hp_depletion confrontations (chase/negotiation mutation beats). Dev must NOT delete `_apply_mutation_beat` when adding the dice route; both entry points share use_ops.
  Affects `sidequest/server/narration_apply.py` (keep the route; add the dice twin).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): the cast precedent also dispatch-validates a spell_id unknown to the resolved catalog (loud DiceDispatchError). The mutation route should mirror it (unknown `mutation_id` → typed rejection) — not pinned in RED because the catalog-resolution shape is Dev's choice; the unowned-id refusal (use_ops `not_owned`) IS pinned.
  Affects `sidequest/server/dispatch/dice.py` (dispatch-time catalog validation, mirror of 102-2).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): 9 pre-existing pyright errors in the two legacy integration files (dict-vs-HpPool ctor, Optional member access, psycopg execute overload) — verified present in the develop baseline, NOT introduced by this story. The new 158-54 suite is pyright-clean.
  Affects `tests/integration/test_102_7_mutant_wasteland_mutations_live.py`, `tests/integration/test_103_10_seaboard_e2e.py` (type hygiene pass, separate chore).
  *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): two pre-existing full-suite failures unrelated to this story — `tests/genre/test_beneath_sunden_creature_images_107_2.py::test_every_low_tagged_bestiary_entry_is_renderable` (41 low-band bestiary entries missing image specs) and `tests/genre/test_beneath_sunden_room_binding_107_2.py::test_distinct_rooms_bind_distinct_creatures` (only one room→creature binding). Verified failing on develop WITHOUT this story's changes (git-stash baseline run, 2026-07-03).
  Affects `sidequest-content/genre_packs/caverns_and_claudes` (107-2 content follow-up story needed, or fold into 158-55's full-suite hygiene).
  *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): dice-path mutation refusals are span-only — the refused player sees nothing in the round output explaining why no mutation fired (matches the narrator-route contract, but the dice path is player-initiated so the silence is felt). A follow-up should surface refusal reasons in the round messages (Sebastien-legibility: expose the math in player-facing surfaces).
  Affects `sidequest/server/dispatch/wn_round.py` (thread spine refusals into round messages — new story).
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `mutation_id` (and `spell_id`) carry no length/format bound at the pydantic boundary, and the mutation catalog check runs only in the spine, after `seal_wn_commit` persists the raw client string. Corroborates TEA's dispatch-time-catalog-validation finding; fix both fields together for parity with the cast path's validate-before-seal ordering.
  Affects `sidequest/protocol/dice.py`, `sidequest/server/dispatch/dice.py` (Field(max_length) + dispatch catalog check — fold into the same follow-up as TEA's Improvement).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): the dice-path mutation spine inherits `save_resolver=lambda stat, target: "fail"` from the narrator route — on every dice-path use the target NEVER saves (full effect, player-favorable, span-honest via `save_result="fail"`). Documented v1, pre-existing, but now reachable from the primary combat path; the opposed-save dice wiring story should be scheduled before a crunch-sensitive playtest reads it as imbalance.
  Affects `sidequest/server/narration_apply.py` / future opposed-save story (v1 save semantics now on the hot path).
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Rewired the two named integration tests off the narrator-apply seam onto the dice path**
  - Spec source: story description ("test_103_10_seaboard_e2e and test_102_7_mutant_wasteland_mutations_live both assert the span and fail"; AC-3 "pass via the real path")
  - Spec text: the tests' own docstrings said "drive the mutation beat through the REAL `_apply_narration_result_to_snapshot` apply path"
  - Implementation: both tests now drive `dispatch_dice_throw` with the mutation-marked beat + `mutation_id` (initiative pinned, rng pinned via global `random.randint`)
  - Rationale: ADR-143 de-nativization (`wn_combat_beat_dropped_engine_owns_round`, measured 2026-07-03) makes the narrator-beat drive doctrine-dead in a live AWN combat — `awn` is WN-family per `is_live_wn_combat`. A live WN round resolves ONLY on the player's DICE_THROW. Exempting mutation beats from the drop would balance the native engine against the bound ruleset (the exact ADR-143 trap; 158-53 precedent ruled the same for WWN cast). The "real path" is now the dice seam.
  - Severity: major
  - Forward impact: Dev's GREEN must build the dice-path mutation route (payload field → sealed commit → `_apply_committed_player_beat` → use_ops), NOT re-enable narrator beats in live WN combat. Reviewer should not expect the old drive shape.
  → ✓ ACCEPTED by Reviewer: ADR-143/SOUL doctrine is unambiguous and the drop was measured live; rewiring the drive seam is compliance, not divergence.
- **Pinned `mutation_id` as a `DiceThrowPayload` field (the `spell_id` transport)**
  - Spec source: story description ("emit awn.mutation.used (component + payload identifying the mutation + actor) on the use decision")
  - Spec text: no transport named for how the commit identifies WHICH mutation
  - Implementation: tests construct `DiceThrowPayload(..., mutation_id=...)` — RED today via `extra=forbid` ValidationError
  - Rationale: exact 102-2 precedent (`spell_id` names WHICH prepared spell); a mutant may own several mutations and the beat is the generic "Use Mutation" texture, so the commit must name one. The UI picker parity makes any other transport a reinvention.
  - Severity: minor
  - Forward impact: Dev threads `mutation_id` through `DiceThrowPayload` → `WnSealedCommit` → the round walk; the `# type: ignore[call-arg]` markers in the two rewired tests come off with the field.
  → ✓ ACCEPTED by Reviewer: exact 102-2 transport parity; the field shipped typed and extra=forbid-validated.
- **Pinned face-independence (a face of 1 still uses the mutation)**
  - Spec source: story description (use decision → span; no to-hit semantics specified)
  - Spec text: —
  - Implementation: `test_mutation_use_is_not_gated_on_the_d20_face` asserts span + Strain on face=1
  - Rationale: use_ops doctrine is already codified ("the power fires, the target saves" — cost paid before save resolution) and the 102-2 cast twin pins the same ("automatic casting; a face-gated cast is a generic INT throw wearing a robe"). Gating on the WIS throw would re-create the generic-stat resolution this story kills.
  - Severity: minor
  - Forward impact: if Architect rules AWN mutation use SHOULD be to-hit-gated (diverging from the cast parity), this one test changes — the rest of the suite stands.
  → ✓ ACCEPTED by Reviewer: use_ops already codifies pay-cost-then-target-saves; face-gating would re-create the generic-stat-throw disease.
- **Pinned malformed-commit guards as `DiceDispatchError` raises (match="mutation_id")**
  - Spec source: story description ("Needs investigation… emit it on the use decision")
  - Spec text: —
  - Implementation: missing-mutation_id / unmarked-beat / non-AWN-ruleset commits assert `pytest.raises(DiceDispatchError, match="mutation_id")`
  - Rationale: the dice-path idiom (102-2 cast guards: loud, TYPED, pre-mutation rejections; No Silent Fallbacks). The narrator route's refused-span idiom (`beat_no_mutation_id`) stays for the apply path; dispatch-time shape errors raise. Match kept to the one token Dev's messages must contain.
  - Severity: minor
  - Forward impact: Dev writes the guard messages; each must contain "mutation_id" (any phrasing).
  → ✓ ACCEPTED by Reviewer: DiceDispatchError is the dice-path idiom; both guards raise pre-mutation as the cast precedent does.

### Dev (implementation)
- **Unknown-to-catalog mutation_id refuses via the spine span, not a dispatch raise**
  - Spec source: session file, TEA Delivery Finding #3 (Improvement, non-blocking)
  - Spec text: "the cast precedent also dispatch-validates a spell_id unknown to the resolved catalog (loud DiceDispatchError). The mutation route should mirror it"
  - Implementation: an unknown mutation_id passes dispatch and is refused by `_resolve_mutation_for_beat`'s existing `unknown_mutation` guard (`awn.mutation.refused` span) rather than raising at dispatch
  - Rationale: minimalist discipline — no test demands the raise, and the spine's catalog guard already exists and is span-visible (engagement, not silence). The cast needed dispatch-time catalog validation because its spine assumed a resolved catalog; the mutation spine validates internally.
  - Severity: minor
  - Forward impact: if a UI wants a typed 4xx-style rejection for a stale mutation picker, a follow-up adds the dispatch check; the GM panel already sees the refusal.
  → ✓ ACCEPTED by Reviewer: span-visible refusal satisfies engagement; note the security specialist independently flagged the same deferred-catalog-check ordering (unbounded string persisted pre-validation) — the existing TEA Improvement finding now carries that corroboration.
- **Out-of-scope hygiene commit: two pre-existing ruff findings fixed**
  - Spec source: session file, Sm Assessment ("Scope discipline: AWN mutation span/effect path only")
  - Spec text: "no unrelated test-suite hygiene (that's 158-55)"
  - Implementation: `7745140e` auto-fixes UP037 (dungeon/themes.py) + I001 (telemetry/spans/__init__.py) — both pre-existing on develop, both `ruff --fix` trivial
  - Rationale: the repo-wide lint gate (`uv run ruff check .` via pf check / dev-exit) fails on them, blocking THIS story's exit through no fault of its diff. Isolated in a separate chore commit for easy review/revert.
  - Severity: minor
  - Forward impact: none — mechanical fixes, no behavior change.
  → ✓ ACCEPTED by Reviewer: isolated chore commit, verified pure `ruff --fix` output, unblocks the repo-wide lint gate.

### Reviewer (audit)
- **Incomplete cast-guard mirror — the opposed_check rejection was dropped:** Dev's deviation log and the guard comment both claim the mutation guards mirror "the 102-2 cast-guard contract," but the cast block's `resolution_mode == opposed_check` loud rejection (dice.py:500-507 — added in 102-2's own review round for exactly the silent-spine-skip failure mode) has no mutation twin. Not documented by TEA/Dev. Severity: High — this is the blocking finding in the Reviewer Assessment.
  → ✓ RESOLVED in rework round 1 (test `bdb6eef4`, fix `73b155aa`): clause added, gate factored into `_is_awn_mutation_beat`, re-review APPROVED.