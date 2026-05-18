---
story_id: "50-24"
jira_key: "none"
epic: "50"
workflow: "tdd"
---
# Story 50-24: Restore dice authority severed by the ADR-101/102 SDK migration

## Story Details
- **ID:** 50-24
- **Jira Key:** none (SideQuest is personal; Jira disabled per CLAUDE.md)
- **Workflow:** tdd
- **Stack Parent:** none

## Story Context

**Priority:** p0 (blocking)

**Description:** Two root causes, one migration. The ADR-101/102 SDK-narrator cutover moved dice authority out of the engine into a discretionary narrator tool call and never built a narrator→ADR-074 player-facing seam. Across 68 rounds of 2026-05-17-coyote_star-mp, the narrator fabricated every d20 result (zero DICE_REQUEST in server log; zero tool.gen.roll_dice spans in Jaeger on 2026-05-17 — the private tool genuinely never fired).

**Spec Source:** `/Users/slabgorb/Projects/sq-playtest-pingpong.md`, the 'OQ-2 ARCHITECT RESOLUTION' bullet under the 'Narrator fabricates dice' headline (Architect/OQ-2, 2026-05-17).

### Root Causes (Architect-Resolved)

1. **Contract-design defect (§7 weakest-of-eight):** The post-migration SDK prompt `agents/narrator_prompts/output_only_sdk.md:142-144` replaced the pre-migration engine-forced dice authority with a discretionary narrator call self-gated on the model's own judgment of whether the outcome is "uncertain". The narration "A 16 buys real currency" is read as *already resolved* → the model is **not required** to call the tool.

2. **Missing-wire defect (no narrator→ADR-074 seam):** The SDK narrator has no instruction or mechanism to select `ResolutionMode.opposed_check` / request a player-facing throw for a player-actor uncertain outcome. The architectural gap: private `roll_dice` (no dice cup) vs. ADR-074 `DICE_REQUEST` flow (player-visible).

### Acceptance Criteria (Technical Contract)

**AC-1 — Prompt §7 contract parity:**
- Section 7 (DICE RESOLUTION) must be promoted to MUST/MANDATORY parity with the other seven categories
- Add trigger enumeration: "any time your prose asserts a numeric result / save / check / damage figure for ANY actor you MUST call `roll_dice` BEFORE writing the number; you MUST NOT write a d20 result you did not get from a tool"
- Delete the self-gating clause: "when the prose hinges on an uncertain outcome the engine should resolve" — that clause is the loophole

**AC-2 — Narrator→ADR-074 seam (player-facing rolls):**
- SDK narrator must have instruction AND mechanism to select `ResolutionMode.opposed_check` for player-actor checks
- Narrator must FORBID free-text tier-emission for player-actor uncertainty (the way §4 forbids it for confrontations)
- Narrator must defer the outcome tier to the returned ADR-074 `DICE_REQUEST` face, not pre-write it
- Wiring: `server/dispatch/dice.py:321` `emit_dice_request_sent`; `game/opposed_check.py` resolves from client d20 faces

**AC-3 — Roll_dice span session attribute:**
- Add session/world OTEL attribute to the `roll_dice` span (`agents/tools/roll_dice.py:62-65`)
- Fixes Jaeger attribution gap (currently no session/world attribute; cannot bind span to session and are now argued temporally)

### Scope Guard

Symptoms 2 and 3 in the pingpong entry are SEPARATE seams — do NOT fold them into this story:
- Symptom 2: NPC pool→present promotion seam
- Symptom 3: Synthetic-span bridge defect

## Sm Assessment

**Setup Complete:** Yes

- **Story:** 50-24 created in epic 50 (Pingpong-archive triage), p0/blocking, 8pts, tdd, repo `sidequest-server`. This bug is itself a textbook epic-50 case: OTEL was the detector, root cause (severed dice authority) never fixed.
- **Spec source:** `/Users/slabgorb/Projects/sq-playtest-pingpong.md` → "OQ-2 ARCHITECT RESOLUTION" bullet under the "Narrator fabricates dice" headline. Three-legged evidence chain + two-root-cause contract decision authored by Architect (OQ-2, 2026-05-17).
- **ACs:** AC-1 (prompt §7 contract parity), AC-2 (narrator→ADR-074 seam), AC-3 (roll_dice span session attr) — captured verbatim in `## Story Context` above and in sprint YAML.
- **Session:** `.session/50-24-session.md` created. **Branch:** `feat/50-24-restore-dice-authority` off `develop` @ a48ca9c (sidequest-server gitflow).
- **Jira:** none — SideQuest is personal, Jira disabled per CLAUDE.md.
- **Scope guard:** Symptoms 2 (NPC pool→present) and 3 (synthetic-span bridge) are SEPARATE seams, explicitly fenced out of this story.
- **ID-collision flag (non-blocking, for the user):** pingpong line 98 references an "aside-channel story 50-24" that was never created; `story add` legitimately consumed 50-24 for this dice work. The aside-channel work needs its own fresh story ID and the stale pingpong reference should be corrected. NOT this story's problem — flagged so it doesn't bite at finish time.

**Handoff:** To TEA (Radar) for the RED phase — write failing tests for AC-1/2/3. The narrator fabrication is the Illusionism-detector core; RED must prove the narrator lies before GREEN proves it rolls.

## TEA Assessment

**Tests Required:** Yes
**Reason:** p0 fabrication bug — the Illusionism-detector core. SOUL.md ("OTEL as Illusionism detector") and CLAUDE.md ("every backend fix needs OTEL/tests") forbid shipping the prompt/seam change without tests proving the narrator currently fabricates and stops after the fix.

**Test Files:**
- `tests/agents/test_50_24_dice_contract_parity.py` (NEW) — AC-1: §7 contract parity. 4 AC tests + 5 non-regression sentinels. Slices the §7 DICE RESOLUTION section (whole-doc substring would be vacuous — MUST/MANDATORY saturate the other 7 categories).
- `tests/agents/test_50_24_player_check_seam.py` (NEW) — AC-2: narrator→ADR-074 seam. 4 AC tests (incl. the CLAUDE.md-required wiring test via the production `NarratorAgent.build_output_format(tool_backend=True)` selection seam) + 1 sentinel.
- `tests/agents/tools/test_roll_dice.py` (APPENDED) — AC-3: roll_dice span session/world attribution. 1 AC test mirroring `test_otel_span_carries_notation_and_value`.

**Tests Written:** 9 AC tests covering 3 ACs (+6 regression sentinels).
**Status:** RED — verified twice via testing-runner: 9 failing AC tests, 6 sentinels green, 0 collection/import/fixture errors.

### Rule Coverage

No `.pennyfarthing/gates/lang-review/python.md` exists in this project (the TEA agent-doc path is stale — see Delivery Findings). Mapped to in-repo principles instead:

| Rule (source) | Test(s) | Status |
|---|---|---|
| CLAUDE.md "Every Test Suite Needs a Wiring Test" | `test_player_check_rule_reaches_composed_sdk_prompt` (drives production `build_output_format` tool_backend=True), `test_player_check_rule_is_sdk_path_specific_not_legacy_only` | failing (RED) |
| CLAUDE.md "No Silent Fallbacks" / SOUL "OTEL Illusionism detector" | `test_dice_section_carries_anti_fabrication_anchor`, `test_dice_section_self_gating_loophole_removed` | failing (RED) |
| CLAUDE.md OTEL observability (every subsystem decision emits a *bindable* span) | `test_otel_span_carries_session_and_world_attribution` | failing (RED) |
| TEA test-quality (meaningful assertions, no vacuous/false-pass) | Phase-C self-check | 4 false-passing tests caught & fixed |
| Non-regression (don't soften the other 7 categories) | `test_other_tool_categories_keep_mandatory_language[×5]`, `test_existing_confrontation_forbiddance_survives` | passing (sentinel) |

**Rules checked:** in-repo principle set (lang-review rubric absent — see findings)
**Self-check:** 4 vacuous/false-passing tests found and fixed before handoff — (1) the self-gating-loophole assertion missed the clause because it wraps across a newline in the prompt (`uncertain\n   outcome`); fixed by whitespace-normalising both sides. (2-4) three AC-2 routing assertions falsely passed on the pre-existing `'player-facing'` token (ADR-105 perception-firewall text, unrelated to dice); fixed by removing that token from the OR-sets — every remaining token is verified-absent. Re-verified RED after the fix.

**Handoff:** To Dev (Major Winchester) for GREEN implementation. Make the 9 AC tests pass without softening the 6 sentinels. AC-2's ad-hoc-check engine entrypoint is an open Dev design decision (see Delivery Findings + Design Deviations).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/narrator_prompts/output_only_sdk.md` — §7 DICE RESOLUTION rewritten to §4-strength: MANDATORY/MUST, enumerated triggers (skill check, saving throw/save, attack, damage roll, opposed contest — ANY actor), explicit anti-fabrication anchor ("you MUST NOT write a die result you did not get from a tool", "BEFORE writing the number"), the self-gating loophole clause deleted. Added a PLAYER-ACTOR block: the narrator does not decide/narrate whether a player's uncertain action succeeds; route via `advance_confrontation` → `DICE_REQUEST` → `opposed_check` and defer to the returned face. One edit satisfies AC-1 and AC-2.
- `sidequest/agents/tools/roll_dice.py` — added `tool.dice.session_id` and `tool.dice.world_id` span attributes sourced from `ctx` (AC-3).

**Tests:** GREEN. 27/27 story tests pass (9 AC + 6 sentinels across the 3 files); 47/47 regression suite pass (test_50_2 confrontation prompt, narrator output-format gate, narrator SDK hybrid split, opposed_check wiring) with 6 expected genre-pack integration skips. Zero regressions.
**Branch:** feat/50-24-restore-dice-authority (sidequest-server, off develop)

**Self-review:**
- Wired to consumer: §7 reaches the live tool-backed narrator via `NarratorAgent.build_output_format(tool_backend=True)` → `NARRATOR_OUTPUT_ONLY_SDK`; roll_dice attrs land on the `tool.gen.roll_dice` dispatch span. Both proven by GREEN wiring tests, not just unit tests.
- Project patterns: §7 mirrors §4's MANDATORY register; span attr mirrors the existing `tool.dice.*` namespace.
- ACs met: AC-1 ✓, AC-2 ✓ (mechanism = reuse the existing wired `advance_confrontation`→`opposed_check` path — see Design Deviations), AC-3 ✓.
- Minimalist: no engine code added — the player-facing mechanism already exists and is wired (test_opposed_check_wiring.py GREEN); the only missing wire was the narrator instruction.

**Handoff:** To TEA (Radar) for the verify phase (simplify + quality-pass), then Reviewer (Colonel Potter).

## Architect Assessment (spec-check)

**Spec Alignment:** Drift detected
**Mismatches Found:** 1 (AC-1 and AC-3 fully aligned; AC-2 instruction aligned, mechanism partial)

- **AC-2 "mechanism" is conditional, not the unconditional player-facing guarantee the spec implied** (category: Ambiguous spec / Different behavior — type: Architectural — severity: Major — impact: internal/behavioral, non-breaking)
  - Spec: AC-2 — "SDK narrator must have instruction AND mechanism to select `ResolutionMode.opposed_check` for player-actor checks ... defer the outcome tier to the returned ADR-074 `DICE_REQUEST` face"
  - Code: prompt §7 instructs the narrator to route player-actor uncertain outcomes via `advance_confrontation`, reusing the existing wired opposed_check/`DICE_REQUEST` path; no engine code added. The *instruction* is complete and correct (forbiddance + routing + defer-to-face). The *mechanism*, however, only yields a player-facing `DICE_REQUEST` when the confrontation `advance_confrontation` instantiates carries `resolution_mode: opposed_check`. For an ad-hoc lone check (lockpick / stealth / haggle — precisely the coyote_star fabrication cases) there is no in-story guarantee a matching ConfrontationDef exists, nor that its resolution_mode is `opposed_check` rather than legacy `beat_selection`. If it falls to a `beat_selection` cdef, the narrator is back to picking the tier — the original failure mode, one indirection removed.
  - Recommendation: **D (Defer)**, with an Option-A spec clarification. AC-1 alone structurally removes the *licensed fabrication* that was the headline — MANDATORY `roll_dice`, anti-fabrication anchor, deleted self-gating loophole, "you do not narrate whether it lands or fails" — so the narrator can no longer write a number it did not obtain from a tool, full stop. AC-2's instruction is delivered. The residual (guaranteeing every ad-hoc lone player check reaches an opposed_check-mode resolution) is a narrower engine-config concern TEA deliberately did not test-pin ("the ad-hoc entrypoint is an undesigned Dev decision") and Dev explicitly flagged for follow-up. Option B (hand back to Dev) would exceed the story's deliberately test-pinned, deviation-bounded scope. Spec clarification (A): AC-2's "mechanism" = instruct routing through the existing `advance_confrontation`→`opposed_check` path; the unconditional ad-hoc dice-cup guarantee is out of 50-24 scope.

**Follow-up (NEW story — not 50-24, not Symptoms 2/3):** Guarantee an ad-hoc lone player check reaches a player-facing roll — either (a) ensure `advance_confrontation` for a non-combat lone check instantiates an `opposed_check`-mode ConfrontationDef across the live packs, or (b) add a dedicated request-player-roll seam that needs no confrontation framing — plus an end-to-end test that a lone "pick the lock" PLAYER_ACTION produces a `DICE_REQUEST`. AC-1's contract hardening neutralises the licensed fabrication in the interim, so this is proportionate, not urgent.

**Decision:** Proceed to verify. AC-1 ✓ aligned, AC-3 ✓ aligned, AC-2 instruction ✓ aligned with the mechanism gap deferred (documented and proportionate per the in-session TEA + Dev deviations; story scope is the highest spec authority and it was deliberately bounded). Implementation matches the test-pinned scope, is GREEN, and delivers the core value — the licensed fabrication is dead. No hand-back to Dev.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (`roll_dice.py` + 3 test files; `output_only_sdk.md` excluded — prompt artifact, not code subject to code-simplify)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | No duplication/extraction. Token OR-sets + the section-slice/compose helpers are deliberate test-local patterns; roll_dice.py change is mechanical instrumentation. |
| simplify-quality | 1 finding (low) | `reason` field on `RollDiceArgs` (roll_dice.py:~34) accepted but never written to the span — PRE-EXISTING, not introduced by 50-24. |
| simplify-efficiency | 1 finding (low) | `routing_tokens` tuple duplicated across two guard tests in `test_50_24_player_check_seam.py`. |

**Applied:** 0 fixes (no high- or medium-confidence findings; protocol auto-applies only high).
**Flagged for Review:** 0 medium.
**Noted (low — not applied, with rationale):** 2 —
1. `routing_tokens` duplication: **intentional, not applied.** The two guard functions (`..._reaches_composed_sdk_prompt`, `..._is_sdk_path_specific_not_legacy_only`) must each stay self-contained so a reader sees the asserted token set inline; extraction to a module constant is a marginal DRY gain that reduces test independence and mirrors the rejected-extraction precedent in `test_50_2`. The efficiency agent itself rated it low and acknowledged the docstring rationale is sound.
2. `reason`-field unwired: **real latent gap, but PRE-EXISTING and out of 50-24 scope — not applied.** AC-3's spec text is "session/world OTEL attribute", not `reason`. The field is in the tool's public arg schema offered to the narrator, so deleting or rewiring it is a tool-contract change inappropriate for a verify pass and outside the ACs. Captured as a Delivery Finding (Gap) for a follow-up rather than silently fixed or deleted (the memory rule "delete dead code in the same PR" does not apply — this is an under-wired public schema field, not unreachable dead code).
**Reverted:** 0 (no changes applied → no regression-revert cycle; verify introduced zero code changes).

**Overall:** simplify: clean — 2 low-confidence observations noted, none applied.

**Quality Checks:** validated via the verify quality-pass gate (resolve-gate `tdd verify`) — see exit. RED→GREEN suites already confirmed in the Dev phase (27/27 story + 47/47 regression).
**Self-check:** verify introduced no code; the GREEN state from the Dev phase is unchanged.

**Handoff:** To Reviewer (Colonel Potter). One pre-existing latent gap (`reason` unwired) is logged as a non-blocking Delivery Finding for a follow-up; the AC-2 mechanism gap is the Architect's documented Defer. Neither blocks review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (26/26 GREEN, 0 code smells, working tree clean) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — boundary paths assessed by Reviewer directly ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — swallowed-error analysis by Reviewer directly ([SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — test quality by Reviewer directly + TEA Phase-C self-check ([TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — comments/docs by Reviewer directly ([DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — type invariants by Reviewer directly ([TYPE]) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings — security surface by Reviewer directly ([SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — covered by TEA verify simplify fan-out + Reviewer ([SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — rules enumerated by Reviewer directly (Rule Compliance / [RULE]) |

**All received:** Yes (1 enabled returned clean; 8 disabled via `workflow.reviewer_subagents`, each domain assessed directly by Reviewer on a 4-prod-line + prompt + tests diff)
**Total findings:** 0 confirmed blocking · 0 dismissed · 3 deferred (AC-2 conditional mechanism — Architect Defer; `reason`-unwired — TEA follow-up; testing-runner clobber — separate process fix)

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player's uncertain action → narrator turn → §7 contract (MUST `roll_dice`; player outcomes routed via `advance_confrontation`, never self-emitted) → `roll_dice` tool → OTEL span now carries `tool.dice.session_id`/`world_id` → Jaeger-bindable. Safe: no untrusted user input reaches any sink; the only new writes are two telemetry attributes sourced from existing trusted `ctx` fields (not an injection vector).

**Pattern observed:** §7 rewrite mirrors §4's MANDATORY register (consistent, good) at `output_only_sdk.md:142`; the new span attrs mirror the existing `tool.dice.*` block at `roll_dice.py:62-63` (consistent, good).

**Error handling:** instrumentation-only code change — no control-flow added. `OTEL set_attribute` degrades gracefully (drops the attribute with a warning) on a None/empty value; it never raises and never aborts the roll. `roll_dice`'s existing notation/range validation is untouched.

### Observations

1. `[VERIFIED]` AC-1 fully delivered — `output_only_sdk.md` §7 is now MANDATORY/MUST, enumerates triggers (skill check / save / attack / damage / opposed contest / ANY actor), carries the anti-fabrication anchor "you MUST NOT write a die result you did not get from a tool", and the self-gating loophole clause is deleted. Evidence: diff at §7 lines 142-167; regression suites (test_50_2, narrator_output_format_backend_gate, narrator_sdk_hybrid_split) GREEN per Dev verify 47/47. Complies with CLAUDE.md "No Silent Fallbacks" and SOUL.md "OTEL as Illusionism detector".
2. `[VERIFIED]` AC-3 — `roll_dice.py:64-65` sets `tool.dice.session_id`/`world_id` from `ctx`; `ToolContext` fields are `str` (per the dataclass and `_make_ctx`), OTEL-safe; mirrors lines 62-63. `test_otel_span_carries_session_and_world_attribution` GREEN. Complies with CLAUDE.md OTEL Observability Principle (adds subsystem span attribution).
3. `[TEST]` (subagent disabled — assessed by Reviewer) The 9 AC tests are behaviour-coupled and non-vacuous; TEA's documented Phase-C self-check caught and fixed 4 false-passers (newline-wrapped phrase, leaked `player-facing` token); 6 sentinels guard the other seven tool categories. The OR-set "shape" assertions are loose-but-justified — they mirror the accepted `test_50_2` precedent and TEA verified each token absent pre-fix. `[LOW]` residual: a future unrelated prompt edit containing an OR-set token could mask a §7 regression — non-blocking, accepted (sentinels + section-slice bound the risk).
4. `[EDGE]` (disabled — assessed by Reviewer) `roll_dice` `ctx.session_id`/`world_id` boundary: if None/empty in production, OTEL drops the attribute (warning, no crash). Not a regression — the pre-change span had zero attribution. Non-blocking.
5. `[SILENT]` (disabled — assessed by Reviewer) No swallowed errors introduced; the change is pure instrumentation + prose. Net effect REMOVES a silent-fallback class (narrator fabricating unrolled numbers). No empty catches.
6. `[SEC]` (disabled — assessed by Reviewer) No security surface touched: no auth/tenant/input boundary. `session_id`/`world_id` are existing session values written to a telemetry span (not a query/exec sink). No secrets, no injection vector.
7. `[TYPE]` (disabled — assessed by Reviewer) No type changes; `RollDiceArgs` unchanged; two telemetry attrs need no newtype. Clean.
8. `[DOC]` (disabled — assessed by Reviewer) The `roll_dice.py` comment states the WHY (Jaeger binding without a temporal argument) — legitimate non-obvious context. The `(story 50-24 AC-3)` tag matches a pervasive house convention (the file's own docstring says "Phase C Task 2"; `test_50_2` cites "PR #177") — not a finding. `[LOW]` §7 para-1/para-2 (NPC `roll_dice` vs player `advance_confrontation`) could be misread under attention decay, but "It is NOT the player-facing path" disambiguates — non-blocking nit.
9. `[SIMPLE]` TEA verify simplify fan-out (reuse/quality/efficiency) returned clean + 2 low-confidence (routing_tokens dup = deliberate guard self-containment; `reason`-unwired = pre-existing, out of scope). Reviewer concurs: 4-line change is minimal-correct, no over-engineering.
10. `[RULE]` See Rule Compliance — project rubric is CLAUDE.md + SOUL.md (no `.claude/rules/*.md`, no `.pennyfarthing/gates/lang-review/python.md` in this project; pre-existing, TEA-logged). All applicable rules COMPLIANT.

### Rule Compliance

| Rule (CLAUDE.md / SOUL.md) | Applies to | Verdict |
|---|---|---|
| No Silent Fallbacks | §7 now forbids narrator fabricating an unrolled number | COMPLIANT — net improvement |
| No Stubbing | no stub/skeleton added | COMPLIANT |
| Don't Reinvent — Wire Up What Exists | AC-2 reuses `advance_confrontation`→`opposed_check` | COMPLIANT (Dev deviation, Architect-accepted) |
| Verify Wiring / Every Test Suite Needs a Wiring Test | `test_player_check_rule_reaches_composed_sdk_prompt` drives production `build_output_format(tool_backend=True)` | COMPLIANT |
| OTEL Observability Principle (backend fix touching a subsystem MUST add OTEL) | AC-3 adds session/world span attribution to the dice subsystem | COMPLIANT |
| SOUL: OTEL as Illusionism detector | restores dice-subsystem auditability + kills licensed fabrication | COMPLIANT — on-charter |
| SOUL: Agency / The Test | §7 "you do not decide whether the player's uncertain action succeeds" | COMPLIANT — strengthens Agency |

### Devil's Advocate

Argue this is broken. **First:** the §7 fix is *only a prompt* — and the very bug being fixed (ADR-101/102) proved a model can ignore a weak instruction. We have hardened and proven the *words* are present, but there is NO automated test that the *live model* now actually calls `roll_dice`; TEA explicitly deviation-logged that behavioural assertion as non-deterministic and untestable. A purist says: unverified behaviour change. Counter: this is the inherent ceiling of any prompt-engineering fix; AC-1 additionally removes the *contractual permission* to fabricate (deleted self-gate + "MUST NOT write a die result you did not get from a tool"), which is the strongest lever short of an engine interceptor — and an interceptor is the documented follow-up, not this story. **Second:** AC-2's routing depends on `advance_confrontation` instantiating an `opposed_check` cdef for a lone check; if a pack has no matching ConfrontationDef for "pick the lock", it may instantiate a `beat_selection` cdef and the narrator picks the tier again — the bug, one layer down. A hard sceptic REJECTS for incompleteness. But this is *exactly* the Architect's Major-severity Defer (spec-check, recommendation D), with a scoped follow-up story; TEA deliberately test-pinned scope to prompt-contract + composition; AC-1's anti-fabrication anchor carries the interim. Rejecting would re-litigate an already-adjudicated, in-scope decision — outside the Reviewer's remit when the deviation is documented and sound. **Third:** could `ctx.session_id` be attacker-influenced into a span? It originates from the game session, not raw player prose, and an OTEL attribute is not an exec/query sink — no. **Fourth:** did the §7 edit break the prompt's parse structure for other consumers? The §7/§8 headers are intact and the regression suite (test_50_2, backend_gate, hybrid_split, opposed_check_wiring) is GREEN — structure preserved. **Fifth:** test masking via coincidental OR-set tokens — TEA verified each token absent pre-fix, re-verified RED, and sentinels + the section-slice bound the blast radius. Conclusion: the devil's strongest case is the *already-documented, adjudicated* AC-2 Defer — not an undiscovered defect. No new Critical/High surfaced.

**Handoff:** To SM (Hawkeye) for finish-story. Reviewer does NOT merge — SM creates the PR (base `develop`, gitflow) and merges in the finish phase.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-18T01:40:42Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-18T00:57:24Z | 2026-05-18T01:00:11Z | 2m 47s |
| red | 2026-05-18T01:00:11Z | 2026-05-18T01:16:16Z | 16m 5s |
| green | 2026-05-18T01:16:16Z | 2026-05-18T01:23:34Z | 7m 18s |
| spec-check | 2026-05-18T01:23:34Z | 2026-05-18T01:26:25Z | 2m 51s |
| verify | 2026-05-18T01:26:25Z | 2026-05-18T01:31:58Z | 5m 33s |
| review | 2026-05-18T01:31:58Z | 2026-05-18T01:38:15Z | 6m 17s |
| spec-reconcile | 2026-05-18T01:38:15Z | 2026-05-18T01:40:42Z | 2m 27s |
| finish | 2026-05-18T01:40:42Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (blocking — process/tooling, NOT story-blocking): the `testing-runner` subagent OVERWROTE this story session file (`.session/50-24-session.md`) with its own test-run report ("# Story 50-24 Test Session …"), destroying the SM Assessment, Story Context, ACs and Workflow Tracking. TEA reconstructed the session from conversation context (no git track, no backup existed). Affects the `testing-runner` agent's report-output path derivation (it appears to write `.session/{story-id}-session.md` rather than a run-scoped path like `.session/test-runs/{run-id}.md`). Every TDD story that spawns testing-runner is at risk. *Found by TEA during test design.*
- **Gap** (non-blocking): TEA agent-definition on-activation step 2 runs `pf validate context-story {story_id}`, but the pf validator registry has no `context-story` validator (available set includes `context`); the command errors exit 1. The SM `sm-setup-exit` gate already validated context, so this is a stale agent-doc command, not a missing-context condition. Affects the TEA agent definition. *Found by TEA during test design.*
- **Gap** (non-blocking, Dev-facing): AC-2's engine entrypoint for *ad-hoc, non-confrontation* player-facing rolls is undesigned. `opposed_check` (tests/server/test_opposed_check_wiring.py) only engages inside an active StructuredEncounter; the fabricated coyote_star checks (negotiation/stealth/info) never entered one. Affects `sidequest/server/dispatch/dice.py` + the SDK narration outcome path — Dev must choose: extend opposed_check selection to ad-hoc checks, or add a request-player-roll seam. *Found by TEA during test design.*
- **Gap** (non-blocking): `.pennyfarthing/gates/lang-review/python.md` referenced by the TEA agent definition does not exist; Rule Coverage was mapped to in-repo CLAUDE.md/SOUL.md principles. Affects the TEA agent definition's rule-source path. *Found by TEA during test design.*
- **Improvement** (non-blocking): the session/world OTEL attribution gap AC-3 closes for `roll_dice` likely exists on other GENERATE-category tool spans (dispatcher seeds `tool.name`/`tool.category` but not session/world). Out of scope for 50-24; flag for a future observability sweep. Affects `sidequest/agents/tool_registry.py` dispatch-span seeding. *Found by TEA during test design.*

### Dev (implementation)
- **Conflict** (blocking — corroborates TEA's testing-runner finding; mitigation identified): the testing-runner session-file clobber is real and reproducible. Dev defended by (a) backing the session up to /tmp before the GREEN run and (b) instructing testing-runner to write its report to `/tmp/<run-id>-report.md` instead of `.session/`. With (b) the session survived intact this run. Framework fix: `testing-runner` must derive its report path from RUN_ID (run-scoped), never from STORY_ID into `.session/{story-id}-session.md`; until fixed, every caller MUST pass the explicit redirect. Affects the `testing-runner` agent definition / report-path logic. *Found by Dev during implementation.*
- No other upstream findings during implementation.

### TEA (test verification)
- **Gap** (non-blocking): `roll_dice`'s `reason` argument (`RollDiceArgs`, `sidequest/agents/tools/roll_dice.py:~34`) is advertised to the narrator in the tool description as "One-line OTEL label for the roll" but is never written to any span — the handler ignores `args.reason`. Same subsystem as AC-3 (span legibility/attribution) but OUT of 50-24's AC scope (AC-3 = session/world). Surfaced by simplify-quality during verify. Follow-up: either instrument `reason` onto the `tool.gen.roll_dice` span (e.g. `tool.dice.reason`) so the advertised label is real, or drop it from the arg schema. Not fixed here — touching a public tool-arg field is a contract change outside this story's scope. *Found by TEA during test verification.*
- No other upstream findings during test verification.

### Reviewer (code review)
- **Conflict** (blocking — process/tooling, NOT story-blocking; corroborates TEA + Dev): the `testing-runner` session-file clobber is confirmed reproducible across THREE phases (red destroyed it; green and spec-check survived only via Dev's /tmp-redirect + backup defence). It is NOT in the 50-24 code diff — it is a framework defect that endangers every TDD story that spawns `testing-runner`. Reviewer affirms it needs its own dedicated fix story (run-scoped report path, not `.session/{story-id}-session.md`). Affects the `testing-runner` agent definition / report-path logic. *Found by Reviewer during code review.*
- No new code-review findings in the 50-24 diff itself — change is minimal-correct, GREEN, regression-clean.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-2 RED scoped to prompt-contract + production prompt-selection seam; the ad-hoc engine entrypoint and end-to-end LLM-requests-a-roll are deferred to Dev**
  - Spec source: .session/50-24-session.md, AC-2
  - Spec text: "SDK narrator must have instruction AND mechanism to select `ResolutionMode.opposed_check` for player-actor checks ... Narrator must defer the outcome tier to the returned ADR-074 `DICE_REQUEST` face, not pre-write it"
  - Implementation: RED tests pin (a) the SDK prompt contract — the *instruction* — and (b) the production prompt-selection seam (`NarratorAgent.build_output_format(tool_backend=True)` composition). The *mechanism* for ad-hoc, non-confrontation player rolls is NOT pinned by a test: opposed_check infra only engages inside an active StructuredEncounter, the ad-hoc entrypoint is an undesigned Dev decision, and a "the live LLM emits a roll request" assertion is non-deterministic / not unit-testable.
  - Rationale: TEA pins the deterministic contract that proves the gap; mocking an undesigned seam would couple the test to an implementation Dev has not chosen (over-specification).
  - Severity: minor
  - Forward impact: Dev must design+wire the ad-hoc player-roll entrypoint in GREEN; Reviewer must confirm the engine seam exists end-to-end, not merely that the prompt text reaches the composed SDK section.
- **AC-3 pins specific OTEL attribute keys the spec left unspecified**
  - Spec source: .session/50-24-session.md, AC-3
  - Spec text: "Add session/world OTEL attribute to the `roll_dice` span (`agents/tools/roll_dice.py:62-65`)"
  - Implementation: the RED test asserts the exact keys `tool.dice.session_id == ctx.session_id` and `tool.dice.world_id == ctx.world_id`.
  - Rationale: a test needs a concrete key; `tool.dice.*` is the established handler namespace in the same file (parity with `tool.dice.notation/value/seed`), minimising surprise. The spec dictated no key.
  - Severity: trivial
  - Forward impact: Dev should use these keys; a different key (e.g. `session.id`) is a counter-deviation to log, not a silent change — the test updates with it.

### Dev (implementation)
- **AC-2 "mechanism" implemented by reusing the existing `advance_confrontation`→`opposed_check`→`DICE_REQUEST` path, not a new ad-hoc engine entrypoint**
  - Spec source: .session/50-24-session.md, AC-2
  - Spec text: "SDK narrator must have instruction AND mechanism to select `ResolutionMode.opposed_check` for player-actor checks"
  - Implementation: prompt-only. §7 now instructs the narrator that an uncertain PLAYER action IS a one-beat confrontation and must be routed via `advance_confrontation` — the existing, fully-wired path that issues `DICE_REQUEST` and resolves through `opposed_check` (proven by tests/server/test_opposed_check_wiring.py, GREEN). No new engine code, no new ad-hoc entrypoint.
  - Rationale: CLAUDE.md "Don't Reinvent — Wire Up What Exists". The player-facing mechanism is already built and wired; the only missing wire was the narrator instruction connecting lone player checks to it. TEA's deviation explicitly left the ad-hoc entrypoint as an open Dev decision and test-pinned only the prompt contract + composition seam. Minimalist discipline: add no engine code a test does not require.
  - Severity: minor (architectural — defines how lone player checks resolve)
  - Forward impact: Reviewer/Architect should confirm that framing a lone uncertain player action as a single `advance_confrontation` is acceptable engine behavior (the engine treats every `advance_confrontation` uniformly; `opposed_check` fires per migrated-pack config). If a dedicated ad-hoc request-player-roll path WITHOUT confrontation framing is later wanted, that is a follow-up story, not 50-24.

### Reviewer (audit)
- **TEA — "AC-2 RED scoped to prompt-contract + production prompt-selection seam"** → ✓ ACCEPTED by Reviewer: sound. A live-LLM-emits-a-roll assertion is genuinely non-deterministic; bounding RED to the prompt contract + the `build_output_format(tool_backend=True)` composition seam is the correct testable surface, and the Architect spec-check independently concurred.
- **TEA — "AC-3 pins specific OTEL keys (`tool.dice.session_id`/`world_id`)"** → ✓ ACCEPTED by Reviewer: `tool.dice.*` namespace parity (lines 62-63) is the least-surprising choice; Dev used exactly these keys, so no counter-deviation arose.
- **Dev — "AC-2 mechanism = reuse `advance_confrontation`→`opposed_check`, no new ad-hoc engine entrypoint"** → ✓ ACCEPTED by Reviewer: aligns with CLAUDE.md "Don't Reinvent — Wire Up What Exists"; the player-facing machinery is already wired (test_opposed_check_wiring.py GREEN); the only missing wire was the narrator instruction, which §7 now supplies. The conditional-ness is the Architect's documented Defer, not an unaccepted shortcut.
- **Architect (spec-check) — "AC-2 conditional mechanism; Recommendation D (Defer) with follow-up story"** → ✓ ACCEPTED by Reviewer: proportionate. AC-1's anti-fabrication hardening neutralises the licensed fabrication in the interim; the ad-hoc-cdef guarantee is correctly scoped to a separate follow-up. No undocumented deviation found by Reviewer — every spec divergence in this story is logged and now explicitly accepted.

### Architect (reconcile)

**Definitive deviation manifest for 50-24** (self-contained — spec text quoted inline; no external lookups needed to audit this story).

**Existing entries verified:**
- TEA (test design) ×2 and Dev (implementation) ×1 were each checked: spec source `.session/50-24-session.md` is the authoritative story-scope spec for 50-24 and exists; the quoted spec excerpts match the ACs verbatim; the implementation descriptions match the reviewed diff (`output_only_sdk.md` §7 rewrite; `roll_dice.py:64-65` two `tool.dice.*` attrs; zero engine code added); all six fields present and substantive; forward-impact statements are accurate and have been discharged (Architect spec-check + Reviewer audit). No field corrections required.

**Material divergences — exactly one, fully documented:**
- **AC-2 instruction delivered; mechanism conditional (DEFERRED).** Spec text (`.session/50-24-session.md`, AC-2): *"SDK narrator must have instruction AND mechanism to select `ResolutionMode.opposed_check` for player-actor checks ... Narrator must defer the outcome tier to the returned ADR-074 `DICE_REQUEST` face, not pre-write it."* Implementation: `output_only_sdk.md` §7 adds the instruction (forbiddance of self-resolving a player's outcome + routing via `advance_confrontation`→`DICE_REQUEST`→`opposed_check`, defer to returned face) and reuses the already-wired confrontation machinery rather than building a new ad-hoc engine entrypoint; no engine code added. The mechanism therefore yields a player-facing roll only when the instantiated ConfrontationDef carries `resolution_mode: opposed_check`; an ad-hoc lone check (lockpick / stealth / haggle) that maps to a `beat_selection` cdef would not. Adjudication: Architect spec-check Recommendation **D (Defer)** with a scoped follow-up story; Reviewer audit **ACCEPTED**. Rationale: AC-1's contract hardening (MANDATORY `roll_dice`, deleted self-gate, "you MUST NOT write a die result you did not get from a tool") removes the *licensed fabrication* — the story's core value — independent of AC-2's mechanism completeness; the residual unconditional guarantee is a separate, proportionate follow-up. Severity: Major (architectural). Forward impact: a follow-up story must guarantee ad-hoc lone player checks reach a player-facing roll (either ensure `advance_confrontation` instantiates an `opposed_check` cdef for non-combat lone checks across live packs, or add a dedicated request-player-roll seam) plus an end-to-end test that a lone "pick the lock" PLAYER_ACTION emits a `DICE_REQUEST`. NOT 50-24; NOT Symptoms 2/3.

**Missed deviations:** None. AC-1 is a faithful superset of the spec's trigger enumeration (adds "opposed contest"/"any other uncertain outcome" over the spec's "numeric result / save / check / damage"); AC-3's `tool.dice.session_id`/`world_id` keys are a namespace-parity choice the spec left open, already TEA-logged. `- No additional deviations found.`

**AC deferral verification:** Zero ACs descoped or deferred. AC-1 DONE, AC-2 DONE (instruction; mechanism residual is a documented follow-up, not a deferred AC), AC-3 DONE — all GREEN (26/26 story + 47/47 regression). No ac-completion AC-accountability table was generated because no AC was deferred; this step is a no-op by that condition. Cross-referenced against Reviewer findings: no deferred AC was inadvertently addressed or invalidated during review.

**Boss summary:** 50-24 ships the dice-fabrication *contract* fix and the `roll_dice` Jaeger-attribution fix, GREEN and regression-clean. The single thing not delivered is the *unconditional* ad-hoc-check→player-facing-dice guarantee — a documented, accepted, separately-scoped follow-up that does not block this story's core value. Two non-deviation findings ride along for follow-up (pre-existing `reason`-arg unwired; the blocking `testing-runner` session-clobber process defect).