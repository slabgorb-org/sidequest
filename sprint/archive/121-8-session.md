---
story_id: "121-8"
jira_key: "121-8"
epic: "121"
workflow: "tdd"
---
# Story 121-8: F4a3 — Fate chargen UI (ui; DESIGN-GATED by F4a-design)

## Story Details
- **ID:** 121-8
- **Title:** F4a3 — Fate chargen UI (ui; DESIGN-GATED by F4a-design): player-facing Fate creation screens — aspect authoring inputs (high concept + trouble + free), skill-pyramid allocation widget with live legality feedback, stunt picker with refresh readout, the ladder labels; ruleset=='fate'-gated so it never co-renders with the d20/WN chargen screen (paired negative test). Consumes the F4a2 wire contract; server remains the validation authority (No Silent Fallbacks — client mirrors, does not adjudicate). Depends F4a2 (121-7).
- **Jira Key:** 121-8
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server,ui,content (**DEVIATION: sprint YAML lists `repos: ui` only. Architect added `server` (121-7 deferred the render payload). TEA RED discovery + Operator decision 2026-06-16 added the client→server submission handler (server) and pulp_noir `fate_chargen_step` scene authoring (content) — see TEA deviation log.**)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T22:56:27Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T20:07:36.541226+00:00 | 2026-06-16T20:11:42Z | 4m 5s |
| red | 2026-06-16T20:11:42Z | 2026-06-16T21:55:17Z | 1h 43m |
| green | 2026-06-16T21:55:17Z | 2026-06-16T22:22:59Z | 27m 42s |
| review | 2026-06-16T22:22:59Z | 2026-06-16T22:34:38Z | 11m 39s |
| finish | 2026-06-16T22:34:38Z | - | - |

## Technical Context

### Dependencies
- **Blocks:** nothing at this moment
- **Depends on:** 121-7 (F4a2, server engine + validator + wire contract), 121-6 (F4a-design, design spec + ADR-144 amendment)
- **Predecessor:** 121-7 shipped the submission contract and bare input_type surface; this story completes the server→UI render payload and builds the three renderers

### Design References
- **Primary spec:** `docs/superpowers/specs/2026-06-16-fate-interactive-chargen-design.md` — §7 (UI + wire contract), §8 (OTEL + wiring tests)
- **Implementation reconciliation section:** 2026-06-16 Architect clarification at the spec's foot; includes extension points, scope correction, and design clarification on the structural ruleset gate
- **Predecessor story context:** `sprint/context/context-story-121-7.md` (the submission contract this story consumes)
- **Epic context:** `sprint/context/context-epic-121.md` (F4 — Fate Core content migration, ADR-144)

### Story Scope & Technical Approach

This story completes the Fate chargen UI half following the design in §7 and §8 of the spec.

**Server half (121-8 requirement):**
- Extend `protocol/messages.py:390` `CharacterCreationPayload` with additive Fate fields: `fate_aspect_slots`, `fate_available_skills`, `fate_pyramid`, `fate_apex_rating`, `fate_current_allocation`, `fate_ladder_labels`, `fate_available_stunts`, `fate_selected_stunts`, `fate_free_stunts`, `fate_base_refresh`, `fate_current_refresh`, `fate_legal`, `fate_violations`
- Populate via `builder.py:1793` `_render_fate_step_message`, which reads from `self._rules` (FateConfig) + `self._fate_choices` and runs `validate_fate_sheet` at `ruleset/fate_chargen.py:79` to fill `legal`/`violations`
- Pattern mirrors `_render_bones_message` at `builder.py:1843`
- Server is the validation authority; UI mirrors live legality, never adjudicates

**UI half (121-8 deliverable):**
- Extend `types/payloads.ts` `CreationScene` with matching optional fields
- Add three new input_type render blocks to `components/CharacterCreation/CharacterCreation.tsx`:
  1. `fate_aspects` — HC + Trouble + N free inputs, pre-filled from archetype seed, editable; submits edited texts
  2. `fate_skill_pyramid` — allocation widget with live legality mirror (rung labels, remaining slots, payload violations); submits {skill: rating}
  3. `fate_stunts` — catalog picker with refresh readout (base/current); submits selected stunt names
- Each block is an early-return block mirroring precedent renderers (`stat_arrange` at line 260, `roll_the_bones` at 307, `stock` at 355)

**Structural ruleset gate & paired negative test:**
- **Do NOT add a `ruleset=='fate'` conditional in the renderer** (§7, lines 270–272 authoritative)
- The gate is satisfied by *which input_types the pack authors*: a Fate pack emits only `fate_*`; a d20/WN pack emits only `roll_the_bones`/`stat_arrange`/etc
- 121-8 implements the **paired negative test** (Fate-pack chargen run emits no d20 input_type; d20/WN run emits no `fate_*`) as proof the gate holds

### Acceptance Criteria (draft, to be refined by TEA during RED)

1. **Server payload:** `CharacterCreationPayload` gains the §7 Fate fields; `_render_fate_step_message` populates each step from FateConfig + choices, with legal/violations from validate_fate_sheet
2. **fate_aspects renderer:** HC + Trouble + N free inputs, pre-filled from archetype seed, editable; submits edited texts
3. **fate_skill_pyramid renderer:** allocation widget with live legality mirror (rung labels, remaining slots, payload violations); submits {skill: rating}
4. **fate_stunts renderer:** catalog picker with refresh readout (base/current); submits selected stunt names
5. **Structural gate + paired negative:** a Fate pack emits only fate_* input_types; a d20/WN pack emits none; no ruleset conditional in the renderer
6. **Wiring (no source-grep):** a real pulp_noir Guided walk emits each fate_* scene with populated, legal payload that the UI renders; client mirrors, server re-validates

### OTEL & Wiring Tests

The §8 spans (`fate.chargen.*`) are server-side and shipped under 121-7. 121-8's wiring proof includes:
- **Paired negative input_type test:** Fate-pack chargen emits no d20 input_type; WN-pack emits no `fate_*`
- **Real-pack render test:** a pulp_noir Guided walk produces legal scenes with populated payload; wiring asserted via the built character + OTEL span verification

## Sm Assessment

**Setup complete — routing to TEA (red phase).**

- **Story:** 121-8 (F4a3 — Fate chargen UI), 8pt, p2, workflow `tdd` (phased: setup → red → green → review → finish).
- **Design gate SATISFIED:** 121-6 (F4a-design, done) produced the spec; §7/§8 + the 2026-06-16 Architect reconciliation addendum fully specify this story. No fresh design needed.
- **Scope correction (load-bearing):** sprint YAML lists `repos: ui`, but the real scope is **server,ui** — 121-7 (done) deferred the server→UI render payload into this story (`CharacterCreationPayload` has no Fate fields yet; `builder.py:_render_fate_step_message` emits only the bare input_type). The CLI has no `--repos` flag, so this session's **Repos: server,ui** is authoritative. Logged as Deviation 1; at finish, create + merge one PR per repo.
- **Branches created:** `feat/121-8-fate-chargen-ui` in both `sidequest-server` and `sidequest-ui` (github-flow, base `develop`).
- **Dependencies clear:** 121-7 (done) + 121-6 (done); no blockers.
- **Merge gate clear:** only open PR across repos is a Dependabot starlette bump (not a story PR).
- **Handoff to TEA:** refine the six draft ACs (above) during RED; the structural ruleset gate (no `ruleset=='fate'` renderer conditional) + paired-negative test is the wiring proof, alongside a real pulp_noir Guided-walk render test. Server stays the validation authority.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)
**Tests Written:** 33 (server 24, ui 9) across the refined ACs below. Confirmed clean RED via testing-runner — every failure is a contract gap (missing payload field / missing dispatch / missing renderer), zero collection/import/setup errors. The 4 anchors that PASS today are intentional regression guards: the three `test_input_type_is_fate_*` (the bare `input_type` surface 121-7 shipped) and the d20-direction paired-negative (fate surfaces absent on a bones scene) — they de-tautologize the gap tests and must stay green.

**Test Files:**
- `sidequest-server/tests/game/ruleset/test_121_8_fate_render_payload.py` — server→UI render payload (aspects/pyramid/stunts), payload-model field contract, paired-negative render.
- `sidequest-server/tests/server/test_121_8_fate_chargen_handler.py` — client→server submission round-trip through the real `CharacterCreationHandler` (+ no-silent-fallback rejection of an illegal pyramid).
- `sidequest-ui/src/components/CharacterCreation/__tests__/CharacterCreation.fate-chargen.test.tsx` — the three renderers, live-legality mirror, per-step confirms, structural paired-negative gate.

**All tests are fixture-only** — synthetic `FateConfig`/scenes through the real builder/handler/component. No genre pack is loaded in any test (Operator directive: content is validated via `load_genre_pack`, never used as a fixture).

### Refined Acceptance Criteria (TEA, RED)

1. **Render: aspects** — a `fate_aspects` scene emits `fate_aspect_slots` (HC + Trouble required & seeded from `default_high_concept`/`default_trouble`; N free optional slots).
2. **Render: pyramid** — a `fate_skill_pyramid` scene emits `fate_available_skills`, `fate_pyramid`, `fate_apex_rating`, `fate_ladder_labels` (4→Great…1→Average), `fate_current_allocation` (empty initially), and the live mirror `fate_legal`/`fate_violations` (empty allocation → illegal).
3. **Render: stunts** — a `fate_stunts` scene emits `fate_available_stunts` (catalog), `fate_selected_stunts` (empty), `fate_free_stunts`, `fate_base_refresh`, `fate_current_refresh`, and `fate_legal` (empty selection → legal).
4. **Payload model** — the render + submission `fate_*` fields are declared on `CharacterCreationPayload` (`extra="forbid"` requires it).
5. **UI: aspects renderer** — editable slot per aspect, pre-filled; explicit `fate-aspects-confirm` sends `{phase: fate_aspects_confirm, fate_high_concept, fate_trouble, fate_free_aspects}`; nothing auto-commits.
6. **UI: pyramid renderer** — ladder labels visible; live-legality readout mirrors `fate_legal`/`fate_violations` (no client adjudication); `fate-pyramid-confirm` sends `{phase: fate_pyramid_confirm, fate_allocation}`.
7. **UI: stunts renderer** — catalog + refresh readout; `fate-stunts-confirm` sends `{phase: fate_stunts_confirm, fate_selected_stunts}`.
8. **Submission handler (server)** — `fate_*_confirm` phases are dispatched (never "Unknown chargen phase"); the three steps thread into the builder so `build()` attaches the INTERACTIVE sheet (player's pyramid, not the Menu seed); an illegal pyramid submission is rejected loud (No Silent Fallbacks).
9. **Structural gate / paired negative** — fate & d20 surfaces never co-render (server payload + UI); the renderer keys on `input_type` only, with NO `ruleset=='fate'` conditional.
10. **Content (validated, not tested)** — pulp_noir `char_creation.yaml` authors the aspects/pyramid/stunts `fate_chargen_step` scenes; proven by `load_genre_pack`, not a unit test.

### Rule Coverage

| Rule (lang-review) | Test(s) | Status |
|--------------------|---------|--------|
| PY #1 No silent fallbacks | `test_illegal_pyramid_submission_fails_loud` | failing (RED) |
| PY #3 Typed boundaries | `test_render_fields_are_declared`, `test_submission_fields_are_declared` | failing (RED) |
| PY #11 Validate input at boundary | `test_illegal_pyramid_submission_fails_loud` | failing (RED) |
| PY #6 / TS test quality | self-checked — all assertions meaningful (testid/value/onRespond args), no `assert True`, no vacuous truthy checks | n/a |
| TS structural gate (no ruleset cond.) | `structural ruleset gate` describe (both directions) | failing/anchor |
| Wiring (CLAUDE.md, no source-grep) | `test_three_steps_attach_interactive_legal_sheet` (real builder+handler), `test_fate_confirm_phase_is_not_unknown` | failing (RED) |

**Rules checked:** 4 of the applicable Python lang-review rules (#1, #3, #6, #11) + the TS test-quality/structural rules. Path/async/deserialization/resource rules (#5/#7/#8/#9) are not applicable to this payload+renderer surface.
**Self-check:** 1 vacuous/setup-bug test found and fixed (`test_non_fate_scene_carries_no_fate_payload` passed `mechanical_effects=None` to a `CharCreationChoice` → ValidationError; corrected to `MechanicalEffects()`; now fails clean on the contract gap).

**Dev guidance (server is the validation authority; client mirrors):** implement to the pinned snake_case names in the Design Deviations log. The submission handler should accumulate the three steps and reuse 121-7's `record_fate_chargen` → `build()` (no new builder API required); re-run `validate_fate_sheet` on every submission and fail loud. Author pulp_noir's `fate_chargen_step` scenes and prove them with `load_genre_pack`.

**Handoff:** To Inigo Montoya (Dev) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** GREEN — 59/59 server fate tests (24 new 121-8 + 35 121-7 regression); 9/9 UI fate tests; 23/23 UI CharacterCreation regression. Broader server sweep 822/823 (1 pre-existing enum-count drift from 118-3, unrelated). Server ruff + pyright clean on changed files (only pre-existing `_room`/`_rolled_stats`/`add_event` mixin errors remain, line-shifted). UI `tsc -b` + eslint clean. Content validated via `load_genre_pack` (pulp_noir, ruleset: fate, 3 fate steps).

**Branches (pushed):** `feat/121-8-fate-chargen-ui` in sidequest-server, sidequest-ui, sidequest-content.

**Files Changed:**
- server `protocol/messages.py` — `FateAspectSlot`/`FateStuntOption` models + the fate_* render & submission fields on `CharacterCreationPayload`.
- server `game/builder.py` — `_render_fate_step_message` populates the rich payload; per-step accumulator + `apply_fate_aspects/pyramid/stunts` + `preview_fate_pyramid` + `_fate_aspect_slots`/`_fate_ladder_labels`.
- server `game/ruleset/fate_chargen.py` — extracted `pyramid_violations`/`stunt_catalog_violations`; `validate_fate_sheet` composes them (behavior-preserving).
- server `handlers/character_creation.py` — dispatch `fate_aspects/pyramid/stunts_confirm`.
- server `server/websocket_handlers/chargen_mixin.py` — `_chargen_fate_*_confirm` (re-validate, re-prompt illegal pyramid).
- ui `components/CharacterCreation/FateChargenPanel.tsx` (new) — three renderers.
- ui `components/CharacterCreation/CharacterCreation.tsx` — three input_type dispatch blocks.
- ui `types/payloads.ts` — fate_* fields on `CharacterCreationPayload`.
- content `genre_packs/pulp_noir/char_creation.yaml` — three `fate_chargen_step` scenes.

**AC accountability (refined ACs, TEA RED):**
| AC | Status | Evidence |
|----|--------|----------|
| 1 Render aspects | DONE | `TestAspectsRenderPayload` (5) green |
| 2 Render pyramid | DONE | `TestPyramidRenderPayload` (6) green |
| 3 Render stunts | DONE | `TestStuntsRenderPayload` (5) green |
| 4 Payload model fields | DONE | `TestPayloadModelFields` (2) green |
| 5 UI aspects renderer | DONE | fate-chargen.test aspects (2) green |
| 6 UI pyramid renderer | DONE | fate-chargen.test pyramid (3) green |
| 7 UI stunts renderer | DONE | fate-chargen.test stunts (2) green |
| 8 Submission handler round-trip | DONE | `TestFatePhaseDispatch` (3) + `TestFateSubmissionRoundTrip` (2) green |
| 9 Structural gate / paired negative | DONE | server `TestPairedNegativeRender` + UI structural gate (2) green |
| 10 Content fate_chargen_step scenes | DONE | `load_genre_pack(pulp_noir)` → 3 fate steps, ruleset: fate |

**Self-review:** Code wired end-to-end (UI submit → handler → builder → build → interactive sheet; render payload → renderers). Server is the validation authority; client mirrors. No silent fallbacks (illegal pyramid re-prompts; build re-validates whole sheet, fails loud). No stubs/dead code.

**Handoff:** To Westley (Reviewer).

## Dev Rework Assessment (Reviewer REJECT addressed)

**Status:** GREEN — 91 tests pass (64 server incl. 35 121-7 regression + 6 new rework tests; 27 UI incl. the new per-rung-budget test). Content still loads. ruff/format/pyright clean on changed files (only pre-existing mixin errors remain); UI tsc/eslint clean. Pushed.

**Reviewer findings → resolution:**
- **[HIGH] chargen dead-end / uncaught FateChargenError** → FIXED three ways: (1) free aspects are now OPTIONAL at chargen (`validate_fate_sheet` uses `<= free_aspect_count`) — the default flow (blank free slots) now builds a legal sheet (root cause). (2) `_chargen_confirmation` catches `FateChargenError` → structured error (defense-in-depth; never leaks). (3) `fate_aspects_confirm` re-prompts empty HC/Trouble early. Tests: `test_default_flow_zero_free_aspects_builds_legal_sheet`, `test_empty_high_concept_is_re_prompted_early`, `test_confirmation_catches_illegal_fate_build`.
- **[MED][SEC] info-leak `{exc!r}`** → handlers log the repr server-side, return generic client messages.
- **[MED][SEC] unbounded inputs** → Pydantic bounds on submission fields (HC/Trouble 200; free aspects 10×200; allocation/stunts 50).
- **[MED][SEC] stunts not validated at boundary** → `fate_stunts_confirm` runs `stunt_catalog_violations`, rejects early. Test: `test_out_of_catalog_stunt_rejected_at_boundary`.
- **[MED] rung counts discarded** → `FateSkillPyramidPanel` consumes `fate_pyramid`, shows placed/total per rung. Test: "shows per-rung budgets from fate_pyramid".
- **[LOW] builder._rules** → `builder.rules`. **[LOW] ladder type** → `Record<string,string>`. **[LOW] double-cast** → builders typed `Partial<CreationScene>`, cast removed.

**Contract change (deviation):** free aspects optional (≤ count) per story AC1 / epic "refined in play"; 121-7 exact-count test updated to a cap + a fewer-is-legal test.

**Handoff:** Back to Westley (Reviewer) for re-review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 smells (gates all PASS: ruff/format/pyright clean, 59 server + 9 ui green, pulp_noir loads) | confirmed 3 (1 MED rung-counts, 2 LOW), dismissed 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 7 | confirmed 1 (folds into HIGH), downgraded 6 (LOW, optional-by-design / defensive UI defaults) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer — docstrings accurate) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer — double-cast + ladder-label type) |
| 7 | reviewer-security | Yes | findings | 5 | confirmed 3 (2 MED bounds + 1 MED info-leak), folded 2 (catalog-at-boundary into HIGH) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer — builder._rules) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings (covered by Reviewer — Rule Compliance below) |

**All received:** Yes (3 enabled returned; 6 disabled pre-filled and covered by Reviewer's own analysis)
**Total findings:** 1 HIGH + 3 MEDIUM + 3 LOW confirmed; 8 downgraded/dismissed with rationale

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **Default chargen flow dead-ends with an uncaught exception.** The aspects renderer shows 3 free-aspect slots as *optional* (`required:false`, empty `suggestion`) and filters empties on submit, but `validate_fate_sheet` requires **exactly** `free_aspect_count` (3) character aspects. A player who accepts the pre-filled HC/Trouble and leaves the free slots blank (the default) submits 0 free aspects → walks pyramid + stunts → at confirmation `build()` → `apply_fate_chargen` raises `FateChargenError` (a `ValueError`). `_chargen_confirmation` catches only `BuilderError` (chargen_mixin.py:1228), and `handle_message` has no try-wrap (websocket_session_handler.py:492) → the exception leaks to the socket. Chargen cannot complete via the normal path. | UI `FateChargenPanel.tsx` (free-aspect optional/filter) + `chargen_mixin.py` `_chargen_fate_aspects_confirm` (None-only guard) + `_chargen_confirmation:1228` (BuilderError-only catch) | (a) `_chargen_confirmation` MUST catch `FateChargenError`/`ValueError` from `build()` → structured error (never leak); (b) `fate_aspects_confirm` re-validate HC+Trouble non-empty AND free-aspect count, re-prompt (mirror the pyramid path); (c) resolve the UI optional-vs-required free-aspect contradiction; (d) `fate_stunts_confirm` call `stunt_catalog_violations` + re-prompt. |
| [MEDIUM] | **[SEC] Info leakage (CWE-209):** `{exc!r}` embedded in client-facing ERROR strings exposes class names, scene ids, rung counts, skill names. | chargen_mixin.py:497, 530, 552 | `logger.exception` server-side; return a generic category string to the client. |
| [MEDIUM] | **[SEC] Unbounded player inputs:** aspect strings, `fate_selected_stunts`, and `fate_allocation` have no `max_length`/`max_items` — prompt-token abuse, O(N) violation building, and attacker-controlled content echoed in violation strings. | messages.py fate_* fields (+ UI inputs lack maxLength) | Pydantic `Field(max_length=...)` on the fate text/list/dict fields; UI `maxLength`. |
| [MEDIUM] | **[preflight] Rung counts sent but unused.** Server sends `fate_pyramid` (rung counts, e.g. `[1,2,3,4]`); `FateSkillPyramidPanel` never receives it and shows only tier labels, not the per-rung "place N skills here" counts the spec §7 ("remaining slots") and the mechanics-first rubric (Sebastien/Jade) call for. | FateChargenPanel.tsx `FateSkillPyramidPanel`; CharacterCreation.tsx pyramid block | Thread `fate_pyramid` into the panel; render per-rung counts / remaining slots. |
| [LOW] | **[SIMPLE] Encapsulation bypass:** `builder._rules` reaches past the public `builder.rules` property. | chargen_mixin.py:514 | Use `builder.rules.ruleset_config()`. |
| [LOW] | **[TYPE] Type inconsistency:** `fate_ladder_labels` is `Record<number,string>` in payloads.ts but `Record<string,string>` in CharacterCreation.tsx (JSON keys are strings). | payloads.ts:230 / CharacterCreation.tsx:86 | Unify to `Record<string,string>`. |
| [LOW] | **[TYPE] Double-cast** `scene as unknown as CreationScene` (TS checklist #1 — "almost always wrong"). | CharacterCreation.fate-chargen.test.tsx:88 | Type the scene builders/param so the cast is unnecessary. |

**Data flow traced:** player free-aspect text → UI `fate_aspects_confirm` (filters empties) → `_chargen_fate_aspects_confirm` (None-guard only) → `builder.apply_fate_aspects` (stores raw) → … → `_chargen_confirmation` → `build()` → `apply_fate_chargen` → `validate_fate_sheet` → **FateChargenError on count mismatch** → **uncaught** (BuilderError-only catch + no handle_message wrap). The unhappy path is the *default* path. Player aspect text that DOES reach the narrator is sanitized downstream at `fate_projection.py:59` (ADR-047) — [SEC] verified no new bypass introduced.

**Tag coverage:** `[SILENT]` empty/incomplete aspects accepted then rejected late (finding HIGH); `[SEC]` info-leak + unbounded inputs (MED) + sanitization gate verified; `[EDGE]` (subagent disabled — Reviewer) out-of-order submission + empty-config defaults traced, low risk; `[TEST]` (disabled — Reviewer) assertions are meaningful, but the suite has NO test for the incomplete-aspects→confirmation path (the HIGH gap) — that's the missing coverage TEA must add; `[DOC]` (disabled — Reviewer) docstrings accurate, deferral note correctly removed; `[TYPE]` ladder-label + double-cast (LOW); `[SIMPLE]` builder._rules (LOW); `[RULE]` see Rule Compliance.

### Rule Compliance

- **No Silent Fallbacks (SOUL/CLAUDE):** pyramid path COMPLIES (re-prompts illegal). Aspects/stunts path VIOLATES the spirit — illegal/incomplete input is accepted at the step and only rejected (loud, but late and *uncaught*) at build(). → HIGH finding.
- **Server is the validation authority; never leak exceptions:** VIOLATED — `_chargen_confirmation` does not catch the fate `build()` raise; `{exc!r}` leaks internals on the paths it does catch. → HIGH + MED.
- **Input validation at boundaries (PY #11):** pyramid validated at boundary (good); stunts NOT (deferred to build); no input bounds (MED).
- **OTEL (CLAUDE):** COMPLIES — `character_creation.fate_{aspects,pyramid,stunts}_confirm` events added; `fate.chargen.*` spans fire from apply_fate_chargen (121-7). [VERIFIED] chargen_mixin add_event calls present.
- **Crunch legible in player UI (CLAUDE playgroup rubric):** PARTIAL — ladder labels shown, but rung counts (the allocation budget) discarded. → MED.
- **Single legality authority (§9):** COMPLIES — `validate_fate_sheet` composes the extracted `pyramid_violations`/`stunt_catalog_violations`; 35 121-7 tests green. [VERIFIED] fate_chargen.py:117-156.
- **No stubs/dead code:** COMPLIES — all new methods wired; BUT `fate_pyramid` is received-and-discarded data (dead data, MED).

### Devil's Advocate

Assume a real player at Keith's table. Alex — slow, no time pressure — opens the Fate aspects screen. High Concept and Trouble are already filled (the seed). Below them sit three blank boxes labelled only "Aspect," with no hint of what they want or that they're mandatory. Alex, reasonably, leaves them blank and clicks Confirm — the boxes looked optional, and nothing said otherwise. Alex allocates the pyramid (the one step that *does* push back), picks a stunt or two, and clicks the final Confirm… and the character never appears. Best case, a cryptic error string full of Python `repr()`; worst case (the actual code path — no try-wrap at handle_message:492), the socket throws and the screen hangs. Alex cannot make a character. This is not a contrived edge — it is the *path of least resistance* through the new flow, and it is exactly the player the playgroup rubric tells us to protect. A confused user doesn't read three empty boxes as "fill all of these or the game breaks at the very end." Worse, the failure is maximally late: the player invests the whole walk before the wall. A malicious client makes it uglier — a 1 MB High Concept inflates the narrator prompt; a 100k-entry stunt list or allocation dict spins `validate_fate_sheet` building one violation string per entry, each echoing attacker text back through the leaked `{exc!r}`. The server is supposed to be the authority that fails *loud and early at the boundary*; here it fails *loud, late, and uncaught*. The pyramid step proves the team knows the right pattern (validate-and-re-prompt at the handler) — it simply wasn't applied to aspects or stunts, and the confirmation handler's catch is too narrow to backstop it. None of this is hard to fix; all of it must be fixed before a player touches it.

**Observations (≥5):**
1. [HIGH] incomplete-aspects → uncaught FateChargenError (above).
2. [MED][SEC] `{exc!r}` info leak — chargen_mixin.py:497/530/552.
3. [MED][SEC] unbounded fate inputs — messages.py.
4. [MED] rung counts discarded in UI — FateChargenPanel.tsx.
5. [LOW][SIMPLE] builder._rules vs builder.rules — chargen_mixin.py:514.
6. [LOW][TYPE] ladder-label type mismatch — payloads.ts:230.
7. [LOW][TYPE] test double-cast — fate-chargen.test.tsx:88.
8. [VERIFIED] validator refactor behavior-preserving — fate_chargen.py:117-156, 35/35 121-7 tests green.
9. [VERIFIED] structural ruleset gate correct — renderer keys on input_type only, paired-negative tests green (server + UI).

**Handoff:** Back to Fezzik (TEA) for red-phase rework — the HIGH and the validation MEDs are testable logic gaps (add the incomplete-aspects→structured-error test, the catalog-re-prompt test, the bounds tests).

## Subagent Results (re-review, round-trip 1)

| # | Specialist | Received | Status | Decision |
|---|-----------|----------|--------|----------|
| 1 | reviewer-preflight | Yes | GREEN (64 server + 10 ui pass, content loads, ruff/tsc/format clean, 0 smells) | confirmed pass |
| 2 | reviewer-edge-hunter | Skipped | disabled | covered by Reviewer |
| 3 | reviewer-silent-failure-hunter | Yes | clean (0 findings) | all 4 prior concerns confirmed resolved |
| 4 | reviewer-test-analyzer | Skipped | disabled | covered by Reviewer (new regression tests meaningful) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | covered by Reviewer |
| 6 | reviewer-type-design | Skipped | disabled | covered by Reviewer (double-cast removed) |
| 7 | reviewer-security | Yes | findings | prior 3 RESOLVED/partial; 2 new MED + 1 pre-existing LOW (non-blocking) |
| 8 | reviewer-simplifier | Skipped | disabled | covered by Reviewer |
| 9 | reviewer-rule-checker | Skipped | disabled | covered by Reviewer |

**All received:** Yes (3 enabled returned; 6 disabled covered by Reviewer)

## Reviewer Assessment (re-review, round-trip 1)

**Verdict:** APPROVED

The round-1 **HIGH** (chargen dead-end / uncaught `FateChargenError`) is **RESOLVED** — verified three ways: preflight GREEN (64 server + 10 ui), silent-failure **CLEAN**, and my own code check — `validate_fate_sheet` now caps free aspects (`> free_aspect_count`, fate_chargen.py:141); `_chargen_confirmation` catches `FateChargenError` (chargen_mixin.py:1254, logs `fate_build_rejected`); `fate_aspects_confirm` re-prompts empty HC/Trouble; `fate_stunts_confirm` validates the catalog at the boundary (:565); generic client messages + server-side `logger.warning` at all four sites; `builder.rules` (public). New regression tests assert the default-flow build, the empty-HC re-prompt, the confirmation catch, and the catalog reject — non-vacuous.

**Tag coverage:** `[SILENT]` clean (subagent); `[SEC]` prior MEDs resolved, 2 new MED follow-ups recorded below; `[TEST]` (Reviewer) the 6 new regression tests are meaningful and cover the HIGH; `[EDGE]` (Reviewer) the `_render_fate_step_message` `isinstance(cfg, FateConfig)` guard is a fail-loud for a *misconfigured* pack (never fires for a valid fate pack — correct No-Silent-Fallback, not a leak in practice); `[TYPE]` double-cast removed, ladder labels `Record<string,string>`; `[SIMPLE]` `builder._rules`→`builder.rules`; `[DOC]` docstrings accurate; `[RULE]` No-Silent-Fallbacks + validate-at-boundary + OTEL events all satisfied on the fate paths.

**Non-blocking findings (MEDIUM/LOW — do not block; personal-project threat model, count caps already in place):**
- [MED][SEC] `fate_allocation` dict keys and `fate_selected_stunts` items are count-capped (50) but not per-item length-capped; the stunt-violation message echoes the submitted name. These fields don't reach the narrator (aspect text IS length-capped at 200). Crafted-client-only.
- [LOW][SEC] pre-existing `{exc!r}` client leaks in paths 121-8 did not touch (`back`, `arrange_reject`, `story_autogen`, the BuilderError branch of `_chargen_confirmation`).

**Data flow re-traced:** default flow (HC/Trouble seeded, free blank → 0 free aspects) → submit → build() → legal sheet, character created. No dead-end. **Handoff:** To Vizzini (SM) for finish.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking — absorbed into 121-8): the client→server submission handler is missing. `handlers/character_creation.py` has no `fate_*` phase branch and `record_fate_chargen` has zero production callers, so a UI fate submission falls through to `_error_msg("Unknown chargen phase")`. Affects `sidequest-server/sidequest/handlers/character_creation.py` (+ a `_chargen_fate_*` seam on the session, threading into the builder). *Found by TEA during test design.*
- **Gap** (blocking — absorbed into 121-8): no pack authors `fate_chargen_step` scenes, so the interactive Fate flow cannot appear in play. Affects `sidequest-content/genre_packs/pulp_noir/char_creation.yaml` (author the aspects/pyramid/stunts step scenes; validated via `load_genre_pack`, NOT a test). *Found by TEA during test design.*
- **Improvement** (non-blocking): the three other Fate packs (tea_and_murder, wry_whimsy, spaghetti_western) have no `fate_chargen_step` scenes and their migration stories 121-3/4/5 are *canceled*. A follow-up is needed for them to get interactive chargen. Affects those packs' `char_creation.yaml`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking, pre-existing — NOT introduced by 121-8): `tests/protocol/test_enums.py::test_message_type_complete_count` asserts MessageType count 56 but it is 57 (story 118-3's `FATE_ROLL`). My changes add nested payload models (`FateAspectSlot`/`FateStuntOption`), not `MessageType` enum members, so this is unrelated stale-assertion drift. Affects `sidequest-server/tests/protocol/test_enums.py` (bump the expected count). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the pyramid widget is a per-skill rating select (functional, mechanics-legible). A future polish could make it a drag/click pyramid grid with remaining-slot counters per rung. Affects `sidequest-ui/src/components/CharacterCreation/FateChargenPanel.tsx`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): incomplete/empty aspects (the default flow) produce an illegal sheet that reaches `build()`, and `_chargen_confirmation` does not catch `FateChargenError` → uncaught exception leaks; chargen dead-ends. Affects `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` (catch the fate build() raise + re-prompt aspects/stunts at the step) and `sidequest-ui/.../FateChargenPanel.tsx` (free-aspect optional/required contract). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): info-leak (`{exc!r}` to client), unbounded fate inputs (no `max_length`/`max_items`), discarded `fate_pyramid` rung counts, `builder._rules` encapsulation bypass, ladder-label `Record<number>` vs `Record<string>`, test double-cast. Affects `chargen_mixin.py`, `protocol/messages.py`, `FateChargenPanel.tsx`, `payloads.ts`. *Found by Reviewer during code review.* → all ADDRESSED in rework.
- **Improvement** (non-blocking, re-review): per-item length bounds missing — `fate_allocation` dict keys and `fate_selected_stunts` items are count-capped (50) but not length-capped; stunt-violation messages echo the submitted name. Add `Field(max_length=200)` to the dict key + list items; make the stunt-violation client message count-only. Affects `sidequest-server/sidequest/protocol/messages.py` + `chargen_mixin.py:571`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking, re-review, pre-existing): `{exc!r}` still leaked to client in paths 121-8 did not touch — `handlers/character_creation.py:90` (`back`), `chargen_mixin.py` `arrange_reject`/`story_autogen` and the BuilderError branch of `_chargen_confirmation`. A repo-wide sweep to the log-and-generic pattern is warranted. *Found by Reviewer during re-review.*

## Design Deviations

**Deviation 1 — Repos mismatch (known, logged at setup):** Sprint YAML lists `repos: ui`, but Architect verified 2026-06-16 that the correct scope is `server,ui`. 121-7 deferred the render payload (CharacterCreationPayload Fate fields + _render_fate_step_message) to this story's UI consumer. At finish, create + merge a PR per repo (sidequest-server AND sidequest-ui); do not trust finish to discover the server repo from YAML.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Submission-handler pillar added to scope (server)**
  - Spec source: context-story-121-8.md, AC6 + Technical Approach
  - Spec text: "Consumes the F4a2 wire contract; server remains the validation authority (No Silent Fallbacks — client mirrors, does not adjudicate)."
  - Implementation: RED adds a client→server submission pillar — `fate_aspects_confirm` / `fate_pyramid_confirm` / `fate_stunts_confirm` phases dispatched in `handlers/character_creation.py`, recorded into the builder, with `build()` attaching the interactive sheet. 121-7's `record_fate_chargen` has zero production callers and the handler had no fate branch.
  - Rationale: without it the UI's submissions hit "Unknown chargen phase" — a half-wired feature (CLAUDE.md "No half-wired features"). Operator confirmed inclusion 2026-06-16.
  - Severity: major
  - Forward impact: no sibling story owns this; it is delivered here. Reviewer must verify the round-trip end-to-end.
- **Content authoring added (pulp_noir fate_chargen_step scenes)**
  - Spec source: context-story-121-8.md, AC6
  - Spec text: "a real pulp_noir Guided walk emits each fate_* scene with a populated, legal payload that the UI renders"
  - Implementation: pulp_noir `char_creation.yaml` gains aspects/pyramid/stunts `fate_chargen_step` scenes; `fate_chargen_step` is authored in no pack today. Repos expanded to `server,ui,content`.
  - Rationale: AC6's live walk is unsatisfiable without authored step-scenes; Operator chose "Author pulp_noir scenes now" 2026-06-16.
  - Severity: major
  - Forward impact: tea_and_murder / wry_whimsy / spaghetti_western (121-3/4/5 canceled) still lack step scenes — see Delivery Findings.
- **Tests use synthetic fixtures; content is validated, not tested**
  - Spec source: context-story-121-8.md, AC6
  - Spec text: "a real pulp_noir Guided walk emits each fate_* scene ... OTEL/fixture-driven, not a read_text() grep"
  - Implementation: AC6's wiring is proven with synthetic `FateConfig`/scenes through the real builder + handler (NO genre pack loaded in any test); the authored pulp_noir scenes are proven by `load_genre_pack` / the content validator, NOT by a pytest fixture pointing at the pack.
  - Rationale: Operator directive 2026-06-16 — "DO NOT TEST AGAINST CONTENT! MAKE FIXTURES! Validate content." Tests pointing at live packs are the prod-rows-in-tests anti-pattern.
  - Severity: minor
  - Forward impact: the GREEN gate for the content piece is `load_genre_pack` success, not a unit test. Dev runs the loader; Reviewer verifies it.
- **Pinned wire-contract field + phase names (snake_case, extra="forbid")**
  - Spec source: context-story-121-8.md, Technical Approach (wire-contract field list)
  - Spec text: "Extend `protocol/messages.py:390` `CharacterCreationPayload` with additive Fate fields: `fate_aspect_slots`, `fate_available_skills`, `fate_pyramid`, ..."
  - Implementation: TEA pinned the exact shared names (render: `fate_aspect_slots`, `fate_available_skills`, `fate_pyramid`, `fate_apex_rating`, `fate_current_allocation`, `fate_ladder_labels`, `fate_available_stunts`, `fate_selected_stunts`, `fate_free_stunts`, `fate_base_refresh`, `fate_current_refresh`, `fate_legal`, `fate_violations`; submit: `fate_high_concept`, `fate_trouble`, `fate_free_aspects`, `fate_allocation`, `fate_selected_stunts`; phases `fate_aspects_confirm` / `fate_pyramid_confirm` / `fate_stunts_confirm`).
  - Rationale: `extra="forbid"` + a snake_case wire requires an exact shared contract so server and UI agree (the posture 121-7 took with its PINNED PUBLIC CONTRACT). Prevents a silent wire mismatch.
  - Severity: minor
  - Forward impact: Dev implements to these names across all three repos; the UI `CreationScene` type mirrors them.
- **Pinned live-legality mirror semantics (empty allocation illegal; empty stunts legal)**
  - Spec source: design spec §7/§9 (the live-legality mirror)
  - Spec text: "Live legality in the UI is a convenience mirror of the server validator; the server re-validates every submission and on build()."
  - Implementation: the render payload's `fate_legal` reflects the validator on the CURRENT state — an empty pyramid is illegal (rung counts unmet → `fate_violations` non-empty); zero stunts is legal (within the free budget).
  - Rationale: the mirror must reflect the real validator at each step so the player sees honest feedback (Sebastien/Jade: the math on screen).
  - Severity: trivial
  - Forward impact: none; Dev honors these semantics when populating the render payload.

### Dev (implementation)
- **Per-step builder accumulator added (small new builder API)**
  - Spec source: 121-8 session TEA Assessment, "Dev guidance"
  - Spec text: "The submission handler should accumulate the three steps and reuse 121-7's record_fate_chargen → build() (no new builder API required)"
  - Implementation: added `CharacterBuilder.apply_fate_aspects/apply_fate_pyramid/apply_fate_stunts` + `preview_fate_pyramid` + a typed per-step accumulator (`_fate_high_concept/_fate_trouble/_fate_free_aspects/_fate_pyramid/_fate_stunts`). The stunts step assembles a `FateChargenChoices` and routes through the EXISTING `record_fate_chargen` → `build()`; the accumulator owns the cross-step state and feeds the live render mirror (current_allocation / selected_stunts / slot values).
  - Rationale: the render mirror needs the in-progress state (TEA's render ACs read current_allocation/selected_stunts), and per-step commits must record a SceneResult + advance (the per-presented-scene ledger doctrine, mirroring `apply_bones_confirm`). Pure handler-side accumulation could not satisfy the live render mirror.
  - Severity: minor
  - Forward impact: none; the builder API is additive and fate-gated.
- **Extracted pyramid_violations / stunt_catalog_violations from validate_fate_sheet (refactor)**
  - Spec source: design spec §9
  - Spec text: "validate_fate_sheet is the single legality authority ... a rule lives in exactly one place"
  - Implementation: factored the pyramid-shape and stunt-catalog subsets into reusable pure functions; `validate_fate_sheet` now composes them, and the render mirror + pyramid-confirm re-validation call the same functions. Behavior-preserving — all 35 121-7 validator tests stay green.
  - Rationale: the live per-step mirror needs a focused subset (an empty pyramid is illegal but empty stunts is legal); reusing the authority's own sub-functions avoids duplicating the rules.
  - Severity: minor
  - Forward impact: none; same authority, more entry points.
- **Pyramid submission re-prompts; stunts validated at build()**
  - Spec source: design spec §7/§9
  - Spec text: "an illegal candidate is corrected or re-prompted — never silently accepted ... the server re-validates every submission and on build()"
  - Implementation: `fate_pyramid_confirm` re-validates server-side and, on an illegal allocation, echoes it and re-renders the pyramid step with its violations (no advance). `fate_aspects_confirm` requires HC+Trouble present; `fate_stunts_confirm` records and advances, and the WHOLE-sheet legality (aspect count, refresh, catalog) is enforced at `build()` via `apply_fate_chargen` (fail loud). So every submission is re-validated, but the pyramid is the only step with an in-step re-prompt.
  - Rationale: the pyramid is the step most likely to be submitted illegal (the allocation puzzle); aspects/stunts illegality is rarer and caught loud at build. Matches the test contract (`test_illegal_pyramid_submission_fails_loud`).
  - Severity: minor
  - Forward impact: a future story may add in-step re-prompts for aspects/stunts for symmetry (not required now).
- **UI filters empty free-aspect slots on submit**
  - Spec source: design spec §4 (free_aspect_count)
  - Spec text: "free aspects (N pack-configurable)"
  - Implementation: the aspects renderer submits only non-empty free-aspect texts, so a player who leaves free slots blank submits fewer than `free_aspect_count`; `build()` then rejects the incomplete sheet loud (validate_fate_sheet's free-aspect-count check). The UI does not block submission (client mirrors, never adjudicates).
  - Severity: trivial
  - Forward impact: none; server remains the authority.

### Dev (rework)
- **Free aspects made OPTIONAL at chargen (≤ free_aspect_count, was exact)**
  - Spec source: context-story-121-8.md AC1 ("N free **optional** slots") + epic 121 ("default aspects seeded + refined in play")
  - Spec text: design spec §9 listed the free-aspect count as an *exact* validated rule, which contradicted the story AC + epic intent.
  - Implementation: `validate_fate_sheet` now flags only `len(free_aspects) > cfg.free_aspect_count`; 0..N is legal. Resolves the Reviewer's HIGH (default blank-free-slots flow now builds a legal sheet). 121-7's `test_wrong_free_aspect_count_is_rejected` retired → `test_too_many_free_aspects_is_rejected` + `test_fewer_free_aspects_is_legal`.
  - Rationale: per the spec-authority hierarchy, the story AC (2) + epic context (3) outrank the design spec (4); the exact-count rule was the bug. Aligns with Fate "aspects refined in play."
  - Severity: minor (semantics widened, not narrowed — no legal sheet becomes illegal)
  - Forward impact: future packs may rely on free aspects being optional; the design spec §4/§9 should be amended to say "≤ N" (noted for the Architect).

### Reviewer (re-audit, round-trip 1)
- **Dev (rework): Free aspects made OPTIONAL (≤ free_aspect_count)** → ✓ ACCEPTED: grounded in story AC1 + epic "refined in play"; widens semantics (no legal sheet becomes illegal), resolves the HIGH at the root, 121-7 tests updated coherently.
- **Round-1 FLAGGED "Dev: Pyramid re-prompts; stunts at build()"** → ✓ ADDRESSED: aspects re-prompt empty HC/Trouble, stunts validate catalog at the boundary, and `_chargen_confirmation` now catches `FateChargenError` (no uncaught leak).
- **Round-1 FLAGGED "Dev: UI filters empty free-aspect slots"** → ✓ ADDRESSED: with free aspects optional, the optional/required contradiction is gone; blank free slots are a legal state.

### Reviewer (audit)
- **TEA: Submission-handler pillar added to scope** → ✓ ACCEPTED: the gap was real (record_fate_chargen had zero callers); absorbing it was correct.
- **TEA: Content authoring added (pulp_noir scenes)** → ✓ ACCEPTED: required for the flow to appear; validated via load_genre_pack, not a test.
- **TEA: Tests use synthetic fixtures, content validated not tested** → ✓ ACCEPTED: matches the Operator directive and the prod-rows-in-tests rule.
- **TEA: Pinned wire-contract field + phase names** → ✓ ACCEPTED: server and UI agree on snake_case names; verified end-to-end.
- **TEA: Pinned live-legality mirror semantics** → ✓ ACCEPTED: render mirror reflects validate_fate_sheet on current state.
- **Dev: Per-step builder accumulator** → ✓ ACCEPTED: necessary for the live mirror + cross-step state; additive, fate-gated.
- **Dev: Extracted pyramid_violations/stunt_catalog_violations** → ✓ ACCEPTED: behavior-preserving (35/35 121-7 green), preserves the single authority.
- **Dev: "Pyramid re-prompts; stunts validated at build()"** → ✗ FLAGGED by Reviewer: this is the root of the HIGH finding. Deferring aspect/stunt legality to build() is only safe if build()'s raise is caught and surfaced — it is NOT (`_chargen_confirmation` catches `BuilderError` only; `FateChargenError` leaks uncaught). Aspects/stunts must re-prompt at the step (mirror the pyramid), and confirmation must catch the build() raise. See severity table HIGH.
- **Dev: UI filters empty free-aspect slots on submit** → ✗ FLAGGED by Reviewer: combined with `validate_fate_sheet`'s *exact* `free_aspect_count` requirement, this makes the default flow (free slots left blank) submit an illegal sheet. The slots are presented as optional but are effectively mandatory — an optional/required contradiction that dead-ends chargen. Resolve the contract (require the slots in-UI, or surface the count requirement) AND ensure the server rejects gracefully.