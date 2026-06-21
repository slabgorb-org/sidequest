---
story_id: "153-15"
jira_key: ""
epic: "153"
workflow: "trivial"
---
# Story 153-15: [SWN-CHARGEN-RECAP-GRAMMAR] map background label to a noun form and drop the from-race-space stitch

## Story Details
- **ID:** 153-15
- **Jira Key:** (none — Jira not configured for this project)
- **Workflow:** trivial
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Repos:** server
**Branch:** feat/153-15-swn-chargen-recap-grammar-noun-form
**Phase Started:** 2026-06-21T23:00:10Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T22:17:10Z | 2026-06-21T22:22:42Z | 5m 32s |
| implement | 2026-06-21T22:22:42Z | 2026-06-21T22:51:56Z | 29m 14s |
| review | 2026-06-21T22:51:56Z | 2026-06-21T23:00:10Z | 8m 14s |
| finish | 2026-06-21T23:00:10Z | - | - |

## Sm Assessment

**Setup complete.** Story 153-15 is a 1-point trivial chore in `sidequest-server` — a chargen confirmation-recap grammar fix in the SWN (Without Number) flow. Two asks: (1) render the background label in a noun form (mirror the existing `race_label`/`class_label` display handling), and (2) drop the "from {race} space" sentence stitch that reads badly.

**Technical approach:** Localize to `sidequest/server/dispatch/chargen_summary.py` (recap-sentence stitch + background-label rendering; `render_confirmation_summary`, `_add(...)` projection, `background_display`/`backstory_label` handling ~lines 254/378–382, humanize/title-case helpers ~lines 95–126). Reference `sidequest/game/builder.py` for how `background_label`/`race_label`/`freeform_race_label` accumulate (defs ~361/427, assignment ~1535–1560). Add a targeted unit test asserting the recap renders the background label in noun form and no longer contains the "from {race} space" stitch.

**Acceptance criteria:**
- AC-1: Chargen confirmation recap renders the background label in noun form (not raw/adjectival).
- AC-2: The "from {race} space" stitch is removed from the recap sentence.
- AC-3: A unit test covers both the noun-form rendering and the absence of the from-race-space stitch.
- AC-4: No silent fallbacks; existing chargen-summary tests still pass.

**OTEL:** Not required — this is a cosmetic prose/grammar refinement (per the OTEL "not needed for cosmetic changes" carve-out). No subsystem decision changes.

**Full story context:** `sprint/context/context-story-153-15.md`.

**Handoff:** To implement (Dev — Naomi Nagata).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Conflict** (non-blocking): Story tagged `repos: server`, but the `from {race} space` recap stitch is authored CONTENT — the actual fix is 3 `char_creation.yaml` edits in sidequest-content. Affects `sprint/epic-153.yaml` (153-15 `repos:` is effectively `server,content`) and the finish ceremony — a content PR (`feat/153-15-swn-recap-race-class-noun`) must merge alongside the server test PR. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `interpolate_scene_narration` supports no `{background}` placeholder (only `{name}`/`{class}`/`{race}`/`{high_concept}`); origin demonyms ride `{race}` (race_hint). If a future recap wants the adjectival `background` (Void-born) or the origin display label as a noun, that placeholder would need adding in `sidequest/game/builder.py`. Not needed for this fix. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): Freeform-origin edge — the `origins` scene is `allows_freeform: true`, and when a player free-types an origin, `race_hint` stays empty, so the new recap `The {race} {class}` renders "The  Pilot" (double space). Affects `sidequest/game/builder.py::substitute_token_with_article` (empty-value branch does a plain replace, no whitespace collapse) or the content templates. PRE-EXISTING and *milder* than the old "The Pilot from  space" (this fix improves it), and observable via the `chargen.scene_narration_interpolated` warn path — not silent. A future whitespace-collapse pass would tidy it. *Found by Reviewer during code review.*
- The Dev cross-repo scope finding is accurate and actionable: SM must merge `sidequest-content` branch `feat/153-15-swn-recap-race-class-noun` alongside the server branch at finish. *Confirmed by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Fix landed in sidequest-content (3 files) + a server test, not chargen_summary.py**
  - Rationale: CLAUDE.md "Never say the right fix is X and then do Y" — the stitch lives in content; a server-only edit cannot remove it. Recap wording ("The {race} {class}") confirmed with Keith via AskUserQuestion (2026-06-21).
  - Severity: minor
  - Forward impact: minor — SM must include `sidequest-content` (branch `feat/153-15-swn-recap-race-class-noun`) in the finish/merge alongside the server branch.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Fix landed in sidequest-content (3 files) + a server test, not chargen_summary.py**
  - Spec source: session Sm Assessment / context-story-153-15.md (Technical approach), `repos: server`
  - Spec text: "Localize to `sidequest/server/dispatch/chargen_summary.py` … render the background label in a noun form … drop the 'from {race} space' sentence stitch."
  - Implementation: The `from {race} space` stitch is authored CONTENT — the `confirmation` scene `narration` in 3 space_opera world `char_creation.yaml` files (aureate_span / coyote_star / perseus_cloud), interpolated by `builder.py::interpolate_scene_narration`. `chargen_summary.py` renders the FIELD preview card (`Race: …`), NOT this prose. Fixed the recap in content ("The {class} from {race} space" → "The {race} {class}"); added the regression test in the SERVER suite (`tests/genre/`), the only repo with a Python harness that loads content.
  - Rationale: CLAUDE.md "Never say the right fix is X and then do Y" — the stitch lives in content; a server-only edit cannot remove it. Recap wording ("The {race} {class}") confirmed with Keith via AskUserQuestion (2026-06-21).
  - Severity: minor
  - Forward impact: minor — SM must include `sidequest-content` (branch `feat/153-15-swn-recap-race-class-noun`) in the finish/merge alongside the server branch.

### Reviewer (audit)
- **Dev deviation "Fix landed in sidequest-content (3 files) + a server test, not chargen_summary.py"** → ✓ ACCEPTED by Reviewer: Correct call, verified independently. The `from {race} space` stitch exists ONLY in the three worlds' `char_creation.yaml` confirmation narration — `chargen_summary.py` renders the field preview card and never carries this prose. A server-only edit could not have removed it. Wording change was confirmed with Keith. CLAUDE.md "do X, not Y" upheld. No UNDOCUMENTED deviations: the diff matches the logged scope exactly (3 content recap reorders + 1 server regression test, no other files touched).

## Dev Assessment

**Implementation Complete:** Yes

**Root finding:** The SWN chargen "recap" is the `confirmation`-scene narration (content), not `chargen_summary.py` (which renders the field preview card). The recap read `{name}. The {class} from {race} space.`; `{race}` resolves to `race_hint` — a demonym (Spacer/Coreworlder/Colonial/Uplifted) — so it rendered "The Pilot from Spacer space", a redundant ungrammatical stitch.

**Fix:** Reorder origin to a noun before the calling and drop the "from … space" scaffold → `The {race} {class}` ("The Spacer Pilot"). Applied to all three SWN worlds. Wording confirmed with Keith.

**Files Changed:**
- `sidequest-content/genre_packs/space_opera/worlds/aureate_span/char_creation.yaml` — confirmation recap reorder
- `sidequest-content/genre_packs/space_opera/worlds/coyote_star/char_creation.yaml` — confirmation recap reorder
- `sidequest-content/genre_packs/space_opera/worlds/perseus_cloud/char_creation.yaml` — confirmation recap reorder
- `sidequest-server/tests/genre/test_153_15_swn_recap_race_class_noun.py` — NEW regression test (content guard over the 3 worlds via GenreLoader + render-wiring through `interpolate_scene_narration`)

**OTEL:** None (cosmetic prose; OTEL carve-out for cosmetic changes). `interpolate_scene_narration` already emits `chargen.scene_narration_interpolated` and unchanged by this fix.

**Tests:** 153-15 scope GREEN — 7 new tests pass; 100 related chargen tests (builder name-extraction, builder scene-message, axis-pack chargen, chargen_summary) pass; ruff clean. Full server suite: 13,824 passed / 345 skipped, 7 failures all confirmed pre-existing & unrelated (5 = story 153-34 WN pointbuy `rules.yaml` migration; 2 = xdist isolation flakes that pass in isolation — `test_intent_router_confrontation_classified`, `test_watcher_events`). RUN_ID 153-15-dev-green.

**Branches (pushed):**
- content: `feat/153-15-swn-recap-race-class-noun` → origin (slabgorb-org/sidequest-content)
- server: `feat/153-15-swn-chargen-recap-grammar-noun-form` → origin (slabgorb-org/sidequest-server)

**Handoff:** To review (Reviewer — Chrisjen Avasarala). Note the cross-repo scope: review both the content recap edits and the server regression test.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 7/7 pass, ruff lint+format clean, no smells |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 1 (non-blocking Low), dismissed 3 |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — all docstrings/comments verified accurate |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (self-assessed below) |
| 9 | reviewer-rule-checker | Yes | clean | none | N/A — 0 violations / 17 rules |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 confirmed (non-blocking Low), 3 dismissed (with rationale), 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

A one-point content-prose fix: the SWN confirmation recap's `from {race} space` stitch (which rendered the demonym redundantly, "The Pilot from Spacer space") is reordered to `The {race} {class}` ("The Spacer Pilot") across the three SWN worlds, guarded by a new server regression test. The fix is correct, the test is genuinely end-to-end, and there are no Critical/High issues.

### Subagent dispatch tags
- **[TEST]** (test-analyzer, 4 findings) — **1 confirmed, non-blocking Low:** the render-wiring test drives only `aureate_span` through the production `interpolate_scene_narration`; `coyote_star`/`perseus_cloud` are exercised only by the content-guard parametrized tests. Non-blocking because the interpolation engine is world-agnostic and all three worlds are content-guarded for the identical `The {race} {class}` pattern, so the per-world render is equivalent by construction. **3 dismissed:** (a) "no ordering assertion / second negative is weaker" — dismissed: `assert "{race} {class}" in narration` already guarantees race-immediately-precedes-class (a stronger ordering check than the suggested `index()` comparison), and the bare `from {race}` guard is deliberate belt-and-suspenders against partial reverts (the inline comment documents this). (b) "merge the two parametrized tests / loader called 6×" — dismissed: the two tests document distinct properties (stitch-absent vs order-correct) and loader cost is negligible (preflight: 3.06s for all 7). (c) "assert a second prose fragment in the render test" — dismissed: the analyzer itself concluded the empty-render risk is already covered (an empty narration fails the `"The Spacer Pilot"` assertion).
- **[DOC]** (comment-analyzer) — clean. Module docstring + inline comments verified accurate against live content and production code (incl. the `substitute_token_with_article` leaves "The" untouched claim).
- **[RULE]** (rule-checker) — clean. 0 violations across 17 rules, including project rules "No Silent Fallbacks", "No Stubbing", "No Source-Text Wiring Tests" (asserting on loader-loaded YAML is data/behavior testing, allowed), and "Every Test Suite Needs a Wiring Test" (satisfied by the interpolate render test).
- **[EDGE]** disabled — self-assessed: the only edge is a freeform origin (empty `race_hint`) → "The  Pilot" (double space); pre-existing, milder than the old "The Pilot from  space", observable via the `chargen.scene_narration_interpolated` warn path. Logged as a non-blocking Improvement finding. Canned origins always set `race_hint`.
- **[SILENT]** disabled — self-assessed (corroborated by rule-checker #1/#14): `_confirmation_narration` uses `next(...)` with no default (fails loud on a missing `confirmation` scene); `GenreLoader.load` and `pack.worlds[slug]` fail loud. No swallowed errors, no silent fallback.
- **[TYPE]** disabled — self-assessed (corroborated by rule-checker #3): every function is fully annotated (`-> str` / `-> None` / `-> CharacterBuilder`); no new types, no stringly-typed production API (content change is YAML prose).
- **[SEC]** disabled — self-assessed (corroborated by rule-checker #11): no user input, no SQL/HTML/path/deserialization surface; a test module + static content prose.
- **[SIMPLE]** disabled — self-assessed: production change is minimal (3 × one-line YAML); test has minor redundancy (test-analyzer findings a/b, dismissed). No over-engineering.

### Rule Compliance
- **SOUL.md "Genre Truth" / "Diamonds and Coal":** the recap stays genre-true space opera and reads cleanly ("The Spacer Pilot. … it's going to be your story."). The `coyote_star`/`perseus_cloud` "for whatever those words mean…" tails keep their referent (the origin demonym is still present). Compliant.
- **SOUL.md "The Test" (player doing something they didn't ask):** N/A — the recap describes the character the player just built; it imposes no action. Compliant.
- **CLAUDE.md OTEL Observability Principle:** cosmetic-prose carve-out applies; no subsystem decision changed. `interpolate_scene_narration` already emits `chargen.scene_narration_interpolated` and is unchanged. Compliant.
- **CLAUDE.md "No Silent Fallbacks":** verified at `_confirmation_narration` (no `next()` default) and the loader path. Compliant.
- **CLAUDE.md "Every Test Suite Needs a Wiring Test" / "No Source-Text Wiring Tests":** the render test drives real production interpolation; content guards assert on loader-loaded data, not grepped source. Compliant.
- **Python lang-review (13 checks):** all pass (rule-checker exhaustive).

### Observations
- `[VERIFIED]` Fix correctness — `aureate_span/char_creation.yaml:226` now `{name}. The {race} {class}.`; with `{race}`→race_hint (Spacer) and `{class}`→class_hint (Pilot), and `substitute_token_with_article` leaving the definite "The" untouched (builder.py:913-923), it renders exactly "The Spacer Pilot". Complies with SOUL Genre Truth.
- `[VERIFIED]` Stitch removed in all three worlds — content diff shows `from {race} space` deleted in aureate_span, coyote_star, perseus_cloud; loader-backed test confirms `"from {race} space" not in narration` for each.
- `[VERIFIED]` Wiring test is real — `test_real_aureate_span_recap_renders_spacer_pilot` loads the shipped recap via `GenreLoader`, builds a real `CharacterBuilder`, applies real choices, and calls production `interpolate_scene_narration`; not mocked (rule-checker #17, comment-analyzer corroborate).
- `[LOW][TEST]` Render-wiring covers only `aureate_span` end-to-end — other two worlds content-guarded + shared engine; non-blocking improvement.
- `[LOW][EDGE]` Freeform origin → empty `race_hint` → "The  Pilot" double space — pre-existing, improved by this fix, observable; non-blocking.
- `[VERIFIED]` No production code path changed — only content prose + a test; OTEL carve-out correctly invoked.

### Data flow traced
Player selects origin choice (`mechanical_effects.race_hint=Spacer`) and crucible choice (`class_hint=Pilot`) → `CharacterBuilder` accumulates `race_hint`/`class_hint` → at the confirmation phase, `interpolate_scene_narration` substitutes `{race}`→race_hint, `{class}`→(class_label or class_hint) into the world's confirmation `narration` → the player reads "The Spacer Pilot." Safe: empty-slot resolution is observable (warn span), and the definite article is not mangled.

### Devil's Advocate
Argue this is broken. First attack: the recap is `allows_freeform: false` at confirmation but the *origins* scene that feeds `{race}` is `allows_freeform: true`. A player who free-types "I grew up on a generation ship" never sets `race_hint` — it routes to `freeform_race_label`, which fills `race_label`/`background_label` but NOT `race_hint`. Since `{race}` deliberately resolves to `race_hint` (builder.py:1691), the recap renders "The  Pilot" with a doubled space, or for coyote_star "The  Pilot — for whatever those words mean here", which now dangles. Is that a regression this fix introduced? No — the *old* template "The {class} from {race} space" rendered "The Pilot from  space" in the exact same freeform case, which is strictly worse (a dangling preposition + noun). So the fix improves the degenerate case rather than creating it, and the empty slot is already flagged at `severity=warn` in `chargen.scene_narration_interpolated`. Second attack: could `{class}` be empty (no crucible choice)? Then "The Spacer " trails a space — again pre-existing and warn-flagged, not introduced here. Third attack: does the test lie? Could `interpolate_scene_narration` return the input unchanged and still pass? No — if the loader read the wrong field or an empty string, "{race}"/"{class}" would be absent and "The Spacer Pilot" would NOT appear, failing the assertion; the test fails closed. Fourth attack: a confused author copies the recap to a fourth SWN world with the old phrasing — the parametrized content guard only covers the three named worlds (`SWN_WORLDS`), so a future world could regress unguarded. That's a real but acceptable limitation for a targeted fix; the content-guard list is explicit and a new world is a deliberate add. None of these rise to Critical/High; the worst case is a doubled space in a freeform edge that the fix already improves.

**Data flow traced:** origin/crucible choices → builder accumulator → `interpolate_scene_narration` → confirmation recap "The Spacer Pilot" (safe; empty slots warn, article preserved).
**Pattern observed:** content-guard-via-real-loader + render-wiring-via-production-engine at `tests/genre/test_153_15_swn_recap_race_class_noun.py` — correct pattern for content-prose regressions (sidequest-content has no Python harness).
**Error handling:** `_confirmation_narration` fails loud (`next()` no default); empty interpolation slots emit a warn span, not silent.
**Handoff:** To SM (Camina Drummer) for finish-story — merge BOTH branches (content `feat/153-15-swn-recap-race-class-noun` + server `feat/153-15-swn-chargen-recap-grammar-noun-form`).