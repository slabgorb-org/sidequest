---
story_id: "126-4"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-4: [BUG] Peer action text not visible during the WAIT phase (ADR-036 violation)

## Story Details
- **ID:** 126-4
- **Jira Key:** (none — personal project)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** sidequest-ui, sidequest-server
- **Branch Strategy:** gitflow (feat/126-4-peer-action-text-wait-visibility)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T16:45:27Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T13:38:42Z | 2026-06-17T13:42:29Z | 3m 47s |
| red | 2026-06-17T13:42:29Z | 2026-06-17T16:19:07Z | 2h 36m |
| green | 2026-06-17T16:19:07Z | 2026-06-17T16:38:37Z | 19m 30s |
| review | 2026-06-17T16:38:37Z | 2026-06-17T16:45:27Z | 6m 50s |
| finish | 2026-06-17T16:45:27Z | - | - |

## Sm Assessment

**Story:** 126-4 — [BUG] Peer action text not visible during the WAIT phase (ADR-036 violation). 3 pts, p2, `tdd` (phased), repos `sidequest-ui` + `sidequest-server`.

**Why this story / why now:** Chosen for oq-4 because it is the only p2 in the backlog with **zero overlap** with the live Fate work in the other clones. 126-7 (determinative 4dF roll) is already in `review` in oq-2; oq-1 is churning Fate-confrontation design (`feat/fate-contest-binding-design`), which is adjacent to 126-1. 126-4 is a multiplayer turn-coordination bug, not Fate — so it can proceed here without colliding with another clone.

**The bug:** During the WAIT phase (everyone submitted, before seal/resolve), a peer's submitted action text is NOT visible to other players — it only appears at reveal. ADR-036's 2026-05-03 amendment requires the opposite: peer action text **is** visible during WAIT (collaborative visibility helps the table coordinate). Sealed/hidden-submission is reserved for the unimplemented PvP path. ~50% intermittent → **suspected race**, likely in the broadcast fan-out (server) or the wait-phase render not applying peers' submitted-but-unsealed text (ui).

**For The Architect (TEA) — red phase:**
- Reproduces only across **multiplayer turns (2 players)** — single-seat won't exercise it. The 06-16 session continued solo, which is why this was never re-verified.
- The doctrine anchor is **ADR-036** (the 2026-05-03 amendment specifically). The regression test should pin that a peer's submitted-but-unsealed action text is **delivered/rendered during WAIT**, not just at reveal.
- It spans both repos: the failing test could live server-side (broadcast fan-out delivers the unsealed peer text) or ui-side (wait-phase render shows it). Pick the layer the root cause lives in; the intermittency (~50%) points at a race, so a deterministic test that forces the ordering is the win.
- Source: sq-playtest-pingpong carryover verify-targets (06-14).

**Judgment checklist:**
- Jira: explicitly skipped — personal project, no Jira (`jira_key` intentionally empty).
- Context: written with concrete ACs (repro + regression test, both citing ADR-036). Technical Approach intentionally deferred to TEA/Dev — correct for a `tdd` bug.

**Routing:** `tdd` (phased) → next phase `red` → next agent **tea** (The Architect).

## TEA Assessment

**Phase:** finish
**Tests Required:** Yes
**Reason:** Bug fix — AC-2 explicitly requires a regression test pinning ADR-036's 2026-05-03 amendment (peer action text visible during WAIT).

**Test Files:**
- `sidequest-ui/src/__tests__/peer-reveal-submitted-only-wait-126-4.test.tsx` — 7 tests (4 guards pass, 3 RED).

**Tests Written:** 7 tests covering AC-1 (repro of the playtest failure) + AC-2 (regression). **Status: RED (3 failing — ready for Dev).** Verified directly via `npx vitest run` (3 failed | 4 passed); did not use the `testing-runner` subagent — see deviation (known session-clobber + hallucinated-output issues on this project).

**Root cause established (red-phase reconnaissance):**
The intermittency is NOT a race in the deterministic logic — it is a **robustness gap**. Per the 2026-06-17 targeted pingpong reproduction, the trigger is *submitted without a preceding `composing`* (fast typist / paste-and-Enter / submit within the 250ms debounce). The peer's action **text has exactly one carrier**: the best-effort `ACTION_REVEAL` frame (`action_reveal.py` broadcasts it WITH text — verified). Every recovery mechanism — the `mergePeerRevealsWithSubmittedStatus` TURN_STATUS merge, `sealedPlayerIds`, seal-reconcile on (re)connect, the round-flush failsafe — restores a peer's **seal status but never their action text**. So:
- **composing-first is resilient** — the composing frame ALSO carries the text and seeds the row early; a lost/late `submitted` frame is masked. (Why turns 1–2 always show text.)
- **submitted-only is fragile** — the single `submitted` frame is the only text carrier; if it is missed (the documented `broadcast.recipient_dropped` "seal frame vanished" churn, `session_room.py:983-990`, or any ordering artifact) there is no recovery — TURN_STATUS supplies the chip, never the text. (Why turn 3 shows the `✓ Sealed` chip with no text.)
- The original "~50% intermittent" was the coin-flip on whether the submitter paused while typing.

I proved the deterministic UI+server logic is correct: a faithful App-mirroring harness (real `usePeerReveals` + `mergePeerRevealsWithSubmittedStatus` + `PeerRevealList`, wired exactly as App.tsx, mounted under `<StrictMode>` as production does) renders a submitted-only frame's text when the frame lands — and across multiple turns. The 4 passing guards pin that. The 3 RED tests pin the missing **recovery**: the WAIT strip / merge must surface a sealed peer's action text from the authoritative seal roster when no best-effort reveal row exists.

**Suggested fix shape (Dev — not prescriptive):** the server already buffers each sealed player's action in `SessionRoom.pending_actions` (`PendingAction.action`). Thread that text onto the authoritative seal the server already broadcasts (`TurnStatusPayload` roster `entries`), extend the UI `TurnStatusEntry` with the text, have `App.tsx` (handleMessage, ~1078-1088) capture it, and have `mergePeerRevealsWithSubmittedStatus` synthesize a text-bearing row when the best-effort reveal is absent. This makes peer text *reliable* (ADR-036), not best-effort-only. ADR-036 collaborative-visibility doctrine permits showing the text (it is the player's own input, visible to the table during WAIT).

### Rule Coverage

| Rule (lang-review TS/React) | Test | Status |
|------|------|--------|
| #4 null/undefined — no falsy/blank row from a text-less seal | `[guard] does NOT synthesize a blank row when the sealed entry carries no text` | passing (guard) |
| Test quality — meaningful assertions, no vacuous | self-check: all 7 assert specific rendered text / row fields | passing |
| Wiring — real hook+merge+component, App-mirrored, under StrictMode | harness drives the production units exactly as App wires them | covered |

**Rules checked:** Production-code rules (#1 type-safety escapes, #2 generics, #3 enums) apply to Dev's GREEN implementation, not to this test file — flagged for Dev's self-review. The test file uses one documented cast (`as TurnStatusEntry & { action }`) to represent the wire field the fix adds; no `as any`, no `||`-on-falsy, no vacuous assertions.
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Agent Smith) for implementation (GREEN).

## Dev Assessment

**Implementation Complete:** Yes
**Approach:** Implemented exactly the recovery channel The Architect pinned — the
peer's sealed action text rides the *authoritative* TURN_STATUS roster so the
WAIT strip recovers it when the single best-effort ACTION_REVEAL frame is missed.
Full pipeline (not merge-only — a merge-only change would be half-wired, the
merge would never receive `action` in production):

**Files Changed:**
- `sidequest-ui/src/types/payloads.ts` — `TurnStatusEntry.action?` (optional wire field).
- `sidequest-ui/src/lib/turnStatusDerivation.ts` — `mergePeerRevealsWithSubmittedStatus` synthesizes a text-bearing display row from a sealed roster entry that carries text when no ACTION_REVEAL reveal row exists; never a blank row; existing status-upgrade path unchanged.
- `sidequest-ui/src/App.tsx` — batch-entries handler captures `action` into `turnStatusEntries`.
- `sidequest-server/sidequest/protocol/messages.py` — `TurnStatusEntry.action: str | None = None` (None elided by ProtocolBase).
- `sidequest-server/sidequest/server/turn_status_roster.py` — `build_turn_status_roster` / `build_seal_reconcile_roster` accept the pending-action texts and stamp `action`; `project_all_submitted` preserves it (model_copy status-only).
- `sidequest-server/sidequest/server/session_room.py` — `pending_action_texts()` read-only snapshot of the buffer.
- `sidequest-server/sidequest/handlers/player_action.py` — active + submitted broadcasts pass the texts; OTEL `turn_status{submitted}` gains `roster_action_text_count` (count only; text never rides telemetry — GM-panel lie-detector for the recovery channel).
- `sidequest-server/sidequest/handlers/connect.py` — seal-reconcile-on-connect passes the texts so a mid-WAIT reconnector recovers text too.
- `sidequest-server/tests/server/test_turn_status_roster_carries_sealed_text.py` — server wiring test (TEA's tests are UI-only; this covers the server half per "Every Test Suite Needs a Wiring Test").

**Doctrine:** Showing the text is ADR-036 collaborative visibility (the player's own submitted action, visible to the table during WAIT) — not a perception-firewall (ADR-104/105) violation; ACTION_REVEAL already broadcasts the same text.

**Tests:**
- UI: TEA's 7 (4 guards + 3 RED → GREEN); full UI suite **2406/2406 pass**.
- Server: 2 new (unit + wiring) pass; broad slices **299** (connect/session_room/protocol/turn_status/roster/barrier/multiplayer) + **131** (turn_status/roster/reveal/seal/player_action) pass. The one slice failure — `test_sealed_letter_dispatch_integration::test_legacy_beat_selection_path_still_works` (`assert 'strike' in set()`) — is **pre-existing** (fails identically with my changes stashed; it is combat beat-selection, disjoint from turn-status).
- Lint/types: UI eslint 0 errors; server ruff clean; my changed lines add **zero** pyright errors (verified by stash-compare on the two flagged pre-existing errors).

**Branch:** `feat/126-4-peer-action-text-wait-visibility` (pushed — both `sidequest-ui` and `sidequest-server`).

**Handoff:** To verify phase (The Architect / TEA).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (all attributable checks pass) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [EDGE] observations) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — covered by Reviewer (see [RULE] + Rule Compliance) |

**All received:** Yes (2 enabled subagents returned clean; 7 disabled via `workflow.reviewer_subagents` and covered by my own analysis)
**Total findings:** 0 confirmed (blocking), 0 dismissed, 2 deferred (pre-existing, not 126-4); 3 LOW/MINOR non-blocking observations noted

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player submits an action → `sanitize_player_text()` (player_action.py:361) → `record_pending_action()` buffers the *sanitized* text in `SessionRoom._pending_actions` (session_room.py:769) → `pending_action_texts()` snapshot → `build_turn_status_roster(..., texts)` stamps `TurnStatusEntry.action` (turn_status_roster.py:61) → `TurnStatusPayload.entries` → `room.broadcast()` to all peers → UI `App.tsx` batch-entries handler captures `e.action` → `mergePeerRevealsWithSubmittedStatus` synthesizes a display row when no ACTION_REVEAL row exists → `PeerRevealList` renders `{r.action}` as an auto-escaped JSX text node (PeerRevealList.tsx:75). Safe end-to-end: text is sanitized at the entry boundary, never reaches a narrator prompt, and is the same text ADR-036 already makes peer-visible.

**Observations (10):**
- `[SEC]` **[VERIFIED]** No new prompt-injection surface. `TurnStatusEntry.action` is sourced only from `_pending_actions`, written from the post-`sanitize_player_text()` value (player_action.py:361→769). `TurnStatusEntry` has zero readers in `sidequest/agents/` — it never enters a narrator/LLM prompt. Complies with ADR-047. Evidence: security subagent trace + grep (0 matches in agents/).
- `[SEC]` **[VERIFIED]** No perception-firewall (ADR-104/105) regression. The roster carries the player's *own* submitted action — the identical text `ACTION_REVEAL` already broadcasts to all peers under ADR-036's 2026-05-03 amendment (peer action text IS visible during WAIT; sealed-visibility/PvP mode is unimplemented). No new private-info category; same `room.broadcast()` fan-out. OTEL `roster_action_text_count` (player_action.py:852) is a count, not content. React text-node render is auto-escaped.
- `[EDGE]` **[VERIFIED]** Aside actions never reach `pending_actions`: an aside branches at player_action.py:373 into the `aside_resolver` and returns early, *before* `record_pending_action` (~769). So the synthesized row's hard-coded `aside: false` is always correct for a sealed turn action. Empty action → `texts.get(pid) or None` → `None` → elided; the UI guard `entry.action && entry.action.length > 0` mirrors it (no blank row). A `pending_actions` pid absent from `playing_player_ids()` is simply not stamped (roster iterates the playing ids) — no crash, no leak.
- `[EDGE]` **[VERIFIED]** Terminal-broadcast preservation: `build_turn_status_roster` stamps `action` from `pending_action_texts` keyed *independently* of the runtime `_submitted` set, and `project_all_submitted` uses `model_copy(update={"status":"submitted"})` (turn_status_roster.py:129) which preserves `action`. So the seal text survives the barrier-fired terminal broadcast even after `_submitted` is cleared (pending_actions is not drained until dispatch, after the broadcast).
- `[TYPE]` **[VERIFIED]** `TurnStatusEntry.action: str | None = None` (messages.py:599) / `action?: string` (payloads.ts) is an additive optional field; `ProtocolBase` elides `None` on the wire (pending players omit it). UI capture `e.action as string | undefined` (App.tsx) matches the established `e.player_id as string` cast pattern two lines up — no `as any`, no `as unknown as T` double-cast.
- `[SILENT]` **[VERIFIED]** No swallowed errors introduced. `pending_action_texts()` is a pure read under `self._lock`; `pending_action_texts or {}` and `texts.get(pid) or None` are intentional null-coalescing (lang-review py #2 mutable-default and #4 null-handling compliant — `None` default with in-body `or {}`). No new `try/except`.
- `[TEST]` `[LOW]` (analyzer disabled — my review): TEA's 7 UI tests (4 guards + 3 RED→GREEN) and Dev's 2 server tests (unit + wiring) all assert specific rendered text / roster fields — no vacuous assertions, no `assert(true)`. **Coverage gap (non-blocking):** the `active_roster` text-carry, the `connect.py` reconcile text-carry, and `project_all_submitted` action-preservation are correct-by-construction (they reuse the unit-tested `build_turn_status_roster`) but not directly asserted. Acceptable for a 3-pt bug; noted for future hardening.
- `[DOC]` **[VERIFIED]** Comments/docstrings match code: `TurnStatusEntry.action` (messages.py:599), `pending_action_texts()` (session_room.py:783), the merge JSDoc and the App.tsx capture comment all describe the implemented behavior accurately. No stale or misleading comments introduced.
- `[SIMPLE]` **[VERIFIED]** The `ensureMerged()` helper (turnStatusDerivation.ts) is a sound extraction shared by both loops and preserves the identity-stability contract (returns `reveals` unchanged when nothing synthesizes). No over-engineering, no dead code; the server change reuses the existing buffer (no new state).
- `[RULE]` **[VERIFIED]** Exhaustive lang-review pass (rule-checker disabled) — see `### Rule Compliance`. All applicable Python (#2/#3/#4) and TypeScript (#1/#4) checks pass; CLAUDE.md OTEL principle satisfied (count-only span added); "Every Test Suite Needs a Wiring Test" satisfied (server wiring test added); No-Silent-Fallbacks honored.

### Rule Compliance

| Rule (source) | Instances checked | Verdict |
|---|---|---|
| lang-review py #2 — mutable default args | `build_turn_status_roster`, `build_seal_reconcile_roster` (`pending_action_texts=None` + in-body `or {}`) | COMPLIANT — None default, not `={}` |
| lang-review py #3 — type annotations at boundaries | `pending_action_texts: Mapping[str,str] \| None`, `pending_action_texts() -> dict[str,str]`, `action: str \| None` | COMPLIANT — all annotated |
| lang-review py #4 — logging never logs sensitive data | OTEL `roster_action_text_count` (count int only) | COMPLIANT — text never emitted |
| lang-review ts #1 — type-safety escapes (`as any`, double-cast) | `e.action as string \| undefined` (App.tsx) | COMPLIANT — single cast, matches sibling `e.player_id as string` |
| lang-review ts #4 — `\|\|`/falsy null-handling | `entry.action && entry.action.length > 0`; `texts.get(pid) or None` | COMPLIANT — truthy guard intentional (empty → no row) |
| CLAUDE.md OTEL Observability — every subsystem fix emits a span | `roster_action_text_count` on `turn_status{submitted}` | COMPLIANT — GM-panel lie-detector for the recovery channel |
| ADR-047 sanitization | text sanitized at player_action.py:361 before buffering | COMPLIANT |
| ADR-036 / ADR-104-105 visibility vs firewall | roster carries the same text ACTION_REVEAL already shows | COMPLIANT — sanctioned visibility |
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | `test_turn_status_roster_carries_sealed_text.py` (real submission → broadcast roster) | COMPLIANT |
| CLAUDE.md "No half-wired features" | full server→App→merge pipeline + both repos' tests green | COMPLIANT |

### Devil's Advocate

*Argue this is broken.* **Double rows?** If both the best-effort ACTION_REVEAL frame and the roster arrive, does the peer see two rows for the same player? No — synthesis is gated on `!reveals.has(player_id)`, and the merge `useMemo` recomputes each render; the instant the real reveal lands, `reveals.has(pid)` is true, synthesis is skipped, and the real row (with its true seq/round/aside) supersedes the synthesized stand-in. Single row, real data wins. **Stale text?** `record_pending_action` is last-write-wins, so a re-submit updates the buffer and the next roster carries the latest — no stale bleed. **Cross-round bleed?** `pending_actions` is drained at dispatch (`drain_pending_actions`); after resolution `pending_action_texts()` returns `{}`, and the UI `clear()` fires on TURN_STATUS{resolved} — so the synthesized row exists only while the player is genuinely sealed this round. **Race with the round counter?** The synthesized row carries `round: 0`, but it lives only in the *display-only* merged map (recomputed each render) and never enters `usePeerReveals`'s reducer (which only ingests ACTION_REVEAL) nor the 71-12 snapshot accumulator (which captures from the RAW `peerReveals.reveals`, not the merged map). So `round: 0` is inert — it cannot corrupt persistence or the round-flush race. **Malicious client?** A client cannot fabricate a peer's seal: TURN_STATUS is server→client only, the server builds the roster from its own `_submitted`/`pending_actions`, and the action is the player's *own* sanitized input — no privilege escalation, no injection (auto-escaped text node). **Huge input?** The text is carried on the roster in addition to ACTION_REVEAL — a minor bandwidth doubling of already-broadcast text, not a new DoS vector. **Reconnect after a process reload?** `pending_actions` is runtime-only, so a post-reload reconnect recovers no text — but that exactly matches the existing `_submitted` seal-status caveat, is documented, and is out of scope. I could not find a break. The edges are handled.

**Error handling:** failure paths unchanged — the new accessor is a pure read under lock; roster construction skips blank ids (pre-existing guard); the broadcast path is the existing fan-out with its `broadcast.recipient_dropped` loud-fail instrumentation. Null/empty action → elided, never a blank row.

**Pattern observed:** authoritative-channel recovery for a best-effort signal — the roster (already the canonical denominator per ADR-036) now also carries the recovery payload, consistent with the existing `sealedPlayerIds`/seal-reconcile status-recovery machinery. Good pattern at `turn_status_roster.py:61` + `turnStatusDerivation.ts` loop (2).

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup entry.

### TEA (test design)
- **Gap** (non-blocking): The authoritative seal channel carries no action text — a peer's submitted action text has a single carrier (best-effort `ACTION_REVEAL`), so a missed frame is unrecoverable while the seal *status* is reliably recovered. Affects `sidequest-server` (the `TurnStatusPayload` roster / seal broadcast should include the submitter's action text, available in `SessionRoom.pending_actions`), `sidequest-ui/src/types/payloads.ts` (`TurnStatusEntry` needs the text field), `sidequest-ui/src/lib/turnStatusDerivation.ts` (`mergePeerRevealsWithSubmittedStatus` must synthesize a text row), and `sidequest-ui/src/App.tsx` (~1078-1088 must capture the seal text into `turnStatusEntries`). *Found by TEA during test design.*
- **Improvement** (non-blocking): Pre-existing build break on `develop` — `sidequest-ui/src/App.tsx:2010` `send(makeFateThrowMessage(...))` fails `tsc -b` (and `npm run build`) because `FateThrowMessage` (`payloads.ts:736`) was never added to the `GameMessage` discriminated union (`types/protocol.ts`), introduced by 126-7 / ui #413. Not 126-4 (App.tsx is byte-identical to `origin/develop`), but it will trip any build/`pf check` gate during GREEN. Affects `sidequest-ui`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): CONFIRMED the pre-existing `FateThrowMessage` build break (TEA's finding above) is still live after my change — `npx tsc -b` reports exactly one error, `src/App.tsx` `FateThrowMessage` not in `GameMessage`, and my edited lines add none. Left untouched: it is 126-7's (#413, in review in oq-2), and fixing another story's union here risks a merge collision. If the verify/review build gate runs `tsc -b`, it will fail on this one pre-existing line — not 126-4. Affects `sidequest-ui/src/types/protocol.ts` (add `FateThrowMessage` to the `GameMessage` union). *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): Independently confirmed the pre-existing `FateThrowMessage`/`GameMessage` `tsc -b` break (TEA + Dev findings above) is the ONLY UI build error and is unrelated to 126-4 (the 4-line App.tsx diff is the batch-entries `action` capture). It is 126-7's (#413). SM should know that if a finish-time build/`pf check` gate runs `tsc -b`, the failure is not a 126-4 regression. Affects `sidequest-ui/src/types/protocol.ts` (add `FateThrowMessage` to the `GameMessage` union). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Test-coverage opportunity — the `active_roster` text-carry, the `connect.py` seal-reconcile text-carry, and `project_all_submitted` action-preservation are correct-by-construction (they reuse the unit-tested `build_turn_status_roster`) but are not directly asserted. Optional future hardening; does not block. Affects `sidequest-server/tests/server/`. *Found by Reviewer during code review.*
- No blocking upstream findings during code review.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

None recorded at setup entry.

### TEA (test design)
- **RED pins recovery-via-authoritative-seal, not best-effort delivery-guarantee**
  - Spec source: context-story-126-4.md, AC-2
  - Spec text: "a peer's submitted-but-unsealed action text is delivered/rendered during WAIT, per ADR-036's 2026-05-03 amendment"
  - Implementation: The RED tests assert the WAIT strip / `mergePeerRevealsWithSubmittedStatus` **recovers** a sealed peer's action text from the authoritative TURN_STATUS seal roster when the best-effort `ACTION_REVEAL` frame is missed — rather than asserting guaranteed delivery of that single frame.
  - Rationale: The deterministic UI+server logic is provably correct — a faithful App-mirroring harness (real units, under `<StrictMode>`) renders submitted-only text when the frame lands (4 passing guards). The bug is a robustness gap: the action text has exactly one carrier and no authoritative recovery path. Recovery via the authoritative channel is the architecturally-consistent, deterministically-testable fix; "guarantee best-effort delivery" cannot be reproduced deterministically and would not address the documented stable-session "seal frame vanished" drop.
  - Severity: minor
  - Forward impact: Fix spans both repos (server supplies the seal text from `pending_actions`; ui extends `TurnStatusEntry` + merge synthesis + App capture). If Dev pursues a delivery-guarantee approach instead, these RED tests should be re-scoped with Reviewer.
- **RED verified by direct `vitest` run, not the `testing-runner` subagent**
  - Spec source: agent-behavior guide — "Tests: Use testing-runner subagent, never run directly."
  - Spec text: spawn `testing-runner` to verify RED state
  - Implementation: Verified RED directly with `npx vitest run` (deterministic: 3 failed | 4 passed).
  - Rationale: Project-specific prior learnings — `testing-runner` clobbers the untracked `.session/{story}-session.md` (no git recovery) and hallucinates per-test prose including false GREEN. Direct, reproducible output is the stronger evidence here.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Implemented the full server→App→merge pipeline, beyond TEA's UI-only tests**
  - Spec source: 126-4-session.md, TEA Assessment (test set) + epic wiring rules (CLAUDE.md "No half-wired features", "Verify Wiring, Not Just Existence")
  - Spec text: TEA's 3 RED tests are UI-only and pass with a `mergePeerRevealsWithSubmittedStatus`-only change
  - Implementation: Also changed the server (`TurnStatusEntry.action`, roster builders, `pending_action_texts()`, the active/submitted/reconcile broadcasts, OTEL) and `App.tsx`'s batch-entries capture, and added a server-side wiring test. A merge-only change would pass TEA's tests while leaving the feature dead in production (nothing populates `action`).
  - Rationale: The recovery channel only works end-to-end if the server supplies the text and App threads it to the merge. This is the wiring TEA flagged as a Gap, not scope creep.
  - Severity: minor
  - Forward impact: none — additive optional field; pending players omit it; existing roster/merge behavior unchanged.
- **Recovery source is the seal roster `action` field (TEA's suggested shape), confirmed sound**
  - Spec source: 126-4-session.md, TEA deviation "RED pins recovery-via-authoritative-seal"
  - Spec text: "server supplies the seal text from `pending_actions`; ui extends `TurnStatusEntry` + merge synthesis + App capture"
  - Implementation: Followed exactly — the text is sourced from `SessionRoom.pending_actions` (no new buffer), carried only for sealed players, and the synthesized display row uses default `aside=false, seq=0, round=0` (display-only; never snapshot-captured into the canonical `peerReveals.reveals`, preserving the 71-12 raw-capture guard).
  - Rationale: Reuses existing buffered data; no delivery-guarantee machinery; consistent with ADR-036 collaborative visibility.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA: RED pins recovery-via-authoritative-seal, not delivery-guarantee** → ✓ ACCEPTED by Reviewer: sound and necessary — the deterministic logic is provably correct (4 guards pass under StrictMode), so the only testable fix is authoritative recovery; a delivery-guarantee approach is not deterministically reproducible and would not address the documented stable-session "seal frame vanished" drop.
- **TEA: RED verified by direct `vitest`, not `testing-runner`** → ✓ ACCEPTED by Reviewer: agrees with author reasoning — the project-specific `testing-runner` clobber/hallucination hazard is real; direct reproducible output is stronger evidence and preflight independently re-ran the suites GREEN.
- **Dev: implemented the full server→App→merge pipeline beyond TEA's UI-only tests** → ✓ ACCEPTED by Reviewer: this is required wiring, not scope creep — a merge-only change would pass TEA's UI tests while leaving the feature dead in production (nothing populates `action`). Dev added a server wiring test to cover the new half; full UI suite (2406) + server slices green.
- **Dev: recovery source is the seal-roster `action` field; synthesized row is display-only** → ✓ ACCEPTED by Reviewer: verified — the synthesized row (round=0/seq=0/aside=false) lives only in the display-only merged map, never enters `usePeerReveals`'s reducer nor the 71-12 raw-reveals snapshot, so it cannot corrupt persistence or the round race; `aside: false` is always correct because asides branch off before `pending_actions`.
- No UNDOCUMENTED spec deviations found — server+UI changes match the ACs (ADR-036 WAIT-phase visibility) and the TEA-pinned approach exactly.