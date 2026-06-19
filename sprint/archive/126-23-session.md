---
story_id: "126-23"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-23: [BUG] OTEL Inspector Live view not partitioned by session_id — renders the last-emitting session, unusable during concurrent runs

## Story Details
- **ID:** 126-23
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Repos:** ui,server
**Phase Started:** 2026-06-19T17:31:19Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T16:57:01Z | 2026-06-19T16:59:17Z | 2m 16s |
| red | 2026-06-19T16:59:17Z | 2026-06-19T17:10:53Z | 11m 36s |
| green | 2026-06-19T17:10:53Z | 2026-06-19T17:22:25Z | 11m 32s |
| review | 2026-06-19T17:22:25Z | 2026-06-19T17:31:19Z | 8m 54s |
| finish | 2026-06-19T17:31:19Z | - | - |

## Sm Assessment

**Story:** 126-23 — OTEL Inspector Live view not partitioned by `session_id`. The dashboard's Live stream follows whichever session last emitted instead of the operator-selected one, so under concurrent sessions (a playtest + a headless test) the Live header jumps to the wrong session, the Timeline stalls at "Waiting for first turn…", and the driven session's spans are never viewable. This makes the GM-panel **lie-detector** — the project's only defense against the narrator winging it — unusable during concurrent runs, which are routine for headless tests.

**Scope / repos:** Two surfaces, both off `develop`.
- **server** — the WatcherHub broadcasts *all* sessions on `/ws/watcher` with no per-session filtering. The consumer needs a way to subscribe to / partition by `session_id`. Touch points: `sidequest-server/sidequest/server/` (watcher) + `sidequest-server/sidequest/telemetry/` (WatcherHub). Doctrine: ADR-132 (per-session ContextVar isolation), ADR-090 (OTEL dashboard restoration), ADR-031/103.
- **ui** — `sidequest-ui/src/components/Dashboard/` Live view must filter the incoming span stream to the *selected* `session_id` (a session dropdown already exists) rather than following the last emitter, and must surface a selected session's already-emitted turns rather than only spans seen after connect.

**Workflow:** tdd. RED (Argus) should prove three failures before any fix: (a) a mixed multi-session stream renders only the selected session in Live; (b) selecting a session that emitted *before* the panel connected still shows its turns (no stuck "Waiting for first turn…"); (c) server-side, the watcher stream is filterable/partitionable by `session_id`. Per the OTEL principle, the fix must preserve/extend span coverage — fitting, since this *is* an observability fix.

**Risk / notes:** No Jira (pf-tracked). No content/daemon involvement. Repos were brought current to `develop` at setup. The fix spans the server→ui seam, so RED must exercise both sides; a pure-UI test that mocks a perfectly-partitioned stream would miss the server half.

**Verdict:** Ready for RED. Handing off to Argus Panoptes.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (12 new tests failing — ready for Hephaestus / Dev)

**Root cause (confirmed by reading the code, not just the report):**
- *UI:* `useLiveSource` already partitions its returned view by `session_slug`, but it scopes to `activeSlug`, which is **auto-derived** from `debugState` sorted by `last_activity_ts` (`useLiveSource.ts:322-330`). There is **no operator-selection API** — under ≥2 concurrent sessions the view always follows the *last-active* session, and `SessionPicker` only offers "Live" (one auto slug) vs saved sessions. That is bug symptom (1) (wrong header) and the dominant cause of (2)/(3).
- *Server:* `session_slug` stamping + replay already work (`watcher_hub.py`, tested in `test_watcher_session_slug.py` / `test_watcher_replay.py`). The genuine server defect is the **single shared `deque(maxlen=2000)`** replay buffer (`watcher_hub.py:97`): a noisy concurrent session evicts a quiet driven session's buffered turns before the operator connects → "TURNS 0 / Waiting for first turn…". This is the concurrency tail of symptom (2).

**Test Files:**
- `sidequest-ui/src/components/Dashboard/__tests__/useLiveSource-session-select.test.tsx` — 5 tests (1 guard + 4 RED). Pins the hook contract: `selectSession(slug|null)`, `activeSlug` honors the pin, the view follows the SELECTED session and a later event from another session does **not** steal it back, selecting a session surfaces its already-accumulated turns, `selectSession(null)` returns to auto-follow, and `liveSessions: string[]` enumerates known live slugs.
- `sidequest-ui/src/components/Dashboard/__tests__/SessionPicker-live-select.test.tsx` — 2 RED tests (operator-facing wiring). Additive optional props `liveSessions: string[]` + `onSelectLiveSession(slug)`; the picker offers one option per live session and routes the choice.
- `sidequest-server/tests/telemetry/test_watcher_session_replay_retention.py` — 3 RED tests. Per-session replay retention: a quiet driven session's turns survive a noisy neighbor's flood (strict-after AND interleaved), and session-less infra markers stay global.

**Tests Written:** 12 failing (+1 guard passing) covering all 3 ACs that admit behavioral tests.

### Rule Coverage

| Rule (lang-review) | Test(s) | Status |
|--------------------|---------|--------|
| TS #4 null/undefined — auto vs pinned slug, `?? `not `\|\|` | `selectSession(null) clears the pin…` (null is a valid pin-clear, distinct from "no slug") | failing |
| TS #6 React/JSX — selection state must not auto-follow-steal | `selectSession pins the DRIVEN session over the last-emitting one` (asserts a later event does not steal the view) | failing |
| TS #8 test quality — every test asserts a specific value, no `as any` | all UI tests assert concrete slugs/lengths | guard passing / RED |
| PY #6 test quality — no vacuous assertions | server tests assert exact retained turn-id lists | failing |
| PY #1/#9 async — retention must not silently drop session events | `test_session_less_infra_events_are_retained_globally` (loud invariant, not a silent fold) | failing |

**Rules checked:** UI 3 of 13, server 2 of 13 applicable (this is a state-scoping + buffer-retention change, not an input-validation/serialization surface — most lang-review checks N/A).
**Self-check:** 0 vacuous tests written; every assertion checks a concrete value (slug, length, turn-id list, handler arg).

**Wiring test present (per CLAUDE.md "Every Test Suite Needs a Wiring Test"):** `SessionPicker-live-select.test.tsx` proves the operator-facing surface invokes the hook's selection API — the feature is reachable from the operator, not just unit-correct in isolation. **Dev must also wire `live.liveSessions` + `live.selectSession` from `DashboardApp` into `SessionPicker`** (the one glue line the picker test brackets but cannot itself render).

**Handoff:** To Hephaestus the Smith (Dev) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes (code ACs 1 & 2 met; AC3 docs caveat blocked — see findings)
**Tests:** 56/56 passing (GREEN) — 12 new + 44 existing watcher/Dashboard regression tests, 0 failures.

**Files Changed:**
- *UI — `sidequest-ui` (branch `feat/126-23-otel-live-session-partition`, pushed):*
  - `src/components/Dashboard/source/useLiveSource.ts` — added operator selection: `selectSession(slug|null)` (a `useState` pin), `liveSessions: string[]` (debug-state sessions ∪ slug-tagged event sessions), and `activeSlug = pinnedSlug ?? autoSlug`. The existing per-session scoping (`inActiveSession`) now follows the effective slug, so a pinned session is never stolen by a later-emitting one.
  - `src/components/Dashboard/SessionPicker.tsx` — when live sessions exist, renders a "Live sessions" optgroup with one option per session (`live:<slug>`) plus an "auto-follow newest" option; routes `live:<slug>` → `onSelectLiveSession`. Additive optional props (existing single-session callers unaffected).
  - `src/components/Dashboard/DashboardApp.tsx` — wires `live.liveSessions` + `live.selectSession` into the picker; auto-follow clears the pin.
- *Server — `sidequest-server` (same branch, pushed):*
  - `sidequest/telemetry/watcher_hub.py` — replaced the single shared `deque(maxlen=2000)` replay buffer with **per-session ring buffers** keyed by `session_slug`, each bounded (`_PER_SESSION_MAXLEN`), tagged with a monotonic `_seq` so `replay` merges back to global publish order. A noisy session can no longer evict a quiet one's history. Bucket count capped (`_MAX_SESSION_BUCKETS`, LRU, never the global `None` bucket) to bound memory.

**Verification:** `npx tsc --noEmit` → 0 errors; `ruff check` clean; `ruff format` applied to the two changed server files only (per the known full-format drift). No new OTEL spans needed — the UI change is session-selection UI state (cosmetic per UI CLAUDE.md), and the server change is to the watcher infrastructure itself, whose liveness is already exposed via `stats().buffered` + the `watcher.replay_end` event.

**Handoff:** To Hermes Psychopompos (Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (133 UI + 37 server tests pass; lint/type/format clean; 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 10 | confirmed 5 (non-blocking), dismissed 4, downgraded 1 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 5 (all LOW/info, 0 exploitable) | confirmed 0 blocking, all dismissed as non-issues with rationale |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 5 confirmed (all MEDIUM/LOW, non-blocking), 8 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A tight, well-scoped fix that resolves the bug at its true root on both sides of the seam. Preflight is GREEN (133 UI Dashboard + 37 server watcher tests pass; `tsc` 0 errors; `ruff` clean; 0 code smells). No Critical or High issues. The confirmed findings are MEDIUM/LOW usability edges and defensive robustness gaps — all non-blocking, all recoverable, captured as follow-ups.

**Data flow traced:** operator picks a session in `SessionPicker` (`live:<slug>` option) → `DashboardApp.onSelectLiveSession` → `live.selectSession(slug)` → `useLiveSource` `setPinnedSlug` → `activeSlug = pinnedSlug ?? autoSlug` → existing `inActiveSession` scoping filters `turns`/`allEvents`/`componentMap` to the pinned slug → Timeline/header/tabs render only that session. Auto-follow (`onSelectLive` → `selectSession(null)`) restores `autoSlug`. Safe: `session_slug` is server-controlled (ContextVar bound at `connect.py:398` from a DB-validated game_slug), never client-injectable; React escapes the `live:<slug>` option value/text ([SEC] confirmed, CWE-79 clean).

**Server data flow:** every broadcast event is bucketed by `session_slug` into a per-session `deque(maxlen=2000)`, tagged with a monotonic `_seq`; `replay` merges all buckets and re-sorts by `_seq` → global publish order preserved, but a noisy session can no longer evict a quiet one's turns. Verified the eviction invariant myself: `_append_to_session_buffer` creates-then-immediately-appends, so named buckets are always non-empty, so `_evict_session_bucket_if_needed` always finds a candidate when the cap is reached — the "cap exceeded by 1" edge is **not reachable**.

**Pattern observed:** the fix correctly *extends* the existing 2026-06-16 per-session scoping (`inActiveSession`/`activeSlug`) rather than rebuilding it — `activeSlug` becomes the effective slug and every downstream `useMemo` inherits the selection for free (`useLiveSource.ts:354`). Additive, back-compatible props on `SessionPicker` (`SessionPicker.tsx:14-17`) leave the existing single-session caller untouched (proven by the 4 pre-existing `SessionPicker.test.tsx` tests still passing).

**Error handling:** `replay` remains best-effort (partial count on `send_json` failure, `noqa: BLE001`, unchanged); per-session/None-infra retention is loud-by-design lossy (ADR-090), not a silent fallback. `selectSession(null)` is an explicit pin-clear, not a fallback. No swallowed errors introduced.

### Findings (all non-blocking)

- **[EDGE][MEDIUM] Stale pin → blank view** (`useLiveSource.ts:354`): if the operator pins a session that later leaves both `debugState` and `allEvents`, `activeSlug` stays on the dead slug and the view silently blanks with no "pinned session ended" feedback. Mitigated in the common case because `allEvents` accumulates for the hook's lifetime (the pinned session's history persists), and the operator can re-select auto-follow at any time. Recommend a follow-up guard that auto-clears or flags a pin not present in `liveSessions`.
- **[EDGE][LOW] `clear()` does not reset `pinnedSlug`** (`useLiveSource.ts` CLEAR path): debatable design (some operators want the pin to survive a clear). Non-blocking; flag for product decision.
- **[EDGE/SEC][LOW] `liveSessions` conflates live and ended sessions** (`useLiveSource.ts:344`): once a slug appears in `allEvents` it stays pickable for the hook's lifetime; ended sessions remain in the picker with no live/historical distinction. Corroborated by [SEC] (suggests filtering to `debugState` slugs). Usability, not security.
- **[EDGE][LOW] Empty-string `session_slug` mismatch** (`watcher_hub.py:189`): the server buckets `''` as a named session while the UI (`useLiveSource.ts:352`) excludes `''` as session-less. Verified **not currently reachable** (`bind_session_slug` only ever receives a validated slug or `None`). A one-line `or None` normalization would align the two defensively. Non-blocking.
- **[EDGE][LOW] `onSelectLiveSession` optional → silent no-op for a future misuse** (`SessionPicker.tsx:17`): if a future caller passes `liveSessions` without the handler, selection silently does nothing. The sole current caller (`DashboardApp`) wires it; the optionality preserves back-compat. Could be tightened with a discriminated prop union. Non-blocking.

**Dismissed (with rationale):** [EDGE] eviction-cap-exceeded — not reachable (named buckets always non-empty post-append; `None` is a single key). [EDGE] slug containing `:` double-prefix — slugs are date-world-hash, server-generated, DB-validated; cannot contain `:`. [EDGE] `SessionPicker` value-fallback path — self-resolved by the subagent (handled). [EDGE] `stats()` torn read — downgraded LOW: the counters were always read outside the lock (pre-existing); `buffered` is an advisory stat. [SEC] all 5 — `_seq` is an unbounded Python int (no overflow), worst-case memory ~125–500 MB is bounded by `_MAX_SESSION_BUCKETS=64` and acceptable for an operator-only dev server, `session_slug` not client-controllable, XSS clean.

**Disabled specialists:** [SILENT], [TEST], [DOC], [TYPE], [SIMPLE], [RULE] subagents are disabled via `workflow.reviewer_subagents`. I covered their domains myself: [SILENT] no swallowed errors introduced (replay best-effort is by-design, ADR-090); [TEST] the 12 new tests assert concrete values (turn-id lists, slugs, lengths, handler args) — no vacuous assertions, and a wiring test (`SessionPicker-live-select.test.tsx`) proves operator-reachability; [DOC] the new comments accurately describe the per-session retention and pin semantics (the stale 126-16 "OTEL-INSPECTOR" comment is correctly preserved as the layer being extended); [TYPE] no `as any`/unsafe casts, `pinnedSlug ?? autoSlug` and `string | null` typing are sound, `tsc` 0 errors; [SIMPLE] the change reuses the existing scoping path rather than duplicating it — appropriately minimal; [RULE] see Rule Compliance below.

### Rule Compliance

**TypeScript lang-review (changed `.ts`/`.tsx`):**
- #1 type-safety escapes — no `as any`, `as unknown as`, `@ts-ignore`, or non-null assertions on nullable in production code. ✓
- #4 null/undefined — `pinnedSlug ?? autoSlug` and `selectedSlug ?? ""` use `??` (not `||`); `e.session_slug != null && !== ""` guard before `Set.add`. ✓
- #6 React/JSX — `useState` pin, `useMemo`/`useCallback` deps correct (`liveSessions` deps `[debugState, allEvents]`; `selectSession` deps `[]` stable); per-session option `key={slug}` is a stable id (not index). ✓
- #8 test quality — no `as any` in tests; mocks (`useWatcherSocket`, `fetch`) match real signatures. ✓
- #10 input validation — `session_slug` is server-controlled, not user input; option values are React-escaped. ✓

**Python lang-review (changed `.py`):**
- #1 silent exceptions — only the pre-existing `except Exception` in `replay` (best-effort, `noqa: BLE001`, returns partial count); no new bare/swallowed excepts. ✓
- #3 type annotations — `_append_to_session_buffer(self, slug: str | None, safe_event: dict[str, Any]) -> None` and `_evict_session_bucket_if_needed(self) -> None` fully annotated. ✓
- #6 test quality — retention tests assert exact retained turn-id lists (`[0,1,2]`, `[0,1,2,3]`) and infra count (`== 1`), not truthy checks. ✓
- #9 async — `_append`/`_evict` are sync helpers called under the held `_lock`; `replay` correctly snapshots under lock then sorts/sends outside it on an immutable copy. ✓

### Devil's Advocate

Argue this is broken. **Concurrency:** `replay` releases `self._lock` after building `merged`, then sorts and sends outside it — could a concurrent `_broadcast` corrupt the send? No: `merged` is a fresh list of `(int, dict)` tuples; the dicts are `json.loads` products that are never mutated after broadcast, so the references are effectively immutable — both [EDGE] and [SEC] independently reached this conclusion and I confirmed there is no post-broadcast tagging path. **A malicious operator** can't do much — the dashboard is dev-only and `session_slug` originates from the server's own ContextVar, not the websocket payload, so no slug injection, no XSS (React escapes), no bucket-churn DoS from the client. **A confused operator** is the real risk: they pin the session they're driving, it ends, and the timeline goes blank with no explanation — they may think the *engine* died when it's just a stale pin. That's the strongest finding (MEDIUM, [EDGE]) and it's a follow-up, not a regression: before this change there was no pin at all and the view followed the wrong session anyway, so the net change is strictly an improvement. **A stressed buffer:** 64 sessions × 2000 events could reach ~500 MB — but reaching 64 concurrent real sessions on a single dev server is implausible, and the LRU cap prevents unbounded growth; without the cap the old code had the same per-event memory with worse eviction semantics. **A future maintainer** who adds a third `SessionPicker` caller could pass `liveSessions` without `onSelectLiveSession` and get a silent no-op ([EDGE] LOW) — worth a type tightening but not a today-bug. **Edge of correctness:** does `liveSessions.length === 0` ever hide the auto-follow option? No — `hasLiveSessions` false renders the original single `● Live: …` option, and the 4 legacy `SessionPicker` tests prove it. Nothing here rises to blocking. The fix does exactly what the ACs (1 & 2) demand and is honestly tested on both halves.

**AC status:** AC1 (partition + operator-selected, never last-emitting) ✓ tested. AC2 (concurrent sessions, no cross-bleed in header/Timeline) ✓ tested (UI scoping + server retention). **AC3 (sq-playtest skill Phase-3c caveat) — USER-PENDING:** Dev authored the corrected caveat but the commit was structurally soft-blocked by the auto-mode self-modification classifier (agent-config edit). I do not fail the story on AC3 — it is a docs-only caveat the agent is *prevented* from committing, with exact replacement text captured for the user. Flagged below.

**Handoff:** To Themis the Just (SM) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The story's server half ("watcher hub broadcasts all sessions") was an *un-diagnosed hypothesis*; the real server defect is the shared `deque(maxlen=2000)` evicting a quiet session under a noisy neighbor. Affects `sidequest-server/sidequest/telemetry/watcher_hub.py` (replay buffer needs per-session retention, not a bigger global cap). *Found by TEA during test design.*
- **Improvement** (non-blocking): `useLiveSource.ts` already has session-slug scoping from the 2026-06-16 "OTEL-INSPECTOR" partial fix — the remaining work is *operator selection over* that scoping, not new partitioning. Dev should extend the existing `inActiveSession`/`activeSlug` path, not rebuild it. Affects `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts`. *Found by TEA during test design.*
- **Question** (non-blocking): AC3 ("update the sq-playtest skill Phase-3c caveat once Live is trustworthy under concurrency") is a docs change in `.claude`/skill content with no behavioral test — Dev or Tech-Writer should action it as part of GREEN, and Reviewer should confirm it landed. *Found by TEA during test design.*
- **Question** (non-blocking): Per-session buffers risk unbounded memory with many sessions; Dev should bound the per-session retention (and Reviewer should confirm the fix is genuinely per-session, not merely a larger shared cap — a bigger global deque passes the strict-after test only by postponing the bug). Affects `sidequest-server/sidequest/telemetry/watcher_hub.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking — requires USER action): AC3 (sq-playtest skill Phase-3c caveat) — the caveat at `.claude/skills/sq-playtest/SKILL.md:163` is now stale (it still calls Live an unpartitioned "known bug"). I wrote the corrected replacement but the **commit was soft-blocked by the auto-mode self-modification classifier** (editing agent config from a story-derived directive needs explicit user consent), so I reverted the working-tree edit to keep the orchestrator tree clean. **Ready-to-apply replacement** for the line-163 blockquote: *"**Concurrent sessions:** the Inspector's **Live** view is partitioned by `session_id` and the session picker lets you pin a specific live session (story 126-23). With ≥2 concurrent sessions active, select the session you're driving from the picker's **Live sessions** group — the Live header and timeline scope to it, and a concurrent session that emits later won't steal the view. (Default is auto-follow-newest when you haven't pinned one.) The earlier mis-attribution bug — Live following whichever session last emitted — is fixed."* The user can apply+commit this, or grant the permission and ask me to. *Found by Dev during implementation.*
- **Improvement** (non-blocking): TEA's per-session-retention finding is addressed — replay retention is genuinely per-session (per-`session_slug` buckets), and bucket count is capped (`_MAX_SESSION_BUCKETS=64`, LRU) so it is not "a bigger global cap." Reviewer can confirm via `watcher_hub.py` `_append_to_session_buffer` / `_evict_session_bucket_if_needed`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking — USER action): AC3 (sq-playtest skill Phase-3c caveat) is not committed — Dev's edit was soft-blocked by the self-modification classifier. The exact replacement text is in the Dev delivery finding above; the user should apply it to `.claude/skills/sq-playtest/SKILL.md:163` (or grant permission for an agent to commit it). The functional fix (AC1/AC2) is complete and merged-ready without it. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Stale-pin guard — when `pinnedSlug` is not in `liveSessions`, auto-clear it or surface a "pinned session ended" notice so the operator isn't faced with a silently-blank timeline. Affects `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts` (add a guard near the `activeSlug = pinnedSlug ?? autoSlug` line). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Distinguish live vs. ended sessions in the picker (filter `liveSessions` to slugs present in `debugState`, or label historical-only ones) so ended sessions don't linger as if live. Affects `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts` + `SessionPicker.tsx`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Defensive `session_slug` normalization — `slug = safe_event.get("session_slug") or None` in `_broadcast` so an empty-string slug (not currently emitted) buckets as global infra, matching the UI's `'' `exclusion. Affects `sidequest-server/sidequest/telemetry/watcher_hub.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Gap:** The story's server half ("watcher hub broadcasts all sessions") was an *un-diagnosed hypothesis*; the real server defect is the shared `deque(maxlen=2000)` evicting a quiet session under a noisy neighbor. Affects `sidequest-server/sidequest/telemetry/watcher_hub.py`.
- **Improvement:** Stale-pin guard — when `pinnedSlug` is not in `liveSessions`, auto-clear it or surface a "pinned session ended" notice so the operator isn't faced with a silently-blank timeline. Affects `sidequest-ui/src/components/Dashboard/source/useLiveSource.ts`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest-server/sidequest/telemetry`** — 1 finding
- **`sidequest-ui/src/components/Dashboard/source`** — 1 finding

### Deviation Justifications

4 deviations

- **AC3 (skill docs caveat) has no behavioral test**
  - Rationale: Per `feedback_no_content_in_unit_tests`, docs/skill content invariants don't belong in unit tests; asserting on skill markdown would be a source-text test. Tracked instead as a Delivery Finding for Dev/Tech-Writer to action and Reviewer to confirm.
  - Severity: minor
  - Forward impact: Reviewer must verify the Phase-3c caveat was updated; not enforced by CI.
- **Server half pinned as per-session replay RETENTION, not generic "partition"**
  - Rationale: Minimal honest fix — the client→server one-way stream needn't gain a subscription protocol for a 3-pt story; per-session retention closes the genuine concurrency gap without re-architecting transport.
  - Severity: minor
  - Forward impact: If Dev/Reviewer judge the eviction tail out of scope, the server test file can be split to a follow-up; the UI selection fix stands alone for the common (non-overflow) case.
- **AC3 skill-caveat update deferred to user (self-modification guard)**
  - Rationale: The block is a deliberate safety mechanism requiring user consent for agent-config changes; working around it would violate that intent. The code ACs (1 & 2) are fully met and tested, so the story's functional fix is complete.
  - Severity: minor
  - Forward impact: AC3 remains open until the user applies the one-line caveat edit; Reviewer should note AC3 as user-pending rather than failing the story on it.
- **Per-session bucket cap (LRU) added beyond test requirements**
  - Rationale: Prevents a real memory leak on a long-lived dev server accumulating many ephemeral session slugs — directly addresses the flagged risk; without it, per-session buffers grow unbounded.
  - Severity: minor
  - Forward impact: none — bounded, additive; existing behavior unchanged for the common few-session case.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC3 (skill docs caveat) has no behavioral test**
  - Spec source: context-story-126-23.md, AC-3
  - Spec text: "Update the sq-playtest skill Phase-3c caveat once Live is trustworthy under concurrency."
  - Implementation: No automated test written for this AC — it is a prose/skill-doc edit with no runtime behavior to assert.
  - Rationale: Per `feedback_no_content_in_unit_tests`, docs/skill content invariants don't belong in unit tests; asserting on skill markdown would be a source-text test. Tracked instead as a Delivery Finding for Dev/Tech-Writer to action and Reviewer to confirm.
  - Severity: minor
  - Forward impact: Reviewer must verify the Phase-3c caveat was updated; not enforced by CI.
- **Server half pinned as per-session replay RETENTION, not generic "partition"**
  - Spec source: context-story-126-23.md, Problem ("Likely spans server (watcher hub broadcasts all sessions on /ws/watcher)")
  - Spec text: implies the server broadcast is the un-partitioned problem.
  - Implementation: Tests pin the concrete, currently-failing server behavior (a noisy session must not evict a quiet one's buffered replay history) rather than changing the broadcast/subscription protocol. `session_slug` is already broadcast on every event and the client already filters; the only broken server behavior under the repro is shared-buffer eviction.
  - Rationale: Minimal honest fix — the client→server one-way stream needn't gain a subscription protocol for a 3-pt story; per-session retention closes the genuine concurrency gap without re-architecting transport.
  - Severity: minor
  - Forward impact: If Dev/Reviewer judge the eviction tail out of scope, the server test file can be split to a follow-up; the UI selection fix stands alone for the common (non-overflow) case.

### Dev (implementation)
- **AC3 skill-caveat update deferred to user (self-modification guard)**
  - Spec source: context-story-126-23.md, AC-3
  - Spec text: "Update the sq-playtest skill Phase-3c caveat once Live is trustworthy under concurrency."
  - Implementation: Caveat rewrite authored, but the commit was soft-blocked by the auto-mode self-modification classifier (agent-config edit from a story-derived directive). Reverted the working-tree edit to keep the orchestrator tree clean; exact replacement text captured in the Dev delivery finding above for the user to apply.
  - Rationale: The block is a deliberate safety mechanism requiring user consent for agent-config changes; working around it would violate that intent. The code ACs (1 & 2) are fully met and tested, so the story's functional fix is complete.
  - Severity: minor
  - Forward impact: AC3 remains open until the user applies the one-line caveat edit; Reviewer should note AC3 as user-pending rather than failing the story on it.
- **Per-session bucket cap (LRU) added beyond test requirements**
  - Spec source: TEA Delivery Finding (Question, watcher_hub unbounded memory)
  - Spec text: "Dev should bound the per-session retention."
  - Implementation: Added `_MAX_SESSION_BUCKETS=64` with LRU eviction of the least-recently-active slug bucket (never the global `None` bucket). No test exercises this cap (it never triggers with ≤2 sessions).
  - Rationale: Prevents a real memory leak on a long-lived dev server accumulating many ephemeral session slugs — directly addresses the flagged risk; without it, per-session buffers grow unbounded.
  - Severity: minor
  - Forward impact: none — bounded, additive; existing behavior unchanged for the common few-session case.

### Reviewer (audit)
- **TEA: AC3 (skill docs caveat) has no behavioral test** → ✓ ACCEPTED by Reviewer: correct — it's a prose/skill edit with no runtime behavior; a source-text test would be a false positive. Tracking via Delivery Finding is the right call.
- **TEA: Server half pinned as per-session replay RETENTION, not generic "partition"** → ✓ ACCEPTED by Reviewer: sound and minimal — `session_slug` is already broadcast and the client already filters, so eviction was the only genuinely-broken server behavior under the repro. No transport re-architecture needed for 3 pts.
- **Dev: AC3 skill-caveat update deferred to user (self-modification guard)** → ✓ ACCEPTED by Reviewer: the agent is structurally blocked from committing agent-config; deferring with exact replacement text is the correct, honest resolution. AC3 flagged USER-PENDING in the assessment, not failed.
- **Dev: Per-session bucket cap (LRU) added beyond test requirements** → ✓ ACCEPTED by Reviewer: addresses a real unbounded-memory risk flagged by TEA; bounded (64 buckets), additive, never evicts the global `None` bucket, and does not alter the common few-session path. Verified the eviction invariant is sound and the cap-overflow edge is not reachable.

**No undocumented spec deviations found.** The `liveSessions` union of `debugState` + slug-tagged events is a reasonable implementation choice (not a spec divergence); both code ACs are met as specified.