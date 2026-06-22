---
story_id: "153-13"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-13: [glenross-seed-quest] Fate chargen drive-assignment sets a real drive, not the vocation label

## Story Details
- **ID:** 153-13
- **Jira Key:** (none — Jira-less story)
- **Workflow:** tdd
- **Type:** bug
- **Points:** 2
- **Priority:** p3
- **Repos:** server, content
- **Branch:** feat/153-13-glenross-seed-quest (both sidequest-server and sidequest-content)

## Context Reference
See sprint/context/context-story-153-13.md for full acceptance criteria and acceptance tests.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T09:00:48Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T08:01:16Z | 2026-06-22T08:04:19Z | 3m 3s |
| red | 2026-06-22T08:04:19Z | 2026-06-22T08:35:22Z | 31m 3s |
| green | 2026-06-22T08:35:22Z | 2026-06-22T08:47:16Z | 11m 54s |
| review | 2026-06-22T08:47:16Z | 2026-06-22T09:00:48Z | 13m 32s |
| finish | 2026-06-22T09:00:48Z | - | - |

## Sm Assessment

**Setup complete — handing to TEA (Fezzik) for the RED phase.**

- **Session + branches:** Session file created; feature branch `feat/153-13-glenross-seed-quest` created off `develop` in BOTH sidequest-server and sidequest-content. Orchestrator unchanged (no branch).
- **Jira:** Skipped — epic-153 is Jira-less (`jira_key: ""`).
- **Context:** Full ACs + technical approach already authored at `sprint/context/context-story-153-13.md`. Five ACs, including a wiring/integration AC (AC-3) that drives the full Fate chargen path through the production seam.

**Story in one line:** On glenross (tea_and_murder, Fate ruleset), Fate chargen sets `character.drive` to the *vocation label* (e.g. "Episcopal Rector") instead of a real aspiration. `quest_seed.py` then faithfully copies it into both `seed_drive.title` and `.objective`, producing a hollow turn-0 quest. The bug is upstream in the Fate chargen drive-assignment, NOT in `quest_seed.py`.

**Guidance for TEA (red phase):**
- Write tests that FAIL against the current behavior. AC-3 is the load-bearing one: drive the **production Fate chargen seam** (not a direct `quest_seed.py` call), create a character, and assert `character.drive != vocation display_name` AND `quest_log["seed_drive"]` is non-degenerate (title/objective not equal to the vocation).
- AC-5 (No silent fallback) is a hard project principle: if no drives list and no player-supplied drive, the system must fail/degrade LOUDLY — never silently echo the calling label. Pin this with a test.
- AC-4 (article agreement, "an Episcopal Rector") is already fixed by server PR #988 (merged); a guard test exercising the `indefinite_article` helper on the vocation slot is sufficient — do not re-implement.
- **Out of scope:** any change to `quest_seed.py` (correct by design, ADR-146 / story 77-2).
- Repos in play: `server` (Fate chargen handler / seam) and `content` (glenross `classes.yaml` may need a `drives:` list per calling if the content path is taken — confirmed absent today).
- OTEL: per project doctrine, the chargen drive-assignment decision should emit a watcher event so the GM panel can verify a real drive was set vs. a label echo — flag for green phase if a span is missing.

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)

**Repro VERIFIED empirically** (2026-06-22, real `tea_and_murder`/glenross content):
walking glenross chargen → `character.drive == ''`, `calling_label == 'Episcopal
Rector'`, `quest_log['seed_drive'] = QuestEntry(title='Episcopal Rector',
objective='Episcopal Rector')`, `active_stakes == 'Episcopal Rector'`. The degenerate
spine is real.

**The fix is CONTENT, not server.** The server is correct and out of scope:
`builder.py` (1591-1610) sets `character.drive` from a "drive-shaped" chargen choice
(touches relationship/goals/emotional_state, NOT class/race); glenross simply ships no
such scene. `quest_seed.py` faithfully copies the drive (ADR-146 / 77-2). Dev's job:
add a real drive surface to glenross `char_creation.yaml` (a `drive` scene à la
space_opera/annees_folles, or a per-calling `drives:` list). See Delivery Findings —
blackthorn_moor has the same gap.

**Test File:** `sidequest-server/tests/server/test_153_13_glenross_fate_drive_seed.py`
(server repo; loads real content, skips cleanly when content absent — same precedent as
`test_chargen_quest_seed_wiring.py`).

**Tests Written:** 5 (2 RED bug tests + 3 GREEN AC-4 regression guards) covering all 5 ACs.

| Test | AC | Seam | State |
|------|----|------|-------|
| `test_chargen_assigns_real_drive_not_vocation_label` | AC-1 | production `CharacterBuilder` on real glenross content | RED (`drive == ''`) |
| `test_commit_seeds_meaningful_quest_not_the_calling` | AC-2 / AC-3 / AC-5 | full websocket `_chargen_confirmation` → `seed_quest_spine` (the wiring/integration test) | RED (`seed_drive.title == calling`) |
| `test_indefinite_article_picks_an_for_vowel_vocation` | AC-4 | `indefinite_article` | GREEN (already fixed) |
| `test_class_slot_renders_an_episcopal_rector` | AC-4 | `substitute_token_with_article` | GREEN (already fixed) |
| `test_sentence_leading_article_stays_capitalized` | AC-4 | `substitute_token_with_article` | GREEN (already fixed) |

### Rule Coverage (Python lang-review)

| Rule | Test(s) | Status |
|------|---------|--------|
| #1 Silent exception swallowing | AC-5 asserts seed span `severity != "warning"` + `seed_drive.title != calling` (no silent calling-label echo) | RED |
| #4 Logging coverage AND correctness | AC-2/5 asserts exactly one `quest.seeded_at_creation` OTEL span with `has_stakes=True` | RED |
| #6 Test quality | All assertions meaningful (value checks, not `is_some`); self-checked for vacuous — none | n/a |
| #13 Fix-introduced regressions (meta) | AC-4 guards + sibling canary (`test_chargen_quest_seed_wiring` + `test_chargen_dispatch` still green) | GREEN |

**Rules checked:** 4 of 13 applicable (the rest — mutable defaults, deserialization,
async pitfalls, etc. — don't apply to a content-driven chargen drive fix).
**Self-check:** 0 vacuous tests.

**Wiring test:** `test_commit_seeds_meaningful_quest_not_the_calling` drives the FULL
production chargen-commit handler (connect → Fate-aware walk → `_chargen_confirmation`),
proving the seed is reachable end-to-end — not just `quest_seed.py` in isolation.

**Verification:** RED confirmed via direct targeted run with proper env
(`SIDEQUEST_GENRE_PACKS` + `SIDEQUEST_DATABASE_URL` against `sidequest_test`). Hermetic
(0 transport reaches; no live LLM call). `testing-runner` skipped deliberately — it does
not set `SIDEQUEST_DATABASE_URL` and clobbers session files (known gotchas); direct
measurement is the stronger evidence here.

**Handoff:** To Dev (Inigo Montoya) for implementation — the GREEN move is content
(glenross + blackthorn_moor drive surface), with the server mechanism left untouched.

## Dev Assessment

**Implementation Complete:** Yes — **content-only fix** (no server code changed).

**The fix:** Added a `drive` choice scene to both tea_and_murder worlds, inserted after
`eye` and before the Fate steps. Each scene's six choices set
`relationship`/`goals`/`emotional_state` WITHOUT class/race hints, so the server's
existing drive-shaped detection (`builder.py` 1591-1610) fires and the chosen choice's
LABEL becomes `character.drive` (then `quest_seed.py` seeds the spine from it). Labels
are mystery-genre motivations re-voiced per world (glenross publican/kirk;
blackthorn_moor landlord/moor).

**Verified outcome** (glenross, Episcopal Rector + first drive):
- `character.drive == 'A Death They Called an Accident'` (was `''`)
- `calling_label == 'Episcopal Rector'` (distinct from the drive)
- `quest_log['seed_drive']` title/objective `== 'A Death They Called an Accident'`
- `active_stakes == 'A Death They Called an Accident'` — a real turn-0 hook.

**Files Changed:**
- `sidequest-content/.../tea_and_murder/worlds/glenross/char_creation.yaml` — new `drive` scene
- `sidequest-content/.../tea_and_murder/worlds/blackthorn_moor/char_creation.yaml` — new `drive` scene (sibling fix)
- `sidequest-server/tests/server/test_153_13_glenross_fate_drive_seed.py` — parametrized builder-seam test over both worlds (TEA's RED tests, extended)

**Tests:** 6/6 passing (GREEN) — builder seam ×2 worlds, handler seam (glenross), AC-4 article guards ×3.
**Pack load:** `load_genre_pack(tea_and_murder)` + `resolve_char_creation_scenes` OK for both worlds (the real content wiring gate).
**Regression:** Targeted batch (all glenross/blackthorn_moor/tea_and_murder tests + chargen seed/dispatch + pack-load canary) = 1245 pass, 1 fail. The 1 fail (`test_watcher_events.py::test_publish_event_shape`) is **pre-existing test-ordering pollution** — it passes in isolation AND fails identically with my content changes STASHED (verified). Not my regression.

**Branches (pushed):**
- server: `feat/153-13-glenross-seed-quest` (commits f5b6a011 RED + d2900e95 GREEN)
- content: `feat/153-13-glenross-seed-quest` (commit 588fa73)

**AC status:** AC-1 ✓ (real drive), AC-2 ✓ (meaningful seed quest), AC-3 ✓ (production handler seam), AC-4 ✓ (article guards green), AC-5 ✓ (player-chosen drive — no silent calling-label fallback).

**Handoff:** To Reviewer (Westley) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (GREEN 6/6, 0 smells, ruff PASS, both worlds load) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (boundary analysis done by Reviewer — see Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | confirmed 2 (both LOW), dismissed 0, deferred 0 |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test-quality done by Reviewer — see Rule Compliance #6) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (content YAML + test; no new types) |
| 7 | reviewer-security | Yes | clean | none | N/A |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (lang-review enumerated by Reviewer — see Rule Compliance) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 2 confirmed (both LOW, non-blocking), 0 dismissed, 0 deferred

## Reviewer Assessment

**Verdict:** APPROVED

**Summary.** A clean, well-scoped content fix. glenross + blackthorn_moor shipped no
`drive` chargen scene, so Fate chargen left `character.drive` empty and `quest_seed.py`
fell back to the calling label, seeding a degenerate turn-0 quest. The fix adds a
`drive` choice scene (six mystery-genre motivations) to both worlds, matching the
server's existing drive-shaped detection and the established space_opera/annees_folles
pattern. No server/engine code changed. I independently verified the fix end-to-end and
hunted hard for the failure modes; the one suspicious path (freeform-typed drive)
resolved as **intended, documented behavior**.

**Observations (8):**
- `[VERIFIED]` The fix works end-to-end: picking the drive scene sets `character.drive='A Death They Called an Accident'`, distinct from `calling_label='Episcopal Rector'`, and `quest_log['seed_drive']` title/objective + `active_stakes` all carry the real drive — evidence: my own build-and-seed run on real glenross content.
- `[VERIFIED]` All 12 drive choices (6 × 2 worlds) are correctly drive-shaped — each sets `relationship`/`goals`/`emotional_state` and NONE leaks `class_hint`/`race_hint`/`mutation_hint`/`rig_type_hint`. Evidence: enumerated every choice's `mechanical_effects` via the loader. This is the load-bearing correctness property (a leaked class/race hint would re-break the drive for that choice).
- `[VERIFIED]` `jungian_hint` values (caregiver/sage/rebel/…) are inert and safe — tea_and_murder defines no jungian archetypes and `resolved_archetype` stays `None` (no `rpg_role_hint` is set), so they cause zero behavioral change. `jungian_hint` is a free `str | None` (character.py:134), no fail-loud. Evidence: builder.py:3381-3382 requires BOTH hints; only `jungian_hint` is set.
- `[SILENT]` `_build_pc` test helper uses `except Exception` around `apply_auto_advance()` then falls back to `apply_freeform` (test_153_13_…:143). Confirmed LOW: test-only helper, the defensive branch is not exercised by either world's walk (the only non-choice/non-fate scene, `the_satchel`, auto-advances cleanly), and it matches the established `tests/integration/test_126_24_annees_folles_chargen_seed.py::_walk_capturing_seed` idiom. Recommend (non-blocking) narrowing to `except InvalidChoiceError`.
- `[SILENT]` Hermetic fake feeds the sidecar `structured_output_stream({})`, so the test wouldn't catch a dead sidecar (test_153_13_…:247). Confirmed LOW: the sidecar is an out-of-scope incidental subsystem (glenross auto-narrates on commit); the story's AC assertions check the pre-sidecar quest-seed path and are correct. Non-blocking.
- `[TEST]` (subagent disabled — Reviewer did this) Test quality is sound: every assertion checks a specific value (no `assert True`/truthy-only/vacuous), the parametrization covers two distinct content files (not the same code path), `monkeypatch` targets `llm_factory.query` where it is USED, and skips carry reasons. The handler-seam test is a genuine end-to-end wiring test.
- `[SEC]` Security subagent: clean. Authored YAML prose carries no injection payload; the `_pg_isolation` TRUNCATE uses pg_catalog names (not user input); the test is hermetic (no live call). Confirmed.
- `[RULE]` (subagent disabled — Reviewer enumerated) Python lang-review: all 13 checks pass on the one `.py` file (see Rule Compliance). No mutable defaults, no resource leaks, no unsafe deserialization, pathlib used, imports clean.

**Tags with no findings:** `[EDGE]` — edge-hunter disabled; I performed the boundary analysis myself (the freeform-drive path — see Devil's Advocate — VERIFIED intended). `[DOC]` — comment-analyzer disabled; the new content/test docstrings are accurate. `[TYPE]` — type-design disabled; no new types (content YAML + test). `[SIMPLE]` — simplifier disabled; the content is appropriately minimal (one scene per world; blackthorn_moor is a flavor reskin with identical mechanical_effects, which is the intended per-world pattern).

**Data flow traced:** drive choice `label` → `acc.backstory_label` (builder.py:1609, drive-shaped detection) → `character.drive` (builder.py:3507) → `quest_seed.seed_quest_spine` → `quest_log['seed_drive']` + `active_stakes`. Verified empirically: a real drive flows the whole way; the prior empty-drive→calling-fallback is closed for the pick path.

**Pattern observed:** Mirrors the canonical drive scene at `space_opera/worlds/aureate_span/char_creation.yaml` (choices set relationship/goals/emotional_state/jungian_hint, `allows_freeform: true`). Correct reuse, not reinvention.

**Error handling:** No new error paths in production (content-only). The loader fails loud on malformed content; both worlds load clean. `quest_seed.py`'s loud-degrade path (empty source → warning span) is unchanged and now unreached for these worlds on the pick path.

### Rule Compliance (Python lang-review — all 13, enumerated)

| # | Check | Verdict |
|---|-------|---------|
| 1 | Silent exception swallowing | PASS w/ note — one `except Exception` in a test helper (LOW, non-user-controlled, matches annees_folles precedent); recommend narrowing |
| 2 | Mutable default arguments | PASS — defaults are `str`/`None` only |
| 3 | Type annotation gaps at boundaries | PASS — test methods annotated `-> None`; internal helpers exempt |
| 4 | Logging coverage AND correctness | PASS — N/A (test); the seeded path's OTEL span is asserted |
| 5 | Path handling | PASS — `pathlib.Path` via genre_paths helper |
| 6 | Test quality | PASS — meaningful assertions, correct mock target, parametrization covers two content files, skips have reasons |
| 7 | Resource leaks | PASS — `with psycopg.connect(...)` context manager |
| 8 | Unsafe deserialization | PASS — no pickle/eval; content via the safe production loader |
| 9 | Async/await pitfalls | PASS — `asyncio.run`; coroutines awaited; no blocking-in-async |
| 10 | Import hygiene | PASS — explicit imports, no star/circular |
| 11 | Input validation at boundaries | PASS — N/A (no user-input handler added) |
| 12 | Dependency hygiene | PASS — no new deps |
| 13 | Fix-introduced regressions | PASS — content additive-only; pick path fixed, nothing made worse |

**SOUL.md / content rules:** "No Silent Fallbacks" ✓ (pick path sets a real drive; freeform box is honestly labeled flavor per Keith's ruling). "Crunch in Genre, Flavor in World" ✓ (the drive surface is world content; engine unchanged). "Diamonds and Coal" ✓ (six weighted, genre-true motivations for a core chargen choice — appropriate detail). Cliché check (no cliche-judge ran): the drive labels are specific cosy-mystery hooks, not generic — acceptable for a 40-year-GM audience.

**Tenant isolation:** N/A — no multi-tenant data, no structs/trait methods, no tenant_id fields in the diff (content YAML + one test).

### Devil's Advocate

I tried hard to break this. The strongest attack: the drive scene carries `allows_freeform: true`, so the UI renders a free-text box. I verified empirically that a *freeform-typed* drive ("To avenge my murdered sister") is NOT captured into `character.drive` (it comes out `''`) — because the drive-shaped detection keys on a *choice's* `mechanical_effects`, and a freeform answer has none. On its face this looked like a HIGH: a player types their motivation, it vanishes, `quest_seed` falls back to the calling label — the exact bug this story exists to kill, re-created on a realistic, natural path, contradicting AC-5 ("must NOT silently use the calling label"). The fix would have been a one-line content change (drop `allows_freeform`).

But verifying against design intent reversed it. `sidequest-ui/.../CharacterCreation.freeform-flavor.test.tsx` encodes **Keith's explicit 2026-06-17 ruling**: on a *choice* scene, the free-text box is *additive narrative flavor that intentionally does NOT change the sheet* — never a Fate aspect, item, skill, or (by the same logic) the mechanical drive. The UI honestly captions it "colors the story, not your sheet" and softens the placeholder to "add a detail in your own words." So the freeform box does not over-claim, and a typed drive becoming prose-color-not-drive is *intended, documented behavior* — not a silent fallback. The mechanical drive is set by the pick; the box is honest flavor. My new drive scene is a choice scene with `allows_freeform`, falling squarely under this ruling, and matches the live, playtested space_opera/annees_folles pattern verbatim. The change introduces no regression: pre-fix, 100% of glenross PCs got the degenerate quest; post-fix, pick-path PCs get a real drive and the freeform box behaves exactly as Keith specified. Second attack — an unrecognized `jungian_hint` poisoning archetype resolution — also failed: tea_and_murder has no jungian set and `resolved_archetype` stays `None`. Third — a leaked class/race hint making a choice non-drive-shaped — failed: I enumerated all 12 choices, all clean. Verdict stands: APPROVED.

**Handoff:** To SM (Vizzini) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): This is fundamentally a CONTENT fix — glenross ships NO drive
  chargen scene, so `character.drive` is left empty and the spine seeds from the
  calling. The server mechanism (`builder.py` drive-shaped detection 1591-1610) and
  `quest_seed.py` are CORRECT and out of scope. Affects
  `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/char_creation.yaml`
  (add a real `drive` scene whose choices set relationship/goals/emotional_state
  WITHOUT class/race hints — the space_opera / annees_folles pattern; OR a per-calling
  `drives:` list the handler draws from). *Found by TEA during test design.*
- **Gap** (non-blocking): The sibling world
  `tea_and_murder/worlds/blackthorn_moor/char_creation.yaml` has the SAME missing-drive
  gap (per the content investigation). Fixing only glenross leaves blackthorn_moor's
  spine degenerate. Affects that world's `char_creation.yaml`. *Found by TEA during
  test design.*
- **Improvement** (non-blocking): `quest_seed.py`'s fallback from `drive` to
  `calling_label` is the mechanism that MASKS a missing drive on every Fate pack — it
  seeds with `severity="info"` as if a real drive existed. Out of scope here, but a
  follow-up could make the seed warn loudly when it seeds from the calling rather than a
  drive. Affects `sidequest/game/quest_seed.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): The other three Fate genres should be spot-checked for the
  same missing-drive gap. pulp_noir/annees_folles HAS a drive scene (verified via 126-24);
  the remaining Fate worlds (spaghetti_western, wry_whimsy) were not audited here. Affects
  each Fate world's `char_creation.yaml`. *Found by Dev during implementation.*
- TEA's blackthorn_moor finding (above) was RESOLVED in this change, not deferred — see the
  Dev deviation below. *Noted by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): The `_build_pc` test helper's `except Exception` around
  `apply_auto_advance()` should narrow to `except InvalidChoiceError` so a real
  `WrongPhaseError` (builder FSM corruption) surfaces loudly instead of being swallowed and
  re-surfacing later as a confusing "did not reach confirmation". Test-only; matches the
  existing annees_folles idiom, so LOW. Affects `sidequest-server/tests/server/test_153_13_glenross_fate_drive_seed.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The handler-seam test cannot detect a dead sidecar (the
  empty-`SidecarExtraction` fake is indistinguishable from a real empty result). The sidecar
  is out of scope here, but a future sidecar-focused test could assert no
  `sidecar_extraction.failed` span fired. Affects the same test file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Freeform-typed drives on a choice scene are intentionally
  flavor-only (Keith 2026-06-17). If a future story wants typed drives to be mechanically
  honored (Zork-problem affordance), that is an ENGINE change in `builder.py`'s freeform
  handling for drive-shaped scenes — and would fix space_opera/annees_folles/glenross/blackthorn_moor
  at once. Out of scope for 153-13. Affects `sidequest-server/sidequest/game/builder.py`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Root-cause refinement — drive is EMPTY, not set-to-vocation**
  - Spec source: context-story-153-13.md, "Repro / Evidence → Root cause (board)"
  - Spec text: "Fate chargen assigned the vocation/calling label to `character.drive` during the chargen walk; quest_seed.py faithfully copied it."
  - Implementation: Measured the real path (2026-06-22). `character.drive == ""` (glenross authors no drive scene → builder.py's drive-shaped detection never fires); `quest_seed.py` then FALLS BACK to `calling_label`. Tests assert the observable outcome (drive empty / `seed_drive.title == calling_label`), not the board's stated assignment mechanism.
  - Rationale: The board's mechanism is inaccurate; the outcome and fix direction (glenross needs a real drive surface) are unchanged. Pinning the true mechanism keeps Dev from hunting a nonexistent "drive = vocation" assignment to delete.
  - Severity: minor
  - Forward impact: Dev fix is a content drive surface, not a server assignment change.
- **AC-4 coverage is GREEN regression guards, not RED**
  - Spec source: context-story-153-13.md, AC-4
  - Spec text: "already fixed by PR #988; a guard test ensuring the `indefinite_article` helper is exercised on the vocation slot is sufficient."
  - Implementation: Wrote 3 PASSING guard tests (`TestVocationArticleAgreement`) on `indefinite_article` / `substitute_token_with_article`. They are green because the fix already merged.
  - Rationale: AC-4 explicitly asks for a regression guard on already-merged work; a RED test is inappropriate.
  - Severity: minor
  - Forward impact: none.
- **Handler-seam test fakes the sidecar SDK transport**
  - Spec source: context-story-153-13.md, AC-3
  - Spec text: "drives the full Fate chargen path ... through the production chargen seam (not by calling quest_seed.py directly)"
  - Implementation: The handler-seam test drives the real websocket `_chargen_confirmation`; glenross auto-narrates its opening on commit (caverns/flickering_reach does not), which runs the post-narration sidecar extractor — the one collaborator NOT covered by conftest's `build_async_anthropic` stub. Installed a hermetic `FakeQuery(structured_output_stream({}))` (empty, schema-valid `SidecarExtraction`) so the test makes NO live call and emits no transport noise.
  - Rationale: Faithful to the full production seam without a live LLM call; matches the codebase's FakeQuery convention. An empty extraction is valid (every `SidecarExtraction` field defaults).
  - Severity: minor
  - Forward impact: none (test-only). If Dev takes the free-text drive-STEP path instead of a content drive scene, the walk helpers (which send the player name at freeform scenes) must supply a real drive string at the drive step.

### Dev (implementation)
- **Scope extended to the sibling world blackthorn_moor**
  - Spec source: session title "[glenross-seed-quest]" + TEA Delivery Finding (blackthorn_moor, non-blocking)
  - Spec text: Story scoped to glenross; TEA finding: "The sibling world blackthorn_moor has the SAME missing-drive gap ... Fixing only glenross leaves blackthorn_moor's spine degenerate."
  - Implementation: Added the `drive` scene to BOTH `glenross` and `blackthorn_moor` `char_creation.yaml`, and parametrized the builder-seam test over both worlds.
  - Rationale: Identical bug, identical one-scene fix; leaving blackthorn_moor's hollow turn-0 quest is exactly the "no half-wired features" the project forbids — a player on blackthorn_moor hits the same degenerate spine. Cheaper and safer to fix both now.
  - Severity: minor
  - Forward impact: none — blackthorn_moor's seed is now meaningful; no sibling story depends on its prior (broken) state.
- **Fix is content-only; the chargen drive surface chosen is a `drive` choice scene (not a per-calling `drives:` list)**
  - Spec source: context-story-153-13.md, "Fix Direction" (two options)
  - Spec text: "Content path (preferred): Supply a `drives:` list per calling ... OR a `drive` chargen step."
  - Implementation: Added a `drive` choice scene (six motivations) à la space_opera/annees_folles, NOT a per-calling `drives:` list. Server code + `quest_seed.py` untouched.
  - Rationale: The `drive` scene reuses the server's existing drive-shaped detection (builder.py 1591-1610) with zero engine change and gives the player explicit agency over their motivation (also AC-5's loud non-fallback: the choice IS the drive). A per-calling list would couple drives to vocations and need a handler draw the engine doesn't have.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA — Root-cause refinement (drive EMPTY, not set-to-vocation)** → ✓ ACCEPTED by Reviewer: independently confirmed by build-and-seed on real content (drive was `''`, quest_seed fell back to calling). The refinement is correct and load-bearing.
- **TEA — AC-4 coverage is GREEN regression guards, not RED** → ✓ ACCEPTED by Reviewer: AC-4 explicitly asks for a guard on already-merged PR #988; green guards are the right artifact.
- **TEA — Handler-seam test fakes the sidecar SDK transport** → ✓ ACCEPTED by Reviewer: the fake is hermetic (no live call), the empty `SidecarExtraction` is schema-valid, and it silences an incidental out-of-scope subsystem without weakening any AC assertion.
- **Dev — Scope extended to blackthorn_moor** → ✓ ACCEPTED by Reviewer: correct application of "no half-wired features" — identical gap, identical fix, now guarded by the parametrized test. Verified both worlds load + assign a real drive.
- **Dev — Content-only fix via a `drive` choice scene (not per-calling `drives:`)** → ✓ ACCEPTED by Reviewer: reuses the server's existing drive-shaped detection with zero engine change, matches the live space_opera/annees_folles pattern, and preserves player agency over the drive.
- **Freeform drive on a choice scene does not set `character.drive`** → Reviewer-found, RESOLVED as intended: per Keith's 2026-06-17 ruling (encoded in `sidequest-ui/.../CharacterCreation.freeform-flavor.test.tsx`), free-text on a choice scene is honestly-labeled additive flavor ("colors the story, not your sheet"), never a mechanical field. NOT a deviation — the new drive scene conforms to the ruled pattern. No action required.