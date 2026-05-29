---
story_id: "59-25"
jira_key: ""
epic: "59"
workflow: "trivial"
---
# Story 59-25: Multi-key entity extraction in leak_audit

## Story Details
- **ID:** 59-25
- **Jira Key:** (none — SideQuest does not use Jira)
- **Workflow:** trivial
- **Stack Parent:** none
- **Repos:** sidequest-server

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-29T13:21:26Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-29T13:08:17Z | 2026-05-29T13:09:48Z | 1m 31s |
| implement | 2026-05-29T13:09:48Z | 2026-05-29T13:14:30Z | 4m 42s |
| review | 2026-05-29T13:14:30Z | 2026-05-29T13:21:26Z | 6m 56s |
| finish | 2026-05-29T13:21:26Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): The `leak_audit.py` module docstring (line 15) calls the audit "Sebastien's lie-detector". The leak audit is a backend OTEL emit feeding the GM panel — a Keith/dev observability tool, not a player-facing feature. Per CLAUDE.md audience guidance this Sebastien attribution is the named anti-pattern (OTEL/GM-panel ≠ Sebastien). Affects `sidequest/telemetry/leak_audit.py` (reword to "the GM-panel lie-detector"). Left untouched here — out of 59-25 scope (cosmetic, no test impact). *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (non-blocking): `scenario_clue` keys its dispatch entity under `params["fact_id"]` (`sidequest/agents/subsystems/scenario_clue.py:83`), which is NOT in `_ENTITY_ID_KEYS`. A redacted `scenario_clue` dispatch therefore yields `_redacted_entity_id=None`. This is *inert today* — the leak audit's `entity_tokens_by_id` map is built solely from the NPC registry (`orchestrator.py:_entity_tokens_for_registry` 1546–1561, keyed by NPC `name`), so a `fact_id` resolves to no tokens and adding it to the tuple would only bump `redact_tag_count`, detecting nothing. Auditing scenario-clue leakage is a *new capability* (would need both the key AND fact-token population), not a bug in this fix, and is outside the story's documented three-key entity scope. Affects `sidequest/telemetry/leak_audit.py` + the call-site token-map builder (a future story would add `fact_id` to the tuple and populate clue tokens in `_entity_tokens_for_registry`). *Found by Reviewer during code review.* [SEC]

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. (Implemented the multi-key extraction via a module-level `_redacted_entity_id` helper applied to both loops, rather than duplicating the inline key-tuple per loop. The context explicitly offered this as Dev's call — "Consider extracting a tiny local helper to enforce the symmetry mechanically" — so this is the spec-blessed path, chosen because mechanical symmetry is the entire point of the story. Not a deviation.)
  → ✓ ACCEPTED by Reviewer: The helper is the spec-blessed option (context line 86 "Consider extracting a tiny local helper to enforce the symmetry mechanically"); both loops are now byte-identical at the extraction step, which is exactly the anti-drift property the 59-24→59-25 lineage demands. Sound call, not scope creep.

### Reviewer (audit)
- No undocumented deviations found. The diff implements precisely the context's "Suggested extraction" (multi-key `("target","npc_name","actor")`), applied symmetrically to both branches, with no new OTEL span and no hard-fail on keyless dispatches — all matching the documented scope boundaries. The `_redacted_entity_id` helper's `None`-on-keyless behavior is the spec's explicit "narrow the silent-drop surface without hard-failing" intent, not an undocumented choice.

## Sm Assessment

**Premise verified (not stale).** Epic 59 has a history of stale playtest-bug premises, so I confirmed the code before setup. Both branches of `audit_canonical_prose` in `sidequest-server/sidequest/telemetry/leak_audit.py` extract the redacted entity ONLY from `params.get("target")` — per_player loop at line 82 and cross_player loop (added in 59-24) at line 96. The fix (widen to `("target","npc_name","actor")`) is real and applies to both loops. Test bar: a redacted `npc_agency` dispatch keyed on `params['npc_name']` whose name leaks into prose must yield `leaks_detected>=1` (fails against current main); cover BOTH per_player and cross_player.

**Maturity caveat (why p3):** gated on the Group G perception rewriter (ADR-104/105 partial) actually emitting redacted `npc_agency`/`magic_working` dispatches. Current production redaction is mostly `distinctive_detail_hint` where `target` is already correct. Medium-confidence security finding — fix the latent false-negative now, don't over-invest.

**Pre-setup blocker cleared:** dangling PR #516 (story 67-7, AC5 telemetry) was open and non-draft against a `done` story, tripping the merge gate. Per user decision, squash-merged #516 into `develop` (branch deleted) so the code matches 67-7's archived `done` status.

**Routing:** 1-point trivial → phased workflow → dev (implement). Single repo: `sidequest-server`. Branch `feat/59-25-leak-audit-multi-key-entity` created off `develop`. Context found and referenced.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/telemetry/leak_audit.py` — Added module-level `_ENTITY_ID_KEYS = ("target", "npc_name", "actor")` and a `_redacted_entity_id(dispatch)` helper that returns the first present string entity key. Replaced the single-key `params["target"]` extraction in BOTH the per_player loop and the cross_player loop with a call to the helper, keeping the two branches mechanically symmetric.
- `tests/telemetry/test_leak_audit.py` — Extended `_redacted`/`_cross` fixtures with an optional `subsystem` kwarg (backward-compatible default) so new tests read as faithful `npc_agency`/`magic_working` dispatches. Added 4 tests: AC1 npc_agency `npc_name` per_player, AC2 npc_agency `npc_name` cross_player, AC3 magic_working `actor`, AC4 multi-key clean-prose no-false-positive (asserts `redact_tag_count==2`, `leaks_detected==0`).

**Tests:** 10/10 passing (GREEN). RED first confirmed: the 4 new tests failed against single-key code (`leaks_detected=0` / `redact_tag_count=0`), 6 pre-existing passed. After fix: all 10 pass. Ruff check + format clean.

**Wiring:** `audit_canonical_prose` has two production call sites in `sidequest/agents/orchestrator.py` (lines 3071, 3408 — the narrator canonical-leak path). This is a behavior fix to already-wired code; the widened extraction flows into the existing `narrator.canonical_leak_audit` OTEL span (no new span, per scope).

**Scope adherence:** Did not touch `redact_dispatch_package`, orchestrator call sites, fidelity/secrets handling, or add a hard-fail for keyless dispatches — all explicitly out of scope. The `_redacted_entity_id` helper returns `None` for keyless/non-dict params (narrows the silent-drop surface without hard-failing, per the No-Silent-Fallback nuance in context).

**Branch:** `feat/59-25-leak-audit-multi-key-entity` (pushed)

**Handoff:** To review (Westley).

## Context Reference

Story context available at: `sprint/context/context-story-59-25.md`

**Summary:** Multi-key entity extraction in leak_audit (59-24 follow-up). Close a gap where `npc_agency` and `magic_working` subsystem dispatches tagged for redaction are not leak-detected because their entity identifiers live under different param keys (`npc_name` and `actor` respectively, not `target`). Affects both per_player and cross_player audit branches. 1-point trivial fix: widen the key extraction in `audit_canonical_prose` to check `("target", "npc_name", "actor")`, add tests pinning both branches.

## Subagent Results

Toggles (`workflow.reviewer_subagents`): only `preflight` and `security` enabled; the other 7 disabled via settings.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (tests 10/10 GREEN, ruff clean, pyright 0 errors, 0 smells) | N/A — confirmed clean |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 1 high (fact_id omission) + low ordering note | confirmed 0 blocking, deferred 1 (captured as Delivery Finding), 1 low verified-acceptable |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (2 enabled subagents returned; 7 disabled and pre-filled)
**Total findings:** 0 confirmed-blocking, 1 deferred (with rationale), 1 low verified-acceptable

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** `SubsystemDispatch.params` (router-emitted) → `_redacted_entity_id` first-present-string-key extraction over `("target","npc_name","actor")` → `redacted_entities` accumulator → token lookup in `entity_tokens_by_id` (NPC registry, built by `orchestrator.py:_entity_tokens_for_registry`) → substring scan of canonical prose → `LeakAuditResult` + `narrator.canonical_leak_audit` OTEL span. Safe because the entity-id never becomes the search pattern directly (Zork constraint preserved — tokens come from the authoritative registry, verified `leak_audit.py:103-111` unchanged).

**Observations (≥5):**
- [VERIFIED] Exhaustiveness of `_ENTITY_ID_KEYS` against all 7 registered subsystems — evidence: `intent_router.py:118-150` param contract + per-subsystem source. distinctive_detail_hint→`target`, npc_agency→`npc_name`, magic_working→`actor` are the only three carrying a registry-resolvable entity identifier; confrontation(`type`), scenario_clue(`fact_id`), movement(`direction`), reflect_absence(no params) do not. Complies with the No-Silent-Fallbacks rule *as scoped* — see [SEC] deferral for the fact_id edge.
- [VERIFIED] Branch symmetry — evidence: `leak_audit.py:105-129`, both per_player and cross_player loops now call the identical `_redacted_entity_id(d)`; mechanically drift-proof, which is the entire point of the 59-24→59-25 lineage.
- [VERIFIED] No false positives — evidence: `_redacted_entity_id` guards `isinstance(value, str)` (rejects dict/list/None param values) and AC4 (`test_multi_key_no_false_positive_when_prose_clean`) exercises both branches with clean prose asserting `leaks_detected==0, redact_tag_count==2`.
- [VERIFIED] OTEL span preserved — evidence: `leak_audit.py:121-126`, `narrator.canonical_leak_audit` fires unconditionally; no new span added (matches scope). The GM-panel lie-detector keeps reporting.
- [SEC] **Deferred (non-blocking):** `fact_id` (scenario_clue entity key) is absent from `_ENTITY_ID_KEYS`. Accurate observation, but **inert today** — `entity_tokens_by_id` is keyed only by NPC name (`orchestrator.py:1546-1561`), so a fact_id resolves to zero tokens; adding it would bump `redact_tag_count` and detect nothing. Auditing clue leakage is a new capability, not a defect in this fix, and is outside the story's documented three-key entity scope (context "Assumptions": *"The documented entity-identifier keys are target, npc_name, actor"*). Captured as a Delivery Finding for a future story.
- [SEC] **Low / verified-acceptable:** first-present-key-wins ordering in `_redacted_entity_id` — if a dispatch carried both `target` and `npc_name`, only `target` would be read. Subsystem param shapes are mutually exclusive (verified against subsystem sources), so unreachable in practice. Acceptable.
- [TEST] *(subagent disabled)* — reviewer self-assessed: the 4 new tests are behaviorally meaningful (assert `leaks_detected>=1` + entity-in-list, not vacuous truthy), each pins a distinct key/branch, and AC4 is a real over-collection regression guard. RED-then-GREEN was confirmed by Dev (4 failed pre-fix). No vacuous assertions.
- [DOC] *(subagent disabled)* — reviewer self-assessed: the `_ENTITY_ID_KEYS` comment and `_redacted_entity_id` docstring are accurate and name the single extension point. Pre-existing module-docstring mis-attribution ("Sebastien's lie-detector", line 15) already logged by Dev as a non-blocking finding — correctly out of scope here.
- [TYPE] *(subagent disabled)* — reviewer self-assessed: `_redacted_entity_id(dispatch: SubsystemDispatch) -> str | None` is fully annotated, returns a clean Optional; pyright reports 0 errors. No stringly-typed regression introduced.
- [EDGE] *(subagent disabled)* — reviewer self-assessed: edge cases covered — non-dict params (`isinstance` guard → None), keyless dispatch (→ None, intentional soft-drop), empty token list (existing `if not token` guard at `:105`). No new unhandled boundary.
- [SILENT] *(subagent disabled)* — reviewer self-assessed: the `None`-on-keyless return is a *documented, scoped* soft-drop (context explicitly defers hard-failing keyless dispatches), not an unintended swallowed error. Narrows — does not widen — the prior silent-drop surface.
- [SIMPLE] *(subagent disabled)* — reviewer self-assessed: helper extraction is the minimal change that enforces symmetry; no over-engineering, no dead code. 1-pointer stays a 1-pointer.
- [RULE] *(subagent disabled)* — reviewer self-assessed via Rule Compliance section below; no violations.

### Rule Compliance

- **No Silent Fallbacks (CLAUDE.md, critical):** The widening *narrows* the silent-drop surface (3 keys vs 1). The remaining `None`-on-keyless drop is explicitly spec-scoped (context: hard-failing keyless dispatches is "a separate future concern"). The one residual gap (fact_id) is inert and deferred. COMPLIANT as scoped.
- **OTEL Observability (CLAUDE.md):** `narrator.canonical_leak_audit` span unchanged and still fires every turn. COMPLIANT.
- **Zork constraint (SOUL.md):** Entity-token-set vs prose matching unchanged; entity ids never used as raw search patterns. COMPLIANT (`leak_audit.py:103-111`).
- **No Stubbing / No half-wired features:** Behavior fix to already-wired code (2 production call sites in `orchestrator.py`); fully reachable. COMPLIANT.
- **Tenant isolation:** N/A — single-tenant personal project, no tenant-scoped types in the diff.
- **Test quality (lang-review #6):** No `assert True`, no vacuous truthy asserts, no skips, no mis-targeted mocks. COMPLIANT.
- **Mutable defaults / resource leaks / unsafe deserialization / async pitfalls (lang-review #2,#7,#8,#9):** None present in the diff (pure function, no I/O, no defaults). COMPLIANT.

### Devil's Advocate

Let me argue this code is broken. *Claim 1: the fix is incomplete and gives false safety.* The security subagent is right that `fact_id` is a real entity key the tuple misses — and isn't a leak-detector that silently misses a whole subsystem the exact sin this story exists to punish? Rebuttal: I measured it. The audit's entity namespace is the NPC registry (`_entity_tokens_for_registry`, NPC names only); fact_ids never resolve to tokens, so the miss is inert — adding fact_id detects nothing without a separate clue-token feature. Confirming-but-deferring is the honest disposition, and I captured it so it isn't lost. *Claim 2: first-key-wins is a latent bug.* If a malicious or confused router emitted a dispatch with both `target` and `actor`, the audit reads only `target` and might scan the wrong entity. Rebuttal: subsystem param shapes are mutually exclusive (distinctive_detail vs magic_working are different handlers with different pydantic shapes); a dual-key dispatch is unreachable, and even if it occurred, the redact flag covers a single entity per dispatch. Low severity, noted. *Claim 3: the `None` soft-drop hides keyless redacted dispatches.* A redacted dispatch with no recognized key vanishes from the audit silently — that's a false negative. Rebuttal: true in the abstract, but the story explicitly scopes hard-failing keyless dispatches OUT ("separate future concern"), and the widening strictly reduces the keyless surface vs. main. *Claim 4: what if params is a populated dict but the value is an int id (e.g. `{"target": 4471}`)?* Then `isinstance(value, str)` rejects it and the entity is dropped. Rebuttal: this is pre-existing behavior (main already required `isinstance(target, str)`), entity ids are strings throughout the registry (`member.name`), and changing it is out of scope. No new regression. *Stressed-input angle:* huge prose / huge token sets — the scan is `O(entities × tokens)` substring search, unchanged from main; no new perf cliff. Conclusion: no claim survives as a blocker. The change is correct, minimal, well-tested, and faithful to scope.

**Pattern observed:** Spec-blessed helper extraction enforcing branch symmetry — good pattern at `leak_audit.py:34-50`.
**Error handling:** Defensive `isinstance` guards on both params-dict and value-type; no exceptions thrown on malformed input (`leak_audit.py:45-50`).
**Handoff:** To SM (Vizzini) for finish-story.