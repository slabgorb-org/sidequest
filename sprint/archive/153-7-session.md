---
story_id: "153-7"
jira_key: "(no Jira integration)"
epic: "153"
workflow: "tdd"
---
# Story 153-7: [FATE-DEFEND-RESUME-WEDGE] re-emit pending defends on reconnect + clear orphaned pending_defenses (ADR-151)

## Story Details
- **ID:** 153-7
- **Jira Key:** (no Jira integration)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Priority:** p3
- **Repos:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T19:45:11Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T18:55:07Z | 2026-06-21T18:57:49Z | 2m 42s |
| red | 2026-06-21T18:57:49Z | 2026-06-21T19:16:18Z | 18m 29s |
| green | 2026-06-21T19:16:18Z | 2026-06-21T19:34:54Z | 18m 36s |
| review | 2026-06-21T19:34:54Z | 2026-06-21T19:45:11Z | 10m 17s |
| finish | 2026-06-21T19:45:11Z | - | - |

## Sm Assessment

### Problem Summary

ADR-151 introduced the Fate DEFEND follow-up barrier. When a Fate conflict round resolves with seated PCs targeted by attacks, the round parks at a conditional second sealed-commit barrier. The server writes a `pending_defenses` ledger (`FatePendingDefense` entries), emits `FATE_DEFEND_REQUEST` per incoming attack, and waits for defenders to fill each entry.

Two failure modes block this story:

**A) No re-emit on reconnect.** `FATE_DEFEND_REQUEST` emits exactly once at park time. A targeted player who disconnects mid-DEFEND never sees the request again on reconnect — their pending defend is invisible, they can't throw, and the round wedges forever.

**B) Orphaned pending_defenses.** An entry whose defender can never fill it (left table, seat vacated) blocks resume indefinitely. There must be a loud, bounded way to clear orphaned entries so the exchange resumes.

### Key Files (Server Only)

- `sidequest-server/sidequest/server/dispatch/fate_conflict.py` — REVEAL/park/resume, dispatch_fate_defense, resume_fate_exchange
- `sidequest-server/sidequest/handlers/fate_throw.py` — FATE_DEFEND_REQUEST broadcast, defend routing
- `sidequest-server/sidequest/game/encounter.py` — FatePendingDefense model + StructuredEncounter.pending_defenses ledger
- `sidequest-server/sidequest/server/websocket_session_handler.py` — reconnect path + existing pending_defenses references (natural hook point)
- Reconnect/resume paths: session_state.py, session.py, session_room.py

### Technical Approach (TEA Red-Phase + Dev)

- On player reconnect to a session with unfilled `snapshot.encounter.pending_defenses` for the reconnecting player, RE-EMIT the matching `FATE_DEFEND_REQUEST` (same request_id, locked attack_total, attacker, skill).
- Locked NPC dice from REVEAL must NOT be re-rolled (ADR-128 resume-safety).
- Provide a loud, bounded clearing path for orphaned pending_defenses (defender gone / unfillable). Fail loudly / log, never silently drop. This is "loud-but-graceful" per No Silent Fallbacks: clearing must be observable (OTEL/log) and only applied to genuinely orphaned entries.
- Per OTEL principle: emit watcher events for both re-emit-on-reconnect and orphan-clear so GM panel verifies the wedge actually unblocks.
- Respect resume-safety: ledger rides `snapshot.encounter` and survives restart; legacy encounter with no ledger field deserializes to empty ledger (nothing parked ⇒ nothing to re-emit/clear).

### Acceptance Criteria (Draft — TEA Refines into Failing Tests)

1. Given a parked DEFEND barrier with unfilled `pending_defenses` entry for player P, when P reconnects, server re-emits matching `FATE_DEFEND_REQUEST` (correct request_id, attacker, attack_total, skill) to P; locked NPC REVEAL dice not re-rolled.
2. Reconnect with NO unfilled entry for the reconnecting player emits nothing (no spurious defend prompt).
3. Orphaned `pending_defenses` entry (defender no longer present) is cleared via bounded loud path, allowing `resume_fate_exchange` to proceed; clear is observable (OTEL/log) and NEVER applied to still-seated defender awaiting throw.
4. OTEL watcher events fire for both re-emit and orphan-clear decisions.
5. Wiring test proves re-emit is reachable from production reconnect code path (imported, called) — not just unit-tested in isolation.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (23 failing + 1 no-spurious-emit guard) — ready for Dev (Agent Smith).

**Test Files (server):**
- `tests/server/test_fate_defend_resume_emit.py` — 12 unit tests for the re-emit helper `_maybe_reemit_pending_defenses` (mirrors `test_fate_state_emit.py`, the sibling resume re-emitter). Fails: `ModuleNotFoundError: sidequest.server.websocket_handlers.fate_defend_resume`.
- `tests/server/dispatch/test_fate_defend_orphan_clear.py` — 9 unit tests for the orphan sweep `clear_orphaned_pending_defenses` in `fate_conflict.py`. Fails: `ImportError: cannot import name 'clear_orphaned_pending_defenses'`.
- `tests/server/test_fate_defend_resume_wiring.py` — 3 PG-backed integration tests driving the **real connect/resume handler** (mirrors `test_location_description_resume.py`). 2 fail behaviorally (resume bootstrap emits FATE_STATE/PARTY_STATUS but **no FATE_DEFEND_REQUEST** and never sweeps the orphan — the exact wedge); 1 is the no-spurious-emit guard (green before+after).

**Contract pinned for Dev (GREEN):**
1. **Re-emit** — new `sidequest/server/websocket_handlers/fate_defend_resume.py::_maybe_reemit_pending_defenses(*, sd, snapshot, defender_name, player_id, emit_fn)`. Fate-gated (`sd.genre_pack.rules.ruleset == "fate"` — never collide with the WN/native overlay), **read-only on the ledger** (no re-roll, ADR-128), re-emits one `FateDefendRequestMessage(player_id=…)` per *unfilled* `pending_defenses` entry whose `defender == defender_name`, carrying the **locked** request_id/attacker/attack_total/attack_skill/mental. Emits a `fate.defend_phase` span with `reason="reconnect_reemit", responded=False`. Wire it into `connect.py`'s `_State.Playing` bootstrap right beside `_maybe_emit_fate_state`, with `emit_fn=lambda msg, _label: bootstrap_msgs.append(msg)` and `defender_name=resume_char_name`.
2. **Orphan sweep** — new `fate_conflict.py::clear_orphaned_pending_defenses(*, encounter, snapshot, _tracer=None) -> list[FatePendingDefense]`. **Concedes** (never deletes — the NPC's sealed attack still resolves; No Silent Fallbacks) each *unfilled* entry whose `defender` is no longer a live seated PC (`withdrawn` or absent from `snapshot.characters`), emits a `fate.defend_phase` span with `reason="orphaned", conceded=True`, returns the cleared entries. **Safety invariant (most load-bearing test):** must NEVER touch a present-but-silent defender — a disconnected-yet-seated player is the *re-emit* case, not an orphan. Wire it into the same resume bootstrap so a reconnect unwedges a round stuck on a departed defender.

### Rule Coverage

| Rule (CLAUDE.md / SOUL) | Test(s) | Status |
|------|---------|--------|
| OTEL on every subsystem decision (lie detector) | `test_reemit_emits_reconnect_defend_phase_span`, `test_sweep_emits_orphaned_defend_phase_span` | failing |
| No Silent Fallbacks (loud, observable orphan clear; concede not drop) | `test_withdrawn_defender_entry_is_conceded`, `test_sweep_with_no_orphans_emits_no_span` | failing |
| Bind, don't balance — never collide with WN/native overlay (Fate gate) | `test_gated_off_for_without_number_pack`, `test_gated_off_for_dial_pack` | failing |
| Resume-safety / no re-roll (ADR-128) | `test_reemit_does_not_mutate_the_ledger`, `test_swept_orphan_resumes_and_folds_without_rerolling` | failing |
| Agency — never strip a present defender's defense | `test_present_unfilled_defender_is_not_cleared`, `test_only_orphaned_entry_cleared_present_one_untouched` | failing |
| Wiring test (production reachability, not source-grep) | `test_slug_resume_reemits_fate_defend_request_for_parked_defender`, `test_slug_resume_sweeps_orphaned_pending_defense_but_spares_present_one` | failing |

**Rules checked:** OTEL, No-Silent-Fallbacks, Bind-don't-balance, ADR-128 resume-safety, Agency, wiring — all have coverage.
**Self-check:** No vacuous assertions. Every test asserts concrete payload fields, conceded/defense_total state, span attributes, or return values. The one green-in-RED test is a genuine no-spurious-emit guard (fails-on-regression), not vacuous.

**Handoff:** To Dev (Agent Smith) for GREEN. Run server tests with PG up (`SIDEQUEST_TEST_DATABASE_URL=postgresql://slabgorb@localhost:5432/sidequest_test`).

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 24/24 passing (GREEN) — 12 re-emit unit + 9 orphan-clear dispatch + 3 PG wiring.
**Branch:** `feat/153-7-fate-defend-resume-wedge` (pushed)

**Files Changed:**
- `sidequest/server/websocket_handlers/fate_defend_resume.py` (new) — `_maybe_reemit_pending_defenses`: fate-gated, read-only on the ledger, re-emits one `FateDefendRequestMessage(player_id=…)` per unfilled `pending_defenses` entry for the reconnecting defender; fires `fate.defend_phase` span `reason=reconnect_reemit`. Sibling of `fate_state_emit._maybe_emit_fate_state`.
- `sidequest/server/dispatch/fate_conflict.py` — added `clear_orphaned_pending_defenses(*, encounter, snapshot, _tracer=None) -> list[FatePendingDefense]`: concedes (never deletes — the NPC's sealed attack still resolves) each unfilled entry whose defender is no longer a live seated PC (`withdrawn` or absent from `snapshot.characters`); never touches a present defender's open entry; fires `fate.defend_phase` span `reason=orphaned`.
- `sidequest/handlers/connect.py` — wired both into the `_State.Playing` resume bootstrap beside `_maybe_emit_fate_state` (sweep orphans first, then re-emit for the reconnecting defender), gated on a non-empty `pending_defenses` ledger.

**Regression:** Directly-impacted suites all green serially (43/43: fate dispatch, defend-barrier wiring, concede wire, fate_state_emit, slug-connect, location-description resume). Pyright on the two edited files held at baseline (62 → 62; my new module 0 errors). The 13 failures in the broad xdist sweep are pre-existing and unrelated (`test_pregen_fail_loud_90_5` fails 3/3 even with my changes stashed — Monster Manual pregen, a different subsystem).

**Self-review:**
- [x] Wired into production resume path (connect bootstrap), proven by the 3 PG wiring tests driving the real handler.
- [x] Follows project patterns (mirrors `_maybe_emit_fate_state` / the existing resume re-emits).
- [x] All ACs met (re-emit, orphan-clear, OTEL on both, no spurious emit, wiring).
- [x] Error handling: fail-loud/observable (OTEL spans + logs); concede-not-drop honors No Silent Fallbacks.

**Handoff:** To Reviewer (The Merovingian).

## Delivery Findings

<!-- Append-only. Each agent under its own ### subheading. -->

### TEA (test design)
- **Question** (non-blocking): When the orphan sweep concedes the *last* blocking entry, the ledger becomes `ledger_full=True` — but who calls `resume_fate_exchange` + narrate? The unit/wiring tests pin the **sweep** (concede + OTEL) and deliberately do NOT force resume+narration through the connect bootstrap (to avoid coupling RED to the heavy narration pipeline). Dev/Architect must decide whether the resume bootstrap resumes immediately when the sweep fills the ledger, or the next player action does. Affects `sidequest/handlers/connect.py` + `sidequest/server/dispatch/fate_conflict.py` (resume trigger). *Found by TEA during test design.*

### Dev (implementation)
- **Question** (non-blocking): Implemented sweep-only on connect (no auto-resume when the sweep fills the ledger), confirming TEA's open question. For the common case the round still has a live defender whose throw will trigger `_finish_defense`→resume (the conceded orphan is already counted in `ledger_full`). The only un-handled tail is "the orphan was the *last/only* pending entry" — then the round sits ledger-full-but-parked until the next action. Wiring resume+narrate into the connect bootstrap is a larger design call (it pulls in the narration pipeline) and no test requires it; left for Reviewer/Architect. Affects `sidequest/handlers/connect.py` (whether the resume bootstrap should resume+narrate when a sweep completes the ledger). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The `display_name` identity fallback in `resume_char_name` (`connect.py:1720`, pre-existing) means an MP *legacy-backfill* save (empty `player_seats`) resolves the reconnecting defender from the client-supplied `payload.player_name`. A crafted name matching another PC could re-emit that PC's defend-request metadata to the wrong socket (info-only: attacker/skill/attack_total; the defense substitution is RESOLVE-blocked by `dispatch_fate_defense`'s `actor==defender` check). Root cause is pre-existing and shared by the location/chapter resume re-emits; belongs to the **ADR-119 authenticated-identity** track. Affects `sidequest/handlers/connect.py` (harden `resume_char_name` to an authoritative seat lookup). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Pre-existing (not in this diff) — the PARK-time `FATE_DEFEND_REQUEST` is `room.broadcast(exclude_socket_id=None)` with client-side filtering (`fate_throw.py:170`), so every socket sees every seat's defend request. This diff's re-emit correctly uses unicast; the PARK path should be brought to the same per-recipient delivery. Affects `sidequest/handlers/fate_throw.py` (unicast the PARK broadcast). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The "orphan was the *last/only* pending entry, no live defender to trigger resume" tail leaves the round ledger-full-but-parked (TEA + Dev both flagged this). Needs an Architect decision on whether the connect bootstrap (or a lightweight resume hook) should call `resume_fate_exchange` when a sweep completes the ledger. Affects `sidequest/handlers/connect.py` + `sidequest/server/dispatch/fate_conflict.py`. *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Orphan-clear wired to the connect/resume bootstrap, not a disconnect-triggered sweep**
  - Spec source: story title "clear orphaned pending_defenses (ADR-151)" + context-story-153-7.md
  - Spec text: "clear orphaned pending_defenses" (trigger unspecified)
  - Implementation: wiring test pins the sweep to the connect/resume path (same seam as re-emit), so a reconnecting peer unwedges a round stuck on a departed defender; not a disconnect-time sweep
  - Rationale: the story pairs both behaviors under "on reconnect," and the connect bootstrap already owns the FATE_STATE/LOCATION resume re-emits — a single seam is coherent and testable; a disconnect can be transient (the defender may return), so "orphaned" is correctly defined as withdrawn/absent-from-characters, not merely disconnected
  - Severity: minor
  - Forward impact: if Dev prefers a disconnect-time sweep, `test_slug_resume_sweeps_orphaned_pending_defense_but_spares_present_one` would need re-homing
- **"Locked NPC dice not re-rolled" (AC-1) covered via read-only-ledger + existing reload test, not a new dice-lock reconnect test**
  - Spec source: context-story-153-7.md, AC-1
  - Spec text: "locked NPC REVEAL dice not re-rolled"
  - Implementation: `test_reemit_does_not_mutate_the_ledger` asserts the re-emit never mutates the ledger (so it cannot re-roll), and the existing `test_fate_defend_barrier_wiring.py::test_parked_exchange_survives_reload_without_rerolling_npc` already pins dice-lock across a suspend; no duplicate dice-lock test added on the reconnect path
  - Rationale: re-emit is read-only by construction; duplicating the dice-lock assertion would test the existing suspend machinery, not the new code
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **Sweep-only on connect; no auto-resume when the sweep completes the ledger**
  - Spec source: context-story-153-7.md, AC-3 + TEA tests
  - Spec text: "Orphaned pending_defenses entry is cleared … allowing resume_fate_exchange to proceed"
  - Implementation: the connect bootstrap concedes orphans (so the ledger CAN resume) but does not itself call `resume_fate_exchange`+narrate; resume rides the next player action's `_finish_defense`, matching every test (none require resume-on-connect)
  - Rationale: minimalist discipline — implement what the tests pin; forcing resume+narration through the connect bootstrap pulls in the heavy narration pipeline and is the design call TEA explicitly deferred (see Delivery Findings)
  - Severity: minor
  - Forward impact: the "orphan was the last/only pending entry" tail stays parked-but-resumable until the next action — Reviewer/Architect to decide if connect should resume+narrate
- **Belt-and-suspenders `ruleset == "fate"` gate at the orphan-sweep call site**
  - Spec source: TEA contract (orphan sweep is not internally ruleset-gated)
  - Spec text: `clear_orphaned_pending_defenses(*, encounter, snapshot, _tracer=None)` (no sd/ruleset param)
  - Implementation: the sweep function stays ruleset-agnostic (unit-tested with no `sd`); the connect call site guards it with `genre_pack.rules.ruleset == "fate"` on top of the `pending_defenses`-non-empty guard
  - Rationale: `pending_defenses` is a Fate-only ledger, but the extra gate documents the block as Fate-only and prevents the Fate-specific concede from ever running on a non-Fate pack carrying a stale ledger
  - Severity: trivial
  - Forward impact: none

### Reviewer (audit)
- **TEA — Orphan-clear wired to connect/resume bootstrap (not disconnect-triggered)** → ✓ ACCEPTED by Reviewer: a single resume seam mirroring the FATE_STATE/LOCATION re-emits is coherent and testable; "orphaned" correctly = withdrawn/absent-from-characters, so a transient disconnect is never mis-swept.
- **TEA — "Locked NPC dice not re-rolled" covered via read-only-ledger + existing reload test** → ✓ ACCEPTED by Reviewer: the re-emit is read-only by construction (verified — builds payloads, never mutates entries); duplicating the suspend dice-lock test would test pre-existing machinery.
- **Dev — Sweep-only on connect; no auto-resume when the sweep completes the ledger** → ✓ ACCEPTED by Reviewer (with follow-up): faithful to the tests and strictly better than the wedge; the residual "all-orphans, no live defender" tail is captured as a non-blocking Reviewer delivery finding for an Architect decision.
- **Dev — Belt-and-suspenders `ruleset == "fate"` gate at the orphan-sweep call site** → ✓ ACCEPTED by Reviewer: harmless and documents the block as Fate-only; the minor gate asymmetry (sweep gated at call-site, re-emit gated internally) is a readability rough edge, not a defect — both correctly no-op off a Fate pack.
- No UNDOCUMENTED deviations found: the diff matches the TEA contract and the logged deviations.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN 24/24, ruff clean, 0 new pyright, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 (both medium, pre-existing-rooted) | confirmed 2 (both non-blocking, → delivery findings), dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — domain covered by Reviewer ([RULE]) |

**All received:** Yes (2 enabled returned: preflight + security; 7 disabled via `workflow.reviewer_subagents`, domains covered by Reviewer)
**Total findings:** 2 confirmed (both non-blocking, captured as delivery findings), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** A reconnect (`SESSION_EVENT{connect}`) → `ConnectHandler.handle` → the `_State.Playing` resume bootstrap. With a parked Fate barrier (`snapshot.encounter.pending_defenses` non-empty), the code (1) sweeps orphaned entries via `clear_orphaned_pending_defenses` (concede + OTEL) and (2) re-emits the reconnecting defender's own unfilled `FATE_DEFEND_REQUEST`(s) into `bootstrap_msgs` — the **reconnecting socket's** queue (unicast, not `room.broadcast`). Safe because the re-emit filters `entry.defender == resume_char_name` (only the reconnecting player's own entries) and the sweep's `present` guard never touches a still-seated PC.

**Observations (tagged):**
- `[PRE]` Preflight GREEN — 24/24 story tests pass serially, ruff clean, **0 new pyright errors** (connect.py's 62 are pre-existing on the develop baseline, confirmed at identical lines), 0 code smells / TODOs / debug statements.
- `[SEC]` (security subagent) Two MEDIUM findings, both **pre-existing-rooted and non-blocking**: (a) the client-controlled `display_name` identity fallback in `resume_char_name` (`connect.py:1720`, *outside this diff*) could cross-seat-leak defend metadata in an MP legacy-backfill save — substitution is RESOLVE-blocked, info-only, ADR-119 territory; (b) the PARK-time broadcast-to-all (`fate_throw.py:170`, *outside this diff*). My re-emit itself uses correct unicast. Both → delivery findings.
- `[EDGE]` (edge_hunter disabled — Reviewer) VERIFIED the load-bearing edge: a **disconnected-but-still-seated** defender remains in `snapshot.characters` ⇒ `present=True` ⇒ never swept (the orphan safety invariant) — `fate_conflict.py:599`. Empty `resume_char_name` ("") matches no entry ⇒ safe no-op. Iteration mutates `entry.conceded` only, never the list structure ⇒ no concurrent-modification bug — `fate_conflict.py:596-606`.
- `[SILENT]` (silent_failure_hunter disabled — Reviewer) VERIFIED no swallowed errors: no `try/except`, no bare `except`, no `suppress`. The orphan-clear **concedes (never deletes)** so the NPC's sealed attack still resolves — No Silent Fallbacks honored — and every clear/re-emit fires a `fate.defend_phase` span + `logger.info`. `[LOW]` orphan-clear logs at `info`; a `warning` would better signal an abnormal mid-defend departure — non-blocking.
- `[TEST]` (test_analyzer disabled — Reviewer) VERIFIED 24 tests assert concrete values (request_id/attacker/attack_total/conceded/span attrs), no `assert True`/vacuous truthy checks. The one green-before-and-after test is a legitimate no-spurious-emit guard. The PG wiring test drives the **real connect handler** end-to-end (satisfies the wiring-test principle).
- `[DOC]` (comment_analyzer disabled — Reviewer) VERIFIED docstrings + the `connect.py:1790` comment accurately describe sweep-then-re-emit and the read-only/ADR-128 contract; no stale/misleading comments.
- `[TYPE]` (type_design disabled — Reviewer) `clear_orphaned_pending_defenses` is fully, correctly typed (`StructuredEncounter`/`GameSnapshot` → `list[FatePendingDefense]`). `_maybe_reemit_pending_defenses` uses `Any` for `sd`/`snapshot` — a **private** helper (underscore), exempt under python rule #3 and mirroring the `_maybe_emit_fate_state` sibling. Acceptable.
- `[SIMPLE]` (simplifier disabled — Reviewer) Minimal, mirrors the established sibling pattern; function-local imports avoid an import cycle (same as the sibling). The only rough edge is the gate asymmetry (Dev deviation, accepted).
- `[RULE]` (rule_checker disabled — Reviewer) Python lang-review checklist enumerated below — all pass, 2 LOW notes.

### Rule Compliance (python lang-review checklist)
- **#1 Silent exception swallowing:** No try/except in new code. ✓
- **#2 Mutable default args:** None (`_tracer=None`; `cleared=[]` is a local, not a default). ✓
- **#3 Type annotations at boundaries:** `clear_orphaned_pending_defenses` (public) fully typed; `_maybe_reemit_pending_defenses` is private → `Any` exempt. ✓
- **#4 Logging:** Lazy `%s` formatting, no f-strings, no sensitive data. `[LOW]` info-vs-warning for orphan-clear (non-blocking). ✓
- **#6 Test quality:** Concrete assertions, no vacuous/skip; real wiring test. ✓
- **#9 Async/await:** New helpers are sync, do no I/O (queue `.append`), called from the async handler without blocking. ✓
- **#10 Import hygiene:** Function-local imports avoid cycles (intentional, matches sibling); no star imports. `[LOW]` no `__all__` on the new module — but it exposes only a private helper. ✓
- **#11 Security input validation:** Re-emitted payload fields read from the **server-authored** `FatePendingDefense` ledger (skill sanitized at seal time); no user free-text on the wire. ✓ (identity-resolution caveat → `[SEC]` delivery finding)
- **#5/#7/#8/#12:** N/A (no paths, resources, deserialization, or deps changed).

### Devil's Advocate
Argue the code is broken. **Cross-seat leak:** the most credible attack is the `resume_char_name` → `display_name` identity fallback — in an MP legacy-backfill save a crafted `player_name` re-emits another PC's defend metadata. But `dispatch_fate_defense` enforces `actor==defender`, so the attacker cannot *throw* the victim's defense; the leak is information-only, the data was already broadcast to all sockets at PARK (pre-existing), and the root is the pre-existing identity resolution shared with the location/chapter re-emits — ADR-119 scope, not introduced here. **Double-prompt / double-throw:** could a reconnect re-prompt an entry the player already answered? No — filled (`defense_total is not None`) and `conceded` entries are skipped, so a player who already threw is not re-prompted. **Concurrent modification:** the sweep iterates `pending_defenses` while mutating `entry.conceded`; this mutates fields, not the list, so no `RuntimeError`. **Wrong-order sweep:** could the sweep concede the reconnecting player's own entry before re-emit? No — that player is in `pc_names` (present) ⇒ skipped ⇒ their entry survives to be re-emitted. **The real residual:** an "all-orphans, no live defender" round is conceded to ledger-full but nothing on the connect path calls `resume_fate_exchange`, so it sits parked-but-resumable until the next action. This is a genuine partial-fix limitation — but it is strictly better than the permanent wedge it replaces, is documented by TEA/Dev/Reviewer, and the primary playtest wedge (a present defender reconnecting) is fully fixed and proven by the PG wiring test. **Stressed inputs:** empty `resume_char_name`, no encounter, empty ledger, non-Fate pack — all verified safe no-ops. None of these rise to Critical/High.

**Pattern observed:** Faithful mirror of the `_maybe_emit_fate_state` resume re-emitter — `fate_defend_resume.py:28` and `connect.py:1810`.
**Error handling:** Loud-but-graceful — concede-not-drop + `fate.defend_phase` OTEL spans (`reason=reconnect_reemit` / `reason=orphaned`, routed via `SPAN_ROUTES["fate.defend_phase"]`) + `logger.info` on both paths.
**Handoff:** To SM (Morpheus) for finish-story.