# Story 71-1: space_opera Rules page — render per-class signature ability in the class picker

## Story Details
- **ID:** 71-1
- **Epic:** 71 (Playtest bugfix — uncovered findings (coyote_star MP, 2026-05-27))
- **Type:** Bug
- **Points:** 3
- **Priority:** P2
- **Repos:** sidequest-server
- **Workflow:** tdd
- **Status:** backlog

## Story Context

**Problem:** The space_opera Rules page class picker currently renders a class card with:
- Display name (heading)
- Flavor text
- Role, Prime Requisite, Magic Access (label grid)
- Beat Choices (chip strip)

Missing: Each class has a **signature ability** (per ADR-095, exactly one per non-magical class) that should be visible on the class card. The ability includes:
- Name (e.g., "Call the Shot", "Threading the Needle")
- Genre description (narrative flavor)
- Mechanical effect (what the ability does)

Reference data: `/sidequest-content/genre_packs/space_opera/classes.yaml` — each class has an `abilities` list with a single item (involuntary: false).

**Acceptance Criteria:**

1. The `_class_panel_body()` function in `reference_presenters.py` extracts the class's signature ability (if present) and renders it in the class card.
2. The rendered ability includes the name, genre_description, and mechanical_effect in a visually distinct container within the card.
3. The card layout preserves existing elements (flavor, label grid, beat choices) and adds the ability section below them.
4. A test in `test_reference_presenters.py` verifies that a class with a signature ability renders all three fields (name, genre_description, mechanical_effect).
5. Lint and typecheck pass. No debug code. Tree clean.

## Technical Approach

The fix is a presenter enhancement:

1. **Extract ability from class dict** — In `_class_panel_body()`, after rendering the label grid and beat choices, check if the class has an `abilities` field (list).
2. **Render ability section** — If `abilities` is present and non-empty, extract the first item and render:
   - Ability name as a sub-heading (e.g., `<h4>`)
   - Genre description as narrative prose
   - Mechanical effect as a separate block (possibly with a distinct CSS class for visual emphasis)
3. **CSS class** — Use `ref-card__ability` or similar namespace (coordinating with story 63-7's reference CSS) to style the ability section. Do not invent new classes; ensure they exist in `sidequest/server/static/reference/presenters.css`.
4. **Unit test** — Add `test_class_picker_renders_signature_ability()` to `test_reference_presenters.py` that:
   - Constructs a class dict with an `abilities` list containing one ability
   - Calls `present_classes_picker()`
   - Asserts that the HTML contains the ability name, genre_description, and mechanical_effect
5. **Integration test** — Verify the wiring by checking that space_opera classes on the live Rules page render their signature abilities (can be done manually or via a page render fixture).

## Workflow Tracking
**Workflow:** tdd
**Phase:** spec-reconcile
**Phase Started:** 2026-05-28T01:31:36Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-27 | 2026-05-27 | - |
| red | 2026-05-27 | 2026-05-27 | - |
| green | 2026-05-27 | 2026-05-28T01:23:07Z | 25h 23m |
| review | 2026-05-28T01:23:07Z | 2026-05-28T01:31:36Z | 8m 29s |
| spec-reconcile | 2026-05-28T01:31:36Z | - | - |

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Improvement** (non-blocking): Pre-existing pyright type error at `sidequest/server/reference_presenters.py:928` (line 897 on base commit 9fd47bf). Affects `present_magic`'s hard-limits block (`rows = "".join(...)` reassigns a name annotated `list[str]` in the later counters block, so pyright flags the `str` assignment). Unrelated to 71-1; left untouched per minimalist scope discipline. *Found by Dev during implementation.*

### Reviewer (code review)
- No upstream findings. The change is a self-contained presenter enhancement; the
  reference-route → registry → presenter pipeline it plugs into is pre-existing and was
  verified reachable end-to-end during review (`app.py:296` → `create_reference_router`
  → `reference_renderer` → `PRESENTERS[("classes", ())]` → `present_classes_picker`
  → `_class_panel_body`).
- **Improvement** (non-blocking, corroborates Dev/Architect): pre-existing pyright error
  at `reference_presenters.py:928` (`present_magic`) confirmed present on `develop` and
  outside the 71-1 diff. Correctly scoped to follow-up chore 71-8. Affects
  `sidequest-server/sidequest/server/reference_presenters.py` (the `rows` reassignment in
  `present_magic`). *Confirmed by Reviewer during code review.*

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None (one trivial defensive addition, accepted)

Verified the GREEN implementation in `_class_panel_body()` against the contract and all five ACs:

- **AC1** — Signature ability extracted only when `item.get("abilities")` is a non-empty list; takes `abilities[0]`. Magical/empty classes emit no block (guard confirmed by `test_class_picker_omits_ability_section_when_absent`). ✅
- **AC2** — name / genre_description / mechanical_effect render inside a visually distinct `.ref-card__ability` container (margin-top, accent left-border, inset `.ref-card__ability-effect` block with darker bg for mechanical weight). Matches the DOM contract exactly. ✅
- **AC3** — flavor, label grid, and beat-choice strip preserved; ability section appended last. Ordering asserted (`Beat Choices` index < `ref-card__ability` index). ✅
- **AC4** — `test_class_picker_renders_signature_ability` asserts all three field texts plus the container/name/effect classes and kicker. Escaping covered by a dedicated test. 39/39 green. ✅
- **AC5** — Ruff clean on both changed files. See pyright note below. ✅ (with disclosure)

**Trivial addition (accepted, Option A):** Dev independently guarded each of the three fields (`if name`, `if genre_description`, `if mechanical_effect`) so a partial ability dict won't emit empty tags. This is beyond the literal contract but is sound defensive rendering with no behavioral downside — accepted as-is, no spec change needed beyond this note.

**Pyright disclosure — concur, out of lane:** Independently verified the lone pyright error at `reference_presenters.py:928` (`rows` reassigned `str` into a `list[str]`-annotated name) lives in `present_magic`'s hard-limits block and is **not** in the 71-1 diff (`git diff develop … | grep rows` → empty). Pre-existing, unrelated to the signature-ability work. I concur with Dev that fixing it is out of scope for 71-1 — it belongs in a separate chore. Correctly logged as a non-blocking delivery finding.

**Decision:** Proceed to review.

## Design Deviations

None yet. Deviations logged here as they occur.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Implemented exactly to the Architect's GREEN contract (relayed by team-lead): `ref-card__ability` container with a `ref-card__kicker` "Signature Ability" eyebrow, `ref-card__ability-name` sub-heading, `ref-card__body` genre_description, and `ref-card__ability-effect` mechanical block — appended after the beat-choices chip strip, guarded on a non-empty `abilities` list, `abilities[0]` taken without `involuntary` filtering.

### Reviewer (audit)
- **Per-field truthiness guards on name / genre_description / mechanical_effect** (Dev's
  "trivial defensive addition", Architect Option A) → ✓ ACCEPTED by Reviewer: agrees with
  Architect. Guarding each interpolation against empty strings is sound defensive
  rendering with no behavioral downside for well-formed pack data (all three fields are
  always populated in `space_opera/classes.yaml`). No spec change needed.
- **`involuntary` flag ignored as a render filter** → ✓ ACCEPTED by Reviewer: matches the
  Architect ruling and AC1 ("extract the first item"). All space_opera abilities are
  `involuntary: false`; taking `abilities[0]` as authored is correct.
- No undocumented deviations found. Implementation matches the DOM contract exactly.

### Architect (reconcile)

Reviewed all prior deviation entries against the shipped implementation at `eda8926`. Both the Dev and Reviewer entries are accurate and substantive — verified independently during spec-check, no corrections needed.

- **No additional deviations found.** The implementation reconciles cleanly with the story context, the ADR-095 intent (exactly one signature ability per non-magical class, surfaced on the player-facing class card), and the DOM contract I authored. All five ACs are DONE; none deferred or descoped, so the AC-deferral cross-check is a no-op.

- **Disposition on Reviewer L1 (empty-box edge) — ACCEPT AS-IS for 71-1; hardening folded into chore 71-8.** The `abilities: [{}]` case (dict present, all three fields empty → an empty `.ref-card__ability` box carrying only the kicker) is the single cosmetic edge surfaced by the Reviewer's Devil's Advocate pass. My ruling: it does **not** block or reopen 71-1, for three reasons. (1) It cannot occur with first-party pack data — ADR-095 guarantees fully-authored abilities, and all five `space_opera/classes.yaml` classes carry populated `name`/`genre_description`/`mechanical_effect`. (2) It is purely cosmetic — no exception, no security exposure (kicker is a static literal), no data loss; worst case is an empty labeled box, not a crash or a silent wrong answer. (3) The contract I authored did not specify behavior for a malformed empty-ability dict, so this is an unspecified edge rather than a deviation from spec. The optional one-line hardening (skip the whole block when all three fields are empty) is a natural companion to the pre-existing pyright:928 cleanup — **both live in `reference_presenters.py` and both are trivial defensive/type touch-ups** — so I recommend folding the L1 hardening into chore **71-8** alongside the pyright fix rather than spending a separate story on it.

**Reconcile verdict:** Reconciles clean. Clear to finish (PR merge + archive).

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/server/reference_presenters.py` — appended signature-ability block to `_class_panel_body()` (guarded on non-empty `abilities` list; renders name, genre_description, mechanical_effect, each independently escaped and guarded)
- `sidequest-server/sidequest/server/static/reference/presenters.css` — added 3 net-new BEM classes (`.ref-card__ability`, `.ref-card__ability-name`, `.ref-card__ability-effect`); reused existing `.ref-card__kicker` + `.ref-card__body`

**Tests:** 39/39 passing (GREEN). Target tests all pass: `test_class_picker_renders_signature_ability`, `test_class_picker_escapes_signature_ability_content`, `test_class_picker_omits_ability_section_when_absent`.
**Lint:** ruff clean on both changed files.
**Typecheck:** No new errors introduced. One pre-existing pyright error remains at line 928 (logged as a delivery finding; in `present_magic`, out of 71-1 scope).
**Branch:** feat/71-1-space-opera-rules-signature-ability (pushed)

**Handoff:** To review phase.

## Subagent Results

Subagent toggles (`workflow.reviewer_subagents`): only `preflight` and `security` enabled;
the other seven are disabled via settings and pre-filled as Skipped.

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings (all pre-existing) | 0 new (story GREEN; 22 fails + 17 errors confirmed pre-existing on develop; pyright :928 pre-existing) | confirmed 0, dismissed 0, deferred 0 (pre-existing items out of scope) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (no swallowed errors in diff) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (tests reviewed below) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (comment block accurate) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (isinstance guards + str coercion) |
| 7 | reviewer-security | Yes | clean | 0 | confirmed 0, dismissed 0, deferred 0 |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — domain self-assessed (no over-engineering) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Rule Compliance section done by Reviewer |

**All received:** Yes (2 enabled subagents returned; 7 disabled via settings, pre-filled as Skipped)
**Total findings:** 0 confirmed blocking, 0 dismissed, 0 deferred. Pre-existing items (full-suite failures, pyright :928) confirmed out of 71-1 scope.

## Reviewer Assessment

**Verdict:** APPROVED

A small, disciplined, well-tested presenter enhancement. Security clean, tests green,
lint/typecheck clean on the new code, CSS reuse honored, and — most importantly for this
shop — the wiring is real and verified end-to-end, not just unit-tested in isolation.

**Dispatched subagent coverage (tags):**
- `[SEC]` reviewer-security (enabled): CLEAN — all three interpolated fields escaped via
  `html.escape()` at `reference_presenters.py:721` (name), `:726` (genre_description),
  `:731` (mechanical_effect). CWE-79 invariant honored; `test_class_picker_escapes_signature_ability_content`
  would catch a regression. Confirmed.
- `[EDGE]` (disabled — self-assessed): Boundary cases handled — `abilities` missing,
  empty list, and non-dict first element all guarded (`isinstance(abilities, list) and abilities`,
  then `isinstance(ability, dict)`). One cosmetic edge noted below (L1).
- `[SILENT]` (disabled — self-assessed): No swallowed errors, no bare except, no silent
  fallback in the diff. The "render nothing when absent" guard is the *specified* behavior
  (magical classes carry no abilities), not a fallback masking a config problem.
- `[TEST]` (disabled — self-assessed): Three new tests with specific value assertions
  (field text, container/name/effect classes, kicker), an ordering assertion
  (`Beat Choices` index < `ref-card__ability` index for AC3), an absence test
  (missing-key AND empty-list), and an escaping test. No vacuous asserts. They drive the
  registered production entry `present_classes_picker`, not `_class_panel_body` in
  isolation — a genuine behavior/wiring test, and NOT a source-text grep (CLAUDE.md
  "No Source-Text Wiring Tests" honored).
- `[DOC]` (disabled — self-assessed): The comment block at `:706-709` is accurate —
  correctly cites ADR-095 and explains the `involuntary`-not-a-filter decision. No stale
  or misleading docs.
- `[TYPE]` (disabled — self-assessed): New code uses `isinstance` narrowing + `str()`
  coercion + `dict.get` with typed defaults; pyright infers it clean. No stringly-typed
  surprises. The lone pyright error (:928) is pre-existing in `present_magic`, out of scope.
- `[SIMPLE]` (disabled — self-assessed): No over-engineering. Reuses `_render_picker`,
  `_picker_chip_strip`, `ref-card__kicker`, `ref-card__body`. The per-field guards add a
  few lines but buy real defensiveness (accepted by Architect). No dead code.
- `[RULE]` (disabled — self-assessed): See Rule Compliance below — exhaustive pass over
  the Python lang-review checklist and project rules.

### Rule Compliance

Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`), every rule
against the changed code:

| # | Rule | Verdict |
|---|------|---------|
| 1 | Silent exception swallowing | PASS — no try/except in diff |
| 2 | Mutable default arguments | PASS — `parts: list[str] = []` is a local, not a default arg; no mutable defaults |
| 3 | Type annotation gaps | PASS — `_class_panel_body(item: dict) -> str` annotated; new code is internal |
| 4 | Logging coverage/correctness | N/A — pure render path, no logging needed |
| 5 | Path handling | N/A — no path ops |
| 6 | Test quality | PASS — specific assertions, ordering check, absence check, escape check; no vacuous asserts, no skips |
| 7 | Resource leaks | N/A — no resources opened |
| 8 | Unsafe deserialization | N/A — no pickle/eval/yaml.load |
| 9 | Async pitfalls | N/A — synchronous |
| 10 | Import hygiene | PASS — no new imports (`escape` already imported at `:14`) |
| 11 | Security / CWE-79 escaping | **PASS (key check)** — all 3 fields escaped (verified + reviewer-security). Kicker is a static literal |
| 12 | Dependency hygiene | N/A — no dependency changes |
| 13 | Fix-introduced regressions | PASS — no broadened catches, no wrong type annotations |
| 14 | State-cleanup ordering | N/A — no one-shot queue/side-effect |

Project rules (`sidequest-server/CLAUDE.md`):
- **No Silent Fallbacks** — PASS. The empty-abilities guard is specified behavior, not a fallback.
- **No Stubbing** — PASS. No stubs/skeletons.
- **Wire Up What Exists** — PASS. Reuses `_render_picker` and existing BEM classes (`ref-card__kicker` `:44`, `ref-card__body` `:59` in presenters.css).
- **Verify Wiring, Not Just Existence** — PASS. `present_classes_picker` registered at `:780`, reachable via `app.py:296` route. Traced end-to-end.
- **Every Test Suite Needs a Wiring Test** — PASS. New tests exercise the registered production entry `present_classes_picker` and assert rendered behavior.
- **No Source-Text Wiring Tests** — PASS. Tests assert on rendered HTML, never grep source.
- **OTEL Observability** — N/A. CLAUDE.md exempts cosmetic/presentation changes; this is pure HTML rendering with no subsystem decision.

### Data flow traced

Pack `classes.yaml` `abilities[0]` → `_class_panel_body(item)` (called by
`present_classes_picker` via `_render_picker`'s `panel_body` callback at `:658`) →
each field `str()`-coerced, `.strip()`-ed, `escape()`- d, interpolated into the
`ref-card__ability` block → returned to `_render_picker` → served by the reference route
(`app.py:296`). Safe: every interpolation is HTML-escaped.

### Devil's Advocate

Trying to break it: **A malicious/garbage pack file.** `abilities: [{}]` (a dict present
but every field empty/missing) slips past both guards and renders
`<div class="ref-card__ability"><div class="ref-card__kicker">Signature Ability</div></div>`
— an empty labeled box (L1 below). `abilities: ["just a string"]` → the
`isinstance(ability, dict)` guard catches it and emits nothing — good. `abilities: [null]`
→ same guard, emits nothing — good. Embedded `<script>` in any field → escaped (tested).
Extremely long mechanical_effect → no truncation, but that's a content-authoring concern,
not a renderer bug, and the CSS box will wrap. **A confused author** who puts the real
ability at `abilities[1]` and a placeholder at `[0]` gets the placeholder rendered — but
that's the specified "first item" contract, and pack authoring is first-party (Jade/Keith),
so it's a content-review issue, not a code defect. **Filesystem/stressed conditions** don't
apply — this is pure in-memory string construction with no I/O. The only thing the devil
turned up is the cosmetic empty-box edge (L1), which cannot occur with the actual
first-party pack data (all five space_opera classes have fully-populated abilities). Nothing
blocking.

### Non-blocking observations

- **[LOW / cosmetic] L1** — `abilities: [{}]` (dict present, all three fields empty)
  renders an empty `.ref-card__ability` box containing only the "Signature Ability" kicker.
  Cannot occur with current first-party pack data (all space_opera classes fully populated).
  Optional hardening: skip the whole block when name/genre_description/mechanical_effect are
  all empty. Not required for approval. Location: `reference_presenters.py:717-736`.
- **[INFO] Wiring test depth** — the three new tests drive `present_classes_picker` (the
  registered production entry), which satisfies the wiring-test requirement for this change.
  The full HTTP route-level integration test (`test_reference_integration.py`) exists but
  ERRORs locally due to a missing `SIDEQUEST_DATABASE_URL` (pre-existing, environmental —
  not a 71-1 concern). The registry→route chain was verified manually during review.

**Pattern observed:** Clean reuse of the shared `_render_picker` + BEM `ref-card__*`
vocabulary at `reference_presenters.py:687-737`; consistent `escape()` discipline matching
every other interpolation in the module.

**Error handling:** Defensive `isinstance` guards on both the list and the first element
(`reference_presenters.py:711,713`); empty-field guards on each interpolation. No exceptions
possible on malformed input — worst case renders nothing or (L1) an empty labeled box.

**Handoff:** To SM (Hawkeye) for finish-story.