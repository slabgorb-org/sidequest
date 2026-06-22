---
story_id: "153-16"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-16: [CHARGEN-NAME-PROSE-REJECT] accept the full natural-language name answer or surface why it was rejected

## Story Details
- **ID:** 153-16
- **Jira Key:** (no Jira integration for this project)
- **Workflow:** trivial
- **Stack Parent:** none
- **Points:** 1
- **Priority:** p3 (low)
- **Repo:** sidequest-server

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-22T08:33:03Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T08:02:59Z | 2026-06-22T08:04:16Z | 1m 17s |
| implement | 2026-06-22T08:04:16Z | 2026-06-22T08:26:06Z | 21m 50s |
| review | 2026-06-22T08:26:06Z | 2026-06-22T08:33:03Z | 6m 57s |
| finish | 2026-06-22T08:33:03Z | - | - |

## Delivery Findings

### Dev (implementation)
- **Gap** (non-blocking): `tests/game/test_wire_genre_resources.py` (15 tests) and 4 `tests/e2e/test_chargen_e2e.py` flows fail on the clean `develop` tree (verified by `git stash`), independent of this story. The genre-resource failures cover spaghetti_western/pulp_noir luck/heat pools (Fate packs, ADR-144 drift); the e2e failures are caverns/elemental flows with heavy render-mount interference. Affects `tests/game/test_wire_genre_resources.py` and `tests/e2e/test_chargen_e2e.py` (separate triage — not in scope here).

### Reviewer (code review)
- No new upstream findings. Concur with Dev's Gap above — independently confirmed via `git stash` that both failure clusters pre-exist on clean `develop` and are unrelated to this diff. Worth a separate triage story but does not block 153-16.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

2 deviations

- **Re-prompt gated on the NAME half only; the rig/vessel half stays optional (not nagged)**
  - Rationale: There is no `CharCreationScene` field marking a name scene as two-part, and road_warrior is the only pack with a hook_prompt name scene. Gating on the irreducible datum (the name) is general and safe; it also matches the pre-existing optional-vessel contract (`test_vessel_name_none_when_not_given`, `vessel_name()` returns None when absent). Accepting the player's chosen answer over nagging aligns with the Zork-Problem / Agency / Yes-And doctrine.
  - Severity: minor
  - Forward impact: minor — if Keith wants a one-shot nudge for a missing rig specifically, that needs a two-part scene flag (new content schema field), tracked separately.
- **Re-prompt reason reuses the pack hook_prompt rather than a new dynamic per-failure message**
  - Rationale: The hook_prompt is already actionable guidance; authoring a dynamic per-failure error string is scope creep for a 1-pt trivial fix and would duplicate pack-owned copy. The silent-fallback violation was the re-prompt firing on success, which the gate fixes.
  - Severity: minor

## Design Deviations

### Dev (implementation)
- **Re-prompt gated on the NAME half only; the rig/vessel half stays optional (not nagged)**
  - Spec source: 153-16 SM Assessment AC-1/AC-2 (session file)
  - Spec text: "accept the full natural-language name answer or surface why it was rejected"
  - Implementation: The name-scene re-prompt fires only when `extract_freeform_names` extracts NO name. A name-only answer (e.g. "Riggs" with no rig) is accepted and advances — the road_warrior scene's "Both matter." nudge does NOT fire for a missing rig.
  - Rationale: There is no `CharCreationScene` field marking a name scene as two-part, and road_warrior is the only pack with a hook_prompt name scene. Gating on the irreducible datum (the name) is general and safe; it also matches the pre-existing optional-vessel contract (`test_vessel_name_none_when_not_given`, `vessel_name()` returns None when absent). Accepting the player's chosen answer over nagging aligns with the Zork-Problem / Agency / Yes-And doctrine.
  - Severity: minor
  - Forward impact: minor — if Keith wants a one-shot nudge for a missing rig specifically, that needs a two-part scene flag (new content schema field), tracked separately.
- **Re-prompt reason reuses the pack hook_prompt rather than a new dynamic per-failure message**
  - Spec source: 153-16 SM Assessment AC-2
  - Spec text: "re-prompt surfaces a specific, actionable reason (no silent fallback)"
  - Implementation: On a genuine parse miss the existing pack-authored hook_prompt ("Give your rider a road name and your rig a name. Both matter.") is shown — now correlated with an actual miss instead of firing on every answer. A new `chargen.name_reprompt_decision` OTEL span records reason `name_accepted`/`name_unparsed`.
  - Rationale: The hook_prompt is already actionable guidance; authoring a dynamic per-failure error string is scope creep for a 1-pt trivial fix and would duplicate pack-owned copy. The silent-fallback violation was the re-prompt firing on success, which the gate fixes.
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **Re-prompt gated on the NAME half only; rig/vessel stays optional** → ✓ ACCEPTED by Reviewer: sound. Matches the pre-existing `vessel_name()`-is-None contract and the SOUL Agency/Yes-And/Zork doctrine (accept a deliberate answer over nagging). The one-shot rig-nudge alternative genuinely needs a new two-part scene-schema flag and is correctly deferred — not in scope for a 1-pt fix.
- **Re-prompt reason reuses the pack hook_prompt rather than a new dynamic message** → ✓ ACCEPTED by Reviewer: sound. The pack hook_prompt is actionable guidance and is now correctly correlated with a real parse miss; a per-failure dynamic string would duplicate pack-owned copy for no AC benefit. The `chargen.name_reprompt_decision` span gives the dev-side observability AC-2 implies.
- No undocumented deviations found — the diff matches the logged deviations and the story ACs.

## SM Assessment

**Branch Strategy:** gitflow (feat/153-16-chargen-name-prose-reject)
**Workflow Type:** phased
**Story Context:** Created at sprint/context/context-story-153-16.md

### Summary

Story 153-16 is a trivial bug fix addressing silent rejection of natural-language name input during road_warrior chargen (step v). The parser accepts terse "X and his rig Y" but silently rejects fuller prose forms like "They call me Riggs. The rig's name is The Anvil — a black, armored wall on wheels."

**Acceptance criteria:**
1. Fuller prose form is accepted and parses to correct name + rig name; OR
2. If unparseable, re-prompt surfaces a specific, actionable reason (no silent fallback); AND
3. Regression test covers prose-form input at the chargen name step.

**Investigation pointers:** Find the chargen step handler for road_warrior step v (likely sidequest/game/character creation / builder state machine ADR-015/016). Grep for re-prompt string "Both matter" / "road name" and the rig-name parsing logic. The bug is parser naivety: terse "X and his rig Y" works, prose fails.

**Permissions:** No permission check needed (trivial workflow, no special tool access).

**Setup complete:** All gates passed. Ready for implement phase routing to Dev.

## Dev Assessment

**Implementation Complete:** Yes

**Root cause (corrected from the story's investigation pointer):** NOT a parser bug. `extract_freeform_names` (builder.py, #705) already parses the finding's exact prose answer to `('Riggs', 'The Anvil')`. The bug is in `CharacterBuilder.apply_freeform` (builder.py ~2399): any freeform scene with a `hook_prompt` transitions to `AwaitingFollowup` **unconditionally**. On the name scene the hook_prompt is the pack-authored name-correction re-prompt ("…Both matter."), so a perfectly-parsed answer was still re-prompted — read by the player as a silent rejection. (The re-prompt string lives in road_warrior `char_creation.yaml`, not server source.)

**Fix:** Gate the name-scene re-prompt on parse success — re-prompt only when no name was extracted; otherwise accept the answer and advance. Non-name scenes keep their unconditional elaboration hook. Added a `chargen.name_reprompt_decision` OTEL span (reason `name_accepted`/`name_unparsed`) — the GM-panel signal per the OTEL Observability Principle. Only `road_warrior/the_name` is affected (the sole terminal name scene with a hook_prompt; siblings end on `allows_freeform: false` display scenes that `_is_name_scene` excludes).

**Files Changed:**
- `sidequest-server/sidequest/game/builder.py` — gate name-scene `hook_prompt` re-prompt on `extract_freeform_names` returning a name; emit `chargen.name_reprompt_decision`.
- `sidequest-server/tests/game/test_builder_name_extraction.py` — new `TestNameRepromptGate` (parseable prose advances w/o re-prompt incl. exact finding repro; name-only accepted; unparseable still re-prompts; no-hook_prompt advances). Re-pointed `TestNameSceneFollowupCorrection` correction-path tests to an unparseable/vessel-only first answer (the path the followup now opens on).
- `sidequest-server/tests/server/test_chargen_name_rig_extraction.py` — `test_extraction_decisions_are_observable` driven through the genuine re-prompt path; asserts the new `chargen.name_reprompt_decision` span.

**Tests:** Changed surface 30/30 GREEN (`test_builder_name_extraction.py` 27, `test_chargen_name_rig_extraction.py` 3). Broad `tests/game/` + chargen-server sweep: 3561 passed; the only failures (15 `test_wire_genre_resources.py` + 4 `test_chargen_e2e.py`) are **pre-existing on clean `develop`** (verified via `git stash`) and unrelated — see Delivery Findings. ruff check clean; ruff format clean; pyright unchanged from baseline (5 pre-existing builder.py errors, no new ones).

**Branch:** feat/153-16-chargen-name-prose-reject (pushed)

**Handoff:** To review (Reviewer / The Merovingian).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (2 enabled returned clean; 7 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** player name answer → `CharacterCreationPayload(phase="scene", choice=text)` → `WebSocketSessionHandler._chargen_scene` → `CharacterBuilder.apply_freeform(text)` → `extract_freeform_names` + the new gate → either `AwaitingFollowup` (genuine miss re-prompt) or `_advance_scene` → Confirmation. The accepted text lands in `_results` as `FreeformInput(text=text)` exactly as before; `character_name()`/`vessel_name()` re-parse it. Safe: no new narrator-prompt or persistence path (security subagent confirmed; ADR-047 boundary at `builder.py:3504` untouched).

**Observations:**
- [PRE] Preflight GREEN — 30/30 changed-surface tests pass, ruff check clean, ruff format clean, 0 NEW pyright errors (8 pre-existing, unrelated). Evidence: reviewer-preflight.
- [SEC] Security clean — new `chargen.name_reprompt_decision` span emits only `scene_id` + `reprompt` bool + fixed `reason` enum; no raw player text/PII; no new unsanitized-text path; no injection/DoS. Evidence: reviewer-security + `builder.py:2426-2434`.
- [VERIFIED] Gate is scoped to the NAME scene only — `if self._is_name_scene(scene_index)` guards the accept logic (`builder.py:2400`); a non-name freeform scene leaves `followup_prompt = scene.hook_prompt` untouched so its WOUND/elaboration hook still fires unconditionally. The choice-scene followup path (`apply_choice`) is a different method, untouched. Evidence: `builder.py:2398-2443`; `test_non_name_scene_followup_keeps_wound_hook` passes.
- [VERIFIED] `accepted = extracted_name is not None` is the correct predicate — `extract_freeform_names` returns either `None` or a non-empty `_NAME_PHRASE` match (regex requires a leading `[A-Z0-9]` token, `builder.py:932-933`), so an `is not None` check (not truthiness) is exactly right; name-only answers are accepted with the vessel left optional per the pre-existing `vessel_name()`-None contract. Evidence: `builder.py:2421`, `test_vessel_name_none_when_not_given`.
- [VERIFIED] pyright narrowing is correct — the fix carries `followup_prompt: str | None` (cleared to `None` on accept) rather than a bool, so `AwaitingFollowup(hook_prompt=followup_prompt)` narrows to `str`. 0 new pyright errors confirms it. Evidence: `builder.py:2398,2435-2439`.
- [VERIFIED] Tests are non-vacuous and correctly re-pointed — under the new gate, feeding the parseable `_REPRO_SENTENCE` to a correction-path test would fast-path to Confirmation and never enter the followup branch (silently vacuous). The three `TestNameSceneFollowupCorrection` tests were re-pointed to an unparseable/vessel-only first answer so the followup genuinely opens; `is_awaiting_followup()` asserts added. Evidence: test diff.
- [VERIFIED] The exact playtest repro is pinned — `test_parseable_prose_advances_without_reprompt` uses the literal finding sentence and asserts no re-prompt + `character_name()=="Riggs"` + `vessel_name()=="The Anvil"`. Evidence: `TestNameRepromptGate`.

### Rule Compliance
- **No Silent Fallbacks** (CLAUDE.md/SOUL.md) — COMPLIANT. The change *removes* a silent fallback (an unconditional re-prompt that masqueraded as rejection) and replaces it with an explicit accept-or-reprompt, both branches OTEL-observable. No new silent default/alternative introduced.
- **No Stubbing** — COMPLIANT. No stubs, placeholders, or dead shells.
- **OTEL Observability Principle** — COMPLIANT. New `chargen.name_reprompt_decision` span emitted on the subsystem decision (accept vs re-prompt), with reason enum.
- **Verify Wiring / Every Test Suite Needs a Wiring Test** — COMPLIANT. `test_chargen_name_rig_extraction.py` drives the real dispatch path end-to-end (`_connect`→walk→`apply_freeform`) and asserts the span fires; `test_extracted_name_and_renamed_rig_land_on_snapshot` proves the accept path lands name+rig on the snapshot.
- **No Source-Text Wiring Tests** (CLAUDE.md) — COMPLIANT. Tests assert behavior (`is_awaiting_followup`/`is_confirmation`/names) and OTEL span names, never grep production source.
- **ADR-047 prompt-injection sanitization** — COMPLIANT (security subagent). No new player free-text reaches a narrator prompt or span attribute unsanitized.
- **Zork Problem / Agency / Yes-And** (SOUL) — COMPLIANT. The fix accepts the fuller natural-language answer the player was invited to write instead of rejecting it — directly serving the doctrine the finding cited.

### Devil's Advocate
Argue the code is broken: A skeptic would say the gate quietly *drops* the road_warrior scene's explicit "Both matter" contract — a player who types only "Riggs" now sails through with no rig, so the pack author's two-part intent is silently defeated. Worse, an attacker or confused user could submit a name-shaped token that the parser mis-extracts (e.g. "Dust" from "the road took everything… Dust") and have garbage accepted as their name with no correction prompt. And by carrying `followup_prompt` as a local instead of re-reading `scene.hook_prompt`, a future edit that mutates the scene between extraction and dispatch would diverge. Finally, the correction-path tests were *changed* — a cynic reads changed tests as the author bending the spec to fit the code.

Refutation: The "Both matter" concern is a logged, accepted design deviation, not a silent drop — name-only acceptance matches the *pre-existing* `vessel_name()`-is-None contract and the SOUL Agency/Yes-And doctrine (accepting a deliberate answer beats nagging); a one-shot rig nudge would need a new two-part scene flag, correctly deferred. Mis-extraction is bounded: `extract_freeform_names` only matches a capitalized `_NAME_PHRASE` after explicit cues ("call me", "name is", bare-name, comma-pair) — "the road took everything…" yields `None` and DOES re-prompt (pinned by `test_unparseable_answer_triggers_reprompt`); and the legacy verbatim-fallback for a wrong-but-present name predates this change. The `followup_prompt` local is computed and consumed within the same synchronous method with no intervening scene mutation. The test changes are *justified and stronger*: the old assertions would have been vacuous under the new gate, and the re-pointed tests plus the new `TestNameRepromptGate` (incl. the literal finding repro) increase coverage rather than weaken it. Nothing here rises to Medium+.

**Verdict rationale:** No Critical/High/Medium findings. Both enabled subagents clean. Change is minimal, correctly scoped to the single affected pack scene, OTEL-observable, doctrine-aligned, and well-tested. The two pre-existing test-failure clusters (genre-resources, e2e) are confirmed independent of this diff.

**Handoff:** To SM for finish-story (The Merovingian → Morpheus).