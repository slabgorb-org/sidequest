---
story_id: "162-7"
jira_key: "none"
epic: "none"
workflow: "tdd"
---
# Story 162-7: All-sources-one-scene wiring test + understudy identity-split hunt

## Story Details
- **ID:** 162-7
- **Title:** All-sources-one-scene wiring test + understudy identity-split hunt: integration test spawning from every source asserting one identity per creature; understudy scenario flags two-names-one-enemy as a finding
- **Jira Key:** none
- **Workflow:** tdd
- **Type:** chore
- **Points:** 2
- **Repos:** server, understudy
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-06T13:28:23Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-06T11:52:41+00:00 | 2026-07-06T11:54:57Z | 2m 16s |
| red | 2026-07-06T11:54:57Z | 2026-07-06T12:23:41Z | 28m 44s |
| green | 2026-07-06T12:23:41Z | 2026-07-06T12:33:10Z | 9m 29s |
| review | 2026-07-06T12:33:10Z | 2026-07-06T13:28:23Z | 55m 13s |
| finish | 2026-07-06T13:28:23Z | - | - |

## Story Context

### Context: Epic-162 (NPC Origin Consolidation)

Story 162-7 is the **verification capstone** for epic-162: "NPC origin consolidation — one identity, one arbiter, derived Monster Manual". 

**Completed Foundation (162-1 through 162-6):**
1. **162-1:** Derive-don't-cache Monster Manual with content-sha + session-seed keyed pool
2. **162-2:** Identity by id (not name) — kills two-names-one-enemy identity forks via Origin type + alias ledger
3. **162-3:** Bestiary generics section replaces ephemeral stub minting
4. **162-4:** Origin-precedence ADR (Green Room) — typed-provenance feeders; precedence: authored > room-bound > region-population > MM pool > narrator mint
5. **162-5:** flickering_reach content reconciliation (18 phantom creature refs remapped)
6. **162-6:** space_opera bestiary de-triplication (12-entry world bestiaries collapse)

**Load-bearing references:**
- `docs/superpowers/specs/2026-07-05-npc-generation-inventory.md` — The seven spawn paths that 162-7 must exercise
- `docs/adr/004-lazy-genre-binding.md` and `docs/adr/121-layered-content-resolution.md` — Origin/provenance semantics
- `sprint/epic-162.yaml` — Story definitions and completion status

### 162-7 Scope: Two Deliverables

**Deliverable 1 (server, sidequest-server):**
- Integration/wiring test that spawns a creature from **EVERY spawn source/path** (all seven from 2026-07-05 spec)
- Assert **ONE identity per creature:** one creature_id, aliases collapse (no identity forks)
- Verify that narrated prose names are recorded as aliases, not new identities
- Fail loudly if any source mints a duplicate creature_id
- This is "every test suite needs a wiring test" doctrine applied to the seven-spawn-path consolidation

**Deliverable 2 (understudy, sidequest-understudy):**
- A playtest scenario that detects "two-names-one-enemy" (the same enemy narrated under two different names)
- Emit it as a CONFIRMED/BEHAVIORAL finding — the naive-player-visible symptom of an identity fork
- Naive player perceives narration as text-on-screen; if the same creature name-changes mid-scene, that's a finding

### Acceptance Criteria

**Server (sidequest-server):**
- [ ] Test enumerates the seven spawn sources per the 2026-07-05 NPC-generation inventory
- [ ] For each source, spawn a creature and verify it resolves to a single creature_id
- [ ] Assert that any prose names are recorded as aliases (not new identities)
- [ ] Test fails loudly if any source produces a duplicate creature_id or identity fork
- [ ] Test is reachable from production code paths (not mocked, not a shell)

**Understudy (sidequest-understudy):**
- [ ] Create/add a playtest scenario that exercises identity forks (or a scenario where a creature name-changes)
- [ ] Detection logic flags "two-names-one-enemy" as a finding with type CONFIRMED or BEHAVIORAL
- [ ] Finding is emitted in the understudy report (finding.json or findings list)
- [ ] Bot perceives the scenario as a naive player would (screen-reader visibility, no backend access)

**Both Repos:**
- [ ] Both repos green (all tests pass, lint clean)
- [ ] Wiring verified (test runs from production paths, not isolated mocks)

## Sm Assessment

**Setup decision:** Accepted 162-7 as-scoped from epic-162 with no split. It is a 2pt TDD verification capstone — the natural close-out for epic-162's NPC origin consolidation. No decomposition needed; the two deliverables (server integration test, understudy scenario) are cohesive around a single invariant: **one identity per creature across all spawn sources.**

**Why now:** 162-1 through 162-6 are all done and merged to develop. The mechanism exists (id-keyed identity, alias ledger, Green Room precedence); what's missing is the all-sources wiring proof and the naive-player-visible detector. This is exactly the "Every Test Suite Needs a Wiring Test" doctrine (CLAUDE.md) — the epic built machinery across seven spawn paths; 162-7 proves it's wired end-to-end and that a player would catch a regression.

**Base-branch hygiene:** Both subrepos were sitting on stale leftover branches (server on `feat/162-6-...`, understudy on `feat/161-2-...`), working trees clean. Switched both to `develop`, fast-forwarded to origin, then branched `feat/162-7-all-sources-one-scene-identity-test` cleanly off develop in each. No inherited stale commits.

**Merge gate:** Clear at setup. Only open PR across target repos is understudy #19 (DRAFT) — drafts are allowed; no non-draft PRs for out-of-review stories.

**Jira:** Explicitly `none` — epic-162 runs no-jira (all sibling stories are `[no jira]`). Claim step correctly skipped, not overlooked.

**Guidance for TEA (RED phase):**
- The seven spawn paths are the load-bearing input — enumerate them from `docs/superpowers/specs/2026-07-05-npc-generation-inventory.md`, not from memory. The server test must exercise *real* spawn sources (wiring test), not a mocked harness.
- The identity invariant to assert: each spawned creature resolves to exactly one `creature_id`; prose/narrator names land in the alias ledger, never as new identities. A duplicate creature_id from any source is a loud failure (No Silent Fallbacks).
- Understudy side: the finding is the *naive-player-visible* symptom — the same enemy narrated under two names in what the player sees. Keep the naivety invariant: detection reads screen-visible narration, not backend identity state.
- The ADR references the setup subagent listed (004/121) are a starting guess for Origin/provenance semantics — verify against the actual 162-2/162-4 implementation (Origin type, alias ledger, Green Room materializer) rather than trusting the doc pointers.

**Model note:** SM phase ran on opus (models.yaml expects sonnet). Intentional for this session; no impact on setup correctness.

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Reason:** n/a — 162-7 is a two-deliverable verification story; both need tests.

**Test Files:**
- `sidequest-server/tests/server/test_162_7_all_sources_one_scene_identity.py` — the all-sources-one-scene identity **regression guard**. Drives the *real* production seams (MM `inject` #1, `_seed_combat_hp_depletion_to_npcs` #4, `preload_authored_npcs` #5, `accrete_npc_aliases`) + the pure `identity_key` convergence invariant. 8 tests.
- `sidequest-understudy/tests/test_two_names_one_enemy.py` — the `two_names_one_enemy` detector unit tests (screen-only, naivety-safe, false-positive guards) + grading through `reconcile`. 6 tests.
- `sidequest-understudy/tests/wiring/test_identity_fork_finding.py` + `tests/wiring/fixture_identity_fork.html` — end-to-end wiring: real `run_table` over a fixture whose screen-visible narration names one enemy two ways → assert the finding surfaces in `findings.json`. 1 test.

**Tests Written:** 15 total (8 server + 7 understudy) covering both repos' ACs.

**Status:**
- **Understudy = RED (failing, ready for Dev).** `two_names_one_enemy` (import error) and `SignalKind.TWO_NAMES_ONE_ENEMY` (missing member → wiring test emits no signal) are net-new. Verified clean RED: unit file errors on the import; the wiring test runs all 4 turns end-to-end (chromium provisioned) and fails on empty `findings.json` signals — a behavioral RED that proves the whole harness works and only the detector+wiring is missing.
- **Server = GREEN-on-write regression guard (8/8 pass).** It verifies the *already-shipped* 162-2/-3 identity machinery is wired into the real spawn seams and does not fork. **This is expected and correct, not a vacuous RED** — ADR-156's "Relationship to the epic" §names 162-7's server side as "the permanent regression guard." There is no server implementation to do; the RED→GREEN work is entirely the understudy detector.

### Rule Coverage

Applicable lang-review rule for TEA is `python.md` **#6 (test quality)** — the others are production-code rules the GREEN detector must satisfy (Dev).

| Rule | Test(s) / how enforced | Status |
|------|------------------------|--------|
| #6 test-quality (no vacuous asserts) | every truthy assert (`hit is not None`, `resolved`) is followed by a value/attribute check; negative + empty cases present; monkeypatch targets where-used | self-check pass |
| #6 test-quality (no skips) | zero `@pytest.mark.skip`/`xfail` (repo rule: "never xfail in-flight features"); the 162-10 gap is a Delivery Finding, not a quarantine | pass |
| #2 mutable-defaults (GREEN) | detector is a pure fn — Dev must avoid mutable default args | Dev guidance |
| #3 type-annotations (GREEN) | `two_names_one_enemy(snapshot: str) -> str \| None` signature pinned by the unit test | Dev guidance |
| #9 async-pitfalls (GREEN) | the per-turn detector call must not block `SeatRunner.run`'s async loop (pure string scan is fine) | Dev guidance |

**Rules checked:** 1 of 1 TEA-applicable lang-review rule (#6) has coverage; 3 production-code rules flagged as GREEN guidance.
**Self-check:** 0 vacuous tests found.

### GREEN work for Dev (Naomi) — understudy only

1. `SignalKind.TWO_NAMES_ONE_ENEMY = "two_names_one_enemy"` in `src/understudy/types.py` (reconcile auto-treats it as a HARD signal — only `MODEL_ERROR` is down-weighted).
2. `two_names_one_enemy(snapshot: str) -> str | None` in `src/understudy/findings/detect.py` — pure, mirrors `repeated_action`'s zero-LLM style. Reads ONLY the aria snapshot: one enemy in the panel + a differently-named foe in the narration → return the conflicting narrated name; consistent / no-combat-panel → `None`. **NAIVETY INVARIANT: never consult a creature_id, alias map, or OTEL span.**
3. Wire it into `SeatRunner.run()`'s per-turn signal collection (`seat.py`, alongside `repeated_action`): on non-None, append `FrictionSignal(kind=SignalKind.TWO_NAMES_ONE_ENEMY, seat, turn, detail=<the conflict>)`.
4. **Watch the aria shape (see Delivery Finding):** align the detector to the REAL Playwright `aria_snapshot()` of `fixture_identity_fork.html`, not only the hand-written unit fixtures.
- Server: no implementation. Keep the guard green through GREEN/verify.

**Handoff:** To Dev (Naomi Nagata) for the understudy detector implementation.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-understudy):**
- `src/understudy/types.py` — added `SignalKind.TWO_NAMES_ONE_ENEMY` (a hard signal; `reconcile` grades it with no change — only `MODEL_ERROR` is down-weighted).
- `src/understudy/findings/detect.py` — added `two_names_one_enemy(snapshot: str) -> str | None`, a pure screen-only detector (mirrors `repeated_action`'s zero-LLM style): exactly one foe in the aria enemy panel + the panel label absent from the narration + a differently-named foe in the `log:` prose → the conflicting narrated name. Reads only the perceived aria snapshot (naivety invariant — no creature_id/alias map/OTEL span).
- `src/understudy/orchestrate/seat.py` — wired the detector into `SeatRunner.run()`'s per-turn signal collection (right after `count_actionable`, same shape as the `repeated_action` append).

**Files Changed (sidequest-server):** none — the server test is a passing regression guard verifying the already-shipped 162-2/-3 identity machinery. No server implementation was required (as TEA scoped).

**Tests:** 282/282 passing (GREEN).
- New understudy: 7 (detector unit + false-positive guards + grading + end-to-end wiring).
- Full understudy suite: 267 (no regression from the shared-module edits).
- Server regression guard: 8/8.

**Aria-shape verification (TEA Finding #3 — resolved):** dumped the REAL Playwright `aria_snapshot()` of `fixture_identity_fork.html`; it matches the hand-written unit fixtures byte-for-byte (`region "Enemies"` → `listitem: Thief`, `log: <narration>`). The one detector parses both — risk closed, not deferred.

**Branches (pushed to origin):**
- `sidequest-understudy` `feat/162-7-all-sources-one-scene-identity-test`
- `sidequest-server` `feat/162-7-all-sources-one-scene-identity-test` (carries TEA's regression-guard commit)

**Handoff:** To Reviewer (Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 267 understudy + 8 server green, lint/format clean, no smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (silent-inert concern covered by [RULE] HIGH) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 7, dismissed 1 |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — every docstring claim cross-checked against ADR-156/epic-162/signatures, all accurate |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (ReDoS/injection covered by [RULE]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 HIGH + 2 advisory (0 of 13 rule violations) | confirmed 1 (the HIGH; verified independently) |

**All received:** Yes (4 ran, 5 disabled via settings)
**Total findings:** 1 HIGH (confirmed → dispositioned to follow-up story 162-11 per Keith), 6 Medium/Low (confirmed, non-blocking), 1 dismissed (with rationale)

## Rule Compliance

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) — rule-checker enumerated all 13 exhaustively (34 instances, 0 violations); I independently confirmed the load-bearing ones against the new code:

| Rule | Verdict | Evidence |
|------|---------|----------|
| #1 silent exceptions | ✓ | no new try/except; `otel_capture` fixture is try/finally (cleanup), not a swallow |
| #2 mutable defaults | ✓ | `two_names_one_enemy(snapshot: str)`, `_enemy_labels(lines)` — no defaults; test helpers use immutable defaults (`()`, `None`, str) |
| #3 type annotations | ✓ | `two_names_one_enemy(snapshot: str) -> str \| None`, `_enemy_labels(lines: list[str]) -> list[str]` fully annotated |
| #6 test quality | ✓ (1 note) | tests genuinely discriminate (constant-None fails the positive, constant-non-None fails the negatives); one looseness — the wiring test's `grade in {"behavioral","confirmed"}` where only "behavioral" is reachable ([TEST], non-blocking) |
| #9 async pitfalls | ✓ | detector is a pure synchronous regex scan in `SeatRunner.run` (`seat.py`) — no blocking I/O added to the async loop |
| #11 ReDoS / input validation | ✓ | `_PROPER_NOUN` empirically benchmarked linear (~2-8ms on 1MB adversarial input); `re.escape(label)` before interpolation — no injection |
| #10 import hygiene | ✓ | `import re` explicit; `from ...detect import repeated_action, two_names_one_enemy` — no cycle, no star import |
| Naivety invariant (understudy CLAUDE.md) | ✓ | `two_names_one_enemy` / `_enemy_labels` take only the aria `snapshot` string — no creature_id, alias map, or OTEL span referenced. (Reads only screen-visible text — as far as its own inputs go. See the HIGH finding: the shape it reads is absent from the real UI.) |
| SignalKind flow (reconcile) | ✓ | `TWO_NAMES_ONE_ENEMY` not in `_DOWNWEIGHTED` → hard signal → BEHAVIORAL alone / CONFIRMED with complaint (pinned by tests) |

Rules #4 (logging), #5 (path), #7 (resources), #8 (deserialization), #12 (deps), #13 (fix-regression) are not-applicable or clean for this diff (no logging modules, pathlib used, `otel_capture` cleans up, no pickle/eval, no dep changes).

## Reviewer Assessment

**Verdict:** APPROVED (with a blocking follow-up story 162-11, per Keith's disposition of the HIGH finding)

**Data flow traced:** a player-perceived aria snapshot → `perceive(page)` (str) → `SeatRunner.run` per turn → `two_names_one_enemy(snapshot)` (pure regex scan of the enemy panel + `log:` narration) → on a conflict, `FrictionSignal(TWO_NAMES_ONE_ENEMY)` → `reconcile()` → `findings.json`. Screen-only; no backend identity crosses into the detector (naivety invariant holds by construction). **The break in this flow is at the first hop:** the real `perceive()` output for a live confrontation does not contain the `region "Enemies"`/`listitem`/`log:` tokens the detector keys on (see [RULE] below) — so in production the flow terminates at `_enemy_labels() == []` and never emits.

**Observations (8):**
- `[RULE][HIGH]` The detector parses an aria shape absent from the real sidequest-ui — `two_names_one_enemy` returns None on every real session (inert in production) at `sidequest-understudy/src/understudy/findings/detect.py:23-30`. Verified 3 ways: rule-checker + test-analyzer greps + my own — `role="log"` = 0 hits, `aria-label="Enemies"` = 0 hits in `sidequest-ui/src`; the real opponent surface is `ConfrontationOverlay.tsx` `aria-label="Opponent HP"/"Opponent edge"` (dial/HP-bar), not a named `listitem` roster. Root cause is partly a pre-existing tool-wide `log:`-narration convention (`fixture_table.html`, `test_perception.py`). **Dispositioned to blocking follow-up story 162-11** (Keith's call: land the isolation-tested capstone, fix real-UI fidelity tool-wide separately).
- `[TEST][MEDIUM]` Wiring test grade assertion `in {"behavioral","confirmed"}` is looser than reachable (FakeActionModel emits no complaint → only "behavioral" is possible) at `tests/wiring/test_identity_fork_finding.py:83`. Non-blocking; fold the tighten into 162-11.
- `[TEST][MEDIUM]` Missing detector tests for multi-foe panels, label+name co-occurrence, and multi-`log:`-line renames (all deliberate single-snapshot behaviors, unpinned) at `tests/test_two_names_one_enemy.py`. Non-blocking; add in 162-11.
- `[TEST][LOW]` `test_authored_and_bestiary_of_same_being_do_not_double_seat` (`test_162_7_all_sources_one_scene_identity.py:367`) only recomputes `identity_key` for two hand-built Origins — its name over-promises "do not double seat." Non-blocking; rename or extend.
- `[DOC][VERIFIED]` Every docstring factual claim (ADR-156 "not built", four unconverted seams vs epic-162.yaml, `NpcPoolMember` has no creature_id, all function signatures, spawn-path numbering) cross-checked accurate — comment-analyzer, evidence: it read the actual ADR/spec/source.
- `[SEC][VERIFIED]` No injection / ReDoS — `re.escape(label)` at `detect.py:81`; `_PROPER_NOUN` benchmarked linear. Evidence: rule-checker empirical benchmark + mutually-exclusive alternation branches.
- `[SIMPLE][VERIFIED]` Implementation is minimal — `two_names_one_enemy`+`_enemy_labels` ~50 lines mirroring `repeated_action`'s zero-LLM style; one duplicative pair of grading tests noted (`[TEST][LOW]`), no over-engineering. Evidence: `detect.py` diff.
- `[TYPE][VERIFIED]` `SignalKind.TWO_NAMES_ONE_ENEMY` is a proper StrEnum member; detector returns a typed `str | None`; no stringly-typed API regressions beyond the inherent aria-string parsing. Evidence: `types.py`, `detect.py:55`.
- `[EDGE]/[SILENT]` (subagents disabled) — I checked boundaries myself: empty/None snapshot → None (guarded `detect.py:70`); multi-foe → None (`len(labels)!=1`); the silent-inert-on-unparseable behavior IS the `[RULE][HIGH]` finding.

**Pattern observed:** the detector faithfully mirrors the existing `repeated_action` zero-LLM predicate pattern and wires in identically to the per-turn signal block (`seat.py`) — good pattern adherence. The flaw is not the pattern; it is that the *input contract* (the aria shape) was validated against a synthetic fixture instead of the real UI.

**Error handling:** null/empty snapshot → None (safe); unknown/garbled aria → None (safe, but silently — the No-Silent-Fallbacks tension, now tracked in 162-11). No exceptions raised on any input path.

**Security analysis:** the detector is a test-harness dev tool (not player-facing); inputs are the game's own aria snapshot; `re.escape` prevents label-injection into the search regex; ReDoS ruled out empirically. No auth/tenant surface.

### Devil's Advocate

Argue this is broken. The most damning case is the one three independent checks converged on: **this is a beautifully-built parser for a screen that does not exist.** A future dev — or Keith — reads "162-7: identity-split hunt, DONE, 282 tests green" and *trusts* that a real playtest will surface two-names-one-enemy forks. It never will. The detector's `_ENEMY_REGION`/`_LISTITEM`/`_LOG` regexes key on `region "Enemies"`, `listitem:`, and `log:`, none of which `sidequest-ui` emits; a live confrontation renders as `aria-label="Opponent HP"` dials and role-less narration `div`s that `aria_snapshot()` collapses to a flat text blob. So `_enemy_labels()` returns `[]` forever and the detector short-circuits to None. This is precisely the failure mode the project's whole OTEL/lie-detector doctrine exists to prevent — convincing green with zero real backing — except here the inert thing is the *finder* meant to catch it. Second, even granting a matching UI: the "label appears anywhere in the joined narration → clean" guard means a genuine mid-scene rename (an early `log:` line names "Thief", a later line renames it "Molgrath") is *suppressed* because the earlier mention satisfies the guard — the detector would miss the exact multi-turn fork it is named for. Third, the wiring test accepts a "confirmed" grade that its own fixture can never produce, so a reconciler regression that spuriously promotes uncomplained signals would sail through. Fourth, a narrator writing a capitalized common noun in a single-foe fight ("A Guard blocks the door") that doesn't match the panel label would *false-positive* — flagging a non-fork. Fifth, any two-enemy scene is silently exempt (`len(labels)!=1`), so a mislabeled foe among two is never caught. **Which of these survived?** All were captured: #1 and #2 as the HIGH finding + Dev's logged single-snapshot deviation → story 162-11; #3–#5 as non-blocking `[TEST]` findings for the 162-11 test pass. The core detection *logic* is correct in isolation (the unit tests genuinely discriminate) and the epic-162 server regression capstone is real (drives production seams, asserts the `identity.resolved` span) — which is why this is an APPROVE-with-follow-up, not a REJECT. But make no mistake: without 162-11, the understudy half of this story is a green light wired to a bulb that is not plugged in.

**Handoff:** To SM for finish-story (162-7 approved; 162-11 filed as the blocking real-UI fidelity follow-up).

## Delivery Findings

_Setup: No upstream findings (deliverables defined by epic-162 completion)._

### TEA (test design)
- **Gap** (non-blocking): four NPC-identity seams remain name-string-keyed (unconverted to the unified resolver) — the narrator mention path (`_apply_npc_mentions`, matches casefold/comma-inversion/`invented_from` but never the alias ledger, so a prose-alias mention mints a duplicate pool member), the Fate seeder (`_seed_fate_opponents`, raw `by_name`), edge-publish (`_publish_combat_edge_to_npcs`, raw `by_name`), and the pool-member exact-match legs. Affects `sidequest/server/dispatch/encounter_lifecycle.py` and `sidequest/server/narration_apply.py` (adopt `resolve_roster_npc` / a pool sibling). This is **story 162-10's** scope — 162-7 documents it here rather than asserting no-fork (out of scope for a 2pt guard). *Found by TEA during test design.*
- **Improvement** (non-blocking): `sprint/context/context-story-162-7.md` line 9 renders the `Repos:` field character-split (`s, e, r, v, e, r, ,, u, n, d, e, r, s, t, u, d, y`) — a cosmetic sm-setup artifact (the actual repos `server,understudy` are correct everywhere else). Affects the context file only; harmless. *Found by TEA during test design.*
- **Question** (non-blocking): the understudy detector's unit fixtures use a hand-written aria-snapshot shape (`- region "Enemies": - list: - listitem: Thief` + `- log: <foe>`). Dev must confirm the REAL Playwright `aria_snapshot()` of `tests/wiring/fixture_identity_fork.html` produces a compatible shape so the one detector passes BOTH the unit fixtures and the end-to-end wiring test; if they diverge, align the fixture/detector during GREEN. Affects `sidequest-understudy/src/understudy/findings/detect.py` + `tests/wiring/fixture_identity_fork.html`. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved (TEA Question above):** dumped the REAL Playwright `aria_snapshot()` of `fixture_identity_fork.html` — it matches the unit fixtures byte-for-byte. No divergence; the detector parses both. No change needed. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the detector is single-snapshot (panel-label vs co-present narration — the 108-2 symptom). A pure cross-turn rename where the enemy PANEL LABEL itself changes across turns with no co-present conflict is not caught. A future enhancement could track a foe's panel label across turns and flag a mid-scene relabel. Affects `sidequest-understudy/src/understudy/findings/detect.py` (add cross-turn state, likely a post-run row scan). Not needed for this story's ACs. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking for 162-7 — filed as blocking follow-up story **162-11**): the identity-fork detector parses aria tokens (`region "Enemies"`, `listitem:`, `log:`) that the real sidequest-ui never emits, so `two_names_one_enemy` returns None on every live session — inert in production (verified 3 ways: rule-checker, test-analyzer, and Reviewer grep — `role="log"`/`aria-label="Enemies"` = 0 hits; real surface is `ConfrontationOverlay.tsx` `aria-label="Opponent HP"/"Opponent edge"`). Root cause is partly a pre-existing tool-wide `log:`-narration convention. Affects `sidequest-understudy/src/understudy/findings/detect.py` + the wiring fixtures + likely `sidequest-ui` opponent/narration aria roles. Keith dispositioned APPROVE + follow-up (162-11). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): tighten/extend the understudy test suite in 162-11 — the wiring test's grade assertion should be `== "behavioral"` (only reachable value); add detector tests for multi-foe panels, label+name co-occurrence, and multi-`log:`-line renames (deliberate single-snapshot behaviors currently unpinned). Affects `sidequest-understudy/tests/test_two_names_one_enemy.py` + `tests/wiring/test_identity_fork_finding.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the server test `test_authored_and_bestiary_of_same_being_do_not_double_seat` only recomputes `identity_key` for two hand-built Origins — its name over-promises "do not double seat." Rename to reflect what it checks (distinct id namespaces) or extend it to seat both into one `snap.npcs` and assert no collision. Affects `sidequest-server/tests/server/test_162_7_all_sources_one_scene_identity.py`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **"Every source" scoped to the materialized-layer / drivable sources; unconverted seams documented, not asserted**
  - Spec source: context-story-162-7.md, AC "Server — Integration/wiring test enumerates all seven spawn sources … For each source, spawns a creature and asserts ONE creature_id"
  - Spec text: "Integration/wiring test enumerates all seven spawn sources (2026-07-05 spec); For each source, spawns a creature and asserts ONE creature_id (no identity forks)"
  - Implementation: the test drives the three Npc-materializing sources that carry ids (MM inject #1, opponent-seater #4, authored preload #5) plus the pure `identity_key` convergence invariant every feeder's product must satisfy. The three pool-staging sources (#2 mentions, #3 prose, #6 zone-cast) emit `NpcPoolMember`s with no `creature_id` by design (ADR-118 identity-only staging), so "asserts ONE creature_id" is not literally applicable at the pool tier; #7 procedural population feeds via #1's region builder. The four unconverted name-keyed seams are documented as a Delivery Finding → 162-10, not asserted.
  - Rationale: "one identity per creature" is a materialized-layer invariant; the Green Room single-gate that would converge all seven (ADR-156) is `status: proposed` / unbuilt; forcing no-fork on the unconverted seams is 162-10's scope. Repo rule forbids xfail for in-flight features, so the boundary is a finding + the primitive `test_idless_mints_fork_by_name` documents the fork principle safely.
  - Severity: minor
  - Forward impact: when 162-10 converts the remaining seams, extend this guard to assert no-fork there and update the primitive test's "why" note.
- **Server suite is a green-on-write regression guard; the RED is concentrated in the understudy detector**
  - Spec source: TDD workflow (RED phase)
  - Spec text: "Phase A — AC tests: Write failing tests covering each AC."
  - Implementation: the server ACs verify already-shipped 162-2/-3 behavior, so the server suite passes on write (8/8). The failing (RED) tests are the understudy detector suite (net-new `two_names_one_enemy` + `SignalKind.TWO_NAMES_ONE_ENEMY`).
  - Rationale: 162-7 is a verification capstone — ADR-156 names its server side "the permanent regression guard." A green regression guard is the correct artifact; manufacturing server RED would require doing 162-10's seam conversion (out of scope).
  - Severity: minor
  - Forward impact: none — Dev's implementation work is the understudy detector + wiring; the server suite is the safety net.

### Dev (implementation)
- **Detector scoped to single-snapshot (co-present) detection, not cross-turn name tracking**
  - Spec source: context-story-162-7.md, Understudy AC / story title
  - Spec text: "detects two-names-one-enemy (same enemy under two names)"; session scope: "if the same creature name-changes mid-scene, that's a finding"
  - Implementation: `two_names_one_enemy(snapshot)` flags when the enemy panel and the narration name the sole foe differently WITHIN one perceived snapshot (the 108-2 co-present symptom the TEA fixture exercises). It does not carry per-seat state to catch a pure panel-label rename across turns with no co-present conflict.
  - Rationale: the co-present panel-vs-narration case is the 108-2 symptom and exactly what the TEA fixtures + ACs pin; cross-turn state tracking is unneeded to pass the suite and adds per-seat state (Dev minimalism — no abstraction a test doesn't require).
  - Severity: minor
  - Forward impact: none for this story; a cross-turn variant is filed as a non-blocking Delivery Finding for a future enhancement.

### Reviewer (audit)
- **TEA deviation 1 ("every source" scoped to materialized-layer / drivable sources)** → ✓ ACCEPTED by Reviewer: correct. "One identity per creature" IS a materialized-layer (`snapshot.npcs`) invariant; pool-staging sources carry no creature_id by design (ADR-118, verified — `NpcPoolMember` has no such field). Deferring the four unconverted seams to 162-10 is the right scope for a 2pt guard, and the repo's "never xfail in-flight features" rule makes the Delivery-Finding treatment correct over a quarantine.
- **TEA deviation 2 (server suite is a green-on-write regression guard; RED concentrated in understudy)** → ✓ ACCEPTED by Reviewer: correct for a verification capstone. The server tests are NOT green-on-write theater — they drive real gated production branches (`_seed_combat_hp_depletion_to_npcs`'s `created = npc is None` gated on `resolve_roster_npc`) and assert real OTEL attribute values (`identity.resolved`, `via == "alias"`), not mere span presence.
- **Dev deviation (detector scoped to single-snapshot, co-present detection)** → ✓ ACCEPTED by Reviewer, with a note: the single-snapshot scope is a sound minimalist choice for the co-present 108-2 symptom, and the cross-turn variant is correctly filed as a follow-up. However, review surfaced a larger, related issue that supersedes it in priority — the detector's aria contract does not match the real UI at all (Reviewer `[RULE][HIGH]` finding → story 162-11). Both the single-snapshot limitation and the real-UI fidelity gap should be resolved together in 162-11.