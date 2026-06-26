---
story_id: "159-7"
jira_key: ""
epic: "159"
workflow: "tdd"
---
# Story 159-7: Companion chargen choice maps brain selection to scene index/label — unblock real-server character creation

## Story Details
- **ID:** 159-7
- **Jira Key:** (none - personal project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-26T17:49:04Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-26T17:00:16Z | 2026-06-26T17:01:44Z | 1m 28s |
| red | 2026-06-26T17:01:44Z | 2026-06-26T17:12:44Z | 11m |
| green | 2026-06-26T17:12:44Z | 2026-06-26T17:19:40Z | 6m 56s |
| review | 2026-06-26T17:19:40Z | 2026-06-26T17:32:16Z | 12m 36s |
| red | 2026-06-26T17:32:16Z | 2026-06-26T17:37:35Z | 5m 19s |
| green | 2026-06-26T17:37:35Z | 2026-06-26T17:39:59Z | 2m 24s |
| review | 2026-06-26T17:39:59Z | 2026-06-26T17:49:04Z | 9m 5s |
| finish | 2026-06-26T17:49:04Z | - | - |

## SM Assessment

**Setup complete — routing to TEA (red phase).**

- **Story:** 159-7, p1 bug, 3 pts, workflow `tdd` (phased), repo `sidequest-understudy`. No Jira (personal project).
- **Branch:** `feat/159-7-companion-chargen-choice-index` off `develop` (github-flow, per repo CLAUDE.md).
- **Context:** `sprint/context/context-story-159-7.md` written; story carries full description + 5 ACs (`pf sprint story show 159-7`).
- **Why this exists:** First real-server companion playtest (2026-06-26, epic 159) found the companion stalls at character creation. `companion/run.py::_chargen_choice` forwards the brain's ACT prose verbatim as the scene `choice`; the server's `_chargen_scene` (sidequest-server, `chargen_mixin.py`) resolves a choice only by numeric index or exact label, so prose falls through to `apply_freeform` on a select scene and chargen never advances — blocking the whole companion lifecycle.
- **Scope is contained to the companion package** (sidequest-understudy). Server side is reference-only — do NOT add fuzzy choice-resolution on the server (No Silent Fallbacks); the companion must send a valid index/label.
- **Load-bearing AC for TEA's red phase:** a wiring/integration test that asserts against the *real* server choice contract (resolves to a non-None index AND the builder advances past the scene) — the scripted `tests/companion/test_full_loop.py` fixture missed this exact bug because it accepts whatever the companion sends.

**Decision:** Proceed to TEA. Hand off via exit protocol.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): `_chargen_situation` enumerates choices to the brain **0-based** ("0: Warrior…") while the server resolves **1-based** (`max(0, n-1)`), so even a bare-index reply is off by one. Affects `src/companion/run.py` (`_chargen_situation` + the choice mapping must agree on base). Covered by `test_select_choice_resolves_to_last_option_no_off_by_one`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the Donut example def authored during the playtest is untracked at `src/companion/examples/donut_sunden.yaml` and is required by AC5's live re-run — Dev should commit it on this branch. It also works around a related defect: `companion.manifest.DEFAULT_MODEL` is `anthropic/claude-haiku-4-5-20251001`, which fails on the standard dev box (API key disabled); the working default is `claude_p/*`. Affects `src/companion/manifest.py` (`DEFAULT_MODEL`) + `src/companion/examples/`. *Found by TEA during test design.*
- **Question** (non-blocking): AC4 asks for a test "against the REAL server choice contract." sidequest-understudy does not depend on sidequest-server, so a live import is not available offline. Implemented as a faithful reproduction oracle (`_server_resolves` in `test_chargen_choice.py`) — Dev/Reviewer should confirm this satisfies AC4, or add a gated live-server smoke. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): DEFERRED the `DEFAULT_MODEL` change (TEA finding). `companion.manifest.DEFAULT_MODEL` remains `anthropic/claude-haiku-4-5-20251001`; the committed example def overrides `model: claude_p/sonnet`, so AC5's live re-run is unaffected. Changing the default would also require editing the passing `tests/companion/test_manifest.py:43` with no driving test (scope creep beyond the chargen-choice story). Affects `src/companion/manifest.py` + `tests/companion/test_manifest.py` — worth a tiny follow-up so an out-of-box def (no explicit `model`) is runnable on the standard dev box. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the committed example def `src/companion/examples/donut_sunden.yaml` carries `game_slug: REPLACE-WITH-THE-HUMANS-ROOM-SLUG` (placeholder) — the UI mints the real slug per session and the CLI cannot override `game_slug`, so a live run still needs a hand-edit. The `--game-slug`/`--as` CLI affordance (separate ping-pong finding) would remove that edit. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): three `_match_choice`/`_chargen_choice` branches ship without tests — the bare-index path (tier 3), the ambiguous-substring fallback, and the select+freeform hybrid. Affects `tests/companion/test_chargen_choice.py` (add coverage for each; the bare-index path also guards the index off-by-one). *Found by Reviewer during code review.*
- **Conflict** (blocking): confirmed lang-review #2 violation — `_run_select(choices=_CLASSES)` uses a module-level mutable list as a default arg. Affects `tests/companion/test_chargen_choice.py:123` (use a `None` sentinel). Cannot be dismissed (stated project rule). *Found by Reviewer during code review.*
- **Gap** (blocking): the shipped example def's CRITICAL SETUP block contradicts its own `game_slug` note (says use slug `"donut-playtest"` vs. "the UI mints it, can't pre-pick"). Affects `src/companion/examples/donut_sunden.yaml:14` (remove the donut-playtest instruction). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): tighten the test oracle (`except ValueError`, drop dead TypeError, note AwaitingFollowup unmodelled), strengthen the caplog assertion (logger="companion.run" + message match), remove the redundant `..._is_server_resolvable_in_range_not_prose` test, and correct three `run.py` docstrings (casefold "exact label", `_match_choice` ordering, freeform-branch fallback). Affects `tests/companion/test_chargen_choice.py` + `src/companion/run.py`. *Found by Reviewer during code review.*

### Reviewer (re-review round 1)
- **Improvement** (non-blocking): residual test-style nits — `test_select_choice_is_a_selector_not_prose` is implied-by the middle-option oracle test for its input (vary the input or drop it); the three bare-index tests could be a single `parametrize`; `test_chargen_falls_back_to_first_option_when_brain_yields` asserts wire-value `in ("0","1")` rather than the oracle (behaviorally covered by `test_yield_fallback_choice_resolves_to_first_option`). Affects `tests/companion/test_chargen_choice.py` + `tests/companion/test_run.py`. Optional tidy; not blocking. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): `_chargen_choice` docstring's "freeform scene" wording doesn't distinguish pure-free-text (no choices → "." on yield) from select+write-in (choices + allows_freeform → first option on yield); the inline comment disambiguates. Narrow the docstring wording in a future touch. Affects `src/companion/run.py`. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 2 findings (2 Gap, 0 Conflict, 0 Question, 0 Improvement)
**Blocking:** 2 BLOCKING items — see below

**BLOCKING:**
- **Gap:** three `_match_choice`/`_chargen_choice` branches ship without tests — the bare-index path (tier 3), the ambiguous-substring fallback, and the select+freeform hybrid. Affects `tests/companion/test_chargen_choice.py`.
- **Gap:** the shipped example def's CRITICAL SETUP block contradicts its own `game_slug` note (says use slug `"donut-playtest"` vs. "the UI mints it, can't pre-pick"). Affects `src/companion/examples/donut_sunden.yaml:14`.


### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`src/companion/examples`** — 1 finding
- **`tests/companion`** — 1 finding

### Deviation Justifications

2 deviations

- **Contract oracle instead of a live-server import for AC4**
  - Rationale: cross-package import is unavailable offline; the reproduction oracle is the documented contract-drift tripwire and catches the exact bug (prose → None). A live end-to-end smoke remains AC5 (manual re-run), out of the offline suite's scope.
  - Severity: minor
  - Forward impact: if the server's choice-resolution rule changes, `_server_resolves` must be updated in lockstep (noted in the test docstring).
- **Rework round added green coverage tests, not a failing test**
  - Rationale: the Reviewer rejected for COVERAGE GAPS and a test-quality rule violation on already-correct code, not for an implementation bug. There is no defect to capture with a red test; the correct response is characterization coverage of the existing branches. The remaining blocking finding is a source/comment fix owned by Dev (green).
  - Severity: minor
  - Forward impact: this red-rework round legitimately hands forward with an all-green suite; the substantive remaining work (doc fixes) is Dev's.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Contract oracle instead of a live-server import for AC4**
  - Spec source: context-story-159-7.md, AC-4
  - Spec text: "A wiring/integration test exercises chargen against the REAL server choice contract (not only the scripted fixture): asserts the server resolves the companion's choice to a non-None index AND the builder advances past the scene."
  - Implementation: `tests/companion/test_chargen_choice.py::_server_resolves` faithfully reproduces `sidequest-server/.../chargen_mixin.py::_chargen_scene` resolution (int→1-based index, else exact-label, else None) as an offline oracle, asserted against every select-scene choice the companion sends. No live `sidequest-server` import (understudy does not depend on it).
  - Rationale: cross-package import is unavailable offline; the reproduction oracle is the documented contract-drift tripwire and catches the exact bug (prose → None). A live end-to-end smoke remains AC5 (manual re-run), out of the offline suite's scope.
  - Severity: minor
  - Forward impact: if the server's choice-resolution rule changes, `_server_resolves` must be updated in lockstep (noted in the test docstring).

### Dev (implementation)
- No deviations from spec. The implementation satisfies AC1–AC4 directly (select→1-based index mapping, deterministic match with loud-fallback on unmappable, freeform passthrough, oracle-backed contract test). AC5 (live re-run) is enabled by the committed example def but performed manually, out of the offline suite. The one in-scope finding (off-by-one in `_chargen_situation`) was fixed, not deviated. The DEFAULT_MODEL change was deferred — logged under Delivery Findings, not as a spec deviation (it is outside this story's ACs).
- Rework round 1: no new deviations. The four Reviewer doc findings were comment/docstring-only corrections (no behavior change) — not spec deviations.

### TEA (test design) — rework round 1
- **Rework round added green coverage tests, not a failing test**
  - Spec source: TDD workflow red-phase norm (gates/tests-fail) + Reviewer 159-7 round-1 findings
  - Spec text: "red phase produces failing tests (RED state)"
  - Implementation: the rework added 6 passing tests (bare-index, out-of-range, ambiguous, select+freeform, format-invariant) + fixed a test-file rule violation; no test fails.
  - Rationale: the Reviewer rejected for COVERAGE GAPS and a test-quality rule violation on already-correct code, not for an implementation bug. There is no defect to capture with a red test; the correct response is characterization coverage of the existing branches. The remaining blocking finding is a source/comment fix owned by Dev (green).
  - Severity: minor
  - Forward impact: this red-rework round legitimately hands forward with an all-green suite; the substantive remaining work (doc fixes) is Dev's.

### Reviewer (audit)
- **TEA: Contract oracle instead of a live-server import for AC4** → ✓ ACCEPTED by Reviewer: an offline reproduction oracle is the right call for a cross-package boundary and is the documented contract-drift tripwire. CAVEAT (folded into the rework findings, not a reversal): the oracle currently over-reaches its "faithful reproduction" claim — it catches `TypeError` (dead code; the server catches only `ValueError`) and omits the server's `is_in_progress()` guard. Tighten to `except ValueError` + note AwaitingFollowup is unmodelled.
- **Dev: No deviations from spec** → ✓ ACCEPTED by Reviewer: confirmed — AC1–AC4 are implemented as specified and the DEFAULT_MODEL deferral is correctly logged as a Delivery Finding, not a spec deviation (outside this story's ACs). No undocumented deviations found in the diff.

### Reviewer (audit) — re-review round 1
- **TEA (rework r1): Rework round added green coverage tests, not a failing test** → ✓ ACCEPTED by Reviewer: correct handling — the rejection was for coverage gaps + a test-quality rule violation on already-correct code, so characterization coverage that passes is the right response; there was no defect to capture with a red test. The substantive remaining work (doc fixes) was correctly routed to Dev's green. The prior caveat on the oracle is now resolved (`except ValueError` + AwaitingFollowup note present).
- **Dev (rework r1): no new deviations (doc-only)** → ✓ ACCEPTED by Reviewer: confirmed — the four corrections are comment/docstring-only with no behavior change; not spec deviations.

## TEA Assessment

**Tests Required:** Yes
**Reason:** p1 behavioral bug — chargen choice contract.

**Test Files:**
- `tests/companion/test_chargen_choice.py` (new) — 7 tests pinning the select-scene choice contract via a faithful server-resolution oracle.
- `tests/companion/test_run.py` (edited) — fixed `test_chargen_scene_answered_in_persona` (asserted the prose-verbatim bug as correct); relaxed the YIELD-fallback assertion to "resolves to first option" rather than the 0-based literal.
- `tests/companion/test_full_loop.py` (edited) — fixed the wiring test's choice assertion (asserted prose verbatim).

**Tests Written:** 7 new + 3 corrected assertions, covering 5 ACs.
**Status:** RED — 7 failing for the right reason (companion sends server-unresolvable prose), freeform-passthrough and YIELD-fallback guards green.

**AC Coverage:**
| AC | Test(s) | Status |
|----|---------|--------|
| AC1 select → index/label not prose | `test_select_choice_resolves_to_picked_middle_option`, `_first_option`, `_last_option_no_off_by_one` | failing |
| AC2 deterministic map / fail-loud, no stall | `test_unmappable_select_pick_does_not_stall_and_logs` | failing |
| AC3 freeform still sends prose | `test_freeform_scene_sends_prose_answer` | passing (guard — must stay green) |
| AC4 real-server contract oracle | `test_select_choice_is_server_resolvable_in_range_not_prose` + `_server_resolves` oracle | failing |
| AC5 live re-run (Donut, pet) | manual — out of offline suite (see Delivery Findings re: example def) | n/a |

### Rule Coverage (python lang-review)
| Rule | Test(s) | Status |
|------|---------|--------|
| #4 logging — error path logs loudly | `test_unmappable_select_pick_does_not_stall_and_logs` (asserts a WARNING record) | failing |
| #6 test quality — no bug-enshrining assertions | fixed `test_chargen_scene_answered_in_persona` + `test_full_loop` (were asserting prose verbatim) | corrected |
| #3 type annotations at boundary | pre-existing `test_run_companion_has_typed_signature` covers the public `run_companion` seam | passing |

**Rules checked:** 3 of 13 applicable lang-review rules have test coverage (the others — mutable defaults, resource leaks, unsafe deserialization, path handling, etc. — are not touched by this string-mapping fix).
**Self-check:** 2 bug-enshrining assertions found in pre-existing tests and corrected; 0 vacuous assertions introduced.

**Handoff:** To Dev (Naomi Nagata) for GREEN — make the companion map a select-scene pick to a server-resolvable 1-based index (or exact label) deterministically, log loudly on an unmappable pick (don't stall), keep freeform passthrough, and commit the untracked example def + fix `DEFAULT_MODEL` per Delivery Findings.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `src/companion/run.py` — `_chargen_choice(intent, payload)` now resolves a select-scene pick to a 1-based index string the server accepts (new `_match_choice`: exact label → unique label substring → leading 1-based index → None). Freeform/no-choice scenes still send the brain's prose. A non-ACT/YIELD pick takes the first option; an unmappable ACT pick on a select scene logs a `warning` and falls back to the first option (No Silent Fallbacks, never stall). `_chargen_situation` now enumerates **1-based** to match the server (kills the off-by-one). Added `logging`/`re` imports + module `logger`.
- `src/companion/examples/donut_sunden.yaml` (new) — the Donut example def (pet, beneath_sunden, `claude_p/sonnet`) for AC5's live re-run; `game_slug` is a clearly-marked placeholder.

**Tests:** 205/205 understudy pass (79 companion incl. the 7 once-RED contract tests now GREEN; freeform + YIELD-fallback guards stay green). `ruff check` clean.

**Branch:** `feat/159-7-companion-chargen-choice-index` (pushed to origin).

**AC status:** AC1 ✅ (index/label, never prose) · AC2 ✅ (deterministic map; loud fallback, no stall) · AC3 ✅ (freeform passthrough) · AC4 ✅ (oracle-backed contract test) · AC5 ⏳ (example def committed; live re-run is manual — recommend running it before/at review).

**Scope notes:** server untouched (no fuzzy server-side resolution, per SM directive). `DEFAULT_MODEL` change deferred (see Delivery Findings — outside this story's ACs; example def overrides the model so AC5 is unaffected).

**Handoff:** To TEA (Amos Burton) for verify (simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (205 pass, 0 new lint, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 6, dismissed 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 | confirmed 4 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 1 | confirmed 1 |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled)
**Total findings:** 11 confirmed, 1 dismissed (with rationale), 0 deferred

**Dismissed:** test-analyzer's YIELD-fallback note (test_run.py:165 accepts choice ∈ ("0","1")) — dismissed because both values resolve to the first option via the server's `max(0, n-1)`; the permissive assertion is intentional and correct, not a defect.

## Reviewer Assessment

**Verdict:** REJECTED

The implementation logic is correct and all 205 tests pass — but this is a TDD contract fix, and the *test deliverable* falls short of the bar: a confirmed project-rule violation (lang-review #2, which I am not permitted to dismiss) plus three untested primary contract branches, and a misleading comment in the shipped example def. Every fix is small. Sending back to tighten before merge.

### Findings (rework list)

| Severity | Tag | Issue | Location | Fix Required |
|----------|-----|-------|----------|--------------|
| [MEDIUM] | [RULE] | Mutable default: `_run_select(choices=_CLASSES)` uses a module-level list as a default arg — confirmed lang-review #2 violation (cannot dismiss; low practical risk, but the exact antipattern the rule targets) | tests/companion/test_chargen_choice.py:123 | `choices: list[dict] \| None = None` + `choices = choices if choices is not None else _CLASSES` in body |
| [MEDIUM] | [TEST] | The tier-3 **bare-index** path of `_match_choice` ("2", "3) Mage") is entirely untested — the brain's most literal reply after seeing the 1-based prompt, and the only path that guards the index off-by-one | tests/companion/test_chargen_choice.py | Add cases: `("2"→1)`, `("3) I choose Mage"→2)`, and an out-of-range `("4"→fallback/None)` |
| [MEDIUM] | [TEST] | The **ambiguous-substring** fallback (≥2 labels match → None → first-option + warning) is untested | tests/companion/test_chargen_choice.py | Add test: brain "Warrior or Expert — hard call" → resolvable, choice=="1", WARNING logged |
| [MEDIUM] | [TEST] | The **select+freeform hybrid** branch (choices present AND allows_freeform, unmappable text → returns prose, no warning) is untested | tests/companion/test_chargen_choice.py | Add `_select_freeform_scene()` fixture + test: unmappable prose returned verbatim, no WARNING |
| [MEDIUM] | [DOC] | Example def's CRITICAL SETUP says 'Start the UI session with exactly "donut-playtest"' but the `game_slug` note says the UI mints the slug and it can't be pre-picked — mutually contradictory; misleads AC5 setup | src/companion/examples/donut_sunden.yaml:14 | Remove the "donut-playtest" instruction; keep the "copy the minted slug from the URL" guidance |
| [LOW] | [TEST] | `test_select_choice_is_server_resolvable_in_range_not_prose` reruns the middle-option test's exact brain text but asserts only non-None/in-range — strictly weaker; can only fail when the specific-index test already fails | tests/companion/test_chargen_choice.py:153 | Remove, or strengthen to assert `str(choice).isdigit() or casefold ∈ labels` |
| [LOW] | [TEST] | caplog assertion matches *any* WARNING, not `companion.run`'s "unmappable" message — a stray third-party warning would satisfy it even if the run.py warning were deleted | tests/companion/test_chargen_choice.py:177 | `caplog.at_level(logging.WARNING, logger="companion.run")` + assert `"unmappable"` in a record's message |
| [LOW] | [TEST] | `_server_resolves` oracle catches `(ValueError, TypeError)` — server catches only `ValueError` (TypeError is dead code) — and omits the server's `is_in_progress()` guard; docstring claims "faithful reproduction" | tests/companion/test_chargen_choice.py:102 | `except ValueError:` + a comment that AwaitingFollowup is not modelled |
| [LOW] | [DOC] | `_chargen_choice` docstring says "an EXACT label match" but the server casefolds (case-insensitive) | src/companion/run.py:~102 | "a case-insensitive exact label match" |
| [LOW] | [DOC] | `_match_choice` docstring implies step-1 is case-sensitive (qualifier only on step-2) | src/companion/run.py:~146 | "case-insensitive exact label, then unique case-insensitive substring, then leading index" |
| [LOW] | [DOC] | `_chargen_choice` docstring "A non-ACT/YIELD pick takes the first option" is inaccurate for the freeform branch (returns "." placeholder) | src/companion/run.py:~107 | Scope to select scene; note the freeform "." placeholder |

### Dispatch tag coverage
- `[EDGE]` — N/A (edge-hunter disabled)
- `[SILENT]` — N/A (silent-failure-hunter disabled); I checked the diff myself: the two `logger.warning` calls correctly make the fallback paths loud (No Silent Fallbacks satisfied).
- `[TEST]` — 6 confirmed (above) — coverage gaps + redundant test + weak caplog + oracle nuance.
- `[DOC]` — 4 confirmed (above).
- `[TYPE]` — N/A (type-design disabled); my own check: `run_companion` boundary fully annotated (rule-checker #3 clean); private helpers annotated too.
- `[SEC]` — N/A (security disabled); my own check: `re.match(r"(\d+)", t)` is ReDoS-safe (single anchored quantifier, no alternation/nesting); input is LLM prose, not attacker API input; no SQL/HTML/path sinks.
- `[SIMPLE]` — N/A (simplifier disabled); the three-tier `_match_choice` is justified by the AC (deterministic mapping); no obvious over-engineering.
- `[RULE]` — 1 confirmed (mutable default #2).

### Rule Compliance (lang-review/python, exhaustive)
Per rule-checker (83 instances across the diff) and my own read:
- #1 silent exceptions — compliant (only `_server_resolves` catches, specific + intended).
- #2 mutable defaults — **1 VIOLATION** (`_run_select` default `_CLASSES`); all other 19 signatures compliant.
- #3 type annotations at boundaries — compliant (`run_companion` fully annotated; private helpers exempt but annotated).
- #4 logging — compliant (both warnings use lazy `%`-args, level WARNING correct, no PII).
- #5 path handling — N/A (no path ops).
- #6 test quality — no vacuous assertions; the corrected `test_run`/`test_full_loop` assertions properly replace the prior bug-enshrining ones. (Redundancy of one test flagged under [TEST], not vacuity.)
- #7 resource leaks — N/A. #8 unsafe deserialization — N/A. #10 import hygiene — compliant (explicit stdlib imports). #11 input validation/ReDoS — compliant. #12 dependency hygiene — N/A (pyproject unchanged). #13 fix-regressions — clean.

### Observations (≥5)
1. [VERIFIED] Core fix is wired into the production path — `_chargen_choice(intent, payload)` is called from `run_companion`'s chargen branch (run.py:60), not just unit-tested. Evidence: diff call-site change at run.py:60.
2. [VERIFIED] Off-by-one is fixed end-to-end for the label path — `_chargen_situation` now enumerates 1-based and `_match_choice` returns 0-based → `str(idx+1)`; `test_select_choice_resolves_to_last_option_no_off_by_one` asserts Mage→index 2. (The *index* path that would also exercise this is the untested [TEST] gap above.)
3. [VERIFIED] No fuzzy server-side resolution was added — server untouched in the diff; all mapping is client-side and deterministic, per the SM directive and SOUL "No Silent Fallbacks."
4. [MEDIUM][TEST] Three shipped branches of `_match_choice`/`_chargen_choice` lack tests (index, ambiguous, select+freeform) — see findings.
5. [MEDIUM][DOC] Shipped example def carries self-contradictory setup instructions — see findings.
6. [LOW] Substring matching has a latent subset hazard (e.g. labels "Cat" ⊂ "Bobcat" → ambiguous→fallback); harmless for Warrior/Expert/Mage but worth a comment. Noted as non-blocking (no such labels ship today).

### Data flow trace
Brain `CompanionIntent.ACT(text)` → `_chargen_choice(intent, payload)` → (select) `_match_choice(text, choices)` → 0-based idx → `str(idx+1)` → `chargen_choice_frame` → `transport.send`. Verified the produced string satisfies the server's `_chargen_scene` resolver (int 1-based, else casefold exact label) via the offline oracle. Safe: unmappable input cannot emit a server-unresolvable choice — it falls back to "1" with a logged warning.

### Devil's Advocate
Suppose I am wrong and this should merge as-is. The strongest counterargument: the logic is correct, 205 tests pass, and every finding is Medium/Low — the severity table says those don't block, so rejecting is over-zealous and costs a rework cycle on a correct p1 fix. That has real force. But here is why it still fails the bar. This story's entire reason for existing is a *contract* — "the companion must send what the server can resolve." A contract fix earns its keep only if its tests actually pin the contract across the paths the contract spans. They don't: the bare-index reply ("2") is the single most likely thing a real brain emits after reading a numbered prompt, and it travels a different code path (`re.match` + `n-1`) than the substring path the tests exercise — a future refactor flipping `n-1` to `n` would ship a silent off-by-one with a fully green suite. That is precisely the class of bug this very story was filed to kill, reintroduced one tier over. Add the ambiguous-match and select+freeform branches and there are three live branches no test touches. Meanwhile the rule-checker found an actual project-rule violation (#2) that I am explicitly forbidden from dismissing, and the shipped example — the artifact AC5's live validation depends on — tells the operator to type a slug the UI will never accept. A confused operator following the CRITICAL SETUP block does the wrong thing on their first run. None of these is individually catastrophic; together they are exactly the "tests pass, so ship it" trap the adversarial review exists to stop. The fixes total perhaps fifteen minutes. Rework is the cheaper error.

**Handoff:** Back to TEA (Amos Burton) for red-rework — the bulk is test-file work (coverage + the rule-2 fix + caplog/oracle tightening); the four documentation fixes (run.py docstrings ×3 + the example-def comment) are for Dev in the subsequent green.

## TEA Assessment — Rework Round 1

**Phase:** finish (rework, round-trip 1)
**All Reviewer test-side findings addressed in `tests/companion/test_chargen_choice.py`:**
- [RULE/#2] `_run_select` now uses a `None` sentinel instead of the module-level `_CLASSES` default. ✅
- [TEST] bare-index (tier-3) coverage added: `test_select_bare_index_reply_maps_{first,middle,last}_option` ("1"/"2"/"3" → 0/1/2, the index off-by-one guard) + `test_select_out_of_range_index_falls_back_in_range` ("4" → loud in-range fallback). ✅
- [TEST] `test_ambiguous_substring_pick_falls_back_and_logs` (two labels in prose → first option + warning). ✅
- [TEST] `test_select_freeform_hybrid_unmappable_pick_is_written_in` (choices + allows_freeform → prose verbatim, silent). ✅
- [TEST] redundant in-range test replaced by `test_select_choice_is_a_selector_not_prose` (format invariant: digit | exact label). ✅
- [TEST] caplog asserts scoped to `logger="companion.run"` + `"unmappable"` message (both the unmappable and ambiguous tests). ✅
- [TEST] oracle `except ValueError` only (dead TypeError dropped), docstring scoped to InProgress + AwaitingFollowup-unmodelled note. ✅

**Tests:** 211/211 understudy pass (chargen-choice file: 13, up from 7). `ruff` clean.

**RED-state note (process):** the Reviewer rejected for *coverage gaps + a test-quality rule violation*, not for an implementation bug — the code already handled the bare-index/ambiguous/select-freeform branches correctly. The added tests therefore characterize already-correct behavior and pass (green); there is intentionally **no failing test** this round. The remaining blocking finding (example-def comment contradiction) and the three `run.py` docstring corrections are **source edits owned by Dev** in the green phase — TEA cannot modify `src/`.

**Handoff:** To Dev (Naomi Nagata) for green — apply the four documentation fixes (run.py `_chargen_choice`/`_match_choice` docstrings ×3 + `donut_sunden.yaml` CRITICAL SETUP contradiction), keep the suite green.

## Dev Assessment — Rework Round 1

**Implementation Complete:** Yes (all Reviewer findings now addressed across TEA + Dev rework)

**Files Changed (this round):**
- `src/companion/run.py` — docstring-only: `_chargen_choice` now says "case-insensitive exact label match" and scopes the non-ACT/YIELD behavior to select (first option) vs freeform (`"."`); `_match_choice` labels step-1 as case-insensitive. No behavior change.
- `src/companion/examples/donut_sunden.yaml` — CRITICAL SETUP no longer instructs typing `"donut-playtest"`; it now matches the `game_slug` note (UI mints the slug, copy from the URL). Resolves the [DOC/blocking] contradiction.

**Reviewer findings status:**
- [RULE] mutable default — fixed by TEA (None sentinel). ✅
- [TEST] bare-index / ambiguous / select+freeform coverage — added by TEA. ✅
- [TEST] redundant test / caplog / oracle — fixed by TEA. ✅
- [DOC] example-def contradiction (blocking) — fixed (this round). ✅
- [DOC] three run.py docstrings — fixed (this round). ✅

**Tests:** 211/211 understudy pass. `ruff` clean. Example def loads.
**Branch:** `feat/159-7-companion-chargen-choice-index` (pushed: 78a1ddb).

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review.

## Subagent Results

(Re-review, round-trip 1 — same enabled set, re-run against the reworked diff.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (211 pass, 0 new lint, 0 smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (all LOW) | confirmed 3 (non-blocking); prior round-1 findings all verified resolved |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 (LOW) | confirmed 1 (non-blocking); 3 prior doc findings verified resolved |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (13 rules, 53 instances, 0 violations) | N/A — round-1 #2 violation confirmed RESOLVED |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled)
**Total findings:** 4 confirmed (all LOW, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

The round-1 rework resolved every blocking finding from the first pass:
- [RULE] lang-review #2 mutable default → fixed (`None` sentinel, correct `is not None` form). Rule-checker re-run is **clean** (0 violations across 13 rules / 53 instances).
- [TEST] the three untested branches (bare-index tier-3, ambiguous-substring fallback, select+freeform hybrid) → now covered; the bare-index tests genuinely isolate tier-3 and guard the index off-by-one ("3"→Mage index 2). Oracle tightened (`except ValueError`, AwaitingFollowup scoped out), caplog assertions scoped to `companion.run` + message.
- [DOC] example-def setup contradiction + three run.py docstrings → all corrected; comment-analyzer confirms the "donut-playtest" instruction is gone and the case-insensitive/scoping wording now matches the code.

**Data flow traced:** brain ACT prose → `_chargen_choice(intent, payload)` → `_match_choice` (exact → unique substring → leading 1-based index) → `str(idx+1)` → `chargen_choice_frame` → `transport.send`; verified server-resolvable via the `_server_resolves` oracle. Unmappable input cannot emit an unresolvable choice — it falls back to "1" with a loud `companion.run` warning.
**Pattern observed:** deterministic, fail-loud client-side choice mapping at run.py:98–167 — no server change, consistent with SOUL "No Silent Fallbacks."
**Error handling:** both degradation paths (`unmappable` select pick, free-text yield) log at WARNING and still send a server-resolvable value; verified by `test_unmappable_select_pick_does_not_stall_and_logs` and `test_ambiguous_substring_pick_falls_back_and_logs`.

### Dispatch tag coverage
- `[EDGE]` / `[SILENT]` / `[TYPE]` / `[SEC]` / `[SIMPLE]` — N/A (disabled this story); my own spot-checks: no swallowed errors (both fallbacks log), boundary annotated, `re.match(r"(\d+)")` ReDoS-safe, no over-engineering.
- `[TEST]` — 3 confirmed LOW: (1) `test_select_choice_is_a_selector_not_prose` remains implied-by the middle-option oracle test for that input; (2) the three bare-index tests could be one parametrize; (3) `test_chargen_falls_back...` uses wire-value membership ("0"/"1") rather than the oracle (behaviorally covered by the dedicated oracle test). All non-blocking.
- `[DOC]` — 1 confirmed LOW: `_chargen_choice` docstring's "freeform scene" wording doesn't distinguish pure-free-text from select+write-in (inline comment disambiguates).
- `[RULE]` — 0 (clean; prior #2 resolved).

### Rule Compliance (lang-review/python, re-review)
Rule-checker re-ran exhaustively: 13/13 rules, 53 instances, **0 violations**. Round-1 #2 (mutable default) confirmed resolved with the correct `if choices is not None` sentinel (an empty-list override is not collapsed). #1 (oracle `except ValueError`, non-swallowing), #4 (lazy `%` logging, correct level), #9 (async — no blocking), #11 (static-pattern regex, no ReDoS) all clean.

### Observations (≥5)
1. [VERIFIED] Round-1 #2 violation resolved — `_run_select(choices: list[dict] | None = None)` + `choices = choices if choices is not None else _CLASSES` (test_chargen_choice.py:130-132). Complies with lang-review #2.
2. [VERIFIED] Tier-3 index path now tested in isolation — single-digit inputs skip tiers 1-2 (no label match/substring) and exercise `re.match`; "3"→index 2 guards the off-by-one (test_chargen_choice.py bare-index tests).
3. [VERIFIED] Example-def contradiction gone — no "donut-playtest" string remains; SETUP block and `game_slug` note agree (UI mints slug, copy from URL).
4. [VERIFIED] Docstrings match behavior — "case-insensitive exact label match" + select-vs-freeform scoping (run.py _chargen_choice/_match_choice).
5. [LOW][TEST] residual redundancy/parametrization nits + one wire-value assertion — non-blocking, optional tidy (see Delivery Findings).
6. [LOW][DOC] "freeform scene" docstring sense could be narrowed to "pure free-text" — non-blocking.

### Devil's Advocate
Could I be approving too soon? The case against: four findings still stand, so the work isn't pristine. But each is LOW and, on inspection, none is a defect. The "redundant" selector test is weaker-than-but-consistent-with the oracle test — it cannot give a false green that masks a bug; at worst it earns its keep only as documentation. The parametrization point is pure style. The wire-value `in ("0","1")` assertion is the one with the most teeth — a regression to the old "0" would pass it silently — but that exact behavior is independently pinned by `test_yield_fallback_choice_resolves_to_first_option` through the oracle in the dedicated file, so the contract is guarded; the membership check is merely a looser duplicate, not the sole guard. The docstring "freeform" wording is disambiguated by the adjacent inline comment, so a maintainer has the correct signal in context. Against all that: the blocking findings — the rule violation and three untested primary branches — are genuinely closed, the rule-checker is clean, 211 tests pass, and the contract oracle now does exactly what the scripted fixture failed to do. Holding the story for another cycle over LOW style nits would be the over-zealous mirror image of rubber-stamping, and the severity rules make these non-blocking. Approve, and log the nits as optional follow-ups.

**Handoff:** To SM (Camina Drummer) for finish-story. (Reviewer does NOT merge — SM creates/merges the PR in finish.)