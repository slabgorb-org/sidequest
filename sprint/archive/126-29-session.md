---
story_id: "126-29"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-29: [BUG] Gate Fate proactive tiles on committed-this-exchange so a resumed mid-exchange conflict doesn't offer actions the server rejects

## Story Details
- **ID:** 126-29
- **Jira Key:** (none)
- **Workflow:** tdd
- **Repos:** server, ui
- **Branch:** feat/126-29-fate-proactive-tile-commit-gate (base: develop, both subrepos)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T04:52:48Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T04:26:42Z | 2026-06-20T04:29:11Z | 2m 29s |
| red | 2026-06-20T04:29:11Z | 2026-06-20T04:39:08Z | 9m 57s |
| green | 2026-06-20T04:39:08Z | 2026-06-20T04:44:27Z | 5m 19s |
| review | 2026-06-20T04:44:27Z | 2026-06-20T04:52:48Z | 8m 21s |
| finish | 2026-06-20T04:52:48Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (Fezzik) for the RED phase.**

- **Story:** 126-29 — [BUG] Gate Fate proactive tiles on committed-this-exchange (#403). On a **resumed mid-exchange** Fate conflict, the UI offers the proactive Overcome / Create-Advantage / Attack / Concede tiles even when the PC has already committed this exchange; the server then rejects the throw via its sealed-commit guard. The fix surfaces the commit state into the client projection so the UI can pre-disable the tiles — it does **not** touch the guard.
- **Workflow:** tdd (phased) · **Repos:** server + ui · **Branch:** `feat/126-29-fate-proactive-tile-commit-gate` (base `develop`, both subrepos, clean + current).
- **Context doc:** `sprint/context/context-story-126-29.md`.

**Scope, as the story dictates:**
1. **Server:** add a per-PC `committed` bool to each `FATE_STATE.conflict` participant, sourced from `encounter.fate_commits`. First locate the FATE_STATE conflict projection and `fate_commits` (`grep -rn "fate_commits\|FATE_STATE\|conflict.*participant"` in the server repo) and project off the existing commit ledger — do not invent a parallel one.
2. **UI:** when `participant.committed` is set, disable/replace the proactive Overcome/Create-Advantage/Attack/Concede tiles with the **existing** fate-sealed-hint affordance (reuse it — don't author a new one). Note the Fate Conflict surface was just restyled by ui #431 and the dice tray by #430/#432 (all merged to develop today) — build on that current surface, not a stale copy.
3. **Hydration is the actual bug:** the failure is the **resumed** mid-exchange case (FATE_STATE hydrates on connect/resume, epic-126 #942). RED must pin a test where a PC already committed, the conflict is re-projected on resume, and `committed=true` reaches the client — then assert the tiles are gated.

**Hard constraint (ADR-129 / ADR-151):** Do **NOT** relax the server `dispatch_fate_throw` sealed-commit guard. It stays the backstop. RED should include a **regression assertion** that a double-commit is still rejected server-side, so a future change can't quietly soften it.

**OTEL (CLAUDE.md Observability Principle):** the committed-projection decision should emit a watcher event so the GM panel can verify the gate is engaged. RED asserts the span fires, not just the bool.

**Baseline heads-up for TEA/Dev (pre-existing, NOT this story):** the server suite carries a ~258–269 hermeticity-guard baseline (`build_async_anthropic` LlmClientError + loader baselines), and OTEL span-count tests can deadlock under full parallel run — run affected files serially (`-n0`) and classify against the full-suite baseline, not a scoped subset. Set `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test` or expect ~33 phantom MissingDatabaseUrlError.

**Verdict:** Clean two-repo projection-gating bug, no stack deps, merge gate open (all 5 prior Fate PRs landed this session). Ready for RED.

---
## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev). Verified via testing-runner, targeted files only.

**Test Files:**
- `sidequest-server/tests/server/test_126_29_committed_tile_gate.py` — 7 tests (commit `37502d6b`)
- `sidequest-ui/src/components/__tests__/FateConflictSurface.committed.test.tsx` — 5 tests (commit `05e422b`)

**RED proof (measured, not asserted):**
- Server: **6 failed, 1 passed**. 5× `AttributeError: 'FateConflictParticipant' object has no attribute 'committed'`; 1× `TypeError` (span `committed_count` is None). The AC5 guard tripwire PASSES. No collection errors.
- UI: **2 failed, 3 passed**. Tiles-not-disabled + sealed-hint-missing fail; 3 negative guards pass. No compile errors.

### AC → test map
| AC | Test | Repo | Status |
|----|------|------|--------|
| AC1 committed field on participant | `test_committed_pc_participant_projects_true` | server | failing |
| AC4(a) fresh → all uncommitted | `test_fresh_conflict_projects_all_participants_uncommitted` | server | failing |
| AC1 per-actor (not player-only) | `test_committed_is_per_actor_not_player_only` | server | failing |
| AC4(d) resume retains committed | `test_committed_survives_encounter_resume_roundtrip` | server | failing |
| AC2 broadcast carries committed | `test_emit_broadcasts_committed_status_on_the_wire` | server | failing |
| AC6 OTEL span confirms committed | `test_conflict_projected_span_carries_committed_status` | server | failing |
| AC5 guard NOT relaxed (tripwire) | `test_seal_fate_commit_guard_still_rejects_double_commit` | server | **passing** |
| AC3 tiles disable when committed | `disables all proactive tiles when the LOCAL PC's participant is committed` | ui | failing |
| AC3 fate-sealed-hint shows | `shows the fate-sealed-hint when the local PC is committed` | ui | failing |
| AC3 negative (no over-gating) | `leaves the proactive tiles ENABLED when the local PC has not committed` | ui | passing(guard) |
| AC3 gates on LOCAL pc only | `gates on the LOCAL PC's commit, not another participant's` | ui | passing(guard) |

### Rule Coverage
| Rule | Test(s) | Status |
|------|---------|--------|
| pydantic `extra:forbid` + resume dump/validate round-trip | `test_committed_survives_encounter_resume_roundtrip` | failing |
| Wiring test (real emit path, not source-text) | `test_emit_broadcasts_committed_status_on_the_wire` (drives `_maybe_emit_fate_state`) | failing |
| OTEL Observability Principle (subsystem decision emits a span) | `test_conflict_projected_span_carries_committed_status` | failing |
| Regression: guard not relaxed (ADR-129/151) | `test_seal_fate_commit_guard_still_rejects_double_commit` | passing tripwire |
| TS #4 null/undefined handling (`find()` → undefined) | `does not disable when the local PC is absent from participants` | passing(guard) |
| Python #2 mutable defaults | N/A — `committed` is a `bool` default (not mutable); flagged for Dev | n/a |

**Rules checked:** 5 of the applicable python/typescript lang-review rules have coverage (mutable-defaults n/a for a bool field).
**Self-check:** 0 vacuous tests. Every test asserts a concrete value (`.committed is True/False`, span attrs, `toBeDisabled`/`toBeEnabled`, `pytest.raises`). The 3 UI negative-guards pass today but are NOT vacuous — they pin "un-committed ⇒ enabled" so a Dev fix that over-gates (disables for everyone) is caught.

### GREEN spec for Dev (Inigo) — exact seams
**Server:**
1. `protocol/models.py:1065` `FateConflictParticipant` — add `committed: bool = False` (default keeps existing fixtures valid under `extra:forbid`).
2. `game/ruleset/fate_projection.py:128` `_project_conflict_participant(actor, snapshot)` — set `committed=any(c.actor == actor.name for c in snapshot.encounter.fate_commits)` (read the existing ledger; do NOT invent a parallel one). `snapshot.encounter` is non-None on this path (the builder only seats participants when a conflict is active).
3. `server/websocket_handlers/fate_state_emit.py:~90` — extend the `fate.conflict.projected` `Span.open` attributes with `committed_count` (count of `p.committed`) and `committed_actors` (comma-joined names). Then update the `SPAN_FATE_CONFLICT_PROJECTED` `SPAN_ROUTES` extract in `telemetry/spans/fate.py:84` to surface both (so the GM panel actually sees them — the test asserts the raw span attrs, but the route must carry them or the panel is blind).
4. Do **NOT** touch `seal_fate_commit` / its `FateConflictError` guard (ADR-129/151).

**UI:**
1. `src/types/payloads.ts:1220` `FateConflictParticipant` — add `committed?: boolean` (OPTIONAL, mirroring the `pending_compels?` back-compat pattern, so the ~dozen existing `{name, side}` fixtures stay valid).
2. `src/components/FateConflictSurface.tsx` — derive `const committed = conflict.participants.find(p => p.name === actorName)?.committed ?? false;` (use `?? false`, not `||`). Gate the 3 proactive tiles AND the Concede button on `sealedWaiting || armed !== null || committed`; render `fate-sealed-hint` on `sealedWaiting || committed`. No new prop needed — `committed` rides the existing `fateState` prop, so GameBoard wiring is untouched.

**Handoff:** To Dev (Inigo Montoya) for GREEN.

---
## Dev Assessment

**Implementation Complete:** Yes — implemented exactly to TEA's GREEN spec, no scope creep.

**Files Changed:**
*Server* (commit `1719e957`, pushed):
- `sidequest/protocol/models.py` — `FateConflictParticipant` gains `committed: bool = False` (default keeps existing fixtures valid under `extra:forbid`).
- `sidequest/game/ruleset/fate_projection.py` — `_project_conflict_participant` sets `committed=any(c.actor == actor.name for c in snapshot.encounter.fate_commits)` (reads the existing sealed-commit ledger; encounter guarded `is not None`).
- `sidequest/server/websocket_handlers/fate_state_emit.py` — `fate.conflict.projected` span now carries `committed_count` + `committed_actors`.
- `sidequest/telemetry/spans/fate.py` — `SPAN_FATE_CONFLICT_PROJECTED` route extract surfaces the two committed attrs (GM panel sees them).
- `seal_fate_commit` / `FateConflictError` guard — UNTOUCHED (ADR-129/151).

*UI* (commit `8331057`, pushed):
- `src/types/payloads.ts` — `FateConflictParticipant` gains `committed?: boolean` (optional, back-compat like `stunts?`).
- `src/components/FateConflictSurface.tsx` — derives `committed = conflict.participants.find(p => p.name === actorName)?.committed ?? false`; gates the 3 proactive tiles + Concede on `sealedWaiting || armed !== null || committed`; renders `fate-sealed-hint` on `sealedWaiting || committed`. `sealedWaiting` retained (per TEA's Question) — the two gates coexist.

**Tests:** GREEN. Server targeted run **24/24** (126-29 **7/7** + opponent-projection 7/7 + fate-state-emit 7/7 + routing-completeness 2/2 — no regressions). UI targeted run **55/55** across 6 files (committed **5/5** + existing FateConflictSurface test/compel/defend + GameBoard-fate-conflict + fate-protocol — no regressions). Verified via testing-runner.

**Quality gates:** server `ruff check` clean + `ruff format --check` clean (4 files); UI `tsc --noEmit` clean + `eslint` clean (changed files). Both working trees clean.

**Branch:** `feat/126-29-fate-proactive-tile-commit-gate` (pushed to both server + ui).

**Handoff:** To Reviewer (Westley) for review.

---
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 0, dismissed/downgraded 2, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned: preflight clean, security clean, silent-failure 2 findings; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 2 downgraded to non-blocking LOW (with rationale), 0 deferred

---
## Reviewer Assessment

**Verdict:** APPROVED

A lean, single-purpose fix: one boolean field projected from the authoritative sealed-commit ledger, plus the UI gate that reads it. No Critical/High issues. The diff matches the Dev assessment and TEA's GREEN spec exactly; the hard constraint (sealed-commit guard untouched) is verified.

### Observations (7)
- **[VERIFIED]** AC5 hard constraint holds — the sealed-commit guard is untouched. `git diff develop...HEAD -- sidequest/server/dispatch/fate_conflict.py` is empty; `seal_fate_commit` (raises `FateConflictError` on double-commit, fate_conflict.py:96-100) is unchanged. The story is a projection in FRONT of the guard, not a relaxation of it.
- **[VERIFIED]** Reads the authoritative ledger, not a parallel store — `fate_projection.py:154` computes `committed` from `enc.fate_commits`, the same list `seal_fate_commit` appends to. Matches the SM directive "project off the existing commit ledger — do not invent a parallel one."
- **[VERIFIED]** Wiring is real end-to-end — `committed` is a non-excluded field on the wire model, so it is part of `payload.model_dump_json()` (fate_state_emit.py:52), the change-gate signature. A commit flips `committed True` → signature changes → FATE_STATE re-broadcasts. Client `FateConflictSurface` reads `participants[me].committed` off the existing `fateState` prop (no new prop wiring). The commit→broadcast→gate loop is exercised by the server emit test + UI component test (the e2e pair TEA flagged).
- **[VERIFIED]** Resume-safe by construction — `committed` is recomputed every projection from the rehydrated `encounter.fate_commits` (persisted on `StructuredEncounter`, ADR-128). `FateConflictParticipant` is never itself persisted, so there is no stale-committed risk. `test_committed_survives_encounter_resume_roundtrip` pins the dump/validate path.
- **[SILENT]** `committed: bool = False` default (models.py:1090) — silent-failure-hunter flagged MEDIUM ("forgotten field at a future call site shows uncommitted"). **Downgraded to LOW, non-blocking.** Rationale: `FateConflictParticipant` has exactly ONE production constructor (`fate_projection.py:155`), which always sets `committed`; the default is the semantically-correct "no commit recorded = uncommitted" and is required by the TEA spec for `extra:forbid` back-compat. Security subagent independently judged it compliant with No Silent Fallbacks. Not a project-rule violation; making it required would break documented back-compat for zero real safety on a single-constructor model.
- **[SILENT]** `committed?: boolean` optional on the TS type (payloads.ts:1227) — silent-failure-hunter flagged LOW ("`?? false` un-disables if field ever missing"). **Dismissed as acceptable, non-blocking.** Rationale: matches the established `stunts?` / `pending_compels?` optional-back-compat convention in this same file; the server ALWAYS serializes `committed` (plain `bool`, no exclude), so the client always receives it; the `?? false` is the documented spectator-case guard (local PC absent from participants), confirmed correct by the hunter itself. The full-replay client mirror (ADR-133) replaces FATE_STATE wholesale, so "stale cached payload missing committed" is not a real path.
- **[SEC]** Security subagent: **clean** — the broadcast adds only the boolean fact "this actor has sealed an action this exchange." The chosen action, target, skill, dice, and aspect_text stay on `FateSealedCommit` (server-only), never projected. Consistent with ADR-036's collaborative-visibility amendment; `committed_actors` goes to the GM `/ws/watcher` OTEL stream, not the player socket, and actor names are server-set (chargen), not new free-text into a narrator prompt.

### Dispatch tags
`[SILENT]` 2 findings (both downgraded/dismissed non-blocking, above) · `[SEC]` clean · `[EDGE]` disabled · `[TEST]` disabled · `[DOC]` disabled · `[TYPE]` disabled · `[SIMPLE]` disabled · `[RULE]` disabled (6 subagents disabled via `workflow.reviewer_subagents`; their domains assessed by me below where relevant).

### Rule Compliance
- **No Silent Fallbacks (CLAUDE.md):** `enc is not None and any(...)` (fate_projection.py:154) returns the honest `False` ("no encounter → no commit"); the guard is redundant-but-harmless (the sole caller already proves `enc` non-None) — not a masked config error. `committed: bool = False` is the correct absent-default, not a fallback. **Compliant.**
- **No Stubbing / Don't Reinvent (CLAUDE.md):** reads the existing `fate_commits` ledger and reuses the existing `fate.conflict.projected` span + `fate-sealed-hint` element. No new parallel store, no new span, no new UI affordance. **Compliant.**
- **OTEL Observability Principle (CLAUDE.md):** the committed-projection decision emits `committed_count`/`committed_actors` on `fate.conflict.projected`, AND the `SPAN_ROUTES` extract surfaces them so the GM panel actually sees them (not a span-only dead end). **Compliant.**
- **OTEL "No Source-Text Wiring Tests" (CLAUDE.md):** the wiring test (`test_emit_broadcasts_committed_status_on_the_wire`) drives the real `_maybe_emit_fate_state` and asserts on the emitted payload — behavioral, not `read_text()`. **Compliant.**
- **Bind the Ruleset, Don't Balance It (SOUL.md/ADR-143):** no native dial/beat mechanic touched; committed reads the Fate sealed-commit ledger only. **Compliant.**
- **TS null/undefined handling (lang-review #4):** uses `?? false` (nullish), not `||`; `find()`-returns-undefined handled. **Compliant.**
- **pydantic extra:forbid (server):** `committed` added as a typed field; `extra:forbid` still rejects unknown keys. **Compliant.**

### Devil's Advocate
Let me argue this is broken. First attack: **the gate is client-side cosmetics — a malicious client can still fire a FATE_THROW for a committed PC.** True — but that is by design, and the design is correct: AC5 keeps the server `seal_fate_commit` guard as the authoritative fail-loud backstop (verified untouched), so a client that ignores `committed` and throws anyway is rejected with `FateConflictError`. The UI gate only spares an honest client the round-trip rejection on resume; it is not a security boundary, and the story explicitly says so. Second attack: **does broadcasting `committed` leak hidden information in a future PvP/sealed-visibility scenario?** Today no (collaborative visibility, ADR-036), but sealed-visibility is "reserved for unimplemented PvP." If that mode lands, `committed` (a per-participant boolean broadcast to all seats) would reveal "player X has acted" — which in a sealed scenario is exactly what must stay hidden. That is a FORWARD risk for the unimplemented PvP path, not a defect here; I capture it as a non-blocking finding so the PvP work doesn't inherit it silently. Third attack: **the change-gate could suppress the commit broadcast.** Checked: `committed` is in `model_dump_json()`, so a commit flips the signature and forces re-emit — the opposite of suppression; it actually makes the gate fire on commit where before only stress/aspect changes did. Fourth attack: **what if two participants share a name?** `any(c.actor == actor.name ...)` and the UI `find(p => p.name === actorName)` both key on name; a duplicate-named PC and NPC would cross-gate. But participant names are unique within an encounter (the seating + `find_creature_core` paths assume name-uniqueness everywhere), and this fix introduces no new name collision the rest of the system doesn't already assume. Fifth attack: **empty/None encounter crashes the projection.** Guarded — `enc is not None` short-circuits. No new crash surface. Conclusion: the only thing my devil's advocate surfaced is the forward PvP sealed-visibility risk, logged below as non-blocking.

**Data flow traced:** player commits → `seal_fate_commit` appends to `encounter.fate_commits` → next `_maybe_emit_fate_state` → `build_fate_state_payload` → `_project_conflict_participant` reads `enc.fate_commits` → `committed=True` on the wire → client `FateConflictSurface` disables the proactive tiles + Concede and shows `fate-sealed-hint`. On resume the rehydrated `fate_commits` re-projects the same `committed=True`. Safe — server is authoritative throughout; the client gate never substitutes for the guard.

**Handoff:** To SM for finish-story.

---
## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The resume end-to-end (reconnect → FATE_STATE → gated tiles) is pinned at the UNIT boundary as a pair — server `test_committed_survives_encounter_resume_roundtrip` (dump/validate round-trip projection) + UI `disables all proactive tiles…` (component reads `participant.committed`) — not as one full-stack jsdom WebSocket-reconnect test (no such harness exists). Affects `tests/server/test_126_29_committed_tile_gate.py` + `FateConflictSurface.committed.test.tsx` (Reviewer should read the two as the e2e pair; a future playtest/understudy run is the real reconnect proof). *Found by TEA during test design.*
- **Question** (non-blocking): The existing client `sealedWaiting={fateSealed}` (GameBoard.tsx:682) is the in-session pre-resolution gate; this story ADDS a resume-safe committed gate. Dev should OR the two (keep `sealedWaiting`, add `|| committed`), not replace — `fateSealed` still covers the live submit-and-wait window before any resume. Affects `FateConflictSurface.tsx` (confirm both gates coexist). *Found by TEA during test design.*

### Dev (implementation)
- Resolved TEA's Question: kept `sealedWaiting` and OR'd `committed` (`sealedWaiting || armed !== null || committed`), so the in-session barrier and the resume-safe gate coexist exactly as TEA recommended.
- No upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): If the reserved sealed-visibility / PvP mode (ADR-036) is ever implemented, the broadcast `committed` boolean would reveal "player X has acted this exchange" to all seats — exactly what a sealed scenario must hide. The gate is correct for the current collaborative-visibility playgroup; the PvP work should gate `committed` projection on visibility mode. Affects `sidequest/game/ruleset/fate_projection.py` (`_project_conflict_participant`) + `fate_state_emit.py` (per-recipient projection when sealed-visibility lands). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 1 Question, 0 Improvement)
**Blocking:** None

- **Question:** The existing client `sealedWaiting={fateSealed}` (GameBoard.tsx:682) is the in-session pre-resolution gate; this story ADDS a resume-safe committed gate. Dev should OR the two (keep `sealedWaiting`, add `|| committed`), not replace — `fateSealed` still covers the live submit-and-wait window before any resume. Affects `FateConflictSurface.tsx`.

### Downstream Effects

- **`.`** — 1 finding

### Deviation Justifications

2 deviations

- **AC6 span: extend the existing `fate.conflict.projected`, not a new span**
  - Rationale: that span already fires exactly once per in-conflict FATE_STATE broadcast and is the established GM-panel conflict lie-detector (#973 precedent); committed status is in-conflict-only, so it belongs there — a second always-paired span would be redundant.
  - Severity: minor
  - Forward impact: Dev must add the two attrs to BOTH the `Span.open` call (fate_state_emit.py) AND the `SPAN_FATE_CONFLICT_PROJECTED` `SPAN_ROUTES` extract (telemetry/spans/fate.py); if Dev elects a new span instead, the test name + asserted attrs must move with it.
- **AC4(d) resume: pydantic dump/validate round-trip, not a live reconnect**
  - Rationale: `committed` is a pure projection of `encounter.fate_commits`; the resume path persists+rehydrates that ledger, so the round-trip is the deterministic unit-level proof the projection survives. A full reconnect adds integration scope with no added signal for this derived field.
  - Severity: minor
  - Forward impact: none (the field is derived at projection time, never separately stored).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC6 span: extend the existing `fate.conflict.projected`, not a new span**
  - Spec source: context-story-126-29.md, AC6
  - Spec text: "OTEL span to confirm committed status is set/broadcast per participant."
  - Implementation: `test_conflict_projected_span_carries_committed_status` asserts `committed_count` + `committed_actors` attributes on the EXISTING `fate.conflict.projected` span (to be extended), rather than introducing a new dedicated span.
  - Rationale: that span already fires exactly once per in-conflict FATE_STATE broadcast and is the established GM-panel conflict lie-detector (#973 precedent); committed status is in-conflict-only, so it belongs there — a second always-paired span would be redundant.
  - Severity: minor
  - Forward impact: Dev must add the two attrs to BOTH the `Span.open` call (fate_state_emit.py) AND the `SPAN_FATE_CONFLICT_PROJECTED` `SPAN_ROUTES` extract (telemetry/spans/fate.py); if Dev elects a new span instead, the test name + asserted attrs must move with it.
- **AC4(d) resume: pydantic dump/validate round-trip, not a live reconnect**
  - Spec source: context-story-126-29.md, AC4(d)
  - Spec text: "on server resume mid-exchange, the same PC's FATE_STATE retains committed=true."
  - Implementation: `test_committed_survives_encounter_resume_roundtrip` round-trips `StructuredEncounter` through `model_dump()`/`model_validate()` (the serialization the reconnect replays), rebuilds a snapshot, and re-projects — rather than driving a real WebSocket reconnect.
  - Rationale: `committed` is a pure projection of `encounter.fate_commits`; the resume path persists+rehydrates that ledger, so the round-trip is the deterministic unit-level proof the projection survives. A full reconnect adds integration scope with no added signal for this derived field.
  - Severity: minor
  - Forward impact: none (the field is derived at projection time, never separately stored).

### Dev (implementation)
- No deviations from spec. Implemented TEA's GREEN spec verbatim — `committed: bool = False` on the model, projection sourced from `encounter.fate_commits`, the two committed attrs on the existing `fate.conflict.projected` span + its route, optional `committed?: boolean` on the TS type, and the `?? false`-guarded tile/Concede/hint gate. The sealed-commit guard was not touched.

### Reviewer (audit)
- **TEA Deviation 1 (AC6 span: extend `fate.conflict.projected`, not a new span)** → ✓ ACCEPTED by Reviewer: extending the existing in-conflict lie-detector span is the right call (DRY, in-conflict-scoped); verified Dev wired the two attrs to BOTH the `Span.open` call and the `SPAN_ROUTES` extract, so the GM panel actually receives them.
- **TEA Deviation 2 (AC4(d) resume: pydantic dump/validate round-trip, not a live reconnect)** → ✓ ACCEPTED by Reviewer: `committed` is a pure derivation of `encounter.fate_commits`, which is what the resume path persists+rehydrates; the round-trip is the correct deterministic unit proof. A live reconnect adds integration scope with no added signal for this derived field.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed — the diff matches TEA's GREEN spec verbatim, with no undocumented divergence spotted during the rule-by-rule pass.