---
story_id: "97-3"
jira_key: ""
epic: "97"
workflow: "tdd"
---
# Story 97-3: Dice banner DC has two sources of truth — client formula vs server effective difficulty

## Story Details
- **ID:** 97-3
- **Jira Key:** (not configured)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-07T16:56:14Z
**Round-Trip Count:** 2

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-07T15:54:35Z | 2026-06-07T15:56:41Z | 2m 6s |
| red | 2026-06-07T15:56:41Z | 2026-06-07T16:09:48Z | 13m 7s |
| green | 2026-06-07T16:09:48Z | 2026-06-07T16:26:26Z | 16m 38s |
| review | 2026-06-07T16:26:26Z | 2026-06-07T16:35:42Z | 9m 16s |
| red | 2026-06-07T16:35:42Z | 2026-06-07T16:42:06Z | 6m 24s |
| green | 2026-06-07T16:42:06Z | 2026-06-07T16:50:22Z | 8m 16s |
| review | 2026-06-07T16:50:22Z | 2026-06-07T16:53:00Z | 2m 38s |
| green | 2026-06-07T16:53:00Z | 2026-06-07T16:55:02Z | 2m 2s |
| review | 2026-06-07T16:55:02Z | 2026-06-07T16:56:14Z | 1m 12s |
| finish | 2026-06-07T16:56:14Z | - | - |

## Reviewer Assessment (round 3 — final)

**Verdict:** APPROVED

**Scope:** round-2 finding verification only — the code was fully reviewed in rounds 1-2 (round-1 Subagent Results table + full checklist stand; round-2 verified all 16 findings fixed).

- [VERIFIED] Round-2 [HIGH] (stray repo-wide reformat) is dead — `fdeedf8c` restored 163 files to develop's content; `git diff --name-only develop...HEAD` is exactly the 8 story files; the revert commit touched **zero** story files, so the round-2-reviewed code is byte-identical; clean tree. Independently confirmed (own git inspection) + testing-runner `97-3-dev-green-rework2` (247/247 targeted tests, ruff check clean, story files format-clean).
- [VERIFIED] All round-1 findings remain fixed (verified line-level in round 2; no code changed since — see above).

**Data flow traced:** (rounds 1-2, unchanged) pack YAML → beat offer (server-authored difficulty per resolver: native formula / target AC / opposed per-side / hacking tier+alert) → WS → tile + banner → DICE_THROW → resolution → DICE_RESULT — one author end-to-end.
**Pattern observed:** good — resolver-aware authoring branch at the single offer site (confrontation.py), single-sourced with `attack_params` for the SWN family; surgical revert preserving story content (`fdeedf8c`).
**Error handling:** loud refusal at both surfaces (console + transient strip); loud ValueError on unstampable hacking tier; no silent fallbacks remain ([EDGE]/[SILENT]/[TEST]/[DOC]/[TYPE]/[SEC]/[SIMPLE]/[RULE] dispositions per round-1 table).
**Handoff:** To SM (The Announcer) for finish-story — PR creation + merge are SM's.

## Dev Assessment (rework round 2 — commit hygiene)

**Implementation Complete:** Yes (no code change — history hygiene only)

**Files Changed:**
- `sidequest-server` commit `fdeedf8c` — restored 163 unrelated files to develop's content, reverting the stray repo-wide ruff reformat that `28387c48` swept in via `git add -A` after the testing-runner formatted the repo. Branch diff vs develop is now exactly the 8 story files (verified by testing-runner run `97-3-dev-green-rework2`: 247/247 targeted tests, ruff check clean, story files format-clean, clean tree). Pushed.

**Lesson applied (dev-gotchas 59-31 precedent):** unsanctioned subagent side effects get reverted, not absorbed — and `git add -A` after a subagent lint run is how they sneak in. Sidecar updated.

**Handoff:** To Reviewer (The Argument Professional) for round-3 verification.

## Dev Assessment (rework round 1)

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/server/dispatch/confrontation.py` — the offer-authoring branch now dispatches on the cdef, not just the ruleset: `opposed_check` → native-formula per-side DC (via `get_ruleset_module("native").compute_dc`, the formula `_opposed_dc` documents itself as mirroring); cwn `hacking` → security-tier DC + alert (mirrors the dispatch `is_net_run` arithmetic, fails loud on an unstamped tier); else → `ruleset.offer_difficulty`. Per-PC supplier uses `genre_pack.rules` direct attribute access (review MEDIUM — no getattr fallback). Docstring gains the `rules` paragraph (review LOW).
- `sidequest-server/sidequest/game/ruleset/swn.py` — `offer_difficulty` parameters annotated (`beat: BeatDef, target_core: object | None`, review LOW); import order ruff-fixed.
- `sidequest-ui/src/components/ConfrontationOverlay.tsx` — BeatTile DC chip reads `beat.difficulty`; no chip when absent (no formula resurrection); lying "all three agree" comment rewritten; BeatOption block comment aligned (review HIGH-2 + LOWs).
- `sidequest-ui/src/App.tsx` — malformed-offer refusal also calls `setTransientError` (player-visible loudness; `setTransientError` is a stable state setter, no dep change needed).
- `docs/api-contract.md` (orchestrator) — per-beat `difficulty` contract note under the combat/confrontation section, 03cf30a precedent (review MEDIUM). Committed to orchestrator main.

**Reviewer's open question (dogfight):** answered — space_opera's `dogfight` def is `resolution_mode: sealed_letter_lookup` with **no beats list**, so no gunnery beats flow through the offer payload; `ship_attack_params` difficulty never reaches a beat tile. No divergence surface exists.

**Tests:** 12/12 server story tests + 4/4 UI story tests GREEN (testing-runner run `97-3-dev-green-rework1`); targeted server regression suite 250/250 (dice dispatch, ruleset modules, awn combat, net_run lifecycle/resolution); full UI suite 1900/1901 (the 1 failure is the known pre-existing `lobby-start-ws-open` timeout flake); `tsc --noEmit` clean; ruff clean.

**Branch:** `feat/97-3-dice-banner-dc-single-source` pushed in server + ui; api-contract note pushed on orchestrator main. No PR created (SM finish-phase responsibility).

**Handoff:** To Reviewer (The Argument Professional) for re-review.

## TEA Assessment (rework round 1)

**Tests Required:** Yes
**Reason:** Review REJECTED with two HIGH findings, both testable logic gaps; the rework contract must be pinned RED before Dev touches the seam again.

**Test Files (extended, same suites):**
- `sidequest-server/tests/server/test_dice_dc_single_source_97_3.py` — +6 tests: `TestOpposedCheckOfferRespectsResolutionMode` (cwn opposed_check offer == `_opposed_dc` formula 14, NOT target AC 17 — HIGH-1; native opposed pin), `TestHackingOfferIsSecurityDc` (cwn hacking offer == tier DC + alert = 11 — review MEDIUM, mirrors dispatch is_net_run), `TestWwnRoundTrip` (wwn offer==resolution — review MEDIUM, passing regression pin), `TestBeatDcAuthoredSpan` (span fires with ruleset + offered numbers; stays silent on rules=None — review MEDIUM, passing pins). Module docstring de-RED-ified (review LOW).
- `sidequest-ui/src/__tests__/dice-dc-server-authored-97-3.test.tsx` — +2 tests and 1 extension: BeatTile renders `DC {beat.difficulty}` not the formula (HIGH-2); naked beat renders NO DC chip (no formula resurrection); the refusal test now also requires the `transient-error-banner` (player-visible loudness — review Devil's Advocate / Alex rubric). Module docstring de-RED-ified.

**Tests Written:** 8 new/extended over the rework findings
**Status:** RED verified (testing-runner run `97-3-tea-red-rework1`): server 10 pass / 2 fail (both on "offered 17" — the AC author still in charge of opposed + hacking offers); UI 1 pass / 3 fail (tile shows DC 14 formula; naked tile invents DC 14; no transient banner on refusal). Zero import/fixture failures. The 4 passing new tests are deliberate regression pins (wwn round-trip, span emission/silence, native opposed).

**Rule Coverage (delta):** OTEL discipline now asserted (span tests); No Silent Fallbacks extended to the tile surface and the player-visible channel; cwn/wwn ruleset coverage closes the review's enumeration gap.
**Self-check:** 0 vacuous tests — every new test asserts a concrete number, named span attribute, or explicit DOM absence.

**Handoff:** To Dev (Bicycle Repair Man) for rework GREEN. Contract: (1) offer authoring must consult `cdef.resolution_mode` (opposed_check → per-side `_opposed_dc`/native formula) and `category == "hacking"` under cwn (tier DC + alert, mirroring dispatch); (2) BeatTile renders `beat.difficulty`, no chip when absent; (3) refusal path calls `setTransientError`; plus the review's non-test fixes — `genre_pack.rules` direct access (MEDIUM), api-contract.md beats note (MEDIUM), `build_confrontation_payload` docstring `rules` paragraph, swn override annotations, BeatOption block comment (LOWs). Reviewer's open question: check whether any pack offers dogfight-gunnery beats through this payload (report in assessment).

## Reviewer Assessment (re-review, round 2)

**Verdict:** REJECTED — one finding, format/commit-hygiene only; routed straight back to Dev (green rework), no TEA round needed.

**Scope:** rework delta (server `b72acc11..28387c48`, ui `6cd1a03..552bc62`, orchestrator api-contract note) + verification that every round-1 finding is dead.

### Round-1 findings — verification

| Round-1 finding | Status | Evidence |
|---|---|---|
| [HIGH] opposed_check banner regression | **FIXED** | Authoring branch dispatches on `cdef.resolution_mode`; cwn opposed offer == 14 (native/`_opposed_dc` formula), pinned RED→GREEN (`97-3-tea-red-rework1` fail "offered 17" → `97-3-dev-green-rework1` 12/12). Native-opposed pin passes. `_offer_dc` for opposed uses native `compute_dc` — arithmetic identical to `_opposed_dc` (`getattr(beat,"base",1)` ≡ `beat.base` default-1 for BeatDef inputs). |
| [HIGH] BeatTile client formula | **FIXED** | `dc = typeof beat.difficulty === "number" ? beat.difficulty : null`; chip renders only when non-null; tile test pins DC 17 shown / DC 14 absent; naked beat renders no chip. Lying comment rewritten. |
| [MEDIUM] cwn/wwn coverage | **FIXED** | `TestOpposedCheckOfferRespectsResolutionMode`, `TestHackingOfferIsSecurityDc` (tier 9 + alert 2 = 11, loud ValueError on unstamped tier mirroring dispatch), `TestWwnRoundTrip`. |
| [MEDIUM] beat_dc_authored span unasserted | **FIXED** | `TestBeatDcAuthoredSpan` — fires with ruleset + per-beat numbers; stays silent on `rules=None`. |
| [MEDIUM] getattr rules fallback | **FIXED** | `rules=genre_pack.rules` direct access with rationale comment. |
| [MEDIUM] api-contract note | **FIXED** | Per-beat `difficulty` contract block added under combat/confrontation (orchestrator main, follows 03cf30a precedent). |
| [LOW] ×5 (comments, docstrings, annotations) | **FIXED** | BeatOption block comment, "(RED)" titles, `rules` docstring paragraph, swn annotations. `getattr(armor_class, 10)` left as-is per finding's "optional" — acceptable, pre-existing parity. |
| Devil's Advocate (a) dogfight beats | **CLOSED** | space_opera `dogfight` def is `sealed_letter_lookup` with no beats list — no offer surface exists. |
| Devil's Advocate (b) player-visible refusal | **FIXED** | Refusal path calls `setTransientError`; pinned by the extended UI test (`transient-error-banner`). |

### New finding (round 2)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **Story commit contains a repo-wide reformat of ~160 unrelated files.** `28387c48` is 165 files / +1127/−901: the testing-runner's lint step ran `ruff format` across the repo (develop is ~165 files behind its own formatter) and Dev's `git add -A` swept it all into the story fix. Verified format-only (comment realignment, string-concat joins — ruff format is AST-preserving by tool contract; targeted suites 250/250). Not a correctness risk — a review-integrity and history risk: the story PR diff is ~90% noise, bisect/revert of this commit drags 160 files, and it's an unsanctioned subagent side effect swept in blind (cf. dev-gotchas 59-31: don't accept unsanctioned subagent edits). | server commit `28387c48` | Restore the unrelated files to develop's content in a follow-up commit (`git checkout develop -- <files>` for everything outside the story's file set, commit as revert-of-stray-reformat). The repo-wide format catch-up belongs in its own chore commit/PR. Story file set: `sidequest/game/ruleset/{base,swn}.py`, `sidequest/server/dispatch/{confrontation,dice}.py`, `sidequest/server/websocket_session_handler.py`, `sidequest/handlers/yield_action.py`, `sidequest/telemetry/spans/encounter.py`, `tests/server/test_dice_dc_single_source_97_3.py`. |

**Subagent note (round 2):** specialists were not re-spawned for this round — the delta beyond the verified round-1 scope is the authoring-branch rework (covered line-level above, RED→GREEN documented by two independent testing-runner runs) and a mechanical formatter sweep (verified format-only by spot-diff + tool contract). Round-1 Subagent Results table below stands for the full-diff analysis; `All received: Yes` per round 1.

**Routing:** findings are format/commit-hygiene only → green rework → Dev (per exit protocol §6).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1 pre-existing eslint warning, verified present on develop) | N/A |
| 2 | reviewer-edge-hunter | Yes | Skipped | disabled | Disabled via settings (own edge audit performed: opposed_check mode, withdrawn/unseated targets, NaN difficulty, table-type empty beats) |
| 3 | reviewer-silent-failure-hunter | Yes | Skipped | disabled | Disabled via settings (own audit: UI refusal is loud; rules=None path documented; two getattr-default sites flagged via rule-checker) |
| 4 | reviewer-test-analyzer | Yes | findings | 11 | confirmed 4 (2 high, 2 medium), deferred 2 (medium), noted 5 (low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 6 | confirmed 6 (1 escalated to HIGH live bug, 1 medium, 4 low) |
| 6 | reviewer-type-design | Yes | Skipped | disabled | Disabled via settings (rule-checker TS/PY type checks covered the domain: 2 advisory findings confirmed low) |
| 7 | reviewer-security | Yes | Skipped | disabled | Disabled via settings (own audit: no user input crosses the new code; difficulty is server-authored state; runtime typeof validation at the WS boundary) |
| 8 | reviewer-simplifier | Yes | Skipped | disabled | Disabled via settings (own audit: no dead code; offer_difficulty seam is minimal; no over-abstraction) |
| 9 | reviewer-rule-checker | Yes | findings | 5 | confirmed 4 (low/medium advisories), dismissed 1 (runtime imports — consistent with file's documented local-import bootstrap pattern, confrontation.py:179-183) |

**All received:** Yes (4 ran, 5 disabled via settings; all rows accounted)
**Total findings:** 16 confirmed (2 high, 4 medium, 10 low), 1 dismissed (with rationale), 2 deferred

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **opposed_check banner regression under SWN-family rulesets.** `road_warrior` (ruleset: cwn) defines two live `resolution_mode: opposed_check` confrontations (Wasteland Bargain, Road Chase). Opposed_check resolves the player's d20 vs `_opposed_dc(beat)` — the native 10+2·\|base\| formula (narration_apply.py:6362) — for EVERY ruleset. The new SWN-family `offer_difficulty` advertises the opponent's armor class on those same beats, so the banner now shows AC while resolution uses the native formula. **Pre-fix the client formula coincidentally matched `_opposed_dc`; this change makes road_warrior's opposed banner wrong where it used to be right.** | `sidequest-server/sidequest/game/ruleset/swn.py:76` + `narration_apply.py:6026-6033` + `sidequest-content/genre_packs/road_warrior/rules.yaml` | `offer_difficulty` (or the authoring site in `build_confrontation_payload`, which has `cdef` in hand) must respect `cdef.resolution_mode`: opposed_check beats offer the per-side `_opposed_dc`/native-formula DC regardless of ruleset family. TEA: pin with a cwn+opposed_check round-trip test (offer == `_opposed_dc(beat)`). |
| [HIGH] | **BeatTile still displays the dead client formula.** `BeatTile` computes `const dc = Math.min(30, Math.max(10, 10 + Math.abs(base) * 2))` and renders it on every beat tile — its own comment calls it "the honest difficulty signal... matches what the dice panel displays on commit" (playtest 59-8, Sebastien/Jade lane). Under SWN the tile now shows 14 while the armed banner shows 17. The tile is a displayed pre-roll target → direct AC1 violation, and the comment's "all three agree" claim is now false. | `sidequest-ui/src/components/ConfrontationOverlay.tsx:485-488` | Render `beat.difficulty` on the tile (with the same loud-absence handling as App.tsx — likely render no DC chip rather than a formula number) and rewrite the stale comment. TEA: pin with a tile-render test (tile DC text == server difficulty, ≠ formula value). |
| [MEDIUM] | [TEST] cwn/wwn rulesets have zero offer==resolution coverage; both inherit SWN's AC path and both are live (neon_dystopia, elemental_harmony, road_warrior). Directly implicated by the HIGH-1 opposed_check finding. | `tests/server/test_dice_dc_single_source_97_3.py` | Parametrized round-trip tests for cwn + wwn, including the opposed_check and (existing logged gap) hacking cases. |
| [MEDIUM] | [TEST] The `confrontation.beat_dc_authored` span — the GM-panel lie-detector for this very fix — is asserted by no test. A refactor that drops the emit leaves the panel blind with no failing test (CLAUDE.md OTEL discipline). | `tests/server/test_dice_dc_single_source_97_3.py` | Assert the span fires (otel_capture pattern, cf. test_awn_combat_dispatch.py) with correct ruleset + non-empty beat_difficulties in the native and SWN offer tests. |
| [MEDIUM] | [RULE] `rules=getattr(genre_pack, "rules", None)` at the per-PC supplier call site is a No-Silent-Fallbacks pattern violation — production packs always have `.rules` (validated at load); attribute access should fail loud. | `sidequest-server/sidequest/server/dispatch/confrontation.py` (per-PC supplier call site) | Use `genre_pack.rules` directly. |
| [MEDIUM] | [DOC] `docs/api-contract.md` has no contract note for the new per-beat `difficulty` wire field — a public CONFRONTATION payload change (precedent: NARRATION_END `round` note, commit 03cf30a). | `docs/api-contract.md` | Add the beats-shape note: per-ruleset semantics + absent-means-uncommittable. |
| [LOW] | [DOC] `BeatOption` block comment (line ~43) still says base "drives DC scaling"; field JSDoc was updated but the enclosing comment was not. | `sidequest-ui/src/components/ConfrontationOverlay.tsx:43` | Align the block comment. |
| [LOW] | [DOC] "(RED)" stale in both new test-file module docstrings — suites are now the green regression pin. | `test_dice_dc_single_source_97_3.py:1`, `dice-dc-server-authored-97-3.test.tsx:1` | Reword titles. |
| [LOW] | [DOC] `build_confrontation_payload` docstring documents every param except the new `rules`; the None-contract (no difficulty keys → UI uncommittable) is non-obvious and only lives in inline comments. | `sidequest-server/sidequest/server/dispatch/confrontation.py` docstring | Add a `rules` paragraph. |
| [LOW] | [RULE] `offer_difficulty` override in swn.py drops the param annotations the base declares (`beat: BeatDef, target_core: object \| None`). | `sidequest-server/sidequest/game/ruleset/swn.py:76` | Add annotations. |
| [LOW] | [RULE] `getattr(target_core, "armor_class", 10)` silently masks a present-core-missing-AC content bug. Pre-existing pattern (attack_params had it); not a regression — flagged for the seam rework since the line is being touched anyway. | `sidequest-server/sidequest/game/ruleset/swn.py:81` | Optional in rework: fail loud when core present but AC absent. |
| [LOW] | [TEST] MagicMock pack absorbs unknown attribute reads (silent-mock risk); filtered-offer (recipient_pc) difficulty stamping untested; withdrawn-opponent (actor seated, core unresolvable) path untested; UI non-null `!` assertions (accepted RTL pattern). | test files | Address opportunistically in rework. |

### Rule Compliance

- **No Silent Fallbacks:** UI refusal path compliant (loud console.error, no formula resurrection — App.tsx). `rules=None` legacy path documented and intentional (bootstrap/replay reconstruction; absence is loud downstream) — compliant within diff scope. **Two violations confirmed:** `getattr(genre_pack, "rules", None)` (MEDIUM, above) and `getattr(target_core, "armor_class", 10)` (LOW, pre-existing pattern parity).
- **No Stubbing / dead code:** Compliant — the client formula was deleted, not bypassed; no empty shells. The old `rawDc` is fully gone (`grep rawDc src/` → only the historical comment in the new code's explanation).
- **Don't Reinvent — Wire Up What Exists:** Compliant — fix reuses `_opposite_side_first_actor`, `get_ruleset_module`, the established SpanRoute pattern, and the existing `core_resolver` threading. **But:** HIGH-1 shows the seam *under*-reused what exists — it ignored `_opposed_dc`/`resolution_mode`, the third DC author already in production.
- **Verify Wiring, Not Just Existence:** `offer_difficulty` and the span have non-test consumers on three production emit paths (rule-checker ADD-5, verified). Wiring tests run the production builder + dispatcher (no source-text greps — ADD-7 compliant).
- **OTEL Observability Principle:** Span correctly registered and emitted (ADD-6 compliant) — but unasserted by any test (MEDIUM above).
- **lang-review python.md:** PY-1..PY-13 enumerated by rule-checker across all 8 changed server files — 3 advisory findings (annotations, runtime imports [dismissed: consistent with this file's documented local-import bootstrap pattern], getattr default), 0 hard violations.
- **lang-review typescript.md:** TS-1..TS-13 enumerated across all 5 changed UI files — 1 advisory (test-file non-null assertions, accepted RTL pattern), 0 hard violations.

### Observations (own analysis)

1. [HIGH] opposed_check regression — see severity table row 1 (own finding; traced narration_apply.py:6362 → `_opposed_dc` → road_warrior rules.yaml `resolution_mode: opposed_check` ×2).
2. [HIGH] BeatTile formula DC — see row 2 (comment-analyzer flagged; verified myself at ConfrontationOverlay.tsx:488).
3. [VERIFIED] SWN offer/resolution single-sourcing — swn.py:91 `attack_params` reads `target_number=self.offer_difficulty(...)`; the two numbers are one code path and cannot diverge for beat_selection mode. Complies with the story's single-author contract and Don't-Reinvent.
4. [VERIFIED] Data flow traced end-to-end: pack YAML `base`/opponent AC → BeatDef/CreatureCore → `build_confrontation_payload` (difficulty stamped, confrontation.py:301) → ConfrontationPayload.beats (list[dict] — no protocol model change needed, extra="forbid" only governs top-level keys) → WS CONFRONTATION → `confrontationData.beats` → `handleBeatSelect` typeof-guard → armed DiceRequest → InlineDiceTray TARGET (`diceRequest.difficulty`) → DICE_THROW beat_id → `attack_params.target_number` → DICE_RESULT.difficulty. Equality verified by 6 server round-trip tests for native + swn beat_selection.
5. [VERIFIED] UI error handling: missing/non-number difficulty → loud refusal, no request armed, player can re-select (App.tsx typeof guard); NaN impossible via JSON wire. Complies with No Silent Fallbacks.
6. [VERIFIED] All four production emit paths thread `rules=` (yield_action, dice mid-turn, session-handler canonical union, per-PC supplier) — preflight-confirmed tests green on all four files' suites (237 server, 34 UI targeted).
7. [VERIFIED] Pre-existing eslint warning (App.tsx:1438 currentRound dep) confirmed present on develop — not introduced by this branch.
8. [EDGE] Hard questions audited: empty beats list (table types) → zip over empty, fine; difficulty ge=1 protocol bound — AC ≥ 1 and formula ≥ 10, fine; opponent death/AC change mid-encounter → mid-turn re-emits refresh the offer each beat, fine; race between offer and throw uses the same target selection (`_opposite_side_first_actor`) on both sides, fine.
9. [SILENT]/[SEC]/[TYPE]/[SIMPLE] domains (subagents disabled): own audits found the two getattr sites (logged above via [RULE]), no user-input crossing (difficulty is server state; UI runtime-validates the wire value), no over-engineering (the seam is one method + one loop), no dead code.
10. [TEST]/[DOC]/[RULE] subagent findings incorporated per severity table.

### Devil's Advocate

Suppose I argue this code is broken even where I marked it verified. The single-source claim rests on `attack_params` delegating to `offer_difficulty` — but that's only true for the SWN family. Native's `attack_params` still calls `compute_dc` directly while the offer path calls `offer_difficulty` → `compute_dc`; one refactor to native's formula in only one of those two methods and the invariant silently splits again, and only the round-trip tests (which DO exist for native — good) would catch it. The bigger lie is the word "single": I found a *third* author (`_opposed_dc`) the implementation never consulted, and it owns two live confrontations in road_warrior. What else didn't we consult? The CWN hacking branch (fourth author — security tier + alert), already logged as a known gap, advertises AC for hacking beats. The dogfight path (`ship_attack_params`, fifth author) — does any pack offer dogfight *beats* through this payload? If so, their offered difficulty is also AC-from-ground-combat, not the gunnery target number. A confused player in a perseus_cloud dogfight could see a tile DC, a banner DC, and a resolution DC that are three different numbers. And the malformed-offer refusal: the player presses a beat and *nothing happens* except a console line they will never open — Alex would click three times and assume the game froze. A user-visible transient error (the `setTransientError` channel exists two branches up!) would be the honest surface. Finally, the modifier remains client-computed with the native curve — the banner's "need N" line still lies under SWN even with a correct DC, so AC1 read strictly ("the displayed pre-roll target") is only half-met by this diff. The dogfight-beat question and the silent-refusal UX go to the rework as explicit checks.

**Findings added from Devil's Advocate:** (a) verify whether any dogfight-capable pack offers beats whose resolution is `ship_attack_params` — if yes, same class as HIGH-1 (TEA: add to rework scope as a check, not yet a conviction); (b) the UI refusal should surface via the existing `setTransientError` channel, not console-only (fold into HIGH-2's UI rework — Alex-pacing rubric, CLAUDE.md).

**Data flow traced:** pack YAML → BeatDef → offer (difficulty stamped) → WS → armed DiceRequest → banner → DICE_THROW → attack_params → DICE_RESULT (safe for native/swn beat_selection; broken for cwn opposed_check [HIGH-1] and the tile surface [HIGH-2]).
**Pattern observed:** good — seam method + delegation single-sourcing at swn.py:86-92; bad — display surfaces not enumerated before declaring a single author (tile missed).
**Error handling:** loud refusal verified at App.tsx typeof-guard; console-only loudness flagged for player-visible upgrade.
**Handoff:** Back to TEA (red rework) — both HIGH findings are testable logic bugs requiring new failing tests first.

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/game/ruleset/base.py` — new `RulesetModule.offer_difficulty(beat, target_core)` seam; default returns `compute_dc(beat)` (native dial formula)
- `sidequest-server/sidequest/game/ruleset/swn.py` — SWN override returns target armor class; `attack_params.target_number` now routes through the same method, so offer and resolution are structurally one number for the whole SWN family (swn → cwn → awn, swn → wwn)
- `sidequest-server/sidequest/server/dispatch/confrontation.py` — `build_confrontation_payload` gains `rules: RulesConfig | None`; when provided, resolves the ruleset module + the opposing side's core (`_opposite_side_first_actor` + `core_resolver`) and stamps `difficulty` on every offered beat dict; emits the new `confrontation.beat_dc_authored` OTEL span; per-PC supplier call site threads `rules=getattr(genre_pack, "rules", None)`
- `sidequest-server/sidequest/server/dispatch/dice.py` — mid-turn CONFRONTATION union emit threads `rules=pack.rules`
- `sidequest-server/sidequest/server/websocket_session_handler.py` — canonical full-union emit threads `rules=sd.genre_pack.rules`
- `sidequest-server/sidequest/handlers/yield_action.py` — partial-yield live frame threads `rules=sd.genre_pack.rules`
- `sidequest-server/sidequest/telemetry/spans/encounter.py` — `SPAN_CONFRONTATION_BEAT_DC_AUTHORED` ("confrontation.beat_dc_authored") + SpanRoute + context manager (GM-panel lie-detector: offered numbers vs resolution-time difficulty)
- `sidequest-server/tests/server/test_dice_dc_single_source_97_3.py` — fixture typo fix only (`"press"` → `"push"`; BeatKind is a closed enum) — deviation logged
- `sidequest-ui/src/App.tsx` — `handleBeatSelect` arms the DiceRequest from `beat.difficulty`; the `rawDc` client formula is deleted; a beat offer without a server-authored difficulty is refused with a loud `console.error` (No Silent Fallbacks)
- `sidequest-ui/src/components/ConfrontationOverlay.tsx` — `BeatOption.difficulty?: number` documented as the server-authored pre-roll target
- `sidequest-ui/src/__tests__/combat-player-echo-wiring.test.tsx`, `transient-error-autoclear-wiring.test.tsx` — commit-path beat fixtures gain `difficulty` (they model the server, which now always sends it)

**Tests:** 8/8 story tests passing (6 server + 2 UI); 49/49 dice/confrontation wiring tests passing; regression analysis CLEAN (testing-runner run `97-3-dev-green`). Server full-suite noise (26F/82E) characterized as pre-existing database-URL environment config, none touching confrontation/dice/ruleset paths. Ruff lint + format clean on changed files.

**Branch:** `feat/97-3-dice-banner-dc-single-source` — pushed in both repos (server `796999c1`, ui `4c07f55`). No PR created (SM finish-phase responsibility).

**ACs:**
1. ✅ Displayed pre-roll target equals the server's resolution difficulty for native and hp_depletion — single-sourced through `offer_difficulty`; round-trip equality pinned by tests.
2. ✅ `DICE_RESULT.difficulty` matches the banner — the banner now renders the same server-authored number resolution reports; `confrontation.beat_dc_authored` vs `dice.request_sent` spans give the screenshot+log verification pair.

**Handoff:** To verify phase (Mr. Praline — simplify + quality-pass).

## TEA Assessment

**Tests Required:** Yes
**Reason:** 3-pt bug, tdd workflow — the two-sources-of-truth divergence is precisely measurable and must be pinned before Dev touches either repo.

**Test Files:**
- `sidequest-server/tests/server/test_dice_dc_single_source_97_3.py` — 6 tests: the CONFRONTATION beat offer carries a server-authored per-beat `difficulty` (native formula; default-base edge; SWN target-AC divergence), and that offered number equals the difficulty `dispatch_dice_throw` resolves against (native, SWN, and SWN-unseated-opponent edge). Commit `83b94c0c`.
- `sidequest-ui/src/__tests__/dice-dc-server-authored-97-3.test.tsx` — 2 tests through App's production wire→state→prop chain (combat-player-echo harness pattern): `handleBeatSelect` arms the dice request (the TARGET banner source) from server-authored `beat.difficulty`, not the client formula; a beat offer missing `difficulty` is refused loudly with no formula fallback. Commit `ee1bfe4`.

**Tests Written:** 8 tests covering 2 ACs
**Status:** RED (verified by testing-runner, run 97-3-tea-red: 0 passed / 8 failed, all on the missing feature contract — server: `TypeError: unexpected keyword argument 'rules'`; UI: difficulty 14 (client formula) where 17 (server DC) expected, and silent formula fallback where loud refusal expected. No fixture/import failures.)

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks | `refuses a beat offer with no server-authored difficulty — loudly` (ui) | failing |
| Verify Wiring, Not Just Existence / wiring test | `test_native_offer_equals_dice_result_difficulty`, `test_swn_offer_equals_dice_result_difficulty` (offer→dispatch round-trip through production `build_confrontation_payload` + `dispatch_dice_throw`); UI suite drives App's production handlers, not a mock overlay | failing |
| No Source-Text Wiring Tests (server CLAUDE.md) | All server tests are fixture-driven behavior tests (synthetic pack + snapshot + real dispatch); zero `read_text()` greps | failing (by design) |
| Edge paranoia (boundary/degenerate input) | `test_native_beat_offer_difficulty_defaults_base_to_1` (absent base), `test_swn_unseated_opponent_offer_still_matches_resolution` (no target core) | failing |
| Sebastien/Jade player-facing math (CLAUDE.md) | SWN divergence tests pin AC ≠ native-formula values so the banner can't lie | failing |

**Rules checked:** 5 of 5 applicable project-rule families have test coverage (python.md/typescript.md lang-review checklists reviewed; the constructor/newtype-centric checks don't apply to a contract-pinning bug suite — the applicable families above are covered)
**Self-check:** 0 vacuous tests — every test asserts a concrete difficulty value or explicit null/refusal; no `let _`, no bare `is_some`-style assertions

**Handoff:** To Dev (Bicycle Repair Man) for implementation. Contract summary: (1) `build_confrontation_payload` accepts `rules` (the pack `RulesConfig`) and serializes a server-authored `difficulty` onto every offered beat — native: `compute_dc(beat)`; SWN: target AC via the existing `core_resolver`/encounter seating; (2) production call sites thread `rules` through; (3) UI `handleBeatSelect` arms the dice request from `beat.difficulty` and refuses loudly when absent (delete the `rawDc` formula); (4) `BeatOption` gains `difficulty`; (5) per the OTEL principle, emit a watcher span on the DC-authoring decision (finding logged; span name Dev's choice).

## Sm Assessment

Setup complete for story 97-3 (3 pts, tdd workflow, repos: server,ui).

- **Session file:** created with workflow tracking header and phase history.
- **Story context:** `sprint/context/context-story-97-3.md` written with ACs, problem statement, and implementation guidance.
- **Branches:** `feat/97-3-dice-banner-dc-single-source` created in sidequest-server and sidequest-ui (off develop per repos.yaml gitflow strategy).
- **Jira:** not configured for this project — claim explicitly skipped.
- **Routing:** phased tdd workflow; next phase is red, owned by tea.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The client also computes the roll *modifier* with the native D&D curve (`Math.floor((stat-10)/2)`, App.tsx:1568) while SWN uses its own attribute-modifier curve (`swn_attribute_modifier`) — the banner's "need N" line can lie about the modifier the same way it lies about the DC. Out of 97-3's stated scope (DC only), but the same single-source fix seam (server-authored numbers on the beat offer) could carry the modifier too. Affects `sidequest-ui/src/App.tsx` (modifier authorship). *Found by TEA during test design.*
- **Improvement** (non-blocking): Per CLAUDE.md's OTEL Observability Principle, the Dev fix should emit a watcher span on the DC-authoring decision (per-beat difficulty attached to the offer) so the GM panel can verify banner/resolution agreement — the existing `emit_dice_request_sent` covers resolution-time only. Tests deliberately do not pin a span name to leave Dev free on the seam. Affects `sidequest-server/sidequest/server/dispatch/confrontation.py` (add OTEL emit). *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): CWN hacking confrontations resolve via the `is_net_run` branch (security-tier DC + alert modifier, dispatch/dice.py), but `offer_difficulty` for the SWN family returns target AC — so a CWN *hacking* beat offer now advertises the AC-based number, not the net-run effective DC. Out of 97-3's AC scope (native + hp_depletion only), but the same banner-lie exists there. Affects `sidequest-server/sidequest/game/ruleset/cwn.py` (override `offer_difficulty` for hacking-category defs using security_tier + opponent_metric, mirroring the dispatch net_run arm). *Found by Dev during implementation.*
- **Gap** (non-blocking): The roll *modifier* on the banner is still client-computed with the native curve (`Math.floor((stat-10)/2)`, App.tsx) — under SWN the server adds attack_bonus + combat_skill + SWN attr-mod, so the banner's "need N" line can still mis-state the needed face even with the DC now correct. Same fix seam: author per-beat `modifier` on the offer next to `difficulty`. (Duplicates TEA's modifier finding — confirmed real during implementation.) Affects `sidequest-ui/src/App.tsx`, `sidequest-server/sidequest/server/dispatch/confrontation.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Pre-existing server full-suite noise — 26 failures + 82 errors from missing database-URL config in the bare test-harness environment (test_app.py, test_forensics_routes.py, test_reference_*.py), unrelated to this story per testing-runner characterization (run 97-3-dev-green). Affects test environment setup, not code. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking — drives the rejection): `offer_difficulty` ignores `cdef.resolution_mode`; opposed_check confrontations in SWN-family packs (road_warrior: Wasteland Bargain, Road Chase) get an AC banner against a native-formula resolution (`_opposed_dc`). Affects `sidequest-server/sidequest/game/ruleset/swn.py` + `sidequest/server/dispatch/confrontation.py` (consult resolution_mode when authoring). *Found by Reviewer during code review.*
- **Gap** (blocking — drives the rejection): BeatTile renders the dead client formula as its DC chip. Affects `sidequest-ui/src/components/ConfrontationOverlay.tsx:488` (render beat.difficulty). *Found by Reviewer during code review.*
- **Question** (non-blocking): do any packs offer beats whose resolution is `ship_attack_params` (dogfight gunnery)? If yes, their offered difficulty has the same divergence class — check during rework. Affects `sidequest-server/sidequest/game/ruleset/swn.py` (ship gunnery offer authorship). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the UI's malformed-offer refusal is console-only; surface via the existing `setTransientError` channel so a player (Alex-pacing rubric) sees why the click did nothing. Affects `sidequest-ui/src/App.tsx` (refusal path). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `docs/api-contract.md` needs a CONFRONTATION beats-shape note for the new `difficulty` wire field (precedent: 03cf30a). Affects `docs/api-contract.md`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned one of the two candidate fix approaches (beat-offer DC) instead of leaving both open**
  - Spec source: context-story-97-3.md, Implementation Notes
  - Spec text: "choosing one of two approaches: 1. Beat commit round-trip ... 2. Pre-roll correction ... Either way, the server must be the single source of truth for DC"
  - Implementation: Tests pin the contract that `build_confrontation_payload` (the beat offer) carries a server-authored per-beat `difficulty` (via a new `rules` kwarg), and the client arms its dice request from `beat.difficulty`. Both spec'd alternatives require a new pre-roll round-trip; the current flow rolls dice physics *before* the server hears anything (DICE_THROW carries the already-rolled face), so a "pre-roll correction" message cannot beat the banner without restructuring the throw flow. The beat offer already travels to the client with every CONFRONTATION frame and the server has the target core in hand there — authoring DC at offer time satisfies both ACs with no new message type.
  - Rationale: Tests must compile against a concrete seam; the offer-time contract is the minimal one consistent with "server is the only DC author" and the existing physics-is-the-roll flow (story 34-12).
  - Severity: minor
  - Forward impact: Dev implements the `rules` kwarg + per-beat difficulty serialization and the UI consumption; if Dev finds a superior seam, the round-trip equality tests (offer == resolution) remain valid — only the two offer-construction tests would need their call shape adjusted.
- **Missing server difficulty refuses the commit loudly (not tolerated, not fallback)**
  - Spec source: context-story-97-3.md, AC-1; CLAUDE.md "No Silent Fallbacks"
  - Spec text: "The displayed pre-roll target equals the difficulty the server resolves against" (the ACs don't say what happens when the server fails to author one)
  - Implementation: UI test pins that a beat offer lacking `difficulty` arms NO dice request and logs a console error/warning naming the missing field — falling back to the client formula is exactly the pre-fix bug.
  - Severity: minor
  - Forward impact: During any transition window, a server that omits per-beat difficulty makes beats uncommittable in the UI — fail-loud by design; Dev must ship both sides together (repos: server,ui in one story, so this is the intended coupling).

### Dev (implementation)
- **Fixed a fixture typo in TEA's test file rather than treating it as contract**
  - Spec source: tests/server/test_dice_dc_single_source_97_3.py (TEA RED suite)
  - Spec text: native pack fixture declared `"kind": "press"` on the shove beat
  - Implementation: Changed to `"kind": "push"` — `BeatKind` is a closed enum (`strike|brace|push|angle`) and `"press"` fails pydantic validation before the test body runs
  - Rationale: The fixture could never construct; the test's *intent* (a base-less beat offers DC 12) is unchanged. No assertion was altered.
  - Severity: minor
  - Forward impact: none
- **`rules=None` legacy callers keep the difficulty-less payload shape**
  - Spec source: context-story-97-3.md, Implementation Notes ("the server must be the single source of truth for DC")
  - Spec text: implies every offer carries a server DC
  - Implementation: `build_confrontation_payload(rules=None)` (bootstrap/slug-resume reconstruction and pre-97-3 test callers) emits beats without `difficulty`; all four production emit paths thread `rules=` so live offers always carry it. The UI treats a difficulty-less beat as uncommittable and logs loudly — absence is fail-loud downstream, not silently tolerated.
  - Rationale: Matches the codebase's additive-payload convention (win_condition/hp keys, Story 85-3 pattern); forcing `rules` as required would break EventLog-replay reconstruction sites that have no pack in hand.
  - Severity: minor
  - Forward impact: any future caller that wants committable beats must pass `rules`; the UI refusal makes an omission visible immediately in playtest.

### Reviewer (audit)
- **TEA: "Pinned one of the two candidate fix approaches (beat-offer DC)"** → ✓ ACCEPTED by Reviewer: the offer-time contract is the right seam given physics-is-the-roll (a pre-roll correction message cannot beat the banner); the HIGH-1 finding is a gap *inside* the seam (resolution_mode not consulted), not a flaw of the seam choice itself.
- **TEA: "Missing server difficulty refuses the commit loudly"** → ✓ ACCEPTED by Reviewer: correct No-Silent-Fallbacks application; Devil's Advocate adds that the loudness should also reach the player surface (`setTransientError`), folded into rework scope.
- **Dev: "Fixed a fixture typo in TEA's test file"** → ✓ ACCEPTED by Reviewer: BeatKind is a closed enum; intent unchanged, no assertion altered.
- **Dev: "`rules=None` legacy callers keep the difficulty-less payload shape"** → ✓ ACCEPTED by Reviewer: documented additive-payload convention, absence is loud downstream — but the `getattr(genre_pack, "rules", None)` *call-site* spelling is FLAGGED separately as a MEDIUM finding (use plain attribute access; packs always have rules).
- **UNDOCUMENTED (Reviewer): the diff narrowed "displayed pre-roll target" to the banner only.** Spec (AC1) says "the displayed pre-roll target"; the BeatTile DC chip is also a displayed pre-roll target and was not migrated — neither TEA's tests nor Dev's implementation enumerated the display surfaces. Severity: H (this is HIGH-2 in the severity table). → ✓ RESOLVED in rework round 1 (BeatTile renders beat.difficulty; pinned by tile tests).

### Reviewer (audit — rework rounds)
- **TEA rework: "Hacking-offer correctness pulled INTO scope"** → ✓ ACCEPTED by Reviewer: my own round-1 fix-required text made it scope; one fixture, closes a live-pack banner lie.
- **TEA rework: "Player-visible refusal (transient banner)"** → ✓ ACCEPTED by Reviewer: agrees with my Devil's Advocate finding (b); Alex rubric.
- **Dev rework: "Opposed-check offer via native compute_dc, not _opposed_dc import"** → ✓ ACCEPTED by Reviewer: identical arithmetic, avoids a narration_apply import into the dispatch layer; the cwn opposed test pins the mirror. Consolidating the two mirror sites is a fair future cleanup, not a blocker.
- **Dev rework: "Hacking-offer tier failure raises at offer time"** → ✓ ACCEPTED by Reviewer: mirrors the dispatch refusal; an authored-but-wrong DC is the story's own bug class, and the lifecycle always stamps a tier.

### TEA (test design — rework round 1)
- **Hacking-offer correctness pulled INTO scope despite Dev's round-1 out-of-scope finding**
  - Spec source: Reviewer Assessment severity table (MEDIUM, cwn/wwn coverage row: "including the opposed_check and (existing logged gap) hacking cases"); story AC1 scopes only "native and hp_depletion"
  - Spec text: AC1: "for both native and hp_depletion rulesets"
  - Implementation: `TestHackingOfferIsSecurityDc` pins the cwn hacking offer to tier-DC+alert — beyond AC1's literal ruleset list
  - Rationale: The reviewer made it rework scope; an authored-but-wrong number on a live pack's wire is the story's own bug class, and the fixture cost is one test
  - Severity: minor
  - Forward impact: Dev must extend the offer-authoring branch for cwn hacking; closes Dev's round-1 non-blocking Gap finding
- **Player-visible refusal (transient banner) added to the refusal contract**
  - Spec source: Reviewer Devil's Advocate finding (b); CLAUDE.md Alex design implication
  - Spec text: "the UI refusal should surface via the existing `setTransientError` channel, not console-only"
  - Rationale: console.error is invisible to the table; the existing transient strip is the established channel for refused commits (session_unbound precedent)
  - Implementation: refusal test extended with `transient-error-banner` assertion
  - Severity: minor
  - Forward impact: none beyond App.tsx refusal path

### Dev (implementation — rework round 1)
- **Opposed-check offer authored via `get_ruleset_module("native").compute_dc`, not by importing `_opposed_dc`**
  - Spec source: Reviewer Assessment HIGH-1 fix-required ("offer the per-side `_opposed_dc`/native-formula DC")
  - Spec text: "opposed_check beats offer the per-side `_opposed_dc`/native-formula DC regardless of ruleset family"
  - Implementation: The authoring branch calls the native module's `compute_dc` — the formula `_opposed_dc` explicitly documents itself as mirroring — rather than importing `_opposed_dc` from the 6000-line `narration_apply` module into the dispatch layer
  - Rationale: Identical arithmetic, no narration_apply import surface in confrontation.py; both sites document the mirror relationship
  - Severity: minor
  - Forward impact: if `_opposed_dc` ever stops mirroring native `compute_dc`, the offer and the opposed resolver diverge again — the cwn opposed test (offer==14) pins the current arithmetic, and consolidating the two mirrors into one callable is a candidate cleanup
- **Hacking-offer tier failure raises at offer time (ValueError), mirroring the dispatch refusal**
  - Spec source: dispatch is_net_run branch (No Silent Fallbacks); review fix-required
  - Spec text: dispatch raises "net_run dispatch reached without a resolvable security tier"
  - Implementation: offer authoring raises the same class of loud error for a hacking cdef with no resolvable tier — this can fail a CONFRONTATION emit for a malformed lifecycle state rather than emitting a wrong number
  - Rationale: an authored-but-wrong DC is the story's own bug class; the lifecycle seam always stamps a tier (default_tier path), so the raise is unreachable absent a real bug
  - Severity: minor
  - Forward impact: none expected; if a legitimate tier-less hacking offer path emerges, it must stamp before emitting