---
story_id: "158-3"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-3: Block narrator apply-path opponent-HP writes when no confrontation is seated (no-encounter case)

## Story Details
- **ID:** 158-3
- **Jira Key:** (none — Jira integration not enabled)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T04:35:19Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-23T03:51:14Z | 2026-06-23T03:53:42Z | 2m 28s |
| red | 2026-06-23T03:53:42Z | 2026-06-23T04:09:00Z | 15m 18s |
| green | 2026-06-23T04:09:00Z | 2026-06-23T04:14:06Z | 5m 6s |
| review | 2026-06-23T04:14:06Z | 2026-06-23T04:25:35Z | 11m 29s |
| green | 2026-06-23T04:25:35Z | 2026-06-23T04:30:18Z | 4m 43s |
| review | 2026-06-23T04:30:18Z | 2026-06-23T04:35:19Z | 5m 1s |
| finish | 2026-06-23T04:35:19Z | - | - |

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

4 deviations

- **Guard scoped to apply_damage (HP), not apply_status (status)**
  - Rationale: Story title is "opponent-HP writes"; the OTEL lie-detector concern is the changed HP field; apply_status has legitimate non-combat uses (Boon, narrative conditions) and writes no HP. Guarding it broadly would over-reach and break non-combat status narration.
  - Severity: minor
  - Forward impact: Captured as a Delivery Finding (Gap) for a possible apply_status follow-up.
- **"Opponent" detection pinned as "target is a non-player NPC", not disposition-aware**
  - Rationale: Outside a confrontation there is no `side="opponent"` marker to read; ADR-116 makes NPC combat HP undefined without a confrontation, so any NPC HP write outside one is unbacked. apply_damage's documented legitimate non-combat use is environmental damage to the PC. Tests pin behavior, not the detection mechanism — Dev may implement PC/NPC discrimination however fits.
  - Severity: minor
  - Forward impact: If Keith later wants friendly-NPC environmental damage outside combat, that's a follow-up (disposition-aware guard).
- **Resolved (zombie) encounters not tested**
  - Rationale: The title explicitly scopes to the "(no-encounter case)". A resolved-encounter (ADR-139 zombie-dial) write is a separate concern with its own guard pattern (advance_confrontation.py:183).
  - Severity: minor
  - Forward impact: Possible follow-up if zombie-encounter opponent writes are observed in play.
- **Guard scope expanded to include resolved-husk encounters**
  - Rationale: Reviewer FLAGGED TEA's deferral of the resolved case as a real residual hole — a resolved husk is preserved on the dice-replay re-entry and is the phantom-wound vector (ADR-139: no live Other). This intentionally goes one step beyond the literal "(no-encounter case)" title at the Reviewer's direction.
  - Severity: minor
  - Forward impact: none — broadens the guard, no caller depends on the old narrower behavior (no production direct callers).

## Sm Assessment

**Story:** 158-3 — Block narrator apply-path opponent-HP writes when no confrontation is seated (no-encounter case). p1 bug, server-only, tdd (phased).

**Why this is next:** Highest-priority open item in epic 158. It is a direct instance of the project's load-bearing OTEL "lie-detector" doctrine — the narrator can write opponent damage with no seated confrontation to back it, so a changed HP field reads as a fired mechanic when nothing fired. 158-1/158-2 fixed the *seating* and *routing* halves of the WWN-combat finding; this fixes the *unbacked-write* half on the apply path.

**Scope (held tight):** Only the opponent-HP apply path when no confrontation is seated. Block/reject the write, emit an OTEL warning span so the GM panel can see the rejection. Do NOT broaden into general narration-tool changes, ablative-HP retuning (ADR-114), or seating logic (already covered by 158-1). The fix is a guard, not a redesign.

**Context for TEA/Dev:** Source of truth is `~/Projects/sq-playtest-pingpong.md`. Epic context at `sprint/context/context-epic-158.md`; story context at `sprint/context/context-story-158-3.md` (root cause + ACs + code-area guidance). Relevant ADRs: 116/139 (confrontation integrity invariants — there must be a seated Other), 123 (mechanical-engagement pipeline), 114 (HP substrate).

**Red-phase guidance for Argus:** ACs need a failing test for the no-encounter case (narrative beat attempts opponent-state write → rejected + OTEL warning span) and a non-regression test for the seated-combat case (damage write accepted + OTEL info span). The intent-router pass and any combat-creation seam must be stubbed per the project's "E2E encounter tests are router-driven now" gotcha to avoid flaky tests.

**Handoff:** TEA (Argus Panoptes) → red.

## TEA Assessment

**Tests Required:** Yes
**Reason:** p1 behavioral bug fix — a guard + OTEL on the opponent-HP apply path.

**Test Files:**
- `tests/agents/tools/test_apply_damage_confrontation_guard.py` — confrontation-seated guard for `apply_damage`, driven through `default_registry.dispatch` (production path).

**Tests Written:** 6 tests covering all 4 ACs
**Status:** RED confirmed (4 guard tests fail on clean assertions; 2 regression-protectors pass) — no import/DB/fixture errors.

**Real code vs. context doc (IMPORTANT for Dev):** The context doc's `narration_tool.py` / `opponent_state.hp` / `in_combat` do **not exist**. Real surfaces:
- Apply-path: `sidequest/agents/tools/apply_damage.py` (`apply_damage` handler) — the narrator's freeform/environmental damage tool.
- Seated-confrontation signal: `GameSnapshot.encounter is not None` (`sidequest/game/session.py:870`).
- HP lives on `CreatureCore.hp` (HpPool); `find_creature_core(name)` resolves Characters + NPCs.
- OTEL: handlers set `ctx.otel_span.set_attribute(...)`; dispatch span name `tool.write.apply_damage`; `tool.result_status` set by the dispatcher from the ToolResult.

**Guard contract pinned by the tests (behavior, not implementation):**
| Case | Expected |
|------|----------|
| NPC target, `encounter is None` | REJECT → `ERROR_RECOVERABLE`, msg names confrontation/encounter, HP unchanged, span `guard_rejected=True` + `guard_reason="no_confrontation_seated"` + `result_status="error_recoverable"` |
| Player Character target, `encounter is None` | ALLOW (environmental/freeform) → `OK`, HP reduced |
| NPC target, `encounter` seated | ACCEPT → `OK`, HP reduced, span `guard_rejected=False` + `target_hp_after` + `result_status="ok"` |

**Test status breakdown:**
- RED now (need the guard): `test_npc_damage_rejected_without_confrontation`, `test_rejected_npc_write_emits_warning_span`, `test_accepted_npc_write_emits_info_span` (asserts the new `guard_rejected=False` attr on the accept path), `test_repro_no_encounter_then_combat_beat`.
- GREEN now (regression-protectors — must STAY green after the fix): `test_pc_environmental_damage_allowed_without_confrontation`, `test_npc_damage_accepted_with_confrontation`.

**Dev note — existing test will break:** `tests/agents/tools/test_apply_damage.py::test_damage_targets_npc` (line 146) damages a Goblin NPC with **no encounter** and asserts OK — that encodes the *buggy* contract. After the guard lands it must be updated (seat an encounter so it stays a valid "NPC damage during combat" test, or flip it to expect rejection). This is expected and in-scope for GREEN.

### Rule Coverage (Python lang-review)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 No silent fallback (fail loud) | `test_npc_damage_rejected_without_confrontation`, `test_rejected_npc_write_emits_warning_span` | failing (guard absent) |
| #4 Logging coverage/correctness (error path → warning signal) | `test_rejected_npc_write_emits_warning_span` (OTEL `guard_rejected`/`result_status`) | failing |
| OTEL Observability Principle (every decision emits a span) | `test_rejected_npc_write_emits_warning_span`, `test_accepted_npc_write_emits_info_span` | failing |
| #6 Test quality (specific-value asserts, no vacuous/skip) | all 6 (assert HP values, status enums, span attrs) | self-checked clean |

**Rules checked:** 4 of the applicable lang-review rules have coverage. #3 (type annotations) and #9 (async/await) apply to Dev's handler implementation, not testable here. #2/#5/#7/#8 not applicable to a guard.
**Self-check:** 0 vacuous tests — every test asserts a specific value (HP integer, status enum, or span attribute) plus persisted state via `_hp()`.

**Handoff:** To Dev (Hephaestus the Smith) for the GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/agents/tools/apply_damage.py` — confrontation guard: reject damage to a non-player creature when `snapshot.encounter is None` (ERROR_RECOVERABLE + warning span `guard_rejected=True`/`guard_reason="no_confrontation_seated"`); accepted writes set `guard_rejected=False`. Player characters exempt (freeform/environmental path). Docstring updated.
- `tests/agents/tools/test_apply_damage.py` — `test_damage_targets_npc` now seats a combat encounter (it had encoded the now-blocked no-confrontation contract).

**How it works:** `target_is_player = any(ch.core.name == args.target for ch in snapshot.characters)`. If the target is not a player AND no encounter is seated → reject before the HP delta lands. Otherwise apply as before. OTEL `tool.damage.guard_rejected` fires on every path so the GM panel sees blocked vs. accepted writes.

**Tests:** 23/23 passing (GREEN) — 6 new guard tests, 11 existing apply_damage tests, 6 tool-dispatch-span sanity tests. ruff check clean, ruff format clean, pyright 0 errors on changed files.

**AC coverage:** AC-1 (guard blocks unbacked writes) ✓; AC-2 (OTEL warning on reject / info on accept) ✓; AC-3 (no regression on legal opponent writes during combat) ✓; AC-4 (repro-level end-to-end via real dispatch) ✓.

**Branch:** feat/158-3-block-unbacked-opponent-hp-writes (pushed)

**Handoff:** To Reviewer (Hermes Psychopompos)

### Dev Assessment — Rework Round 1 (reviewer findings addressed)

**Both blocking [EDGE] findings fixed:**
1. **[HIGH] Resolved-husk window** — guard condition changed from `snapshot.encounter is None` to `snapshot.encounter is None or snapshot.encounter.resolved` (apply_damage.py). A resolved husk now rejects with a distinct `guard_reason="confrontation_resolved"` (vs `"no_confrontation_seated"`) so the GM panel can tell the two causes apart. New tests: `test_npc_damage_rejected_when_encounter_resolved` (handler-level rejection + HP unchanged) and `test_resolved_husk_reject_span_uses_distinct_reason` (dispatch-level span reason).
2. **[MEDIUM] Reject-span completeness** — the rejection branch now sets `tool.damage.damage_type` and `tool.damage.source`, symmetric with the accept branch. `test_rejected_npc_write_emits_warning_span` extended to pass and assert both fields.

**Non-blocking findings (4):** acknowledged, not actioned this round — they are out-of-scope follow-ups (MP inter-PC friendly-fire; non-combat encounter category coarseness) or were dismissed with rationale by the Reviewer (case-sensitivity matches the `find_creature_core` idiom; npc_pool members correctly hit `not_found`). Captured in Delivery Findings.

**Tests:** 25/25 passing (8 guard tests incl. 2 new, 11 apply_damage, 6 tool-dispatch-span). ruff check + format clean, pyright 0 errors.

**Commits:** `fix(158-3): close resolved-husk window + complete reject OTEL span` (pushed).

**Handoff:** Back to Reviewer (Hermes Psychopompos) for re-review.

## Subagent Results (Round 1 — superseded)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (17 tests GREEN, ruff/format/pyright clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 2, dismissed 5 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (4 rules checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned, 6 disabled via settings)
**Total findings:** 2 confirmed, 5 dismissed (with rationale), 0 deferred

### Edge-hunter finding dispositions
- **Finding 1 — resolved-encounter husk (CONFIRMED, [HIGH][EDGE]):** see severity table. Independently verified: `reap_resolved_encounter_husk` (websocket_session_handler.py:794) clears the husk at turn-start *except* on the dice-replay re-entry (`is_dice_replay`), which deliberately preserves `resolved=True` (comment :784-789, the phantom-wound CRITICAL). `apply_damage` is `combat_resolution=True` (withheld only on *live* WN combat; a resolved encounter is not live → reachable). Guard's `encounter is None` lets the write through.
- **Finding 2 — case-sensitive name match (DISMISSED, low):** `target_is_player` uses exact `==`, identical to `find_creature_core` (session.py:1824). Name-case normalization is a pre-existing codebase-wide convention, not introduced or worsened by this guard. The contrived collision (PC "Alice" + NPC "alice") is not a regression of this diff.
- **Finding 3 — npc_pool members (DISMISSED, low):** edge-hunter itself confirms pool members correctly hit `not_found` before the guard; only an error-message-quality nicety, not a safety issue.
- **Finding 4 — MP inter-PC damage (DISMISSED → captured as non-blocking delivery finding):** player-state is *explicitly out of scope* (context doc Scope). Allowing environmental damage to any PC is intentional (a party-wide hazard hits multiple PCs); restricting to `perspective_pc` would break that. PvP/friendly-fire is a separate concern, not this story's.
- **Finding 5 — non-combat encounter category (DISMISSED → captured as non-blocking note):** a seated confrontation of any category satisfies ADR-116 ("an Other is present"). HP-axis restriction by `win_condition` is a separate mechanical concern, not this story's scope.
- **Finding 6 — reject span omits damage_type/source (CONFIRMED, [MEDIUM][EDGE]):** see severity table.

## Reviewer Assessment (Round 1 — REJECTED, superseded)

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH][EDGE] | Guard ignores `encounter.resolved` — a resolved husk (preserved intentionally on the dice-replay re-entry, reap skipped) lets a freeform NPC HP write land against an opponent whose fight is already settled. This is a residual instance of the exact unbacked-write class the story targets; ADR-139 (load-bearing per the story context) treats a resolved encounter as having no live Other. | `sidequest/agents/tools/apply_damage.py:97` | Change the guard condition to `snapshot.encounter is None or snapshot.encounter.resolved`. Emit a distinct `guard_reason` for the husk case (e.g. `"confrontation_resolved"`) so the GM panel can tell the two rejection causes apart. Add a test seating a `resolved=True` encounter and asserting the NPC write is rejected + warning span. |
| [MEDIUM][EDGE] | Reject-path OTEL span omits `tool.damage.damage_type` and `tool.damage.source` (the accept path sets both) — the warning span is asymmetric/incomplete in a story whose purpose is GM-panel observability of blocked writes (AC-2: warning span carries the attempted write spec). | `sidequest/agents/tools/apply_damage.py:98-101` | Set `tool.damage.damage_type` and `tool.damage.source` on the rejection branch so every span path carries the full write spec. Extend `test_rejected_npc_write_emits_warning_span` to assert both. |

**Dispatch-tag coverage:** [EDGE] findings 1 & 6 confirmed above. [SEC] clean (reviewer-security: 0 violations across 4 rules — no silent fallback, OTEL both paths, no PII in spans, perception firewall untouched). [SILENT], [TEST], [DOC], [TYPE], [SIMPLE], [RULE] — subagents disabled via `workflow.reviewer_subagents`; I assessed these domains myself (see Rule Compliance + observations below).

### Rule Compliance (self-assessed, disabled-subagent domains + project rules)
- **[VERIFIED] No Silent Fallbacks (CLAUDE.md):** the guard fails loud — `ToolResult.error(..., recoverable=True)` + warning span at apply_damage.py:98-106, never a silent skip. Complies. ([SILENT] domain)
- **[VERIFIED] OTEL Observability Principle:** both branches set `tool.damage.guard_rejected`; reject adds `guard_reason`; dispatcher stamps `tool.result_status` (tool_registry.py:357). The *incompleteness* of the reject span (missing damage_type/source) is finding 6, not a wiring break. ([RULE] domain)
- **[VERIFIED] No Source-Text Wiring Tests (CLAUDE.md):** the new tests drive `default_registry.dispatch` and assert behavior + OTEL spans (test_apply_damage_confrontation_guard.py), no `read_text()`/regex-on-source. Complies. ([TEST] domain)
- **[VERIFIED] Test quality:** every test asserts specific values (HP ints, status enums, span attrs) + persisted state via `_hp()`; no vacuous asserts, no skips. ([TEST] domain)
- **[VERIFIED] Type design:** handler signature fully annotated; `ApplyDamageArgs` is a validated pydantic model (`amount: int = Field(ge=0)`); guard adds no stringly-typed API. ([TYPE] domain)
- **[VERIFIED] Docstring honesty ([DOC] domain):** module docstring updated (apply_damage.py:24-31) to describe the guard accurately; inline comment at :88-95 explains the ADR-116 rationale. No stale doc.
- **[VERIFIED] Simplicity ([SIMPLE] domain):** guard is a single `any()` + one condition; no over-engineering. The only simplification debt is the duplicated attribute-setting that finding 6's fix will touch.

### Observations
- **[VERIFIED] Ordering is correct** — guard returns before `core.apply_hp_delta`/`ctx.repository.save` (apply_damage.py:97-106 precede :111-114), so a blocked write truly leaves HP unchanged. Evidence: `test_npc_damage_rejected_without_confrontation` asserts `_hp(store,"Goblin")==8`.
- **[VERIFIED] Player-exemption is correct for the freeform/environmental path** — `target_is_player` matches any `snapshot.characters` entry (apply_damage.py:96); environmental damage to a PC outside combat is the documented use (docstring), and player-state is explicitly out of scope.
- **[VERIFIED] Primary phantom-wound vector already mitigated** — `reap_resolved_encounter_husk` clears husks at turn-start for normal turns; the guard + reap together close the cross-turn case. The residual (finding 1) is the dice-replay window only.
- **[MEDIUM] finding 6** and **[HIGH] finding 1** as tabled.
- **[VERIFIED] No production caller bypasses the guard** — `apply_damage` is only reachable via `default_registry.dispatch` (narrator tool-use); confirmed no direct non-test callers.

### Devil's Advocate
Assume this guard is broken. The most damning attack: the story's title says "no-encounter case," and the author read that literally as `encounter is None`. But the engine has a *third* state between "live fight" and "no fight" — the **resolved husk**. A narrator that has just won a fight, narrating the kill on the dice-replay re-entry (where the reap is deliberately skipped), still sees `snapshot.encounter` populated with `resolved=True`. It can call `apply_damage` on the dead opponent and the guard waves it through, because `resolved is True` but `encounter is not None`. This is not hypothetical: the reap exists *specifically because* a resolved husk is a phantom the narrator layers fresh wounds onto (the 2026-06-14 CRITICAL). The guard was built to be the write-site defense for exactly this class of bug and it leaves the husk door open. A confused narrator under "describe the aftermath" pressure is precisely the actor that does this.

Second attack: the GM panel is the lie detector, and a blocked write is supposed to be *fully visible*. But the reject span carries only target+amount+reason, while the accept span carries damage_type+source too. A GM auditing "what did the narrator try to do that I blocked?" sees a sparser record for the *blocked* (more suspicious) case than for the *allowed* one — backwards from what an integrity tool should do. For a 40-year-GM (Keith) using the panel to catch improvisation, the blocked-write view should be at least as rich as the allowed-write view.

Third (non-finding) probe: could a player free-text inject through `args.target` into the span/error? No — `find_creature_core` has already resolved it to a real roster name before the guard, and it's `!r`-quoted into a structured span attr / model-facing tool result, never a log sink (confirmed by reviewer-security). Could amount=0 against an NPC with no encounter cause a confusing rejection? It's rejected (a no-op write is still a write attempt) — acceptable and arguably correct. Neither rises to a finding.

Both confirmed findings are small, testable, and directly serve the story's own integrity/observability purpose, so they belong in this story rather than a follow-up.

**Handoff:** Back to TEA for red rework (both findings are testable — a new resolved-encounter rejection test and an extended warning-span assertion).

## Subagent Results

Round 2 re-review (after rework). Same enabled set as round 1.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (25 tests GREEN, ruff/format/pyright clean, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Yes | findings | 3 (all low) | both round-1 findings confirmed resolved; 3 new low-confidence, dismissed 3 |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | clean | 0 (4 rules checked, 0 violations) | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (3 enabled returned, 6 disabled via settings)
**Total findings:** 0 confirmed, 3 dismissed (all low-confidence, non-regression), 0 deferred

### Round-2 edge-hunter dispositions
- **Round-1 finding 1 (resolved husk):** CONFIRMED RESOLVED — guard now `encounter is None or encounter.resolved` with safe short-circuit; distinct `guard_reason="confrontation_resolved"`; tested.
- **Round-1 finding 6 (reject span completeness):** CONFIRMED RESOLVED — reject branch sets `damage_type`+`source`; test extended to assert them.
- **New finding 1 — player_seats not cross-checked (DISMISSED, low):** `target_is_player` iterates `snapshot.characters`, which is the canonical PC roster and exactly what `find_creature_core` (session.py:1824) uses to define a PC. The concern requires `characters` to be incomplete while a seat is occupied — not a real lifecycle state. Captured as a non-blocking improvement note.
- **New finding 2 — companion-NPC-on-player-side policy undocumented (DISMISSED, low):** behavior is consistent and intentional — a companion NPC is an NPC (not a Character), so its combat HP requires a seated encounter; the live-encounter path accepts it, the no-encounter path rejects it. Captured as a non-blocking doc-nit.
- **New finding 3 — `encounter.resolved` could be None (DISMISSED, self-resolved):** edge-hunter confirmed `resolved: bool = False` (encounter.py:371), never None. No action.

## Reviewer Assessment

**Verdict:** APPROVED

**Round:** 2 (re-review after rework round 1). Both round-1 blocking [EDGE] findings are fixed and independently verified.

**What changed since round 1:**
- Guard now rejects resolved-husk encounters (`encounter is None or encounter.resolved`) with a distinct `guard_reason="confrontation_resolved"` — closes the phantom-wound dice-replay window (ADR-139). Short-circuit verified safe (`.resolved` never dereferenced when `encounter is None`).
- Reject OTEL span now carries `damage_type`+`source`, symmetric with the accept span.
- Two new tests + one extended assertion; 25/25 green.

**Data flow traced:** narrator tool-use `apply_damage(target, amount, ...)` → `default_registry.dispatch` → handler loads snapshot → `find_creature_core` resolves target → guard (`target_is_player` / `encounter` live?) → reject (error + warning span, no write) OR `apply_hp_delta` + `repository.save` + info span. Safe: a blocked write returns before persistence (verified by `_hp(...)==8` assertions).

**Pattern observed:** guard mirrors the canonical confrontation-guard pattern at advance_confrontation.py:169-193 (None/resolved check + OTEL refusal attrs) — consistent with the codebase. `apply_damage.py:101-116`.

**Error handling:** fails loud per CLAUDE.md No-Silent-Fallbacks — `ToolResult.error(recoverable=True)` + warning span on both rejection causes; no silent no-op.

**Dispatch-tag coverage:** [EDGE] round-1 findings resolved, 3 new low dismissed (above). [SEC] clean (reviewer-security round 2: 0 violations, args.source confirmed narrator-authored / no log sink / no broadcast). [SILENT] no swallowed errors (guard returns explicit error). [TEST] 25/25 green, assertions specific (HP ints, status enums, span attrs), no vacuous/skips. [DOC] module docstring + inline comment updated and accurate. [TYPE] handler fully annotated, validated pydantic args. [SIMPLE] guard is one predicate + one condition, no over-engineering. [RULE] OTEL Observability + No-Silent-Fallbacks satisfied; no lang-review violations.

**Observations (≥5):**
- [VERIFIED] Resolved-husk closed — apply_damage.py:104 `(encounter is None or encounter.resolved)`; test `test_npc_damage_rejected_when_encounter_resolved` + `test_resolved_husk_reject_span_uses_distinct_reason`.
- [VERIFIED] Reject-span symmetry — apply_damage.py:108-109 set damage_type+source; asserted in `test_rejected_npc_write_emits_warning_span`.
- [VERIFIED] No live-encounter regression — guard skipped when encounter present & unresolved; `test_npc_damage_accepted_with_confrontation` + `test_accepted_npc_write_emits_info_span` green.
- [VERIFIED] Player-exemption intact — `test_pc_environmental_damage_allowed_without_confrontation` green; environmental damage path preserved.
- [VERIFIED] Short-circuit safety — `or` prevents `None.resolved`; edge-hunter + my read concur.
- [LOW] player_seats cross-check + companion-NPC doc-nit — non-blocking, captured as delivery findings.

**Handoff:** To SM (Themis the Just) for finish-story.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The story context doc (context-story-158-3.md) names a `narration_tool.py` apply-path with `opponent_state.hp`/`opponent_state.status` fields and an `in_combat` snapshot flag — **none of these exist**. The real opponent-HP apply-path is the `apply_damage` tool (`sidequest/agents/tools/apply_damage.py`), HP lives on `CreatureCore.hp` (HpPool), and the seated-confrontation signal is `GameSnapshot.encounter is not None` (`sidequest/game/session.py`). Dev should implement the guard in `apply_damage.py`, not a nonexistent module. *Found by TEA during test design.*
- **Gap** (non-blocking): `apply_status` (`sidequest/agents/tools/apply_status.py`) is left unguarded. AC-1 mentions opponent *status* writes, but apply_status has legitimate non-combat uses (Boon, narrative conditions) and writes no HP, so it falls outside this story's HP-focused scope. A narrator could in principle inflict harmful status (Wound/Scar) on a prose enemy with no confrontation. Affects `sidequest/agents/tools/apply_status.py` (would need its own disposition-aware guard). Candidate follow-up story. *Found by TEA during test design.*
- No further upstream findings.

### Dev (implementation)
- No upstream findings during implementation. Confirmed no production (non-test) code calls the `apply_damage` handler directly — it is only reachable via the narrator's tool-use through `default_registry.dispatch`, so the guard's blast radius was limited to one existing test (now updated). The TEA-flagged `apply_status` gap remains a valid follow-up candidate.

### Reviewer (code review)
- **Gap** (blocking): The confrontation guard ignores `encounter.resolved`, so a freeform NPC HP write lands against a resolved husk (preserved on the dice-replay re-entry). Affects `sidequest/agents/tools/apply_damage.py:97` (extend condition to `encounter is None or encounter.resolved` + test). *Found by Reviewer during code review.* — routed to rework.
- **Gap** (blocking): The rejection OTEL span omits `damage_type`/`source`, making the blocked-write GM-panel view sparser than the allowed-write view. Affects `sidequest/agents/tools/apply_damage.py:98-101` (set both attrs + extend test). *Found by Reviewer during code review.* — routed to rework.
- **Improvement** (non-blocking): In multiplayer, the player-exemption allows PC-on-PC `apply_damage` with no encounter (friendly-fire). Intentional for party-wide environmental hazards and player-state is out of scope here, but flag for a future PvP/friendly-fire policy. Affects `sidequest/agents/tools/apply_damage.py:96`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The guard is coarse at the encounter present/absent boundary — NPC damage is allowed during a seated *non-combat* (social/table) encounter regardless of `win_condition`. Acceptable (a confrontation = an Other is present per ADR-116) but worth a future decision on HP-axis vs non-HP confrontations. Affects `sidequest/agents/tools/apply_damage.py:97`. *Found by Reviewer during code review.*

### Reviewer (code review — round 2)
- **Improvement** (non-blocking): Player-detection uses `snapshot.characters` only; could additionally cross-check `snapshot.player_seats.values()` to be robust if the Character roster is ever incomplete mid-session. Currently consistent with `find_creature_core`'s PC definition, so not a defect. Affects `sidequest/agents/tools/apply_damage.py:102`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The guard's treatment of companion NPCs (player-side encounter actors that aren't Characters) — rejected with no encounter, accepted with a live one — is consistent but undocumented/untested. A one-line comment or test would lock the intent. Affects `sidequest/agents/tools/apply_damage.py:102`. *Found by Reviewer during code review.*
- No blocking findings round 2 — both round-1 blockers resolved and verified.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Guard scoped to apply_damage (HP), not apply_status (status)**
  - Spec source: context-story-158-3.md, AC-1
  - Spec text: "the narrator attempts to write opponent-state fields (e.g., opponent_state.hp, opponent_state.status)"
  - Implementation: Tests cover only the HP write path (`apply_damage`). `apply_status` is not tested/guarded.
  - Rationale: Story title is "opponent-HP writes"; the OTEL lie-detector concern is the changed HP field; apply_status has legitimate non-combat uses (Boon, narrative conditions) and writes no HP. Guarding it broadly would over-reach and break non-combat status narration.
  - Severity: minor
  - Forward impact: Captured as a Delivery Finding (Gap) for a possible apply_status follow-up.
- **"Opponent" detection pinned as "target is a non-player NPC", not disposition-aware**
  - Spec source: context-story-158-3.md, Scope ("opponent-state only"; "npc-state ... out of scope")
  - Spec text: "Block/reject opponent-state field writes when no confrontation is seated."
  - Implementation: Tests assert that ANY NPC target is rejected without a seated encounter, while damage to a player Character is always allowed. Detection is by player-vs-NPC, not by hostile disposition.
  - Rationale: Outside a confrontation there is no `side="opponent"` marker to read; ADR-116 makes NPC combat HP undefined without a confrontation, so any NPC HP write outside one is unbacked. apply_damage's documented legitimate non-combat use is environmental damage to the PC. Tests pin behavior, not the detection mechanism — Dev may implement PC/NPC discrimination however fits.
  - Severity: minor
  - Forward impact: If Keith later wants friendly-NPC environmental damage outside combat, that's a follow-up (disposition-aware guard).
- **Resolved (zombie) encounters not tested**
  - Spec source: session.md story title
  - Spec text: "Block narrator apply-path opponent-HP writes when no confrontation is seated (no-encounter case)"
  - Implementation: The guard is tested only for `encounter is None`; a present-but-`resolved` encounter is not asserted to reject.
  - Rationale: The title explicitly scopes to the "(no-encounter case)". A resolved-encounter (ADR-139 zombie-dial) write is a separate concern with its own guard pattern (advance_confrontation.py:183).
  - Severity: minor
  - Forward impact: Possible follow-up if zombie-encounter opponent writes are observed in play.

### Dev (implementation)
- No deviations from spec. Implemented exactly the guard contract TEA pinned. The one open implementation choice (how to discriminate PC vs NPC) was resolved by membership in `snapshot.characters` — `target_is_player = any(ch.core.name == args.target for ch in snapshot.characters)` — which matches `find_creature_core`'s own characters-then-npcs resolution order. No spec named a discrimination mechanism, so this is an implementation detail within the test contract, not a deviation.

### Dev (implementation — rework round 1)
- **Guard scope expanded to include resolved-husk encounters**
  - Spec source: session.md story title + Reviewer FLAG (gates/deviations-audited)
  - Spec text: "...when no confrontation is seated **(no-encounter case)**"
  - Implementation: Guard now rejects when `encounter is None OR encounter.resolved` (was `is None` only), with a distinct `guard_reason="confrontation_resolved"`.
  - Rationale: Reviewer FLAGGED TEA's deferral of the resolved case as a real residual hole — a resolved husk is preserved on the dice-replay re-entry and is the phantom-wound vector (ADR-139: no live Other). This intentionally goes one step beyond the literal "(no-encounter case)" title at the Reviewer's direction.
  - Severity: minor
  - Forward impact: none — broadens the guard, no caller depends on the old narrower behavior (no production direct callers).

### Reviewer (audit)
- **TEA: Guard scoped to apply_damage not apply_status** → ✓ ACCEPTED by Reviewer: sound — apply_status writes no HP and has legitimate non-combat uses; the HP write is the lie-detector concern. Captured as a non-blocking follow-up.
- **TEA: "Opponent" detection as non-player NPC** → ✓ ACCEPTED by Reviewer: consistent with `find_creature_core`'s resolution order (session.py:1824) and ADR-116; the player-exemption correctly preserves the freeform/environmental path.
- **TEA: Resolved (zombie) encounters not tested** → ✗ FLAGGED by Reviewer: this deferral left a real residual hole. The guard's `encounter is None` check lets a freeform NPC HP write through against a `resolved=True` husk, which is preserved on the dice-replay re-entry (reap skipped). This is finding 1 in the severity table — it is the same unbacked-write class the story targets (ADR-139: a resolved encounter has no live Other), the fix is a one-liner, so it must be closed in this story rather than deferred. Severity: H.
- **Dev: PC/NPC discrimination via `snapshot.characters` membership** → ✓ ACCEPTED by Reviewer: matches the codebase idiom; behavior pinned by tests. (Note: the rework should keep player-exemption intact while adding the `resolved` condition to the NPC branch.)
- **Dev (rework round 1): Guard scope expanded to include resolved-husk encounters** → ✓ ACCEPTED by Reviewer: this implements my round-1 FLAG. Correctly closes the phantom-wound vector (ADR-139), keeps player-exemption intact, and is verified by two new tests. Round-2 edge-hunter confirmed no regression on the live-encounter path.