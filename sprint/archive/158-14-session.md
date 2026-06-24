---
story_id: "158-14"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-14: 158-8 follow-up: harden Character.pronouns (validated grammatical set + chargen normalization) and instrument the remaining _apply_pov_swap skip paths

## Story Details
- **ID:** 158-14
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Stack Parent:** none (depends on 158-8 completion)
- **Type:** refactor
- **Points:** 3
- **Priority:** p2
- **Repos:** server

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-24T09:33:53Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-24T08:32:04Z | 2026-06-24T08:34:10Z | 2m 6s |
| red | 2026-06-24T08:34:10Z | 2026-06-24T09:15:28Z | 41m 18s |
| green | 2026-06-24T09:15:28Z | 2026-06-24T09:25:12Z | 9m 44s |
| review | 2026-06-24T09:25:12Z | 2026-06-24T09:33:53Z | 8m 41s |
| finish | 2026-06-24T09:33:53Z | - | - |

## Overview

**Durable hardening of the 158-8 freeform-pronoun crash class.** Story 158-8 shipped only an in-function fail-open guard in `sidequest/server/emitters.py::_apply_pov_swap`. This story hardens the root cause: `Character.pronouns: str` is unconstrained while the localizer `swap_to_second_person` only accepts the canonical grammatical set `{he/him, she/her, they/them}`.

### Load-Bearing Design Caveat

Freeform pronouns are an **INCLUSIVE chargen feature** (`builder.py pronouns_allow_freeform`). Do NOT force `Character.pronouns` to a 3-value Literal — that breaks inclusive display. 

**Separate concerns:**
- **Keep freeform DISPLAY pronouns** (what the player chose in chargen)
- **Derive/validate a canonical GRAMMATICAL projection** for the localizer (swap_to_second_person only accepts {he/him, she/her, they/them}), or normalize at chargen

The strategy is to guarantee the localizer is NEVER handed a non-canonical value from ANY caller, while preserving the player's actual pronoun choice for display.

## Technical Context

### Root Cause (158-8 Reviewer findings)
- `Character.pronouns: str` (character.py:106) is unconstrained
- `swap_to_second_person` (pov_swap.py:878) raises `ValueError` for non-canonical pronouns
- Chargen allows freeform (builder.py:2194): pronouns like "she/they", "any", "xe/xem"
- 158-8's in-function guard catches crashes only AFTER they reach emitters

### Current State (158-8 shipped)
- Minimal guard in `_apply_pov_swap` (emitters.py:297–313) prevents crashes from non-canonical pronouns
- Fail-open returns canonical prose + emits `narration.pov_swap_skipped` span for unsupported pronouns
- **Gap:** Two other skip paths are still silent (no observability):
  - Empty-pronoun guard (emitters.py:292)
  - Invalid-text guard (emitters.py:314)
- **Gap:** The pronouns span attribute echoes raw player-supplied freeform text (PII/length concern)

### References
- Archived 158-8 session: `sprint/archive/158-8-session.md`
  - Reviewer Assessment (2026-06-23, round-trip 2)
  - Delivery Findings (Reviewer [SEC][LOW], [SILENT], [TYPE] root cause)
- Current guard: `sidequest/server/emitters.py::_apply_pov_swap` (L289–L317)
- Current tests: `tests/server/test_narration_pov_emission.py` (158-8 section)

## Acceptance Criteria

**AC1: Character.pronouns hardening** — the localizer is fed a validated canonical grammatical pronoun set (Literal/validator or chargen-time normalization) so a non-canonical value can never reach swap_to_second_person from ANY caller — without removing the inclusive freeform DISPLAY choice at chargen.

**AC2: Complete _apply_pov_swap skip-path observability** — route the pre-existing empty-pronoun guard (emitters.py:292) through narration.pov_swap_skipped, splitting the _pronouns_for_pc conflation into reason='pronouns_empty' vs reason='pc_not_in_snapshot'; and the invalid-text guard (emitters.py:314) with reason='text_missing_or_invalid'.

**AC3: Bound the pronouns span attribute** — truncate/normalize the player-supplied value written to the narration.pov_swap_skipped 'pronouns' attribute ([SEC][LOW] PII/length nit from 158-8 review).

## Design Notes

**On AC1 implementation options:**
1. **Literal + validator on Character.pronouns** — constrain at model definition, validate on assignment
2. **Chargen-time normalization** — accept freeform at chargen but normalize/store a canonical projection
3. **Dual field approach** — keep `pronouns_display` (freeform) and `pronouns_grammatical` (canonical) separate

Recommend consulting Keith on the design before red phase. The key constraint: the localizer caller MUST be guaranteed a canonical value.

**On AC2 observability:**
- Route empty/invalid/unsupported through the same OTEL span path
- Distinct `reason` values per skip type for GM panel filtering
- Resolve the `_pronouns_for_pc` conflation (currently returns "" both for "no pronouns" and "PC not in snapshot")

**On AC3 security:**
- Truncate pronouns attribute to a safe length (e.g., 64 chars) before writing to OTEL
- Consider a placeholder if the raw value is sensitive

## Sm Assessment

**Setup verdict: ready for red phase (TEA).** — Themis the Just, 2026-06-24

- **Scope is clean and bounded.** Server-only, 3 pts, tdd phased. No `depends_on` blocks it (158-8 already shipped + archived). Merge gate clear at setup time (only open PR is a dependabot bump unattached to a story).
- **Root cause + design caveat are captured.** The load-bearing constraint is recorded verbatim: freeform pronouns are an INCLUSIVE chargen feature — do NOT collapse `Character.pronouns` to a 3-value Literal. Separate the freeform DISPLAY value from the canonical GRAMMATICAL projection handed to `swap_to_second_person`. This is the guardrail every downstream agent must honor.
- **Three ACs are concrete and testable** (pronouns hardening / skip-path observability with distinct `reason` values / bounded span attribute), each tied to specific 158-8 Delivery Findings ([TYPE], [SILENT], [SEC][LOW]).
- **Routing note — AC1 structural choice is a design call, not mine.** The three options (Literal+validator / chargen-time normalization / dual `pronouns_display`+`pronouns_grammatical`) are all valid expressions of the caveat. TEA can pin the *behavioral* invariant in red ("the localizer is never handed a non-canonical value from any caller; freeform display is preserved") without prematurely committing to one structure. If TEA/Dev want an Architect ruling on the structure, route it then — do not block setup on it.
- **OTEL discipline applies.** AC2 is itself observability work; ensure the new skip-path `reason` values land on `narration.pov_swap_skipped` so the GM panel can confirm each path fires (not just that prose looks right).

Branch `feat/158-14-harden-character-pronouns` off `develop`. Jira skipped — no key exists for this story.

---
## TEA Assessment

**Tests Required:** Yes — by Argus Panoptes, 2026-06-24 (red phase)
**Reason:** Durable behavioral hardening with new OTEL contracts; TDD applies.

**Design decision captured (load-bearing):** Keith chose **"Project to canonical & swap"** (2026-06-24, via AskUserQuestion) over "type-level guarantee only." A non-empty freeform pronoun is **projected to a canonical grammatical set and the swap PROCEEDS** — the freeform-pronoun player reads "you" like everyone else, no longer the one player stuck in 3rd person. This **supersedes** 158-8's fail-open-for-freeform behavior.

**Test File:** `sidequest-server/tests/server/test_narration_pov_emission.py` (extended — section 9 added; 3 superseded 158-8 functions removed)

**Tests Written:** 24 new failing cases (12 functions, several parametrized over `_FREEFORM_PRONOUNS`) covering 3 ACs
**Status:** RED — verified serially (`-n0`, OTEL deadlock avoidance) via testing-runner: **24 failed (all AssertionError, no import/collection errors), 18 passed**. All kept 158-8 regression pins (`genuinely_noncanonical`, `does_not_brick_the_table` ×5, `recipient_not_named`) stay GREEN; sections 1–7 unaffected.

**AC → test map:**
- **AC1** (project + swap, from ANY caller): `test_158_14_freeform_recipient_swaps_via_canonical_projection` (×5, peer path), `..._freeform_emitter_swaps_via_canonical_projection` (×3, emitter path), `..._freeform_swap_emits_second_person_span` (×5, lie-detector proof the localizer got a canonical value), `..._projection_emits_observability_span` (×5, grammatical ∈ canonical set). Tests set `c.pronouns` directly (the "loaded save / any caller" shape) so a chargen-only normalization that leaves a freeform `pronouns` value unprojected will NOT pass — the projection must be derivable from `Character.pronouns`.
- **AC2** (split skip reasons): `test_158_14_skip_reason_pronouns_empty` (direct + `..._through_emit_path` integration), `..._pc_not_in_snapshot` (direct), `..._text_missing_or_invalid` (direct).
- **AC3** (bound span attr): `test_158_14_projection_span_bounds_player_display_pronouns` (≤64), `..._no_span_leaks_unbounded_player_pronouns` (span/attr-agnostic net).

### Rule Coverage (lang-review/python.md)

| Rule | Test(s) | Status |
|------|---------|--------|
| #11 input validation at boundaries (pronouns is chargen user-input) | `freeform_recipient_swaps_via_canonical_projection` (×5) — every freeform variant validated→projected, never reaches the localizer raw | failing (RED) |
| #4 never log/emit sensitive player-supplied data; bound length | `projection_span_bounds_player_display_pronouns`, `no_span_leaks_unbounded_player_pronouns` | failing (RED) |
| #1 no silent fallbacks (skip paths must be observable) | `skip_reason_pronouns_empty` / `..._pc_not_in_snapshot` / `..._text_missing_or_invalid` | failing (RED) |
| #6 test quality (no vacuous assertions; parametrize hits distinct mapping branches) | self-checked — every test asserts specific text/span/reason; freeform params exercise distinct projection mappings (she/they vs neopronoun→they/them) | n/a |

**Rules checked:** 4 of 13 lang-review rules are AC-relevant and have test coverage. **Self-check:** 0 vacuous assertions found (no `assert True`, no bare truthy checks on always-true values, no missing assertions).

**OTEL contract (TEA-defined; Dev implements to match, Reviewer may rename):**
- `narration.pov_swap_projected` — attrs `recipient_pc`, `display_pronouns` (player freeform, **truncated ≤64**), `grammatical_pronouns` (∈ `_PRONOUN_FORMS`). Fires on the display→grammatical projection.
- `narration.pov_swap_skipped` — keeps `recipient_pc` + `reason` ∈ {`pronouns_empty`, `pc_not_in_snapshot`, `text_missing_or_invalid`}. The 158-8 `unsupported_pronouns` reason is **retired** (projection is total for non-empty pronouns → that branch is unreachable; remove it, don't leave dead code).

**Handoff:** To Dev (Hephaestus the Smith) for GREEN implementation.

---
## Dev Assessment

**Implementation Complete:** Yes — by Hephaestus the Smith, 2026-06-24 (green phase)

**Files Changed:**
- `sidequest-server/sidequest/agents/pov_swap.py` — added `project_to_canonical_pronouns(pronouns) -> str | None`: derives a canonical grammatical set (a key of `_PRONOUN_FORMS`) from any non-blank freeform pronoun string while preserving the player's freeform DISPLAY choice. Mapping: already-canonical → itself; names she/her → `she/her`; else names he/him/his → `he/him`; everything else (they, any, neopronouns) → `they/them`. Whole-token matching (split on non-letters) so "they" is never mistaken for the "he" substring. Returns `None` only for blank input.
- `sidequest-server/sidequest/server/emitters.py` —
  - `_pronouns_for_pc` now returns `str | None` (`None` = PC absent from snapshot, `""` = present-but-empty) so the two skip paths are distinguishable;
  - `_apply_pov_swap` projects the recipient's pronouns to canonical before swapping, so the localizer always receives a valid value from ANY caller and the swap **proceeds** for freeform-pronoun players (they read "you" like everyone else); the `unsupported_pronouns` branch is **removed** (unreachable once projection is total);
  - split skip spans `narration.pov_swap_skipped` with `reason` ∈ {`pc_not_in_snapshot`, `pronouns_empty`, `text_missing_or_invalid`} (all three were previously silent returns);
  - new `narration.pov_swap_projected` span (`recipient_pc`, `display_pronouns` bounded to `_MAX_PRONOUN_ATTR_LEN`=64, `grammatical_pronouns`) records the display→grammatical decision for the GM panel.

**Tests:** GREEN — verified serially (`-n0`) via testing-runner:
- `tests/server/test_narration_pov_emission.py`: **42 passed** (24 new `test_158_14_*` + 18 kept, incl. all 158-8 regression pins).
- `tests/agents/test_pov_swap.py` + `test_pov_swap_otel.py` + `test_pov_swap_158_8_finding_pins.py`: **96 passed** (new helper introduces no regression).
- `tests/server/test_opening_emit_event_71_13.py` + `test_opening_pov_swap_71_5.py` + `tests/agents/test_dialogue_extract.py`: **16 passed** (POV emit-path regression clean).

**Type check:** pyright on the two changed files shows **11 errors at baseline == 11 with my change** — zero new errors (the `grammatical is None` early-return narrows the type into `swap_to_second_person`). The pre-existing errors are the conditional `view`/`_snapshot_for_swap` binding in `emit_event` and an unrelated `render_status` Literal — both untouched by this story.

**Lint/format:** `ruff check` clean; `ruff format` applied to the two touched files only.

**AC coverage:** AC1 (project + swap, both peer and emitter call sites, from any caller) ✓ · AC2 (three split skip reasons) ✓ · AC3 (bounded display_pronouns + no unbounded leak) ✓.

**Branch:** `feat/158-14-harden-character-pronouns` (pushed to origin).

**Handoff:** To Reviewer (Hermes Psychopompos) for code review.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): Dev must derive the canonical grammatical projection from `Character.pronouns` itself (a property/function or call-time projection in `_apply_pov_swap`), NOT a separate field populated only at chargen — AC1's "from ANY caller" + the RED tests (which set `c.pronouns` directly, simulating a loaded save) require any reader of a freeform `pronouns` value to be safe. Affects `sidequest/game/character.py` and/or `sidequest/server/emitters.py` (`_apply_pov_swap` / `_pronouns_for_pc`). *Found by TEA during test design.*
- **Improvement** (non-blocking): the freeform→canonical **mapping** is left to Dev/Architect (she/they → she/her or they/them; neopronouns → they/them per Keith's note). Tests are mapping-agnostic (swapped clause carries no gendered pronoun; observability asserts `grammatical_pronouns ∈ _PRONOUN_FORMS`), so Dev has latitude on the specific table. Affects the projection helper. *Found by TEA during test design.*
- **Gap** (non-blocking): `_pronouns_for_pc` (emitters.py:250) conflates "PC not in snapshot" and "PC has empty pronouns" — both return `""`. AC2 requires splitting them (e.g., return `None` for not-found vs `""` for found-but-empty) so the emitter can emit distinct skip reasons. Affects `sidequest/server/emitters.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the `unsupported_pronouns` skip branch (emitters.py:297–313) becomes **dead code** once projection is total for non-empty pronouns — remove it (No-Stubbing / dead-code rule), don't leave it guarded. Affects `sidequest/server/emitters.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `builder.py` still stores the raw freeform pronoun string onto `Character.pronouns` with no chargen-time normalization. This story canonicalizes at the emitter (call-time projection), which covers the live POV path, but a future caller of `swap_to_second_person` outside `_apply_pov_swap` must remember to call `project_to_canonical_pronouns` first. A follow-up could expose a `Character.grammatical_pronouns` property (one call site, refactor-stable) so the projection is intrinsic to the model rather than caller-applied. Affects `sidequest/game/character.py`. *Found by Dev during implementation.*
- **Question** (non-blocking): `project_to_canonical_pronouns` resolves "she/they" to `she/her` (gendered token wins over `they`). If the table prefers neutral-default for any mixed set, flip the precedence to `they/them`. The 158-14 tests are mapping-agnostic so either is green; this is a content/voice call, not a correctness one. Affects `sidequest/agents/pov_swap.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking) `[EDGE]`: a mixed-case but canonical-intent freeform value (e.g. `"He/Him"`) misses the `pronouns in _PRONOUN_FORMS` fast-path (keys are lowercase), projects to `he/him`, and — because `"he/him" != "He/Him"` — fires a `narration.pov_swap_projected` span, labelling a canonical-intent value as a freeform projection. The swap output is still correct; only the GM-panel telemetry is slightly noisy. Cheap fix: a case-folded fast-path `if pronouns.lower() in _PRONOUN_FORMS: return pronouns.lower()`. Affects `sidequest/agents/pov_swap.py:118`. **Recommended highest-value fast-follow.** *Found by Reviewer during code review.*
- **Improvement** (non-blocking) `[EDGE]`: the `narration.pov_swap_projected` span is emitted *before* the text-missing guard, so a pc_anchored card whose text is absent emits both a projection span and a `text_missing_or_invalid` skip span for the same recipient — implying a swap that never ran. Reorder the text-missing check ahead of the projection span so the projection span only fires when the swap will be attempted. Behavior is correct; this is telemetry precision. Affects `sidequest/server/emitters.py` (`_apply_pov_swap`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking) `[EDGE]`: `_pronouns_for_pc` returns `c.pronouns or ""`; the new `project_to_canonical_pronouns` calls `.strip()`/`.lower()` on it, so a non-str-truthy `c.pronouns` would raise `AttributeError` inside `emit_event`'s transaction → table-wide NARRATION rollback (the exact 158-8 blast radius). **Not reachable in production today** — `Character.pronouns` is `str`-typed and rejects non-str at construction, and all production assignment sites feed it from other `str`-typed `.pronouns` fields — but `validate_assignment` is off, so a one-line defensive guard (`return c.pronouns if isinstance(c.pronouns, str) else ""`) cheaply restores the robustness the pre-158-14 code had. Affects `sidequest/server/emitters.py:_pronouns_for_pc`. **Recommended fast-follow given the 158-8 lineage.** *Found by Reviewer during code review.*
- **Improvement** (non-blocking) `[SEC][LOW]`: the AC3 length bound on `display_pronouns` is correct, but neither it nor the `recipient_pc` attribute (the player-chosen PC name, written verbatim on all four skip/projection spans) strips control characters/newlines — a CWE-117 log-injection vector on a text-log OTEL exporter. Telemetry-plane only (the GM panel is local/dev, not the player-facing WS). The `recipient_pc`-name-in-span pattern is pre-existing (the old skip span and `second_person_swap` both write the name); this story did not introduce it. Optional hardening: strip `[\x00-\x1f]` and bound the name before the OTEL write. Affects `sidequest/server/emitters.py`. *Found by Reviewer during code review.*
- **Question** (non-blocking) `[EDGE]`: a non-blank pronoun string with zero letter tokens (e.g. `"/"`, `"123"`) projects to `they/them` rather than the `pronouns_empty` skip — the docstring says `None` is returned "only for empty/blank input", but a letter-less string is semantically empty. Behavior is defensible (garbage → they/them → the player still reads "you"), but if the table prefers fail-open for letter-less junk, add `if not tokens: return None` after the split. Affects `sidequest/agents/pov_swap.py:120`. *Found by Reviewer during code review.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Superseded three 158-8 fail-open test functions**
  - Spec source: archived `sprint/archive/158-8-session.md` (fail-open contract) vs context-story-158-14.md AC1 + Keith's 2026-06-24 decision
  - Spec text: 158-8 pinned freeform pronouns → "fall open to canonical 3rd-person prose" + `unsupported_pronouns` skip span
  - Implementation: removed `test_158_8_noncanonical_pronoun_recipient_falls_open_to_canonical`, `..._emitter_does_not_crash`, `..._emits_skip_span`; replaced with section-9 projection-and-swap tests
  - Rationale: AC1 + Keith's explicit "Project to canonical & swap" decision directly supersedes the emergency fail-open; keeping the old pins would contradict the new behavior
  - Severity: minor
  - Forward impact: Dev's GREEN flips these cases (name→"you"); the `unsupported_pronouns` reason is retired
- **AC2 `pc_not_in_snapshot` tested via a direct `_apply_pov_swap` call, not the full emit path**
  - Spec source: context-story-158-14.md AC2
  - Spec text: "splitting the _pronouns_for_pc conflation into reason='pronouns_empty' vs reason='pc_not_in_snapshot'"
  - Implementation: `test_158_14_skip_reason_pc_not_in_snapshot` constructs a view/snapshot desync and calls `_apply_pov_swap` directly; the other AC2 reason (`pronouns_empty`) IS wired through `_emit_event` (`..._through_emit_path`) to satisfy the integration-coverage rule
  - Rationale: a view→snapshot desync (view names a PC the snapshot lacks) cannot be expressed through the live room fixture (seats always correspond to snapshot characters)
  - Severity: minor
  - Forward impact: none — `_apply_pov_swap` is the real production function; the empty-pronoun integration test covers the wiring
- **Introduced a TEA-defined OTEL span (`narration.pov_swap_projected`) and a 64-char bound**
  - Spec source: context-story-158-14.md AC3 + CLAUDE.md OTEL Observability Principle
  - Spec text: AC3 "truncate/normalize the player-supplied value written to the narration.pov_swap_skipped 'pronouns' attribute"
  - Implementation: under projection-and-swap, freeform no longer produces a skip span, so the player's freeform value is recorded on a new projection-observability span instead; tests pin that span + a ≤64 bound (the design note's suggested length)
  - Rationale: the projection is a subsystem decision that MUST be observable (OTEL principle), and that's where the player-supplied value now lives, so AC3's bounding moves there; the span name/attrs are TEA-proposed and Reviewer/Dev may rename as long as the contract (observable projection + bounded display value + canonical grammatical) holds
  - Severity: minor
  - Forward impact: Dev implements the span to match, or renames with Reviewer concurrence

### Dev (implementation)
- **Canonicalized at the emitter (call-time projection) rather than on the Character model**
  - Spec source: context-story-158-14.md AC1 + TEA Delivery Finding (test design)
  - Spec text: "the localizer is fed a validated canonical grammatical pronoun set (Literal/validator or chargen-time normalization) so a non-canonical value can never reach swap_to_second_person from ANY caller"
  - Implementation: added `project_to_canonical_pronouns` in `pov_swap.py` and call it inside `_apply_pov_swap` (the sole production caller of the localizer); did NOT add a `Character.pronouns` validator/Literal nor a chargen-time normalization step
  - Rationale: minimalist-discipline — the RED tests set `c.pronouns` directly (loaded-save / any-caller shape) and only assert emit-path behavior, so call-time projection from `Character.pronouns` satisfies every test while preserving the freeform DISPLAY value; a model-level field is unrequired scope. The reusable helper means any future caller can project too. (Logged as a Dev finding for a possible `Character.grammatical_pronouns` follow-up.)
  - Severity: minor
  - Forward impact: none for the live POV path; a future non-`_apply_pov_swap` caller of `swap_to_second_person` must call `project_to_canonical_pronouns` first
- **Adopted the TEA-defined OTEL contract verbatim (`narration.pov_swap_projected`, 64-char bound)**
  - Spec source: TEA Assessment OTEL contract + context-story-158-14.md AC3
  - Spec text: "narration.pov_swap_projected — attrs recipient_pc, display_pronouns (truncated ≤64), grammatical_pronouns (∈ _PRONOUN_FORMS)"
  - Implementation: implemented the span + attribute names exactly as TEA specified; `_MAX_PRONOUN_ATTR_LEN = 64`; the span fires only when projection actually changes the value (freeform input), not for already-canonical pronouns (avoids span noise on the canonical path)
  - Rationale: TEA owns the OTEL contract for this story; implementing to match keeps the tests green and the GM panel honest
  - Severity: minor
  - Forward impact: none

### Reviewer (audit)
- **TEA: Superseded three 158-8 fail-open test functions** → ✓ ACCEPTED by Reviewer: directly mandated by Keith's 2026-06-24 "project to canonical & swap" decision; the old fail-open pins would contradict the new behavior. Kept regression pins (`does_not_brick_the_table`, `genuinely_noncanonical`, `recipient_not_named`) correctly survive and stay green.
- **TEA: AC2 `pc_not_in_snapshot` via direct `_apply_pov_swap` call** → ✓ ACCEPTED by Reviewer: a view/snapshot desync is genuinely inexpressible through the live room fixture; `_apply_pov_swap` is the real production function and the `pronouns_empty` reason is wired through `_emit_event` for integration coverage. Sound.
- **TEA: Introduced `narration.pov_swap_projected` span + 64-char bound** → ✓ ACCEPTED by Reviewer: under projection-and-swap, freeform no longer hits a skip span, so the player value legitimately moves to the projection span; bounding it there satisfies AC3's intent and the OTEL principle. (Telemetry-precision nits on when the span fires are logged as non-blocking Reviewer findings, not a rejection of the contract.)
- **Dev: Canonicalized at the emitter (call-time projection) rather than on the Character model** → ✓ ACCEPTED by Reviewer: matches minimalist-discipline and the tests' "any caller / loaded-save" shape; the reusable `project_to_canonical_pronouns` helper means a future caller can project too. The `Character.grammatical_pronouns` property is correctly logged as a follow-up, not forced into this story.
- **Dev: Adopted the TEA OTEL contract verbatim** → ✓ ACCEPTED by Reviewer: span/attr names match the contract; firing only on a value-changing projection is the right call (avoids canonical-path noise). The mixed-case-canonical edge (`"He/Him"`) that defeats this intent is logged as a non-blocking Reviewer finding.
- No UNDOCUMENTED spec deviations found — the implementation matches the TEA contract and Dev's logged deviations; all Reviewer findings are quality/hardening nits, not silent spec divergences.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 defects (2 non-defect smells) | confirmed 0, dismissed 0, deferred 0 — tests 138 GREEN, ruff+format clean |
| 2 | reviewer-edge-hunter | Yes | findings | 8 | confirmed 5 (all non-blocking), dismissed 3 (low/informational) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [SILENT] tag) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [TEST] tag) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [DOC] tag) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [TYPE] tag) |
| 7 | reviewer-security | Yes | findings | 3 (all LOW) | confirmed 3 (non-blocking), dismissed 0 — AC3 bound compliant, ReDoS refuted |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [SIMPLE] tag) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — self-assessed (see [RULE] tag) |

**All received:** Yes (3 enabled subagents returned; 6 disabled via `workflow.reviewer_subagents` settings)
**Total findings:** 0 confirmed-blocking, 8 confirmed non-blocking (logged as Delivery Findings), 6 dismissed/informational

## Reviewer Assessment

**Verdict:** APPROVED

No Critical or High findings, and no *reachable* blocking defect. All three ACs are met, the full suite is GREEN (138 passed serially), ruff/format clean, zero new pyright errors, the AC3 [SEC] length bound is confirmed compliant, and the projection regex is ReDoS-safe. The eight subagent findings are LOW / non-blocking hardening + telemetry-precision items, all logged as Delivery Findings for a fast-follow.

**Data flow traced:** player freeform pronoun (chargen) → `Character.pronouns` (str-typed, rejected-if-non-str at construction) → `snapshot.characters[i].pronouns` → `_pronouns_for_pc` (None=absent, ""=empty) → `project_to_canonical_pronouns` (→ canonical key of `_PRONOUN_FORMS`, total for non-blank input) → `swap_to_second_person` (now always receives a canonical value). The player-supplied value reaches OTEL only as `display_pronouns`, bounded to 64 chars. Safe end-to-end.

**Observations (≥5):**
- `[VERIFIED]` AC1 — freeform projects-and-swaps from both call sites: `emitters.py` peer fan-out + emitter path both flow through `_apply_pov_swap` → `project_to_canonical_pronouns`; `swap_to_second_person` receives `grammatical` (canonical) at `emitters.py` swap call. Evidence: `project_to_canonical_pronouns` returns a `_PRONOUN_FORMS` key for every non-blank input (junk like "123" → `they/them`, never non-canonical, never None). Tests `test_158_14_freeform_recipient_swaps_via_canonical_projection` (×5) + `..._emitter_...` (×3) green.
- `[VERIFIED]` AC2 — three distinct skip reasons reachable and observable: `pc_not_in_snapshot` (raw is None), `pronouns_empty` (`project(...)` is None for blank/whitespace), `text_missing_or_invalid` (text guard). Each emits a `narration.pov_swap_skipped` span with `recipient_pc`+`reason`. The `_pronouns_for_pc` None-vs-"" split is the load-bearing disambiguation. Evidence: emitters.py `_apply_pov_swap`; tests green.
- `[VERIFIED]` AC3 — `display_pronouns` bounded: `raw_pronouns[:_MAX_PRONOUN_ATTR_LEN]` (=64) at the projection span; the old unbounded `span.set_attribute("pronouns", pronouns)` is removed. Evidence: emitters.py projection-span block; `test_158_14_projection_span_bounds_player_display_pronouns` + `..._no_span_leaks_...` green. Complies with python.md #4 (bound player-supplied telemetry).
- `[EDGE]` Confirmed non-blocking: mixed-case canonical `"He/Him"` fires a spurious projection span (case-folded fast-path fix). **Recommended fast-follow.**
- `[EDGE]` Confirmed non-blocking: projection span fires before the text-missing guard (reorder for telemetry precision).
- `[EDGE]` Confirmed non-blocking: non-str `c.pronouns` → `.strip()` crash → table rollback. **Not reachable** (str-typed field, construction rejects non-str, production assigns only str), but a one-line `isinstance` guard restores pre-158-14 robustness — **recommended fast-follow given the 158-8 lineage.**
- `[EDGE]` Confirmed non-blocking: letter-less junk ("/", "123") → `they/them` rather than `pronouns_empty` (defensible default; optional `if not tokens: return None`).
- `[SEC]` Confirmed non-blocking (LOW ×3): AC3 length bound **compliant**; ReDoS **refuted** (`[^a-z]+` is a linear char-class split, ~0.05ms on 10k separators); residual control-char/newline non-stripping on `display_pronouns` and unbounded `recipient_pc` name on spans — telemetry-plane only (local GM panel), and the name-in-span pattern is **pre-existing** (old skip span + `second_person_swap` both write the name), not introduced here.
- `[SILENT]` (subagent disabled — self-assessed): this story *improves* silent-fallback posture — all three previously-silent returns now emit `narration.pov_swap_skipped` spans (No-Silent-Fallbacks ✓). No new bare `except`/swallowed errors introduced.
- `[TEST]` (subagent disabled — self-assessed): TEA's suite is non-vacuous (specific text/span/reason assertions), supersession of the 3 fail-open tests is sound, and the kept regression pins survive. 138 tests green incl. pov_swap + opening-emit regression.
- `[DOC]` (subagent disabled — self-assessed): docstrings on both new functions are accurate; the `_pronouns_for_pc` "None vs ''" contract is documented. Minor: the `project_to_canonical_pronouns` docstring "Returns None only for empty/blank" slightly overstates vs the letter-less-junk path (logged as a Reviewer finding).
- `[TYPE]` (subagent disabled — self-assessed): `_pronouns_for_pc -> str | None` and `project_to_canonical_pronouns(str) -> str | None` are annotated; the `grammatical is None` early-return narrows the type into `swap_to_second_person` (zero new pyright errors). One latent type-safety gap (non-str at runtime via `validate_assignment` off) logged as `[EDGE]`/non-blocking.
- `[SIMPLE]` (subagent disabled — self-assessed): no over-engineering; the dead `unsupported_pronouns` branch was correctly removed (No-Stubbing ✓). Preflight noted `_apply_pov_swap` is at the outer edge of comfortable size — non-defect, optional `_pov_skip_span` extraction if it grows again.
- `[RULE]` (subagent disabled — self-assessed): see Rule Compliance below — python.md #1/#3/#4/#11 all compliant; no project-rule violations.

### Rule Compliance (lang-review/python.md + CLAUDE.md/SOUL.md)

- **#1 No silent fallbacks / No-Silent-Fallbacks (CLAUDE.md):** COMPLIANT — every fail-open path in `_apply_pov_swap` (pc_not_in_snapshot, pronouns_empty, text_missing_or_invalid) now emits an OTEL span; the previously-silent returns are gone. No bare `except` added.
- **#3 Type annotations at boundaries:** COMPLIANT — both new/changed function signatures fully annotated (`str | None`).
- **#4 Never emit unbounded/sensitive player data to telemetry:** COMPLIANT for the AC3 target (`display_pronouns[:64]`). Residual LOW (control-char strip; `recipient_pc` name bound) logged non-blocking; the name-in-span is pre-existing.
- **#11 Input validation at boundaries (ReDoS):** COMPLIANT — freeform pronoun input is validated/projected/bounded; `re.split(r"[^a-z]+", …)` is linear, not a ReDoS vector.
- **OTEL Observability Principle (CLAUDE.md):** COMPLIANT — the projection (a subsystem decision) emits `narration.pov_swap_projected`; skip decisions emit `narration.pov_swap_skipped`. Telemetry-precision nits (#5/#6) logged non-blocking.
- **No-Stubbing / dead code:** COMPLIANT — the unreachable `unsupported_pronouns` branch was removed, not left guarded.
- **SOUL "INCLUSIVE chargen / freeform display preserved":** COMPLIANT — the freeform value is preserved on `Character.pronouns`; only a derived grammatical projection is handed to the localizer, and the freeform-pronoun player now reads "you" like everyone else (Keith's decision realized).

### Devil's Advocate

Assume this is broken. **Attack 1 — crash the table via pronouns.** The strongest vector is a non-str `c.pronouns` reaching `.strip()` (edge #7). I traced it: `Character.pronouns` is `str`-typed and Pydantic rejects non-str at construction; the four production assignment sites (`narration_apply.py` ×4, `session.py` npc) all copy from other `str`-typed `.pronouns` fields; JSON deserialization yields str-or-fails. So a non-str cannot arrive through any real path — the crash is unreachable today. It remains a latent fragility because `validate_assignment` is off, hence the logged fast-follow guard. **Attack 2 — poison the GM panel.** A player names their PC `"Hero\nFAKE: span"` or sets pronouns to `"xe/xem\nINJECT"`; the newline survives into a span attribute (no control-char strip). Real, but telemetry-plane only — the GM panel is a local dev/Keith tool, not a multi-tenant log sink, and nothing player-facing is affected. LOW, logged. **Attack 3 — confuse the projection.** Unicode "ｈｅ/ｈｉｍ", "/", "123", "she/him" — none crash; all resolve to a valid canonical set (worst case `they/them`), so the swap always proceeds correctly. The mixed-case `"He/Him"` produces a *correct swap* but a *spurious* projection span — telemetry noise, not a player-facing defect. **Attack 4 — break a non-freeform player.** Canonical "he/him"/"she/her"/"they/them" hit the fast-path, no projection span, identical behavior to pre-158-14; the 18 kept tests + 96 pov_swap + 16 opening-emit regression tests confirm no regression. **Attack 5 — a stressed reload.** A save with empty pronouns → `pronouns_empty` skip (fail-open to 3rd person, observable); a save with a PC the view names but the snapshot dropped → `pc_not_in_snapshot` skip. Both fail open safely with telemetry. Conclusion: the only HIGH-impact tail (table rollback) is unreachable; everything else is correct behavior with minor telemetry imprecision. Nothing rises to blocking.

**Pattern observed:** clean fail-open-with-observability throughout `_apply_pov_swap` (`emitters.py`), consistent with the existing `narration.*` span family.
**Error handling:** all failure paths fail open to canonical prose + an OTEL span; no exceptions can escape into `emit_event`'s transaction for any reachable input.
**Handoff:** To SM (Themis the Just) for finish-story.