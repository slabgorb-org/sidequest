---
story_id: "73-3"
jira_key: ""
epic: "73"
workflow: "tdd"
---
# Story 73-3: advance_confrontation lost-update — route through canonical snapshot, not a fresh load/save that the end-of-turn save clobbers

## Story Details
- **ID:** 73-3
- **Jira Key:** (not set)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-30T23:35:06Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30T21:48:44Z | 2026-05-30T21:50:06Z | 1m 22s |
| red | 2026-05-30T21:50:06Z | 2026-05-30T21:57:52Z | 7m 46s |
| green | 2026-05-30T21:57:52Z | 2026-05-30T22:00:57Z | 3m 5s |
| review | 2026-05-30T22:00:57Z | 2026-05-30T23:33:29Z | 1h 32m |
| spec-reconcile | 2026-05-30T23:33:29Z | 2026-05-30T23:35:06Z | 1m 37s |
| finish | 2026-05-30T23:35:06Z | - | - |

## Sm Assessment

Story 73-3 selected from Epic 73 (Confrontation Engine Hardening) at the user's
direction — a state-coherence **bug**, prioritized over the larger 73-1 feature work
because a dial that silently reverts is worse than a missing one. Context document
(`sprint/context/context-story-73-3.md`) is complete and authoritative: it diagnoses
the root cause (`advance_confrontation` does a read-modify-write against a fresh
`repository.load()` snapshot that the end-of-turn canonical save clobbers), names the
reference seam that works (`apply_beat` mutates the canonical in-turn snapshot), and
prescribes the fix shape (thread `context.snapshot` onto `ToolContext` at
`orchestrator.py:3853`, mutate the canonical encounter metric, drop the redundant
in-tool save). Five derived ACs (AC1 lost-update regression, AC2 canonical mutation /
fail-loud, AC3 sequential composition, AC4 advance+resolve, AC5 OTEL truth) plus edge
cases (negative delta, mixed-axis, end-of-turn resolution).

**Routing:** tdd workflow, phased → TEA owns the RED phase. Scope is server-only
(`sidequest-server`), no protocol/UI/ADR/content changes. Honor CLAUDE.md guards:
No Silent Fallbacks (fail loud if canonical snapshot absent on context — no quiet
`repository.load()` fallback), Wire Up What Exists (the canonical snapshot already
lives on `TurnContext.snapshot` and is plumbed to the ToolContext construction site —
this is a wiring fix, not new persistence machinery), and the OTEL lie-detector
principle (the span must report a delta that actually persists, not the doomed write).

**Test discipline:** assert behavior + OTEL spans, never source text. The load-bearing
assertion is load-after-canonical-save equals `before + N` — a test that checks only
the tool's return payload would pass against the buggy code.

## TEA Assessment

**Tests Required:** Yes
**Reason:** State-coherence bug fix with five behavioral ACs and a fail-loud contract — squarely test-driven.

**Test Files:**
- `tests/agents/tools/test_advance_confrontation.py` — rewritten to thread the canonical
  snapshot onto `ToolContext` and assert persistence *after* a simulated end-of-turn
  canonical save (the production ordering that exposes the lost-update).

**Tests Written:** 21 tests total (1 pre-existing registration test untouched; 13 existing
tests migrated to the canonical-snapshot contract; 7 new Story-73-3 AC tests).
**Status:** RED (20 failing, 1 passing — ready for Dev).

### RED verification

`uv run pytest tests/agents/tools/test_advance_confrontation.py -n0 -v` →
**1 passed, 20 failed.** All 20 failures share the root cause
`TypeError: ToolContext.__init__() got an unexpected keyword argument 'snapshot'` —
the canonical-snapshot seam does not exist yet. This is the *outer* RED layer.

**Layered RED (important for Reviewer):** the behavioral assertions sit beneath the
construction error. Once Dev adds the `snapshot` field but *before* changing the
mutation target, the following still fail by design — the tests drive behavior, not
just field presence:
- AC1 (`test_advance_survives_end_of_turn_canonical_save`): tool mutates a fresh
  `load()` copy → canonical `snap` untouched → `store.save(snap)` clobbers → reload
  shows `before`, not `before+N`.
- AC2 (`test_mutates_canonical_snapshot_in_place`): the canonical object instance is
  never mutated by the fresh-load path.
- AC2 (`test_missing_canonical_snapshot_fails_loud_no_repo_fallback`): a `load()`
  fallback would *succeed* instead of failing loud.
- AC3 / AC5: composition + `tool.confrontation.canonical` signal absent on the
  fresh-load path.

### AC → test map

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 dial survives end-of-turn save | `test_advance_survives_end_of_turn_canonical_save`, `test_negative_advance_survives_end_of_turn_canonical_save`, `test_advance_player_axis_positive_delta`, `test_advance_opponent_axis_negative_delta` | failing |
| AC2 mutate canonical in-place | `test_mutates_canonical_snapshot_in_place` | failing |
| AC2 fail-loud, no silent `load()` fallback | `test_missing_canonical_snapshot_fails_loud_no_repo_fallback`, `test_no_encounter_returns_fatal_error` | failing |
| AC3 sequential composition (same + mixed axis) | `test_sequential_same_axis_advances_compose`, `test_sequential_mixed_axis_advances_both_persist`, `test_parallel_advance_against_same_session_runs_sequentially` | failing |
| AC4 advance + resolve same turn | `test_advance_and_resolve_same_turn_both_persist` | failing |
| AC5 OTEL persisted delta + canonical signal | `test_otel_reports_canonical_persisted_delta`, `test_otel_attrs_set_on_success` | failing |

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|---------------------------|---------|--------|
| #1 No silent fallback (fail loud) | `test_missing_canonical_snapshot_fails_loud_no_repo_fallback` | failing |
| #3 Typed boundary field | contract pins `ToolContext.snapshot: GameSnapshot \| None` (Dev types it) | n/a (impl) |
| #6 Test quality (meaningful assertions) | self-check: all tests assert concrete dial values / status enums; no `assert True`, no bare truthy | pass |

**Rules checked:** 3 of 13 lang-review rules applicable to this internal state-coherence fix have coverage (the rest — path handling, deserialization, security input, deps, resource leaks — are not engaged by this change).
**Self-check:** 0 vacuous tests found.

### Implementation contract for Dev (tests are the spec)

1. Add `snapshot: GameSnapshot | None = None` to `ToolContext` (`tool_registry.py`,
   the frozen/slots dataclass — append as the last optional field).
2. Thread it at the construction site (`orchestrator.py:~3911`, right after
   `genre_pack=context.pack`): `snapshot=context.snapshot`.
3. In `advance_confrontation.py`: replace `session = ctx.repository.load()` /
   `snapshot = session.snapshot` with the canonical `ctx.snapshot`. If `ctx.snapshot
   is None` → `return ToolResult.error("...", recoverable=False)` (NO `repository.load()`
   fallback). Preserve the `encounter is None` fatal guard. **Delete** the tool's
   `ctx.repository.save(snapshot)` — the end-of-turn canonical save is the single
   persistence point.
4. Add `ctx.otel_span.set_attribute("tool.confrontation.canonical", True)` to the OTEL block.

**Handoff:** To Puck (Dev) for GREEN.

## Dev Assessment

**Status:** GREEN — implementation complete, pushed.

**Branch:** `feat/73-3-advance-confrontation-lost-update` (pushed to origin).
**Commits:** `aa4617df` (RED tests, TEA) · `<green>` feat(73-3) implementation.

**Files changed (3, server-only):**
- `sidequest/agents/tool_registry.py` — added `snapshot: GameSnapshot | None = None`
  to `ToolContext` (last optional field; `GameSnapshot` added to the `TYPE_CHECKING`
  import block).
- `sidequest/agents/orchestrator.py` — threaded `snapshot=context.snapshot` at the
  sole production `ToolContext(...)` construction site (`:3882`), right after
  `genre_pack=context.pack`.
- `sidequest/agents/tools/advance_confrontation.py` — mutate `ctx.snapshot.encounter`
  in place instead of `repository.load()`; fail loud (`ERROR_FATAL`) when
  `ctx.snapshot is None` (no `repository.load()` fallback); **removed** the in-tool
  `ctx.repository.save(snapshot)`; emit `tool.confrontation.canonical=True`. Docstring
  OTEL section updated.

**Wiring verification (not just existence):**
- Grep confirmed exactly ONE production `ToolContext(` construction site
  (orchestrator.py:3882) — now wired. No subsystem/dispatch path builds its own
  `ToolContext` for `advance_confrontation`, so the fix is fully wired, not half.
- `context.snapshot` (`TurnContext.snapshot`, orchestrator.py:867) is populated by
  `_build_turn_context` for live turns. If a path ever fails to populate it, the new
  guard fails LOUD (visible `ERROR_FATAL`) rather than silently reverting — strictly
  safer than the old behavior.
- The ToolContext field is additive (optional, default `None`) → backward compatible;
  442-test tool-suite regression sweep is green.

**Verification (GREEN):**
- `tests/agents/tools/test_advance_confrontation.py` — **21/21 pass**.
- `tests/agents/tools/` regression sweep — **442 pass, 0 fail**.
- `ruff check` (3 changed files) — clean.
- `pyright` (tool + registry) — 0 errors.

**OTEL (lie-detector):** the advance now mutates the canonical snapshot the
end-of-turn save persists, and `tool.confrontation.canonical=True` lets the GM panel
distinguish the durable path from the old doomed fresh-load path —
`tool.confrontation.value_after` now matches the persisted dial (AC5).

**Handoff:** To Portia (Reviewer) for code review.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings during implementation. The fix matched the context doc and
  TEA contract exactly; the canonical-snapshot seam (`TurnContext.snapshot` →
  `ToolContext.snapshot`) existed and only needed threading + a mutation-target swap.

### TEA (test design)
- **Improvement** (non-blocking): The pre-existing persistence tests encoded the
  *buggy* contract — they asserted `store.load()` reflected the mutation
  immediately after the tool call, which only passed because the tool did its own
  `repository.save()` of a doomed fresh copy. That assertion shape is precisely
  why the lost-update shipped undetected. Updated to assert
  load-*after*-canonical-save. Affects `tests/agents/tools/test_advance_confrontation.py`
  (already updated in this phase). *Found by TEA during test design.*
- **Question** (non-blocking): AC5 asserts the new OTEL signal as a
  `tool.confrontation.canonical` attribute on the dispatch span (same family as
  the existing `tool.confrontation.*` attrs the GM panel reads). The context doc
  also floats reusing `encounter_metric_advance_span`
  (`telemetry/spans/encounter.py:761`). If Dev/Architect prefer the dedicated
  span, the AC5 assertion must move with it. Affects
  `sidequest/agents/tools/advance_confrontation.py` (OTEL emit site).
  *Found by TEA during test design.*

### Reviewer (code review)
- **Gap** (non-blocking): 16 other WRITE tools — `apply_damage`, `apply_status`,
  `advance_encounter_beat`, `adjust_system_strain`, `advance_scene_clue`,
  `apply_spell_effect`, `apply_world_patch`, `commit_known_fact`, `commit_effort`,
  `long_rest`, `update_npc_disposition`, `tick_tropes`, `stabilize_mortal_injury`,
  `update_resource_pool`, `veterans_luck` — still use the exact
  `ctx.repository.load()` → mutate → `ctx.repository.save()` fresh-copy pattern that
  73-3 identifies as the lost-update anti-pattern. `PgSaveRepository.load()` →
  `load_snapshot()` (`sidequest/game/pg/snapshot.py:134-163`) re-reads `game_state`
  from Postgres and `json.loads()`-deserializes a **fresh** object every call — NOT
  the canonical `room._snapshot` the end-of-turn `room.save()` persists. Whether
  these 16 are latently broken (or are rescued by `narration_apply` re-applying
  their effects to canonical) needs a dedicated audit. Affects
  `sidequest/agents/tools/*.py` (WRITE category) — warrants a follow-up story under
  epic 73. Out of scope for 73-3, which is correctly scoped to advance_confrontation.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): No test asserts `ctx.repository.save` is *not*
  called in-tool on the success path. AC says "no in-tool save remains" but a
  re-introduced `ctx.repository.save(ctx.snapshot)` would persist the same canonical
  object and pass every round-trip test, so the regression guard is absent. Affects
  `tests/agents/tools/test_advance_confrontation.py` (add a `save.assert_not_called()`
  spy test). Production code is correct; this is test-coverage hardening only.
  *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Implemented the TEA contract exactly: field named
  `ToolContext.snapshot` (typed `GameSnapshot | None`), threaded
  `snapshot=context.snapshot` at the orchestrator construction site, mutated the
  canonical snapshot in place, deleted the in-tool `repository.save`, fail-loud
  (`ERROR_FATAL`) when `ctx.snapshot is None` with no `repository.load()`
  fallback, and emitted `tool.confrontation.canonical=True`.

### TEA (test design)
- **Pinned the canonical-snapshot field name as `ToolContext.snapshot`**
  - Spec source: context-story-73-3.md, "Technical Guardrails → The canonical-snapshot seam"
  - Spec text: "thread the canonical snapshot onto `ToolContext` (new field, mirroring the existing optional context fields) ... sourced from `context.snapshot`"
  - Implementation: tests construct `ToolContext(..., snapshot=canonical)` — the field is named `snapshot`, mirroring `TurnContext.snapshot` (orchestrator.py:867).
  - Rationale: `TurnContext` already calls it `snapshot`; matching the name keeps the construction-site thread-through symmetric (`snapshot=context.snapshot`, exactly like `genre_pack=context.pack`). Dev MUST name the field `snapshot` to satisfy the tests.
  - Severity: minor
  - Forward impact: Dev adds `snapshot: GameSnapshot | None = None` to `ToolContext` and `snapshot=context.snapshot` at the orchestrator.py:~3911 construction site.
- **Pinned the canonical OTEL signal as `tool.confrontation.canonical` (bool, on the dispatch span)**
  - Spec source: context-story-73-3.md, "OTEL (the lie-detector must now tell the truth)"
  - Spec text: "Surface that the mutation targeted the canonical snapshot (e.g. `tool.confrontation.canonical=true` / a `persisted_delta` ...)"
  - Implementation: tests assert `ctx.otel_span` records `tool.confrontation.canonical is True`, alongside the existing `tool.confrontation.*` attributes.
  - Rationale: keeps the new signal in the existing `tool.confrontation.*` family the GM panel already reads, rather than a separate span; minimal, refactor-stable contract. (See the non-blocking Question finding for the `encounter_metric_advance_span` alternative.)
  - Severity: minor
  - Forward impact: Dev calls `ctx.otel_span.set_attribute("tool.confrontation.canonical", True)`.

### Reviewer (audit)
- **TEA: Pinned the canonical-snapshot field name as `ToolContext.snapshot`** → ✓ ACCEPTED
  by Reviewer: matches the existing `TurnContext.snapshot` name, keeping the
  construction-site thread-through symmetric (`snapshot=context.snapshot`, exactly like
  `genre_pack=context.pack`). Sound, minimal, refactor-stable.
- **TEA: Pinned the canonical OTEL signal as `tool.confrontation.canonical` (bool, dispatch span)**
  → ✓ ACCEPTED by Reviewer: keeps the new signal in the `tool.confrontation.*` family
  the GM panel already reads rather than introducing a separate span. The
  comment-analyzer correctly notes the attribute is presence-only (always `True` on
  success, absent on the fail-loud path) — that is the right shape for a lie-detector
  signal and is captured as a LOW doc-wording finding, not a deviation reversal.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed against the diff —
  field named `snapshot`, threaded at the sole production construction site, canonical
  mutated in place, in-tool `repository.save` deleted, fail-loud on `None` with no
  `repository.load()` fallback, `tool.confrontation.canonical=True` emitted. Implementation
  matches the TEA contract exactly.
- No undocumented spec deviations found by Reviewer.

### Architect (reconcile)

**Existing entries verified:**
- **TEA — "Pinned the canonical-snapshot field name as `ToolContext.snapshot`"**: VERIFIED ACCURATE.
  Spec source `sprint/context/context-story-73-3.md` exists; the cited section "The
  canonical-snapshot seam" is at line 85, and the quoted spec text ("thread the canonical
  snapshot onto `ToolContext` … mirroring the existing optional context fields") matches
  lines 142–143. Implementation (field named `snapshot`, typed `GameSnapshot | None`) matches
  the code at `tool_registry.py`. All 6 fields substantive. No correction needed.
- **TEA — "Pinned the canonical OTEL signal as `tool.confrontation.canonical`"**: VERIFIED
  ACCURATE. The cited section "OTEL (the lie-detector must now tell the truth)" is at
  context line 122; the spec text floating `tool.confrontation.canonical=true` / a
  `persisted_delta` is at line 131 (and the alternative `encounter_metric_advance_span` at
  line 209). Implementation matches the code emit at `advance_confrontation.py:168`. The
  non-blocking `encounter_metric_advance_span` alternative was correctly carried as a Question
  finding rather than silently dropped. No correction needed.
- **Dev — "No deviations from spec"**: VERIFIED ACCURATE against the diff and Reviewer audit.
  Implementation matches the TEA contract exactly.

**Missed deviations:**
- No additional design or behavioral deviations found. The story was implemented exactly as
  the context document and TEA contract specified.

**Trivial note (not a deviation):** The context doc names the ToolContext construction site
as `orchestrator.py:3853` (context lines 93/99/116/144/226); the code landed at
`orchestrator.py:3920`. This is stale line-number drift in a descriptive pointer as the file
evolved — the *same* construction site (immediately after `genre_pack=context.pack`,
threading `snapshot=context.snapshot`). The design was honored verbatim; no spec/code
divergence to log.

**Cross-reference (forward scope, not a deviation):** The Reviewer's Delivery Finding — 16
other WRITE tools still use the `load()→mutate→save()` fresh-copy idiom — is *forward scope*,
not a deviation of 73-3. The story context (line 85+) scoped this fix to
`advance_confrontation` alone, and the implementation matched that scope precisely. The
sibling-tool audit belongs to a follow-up story under epic 73, where the Delivery Finding
already records it.

**AC deferral verification:** No-op. No ACs were deferred or descoped — all five (AC1–AC5)
are DONE per the AC→test map (session §TEA Assessment) and Portia's APPROVED verdict. No
ac-completion accountability table was written because nothing was deferred.

**Spec Alignment:** Aligned. **Manifest complete.**

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 smells; 21/21 targeted + 442/442 regression green; lint clean | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (domain self-assessed — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (domain self-assessed — see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 (1 high, 1 medium, 4 low) | confirmed 2 (downgraded to MEDIUM/LOW), dismissed 0, deferred 4 (low) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 (2 high, 1 medium) | confirmed 3 (downgraded to LOW doc-polish), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (domain self-assessed — see [TYPE]) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (domain self-assessed — see [SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (domain self-assessed — see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 58 instances / 17 checks | confirmed 0, dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled and domain self-assessed)
**Total findings:** 0 confirmed blocking; 7 confirmed non-blocking (2 test + 3 doc + 2 Reviewer-originated), 0 dismissed, 4 deferred (low-confidence test nits)

## Reviewer Assessment

**Verdict:** APPROVED

This is a tight, correctly-scoped state-coherence bug fix. The thesis — route the
confrontation dial-move through the canonical in-turn `GameSnapshot` (the object the
single end-of-turn `room.save()` persists) instead of a fresh `repository.load()` copy
that the end-of-turn save clobbers — is sound, and I verified the load-bearing claims
myself rather than trusting the narration around them.

**Object-identity chain traced end-to-end (the only thing that makes this fix work):**
- `room._snapshot` is what `room.save()` persists — `sidequest/server/session_room.py:297`.
- `sd.snapshot` IS `room._snapshot`: after `room.bind_world(snapshot=snapshot)`, connect
  reassigns `snapshot = room.snapshot` — `sidequest/handlers/connect.py:650` and `:690` —
  so the session-data object becomes the canonical room object.
- `TurnContext.snapshot = sd.snapshot` — `sidequest/server/session_helpers.py:762` + `:1209`.
- `ToolContext.snapshot = context.snapshot` — `sidequest/agents/orchestrator.py:3920` (the
  sole production construction site).
- `advance_confrontation` mutates `ctx.snapshot.encounter.<metric>.current` in place —
  `sidequest/agents/tools/advance_confrontation.py:148-150`.
- End-of-turn `room.save()` persists that same object — `websocket_session_handler.py:1171`.

[VERIFIED] The dial mutation lands on the exact object the end-of-turn save writes —
evidence: the five-link chain above; every link is reference assignment, no copy. Complies
with ADR-037 (room owns the canonical snapshot) and CLAUDE.md "Verify Wiring, Not Just
Existence".

[VERIFIED] The dev's root-cause premise is correct, not hand-waved — evidence:
`PgSaveRepository.load()` → `load_snapshot()` (`sidequest/game/pg/snapshot.py:134-163`)
runs `SELECT snapshot_json` + `json.loads()` and deserializes a **fresh** object every
call. The old `load()→mutate→save()` therefore wrote a distinct object the canonical
`room.save()` overwrote — a genuine lost-update. The fix is the right one.

**Data flow traced:** narrator tool-call (`advance_confrontation`, axis+delta) →
`ctx.snapshot.encounter.player_metric|opponent_metric.current += delta` (in-memory, on
canonical) → end-of-turn `room.save()` → Postgres `game_state.snapshot_json`. Safe because
the mutated object and the persisted object are identical by reference.

[EDGE] (self-assessed; edge-hunter disabled) — Boundary paths enumerated:
`ctx.snapshot is None` → fail-loud `recoverable=False` (`:131-139`); `encounter is None` →
fatal (`:141-146`); negative delta → tested (`test_negative_advance_survives...`); delta=0 →
harmless no-op (untested — deferred low finding); threshold-crossing uses strict
`value_before < threshold and value_after >= threshold`, so an already-past metric does not
re-fire (`:157`). No unhandled path.

[SILENT] (self-assessed; silent-failure-hunter disabled) — The change *removes* a silent
fallback rather than adding one: the deleted `repository.load()` path is replaced by an
explicit `ToolResult.error(..., recoverable=False)` whose message names the refused
fallback. No bare except, no swallowed error, no `suppress()`. Rule-checker A1 corroborates.
Complies with CLAUDE.md "No Silent Fallbacks".

[TEST] (test-analyzer, confirmed, downgraded to non-blocking) — Two coverage gaps:
(a) no `save.assert_not_called()` regression guard for the deleted in-tool save (captured
as a Delivery Finding); (b) `test_missing_canonical_snapshot_fails_loud_no_repo_fallback`
asserts `r.message is not None` but not message content (line ~389) — should assert
`"canonical snapshot" in r.message` to bind the test to the correct failure mode, mirroring
the `"no active encounter"` assertion at line ~368. Neither is a production defect; the
21-test suite already proves persistence-after-canonical-save (the load-bearing AC1). Four
further low-confidence nits (delta=0, tautological arithmetic, concurrency OTEL) deferred.

[DOC] (comment-analyzer, confirmed, downgraded to LOW polish) — Three wording imprecisions,
none affecting behavior: (1) `tool_registry.py:151` says "orchestrator construction site"
but the `ToolContext` is built per-turn inside `_run_narration_turn_sdk`, not at Orchestrator
construction; (2) `advance_confrontation.py:52` docstring frames `canonical` as distinguishing
two values though it is hardcoded `True` (a presence-signal, never `False`); (3)
`advance_confrontation.py:153` "re-create the ordering hazard" overstates — a second save of
the *same canonical* object would be redundant but harmless, not hazardous. Worth a one-line
docstring/comment tidy on a future pass; not blocking.

[TYPE] (self-assessed; type-design disabled) — `ToolContext.snapshot: GameSnapshot | None
= None` on a `frozen=True, slots=True` dataclass with `GameSnapshot` under `TYPE_CHECKING`
is safe because `from __future__ import annotations` (tool_registry.py:8) stringizes all
annotations at runtime. Optional/`None` default → backward compatible with every existing
construction site. Rule-checker #3/#10 corroborates. No stringly-typed surface introduced.

[SEC] (self-assessed; security disabled) — No security surface. `AdvanceConfrontationArgs`
uses `model_config = {"extra": "forbid"}`, `axis: Literal["player","opponent"]`, and
`delta: int` — unknown fields and bad axes rejected at the Pydantic boundary; no string
indexing, injection, deserialization-of-untrusted-input, or path handling. `ctx.snapshot`
is server-owned, not user input. Rule-checker #11 corroborates.

[SIMPLE] (self-assessed; simplifier disabled) — The change is net-simplifying: it deletes a
load + a save and a local, adding one optional field, one guard, and one OTEL attribute. No
dead code, no over-engineering, no speculative generality. Aligns advance_confrontation with
the signal-then-canonical pattern the other confrontation tools already use.

[RULE] (rule-checker, clean) — 0 violations across 17 checks / 58 instances, including the
four CLAUDE.md additionals (No Silent Fallbacks, No Stubbing, Verify Wiring, OTEL
Observability). I independently confirmed the wiring (A3) and OTEL (A4) claims above.

**Pattern observed:** signal-on-canonical persistence — the tool mutates the room-owned
snapshot and lets the single end-of-turn save persist it, exactly the ADR-037 seam the other
confrontation tools follow — at `sidequest/agents/tools/advance_confrontation.py:148-155`.

**Error handling:** both failure modes (`None` snapshot, `None` encounter) return
`ToolResult.error(recoverable=False)` with diagnostic messages; no exceptions raised, no
state mutated on the error path — `sidequest/agents/tools/advance_confrontation.py:131-146`.

### Rule Compliance

Enumerated every changed type/function/field against the applicable CLAUDE.md + python
lang-review rules:

- **No Silent Fallbacks** — `advance_confrontation` `None`-snapshot branch (`:131-139`):
  COMPLIANT (fail-loud, names the refused `repository.load()` fallback). `None`-encounter
  branch (`:141-146`): COMPLIANT. `_build_turn_context` seat-map non-dict path
  (pre-existing, session_helpers.py:802-811): COMPLIANT (warns, does not silently
  substitute). No violations.
- **No Stubbing** — `ToolContext.snapshot` field, orchestrator wire-up, tool body: all
  COMPLIANT (real, immediately-exercised code; no placeholders).
- **Verify Wiring, Not Just Existence** — `ToolContext.snapshot` has a non-test production
  consumer (`advance_confrontation`) reached via the sole production construction site
  (orchestrator.py:3920): COMPLIANT.
- **OTEL Observability** — `tool.confrontation.canonical=True` emitted on the dispatch span
  every success (`:168`): COMPLIANT.
- **python #1 silent-exceptions / #2 mutable-defaults / #3 type-annotations / #6 test-quality
  / #9 async-pitfalls / #10 import-hygiene / #11 input-validation** — all changed instances
  COMPLIANT per the exhaustive rule-checker pass (58 instances) which I spot-confirmed on the
  TYPE_CHECKING import, the frozen-dataclass field, the Literal-gated args, and the removal of
  the blocking `repository.save()` from the async body.

### Devil's Advocate

Let me argue this code is broken. **First attack — the fix moves the lost update instead of
fixing it.** If `ctx.snapshot` were a copy of the canonical rather than the canonical itself,
the dial would still vanish under `room.save()`. I chased this to ground: `connect.py:650/690`
reassigns the local to `room.snapshot` immediately after `bind_world`, and `_SessionData`,
`TurnContext`, and `ToolContext` all carry that same reference forward by assignment — no
`copy`, no `model_copy`, no re-deserialization between bind and tool dispatch. The attack
fails; identity holds. **Second attack — the opposite bug: removing the in-tool save means a
write that never persists.** If a turn invokes `advance_confrontation` but no end-of-turn
`room.save()` fires, the dial move is lost forever — and now there is no in-tool save as a
safety net. I checked the production turn paths: `websocket_session_handler.py:1171` saves in
the persistence phase after narration, and `:454` saves on disconnect; the WRITE tool runs
inside `run_narration_turn`, which those paths always follow with a save. Every other WRITE
tool already relies on this same end-of-turn save, so advance_confrontation was the anomaly,
not the saved-tools. The attack identifies a real *coupling* (the fix now depends on the
end-of-turn save always firing) but no actual broken path. **Third attack — a confused
maintainer re-adds `ctx.repository.save(ctx.snapshot)` and the tests stay green.** True — and
this is the legitimate gap I filed: a redundant save of the canonical object passes every
round-trip assertion, so the regression guard is absent. But re-adding it would not even
reproduce the original bug (it now saves the canonical, not a fresh copy); it would be merely
redundant I/O. Non-blocking. **Fourth attack — concurrency.** Two narrator dispatches racing
on the same metric could interleave read-modify-write. The Registry's per-session
`_write_locks` serializes WRITE handlers (tool_registry.py async-with lock), and
`test_parallel_advance_against_same_session_runs_sequentially` proves composition to the
expected total. The attack fails. The devil surfaces one real coupling and one real
test-gap — both non-blocking, both documented — and no Critical/High defect.

**Handoff:** To Prospero (SM) for finish-story.