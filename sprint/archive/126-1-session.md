---
story_id: "126-1"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-1: [FATE] Verify + wire Fate-conflict harm to ablate stress/consequences, not core.hp

## Story Details
- **ID:** 126-1
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-17T21:14:04Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-17T20:39:02.340666Z | 2026-06-17T20:47:04Z | 8m 1s |
| red | 2026-06-17T20:47:04Z | 2026-06-17T21:01:17Z | 14m 13s |
| green | 2026-06-17T21:01:17Z | 2026-06-17T21:06:22Z | 5m 5s |
| review | 2026-06-17T21:06:22Z | 2026-06-17T21:14:04Z | 7m 42s |
| finish | 2026-06-17T21:14:04Z | - | - |

## Sm Assessment

**Routing → TEA (red phase).** Server-only `tdd` story. Branch `feat/126-1-fate-conflict-harm-ablates-stress` is cut and current at `origin/develop` (clone freshly pulled; the just-merged 126-7 FATE_THROW path is present). Context story written with 3 ACs.

**This is the lie-detector test for the entire ADR-144 Fate binding.** The open question: when a SEATED Fate conflict deals harm to a Fate PC, does it ablate the **Fate sheet** (stress track → four consequence slots) or does it leak into the legacy **`core.hp`** unified-model field (ADR-007, the 2026-06-14 hp_depletion track)? Fate PCs carry both in parallel. If harm reads/writes `core.hp`, the binding is HALF-WIRED — a direct SOUL violation ("Bind the Ruleset, Don't Balance It": the bound ruleset's engine must *replace* the native one, not layer on top).

**TEA — where to point the RED tests:**
- `sidequest/server/dispatch/fate_conflict.py` — the seated-conflict harm-application path (where harm currently lands).
- `sidequest/game/ruleset/fate_resolution.py` + `fate.py` — Fate resolution + module; the Fate sheet model (stress + consequence slots) lives here.
- `core.hp` / hp_depletion track (ADR-007 / ADR-114) — assert it stays **untouched** by Fate-conflict harm.
- Cross-ref ADR-144 (binding replaces native) and ADR-148 (sibling Fate-roll story, just landed — mirror its test shape).

**RED must cover, per the ACs:**
1. A failing test that proves *where harm currently lands* (stress vs core.hp).
2. Fate-conflict harm decrements Fate stress / fills a consequence and leaves `core.hp` untouched.
3. An **OTEL span** on the harm-application decision so the GM panel can verify which track was written (CLAUDE.md OTEL Observability Principle — this is the literal lie detector).
4. A **wiring/integration test** proving the harm path is reachable end-to-end from the live conflict dispatch, not just unit-tested in isolation.

**Test env:** server dispatch/handler tests need `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test` (`just pg-up`). Jira not configured (skip). No Fate native mechanics to balance — if you catch yourself tuning a dial to "fit," stop: the harm path is *removed* from the native engine and bound to the Fate sheet.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED — 3 failing (missing span) + 3 passing (invariant guards); pre-existing `test_fate_conflict.py` 22/22 still green.

**Test File:**
- `sidequest-server/tests/server/dispatch/test_fate_harm_routing.py` — 6 tests, committed `3ac6163d` on `feat/126-1-fate-conflict-harm-ablates-stress`.

**What I found (read this first, Dev):** the harm path is **already correctly wired**. `_resolve_attack`→`absorb_shifts` (`sidequest/server/dispatch/fate_conflict.py:537/170`) writes ONLY `fate_sheet.stress`/`consequences`; `core.hp` is never touched, and the native HP path is unreachable under a Fate ruleset (`dispatch_fate_action:771` fails loud; FateRulesetModule raises on d20-surface methods). So **AC-3's conditional "if harm currently reads core.hp: wire it" is FALSE — there is NO harm-routing rewrite to do.** Do NOT go hunting a core.hp leak to "fix"; the invariant guards (tests 1–2) already pass and prove it's clean. **GREEN = add the missing OTEL span only.**

**The one thing to implement (makes the 3 RED tests green):**
Emit a new `fate.harm.routed` span in `_resolve_attack` whenever an attack lands real harm (`shifts >= 1`) — placed AFTER the miss/tie early-return (line 536) and at/around the `absorb_shifts` call (line 537), so it fires for BOTH absorbed and taken-out outcomes but NOT on a miss. Contract:
- Helper `fate_harm_routed_span(*, actor, by, track, shifts, _tracer=None, **attrs)` beside the other `fate.*` helpers in `sidequest/telemetry/spans/fate.py`.
- Span name `fate.harm.routed`; attributes `field="harm_routed"`, `actor` (target), `by` (attacker), `track` ("physical"/"mental"), `shifts` (int), `sink="fate_sheet"`.
- Register `SPAN_ROUTES["fate.harm.routed"]` (component="fate") so the watcher/GM panel sees it (mirror `fate.exchange.*` route registration in the same file).
- `sink` is the lie-detector field: the GM panel reads it and confirms a Fate-conflict harm is NEVER routed to `core_hp`.

| Test | AC | Expected after GREEN |
|------|----|---------------------|
| test_attack_harm_lands_on_fate_sheet_and_leaves_core_hp_untouched | 2 | already green (guard) |
| test_taken_out_attack_leaves_core_hp_untouched | 2 | already green (guard) |
| test_missed_attack_emits_no_harm_routed_span | 3 | green; verifies span gates on real harm |
| test_attack_emits_fate_harm_routed_span_naming_the_fate_sheet_sink | 3 | RED→green (emit span + attrs) |
| test_taken_out_attack_still_emits_harm_routed_to_fate_sheet | 3 | RED→green (span fires on taken-out too) |
| test_dispatch_fate_action_routes_harm_to_fate_sheet_end_to_end | 1+3 | RED→green (reachable from dispatch) |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test-quality (meaningful assertions) | all 6 (assert on `sink`, `core.hp.current`, specific span presence/absence) | self-checked, 0 vacuous |
| #1 silent-fallback / SOUL "No Silent Fallbacks" (harm must never silently leak to core.hp) | `test_attack_harm_lands…` (asserts no `state_patch_hp` span) + `test_missed…` (no over-emit) | passing guards |
| OTEL coverage (CLAUDE.md OTEL principle — every subsystem decision emits a span) | the 3 `fate.harm.routed` tests | RED (drives the GREEN) |

**Rules checked:** 3 of 13 lang-review checks are applicable to this server-only, behavior-verify + observability story (the rest — path handling, async, deserialization, deps — have no surface here).
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Hephaestus) for GREEN — span emission only.

## Dev Assessment

**Implementation Complete:** Yes — observability-only, no behavior change (per TEA's verified finding that the harm path already routes correctly).

**Files Changed:**
- `sidequest-server/sidequest/telemetry/spans/fate.py` — new `fate_harm_routed_span()` helper + `SPAN_ROUTES["fate.harm.routed"]` (component "fate") + `__all__` export.
- `sidequest-server/sidequest/server/dispatch/fate_conflict.py` — import `fate_harm_routed_span`; emit it in `_resolve_attack` when an attack lands real harm (`shifts >= 1`), before the `absorb_shifts` marks, with `sink="fate_sheet"`.
- `sidequest-server/tests/server/dispatch/test_fate_harm_routing.py` — ruff-format only (TEA's RED tests, unchanged in substance).

**Span contract delivered (exactly TEA's spec):** `fate.harm.routed`, attrs `{field:"harm_routed", actor, by, track, shifts, sink:"fate_sheet"}`. Fires for absorbed AND taken-out outcomes; a miss/tie (`shifts <= 0`) emits nothing.

**Tests:** 6/6 harm-routing GREEN. No regression — `test_fate_conflict.py` 22/22, `tests/telemetry/` 412/412, wider `-k "fate and span"` 55/55. ruff check + format clean, pyright 0 errors.
**Branch:** `feat/126-1-fate-conflict-harm-ablates-stress` (pushed to origin; no PR — SM creates it at finish).

**Self-review (judgment checks):**
- Wired to a real consumer: the span is emitted from the production `_resolve_attack` harm path AND registered in `SPAN_ROUTES` so the watcher/GM panel routes it (component "fate") — not a dangling helper. The dispatch-entry wiring test proves reachability.
- Follows project patterns: mirrors the existing `fate_stress_applied_span` / `fate_taken_out_span` helper + route-registration shape in the same file.
- All ACs met: AC-2 invariant guarded (core.hp untouched), AC-3 routing-decision span emitted + dispatch wiring test green, AC-1 fate.* spine asserted at the dispatch layer.
- Error handling: none added — the harm path's fail-loud guards (`No Silent Fallbacks`) are pre-existing and untouched; the span is a passive emit.

**Handoff:** To Reviewer (Hermes) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A — all gates green (440 passed, ruff/pyright clean, 0 smells) |
| 2 | reviewer-edge-hunter | Yes | findings | 3 | confirmed 0, dismissed 2, deferred 1 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — assessed directly ([SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed directly ([TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed directly ([DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed directly ([TYPE]) |
| 7 | reviewer-security | Yes | clean | 0 | N/A — sanitized inputs, no PII/secrets, gated surface |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — assessed directly ([SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — enumerated directly ([RULE]) |

**All received:** Yes (3 enabled returned, 6 disabled pre-filled)
**Total findings:** 0 confirmed (blocking), 2 dismissed (with rationale), 1 deferred (non-blocking Delivery Finding)

**Edge-hunter finding dispositions:**
- E1 (line 523, medium) — non-{combat,social} category silently → `track="physical"`. **Deferred** → the `mental`/`track` derivation is **pre-existing** (not in this diff); the span faithfully mirrors `absorb_shifts`' track. Surfaced as a non-blocking Delivery Finding (the span actually *helps* by making this visible on the GM panel).
- E2 (line 541, medium) — span fires before `absorb_shifts`, which raises on an unknown track. **Dismissed** → `_default_stress` (fate_sheet.py:99-102) always provisions both `physical` + `mental`; no production path builds a partial sheet, so the raise is unreachable with real input, and TEA's contract requires the span to fire on the taken-out path.
- E3 (line 542, low) — empty `actor.name` → `by=""`. **Dismissed** → `EncounterActor.name` non-emptiness is a pre-existing invariant outside this diff; every `fate.*` span reports the configured name identically.

## Reviewer Assessment

**Verdict:** APPROVED

Observability-only change: one passive OTEL span (`fate.harm.routed`) + its helper + `SPAN_ROUTES` registration + a single emit at the one harm-application site. No behavior change (additive-only, 0 deletions in production logic). All gates green; the harm-ablation invariant is now both test-guarded and observable.

**Observations (15; tags: [EDGE] [SILENT] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE] all covered):**
1. [VERIFIED] Emit placement correct — `fate_conflict.py:541` fires only when `shifts >= 1` (after the `shifts <= 0` early-return 524-536), before `absorb_shifts:544`. Matches AC-3 and the taken-out test; the miss/tie path emits nothing (`test_missed_attack_emits_no_harm_routed_span` green).
2. [VERIFIED] Single harm site — `absorb_shifts` is called only from `_resolve_attack:544` (grep: lines 197/202 are its own error strings); Contests raise on `attack` (`:788`). One emit site fully covers harm — no missing path.
3. [VERIFIED] No-leak invariant is test-guarded — `core.hp` untouched is asserted by `test_attack_harm_lands…` + the taken-out test; structural separation holds (`FateRulesetModule` raises on d20-surface; `dispatch_fate_action:771` fails loud on non-Fate). Evidence: `_resolve_attack` (537-557) writes only `target_core.fate_sheet`.
4. [SEC] Security clean (subagent + own trace) — `actor=commit.target` sanitized at seal (`sanitize_player_text`, `:956`), `by=commit.actor` server-side seat identity, `track`/`shifts`/`sink` non-PII; GM panel behind Cloudflare Access (ADR-119). Complies lang-review #4/#11 + ADR-047.
5. [VERIFIED] `SPAN_ROUTES["fate.harm.routed"]` (`fate.py:154`) extract keys match the helper attrs; `component="fate"`, `event_type="state_transition"` — consistent with `fate.taken_out`/`fate.exchange.*`. GM-panel routing wired, not a dangling helper.
6. [TYPE] Helper fully annotated (`actor/by/track: str`, `shifts: int`, `sink: str = "fate_sheet"`, `_tracer`, `**attrs: Any) -> None`); immutable default; mirrors `fate_stress_applied_span` shape; pyright 0 errors. (type_design disabled — assessed directly.)
7. [DOC] Docstring + inline comments accurate ("fires once per attack that lands real harm", "sink the lie-detector field … never core_hp"). No stale/misleading docs. (comment_analyzer disabled — assessed directly.)
8. [SIMPLE] Minimal — one helper + one route + one 4-line call; no over-engineering, no dead code, additive-only. (simplifier disabled — assessed directly.)
9. [SILENT] No try/except/suppress added; passive span emit; `absorb_shifts` fail-loud guards (195/200) and `_resolve_attack` guards (508/511) untouched → No Silent Fallbacks preserved. (silent_failure_hunter disabled — assessed directly.)
10. [TEST] TEA's 6 tests carry specific assertions (span attrs, `core.hp` values, span absence on miss) + a dispatch-entry wiring test (fixture-driven, not source-grep — honors "No Source-Text Wiring Tests"). No vacuous assertions. (test_analyzer disabled — assessed directly.)
11. [EDGE] Edge-hunter's 3 findings all pre-existing or non-reachable (E1 deferred, E2/E3 dismissed — see dispositions above). None introduced by this diff; none Critical/High.
12. [RULE] Rule Compliance enumerated below — all applicable lang-review checks pass. (rule_checker disabled — enumerated directly.)
13. [LOW][EDGE] E1 surfaced as a follow-up (category→physical) — non-blocking; pre-existing.
14. [VERIFIED] `__all__` updated (`fate.py:1077`) so `from .fate import *` re-exports the helper; the `fate_conflict.py` import resolves (pyright clean). Wired end-to-end.
15. [VERIFIED] `sink` is a declarative routing marker, not a runtime core.hp-write detector — the no-leak guarantee is the behavior test + structural separation, the span documents the decision for the GM panel (dynamic `track` carries real info). Appropriate for AC-3 ("verify which track was written").

**Data flow traced:** player `FATE_ACTION` (`payload.target`, free text) → `sanitize_player_text` at seal (`dispatch_fate_action:956`) → `FateSealedCommit.target` → `_resolve_attack` reads `commit.target` → `fate_harm_routed_span(actor=commit.target, …)` → `Span.open` → watcher/`SPAN_ROUTES` → GM panel (Cloudflare-Access-gated). Safe: sanitized before the span; non-player surface.

**Pattern observed:** mirrors the existing `fate.*` helper + `SPAN_ROUTES` shape (`fate.stress.applied` `fate.py:130`, `fate.taken_out` `:377`) — house convention followed exactly at `fate.py:154`/`:355`.

**Error handling:** none added, correctly — a passive emit needs none; pre-existing fail-loud guards untouched.

### Rule Compliance (python lang-review, enumerated against the diff)
- #1 silent exceptions — no try/except/suppress added. ✓
- #2 mutable defaults — `sink: str = "fate_sheet"` immutable; no default containers. ✓
- #3 type annotations — `fate_harm_routed_span` fully annotated incl. `-> None`. ✓
- #4 logging/telemetry no sensitive data — sanitized fictional names + enums + ints + literal; no secrets/PII. ✓
- #5 path handling — no paths. N/A
- #6 test quality — specific assertions, wiring test present, no vacuous. ✓
- #7 resource leaks — `Span.open` is a `with` context manager. ✓
- #8 unsafe deserialization — none. N/A
- #9 async pitfalls — synchronous emit. N/A
- #10 import hygiene — explicit import + `__all__` update; no production star import. ✓
- #11 input validation — `commit.target` sanitized at boundary (`:956`). ✓
- #12 dependency hygiene — no dep changes. N/A
- #13 fix-introduced regressions — additive-only, 0 deletions; 440 tests green. ✓

### Devil's Advocate
Argue this is broken. The sharpest attack: **the span is a liar by construction.** `sink` is a hardcoded `"fate_sheet"`; the only call site never overrides it. So the field that supposedly lets the GM panel "verify the harm did not leak to core.hp" can *never* report `core_hp` — if a future refactor reintroduced a `core.hp` write on the Fate harm path, this span would still cheerfully announce `sink="fate_sheet"`, and the lie-detector would be blind to the exact lie it exists to catch. That is a real conceptual limit. The mitigation is that the *behavior* test (`core.hp` untouched) is the true guard and *would* fail on such a regression; the span is a declarative routing marker for the operator, and its dynamic `track` field does carry genuine per-hit information. Detector = span + test, not span alone — acceptable, but the team should not mistake the span for a runtime leak sensor. Second attack: the span fires **before** `absorb_shifts`, so a malformed `FateSheet` missing the computed stress track would record a "harm routed" event for harm that then raises and never lands — a misleading trace. Countered: `_default_stress` always provisions both tracks and no production path builds a partial sheet, so it is unreachable with real input. Third: a GM watching a `"hacking"`/`"movement"` Fate conflict would see `track="physical"` because `mental = category == "social"` treats every non-social category as physical — genuinely misleading, but **pre-existing** in the track derivation, not introduced here; if anything the new span *surfaces* the latent gap (logged as a follow-up). Fourth, the malicious-user angle: `sink` is unreachable from any payload, `actor` is sanitized, `by` is a server-side seat identity — no injection or spoof surface. Fifth, a stressed runtime: the emit is in-memory OTEL with no filesystem; a throwing `Span.open` would break the exchange, but that risk is identical for every existing `fate.*` span and is not introduced by this diff. Net: no defect that blocks; one pre-existing latent gap surfaced as a non-blocking finding.

**Handoff:** To SM (Themis) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): The Fate-conflict harm-ablation invariant (harm→sheet, core.hp untouched) was correct in code but had ZERO test coverage and no observability span — a latent regression risk the binding could have silently lost. Affects `sidequest/server/dispatch/fate_conflict.py` (`_resolve_attack`/`absorb_shifts`) + `sidequest/telemetry/spans/fate.py` (add `fate.harm.routed`). Now guarded by `tests/server/dispatch/test_fate_harm_routing.py`. *Found by TEA during test design.*
- **Question** (non-blocking): AC-3 also names "FATE_ROLL + confrontation.* spans" for the full live spine; those belong to the websocket/intent-router layer (siblings 126-7 landed, 126-2 backlog) and are deliberately out of this story's dispatch-level RED (see Design Deviations → AC-1 scoping). If the table wants a single end-to-end span census across the Fate spine, that is a separate observability story. *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. TEA's investigation matched exactly what the code does — harm already routes to the Fate sheet, `core.hp` untouched — so GREEN was a pure span-emission add with no surprises.

### Reviewer (code review)
- **Improvement** (non-blocking): `_resolve_attack` derives the stress `track` from `mental` (= `encounter.category == "social"`), so a seated Fate attack in any non-`{combat, social}` category silently routes to `track="physical"` — now made visible on the GM panel by the new `fate.harm.routed` span. Affects `sidequest/server/dispatch/fate_conflict.py` (consider validating `encounter.category ∈ {combat, social}` for a seated Fate attack, or explicitly documenting + testing the physical-default contract). Pre-existing in the track derivation — surfaced by this story's span, not introduced by it. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-2 "wire" half is moot — harm already routes to the Fate sheet; this is a Verify + observability story**
  - Spec source: context-story-126-1.md, AC-2/AC-3 ("If harm currently reads core.hp: wire the harm-application path…")
  - Spec text: "Harm from the conflict ablates the Fate stress/consequence track, NOT core.hp" / "If harm currently reads core.hp: wire the harm-application path"
  - Implementation: Investigation (Explore sweep) proved `_resolve_attack`→`absorb_shifts` (`fate_conflict.py:537/170`) writes ONLY `fate_sheet.stress`/`consequences`; `core.hp` is never touched and the native HP path is unreachable under a Fate binding (`dispatch_fate_action:771` fails loud on non-Fate ruleset; FateRulesetModule raises on d20-surface methods). So the AC-3 conditional "if harm reads core.hp" is FALSE — no harm-routing rewrite is required. RED therefore targets the two genuine gaps: (a) no test asserts the invariant, (b) no OTEL span records the routing decision.
  - Rationale: TDD RED on already-correct behavior would be vacuously green; the honest RED is the missing lie-detector span + invariant guards.
  - Severity: minor
  - Forward impact: Dev's GREEN is span-emission + (optional) no behavior change to absorb_shifts; if Dev finds a core.hp write I missed, the guard tests catch it.
- **New OTEL span `fate.harm.routed` shape is TEA-specified (the AC named the need, not the schema)**
  - Spec source: context-story-126-1.md, AC-3
  - Spec text: "An OTEL span on the harm-application decision so the GM panel can verify which track was written"
  - Implementation: Tests assert a new `fate.harm.routed` span emitted in `_resolve_attack` when shifts>=1, attrs `{field:"harm_routed", actor, by, track ("physical"/"mental"), shifts, sink:"fate_sheet"}`, registered in `SPAN_ROUTES` (component="fate"). `sink` is the lie-detector field — the GM panel confirms it is never `core_hp`.
  - Rationale: AC requires a routing-decision span but does not name it; chose a name/attrs consistent with existing `fate.stress.applied`/`fate.taken_out` helpers in `telemetry/spans/fate.py`.
  - Severity: minor
  - Forward impact: Dev implements `fate_harm_routed_span(...)` to this contract; UI/GM-panel can later read `sink`.
- **AC-1 "FATE_ROLL + confrontation.* spans" scoped to the dispatch/exchange layer, not the websocket/intent-router layer**
  - Spec source: context-story-126-1.md, AC-1
  - Spec text: "confirm the mechanical spine fires: FATE_ROLL + fate.* + confrontation.* OTEL spans present … confrontation != None"
  - Implementation: RED drives the production dispatch entry `dispatch_fate_action` (confrontation/encounter != None) and asserts the `fate.*` spine spans (`fate.exchange.committed/order/resolved` + new `fate.harm.routed`). The FATE_ROLL broadcast (FateThrowHandler, landed in sibling 126-7) and intent-router `confrontation.*` re-seat spans (sibling 126-2) are NOT re-exercised here.
  - Rationale: story scope (spec-authority #1) is the harm-ablation lie-detector; the FATE_ROLL/router seam is owned by 126-7/126-2 and already has wiring tests (`test_fate_throw_handler_wiring.py`). Re-testing it here would duplicate, not verify the marquee.
  - Severity: minor
  - Forward impact: none — sibling stories own those spans; if the table wants a single end-to-end span census, that is a separate observability story.

### Dev (implementation)
- No deviations from spec. Implemented the `fate.harm.routed` span exactly to TEA's contract (name, attributes, emit site, route registration) with no added abstraction and no behavior change to the harm path.

### Reviewer (audit)
- **TEA #1 (AC-2 "wire" half moot — Verify + observability story)** → ✓ ACCEPTED by Reviewer: the diff confirms `_resolve_attack`→`absorb_shifts` writes only the Fate sheet; the "verify, don't rewrite" reframing is correct and well-evidenced.
- **TEA #2 (`fate.harm.routed` span shape TEA-specified)** → ✓ ACCEPTED by Reviewer: the chosen name/attrs are consistent with the existing `fate.stress.applied`/`fate.taken_out` helpers, and Dev implemented to the contract exactly.
- **TEA #3 (AC-1 scoped to the dispatch/exchange layer)** → ✓ ACCEPTED by Reviewer: the FATE_ROLL broadcast and intent-router `confrontation.*` spans are owned by siblings 126-7 (landed, `test_fate_throw_handler_wiring.py`) and 126-2; re-exercising them here would duplicate, not verify the marquee.
- **Dev (No deviations from spec)** → ✓ ACCEPTED by Reviewer: the diff matches TEA's contract with no undocumented divergence.
- **Undocumented-divergence check:** one behavior surfaced — the span reports `track="physical"` for non-`{combat,social}` categories — but this is **pre-existing** in the `mental`/`track` derivation, not a deviation introduced by TEA/Dev. Recorded as a non-blocking Delivery Finding rather than FLAGGED.