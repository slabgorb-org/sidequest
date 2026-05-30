---
story_id: "72-5"
jira_key: ""
epic: "72"
workflow: "trivial"
---
# Story 72-5: Fix narrator-invented born-hostile disposition default

## Story Details
- **ID:** 72-5
- **Title:** Fix narrator-invented born-hostile disposition default (-20 to neutral spawn)
- **Epic:** 72 (NPC Identity Hardening)
- **Points:** 2
- **Type:** bug
- **Jira Key:** (none)
- **Workflow:** trivial
- **Repo:** sidequest-server
- **Stack Parent:** none

## Story Context

An NPC the narrator invents should walk on stage *neutral*, not spitting hostility. Today the materialization seam stamps a `-20` disposition default — which ADR-020's band table reads as **hostile** (`< -10`). That default was written for Monster Manual creatures (encountergen output, ADR-059), where born-hostile is correct: a goblin ambush *should* spawn at -20. But the same code path also materializes ordinary narrator-invented people, so a shopkeeper or a passerby the narrator names can spawn pre-loaded for a fight.

This violates SOUL "Living World": NPCs act on goals and earn their dispositions through interaction (the ADR-014/020 model the epic's development pipeline revives in 72-1) — they are not *born* hostile by default.

**Technical site:** `sidequest-server/sidequest/game/session.py` — `Session._npc_from_patch` at line 1501. The born-hostile default is at line 1533:
```python
# Creatures default to hostile (-20), matching encountergen output.
disposition=-20 if is_creature else 0,
```

The `is_creature` flag (line 1505) is `True` only when the patch carries a creature-shape field (`creature_id`, `threat_level`, or `hp`). A narrator-invented *person* carries none of those, so it *already* falls to the `else 0` branch in this exact function.

**OTEL requirement:** Emit a span recording the spawn disposition and whether it was the default or an explicit value, so the GM panel can verify the corrected default fired. NPC spans live in `sidequest/telemetry/spans/npc.py`.

## Acceptance Criteria

1. **Default → neutral.** A narrator-invented NPC materialized with no explicit disposition and no creature-shape field (`creature_id`/`threat_level`/`hp` all absent) spawns at disposition `0` (neutral per ADR-020), not `-20`.

2. **Explicit hostile still hostile.** An NPC whose patch explicitly marks hostility (or a genuine creature patch carrying a creature-shape field) still spawns hostile (`-20` / its explicit value). The fix changes the *default* branch only.

3. **OTEL reflects spawn.** Materializing an NPC emits a span carrying the spawn disposition and whether it was the default or explicit, firing on the real production path so the GM panel can confirm the neutral default.

4. **Wiring test.** A test proves the spawn path is exercised from a production code path, validated by an OTEL span assertion.

## Scope Boundaries

**In scope:**
- The DEFAULT disposition a narrator-invented, non-creature NPC receives at materialization (neutral `0`, not hostile)
- Preserving born-hostile (`-20`) for genuine creatures (creature_id / threat_level / hp)
- Preserving an explicit narrator-supplied hostile disposition (fix is default-only)
- An OTEL span recording the spawn disposition

**Out of scope:**
- The disposition drift pipeline (72-1)
- Disposition preservation on promotion + load-time reconcile (72-2)
- Routing invented names through ADR-091 namegen (72-4)
- Pool growth caps (72-6)
- Identity-drift overwrite (72-7)
- OCEAN/belief seeding (72-9)

## Workflow Tracking

**Workflow:** trivial (phased: setup → implement → review → finish)
**Phase:** finish
**Phase Started:** 2026-05-30T11:23:41Z 23:24:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-30 23:24:00Z | 2026-05-30T11:03:38Z | -44422s |
| implement | 2026-05-30T11:03:38Z | 2026-05-30T11:17:41Z | 14m 3s |
| review | 2026-05-30T11:17:41Z | 2026-05-30T11:23:41Z | 6m |
| finish | 2026-05-30T11:23:41Z | - | - |

## Sm Assessment

**Setup verdict:** Ready for implement. Session, context, and branch all in place; story is well-scoped at 2pts trivial.

**Routing flag for Dev (Agent Smith) — read before touching code:** The context analysis (lines 32–33) found that a narrator-invented *person* carries no creature-shape field (`creature_id`/`threat_level`/`hp`), so it *already* falls to the `else 0` branch at `session.py:1533`. That means the naive "change -20 to 0" edit may not be the fix — and a test written against line 1533 alone could pass green while the real bug persists.

**Therefore: reproduce first.** Before editing, establish *why* a narrator-invented NPC actually reaches `-20` in the wild (the perseus_cloud session-894 observation that spawned this story). Two live hypotheses:
1. The narrator's tool-use patch for an invented person is carrying a stray creature-shape field (e.g. `hp`), flipping `is_creature` true → -20. Fix would be at the patch-construction / `is_creature` seam, not the default.
2. There is a *second* materialization path (pool→Npc promotion, MM injection) seating -20 that bypasses `_npc_from_patch`.

Write the failing test against the observed behavior, not the assumed line. If the repro confirms the default branch is genuinely correct for persons, the AC1 fix lives upstream of line 1533 — document the deviation. Either way, AC2 (creatures stay -20) and AC3/AC4 (OTEL span on the real path) stand.

**No Jira key** — this is YAML-only tracking; Jira claim was skipped intentionally.

## Dev Assessment

**Implementation Complete:** Yes

**Approach:** Systematic debugging first (reproduce before fixing, per SM routing flag). The RED run confirmed disposition values were *already* correct (person→0, creature→-20) — the only failing assertion was the missing `npc.spawn_disposition` span. So the fix is pure observability: emit the span at both NPC materialization seams, change no disposition value.

**Files Changed:**
- `sidequest/telemetry/spans/disposition.py` — new `SPAN_NPC_SPAWN_DISPOSITION` ("npc.spawn_disposition") route (state_transition / component=disposition) + `npc_spawn_disposition_span(...)` context-manager helper with a `provenance` dial (`default_neutral` / `default_creature_hostile`).
- `sidequest/game/session.py` — `_npc_from_patch` now binds the built `Npc` to a var and emits the span (provenance derived from `is_creature`) before returning.
- `sidequest/server/narration_apply.py` — `_promote_pool_member_to_npc` (the narrator-invented seam) emits the span tagged `default_neutral` with `pool_origin`; added the helper to the existing span import block.
- `tests/integration/test_npc_spawn_disposition_otel.py` — new; 3 OTEL-wiring tests driving the real production seams.

**Tests:** 3/3 new passing (GREEN). Regression: 385 passed / 0 failed across disposition spans, NPC pool promotion, invented-name routing, recurring presence, and the full telemetry suite. Lint clean; pyright: 34 pre-existing errors, **0 new** (verified by stash/compare — all in the unrelated encounter-resolution block 3798–4100).

**ACs:** AC1 (person→neutral) ✓ · AC2 (creature→-20 preserved) ✓ · AC3 (OTEL span) ✓ · AC4 (wiring via OTEL span assertion on real path, per No-Source-Text-Wiring-Tests) ✓

**Branch:** `feat/72-5-fix-born-hostile-disposition-default` (pushed)

**Handoff:** To review (The Merovingian). Note for review: no `-20` literal changed — see Design Deviations for why (anticipated by context + SM). The GM panel can now read every NPC spawn's disposition + provenance.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (0 attributable to 72-5) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (covered by me — see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (covered by me — see [SILENT]) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (covered by me — see [TEST]) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings (covered by me — see [DOC]) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (covered by me — see [TYPE]) |
| 7 | reviewer-security | Yes | clean | none | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (covered by me — see [SIMPLE]) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (covered by me — see [RULE]) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` and covered by my own analysis)
**Total findings:** 0 confirmed blocking, 0 dismissed, 1 low/non-blocking deferred (provenance-coupling note)

## Rule Compliance

Rules enumerated from server `CLAUDE.md` + `SOUL.md`, checked against every changed symbol:

- **OTEL Observability Principle** ("every backend subsystem decision MUST emit an OTEL span"): The NPC spawn-disposition decision (`-20 if is_creature else 0`) is a subsystem decision that previously emitted nothing. Now both materialization seams (`session.py:_npc_from_patch`, `narration_apply.py:_promote_pool_member_to_npc`) emit `npc.spawn_disposition`. ✓ COMPLIANT — this change exists *to satisfy* this rule.
- **No Silent Fallbacks**: No new fallback/default-path branch. The `.get(attr, default)` calls in the `extract` lambda are the standard span-route read pattern (identical to `SPAN_DISPOSITION_SHIFT` directly above), reading already-emitted attributes — not a config fallback. ✓ COMPLIANT.
- **No Stubbing**: No empty shells; the span helper is fully implemented and consumed by two real call sites. ✓ COMPLIANT.
- **Don't Reinvent — Wire Up What Exists**: Reuses `Span.open`, `SPAN_ROUTES`/`SpanRoute`, `WatcherSpanProcessor`. No new telemetry plumbing. ✓ COMPLIANT.
- **Verify Wiring, Not Just Existence**: Both emit sites are on production paths (`_apply_world_patch_inner` → `_npc_from_patch`; `resolve_status_target` → `_promote_pool_member_to_npc`). I verified the route registers at import and the helper is exported via a live `python -c` import. ✓ COMPLIANT.
- **Every Test Suite Needs a Wiring Test / No Source-Text Wiring Tests**: AC4 is satisfied by OTEL span assertions on the real watcher pipeline — not a source grep. ✓ COMPLIANT (this is the prescribed pattern).
- **Sebastien-name discipline** (CLAUDE.md: don't attach Sebastien's name to backend OTEL/observability): The new span code introduces **zero** new `Sebastien` references (confirmed by preflight + my diff read). The one `Sebastien` mention near `_promote_pool_member_to_npc` is a **pre-existing** docstring (line ~1049), not in the 72-5 diff. ✓ COMPLIANT — not a violation introduced here.

## Devil's Advocate

Arguing this code is broken. **(1) Double emission.** Could the same NPC fire two spawn spans? `_npc_from_patch` only runs for a name not already in `self.npcs` (guard at `session.py:1431`), and `_promote_pool_member_to_npc` fires when a pool member first engages — after which the name is in `npcs` and shadows the pool. So a given NPC materializes once per store. No duplicate-spawn storm. **(2) The provenance lie.** `_promote_pool_member_to_npc` hardcodes `provenance="default_neutral"` and `is_creature=False` but reports `disposition=int(npc.disposition)` (the *real* value). If a future refactor changed `Npc`'s default disposition away from 0, the span would honestly report the new number while the label still said "default_neutral" — a latent label/value divergence. Today this cannot fire (pool members structurally carry no creature shape and no disposition), so it is a LOW latent coupling, not a live bug — recorded as a finding for 72-2/72-7 awareness. **(3) Empty/garbage name.** `npc.core.name` could in theory be ""? No — `NpcPatch.name` has a non-blank validator and `CreatureCore.name`/`NpcPoolMember.name` are required; the span's `npc_name` is always populated. **(4) `int(npc.disposition)` blows up?** `Disposition.__int__` exists (`disposition.py:156`); verified. **(5) The `**attrs` escape hatch** could let a caller overwrite `npc_name`/`provenance` since `**attrs` spreads *after* the named keys. Neither call site passes `attrs`, and this mirrors the existing `npc_referenced_span` contract — not exploitable, but worth a doc note (security subagent flagged the same, non-blocking). **(6) Telemetry crashes the game?** The span wraps a bare `pass`; if the tracer is a NoOp (no provider), it silently no-ops — correct priority for a game engine where telemetry must never block `return npc`. **(7) xdist flakiness?** The tests mutate process-global `watcher_hub`, but this is the identical, already-green pattern in `test_disposition_otel_wiring.py`, and xdist isolates per-process; the full suite passed under `-n auto`. None of these rise to blocking. The change is narrow, additive, and honest.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** narrator-invented name → `NpcPoolMember(drawn_from="narrator_invented")` → `resolve_status_target` → `_promote_pool_member_to_npc` builds `Npc` (default disposition 0) → `npc_spawn_disposition_span` → `Span.open` → `WatcherSpanProcessor.on_end` → `SPAN_ROUTES[npc.spawn_disposition]` → `watcher_hub` `state_transition` → GM panel. Safe because the span is additive and outside the `return npc` control path; verified end-to-end by `test_narrator_invented_npc_spawns_neutral_with_span`.

**Pattern observed:** Span route + `@contextmanager` helper mirrors `SPAN_DISPOSITION_SHIFT` / `npc_referenced_span` exactly (`disposition.py:112-160`); `with span(): pass` idiom matches the existing disposition-shift emit at `session.py:1416`. Idiomatic, low-risk.

**Subagent dispatch (all 8 domains accounted for):**
- `[SEC]` reviewer-security → **clean**. No leakage (npc_name/int/literal only), no injection (OTEL typed attrs, no shell/SQL/template), no error swallowing. Confirmed.
- `[EDGE]` (disabled — self-covered): boundary cases (empty name, double-emit, int coercion, NoOp tracer) enumerated in Devil's Advocate; none blocking.
- `[SILENT]` (disabled — self-covered): no swallowed errors; the only silence is OTEL NoOp when no provider is configured, which is the correct non-blocking telemetry posture and pre-existing across all spans.
- `[TEST]` (disabled — self-covered): 3 tests each assert BOTH the disposition value AND the routed span fields (not vacuous); they drive real production seams; AC4 wiring is an OTEL span assertion per repo rule. Adequate.
- `[DOC]` (disabled — self-covered): module docstring updated to "affinity shifts and spawn defaults"; inline comments accurate and story-tagged. Minor: `**attrs` escape hatch could carry a one-line "internal callers only" note. LOW, non-blocking.
- `[TYPE]` (disabled — self-covered): keyword-only signature, `pool_origin: str | None` with explicit `""` normalization, `is_creature: bool` coerced. No stringly-typed surface beyond the deliberate `provenance` dial (two known literals). Sound.
- `[SIMPLE]` (disabled — self-covered): minimal addition; no dead code or over-engineering. The hardcoded `provenance` in the promote seam is the simplest correct choice (see LOW finding).
- `[RULE]` (disabled — self-covered): see Rule Compliance — all applicable rules COMPLIANT; the change *implements* the OTEL principle.

**Findings (none blocking):**

| Severity | Issue | Location | Note |
|----------|-------|----------|------|
| [LOW] | `provenance="default_neutral"` hardcoded while `disposition` is read live — latent label/value divergence if `Npc`'s default disposition ever changes | `narration_apply.py:1077-1086` | Cannot fire today (pool members carry no creature shape); deferred to 72-2/72-7 awareness |
| [LOW] | `**attrs` passthrough has no "internal callers only" doc note | `disposition.py:127-154` | Matches existing `npc_referenced_span` contract; cosmetic |

**Error handling:** Telemetry emission cannot block NPC materialization (`return npc` is outside the `with`); `int(npc.disposition)` is safe (`Disposition.__int__`, `disposition.py:156`).

**ACs:** AC1 ✓ (person→0, both seams) · AC2 ✓ (creature→-20 preserved) · AC3 ✓ (span emitted) · AC4 ✓ (OTEL span assertion on real path).

**Handoff:** To SM (Morpheus) for finish-story.

## Delivery Findings

No upstream findings at setup time. The context document (context-story-72-5.md) is thorough and provides exact line numbers and code pointers.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Disposition values were already correct — the live bug was observability, not a wrong default.**
  Systematic root-cause trace (Phase 1) established that every narrator-origin NPC-creation path already produces the correct disposition: narrator-invented NPCs flow extraction → `NpcMention` → `NpcPoolMember(drawn_from="narrator_invented")` → `_promote_pool_member_to_npc` → `Npc()` with the field-default `Disposition()` = **0 (neutral)**; the `-20` at `session.py:1533` fires **only** when `is_creature` (creature_id/threat_level/hp), and `WorldStatePatch.npcs_present` is populated **only** by Monster Manual injection and a debug command — never by the narrator. So "narrator-invented person spawns at -20" does **not** reproduce in current code. The real gap (and the story's actual value) was that **neither materialization seam emitted an OTEL span**, so the GM panel could not verify the neutral default — the exact "unexplained number" the deep-dive flagged. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `NpcPatch` has no `disposition` field, so AC2's "explicitly marks hostility" clause is not realizable at these two seams (disposition is always a *default* here). Narrator-authored/world-authored explicit hostility lives in `world_materialization.py` (`initial_disposition`), which was correctly out of scope for 72-5. If a future story wants the narrator to set NPC disposition directly, that seam — not these two — is where it belongs. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `_promote_pool_member_to_npc` hardcodes `provenance="default_neutral"` while reporting the live `int(npc.disposition)`. Affects `sidequest/server/narration_apply.py` (if 72-2/72-7 ever change the `Npc` default disposition, derive `provenance` from the actual value rather than hardcoding it, to avoid a label/value divergence). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `npc_spawn_disposition_span` `**attrs` passthrough has no "internal callers only" note. Affects `sidequest/telemetry/spans/disposition.py` (a one-line docstring note would guard future callers against smuggling unexpected span attributes). *Found by Reviewer during code review.*

## Design Deviations

None at setup time.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **No `-20` literal was flipped; the AC1 "fix" is delivered as observability + provenance, not a value change.**
  - Spec source: context-story-72-5.md, AC-1 / Technical Guardrails (lines 47–53)
  - Spec text: "ensure a narrator-invented, non-creature NPC reaches `_npc_from_patch` (or whatever seam materializes it) with `is_creature == False` so it spawns neutral (0) … **the fix is about provenance, not a blind flip of -20**."
  - Implementation: Confirmed (by trace + RED test showing correct values pre-fix) that invented persons already spawn at 0 and creatures at -20. Added `npc.spawn_disposition` OTEL span (provenance dial `default_neutral` / `default_creature_hostile`) at **both** materialization seams (`Session._npc_from_patch`, `_promote_pool_member_to_npc`). Changed no disposition value.
  - Rationale: The context and the SM assessment both anticipated the default branch is already correct for persons; the deliverable AC was the missing span (AC3) + its wiring proof (AC4). Flipping a literal would have been a no-op at best and a regression risk at worst.
  - Severity: minor
  - Forward impact: none — disposition values unchanged; 72-2 (preserve-on-promotion + reconcile), 72-6 (pool caps), 72-7 (identity drift) are unaffected. The new span gives those stories a ready GM-panel signal for spawn disposition.

### Reviewer (audit)
- **No `-20` literal flipped; AC1 delivered as observability + provenance** → ✓ ACCEPTED by Reviewer: The deviation is sound and was explicitly anticipated by the story context ("the fix is about provenance, not a blind flip of -20") and the SM routing flag. I independently re-traced every narrator-origin NPC-creation path and confirmed invented persons already spawn at 0 and creatures at -20 — flipping the literal would have been a no-op at best and an AC2 regression risk at worst. The RED run captured the correct pre-fix disposition values, proving the deliverable was the missing span, not a value change. Agrees with author reasoning.
- No undocumented deviations found. The diff changes no disposition value and adds only telemetry; behavior is identical to pre-change.