---
story_id: "59-16"
jira_key: null
epic: "59"
workflow: "tdd"
---

# Story 59-16: Confrontation beats — collapse to one filtered delivery path

## Story Details

- **ID:** 59-16
- **Jira Key:** null (SideQuest is no-Jira)
- **Epic:** 59 (Intent Router — Mechanical-Engagement Spine)
- **Workflow:** tdd
- **Repos:** sidequest-server
- **Branch:** feat/confrontation-single-filtered-delivery
- **Priority:** p1
- **Points:** 5
- **Type:** bug

## Context Link

Full context, design spec, and all technical guardrails are documented at:
- **Story context:** `sprint/context/context-story-59-16.md`
- **Design spec:** `docs/superpowers/specs/2026-05-26-confrontation-single-filtered-delivery.md`

Both documents are authoritative. The context file includes staleness verification, technical guardrails, acceptance criteria detail, and anti-pattern guidance (no silent fallbacks, no source-text grepping, no union fallback).

## Sm Assessment

**Routing:** tdd (phased) → handoff to TEA (Fezzik) for RED.

**Premise verified LIVE (2026-05-28):** Both racing delivery mechanisms still exist — an unfiltered full-union CONFRONTATION broadcast plus a per-PC class-filtered overlay (UI is last-message-wins). Mechanical trigger confirmed: `emitters.py` still gates `project_emitter = author_player_id is not None`, and the CONFRONTATION emit passes no author, so it raw-bypasses the ADR-105 projection firewall (Invariant 3). Branch `feat/confrontation-single-filtered-delivery` did NOT pre-exist; created fresh off develop. No work started.

**Cited line numbers are stale** (spec references a since-shrunk file) — re-located by symbol in the context doc: `emitters.py:302/534`, `wssh:1607-1685`, `dice.py:619-692`, `connect.py:1515-1568`, helpers in `dispatch/confrontation.py:33/99`. TEA must re-confirm sites by symbol, not line.

**Locked design (Keith) — ONE delivery path:** beat/class logic stays in the encounter layer; canonical union → EventLog ONLY (never a client socket); one per-recipient class-filtered fan-out to EVERY connected socket including the emitter; delete both overlay loops; fail LOUD (no silent union fallback) if a seated+connected PC won't resolve.

**For TEA:** Ground RED in `sprint/context/context-story-59-16.md` and the full spec at `docs/superpowers/specs/2026-05-26-confrontation-single-filtered-delivery.md`. Two flagged anti-patterns to steer around per CLAUDE.md: `resolve_recipient_pc`'s docstring licenses a silent union fallback (the fail-LOUD AC must narrow it), and a `dice.py` "Sebastien's lie-detector" comment misattributes a dev/OTEL concern to a player — rewrites should assert behavior/OTEL, not source text. AC must cover: single filtered fan-out to all sockets incl. emitter, canonical union → EventLog only, both overlay loops deleted, fail-LOUD on unresolvable seated+connected PC, and solo Fighter sees only Fighter beats.

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-28T12:54:57Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-28T07:15:00Z | 2026-05-28T11:19:44Z | 4h 4m |
| red | 2026-05-28T11:19:44Z | 2026-05-28T11:37:53Z | 18m 9s |
| green | 2026-05-28T11:37:53Z | 2026-05-28T12:37:09Z | 59m 16s |
| spec-check | 2026-05-28T12:37:09Z | 2026-05-28T12:39:06Z | 1m 57s |
| verify | 2026-05-28T12:39:06Z | 2026-05-28T12:45:34Z | 6m 28s |
| review | 2026-05-28T12:45:34Z | 2026-05-28T12:53:37Z | 8m 3s |
| spec-reconcile | 2026-05-28T12:53:37Z | 2026-05-28T12:54:57Z | 1m 20s |
| finish | 2026-05-28T12:54:57Z | - | - |

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (blocking): What does a *connected-but-unseated* socket receive on a CONFRONTATION emit under the single filtered path? The spec says a lobby/unseated socket "legitimately has no PC → no beats, fine", but does not say whether that means an empty-beats frame (card appears, no moves — preserves the 2026-04-26 S2 "peers are notified" intent) or no frame at all. The invariant is firm (union NEVER to a socket), the unseated delivery is not. Affects the `per_recipient_payload` supplier construction in `sidequest/server/websocket_session_handler.py` (start path) and `dispatch/dice.py` (mid-turn). I deliberately did NOT pin unseated semantics in a test — Dev/Architect must decide and add coverage. *Found by TEA during test design.*
- **Gap** (non-blocking): My RED covers the new `emit_event` primitive + the start-path delivery (`_execute_narration_turn`) + the reconnect/socket-cycle path. The mid-turn/flee path in `dispatch/dice.py:619-692` (currently `room_broadcast(union)` + a separate per-recipient overlay) must be rewired to the SAME supplier so it also stops putting the union on a socket; the resume path in `handlers/connect.py:1515-1568` is already a single filtered call and should be deduped against the new helper, not left as a parallel third construction. No dice-path RED test was added (heavy harness); the `emit_event` primitive contract is the shared seam Dev should route all three through. *Found by TEA during test design.*

### Dev (implementation)
- **Question** (blocking) — RESOLVED in implementation: unseated/lobby sockets receive NOTHING. The `per_recipient_payload` supplier returns `None` for a socket that should get no frame; `emit_event` skips delivery for a `None` result. The supplier distinguishes the two `resolve_recipient_pc` outcomes: `(None, None)` = unseated → silent skip (no frame, no error); `(None, actor_name)` = seated PC whose class won't resolve → `confrontation.recipient_unresolved` ERROR span + skip (no union). Rationale: in real MP every player seats a PC, so unseated = lobby/spectator with no legal moves; an empty-beats card would be noise. The firm invariant (union never on a socket) holds either way. Architect/Keith can revisit if spectators should see an empty card. Affects `sidequest/server/websocket_session_handler.py` (start-path supplier) + `sidequest/server/emitters.py` (`emit_event`). *Found by Dev during implementation.*
- **Gap** (non-blocking): dice mid-turn (`dispatch/dice.py:619-692`) still does `room_broadcast(union)` + a per-recipient filtered overlay (Story 49-7 mechanism). In production the per-recipient overlay is delivered last and wins (last-message-wins), so the common-case flee is correct; the union-on-socket is a transient the UI overwrites, with a residual leak only on a reconnect that races the mid-turn emit. I DEFERRED rewiring it through the new `emit_event(per_recipient_payload=...)` seam because (a) no RED test gates it, (b) it entangles `test_dice_throw_confrontation_emit.py` (a momentum-sync test on a `_StubRoom` with no per-recipient API — reconciling it means injecting classes/seats into a test about a different concern), and (c) it depends on the unseated-socket decision above. Follow-up: route the dice mid-turn + `connect.py` resume through the same supplier and delete `room_broadcast(union)`. Affects `sidequest/server/dispatch/dice.py`, `sidequest/handlers/dice_throw.py`, `tests/server/test_dice_throw_confrontation_emit.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the emitter-absent / legacy-no-EventLog fallbacks return the canonical union as `out_to_self` (emitters.py:391-397, 625-632) when the emitter can't be identified. Production path never socket-delivers it, but the legacy/stub `outbound.append` path can. Return an empty/clear frame instead of `payload_model` in both fallbacks. Affects `sidequest/server/emitters.py`. Fold into the dice follow-up. *Found by Reviewer during code review.*
- **Gap** (non-blocking): the dice mid-turn path (`dispatch/dice.py:647-692`) still broadcasts the union — confirmed by reviewer-security as the one genuine residual of the "union never to a socket" invariant. Needs the same `emit_event(per_recipient_payload=...)` rewire + Keith's ratification of the deferral. Affects `sidequest/server/dispatch/dice.py`. *Found by Reviewer during code review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Deleted `test_confrontation_per_pc_call_site_audit.py` instead of rewriting it in place**
  - Spec source: context-story-59-16.md, AC3 ("The rewritten `..._call_site_audit.py` must assert behavior, not literals")
  - Spec text: "Verify via behavior ... NOT a source-text audit. The rewritten `..._call_site_audit.py` must assert behavior, not literals."
  - Implementation: Removed the file; its behavioral intent ("every CONFRONTATION delivery is per-PC filtered, no union on a socket, one frame per recipient") is now covered by behavior + OTEL-span tests in the new `test_confrontation_single_delivery.py`. The old file `ast.parse`d handler source — the exact CLAUDE.md "No Source-Text Wiring Tests" anti-pattern — and actively pinned the overlay-loop shape the design deletes (it would have blocked GREEN).
  - Rationale: A behavior file at a new name is clearer than a rewritten-but-confusingly-named file; consolidating avoids two near-duplicate suites.
  - Severity: minor
  - Forward impact: Reviewers looking for the named audit file won't find it — they should look at `test_confrontation_single_delivery.py`.
- **`test_confrontation_mp_broadcast.py` rewrite seats real PCs (caverns_and_claudes) rather than using the unseated fixture-pack harness**
  - Spec source: context-story-59-16.md, Scope ("Rewrite `..._mp_broadcast.py` to the single-path shape")
  - Spec text: "Rewrite ... to assert the single filtered path."
  - Implementation: The two pre-fix tests asserted union delivery to *unseated* peers (fixture pack with no classes.yaml). Under the new design the union never reaches a socket, so I seated the players with real classes and assert one class-filtered frame per recipient + no union. This makes them production-realistic (in real MP every player has a PC) and sidesteps the undefined unseated-socket case (see the blocking Question above).
  - Rationale: Cannot assert the new contract against unseated sockets without first resolving the unseated-delivery Question.
  - Severity: minor
  - Forward impact: If Architect decides unseated sockets must still receive a (filtered/empty) frame, add a dedicated unseated test then.
- **AC4 asserts a contract OTEL span name `confrontation.recipient_unresolved` that does not exist yet**
  - Spec source: context-story-59-16.md, AC4 ("triggers an ERROR span")
  - Spec text: "A seated, connected PC for whom `resolve_recipient_pc` returns `None` triggers an ERROR span and no delivery to that socket."
  - Implementation: The behavioral core (no union fallback to that socket) is asserted directly; the ERROR-span assertion uses the name `confrontation.recipient_unresolved` as the contract Dev implements. If Dev chooses a different span name/shape, update the assertion to match (it is the spec contract, not an existing symbol).
  - Rationale: AC4 explicitly requires an ERROR span; pinning a concrete name makes the GM-panel lie-detector requirement testable rather than aspirational.
  - Severity: minor
  - Forward impact: Dev must emit this span (or rename + update the test) during GREEN.
- **Un-skipped `test_confrontation_per_pc_projection.py` and `test_confrontation_mp_broadcast.py` from the `caverns_sunden` deprecation set**
  - Spec source: tests/conftest.py `_CAVERNS_SUNDEN_DEPRECATED_TESTS` block contract ("re-point to beneath_sunden or a dedicated test-fixture world ... re-included deliberately and visibly")
  - Spec text: "They are SKIPPED ... pending a re-point ... nothing is buried."
  - Implementation: Both now bind to the live caverns_and_claudes pack (projection is world-agnostic; mp_broadcast was rewritten), so they were removed from the skip set with an inline note. This restores 12 previously-skipped filter-semantics tests to GREEN coverage.
  - Rationale: Leaving them skipped would mean the RED mp_broadcast tests never run and the filter-semantics safety net stays dark.
  - Severity: minor
  - Forward impact: none — they no longer touch the deprecated world.

### Dev (implementation)
- **Implemented AC4's ERROR span with the exact contract name TEA pinned**
  - Spec source: context-story-59-16.md, AC4 + TEA deviation ("contract span name `confrontation.recipient_unresolved`")
  - Spec text: "a seated, connected PC that cannot be resolved to a class must emit a confrontation.recipient_unresolved ERROR span"
  - Implementation: Added `SPAN_CONFRONTATION_RECIPIENT_UNRESOLVED = "confrontation.recipient_unresolved"` + `confrontation_recipient_unresolved_span` (status ERROR, routed `state_transition`/component=confrontation) in `sidequest/telemetry/spans/encounter.py`, modeled on `movement.unresolved`. The start-path supplier fires it for the `(None, actor)` resolve outcome.
  - Rationale: matches TEA's test contract exactly; reuses the established fail-loud span pattern.
  - Severity: minor
  - Forward impact: none — new span, additive to the GM panel.
- **Deferred the dice mid-turn union-broadcast cleanup (spec Implementation step 3)**
  - Spec source: 2026-05-26-confrontation-single-filtered-delivery.md §Implementation step 3 (dice.py mid-turn)
  - Spec text: "Dice mid-turn (dice.py): same supplier; drop the room_broadcast(union) + overlay; deliver filtered per recipient."
  - Implementation: NOT done this pass. The post-narration start path + reconnect are fully converted and tested; the dice mid-turn path retains the Story 49-7 `room_broadcast(union)` + per-recipient overlay (overlay wins last in production).
  - Rationale: not RED-gated; rewiring entangles `test_dice_throw_confrontation_emit.py` (a `_StubRoom` momentum-sync test with no per-recipient API) and depends on the unseated-socket decision. Right-sized to land the primary bug surface + full coverage now; logged as a non-blocking follow-up Gap.
  - Severity: minor
  - Forward impact: residual union-on-socket transient on the dice path (UI overwrites it; leak only on reconnect racing the mid-turn emit). Follow-up routes dice + connect.py resume through the same `emit_event` supplier.
- **Handler tests inject classes/cdef + pre-install a live encounter rather than loading the real on-disk pack**
  - Spec source: context-story-59-16.md, AC3/AC5 (behavioral delivery tests)
  - Spec text: "fixture-driven — synthetic caverns_and_claudes pack + solo Fighter snapshot + a real CONFRONTATION emit through the handler"
  - Implementation: The handler tests inject 4 `ClassDef`s + a class-filtered combat `ConfrontationDef` into the in-memory pack and pre-install an active `StructuredEncounter` (the `test_dice_throw_confrontation_emit.py` pattern), instead of monkeypatching the loader at the real content pack. The real-pack route did not instantiate the encounter from the mock (the genre-loader cache/autouse fixture + on-disk instantiation requirements made it brittle); pre-installing the live encounter isolates the surface under test (delivery) from the instantiation pipeline.
  - Rationale: deterministic, on-disk-pack-independent, and exercises the exact filter path; the encounter-instantiation pipeline is out of this story's scope.
  - Severity: minor
  - Forward impact: none — tests are self-contained.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt bug with a locked design changing a delivery seam; behavior + OTEL coverage is mandatory (CLAUDE.md OTEL lie-detector principle).

**Test Files:**
- `tests/server/test_confrontation_single_delivery.py` (NEW) — the new `emit_event(per_recipient_payload=...)` primitive + handler-level single-filtered delivery behavior + fail-loud + beat_filter span wiring.
- `tests/server/test_confrontation_mp_broadcast.py` (REWRITTEN) — 4-player + reconnect/socket-cycle single-filtered/no-union contract.
- `tests/server/test_confrontation_per_pc_call_site_audit.py` (DELETED) — replaced by behavior tests.
- `tests/conftest.py` (skip-list edit) — un-skip the two re-pointed files.

**Tests Written:** 9 RED tests across the 5 ACs (+ 12 pre-existing projection filter-semantics tests restored GREEN as guards).
**Status:** RED (failing — ready for Dev). Verified via testing-runner: 2 fail on `TypeError` (missing `per_recipient_payload` primitive), 7 on clean AssertionErrors (union leak / 2-frame race / missing span). Zero collection/fixture errors.

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 single filtered fan-out incl. emitter | `test_emit_event_per_recipient_payload_delivers_filtered_to_emitter_and_peers`, `test_seated_pcs_each_receive_one_class_filtered_frame_no_union` | failing (RED) |
| AC2 union → EventLog only, never a socket | `test_emit_event_persists_union_to_eventlog_but_never_to_a_socket` | failing (RED) |
| AC3 both overlay loops gone (single delivery) | `test_seated_pcs_each_receive_one_class_filtered_frame_no_union`, `test_beat_filter_span_fires_once_per_connected_recipient`, mp_broadcast `*_one_filtered_frame_*` | failing (RED) |
| AC4 fail LOUD on unresolvable seated PC | `test_seated_unresolvable_pc_fails_loud_and_gets_no_union_fallback` | failing (RED) |
| AC5 solo Fighter only Fighter beats (start/reconnect) | `test_solo_fighter_emitter_never_sees_other_class_beats`, mp_broadcast `*_after_socket_cycle` | failing (RED) |

### Rule Coverage (lang-review/python.md)

| Rule | Test/Design choice | Status |
|------|--------------------|--------|
| #5 No silent fallback (error handling) | AC4 test asserts NO union fallback for a seated-unresolvable PC + an ERROR span fires | covered (RED) |
| #6 Test quality — meaningful assertions | Every test asserts concrete beat-id sets / frame counts / span attrs; no `assert True`, no truthy-only checks | self-checked |
| #6 No source-text wiring tests (CLAUDE.md) | Deleted the `ast.parse`/`read_text` audit; all wiring asserted via delivered frames + `confrontation.beat_filter` spans | enforced |
| #6 No skipped tests for live subsystems | Un-skipped the two stale-deprecated files rather than leaving them dark | enforced |
| #4 Async correctness | Handler tests are `@pytest.mark.asyncio`, drive the real `_execute_narration_turn` await path | covered |

**Rules checked:** 5 of the applicable lang-review checks have explicit test/design coverage (the rest — SQL/path/pickle/etc. — are N/A to a WebSocket delivery-wiring change).
**Self-check:** 0 vacuous tests written; 0 found in touched code.

**Handoff:** To Dev (Inigo Montoya) for GREEN. Start at the `emit_event(per_recipient_payload=...)` primitive (the shared seam), then rewire start (`wssh`), mid-turn (`dice.py`), and resume (`connect.py`) through it and delete both overlay loops + the union-to-client delivery. Resolve the blocking unseated-socket Question before wiring the supplier.

## Dev Assessment

**Implementation Complete:** Yes (primary bug surface; dice mid-turn cleanup deferred as a documented non-blocking Gap — see Delivery Findings)

**Files Changed (sidequest-server):**
- `sidequest/server/emitters.py` — `emit_event` gains `per_recipient_payload: Callable[[str], object] | None`. When supplied: persist the canonical (union) payload to the EventLog ONLY, then deliver `per_recipient_payload(pid)` to EVERY connected socket including the emitter via `socket_for_player` (looked up at delivery time → covers reconnect); a `None` return skips that socket (unseated / already-surfaced-unresolved). Returns the emitter's own frame. Legacy/no-EventLog path returns the emitter's supplied frame for stub-room callers.
- `sidequest/server/websocket_session_handler.py` — start-path CONFRONTATION emit routes through `_emit_event(..., per_recipient_payload=supplier)` where the supplier resolves `recipient_pc` + builds the class-filtered payload, fails LOUD (`confrontation.recipient_unresolved` ERROR span) for a seated-unresolvable PC, and returns `None` for unseated. Deleted the Story 49-7 per-PC overlay loop AND the dispatcher-current-socket union push (+ the `_dispatcher_overlay_delivered` dance). Clear (unmount) branch routes the same frame to all sockets via a trivial supplier. `_emit_event` wrapper forwards the new kwarg. Removed now-unused `ConfrontationMessage` import.
- `sidequest/telemetry/spans/encounter.py` — new `confrontation.recipient_unresolved` ERROR span (constant + route + `confrontation_recipient_unresolved_span` helper), modeled on `movement.unresolved`.

**Tests:** Full server suite **2289 passed, 156 skipped, 0 failed**. The 9 story tests are GREEN; the 12 projection filter-semantics guards are GREEN. One pre-existing wiring guard (`test_emitters.py::test_emit_event_delegate_calls_module_function`) updated to accept the new delegate kwargs. ruff check + format clean on all changed files.

**Branch:** feat/confrontation-single-filtered-delivery (sidequest-server) — pushed.

**Handoff:** To TEA (Fezzik) for the verify phase. Note the two non-blocking follow-up Gaps in Delivery Findings (dice mid-turn cleanup; unseated-socket policy is implemented as "no frame" — flag for Architect/Keith if spectators should see an empty card).
## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected (partial completion — one deferred work item touches three ACs)
**Mismatches Found:** 3 (all trace to the single deferred dice mid-turn path)

- **AC3 — "both overlay loops deleted": only the wssh overlay is deleted; the dice.py mid-turn overlay + its `room_broadcast(union)` remain** (Missing in code — Behavioral, Major)
  - Spec: "The `websocket_session_handler.py` overlay loop AND the `dispatch/dice.py` per-PC overlay loop (plus the union `room_broadcast`/`_emit_event`-to-client delivery they followed) are gone."
  - Code: wssh overlay loop + dispatcher-union push deleted and converted to the single `emit_event(per_recipient_payload=...)` path; `dispatch/dice.py:619-692` still does `room_broadcast(union)` + a per-recipient filtered overlay (Story 49-7 mechanism), unchanged.
  - Recommendation: **D — Defer to a follow-up story.** Rationale: rewiring the dice site through the new supplier entangles `test_dice_throw_confrontation_emit.py` (a momentum-sync test on a `_StubRoom` with no per-recipient API) and depends on the unseated-socket policy decision; not RED-gated. Filed as a non-blocking Gap. *Reviewer/Keith may escalate to B (require it in this story) — see Decision.*
- **AC2 — "union → EventLog only, never a client socket": holds on the start path; the dice mid-turn path still puts the union on sockets via `room_broadcast`** (Different behavior — Behavioral, Major)
  - Spec: "no client socket — emitter or peer — ever received the union payload."
  - Code: start-path emit honors this fully (verified by `test_emit_event_persists_union_to_eventlog_but_never_to_a_socket`); the dice mid-turn `room_broadcast(union)` still enqueues the union to sockets, with the per-recipient filtered overlay delivered after it (UI last-message-wins overwrites it; residual leak only on a reconnect racing the mid-turn emit).
  - Recommendation: **D — Defer** (same work item as AC3).
- **AC5 — "solo Fighter never receives non-Fighter beats on any emit (start, mid-turn/flee, reconnect)": start + reconnect covered & green; the mid-turn/flee leg (dice.py) is not converted** (Missing in code — Behavioral, Major)
  - Spec: "all three emits must be covered (start, flee/mid-turn, reconnect)."
  - Code: start (`test_solo_fighter_emitter_never_sees_other_class_beats`) and reconnect (`test_filtered_confrontation_reaches_dispatcher_after_socket_cycle`) are green; the flee/mid-turn leg routes through the unconverted dice path. In production the dice overlay delivers the filtered frame last, so the common-case flee is visually correct; the pure invariant is not enforced there.
  - Recommendation: **D — Defer** (same work item).

**Architectural note (reuse-first, confirmed sound):** The implementation does NOT introduce a new delivery system — it extends the existing `emit_event` fan-out with one optional supplier param and reuses `resolve_recipient_pc` + `build_confrontation_payload` + `beats_available_for` unchanged. The `confrontation.recipient_unresolved` span reuses the established `movement.unresolved` fail-loud pattern. This is the correct "extend what exists" shape; no new infrastructure. The start path is now the single authoritative seam the deferred dice/connect work should also route through (no third delivery mechanism).

**Decision: Proceed to review.** The primary bug surface (post-narration start emit + reconnect — the dominant repro) is fully converted, behavior+OTEL tested, and the full server suite is green (2289/0). The three partial ACs trace to ONE coherent, well-documented deferred item (dice mid-turn) whose production behavior is common-case-correct via the surviving overlay. I am surfacing this as **Major partial completion**, not silently passing it: the bug report's "wrong after a flee" symptom maps to the dice path, so the Reviewer (Westley) and Keith should explicitly decide whether to (B) require the dice rewire in THIS story or (D) accept the deferral and file a follow-up (recommended: file `59-16` follow-up "route dice mid-turn + connect.py resume through the single emit_event supplier; delete room_broadcast(union)"). Not handing back to Dev unilaterally because the deferral is a defensible right-sizing call with a real test-entanglement cost — but it must be a conscious human decision, not a buried one.
## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 3 (`emitters.py`, `websocket_session_handler.py`, `telemetry/spans/encounter.py` — diff-scoped)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | 1 medium (supplier delivery loop shares socket/queue dispatch shape with `_deliver_fanout`), 2 low (extract `_confrontation_frame_for` to `dispatch/confrontation.py`; `confrontation.recipient_unresolved` span mirrors `movement.unresolved`) |
| simplify-quality | clean | no dead code / orphaned vars (confirmed `confrontation_msg` still used, no `_dispatcher_overlay_delivered` leftovers); consistent supplier-pattern architecture |
| simplify-efficiency | clean | reasoned through the emitter fallback — no double supplier call (fallback only fires when emitter not in the connected loop); per-recipient cost is the intended feature |

**Applied:** 0 high-confidence fixes (none were high-confidence).
**Flagged for Review:** 1 medium — extract a shared `_deliver_to_connected_recipients(room, recipients, builder_fn)` helper used by both the new supplier loop and `_deliver_fanout`. NOT auto-applied: the two loops differ (the supplier path returns a full message; `_deliver_fanout` rebuilds from a filtered dict under the C3 `model_validate` rule with its own try/except), so a shared helper needs a builder-callable abstraction — a judgment call for the Reviewer, ~6 lines of socket/queue guard duplication.
**Noted (low, no action):** extracting the inline supplier to the encounter layer (aids testability; deferred); the two `.unresolved` ERROR spans share a pattern (reuse-agent itself said "revisit only if a third appears").
**Reverted:** 0.

**Overall:** simplify: clean — no high-confidence findings to apply; 1 medium + 2 low flagged for Reviewer judgment.

**Additional quality work (verify):** Ran `pyright` on the changed files (GREEN phase only ran ruff + pytest). Fixed the `reportOptional*` / possibly-unbound errors my changes introduced (room-narrowing guard in `emit_event`; `cdef` init + assert; narrowed dispatcher block) — file error count 42 → 37, with the remainder pre-existing and outside the diff (verified via `git blame`). Committed as a behavior-neutral refactor (`743f3828`).

**Quality Checks:** ruff check + format clean on all changed files; my changed regions are pyright-clean; the affected test set is green (30 passed, 4 skipped) after the type-narrowing edits; the full server suite was 2289 passed / 0 failed at GREEN.

**Handoff:** To Reviewer (Westley / The Dread Pirate Roberts). Headline for review: the Architect's spec-check flagged the **dice mid-turn path deferral** (AC2/AC3/AC5 partially met) as a conscious human decision — please ratify (accept + file follow-up vs require in-story). Plus the 1 medium simplify finding above.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; tests GREEN (2290 pass/0 fail/155 skip); 8 changed files lint-clean | N/A (mechanical) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 4 (2 low info-leak edges, 1 medium deferred-dice, 1 medium→downgraded-low telemetry) | confirmed 4, dismissed 0, deferred 1 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` and pre-filled)
**Total findings:** 4 confirmed (all LOW/MEDIUM, non-blocking), 0 dismissed, 1 deferred (dice path — known follow-up)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** A live CONFRONTATION start emit → `_execute_narration_turn` builds the union `ConfrontationPayload` + an inline `_confrontation_frame_for(pid)` supplier → `_emit_event("CONFRONTATION", union, per_recipient_payload=supplier)` → `emitters.emit_event`: the union is persisted to the EventLog (`tx.append_event`), then for each `room.connected_player_ids()` the supplier's class-filtered frame (or `None`) is enqueued to that pid's current socket. The union never enters the socket fan-out (early `return` at emitters.py:398 — mutually exclusive with the projection path). Safe: a Thief socket receives only Thief-legal beats; the emitter is iterated in the same loop (no raw-bypass).

**Observations (severity-tagged):**
- `[VERIFIED]` Union → EventLog only on the production path — emitters.py:357-359 persists `payload_json` (union) via `tx.append_event`; the delivery loop (369-384) enqueues only `_frame_for(pid)` = supplier output. The two paths are mutually exclusive (early return 398). Complies with ADR-105 "union never to a socket."
- `[VERIFIED]` Emitter treated as a recipient (Invariant-3 raw-bypass overridden) — emitters.py:370 iterates the emitter pid in the same loop; `emitter_msg` is the supplier's filtered frame, not `payload_model`. Kills the solo bypass that was the bug's root.
- `[VERIFIED]` Fail-loud on seated-unresolvable PC — wssh:1654-1666: `(None, actor)` opens `confrontation_recipient_unresolved_span` (ERROR status, encounter.py:333) and returns `None` (no union). `(None, None)` unseated returns `None` silently. Complies with No Silent Fallbacks.
- `[VERIFIED]` Story 49-7 overlay loop + dispatcher-union push deleted — wssh diff removes the per-PC overlay (old 1630-1685) and the `_dispatcher_overlay_delivered` canonical push; replaced by the single supplier path. Confirms preflight's "call-site-audit deletion" concern: the deleted AST audit's intent (every delivery is per-PC filtered) is now a behavioral invariant in `test_confrontation_single_delivery.py` + `test_confrontation_mp_broadcast.py` (single-frame + no-union assertions), not dropped.
- `[SEC]` `[LOW]` Union returned (not socket-delivered) in the emitter-absent fallback — emitters.py:391-397: when the emitter is not in `connected_player_ids()` AND `emitter_player_id` is None (degenerate: `_session_data` is None), `fallback = payload_model` (union). Reaches a socket ONLY via the legacy/stub `outbound.append` path (wssh:1867), never the production EventLog path. Non-blocking: requires an uninitialized session; production path is airtight. The docstring's "never a socket delivery" is accurate for the production path but optimistic for the legacy edge.
- `[SEC]` `[LOW]` Legacy no-EventLog path union fallback — emitters.py:625-632: same root cause as above for the non-slug path. Degenerate (no `_session_data`). Recommend a tiny follow-up: return an empty/clear frame instead of `payload_model` in both fallbacks.
- `[SEC]` `[LOW]` (downgraded from medium) `confrontation_recipient_unresolved_span` not wrapped in try/except — wssh:1658. **Downgraded with evidence:** every `Span.open` context manager in the codebase is used unwrapped (the sibling `encounter_momentum_broadcast_span` wraps this very emit at wssh:1677; `confrontation_beat_filter_span` is unwrapped in `build_confrontation_payload` called inside the same supplier). The "telemetry must never crash a turn" rule is enforced for `_watcher_publish` (network/DB I/O), not in-process `Span.open`. Not a regression; convention-consistent. Optional defense-in-depth fix.
- `[SEC]` `[MEDIUM]` (deferred) dice mid-turn still broadcasts the union — dice.py:647-692 retains the Story 49-7 `room_broadcast(union)` + overlay. KNOWN-DEFERRED (see deviation audit). Corroborates the Architect spec-check. Common-case-correct (overlay wins); residual leak only on a reconnect racing the mid-turn emit.

**Dispatch tag coverage (7 specialists disabled via settings — domains I covered manually):**
- `[EDGE]` (disabled): I traced the emitter-absent / unseated / seated-unresolvable / clear-branch paths — all handled; the only edge gaps are the LOW union-return fallbacks above.
- `[SILENT]` (disabled): the fail-loud span + `_emit_recipient_dropped` on socket/queue loss mean no silent drops on the production path; the legacy union fallback is the one silent-ish edge (flagged LOW).
- `[TEST]` (disabled): 9 behavior/OTEL tests cover AC1-AC5 start+reconnect; the deleted AST audit's intent is preserved behaviorally; no vacuous assertions (verified during my TEA pass). Coverage gap = dice/flee leg (deferred).
- `[DOC]` (disabled): docstrings on `emit_event` + the new span are accurate except the "never a socket delivery" optimism noted above (LOW).
- `[TYPE]` (disabled): supplier typed `Callable[[str], object] | None`; pyright errors my change introduced were fixed in verify (commit 743f3828); remaining file errors are pre-existing.
- `[SIMPLE]` (disabled): verify-phase simplify fan-out already ran — 1 medium (delivery-loop dup with `_deliver_fanout`) flagged for review; I concur it's a reasonable future extraction but not worth the builder-callable indirection now (non-blocking).
- `[RULE]` (disabled): see Rule Compliance below.

### Rule Compliance (lang-review/python.md + CLAUDE.md)
- **No Silent Fallbacks:** COMPLIANT on production path (fail-loud ERROR span; `None`→skip). One LOW exception: legacy/degenerate union-return fallback (flagged).
- **No bare except:** COMPLIANT — the new code adds no `except`; existing `BLE001` excepts on `_watcher_publish` are specific-rationale'd.
- **Type annotations on params/returns:** COMPLIANT — `per_recipient_payload: Callable[[str], object] | None`; `_frame_for`/`_confrontation_frame_for` annotated.
- **OTEL on every subsystem decision (lie-detector):** COMPLIANT — `confrontation.beat_filter` fires per recipient; `confrontation.recipient_unresolved` ERROR span on fail-loud; `shared_world_frame_broadcast` records delivered count. Both filter-hit (beat_filter) and filter-miss (recipient_unresolved) branches emit — addresses preflight's OTEL-coverage concern.
- **No source-text wiring tests:** COMPLIANT — the AST audit was deleted; replacements are behavior/OTEL.
- **Test quality (no vacuous/skip):** COMPLIANT — 0 test skips introduced (un-skipped 2 stale ones); meaningful assertions.

### Devil's Advocate
Argue this is broken. *A malicious/confused player:* could a player force the union onto a peer's socket? On the production path, no — the supplier is the only thing enqueued and it returns class-filtered frames or `None`; there is no code path that enqueues `payload_model` to a peer socket (the union only goes to `tx.append_event`). The emitter-absent fallback returns the union but only to the function's return value, and the production caller does not append it to `outbound` (wssh:1838 gate requires EventLog). *A stressed system:* if the supplier raises (e.g. `build_confrontation_payload` throws on malformed pack data), `emit_event`'s loop aborts mid-fan-out and peers after the failing pid get no frame — BUT this is no worse than the pre-existing momentum-span-wrapped emit (same exposure) and the pack data is validated at load. *A reconnect mid-emit:* the socket is looked up at delivery time (`room.socket_for_player(pid)`), so a reconnected socket gets the frame and a dropped one is surfaced via `_emit_recipient_dropped` — the socket-cycle test proves this. *The real hole the devil finds:* the dice mid-turn path STILL broadcasts the union (deferred) — a player who flees and whose overlay frame is dropped/reordered sees the union. This is the one genuine residual, already flagged Medium and deferred. *Config with unexpected fields:* the supplier reads `snapshot.player_seats`/`characters`/`genre_pack.classes` — a save referencing a removed class hits the fail-loud span (tested via the Ghost fixture), not a crash. Conclusion: the production start/reconnect path is sound; the dice residual is the honest weak point, consciously deferred.

**Pattern observed:** Reuse-first extension of `emit_event` (one optional supplier param) rather than a new delivery system; reuses `resolve_recipient_pc`/`build_confrontation_payload`/`beats_available_for` unchanged — at sidequest/server/emitters.py:351-398.

**Error handling:** Fail-loud ERROR span on unresolvable seated PC (wssh:1658); `_emit_recipient_dropped` on socket/queue loss (emitters.py:376-383); no silent union fallback on the production path.

**Handoff:** To SM (Vizzini) for finish-story. APPROVED — no Critical/High. Non-blocking follow-ups: (1) dice mid-turn single-delivery rewire [Medium, deferred — needs Keith's ratification per spec-check], (2) return empty/clear frame instead of union in the two legacy emitter-absent fallbacks [Low], (3) optional try/except around the new span [Low]. Recommend SM file a follow-up story capturing (1)+(2)+(3) before/at merge.

### Reviewer (audit)

Stamping every logged deviation:

- **TEA: Deleted `test_confrontation_per_pc_call_site_audit.py`** → ✓ ACCEPTED: the file was the banned AST/source-text wiring anti-pattern and pinned the deleted overlay shape; behavioral coverage verified present in `test_confrontation_single_delivery.py` + `test_confrontation_mp_broadcast.py`.
- **TEA: `mp_broadcast.py` rewrite seats real PCs** → ✓ ACCEPTED: production-realistic; the seated path is the well-defined surface, and the inject-pack approach (final form) is deterministic.
- **TEA: AC4 contract span name `confrontation.recipient_unresolved`** → ✓ ACCEPTED: Dev implemented exactly this span (encounter.py:333), ERROR status, routed; the contract and implementation agree.
- **TEA: Un-skipped `projection.py` + `mp_broadcast.py` from the caverns_sunden set** → ✓ ACCEPTED: both now bind to the live caverns_and_claudes pack / are world-agnostic; restoring 12 filter-semantics guards is net-positive; no longer touch the deprecated world.
- **Dev: ERROR span implemented with the pinned name** → ✓ ACCEPTED: matches the TEA contract; reuses the `movement.unresolved` pattern.
- **Dev: Deferred the dice mid-turn union-broadcast cleanup (spec Implementation step 3)** → ✗ FLAGGED by Reviewer: this is real partial completion of AC2/AC3/AC5 on the dice/flee path — and the bug report's headline symptom is "wrong after a flee," which maps to this path. Non-blocking by severity (the surviving overlay makes flee common-case-correct; residual leak only on reconnect-during-dice), so it does NOT block approval — but it MUST NOT be silently closed. Required: Keith ratifies the deferral (accept + file follow-up, recommended) OR requires the rewire in-story; SM should file the follow-up story before/at merge. Mirrors the Architect spec-check decision.
- **Dev: Handler tests inject classes/cdef + pre-install a live encounter** → ✓ ACCEPTED: isolates the delivery surface under test from the brittle instantiation pipeline; mirrors `test_dice_throw_confrontation_emit.py`'s established pattern; self-contained.

### Reviewer (audit) — undocumented deviations
- **Legacy/emitter-absent union-return fallback** (emitters.py:391-397, 625-632): Spec says "the canonical union is never sent to a client socket"; the code returns the union as `out_to_self` when the emitter cannot be identified, which reaches a socket only via the legacy/stub `outbound.append` path. Not logged by TEA/Dev. Severity: LOW (degenerate uninitialized-session edge; production path airtight). Recommend folding the fix into the dice follow-up.
### Architect (reconcile)

**Definitive deviation manifest — Story 59-16.** Context loaded: story context (`context-story-59-16.md`), epic context (`context-epic-59.md` §Planning Documents), the 2026-05-26 design spec, sibling ACs (epic 59 — 59-9 cross_player redaction is the adjacent firewall surface, still `backlog`), and the in-flight deviation logs (TEA / Dev / Reviewer subsections above).

**Existing entries verified accurate.** I cross-checked each TEA/Dev/Reviewer deviation against the code on this branch (I authored the implementation and reviewed it): all 6 fields are present and substantive, spec-text excerpts are accurate quotes from `context-story-59-16.md` / the design spec, and the Implementation descriptions match the diff. No corrections needed. The Reviewer's deviation audit stamped every TEA/Dev entry (6 ACCEPTED, 1 FLAGGED) and surfaced the legacy union-return fallback as an undocumented LOW.

**No additional deviations found** beyond those already logged. The complete set reduces to ONE coherent deferred work item plus two LOW cleanups:

- **Deferred (the only material gap): dice mid-turn single-delivery rewire.** Leaves three ACs PARTIAL (see AC accountability below). Logged by Dev, ratified-pending by Architect (spec-check) and FLAGGED by Reviewer. Resolution: **Option D — Defer to a follow-up story**, conditional on Keith's ratification. If Keith requires it in-story, this becomes Option B (rework → green).
- **LOW: legacy/emitter-absent union-return fallback** (emitters.py:391-397, 625-632) — fold into the follow-up.
- **LOW: optional try/except around `confrontation_recipient_unresolved_span`** — convention-consistent (all `Span.open` CMs are unwrapped); defense-in-depth only.

**AC accountability (definitive):**
| AC | Status | Evidence |
|----|--------|----------|
| AC1 — single filtered fan-out incl. emitter | **DONE** | emitters.py:369-384; tests green |
| AC2 — union → EventLog only, never a socket | **PARTIAL** | DONE on start path (emitters.py:357-398); dice mid-turn still `room_broadcast(union)` (deferred) |
| AC3 — both overlay loops deleted | **PARTIAL** | wssh overlay deleted; dice.py overlay deferred |
| AC4 — fail LOUD on unresolvable seated PC | **DONE** | wssh:1654-1666 + `confrontation.recipient_unresolved` span; tested |
| AC5 — solo Fighter only Fighter beats (start/mid-turn/reconnect) | **PARTIAL** | start + reconnect DONE & tested; mid-turn/flee leg deferred |

**Reconcile verdict:** The manifest is complete and audit-ready. Two of five ACs are fully met, three are partially met — all partials trace to the single, well-documented dice-path deferral. The implemented surface (post-narration start + reconnect — the dominant repro) is correct, tested (full server suite 2290/0), and free of Critical/High findings. **SM should file the follow-up story** ("route dice mid-turn + connect.py resume through the `emit_event(per_recipient_payload=...)` supplier; delete `room_broadcast(union)`; return clear-frame instead of union in the emitter-absent fallbacks") and **surface the partial-AC status to Keith** before/at merge, per the deferral decision raised at spec-check. No additional deviations.