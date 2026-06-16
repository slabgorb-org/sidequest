---
story_id: "122-4"
jira_key: ""
epic: "122"
workflow: "tdd"
---
# Story 122-4: Narrow orbital/intent from full Session to a 4-field read Protocol

## Story Details
- **ID:** 122-4
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T02:39:30Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T02:17:40.990894Z | 2026-06-16T02:18:45Z | 1m 4s |
| red | 2026-06-16T02:18:45Z | 2026-06-16T02:25:50Z | 7m 5s |
| green | 2026-06-16T02:25:50Z | 2026-06-16T02:31:44Z | 5m 54s |
| review | 2026-06-16T02:31:44Z | 2026-06-16T02:39:30Z | 7m 46s |
| finish | 2026-06-16T02:39:30Z | - | - |

## Sm Assessment

**Story selected by Keith (overriding the SM's p1 recommendation of 119-3).** 122-4 is a sound, well-scoped pick: a 3pt behavior-preserving refactor in epic-122 (ADR-147 Honest Layering), with siblings 122-1 and 122-2 already done+approved, so the pattern is established. Server-only, single repo, no `depends_on`. Merge gate clear (only open server PR #893 is DRAFT, non-blocking).

**Scope is tight and legible:** narrow `orbital/intent`'s dependency from a full `Session` object to a 4-field read-only `Protocol`, killing one upward import edge. No library extraction, no logic changes — only the type contract at the seam.

**Handoff to TEA (RED phase):** First task is investigation — locate the orbital/intent module in `sidequest-server/sidequest/orbital/`, identify exactly which `Session` fields it reads (the "4 fields"), and pin those before defining the Protocol. Tests must (a) lock existing behavior, (b) prove a 4-field Protocol stand-in satisfies the seam, and (c) include a wiring/import-direction assertion consistent with epic-122's law (foundation <- {game,genre,orbital,magic,interior} <- server). Reference ADR-147 for the layering doctrine. Watch for the project rule: every test suite needs a wiring test.

**Risk note:** "approximately 4 fields" is the epic's estimate, not verified. TEA/Dev should confirm the actual read-set; if it's materially more than 4, log a Delivery Finding rather than forcing the count.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest/orbital/intent.py` — added `@runtime_checkable` `OrbitalIntentSession` Protocol (5 members: `orbital_content`, `orbital_scope`, `clock`, `party_body_id`, `plotted_course`); narrowed `handle_orbital_intent`'s param to it; dropped `from sidequest.server.session import Session`; read the course from `session.plotted_course` instead of the private `session._snapshot.plotted_course`.
- `sidequest/server/session.py` — added a `plotted_course` property returning `self._snapshot.plotted_course` (the clean accessor that lets a real `Session` satisfy the Protocol); added `PlottedCourse` to the `TYPE_CHECKING` imports.
- `tests/orbital/test_intent_session_protocol_122_4.py` — corrected one over-specified assertion (see Design Deviations → Dev).

**Implementation notes:**
- The orbital→server upward import edge is gone; `sidequest/orbital/` is now entirely server-pure (locked by `test_orbital_tier_is_server_pure`), pre-paying part of 122-5's CI guard.
- Protocol type imports are under `if TYPE_CHECKING:` (annotations are lazy strings via `from __future__ import annotations`), so no new runtime imports and no circular-import risk.
- Behavior fully preserved: drill-in/out logic untouched; the only logic-adjacent change is the `_snapshot` → property indirection, which returns the same value.

**Tests:** 405/405 passing (GREEN) — story file 12/12, full orbital tier + handler regression 393/393. Lint clean (ruff), type-clean (pyright) on both changed source files.
**Branch:** `feat/122-4-orbital-intent-narrow-session-protocol` (pushed)

**Handoff:** To Reviewer (Hermes) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 blockers (5 observations) | confirmed 0, dismissed 1 (isinstance claim, challenged), deferred 0 |
| 2 | reviewer-edge-hunter | Yes | findings | 3 (1 med, 2 low) | confirmed 3 (all non-blocking), dismissed 0, deferred 0 |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [TYPE] below) |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — assessed manually (see Rule Compliance) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 3 confirmed (all non-blocking, Low/Medium), 1 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A clean, minimal, behavior-preserving layering refactor. The orbital→server upward import edge is removed (ADR-147), the orbital tier is now fully server-pure, and the private `_snapshot` reach-through is replaced by a clean accessor. 405/405 tests green; ruff + pyright clean. No Critical or High findings from any specialist or my own audit.

**Data flow traced:** `handlers/orbital_intent.py:59` passes `room.session` (always a concrete `Session`, sourced from a typed property that raises if unbound — no silent fallback) → `handle_orbital_intent(session: OrbitalIntentSession, intent)`. The function reads `orbital_content`, `clock.t_hours`, `party_body_id`, `plotted_course`, reads+writes `orbital_scope`. `Session` structurally satisfies all five members (the newly-added `plotted_course` property closes the gap). Safe: no external input, no auth/DB/network/injection surface touched.

**Pattern observed:** in-tier `@runtime_checkable Protocol` narrowing — the same ADR-147 layering doctrine as the approved 122-1/122-2 siblings, applied to a type seam rather than a helper relocation. `sidequest/orbital/intent.py:35`.

**Error handling:** `OrbitalContentUnavailableError` still raises loudly when `orbital_content is None` (`intent.py:69-73`); behavior unchanged. `Session.plotted_course` proxies a Pydantic field that always exists (default `None`) — no new exception path.

### Observations (8+)
- `[VERIFIED]` Protocol surface is complete and exact — every `session.` access (intent.py lines 69/85/98/99/102/107/118/119/122/128/145/147) maps onto exactly one of the 5 declared members; none missing, none unused. Checked against SOUL "No Stubbing" (all members are live) and No-Silent-Fallbacks (raise path intact).
- `[VERIFIED]` Behavior preserved — drill-out branch is byte-for-byte identical to `develop` (confirmed via `diff`); `Session.plotted_course` returns the same `self._snapshot.plotted_course` value. evidence: `git diff` shows only signature + import + one accessor line changed in the function body.
- `[VERIFIED]` Layering law satisfied — `from sidequest.server.session import Session` removed from `intent.py`; AST scan (`test_orbital_tier_is_server_pure`) walks `TYPE_CHECKING` blocks and confirms zero residual `sidequest.server` imports tier-wide. Complies with ADR-147.
- `[EDGE]` `[MEDIUM→LOW]` Protocol doesn't enforce the `orbital_scope` setter (intent.py:50) — a read-only-property impl would pass `isinstance` then `AttributeError` at line 122. Downgraded to non-blocking: the docstring already documents "read **and written**," and the sole production impl (`Session`) has a setter. No change required.
- `[EDGE]` `[LOW]` `get_type_hints(OrbitalIntentSession)` would `NameError` on the `TYPE_CHECKING`-only annotation names. Latent only — no caller introspects this Protocol; `isinstance` does not evaluate hints. Non-blocking; same pattern is used throughout the codebase (incl. `Session` itself).
- `[EDGE]` `[LOW]` test asserts on CPython-private `_is_runtime_protocol` internals (test file) — brittle across Python versions; redundant with the isinstance-based conformance test. Non-blocking test-robustness nit.
- `[SEC]` Clean — security specialist confirmed no widened surface (read-only property proxies already-reachable snapshot state), no injection/secrets/info-leak, and the `runtime_checkable` Protocol is never used as a production auth/isinstance gate. evidence: SEC_RESULT status: clean, 4 rules checked, 0 violations.
- `[TYPE]` (subagent disabled — assessed manually) Type design is sound: minimal Protocol, accurate member set, `runtime_checkable` justified (needed for the conformance tests, harmless in prod). I empirically confirmed on Python 3.14.4 that `isinstance` against this attribute-only `runtime_checkable` Protocol **does** check data-attribute presence (`missing-b -> False`) — so the conformance tests genuinely prove what they claim.
- `[SILENT]` (subagent disabled — assessed manually) No swallowed errors or silent fallbacks introduced; the only raise path (`OrbitalContentUnavailableError`) is preserved.
- `[TEST]` (subagent disabled — assessed manually) Tests are non-vacuous and cover all 5 ACs incl. a real-Session wiring test and an AST layer guard; the one LOW robustness nit is logged as a non-blocking improvement.
- `[DOC]` (subagent disabled — assessed manually) Docstrings on both the Protocol and the new property are accurate and reference ADR-147; the Protocol docstring correctly documents `orbital_scope` writability.
- `[SIMPLE]` (subagent disabled — assessed manually) No over-engineering; the change is the minimal narrowing. `TYPE_CHECKING` imports avoid runtime cost and circular-import risk.
- `[RULE]` (subagent disabled — assessed manually) See Rule Compliance below — all applicable server rules pass.

### Rule Compliance
| Rule (server CLAUDE.md / SOUL) | Applies to | Verdict |
|---|---|---|
| No Silent Fallbacks | `intent.py` raise path; `Session.plotted_course` | ✓ compliant — `OrbitalContentUnavailableError` raised loudly; property is a direct proxy, no fallback |
| No Stubbing | `OrbitalIntentSession` Protocol | ✓ compliant — live type constraint, all 5 members in active use |
| Verify Wiring (non-test consumer) | `handlers/orbital_intent.py:59` | ✓ compliant — production caller passes `room.session`, which conforms |
| Every Test Suite Needs a Wiring Test | test file | ✓ compliant — `test_real_session_satisfies_protocol_and_works` + AST scan |
| No Source-Text Wiring Tests (use AST/reflection, not grep) | import-direction tests | ✓ compliant — uses `ast.parse`/`ast.walk`, not `read_text()` grep |
| OTEL Observability (subsystem decisions) | unchanged | ✓ N/A — pure type narrowing; the `emit_course_render_overlay` span (intent.py:79) is untouched. "Not needed for cosmetic/structural changes." |
| ADR-147 import-direction law | `sidequest/orbital/` tier | ✓ compliant — orbital→server edge removed; tier server-pure |

### Devil's Advocate
Suppose this code is broken. Where would it bite? The most plausible failure is the `runtime_checkable` Protocol giving false confidence: if Python's `isinstance` ignored data attributes (as the preflight claimed), then `test_real_session_satisfies_protocol_and_works` and `test_standin_conforms_to_runtime_protocol` would be vacuous, and a `Session` missing `plotted_course` could slip through — silently restoring the layering bug class. I did not take this on faith: I ran an empirical probe on the actual 3.14.4 runtime and a `Missing`-attribute object returned `isinstance -> False`. The claim is false here; the tests are real. A second attack: a confused future contributor adds an orbital implementor that exposes `orbital_scope` as a read-only property — `isinstance` passes, then `intent.py:122` throws `AttributeError` at runtime on the first drill. This is a genuine sharp edge, but it requires inventing a *new* non-Session implementor (none exists), and the Protocol docstring warns "read and written." A third: `get_type_hints` on the Protocol would `NameError` — but nothing calls it; Pydantic/FastAPI never see this Protocol. A fourth, subtler one: does storing drill-out scope as `"coyote"` vs `"<root>"` ever diverge downstream? I traced it — a subsequent drill_out from `coyote` (parent `None`) resolves to `system_root()`, identical to starting from `<root>`; render output centers on coyote either way. No divergence. A fifth: could the new property mask a write? `handle_orbital_intent` only *reads* `plotted_course`; the property is read-only, so an accidental future write fails loudly rather than silently corrupting `_snapshot`. Net: the sharp edges are all latent, documented, or empirically disproven. Nothing rises to blocking. Verdict stands: APPROVED.

**Handoff:** To SM (Themis) for finish-story.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavior-preserving refactor that changes a type contract at a seam — needs both regression coverage (real Session still works) and new-contract coverage (narrow Protocol accepted), plus the ADR-147 import-direction wiring test.

**Test Files:**
- `tests/orbital/test_intent_session_protocol_122_4.py` — 12 tests: Protocol existence/shape, behavioral narrowing against a non-Session stand-in, `_snapshot` reach-through tripwire, real-Session conformance (production-caller regression), and AST import-direction scan.

**Tests Written:** 12 tests covering 5 derived ACs (no ACs were in the YAML — TEA defined them from a source audit of `handle_orbital_intent`).
**Status:** RED — 11 fail as intended, 1 already green (`test_standin_without_orbital_content_raises`: the no-content guard raises before reaching the un-narrowed surface, so it is valid and stays green). Pre-existing `tests/orbital/test_intent.py` (7) + `tests/handlers/test_orbital_intent_handler.py` (6) all still pass — no collateral breakage.

### Derived Acceptance Criteria (no ACs in YAML)
1. A `@runtime_checkable` `OrbitalIntentSession` Protocol exists in `sidequest.orbital.intent`.
2. `handle_orbital_intent`'s `session` param is annotated with the Protocol, not `Session`.
3. The function runs correctly against a minimal non-`Session` stand-in (view_map / drill_in / drill_out, scope read+write).
4. The private `session._snapshot.plotted_course` reach-through is gone — course is read from `session.plotted_course`; a real `Session` still conforms (production caller unbroken).
5. `sidequest/orbital/intent.py` no longer imports `sidequest.server`; the whole orbital tier is server-pure.

### Rule Coverage

| Rule (source) | Test(s) | Status |
|---------------|---------|--------|
| ADR-147 import-direction law (no domain→server upward edge) | `test_intent_module_no_longer_imports_server`, `test_orbital_tier_is_server_pure` | failing |
| "Every test suite needs a wiring test" (server CLAUDE.md) | `test_real_session_satisfies_protocol_and_works` (production caller passes real `room.session`), AST scan | failing |
| "No Source-Text Wiring Tests" — use AST/reflection, not grep (server CLAUDE.md) | import-direction tests use `ast.parse` + import-target walk (ADR-147 §Enforcement pattern), not `read_text()` grep | n/a (compliant) |
| No Silent Fallbacks / No Stubbing (SOUL) | tripwire forbids a silent `_snapshot` reach-through surviving the narrowing | failing |
| Behavior preservation (epic-122) | drill_in/out scope semantics + overlay path pinned against the stand-in; pre-existing real-Session tests kept green | failing (new) / passing (regression) |

**Rules checked:** 5 of 5 applicable rules have test coverage (the lang-review checklist for Python centers on import-direction + wiring + no-grep, all covered).
**Self-check:** 0 vacuous tests. Every test has a meaningful assertion; the one near-smoke line in `test_no_plotted_course_does_not_touch_snapshot` is backed by the real assertion that the call completes without tripping `_SnapshotTripwire`.

**Handoff:** To Dev (Hephaestus) for implementation.

## Delivery Findings

The orbital/intent module currently takes a full Session object from the server tier, creating an upward import dependency that violates ADR-147's layering law. This story narrows that dependency by:

1. Identifying the exact Session fields that orbital/intent reads (approximately 4 fields based on the epic context)
2. Creating a read-only Protocol with those 4 fields (structural typing)
3. Refactoring orbital/intent to accept the Protocol instead of the full Session
4. Verifying behavior preservation — no logic changes, only the type contract at the seam

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): The story's "4-field **read** Protocol" framing undercounts the real seam. `handle_orbital_intent` touches **five** members of `session`, not four, and they are not all reads. Affects `sidequest/orbital/intent.py` (Dev must shape the Protocol to the true surface): `orbital_content` (read), `orbital_scope` (read **and write** — drill_out reads it, every branch assigns it back), `clock` (read, needs `.t_hours`), `party_body_id` (read), and `plotted_course` (read). The SM risk note anticipated this. *Found by TEA during test design.*
- **Gap** (blocking for GREEN): The function currently reads the course via a **private reach-through** `session._snapshot.plotted_course`. A clean Protocol cannot expose `_snapshot`, so Dev must (a) change the function body to `session.plotted_course` and (b) add a `plotted_course` accessor to `Session` returning `self._snapshot.plotted_course`. Affects `sidequest/orbital/intent.py` and `sidequest/server/session.py`. Without the Session accessor, the production caller `handlers/orbital_intent.py` (passes `room.session`) stops conforming to the Protocol. *Found by TEA during test design.*
- **Improvement** (non-blocking): `intent.py` is the orbital tier's **last** file importing `sidequest.server`. Once narrowed, the entire `sidequest/orbital/` tier is server-pure — `test_orbital_tier_is_server_pure` locks that in and pre-pays part of 122-5's CI guard. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (non-blocking): TEA's two GREEN-blocking findings are both addressed — `orbital_scope` is modeled as a mutable Protocol member, and `Session.plotted_course` now exists as the clean accessor replacing the `_snapshot` reach-through. *Found by Dev during implementation.*
- **Improvement** (non-blocking): The orbital tier is now fully server-pure (confirmed GREEN). When 122-5 lands the tier-wide CI guard, `orbital/` should already pass with zero remediation. Affects `sidequest/orbital/` (no change needed; informational for 122-5). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `OrbitalIntentSession` does not enforce that `orbital_scope` is *writable* — `@runtime_checkable` only checks member presence, so a future implementor exposing it as a read-only `@property` would pass `isinstance` but raise `AttributeError` at `intent.py:122`. Mitigated today: the Protocol docstring already states "read **and written**," and the only production impl (`Session`) has a setter. Affects `sidequest/orbital/intent.py` (optional: add an inline `# read+write — setter required` comment on the member). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The Protocol's annotation types (`Clock`, `PlottedCourse`, `OrbitalContent`) are `TYPE_CHECKING`-only imports; a runtime `typing.get_type_hints(OrbitalIntentSession)` call would `NameError`. No current caller introspects this Protocol (it is used purely as an annotation; `isinstance` does not evaluate hints — confirmed empirically on 3.14), so this is latent only. Affects `sidequest/orbital/intent.py` (no action unless a future caller needs `get_type_hints`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `test_orbital_intent_session_protocol_is_runtime_checkable` asserts on CPython-private `_is_protocol`/`_is_runtime_protocol` internals, which can silently degrade to the `False` default if renamed in a future Python. The redundant `test_standin_conforms_to_runtime_protocol` already proves runtime-checkability via `isinstance`. Affects `tests/orbital/test_intent_session_protocol_122_4.py` (optional hardening: use `issubclass(..., Protocol)` + the existing isinstance proof). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (0 Gap, 0 Conflict, 0 Question, 3 Improvement)
**Blocking:** None

- **Improvement:** The orbital tier is now fully server-pure (confirmed GREEN). When 122-5 lands the tier-wide CI guard, `orbital/` should already pass with zero remediation. Affects `sidequest/orbital/`.
- **Improvement:** `OrbitalIntentSession` does not enforce that `orbital_scope` is *writable* — `@runtime_checkable` only checks member presence, so a future implementor exposing it as a read-only `@property` would pass `isinstance` but raise `AttributeError` at `intent.py:122`. Mitigated today: the Protocol docstring already states "read **and written**," and the only production impl (`Session`) has a setter. Affects `sidequest/orbital/intent.py`.
- **Improvement:** The Protocol's annotation types (`Clock`, `PlottedCourse`, `OrbitalContent`) are `TYPE_CHECKING`-only imports; a runtime `typing.get_type_hints(OrbitalIntentSession)` call would `NameError`. No current caller introspects this Protocol (it is used purely as an annotation; `isinstance` does not evaluate hints — confirmed empirically on 3.14), so this is latent only. Affects `sidequest/orbital/intent.py`.

### Downstream Effects

Cross-module impact: 3 findings across 2 modules

- **`sidequest/orbital`** — 2 findings
- **`sidequest`** — 1 finding

### Deviation Justifications

3 deviations

- **Corrected an over-specified TEA assertion (drill-out scope normalization)**
  - Rationale: Satisfying the original assertion would require changing production drill-out logic, which violates the highest-authority spec (behavior-preservation). Spec-authority hierarchy: story scope > tests. The corrected test still proves the real point (orbital_scope is read+write on the stand-in).
  - Severity: minor
  - Forward impact: none — render output is identical; a subsequent drill_out from the "coyote" scope still resolves to `<root>` (the primary has no parent).
- **Protocol is 5 members with a mutable scope, not a 4-field read surface**
  - Rationale: Source audit of `handle_orbital_intent` (intent.py:32-119) shows it both reads and assigns `session.orbital_scope`, and reads a 5th member. A read-only 4-field Protocol cannot model the scope write and would drop a real dependency. The SM assessment flagged the count as an estimate to verify.
  - Severity: minor
  - Forward impact: Dev's Protocol must declare `orbital_scope` mutable and include `plotted_course`; otherwise type-check/behavior fails.
- **plotted_course promoted to a clean Session accessor (kills the `_snapshot` reach-through)**
  - Rationale: A Protocol cannot expose a private `_snapshot`. Promoting the accessor is the minimal change that lets the seam narrow while preserving behavior (the property just returns `self._snapshot.plotted_course`).
  - Severity: minor
  - Forward impact: One small additive property on `Session`; no behavior change for existing callers.

## Design Deviations

No deviations recorded at setup time.

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Corrected an over-specified TEA assertion (drill-out scope normalization)**
  - Spec source: context-epic-122.md (behavior-preservation mandate) vs `tests/orbital/test_intent_session_protocol_122_4.py::test_drill_out_reads_then_writes_scope_on_standin`
  - Spec text: epic-122 — "Behavior-preserving refactor ... only the type contract at the seam"; the test asserted `standin.orbital_scope.center_body_id == "<root>"` after drilling out from `red_prospect`.
  - Implementation: Changed the assertion to `== "coyote"`. The drill-out branch (intent.py) is byte-for-byte identical to HEAD and stores the parent's id verbatim — `Scope(center_body_id="coyote")` — it never normalized the system-primary to `"<root>"`. The pre-existing `test_drill_out_from_body_scope_returns_to_system` confirms only `resp.scope_center == "coyote"` was ever the contract.
  - Rationale: Satisfying the original assertion would require changing production drill-out logic, which violates the highest-authority spec (behavior-preservation). Spec-authority hierarchy: story scope > tests. The corrected test still proves the real point (orbital_scope is read+write on the stand-in).
  - Severity: minor
  - Forward impact: none — render output is identical; a subsequent drill_out from the "coyote" scope still resolves to `<root>` (the primary has no parent).

### TEA (test design)
- **Protocol is 5 members with a mutable scope, not a 4-field read surface**
  - Spec source: context-story-122-4.md (title) + context-epic-122.md; story body "Creating a read-only Protocol with those 4 fields"
  - Spec text: "Narrow orbital/intent from full Session to a 4-field **read** Protocol"
  - Implementation: Tests pin a **5-member** Protocol (`orbital_content`, `orbital_scope`, `clock`, `party_body_id`, `plotted_course`) with `orbital_scope` as **read+write**, not a 4-field read-only surface.
  - Rationale: Source audit of `handle_orbital_intent` (intent.py:32-119) shows it both reads and assigns `session.orbital_scope`, and reads a 5th member. A read-only 4-field Protocol cannot model the scope write and would drop a real dependency. The SM assessment flagged the count as an estimate to verify.
  - Severity: minor
  - Forward impact: Dev's Protocol must declare `orbital_scope` mutable and include `plotted_course`; otherwise type-check/behavior fails.
- **plotted_course promoted to a clean Session accessor (kills the `_snapshot` reach-through)**
  - Spec source: context-epic-122.md — "Behavior-preserving refactor; no library extraction"; SOUL "No Silent Fallbacks" / honest-layering law
  - Spec text: "Relocates pure helpers ... corrects layering-inversion edges ... behavior-preserving"
  - Implementation: Tests require the function to read `session.plotted_course` (Protocol member) instead of the private `session._snapshot.plotted_course`; a `_SnapshotTripwire` stand-in fails the build if `_snapshot` is touched. This obliges Dev to add a `plotted_course` property to `Session`.
  - Rationale: A Protocol cannot expose a private `_snapshot`. Promoting the accessor is the minimal change that lets the seam narrow while preserving behavior (the property just returns `self._snapshot.plotted_course`).
  - Severity: minor
  - Forward impact: One small additive property on `Session`; no behavior change for existing callers.

### Reviewer (audit)
- **Dev: corrected over-specified TEA assertion (`<root>`→`coyote`)** → ✓ ACCEPTED by Reviewer: independently verified via `diff` that the drill-out branch is byte-for-byte identical to `develop`; the original stores `Scope(center_body_id="coyote")` (parent id), never normalizing the primary to `<root>`. Pre-existing `test_drill_out_from_body_scope_returns_to_system` only ever asserted `resp.scope_center == "coyote"`. Changing production logic to satisfy the original assertion would have been a behavior change — correcting the test was the right call. The corrected test still exercises read+write of `orbital_scope`.
- **Dev/TEA: `plotted_course` promoted to a clean `Session` accessor** → ✓ ACCEPTED by Reviewer: the property returns `self._snapshot.plotted_course` — behavior-identical (verified: `GameSnapshot.plotted_course` is a Pydantic field defaulting to `None`, always present), and the `_snapshot` field is set unconditionally in `Session.__init__`, so no new exception path.
- **TEA: Protocol is 5 members with a mutable scope (not a 4-field read surface)** → ✓ ACCEPTED by Reviewer: my own audit of every `session.` access (lines 69/85/98/99/102/107/118/119/122/128/145/147) maps exactly onto the 5 declared members; `orbital_scope` is genuinely read (85) and written (122). The "4-field read" framing in the story title was an estimate; the 5-member mutable Protocol is correct.
- No undocumented deviations found. The behavior-preservation claim holds.