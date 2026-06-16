---
story_id: "118-5"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 118-5: F3e — Compel accept/refuse round-trip (closes the F2b deferral)

## Story Details
- **ID:** 118-5
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** 118-2 (F3b Fate panel)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T20:35:54Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T18:34:53Z | 2026-06-16T18:37:22Z | 2m 29s |
| red | 2026-06-16T18:37:22Z | 2026-06-16T18:59:55Z | 22m 33s |
| green | 2026-06-16T18:59:55Z | 2026-06-16T19:49:14Z | 49m 19s |
| review | 2026-06-16T19:49:14Z | 2026-06-16T20:03:47Z | 14m 33s |
| finish | 2026-06-16T20:03:47Z | 2026-06-16T20:05:52Z | 2m 5s |
| green | 2026-06-16T20:05:52Z | 2026-06-16T20:21:47Z | 15m 55s |
| review | 2026-06-16T20:21:47Z | 2026-06-16T20:35:54Z | 14m 7s |
| finish | 2026-06-16T20:35:54Z | - | - |

## Story Summary

F3e closes the F2b deferral by implementing the compel accept/refuse round-trip. F2b's `propose_fate_compel` fires `fate.compel.offered` but the engine never persisted a `PendingCompel` (the shipped flow is stateless). This story adds:

- **SERVER:** The accept/refuse routing seam. Accept → `module.accept_compel` (+1 fate point, fires `fate.compel.accepted`); Refuse → pay 1 fate point to decline (per SRD). Show the fate-point delta on resolve.
- **UI:** The player surface for accept/refuse buttons.

## Acceptance Criteria

1. **Server: PendingCompel persistence** — When a compel is offered (F2b `propose_fate_compel`), the engine stores a `PendingCompel` data structure with compel id, character name, aspect text, and the offered fate point delta.

2. **Server: Accept/Refuse routing** — Extend the FATE_ACTION pipeline (already wired in 118-6) with two new action verbs:
   - `compel_accept`: Routes to `module.accept_compel`, which adds +1 fate point (the player accepts the compel and receives a fate point as reward per SRD) and fires an `fate.compel.accepted` OTEL span.
   - `compel_refuse`: Routes to a refuse handler that subtracts 1 fate point (the player declines the compel by spending a fate point) and fires an `fate.compel.refused` OTEL span.

3. **Server: Fate-point delta on resolve** — The server response includes the fate-point delta (±1) so the UI can show the mechanical outcome inline.

4. **UI: Accept/Refuse buttons** — Extend `FateConflictSurface.tsx` with Accept/Refuse buttons, gated on `FATE_STATE.conflict.pending_compels`. Buttons trigger `onFateAction` with the appropriate compel verb (`compel_accept` or `compel_refuse`).

5. **UI: Mechanics-first legibility** — Show the ±1 fate-point delta inline (supports Sebastien/Jade's mechanics-first player style per CLAUDE.md).

6. **UI integration test** — A test proving that Accept/Refuse buttons trigger `onFateAction` → `FATE_ACTION` message fires with the compel verb.

7. **Server wiring test** — A test proving that `PendingCompel` is persisted and the fate-point delta is applied on accept/refuse.

8. **OTEL observability** — Every subsystem decision emits an OTEL span:
   - `fate.compel.offered` (already emitted by F2b)
   - `fate.compel.accepted` (new, on accept)
   - `fate.compel.refused` (new, on refuse)

## Technical Approach

### Carrier: Dedicated In-Panel Control (Resolved)

**DECISION (Keith, 2026-06-16):** Compel control lives on the Fate surfaces (FateConflictSurface / FatePanel), NOT the ADR-107 aside channel. This reuses the FATE_ACTION pipeline shipped in 118-6 — "wire up what exists."

**Rationale:**
- Fate packs emit FATE_STATE and never co-render the confrontation tab (ADR-144, widgetRegistry.ts:165).
- Accept/Refuse buttons extend the FATE_ACTION verb set with `compel_accept` / `compel_refuse`.
- The control lives on `FateConflictSurface.tsx` (the Fate analog of ConfrontationOverlay, already mounting in 118-6), gated on `FATE_STATE.conflict.pending_compels`.
- Show the ±1 fate-point delta inline for mechanics-first legibility (Sebastien/Jade).

### Key Technical Anchors

1. **UI Message Pipeline:**
   - `FATE_ACTION` message type already exists (protocol.ts)
   - Dispatched via `App.tsx:handleFateAction()` (~line 1976)
   - `FateActionPayload.action` verb is extensible — add `compel_accept` and `compel_refuse`

2. **UI Surface:**
   - `FateConflictSurface.tsx` is the mounting point for Accept/Refuse buttons
   - Gate on `FATE_STATE.conflict.pending_compels` (a list of pending compels per PC)
   - Render one set of buttons per pending compel

3. **Server:**
   - Persist a `PendingCompel` structure when `propose_fate_compel` is called (F2b's deferred work)
   - Extend `dispatch_fate_action` to route `compel_accept` and `compel_refuse` verbs
   - `compel_accept` → `module.accept_compel(pc, compel_id)` → +1 FP + fire `fate.compel.accepted` span
   - `compel_refuse` → custom refuse handler → -1 FP + fire `fate.compel.refused` span
   - Include fate-point delta in the FATE_STATE update so the UI can display it

4. **OTEL Observability:**
   - `fate.compel.offered` already fires in F2b's `propose_fate_compel`
   - `fate.compel.accepted` fires on accept (new)
   - `fate.compel.refused` fires on refuse (new)
   - GM panel can verify the round-trip via these spans (OTEL observability principle from CLAUDE.md)

5. **Wiring Tests:**
   - UI integration test: Accept/Refuse buttons exist and trigger `onFateAction` with the correct compel verb
   - Server test: `PendingCompel` is persisted and fate-point delta is applied correctly
   - (These are wiring tests per the development principles — proving the feature is actually integrated, not just that isolated components work)

## Sm Assessment

**Setup complete; routing to TEA (Amos Burton) for RED.**

- **Repos:** server, ui. Branches `feat/118-5-fate-compel-accept-refuse` cut off `develop` in both subrepos. (Orchestrator repo targets `main`; these two subrepos target `develop` per repos.yaml — TEA/Dev work happens in the subrepos.)
- **Jira:** not configured for this project — claim skipped intentionally, sprint runs on YAML only.
- **PARKED OPEN Q is RESOLVED.** Keith decided the carrier this session: dedicated in-panel control extending the existing `FATE_ACTION` pipeline (NOT the ADR-107 aside channel). Captured in Technical Approach §Carrier. This was the one decision blocking RED — it is now closed, so TEA can write failing tests against a fixed surface.

**What RED must cover (failing tests first):**
1. Server: a `PendingCompel` is persisted when `propose_fate_compel` fires (F2b's deferred state). Currently the flow is stateless — assert persistence.
2. Server: `FATE_ACTION` verbs `compel_accept` (+1 FP, `fate.compel.accepted` span) and `compel_refuse` (−1 FP, `fate.compel.refused` span) route correctly and apply the fate-point delta. Refuse must require/spend a fate point per SRD — TEA should assert the refuse path when the PC has 0 FP (cannot decline) as an edge case.
3. UI wiring test: Accept/Refuse buttons in `FateConflictSurface.tsx`, gated on `FATE_STATE.conflict.pending_compels`, trigger `onFateAction` with the correct verb → `FATE_ACTION` fires (the mandatory wiring test — proves end-to-end integration, not isolated components).
4. OTEL: the two new spans are the lie-detector for the round-trip — assert they emit.

**Flags for TEA / Dev:**
- **Bind, don't balance.** This is ADR-144 Fate Core territory. Accept = +1 FP, refuse = pay 1 FP are SRD rules — take them from the SRD, don't homebrew the economy.
- Reuse the shipped 118-6 `FateActionHandler` / `dispatch_fate_action` seam — do not introduce a parallel compel message type.
- Stack parent is 118-2 (F3b Fate panel), already shipped; no stack-ready block.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt feature story (server + ui) — a Fate Core economy round-trip with OTEL and a player surface. Not a chore bypass.

**Test Files:**
- `sidequest-server/tests/game/ruleset/test_fate_compel_refuse.py` — the new `refuse_compel` ruleset primitive (spend 1 FP + `fate.compel.refused` span; fail loud at 0 FP, no span on rejection).
- `sidequest-server/tests/server/dispatch/test_fate_compel_roundtrip.py` — the full server round-trip: offer persists → `FATE_STATE.conflict.pending_compels` surfaces it → `dispatch_fate_action` routes `compel_accept`/`compel_refuse` (±1 FP, accepted/refused spans, `fate_point_delta` on the result), consumes the compel, and fails loud on refuse-at-0 and on a phantom (never-offered) compel.
- `sidequest-ui/src/components/__tests__/FateConflictSurface.compel.test.tsx` — the Accept/Refuse control: one pair per pending compel, fires `onFateAction({action: compel_accept|compel_refuse, aspect_text})`, ±1 FP delta inline, complication shown, gated negatives (none when empty, none on non-Fate ruleset), sealed-barrier disable.
- `sidequest-ui/src/components/GameBoard/__tests__/GameBoard-fate-compel-wiring.test.tsx` — the mandatory production-path wiring test (App→GameBoard `onFateAction`→FateConflictSurface), behavioral (render board, activate Fate Conflict tab, click Accept, assert callback).

**Tests Written:** 21 tests (11 server, 10 ui) covering all 8 ACs.
**Status:** RED — verified via `testing-runner`. Server 11/11 fail; UI 8/10 fail. The 2 UI passes are the **negative guards** ("no control when no pending compels", "no control on non-Fate ruleset") — they assert *absence*, which correctly holds now and must keep holding after GREEN (paired-negative contract, not vacuous). Collection clean in both repos; every failure is unimplemented behavior (missing `refuse_compel` / `offer_compel(encounter=)` / `pending_compels` / `compel_*` Literal members / `fate_point_delta` / the UI control), never an import or fixture bug.

**AC coverage map:** AC1→`test_offered_compel_persists_and_surfaces_in_fate_state`; AC2→`test_compel_accept_*`/`test_compel_refuse_*`; AC3→`result.fate_point_delta` asserts; AC4→UI render/gate tests; AC5→`shows the +1 / -1 fate-point delta inline`; AC6→UI dispatch + board wiring tests; AC7→the roundtrip file (real dispatch + projection); AC8→accepted/refused span asserts (`offered` is existing F2b behavior, covered by `test_fate_compel_tool.py`).

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| PY #11 input validation / No Silent Fallbacks | `test_refuse_compel_at_zero_points_raises_and_does_not_emit`, `test_compel_refuse_at_zero_points_is_rejected_loudly`, `test_accepting_a_compel_that_was_never_offered_fails_loud` | failing (RED) |
| PY #6 / TS #8 test quality (meaningful asserts, no `as any`) | self-check: intersection types for `pending_compels` (no `as any`); all asserts pin values/counts, not truthiness | pass (self) |
| PY #4 OTEL on every subsystem decision | `fate.compel.accepted` + `fate.compel.refused` span asserts; validate-before-emit (no span on rejected refuse) | failing (RED) |
| TS #6 react-jsx stable keys (not index) | `renders one Accept/Refuse pair per pending compel (keyed by aspect, not index)` | failing (RED) |
| TS #3 / verb routing exhaustiveness | both `compel_accept` and `compel_refuse` routed (`test_compel_accept_*` + `test_compel_refuse_*`) — Dev adds both Literal members | failing (RED) |
| Wiring (CLAUDE.md "every suite needs a wiring test") | `GameBoard-fate-compel-wiring.test.tsx` (behavioral, production path) + `test_fate_compel_roundtrip.py` (real dispatch→projection) | failing (RED) |

**Rules checked:** the TEA-testable lang-review rules (the rest are Dev-implementation checks — silent-except, mutable-defaults, etc. — uncheckable until GREEN; the python gate runs at Dev handoff).
**Self-check:** 0 vacuous tests; the 2 RED-passing UI tests are intentional absence-guards, not vacuous truthy asserts.

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (server):**
- `sidequest/telemetry/spans/fate.py` — `fate.compel.refused` SpanRoute + `fate_compel_refused_span` + `__all__`.
- `sidequest/game/encounter.py` — `PendingCompel` model + `StructuredEncounter.pending_compels` + `add_/find_/remove_pending_compel` helpers.
- `sidequest/game/ruleset/fate.py` — `offer_compel(encounter=)` persists onto the active conflict; new `refuse_compel` (spends 1 FP via fail-loud `spend_fate_point`, emits the refused span); imports + `TYPE_CHECKING` encounter.
- `sidequest/game/ruleset/fate_projection.py` — `build_fate_state_payload` surfaces `conflict.pending_compels`.
- `sidequest/protocol/models.py` — `FatePendingCompel` + `FateConflictEntry.pending_compels`.
- `sidequest/protocol/fate.py` — `compel_accept`/`compel_refuse` added to the `FateActionPayload.action` Literal (+ docstring).
- `sidequest/server/dispatch/fate_conflict.py` — `resolve_compel` + early compel routing in `dispatch_fate_action`; `fate_point_delta` on `FateDispatchResult`.
- `sidequest/agents/tools/fate_tools.py` — `propose_fate_compel` passes the canonical in-turn `ctx.snapshot.encounter` so offers persist in production.
- `tests/server/test_fate_unaffordable_invoke_handler_118_6.py` — drive-by repair (see deviation).

**Files Changed (ui):**
- `src/types/payloads.ts` — `FatePendingCompel` + optional `FateConflictEntry.pending_compels`.
- `src/components/FateConflictSurface.tsx` — `FateActionVerb` extended; compel Accept/Refuse control (per pending compel, complication + ±1 FP shown, sealed-disable, fires `onFateAction`).

**Tests:** GREEN. Server Fate suite **420 passed, 1 skipped** (incl. the 4 new + the repaired 118-6 test). UI Fate components **52 passed** (incl. the 2 new files). Server `ruff` + `ruff format` + `pyright` clean on changed files; UI `tsc --noEmit` + `eslint` clean.

**Pre-existing red (NOT introduced by 118-5, proven):** A full-suite run shows 85 server failures + `test_message_type_complete_count` (57≠56). I reproduced ALL of them on the clean merge-base (`0364ee06`, via a throwaway worktree) — they are the in-flight epic-108 / ADR-143 WWN-combat rework (`committed_blow`/`downed_seam`/`test_102_4_wn_sealed_round`) and a message-type enum drift. My diff touches zero WN/enum/downed-seam files. Captured as a Delivery Finding.

**Wiring (end-to-end, not half-wired):** narrator `propose_fate_compel` → persists on `ctx.snapshot.encounter` → per-turn `_maybe_emit_fate_state` (change-gated; `pending_compels` is in the signature) broadcasts FATE_STATE → UI renders Accept/Refuse → `onFateAction` → `handleFateAction` → `FATE_ACTION` → `FateActionHandler` → `dispatch_fate_action` → `resolve_compel` (+/-1 FP, span, consume) → next cadence re-emits the updated FATE_STATE.

**Branch:** `feat/118-5-fate-compel-accept-refuse` (pushed, both subrepos).

**Handoff:** To Reviewer (Chrisjen Avasarala).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean (fate suite green) | 2 notes | confirmed 1 (find_pending_compel leak→LOW), noted 1 (delta-forward) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — self-assessed ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — self-assessed ([SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 | confirmed 4, downgraded 1, noted 3 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 (2 HIGH lying-docstring) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — self-assessed ([TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — self-assessed ([SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — self-assessed ([SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 2 | confirmed 1 (TS-6 LOW), dismissed 1 (ADD-2 — verified) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 4 confirmed blocking, 6 confirmed non-blocking, 1 dismissed (with evidence)

## Reviewer Assessment

**Verdict:** REJECTED

The feature is functionally correct, fully wired end-to-end, and the Fate suite is green (420 server / 52 UI; ruff/pyright/tsc/eslint clean). The 85 other server failures are proven pre-existing epic-108 WWN-combat debt — confirmed not this diff's doing. **This is a quality/honesty rejection, not a functional one.** Two confirmed lying-docstring findings (which this project's lie-detector doctrine and the 107-1 precedent say I cannot dismiss) and two missing negative tests on fail-loud paths must be fixed first.

### Severity Table (blocking)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] [DOC][SIMPLE] | `PendingCompel.offered_delta` is stored (to satisfy AC-1's "offered fate point delta") but **never projected or read** — `fate_projection` drops it, the UI hardcodes "+1 FP" / "−1 FP" in the button labels. Its docstring claims "the fate point the player GAINS by accepting," behavior nothing implements (No Stubbing + lie-detector doc). | `sidequest-server/.../game/encounter.py:204`, `fate_projection.py:156`, `sidequest-ui/.../FateConflictSurface.tsx:71/79` | WIRE it through: add `offered_delta` to `FatePendingCompel` (server + ui), project it, render `+{offered_delta}` on Accept (refuse is SRD-fixed −1). This satisfies AC-1 (stored) **and** AC-3/AC-5 (the shown delta is real data, not a hardcoded literal that can drift from the SRD). If a forward-only field is truly intended, that contradicts AC-1/AC-3 — escalate; do not leave it dead. |
| [HIGH] [DOC] | `GameBoard-fate-compel-wiring.test.tsx` docstring overclaims it proves the "**App** → GameBoard → FateConflictSurface production path (App.tsx:2727 → GameBoard.tsx:644)". The test renders `<GameBoard>` directly — it never mounts `<App>`, so the App→GameBoard link is **not** exercised. (Identical pattern to the 107-1 rejection; comment-analyzer HIGH, cannot dismiss.) | `sidequest-ui/.../GameBoard/__tests__/GameBoard-fate-compel-wiring.test.tsx:1-13` | Trim the claim to what GREEN proves: "GameBoard → FateConflictSurface; GameBoard threads `onFateAction` down. App.tsx:2727 is the remaining untested link." (Or mount `<App>`.) |
| [MEDIUM] [TEST] | Phantom-**refuse** is untested. Only `compel_accept` on a never-offered aspect is covered (`test_accepting_a_compel_that_was_never_offered_fails_loud`). Both verbs share `resolve_compel`'s `find_pending_compel is None → raise`, but the refuse leg of that fail-loud path has no test — a silent regression vector if routing ever diverges. | `sidequest-server/.../tests/server/dispatch/test_fate_compel_roundtrip.py` | Add `test_refusing_a_compel_that_was_never_offered_fails_loud` (no offer → `_dispatch(_refuse())` raises `FateConflictError`, FP unchanged). |
| [MEDIUM] [TEST] | The `offer_compel` persistence guard `if encounter is not None and not encounter.resolved` has no test for the **resolved-encounter** branch. The guard can be silently removed and stale compels from finished conflicts would start surfacing in the projection. | `sidequest-server/.../game/ruleset/fate.py:323`, tests in `test_fate_compel_roundtrip.py` | Add a test: `enc.resolved = True`, `offer_compel(encounter=enc, ...)` → `fate.compel.offered` span fires, `enc.pending_compels == []`. |

### Observations (tagged; ≥5)

- [DOC][HIGH] `offered_delta` dead/lying field — see severity table. Confirmed by comment-analyzer (HIGH) + test-analyzer.
- [DOC][HIGH] Overclaiming wiring-test docstring — see severity table. Confirmed by comment-analyzer (HIGH).
- [TEST][MEDIUM] Missing phantom-refuse + resolved-guard negatives — see table. Confirmed by test-analyzer.
- [SILENT][MEDIUM] `fate_tools.py:81` comment "no silent state loss — the offer was never persistable to begin with" overclaims: `ToolContext.snapshot` is `None` on legacy/fixture paths too, so a `None` snapshot **during a live conflict** would silently drop a persistable offer (the offered span still fires, but the player never gets the control). Restate the comment to name both `None` origins and flag the live-conflict case as a wire bug to investigate, not a benign path. (No Silent Fallbacks honesty.) Non-blocking — the live path threads `ctx.snapshot` today — but fix the comment.
- [DOC][LOW] `offer_compel` docstring says "when an active `encounter` is given" while the guard is `not encounter.resolved`; state the guard explicitly (`fate.py:318`).
- [EDGE][LOW] `find_pending_compel` exact `(target, aspect)` match — a 2nd compel on the SAME aspect to the SAME PC is unreachable (find/remove hit only the first); consistent with the accepted aspect_text-as-id TEA deviation. Note only.
- [SIMPLE][LOW] [RULE] TS-6: inline arrow `onClick` inside `compels.map` (`FateConflictSurface.tsx:216/224`) — no `useCallback`. Acceptable for a 1-2 item rack; note.
- [TEST][LOW] `±1` assertions match raw button label text (`/\+1/`, `/[-−]1/`) — couples to label prose; once `offered_delta` is wired, assert on a `data-testid` delta value instead.
- [TYPE][VERIFIED] `PendingCompel` (`encounter.py:188`) and `FatePendingCompel` (`models.py:1056`) both set `model_config = {"extra": "forbid"}` and are fully typed; `FateDispatchResult.fate_point_delta: int = 0`; `FateActionPayload.action` is a closed `Literal` (6 members). The UI `pending_compels?` optional-vs-server-required asymmetry is an intentional additive-field convention (Dev deviation, accepted). No stringly-typed escapes, no `as any`. Complies with the type rules.
- [SEC][VERIFIED] `resolve_compel` takes `actor_name` from the **authenticated** session (`fate_action.py:69` `sd.player_id`, with the 118-8 spoof-rejection guard upstream); `aspect_text` is server-pushed data round-tripped back, not free user text; the compel firewall holds (a client can only resolve a compel whose `target == authenticated actor`, else `find_pending_compel` → None → raise). Display text is raw but the UI escapes it (consistent with the projection's documented contract). No injection / cross-seat vector. Evidence: `fate_action.py:69-91`, `resolve_compel` `target`/`actor_name` match.
- [RULE][VERIFIED] rule-checker swept 26 rules / 89 instances: only TS-6 (LOW, above). ADR-144 "bind don't balance" holds — accept=+1/refuse=−1 go through the atomic `earn/spend_fate_point` (SRD-fixed, no tuning vector). The ADD-2 "GameBoard `fateData` prop" concern is **DISMISSED with evidence**: `GameBoard.tsx:202` declares `fateData?: FateStatePayload | null`, line 430 gates the fate-conflict tab on it, GameBoard.tsx is **not** in this diff (pre-existing 118-2/118-6), and the wiring test passed GREEN in preflight — the board→surface path mounts.
- [VERIFIED] OTEL fail-loud discipline: `refuse_compel` spends-then-emits (`fate.py`), so a 0-FP refusal raises `FateEconomyError` before `fate.compel.refused` fires; `resolve_compel` raises `FateConflictError` on a phantom compel before any mutation. Both proven by tests. The lie-detector sees a real decline, never a phantom one.

### Rule Compliance

Per-rule verdict (cross-referenced with reviewer-rule-checker's exhaustive pass):
- **PY #1 silent-exceptions** — compliant (all error paths raise; no try/except in changed lines).
- **PY #2 mutable-defaults** — compliant (None / immutable scalars; list fields use `Field(default_factory=list)`).
- **PY #3 type-annotations** — compliant (all new public functions/fields annotated; test helpers exempt).
- **PY #4 logging/OTEL** — compliant (OTEL-native; the new `fate.compel.refused` span + route registered + exported).
- **PY #6 test-quality** — compliant for what exists; **gap** = missing phantom-refuse + resolved-guard negatives (above).
- **PY #11 input-validation** — compliant (`extra: forbid` models; authenticated actor; pydantic Literal).
- **No Silent Fallbacks (SOUL/critical)** — compliant in code (refuse-at-0 + phantom both fail loud); one **comment** overclaims (fate_tools.py, [SILENT] above).
- **No Stubbing (critical)** — **VIOLATION**: `offered_delta` dead field (above).
- **TS #1 type-escapes / #8 test-quality** — compliant (no `as any`).
- **TS #4 null/undefined** — compliant (`pending_compels ?? []`, correct `??` not `||`).
- **TS #6 react keys / handlers** — keys compliant (`key={c.aspect}`, stable); inline-handler LOW note (above).
- **ADR-144 bind-don't-balance** — compliant (SRD-fixed ±1 via atomic mutators).
- **OTEL Observability (critical)** — compliant (accepted/refused spans, validate-before-emit).

### Devil's Advocate

Assume this is broken. **Cross-seat abuse:** in MP, PC-B clicks Accept on a compel offered to PC-A. Does PC-B steal a fate point? No — `resolve_compel` calls `find_pending_compel(target=actor_name, ...)` where `actor_name` is the *authenticated* clicker (handler `sd.player_id` → seat → name, with the 118-8 spoof guard), so PC-B finds no compel on that aspect targeting *them* → `FateConflictError`. Firewall holds. **Double-accept / replay:** PC-A clicks Accept twice (lag). First call consumes the compel (`remove_pending_compel`); the second finds nothing → raises (no double fate point). Good. **Empty aspect_text:** `find_pending_compel(aspect="")` → no match → raise. Good. **Mid-turn resolution:** a compel is offered, then the conflict resolves the same turn — does a stale compel surface? No: the projection gates the entire `conflict` block on `not enc.resolved`, so a resolved conflict drops `pending_compels` wholesale. Good. **The real soft spots:** (1) the `offered_delta` field is dead and its docstring lies — worse, the UI's "+1 FP" is a *hardcoded literal*, so if a future variable-reward compel sets `offered_delta=2`, the player is shown "+1" while the engine grants the real amount — a quiet narration-vs-mechanics divergence, exactly the El Dorado lie OTEL exists to catch. That is why I require wiring the real delta, not just deleting the field. (2) The `find_pending_compel` exact-aspect match silently leaks a second same-aspect compel — narrow, but it's an unbounded `list` with no de-dupe; a buggy narrator that re-offers the same aspect grows the list and surfaces duplicate controls. (3) The wiring-test docstring claims an App→GameBoard link it never exercises — a confused maintainer trusts a green test that doesn't cover what it says. None of these is data corruption, but two are honesty defects, which this project rejects on principle.

**Handoff:** Back to Dev (Naomi Nagata) — green rework (the gate's reviewer-verdict recovery routes a rejection to `green`, max 3 attempts). Dev wires `offered_delta` through to the UI, trims the overclaiming docstrings, fixes the `fate_tools` comment, and adds the two missing negatives (phantom-refuse + resolved-guard) as part of the fix.

## Delivery Findings

No upstream findings.

### TEA (test design)
- **Improvement** (non-blocking): This story surfaces compels ONLY inside an active Fate conflict (the control is gated on `FATE_STATE.conflict.pending_compels` per Keith's resolved carrier decision). Fate compels can be offered in any scene, not just conflicts — a compel offered with no active conflict has no surface here. Affects `sidequest-ui/src/components/FateConflictSurface.tsx` + `sidequest-server/.../fate_projection.py` (a non-conflict compel surface would be a follow-up). *Found by TEA during test design.*
- **Question** (non-blocking): `offer_compel`'s new `encounter` parameter should be **optional** so an offer made with no active conflict still fires `fate.compel.offered` (existing F2b behavior, exercised by `tests/agents/tools/test_fate_compel_tool.py`) and persists only when a conflict exists. Adding a *required* encounter param would break the existing F2b offered-span test. Affects `sidequest-server/sidequest/game/ruleset/fate.py::offer_compel` + the `propose_fate_compel` tool. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking, project-level): `develop` is RED independent of 118-5 — a full server suite run shows ~85 failures in the in-flight epic-108 / ADR-143 WWN-combat rework (`committed_blow` unknown-beat in `downed_seam`, `test_102_4_wn_sealed_round`, `test_108_*`) plus `tests/protocol/test_enums.py::test_message_type_complete_count` (57≠56 — message-type enum drift). PROVEN pre-existing: all reproduce on the clean merge-base `0364ee06` in a throwaway worktree; my diff touches no WN/enum/downed-seam files. Not fixable within a Fate-compel story. Affects the WWN-combat path + `sidequest/protocol/enums.py` count test — needs the owning epic. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the post-compel FP change + cleared compel surface to the client on the existing per-turn `_maybe_emit_fate_state` cadence (consistent with the invoke flow), not via an immediate push from `FateActionHandler`. The resolved ±1 is shown immediately on the control's static label; the new TOTAL updates next cadence. An immediate FATE_STATE re-emit after a compel resolves would tighten feedback. Affects `sidequest/handlers/fate_action.py`. *Found by Dev during implementation.*
- No new upstream findings from the green-rework (round-trip 1): the four blocking + two non-blocking Reviewer findings were addressed directly; no further gaps surfaced. *Found by Dev during green-rework.*

### Reviewer (code review)
- **Gap** (blocking): `PendingCompel.offered_delta` is stored (per AC-1) but never projected or read; the UI hardcodes "+1 FP"/"−1 FP" labels — a hardcoded delta can silently diverge from the SRD/engine (the El Dorado lie OTEL guards against). Affects `sidequest-server/sidequest/game/encounter.py` + `fate_projection.py` + `sidequest/protocol/models.py` + `sidequest-ui/.../FateConflictSurface.tsx` + `src/types/payloads.ts` (wire `offered_delta` through `FatePendingCompel` and render the real value). *Found by Reviewer during code review.*
- **Gap** (blocking): overclaiming wiring-test docstring asserts an `App → GameBoard` path the test never renders. Affects `sidequest-ui/.../GameBoard/__tests__/GameBoard-fate-compel-wiring.test.tsx` (trim the claim or mount `<App>`). *Found by Reviewer during code review.*
- **Gap** (blocking): missing fail-loud negatives — phantom-refuse and the `not encounter.resolved` persistence guard. Affects `sidequest-server/tests/server/dispatch/test_fate_compel_roundtrip.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `fate_tools.py` "no silent state loss" comment overclaims (a `None` `ctx.snapshot` during a live conflict would drop a persistable offer); restate to name both `None` origins. Affects `sidequest-server/sidequest/agents/tools/fate_tools.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): once `offered_delta` is wired, the refuse-at-0 tests should also assert `fate.fate_point.delta` absent, and the UI ±1 assertions should target a `data-testid` delta value, not button prose. Affects the test files. *Found by Reviewer during code review.*
- **Gap** (blocking — project-level, NOT 118-5): `tests/server/test_fate_action_handler_wiring.py::test_handler_drives_dispatch_end_to_end` is FLAKY under parallel (`-n auto`) execution — 3 consecutive runs alongside the roundtrip suite gave fail/pass/pass; passes in isolation every time. The assertion `enc.find_actor("Thug").withdrawn is True` is RNG-outcome-dependent (the handler uses `random.Random()` with no fixed seed, `fate_action.py:118`) and order/parallel-sensitive. File is untouched by this branch (last commit 118-7 `2ebafaf7`). Affects `sidequest-server/tests/server/test_fate_action_handler_wiring.py` (seed the RNG deterministically or isolate the worker state) — owning area is 118-7 / epic-108, not this story. *Found by Reviewer during code review (re-review).*
- **Improvement** (non-blocking): `FateDispatchResult.fate_point_delta` (`fate_conflict.py:731/795`, original-green field, untouched by the rework) is asserted in tests but has no PRODUCTION consumer — `fate_action.py` returns `[]` on compel paths without reading it; the player observes the delta via the static control labels (`+{offered_delta}` / SRD −1) and the next FATE_STATE re-emit. Its docstring ("Lets the player surface show the mechanical outcome inline") slightly overclaims a direct wire that does not exist. Either route it through an immediate response message (the AC-3 inline-tightening Dev already flagged round 1) or soften the docstring to name the cadence+label surfacing. Affects `sidequest-server/sidequest/server/dispatch/fate_conflict.py`. *Found by Reviewer during code review (re-review).*
- **Improvement** (non-blocking): test-strengthening from test-analyzer — (a) the two phantom tests could also assert `enc.pending_compels == []` (no side-effect compel created); (b) the resolved-encounter test could also assert `build_fate_state_payload` drops the resolved conflict (pins both guards, not just the persistence half); (c) `GameBoard-fate-compel-wiring.test.tsx` uses sync `queryByRole` for the Fate Conflict tab — fine today (the `expect(tab).toBeInTheDocument()` guards the vacuous case), but `findByRole` would be robust if the tab mount ever goes async. Affects the test files. *Found by Reviewer during code review (re-review).*

## Design Deviations

No deviations from spec.

### TEA (test design)
- **Compel identified by `aspect_text`, not a dedicated `compel_id`**
  - Spec source: .session/118-5-session.md, AC-1
  - Spec text: "the engine stores a PendingCompel data structure with compel id, character name, aspect text, and the offered fate point delta"
  - Implementation: Accept/Refuse reference the compel via the existing `FateActionPayload.aspect_text` field; the tests do not pin a `compel_id` on the wire (no id field exists on the payload, and adding one is heavier than the round-trip needs).
  - Rationale: A PC realistically has at most one pending compel per aspect at a time, so `aspect_text` is a sufficient discriminator; reuses the existing payload field ("wire up what exists") instead of growing the protocol.
  - Severity: minor
  - Forward impact: If a design ever allows two simultaneous compels on the SAME aspect for one PC, `aspect_text` becomes ambiguous and a `compel_id` would be needed — out of scope here.

### Dev (implementation)
- **UI `pending_compels` is OPTIONAL, while the server projection field is required-with-default**
  - Spec source: TEA tests + `sidequest-server/sidequest/protocol/models.py` (FateConflictEntry.pending_compels required, default_factory)
  - Spec text: the server always emits `pending_compels` (default empty); the TEA UI fixtures build it explicitly.
  - Implementation: typed `FateConflictEntry.pending_compels?` OPTIONAL on the UI mirror; the component reads `conflict.pending_compels ?? []`.
  - Rationale: additive wire field — optional keeps every pre-F3e fixture/payload (e.g. the existing `FateConflictSurface.test.tsx` / `GameBoard-fate-tab.test.tsx` conflict objects) type-valid without edits; the server still always populates it. Making it required would break `tsc` on out-of-story fixtures for no runtime benefit.
  - Severity: minor
  - Forward impact: none — the server contract is unchanged; consumers must `?? []` (the component does).
- **Repaired an out-of-story pre-existing-red test (`test_fate_unaffordable_invoke_handler_118_6.py`)**
  - Spec source: project doctrine (CLAUDE.md "no half-wired / suite green at handoff"; tea-gotchas "no pre-existing excuse")
  - Spec text: the suite must be green at handoff; don't dismiss broken tests as pre-existing.
  - Implementation: 118-7 (F3g roll broadcast) changed `FateActionHandler` to broadcast the roll via `sd._room` and return `[]`, but the 118-6 test `_fate_session` mock never added `_room` and still asserted `len(out)==1`. Added a capturing `_room` double and updated the assertion to the post-118-7 broadcast contract (returns `[]`, broadcasts one `FateRollMessage`).
  - Rationale: the fate suite I'm handing off must be green; this stale test sat squarely in the Fate path I touched. The fix encodes 118-7's own documented intent ("must NOT also return the message"), not new behavior.
  - Severity: minor
  - Forward impact: none — test-only; the 85 WWN-combat + enum failures are a separate epic (see Delivery Findings) and out of scope.
- **`offered_delta` wired as a REQUIRED UI field; engine grant kept SRD-fixed (green-rework, round-trip 1)**
  - Spec source: Reviewer Assessment severity table, [HIGH][DOC][SIMPLE] finding
  - Spec text: "WIRE it through: add `offered_delta` to `FatePendingCompel` (server + ui), project it, render `+{offered_delta}` on Accept (refuse is SRD-fixed −1)."
  - Implementation: Made `FatePendingCompel.offered_delta` REQUIRED (`offered_delta: number`) on the UI type — matching its required siblings `aspect`/`target`/`reason` — NOT the optional additive convention used for the `pending_compels` LIST (the accepted Dev deviation above); updated the two UI fixtures + their local `PendingCompel` types accordingly. Accept renders `+{c.offered_delta}`; Refuse keeps the SRD-fixed `−1` literal (no stored field). `accept_compel` was NOT changed to read `offered_delta` — it stays the SRD-fixed +1 via `earn_fate_point`; `offered_delta` defaults to that same +1 at the single creation site (`add_pending_compel` exposes no override), so display, stored field, and grant agree by construction.
  - Rationale: (a) `offered_delta` is a field of the F3e-native `FatePendingCompel` whose siblings are all required, so required is consistent — the accepted optional convention concerned adding `pending_compels` to the PRE-EXISTING `FateConflictEntry` (a back-compat case that does not apply to a field born required inside a new type). Required also eliminates a `?? 1` fallback literal — the cleanest answer to an honesty rejection. (b) Keeping the engine grant SRD-fixed honors ADR-144 "bind don't balance"; making `accept_compel` read a variable `offered_delta` would convert an SRD constant into a homebrew tunable.
  - Severity: minor
  - Forward impact: a future variable-reward compel would set `offered_delta` at the `offer_compel`/`add_pending_compel` site AND have `accept_compel` grant it; today both are pinned to the SRD +1 so the field cannot diverge from the grant. Any new UI fixture constructing a `FatePendingCompel` must include `offered_delta`.

### Reviewer (audit)
- **TEA: Compel identified by `aspect_text`, not `compel_id`** → ✓ ACCEPTED by Reviewer: sound — reuses the existing payload field ("wire up what exists"); the only consequence (a 2nd same-aspect compel to the same PC is unreachable) is the [EDGE][LOW] note above and acceptable for the realistic case.
- **Dev: UI `pending_compels` OPTIONAL vs server required-with-default** → ✓ ACCEPTED by Reviewer: correct additive-field convention; keeps pre-F3e fixtures type-valid; the component's `?? []` handles it; server contract unchanged.
- **Dev: Repaired the pre-existing-red 118-6 invoke test** → ✓ ACCEPTED by Reviewer: the repair encodes 118-7's documented broadcast contract (broadcast + return `[]`), not new behavior; the test now asserts a meaningful three-part contract (`out == []`, one broadcast, `FateRollMessage`) — not vacuous. Fixing a stale test in the Fate path being touched is in-bounds, and the proof that the 85 WWN/enum failures are a separate pre-existing epic was rigorous (base-worktree reproduction).
- **UNDOCUMENTED (Reviewer-spotted):** AC-1 lists "the offered fate point delta" as a stored field; Dev added `PendingCompel.offered_delta` to satisfy it but never projected or read it (UI hardcodes ±1). This is the blocking [DOC][HIGH] finding above — the field half-satisfies AC-1 (stored) while violating AC-3's intent (the shown delta must be the real value). Not a logged deviation; flagged as a finding, not accepted.
- **Dev (green-rework): `offered_delta` wired as a REQUIRED UI field; engine grant kept SRD-fixed** → ✓ ACCEPTED by Reviewer (re-review): sound on both axes. (a) REQUIRED on the UI `FatePendingCompel` is the *consistent* choice — its siblings `aspect`/`target`/`reason` are all required, and the previously-accepted optional convention applied to adding `pending_compels` onto the PRE-EXISTING `FateConflictEntry`, a back-compat case that does not apply to a field born required inside a new type. Verified no out-of-story fixture breaks (`tsc --noEmit` clean; only the two updated test files construct `pending_compels`, both carry `offered_delta`). Required avoids a `?? 1` fallback literal — strictly more honest. (b) Keeping the engine grant SRD-fixed (earn/spend_fate_point at ±1, `offered_delta` display-only and pinned to +1 with no `add_pending_compel` override) is correct per ADR-144 — making `accept_compel` read a variable `offered_delta` would have converted an SRD constant into a homebrew tunable. rule-checker PROJ-3 confirms no variable economy was introduced.

## Dev Assessment — Green Rework (round-trip 1)

**Implementation Complete:** Yes — all 4 blocking + both flagged non-blocking findings addressed.

**Findings resolved:**
- **[HIGH][DOC][SIMPLE] dead/lying `offered_delta`** → WIRED end-to-end. `FatePendingCompel` gains `offered_delta` (server `protocol/models.py` + ui `payloads.ts`); `fate_projection.py` projects `c.offered_delta`; the Accept control renders `+{c.offered_delta}` (real server datum, not a hardcoded literal). Refuse keeps the SRD-fixed `−1` (no stored field — one cost, never variable). Engine grant left SRD-fixed +1 (ADR-144 bind-don't-balance); `offered_delta` defaults to that +1 at the single creation site, so display/field/grant agree by construction (logged as a Dev deviation). Docstrings on `PendingCompel` + `FatePendingCompel` corrected to describe the now-real wiring.
- **[HIGH][DOC] overclaiming wiring-test docstring** → trimmed. `GameBoard-fate-compel-wiring.test.tsx` now claims only the GameBoard→FateConflictSurface path it actually exercises; names App.tsx:2727→GameBoard.tsx:644 as the remaining untested seam (test injects `onFateAction` as a prop, does not mount `<App>`). Stale "FAIL today / (RED)" removed.
- **[MEDIUM][TEST] phantom-refuse untested** → added `test_refusing_a_compel_that_was_never_offered_fails_loud` (fp=1 isolates the phantom guard from the refuse-at-0 economy path; asserts `FateConflictError`, FP unchanged, no `fate.compel.refused` span).
- **[MEDIUM][TEST] resolved-encounter guard untested** → added `test_offer_on_a_resolved_encounter_fires_span_but_persists_nothing` (`enc.resolved=True` → `fate.compel.offered` span fires, `enc.pending_compels == []`).
- **[SILENT][MEDIUM] `fate_tools.py` comment** → restated to name both `None`-snapshot origins and flag the live-conflict drop as a wiring bug to investigate, not a benign default.
- **[DOC][LOW] `offer_compel` docstring** → states the explicit `not encounter.resolved` guard (None vs resolved both skip persistence).

**Files Changed (server):**
- `sidequest/protocol/models.py` — `FatePendingCompel.offered_delta` + docstring.
- `sidequest/game/ruleset/fate_projection.py` — project `offered_delta`.
- `sidequest/game/encounter.py` — `PendingCompel.offered_delta` docstring (now-true wiring).
- `sidequest/game/ruleset/fate.py` — `offer_compel` docstring (explicit guard).
- `sidequest/agents/tools/fate_tools.py` — `None`-origin comment honesty fix.
- `tests/server/dispatch/test_fate_compel_roundtrip.py` — 2 new negative tests.

**Files Changed (ui):**
- `src/types/payloads.ts` — `FatePendingCompel.offered_delta` (required) + docstring.
- `src/components/FateConflictSurface.tsx` — Accept renders `+{c.offered_delta}`; comment updated.
- `src/components/__tests__/FateConflictSurface.compel.test.tsx` — fixtures + local type carry `offered_delta`.
- `src/components/GameBoard/__tests__/GameBoard-fate-compel-wiring.test.tsx` — docstring trimmed; fixture + local type carry `offered_delta`.

**Tests:** GREEN (re-verified via Engineering Console).
- Server: compel files **13 passed** (incl. 2 new negatives); full Fate suite **422 passed, 1 skipped**; ruff + ruff format + pyright clean on changed files.
- UI: 2 compel files **10 passed**; Fate component regression **59 passed**; `tsc --noEmit` clean; eslint clean on changed files.
- Pre-existing red (85 WWN-combat + enum-count, epic-108) unchanged and untouched — see Delivery Findings.

**Branch:** `feat/118-5-fate-compel-accept-refuse` (both subrepos).

**Handoff:** Back to Reviewer (Chrisjen Avasarala) for re-review.

---

## Subagent Results

(Re-review, round-trip 1. Subagent toggles unchanged: 4 enabled, 5 disabled-via-settings and self-assessed.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (+ green) | compel 13/13 green, lint/types/format clean, 0 smells; flagged 1 fate-suite failure → I investigated → confirmed FLAKY pre-existing 118-7 test (not 118-5), captured as delivery finding |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed ([SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | all LOW/MEDIUM; VERIFIED the 2 new negatives + display + wiring tests are real (non-vacuous); 3 strengthening suggestions → non-blocking delivery findings |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 actionable | ALL 4 prior findings VERIFIED FIXED (HIGH×2, MEDIUM, LOW); 1 LOW residual (test-CASE name "(production path)" shorthand) → noted, non-blocking; no new misleading comments |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-assessed ([TYPE]) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — self-assessed ([SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-assessed ([SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 2 | 26 rules / 71 instances; 1 LOW (PY-10 pre-existing `__all__` gap, whole-package pattern, not this diff), 1 INFORMATIONAL (`fate_point_delta` intent — verified non-blocking, see below); CONFIRMED offered_delta wired, UI required-field consistent, ADR-144 no variable economy, PY-6 test quality clean |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled and self-assessed)
**Total findings:** 0 confirmed blocking, 7 confirmed non-blocking (3 delivery findings + 4 LOW notes), 0 dismissed without rationale

## Reviewer Assessment

**Verdict:** APPROVED

This is the re-review of the green-rework (round-trip 1). All four of my prior blocking findings are genuinely fixed — verified independently by the comment-analyzer (HIGH confidence on all four), the rule-checker (offered_delta CONFIRMED WIRED end-to-end), the test-analyzer (both new negatives VERIFIED real), and my own line-level tracing. No new Critical/High issue was introduced. The remaining items are all non-blocking and captured as delivery findings.

**Prior findings — re-verified fixed:**

| Prior finding | Status | Evidence |
|---|---|---|
| [HIGH][DOC][SIMPLE] dead/lying `offered_delta` | ✅ FIXED | Wired end-to-end: `PendingCompel.offered_delta` (encounter.py:204, default 1) → `fate_projection.py:162` projects `c.offered_delta` → `FatePendingCompel` wire field → `FateConflictSurface.tsx:220` renders `Accept (+{c.offered_delta} FP)`. No hardcoded literal; Refuse keeps the SRD-fixed −1 (no stored field, so no divergence vector). Docstrings on `PendingCompel`/`FatePendingCompel`/payloads.ts now accurately describe the wiring. |
| [HIGH][DOC] overclaiming wiring-test docstring | ✅ FIXED | `GameBoard-fate-compel-wiring.test.tsx` block comment now claims ONLY the GameBoard→FateConflictSurface path it renders and names App.tsx:2727→GameBoard.tsx:644 as the remaining untested seam. comment-analyzer HIGH-confidence VERIFIED. |
| [MEDIUM][TEST] phantom-refuse untested | ✅ FIXED | `test_refusing_a_compel_that_was_never_offered_fails_loud` — fp=1 isolates the phantom path; asserts `FateConflictError`, FP unchanged, no `fate.compel.refused` span. Non-vacuous (rule-checker PY-6 clean). |
| [MEDIUM][TEST] resolved-encounter guard untested | ✅ FIXED | `test_offer_on_a_resolved_encounter_fires_span_but_persists_nothing` — span fires, `pending_compels == []`. Pins the `not encounter.resolved` guard. |
| [SILENT][MEDIUM] `fate_tools.py` comment | ✅ FIXED | Now names both `None`-snapshot origins and flags the live-conflict drop as a wiring bug, not benign (cites No Silent Fallbacks). |
| [DOC][LOW] `offer_compel` docstring | ✅ FIXED | States the explicit `not encounter.resolved` guard verbatim. |

**Observations (tagged; ≥5):**

- [DOC][VERIFIED] `offered_delta` is read in production end-to-end — `fate_projection.py:162` (server) and `FateConflictSurface.tsx:220` (UI). No longer dead, docstrings honest. Confirmed by comment-analyzer + rule-checker PROJ-2 + my trace.
- [TEST][VERIFIED] The two new negatives are real and non-vacuous; the `offered_delta` display test now exercises the data path (fixture carries `offered_delta:1`, component renders `+{c.offered_delta}`); the wiring test is behavioral (renders real GameBoard, clicks Accept, asserts `onFateAction`), not a source-grep.
- [RULE][VERIFIED] ADR-144 bind-don't-balance holds — `offered_delta` is display-only, pinned to the SRD +1 (no `add_pending_compel` override); `earn_fate_point`/`spend_fate_point` are SRD-fixed ±1; no homebrew tunable (rule-checker PROJ-3 CLEAN).
- [SILENT][VERIFIED] refuse-at-0 and phantom both fail loud before any mutation; validate-before-emit holds (no span on a rejected refusal). rule-checker PROJ-4 clean.
- [TYPE][VERIFIED] `offered_delta`: `int = 1` (server, default) / `number` required (UI). `extra:forbid` holds; no `as any`. The UI required-field is consistent with its siblings (aspect/target/reason); `tsc --noEmit` clean and no out-of-story fixture breaks (only the two updated test files construct `pending_compels`, both carry the field).
- [SEC][VERIFIED] `offered_delta` is a server-sourced int rendered in a label — no injection surface. The compel firewall (`resolve_compel` keys `find_pending_compel` on the authenticated `actor_name`) is unchanged from round 1 — a client can only resolve a compel targeting its own authenticated actor.
- [SIMPLE][VERIFIED] Minimal rework; the required UI field avoids a `?? 1` fallback literal; Dev correctly did NOT make `accept_compel` read `offered_delta` (that would over-engineer + violate ADR-144).
- [EDGE] `find_pending_compel` exact `(target, aspect)` match — a 2nd compel on the SAME aspect to the SAME PC is unreachable (round-1 LOW note, unchanged; acceptable for the realistic one-compel-per-aspect case).
- [TEST][LOW] (non-blocking) `FateDispatchResult.fate_point_delta` is computed + test-asserted but not consumed by the production handler — see Delivery Findings. Materially different from the offered_delta dead-field: it is a computed return value (not a dead store), it is read by tests, the player-facing delta IS surfaced via labels + cadence, and it is original-green code the rework did not touch (and which I VERIFIED in round 1).

**Data flow traced:** narrator `propose_fate_compel` → `offer_compel(encounter)` persists `PendingCompel(offered_delta=1)` on the active conflict → `build_fate_state_payload` projects `FatePendingCompel(offered_delta=1)` onto FATE_STATE → UI renders `Accept (+1 FP)` from `c.offered_delta` → player clicks → `onFateAction({action:"compel_accept", aspect_text})` → `FATE_ACTION` → `FateActionHandler` → `dispatch_fate_action` → `resolve_compel` (`find_pending_compel` keyed on authenticated actor → `accept_compel` earns SRD +1, fires `fate.compel.accepted`, consumes the compel) → next cadence re-emits FATE_STATE with the updated total and the compel gone. Safe: economy is server-authoritative, fails loud on phantom/refuse-at-0, every step emits its OTEL span.

### Devil's Advocate

Assume the rework is broken. **Did Dev just move the dead field instead of wiring it?** No — I traced `offered_delta` to two live readers (projection + JSX) and a grep confirms no other UI constructor exists; the field is genuinely consumed. **Did making the UI field required break an out-of-story fixture?** That was my top suspicion — a required field can silently break sibling fixtures that `tsc` would catch. I grepped every `pending_compels`/`FatePendingCompel` reference: only the two updated test files construct compels and both carry `offered_delta`; the surface only reads it; preflight's `tsc --noEmit` is clean. No breakage. **Is the displayed delta still capable of lying?** Display reads `offered_delta` (default 1), the engine grants SRD +1 via `earn_fate_point`, and `add_pending_compel` exposes no override — so display/field/grant agree by construction; a future caller would have to edit code to diverge them. **Could the new "fixed" docstrings overclaim again?** comment-analyzer swept them HIGH-confidence and found them accurate; the only residual is a test-CASE name's `(production path)` shorthand (the block comment is correct) — LOW. **Is the flaky fate test mine?** Decisively not: it passes in isolation, fails ~1/3 in parallel, lives in a file with zero commits on this branch (118-7), and my diff touches none of the exchange/RNG path. **Is `fate_point_delta` the same sin as `offered_delta`?** It is computed-but-unread-in-production, which I scrutinized hard. But it differs: it is a return value (not dead storage), it has test consumers, the player-facing delta is surfaced via the now-correct labels + the FATE_STATE re-emit, and it is original-green code I already verified — not introduced or touched by this rework. Its only blemish is a slightly aspirational docstring, captured as a non-blocking improvement. None of these rise to Critical/High. The rework did exactly what I demanded, honestly.

**Handoff:** To SM (Camina Drummer) for finish-story.