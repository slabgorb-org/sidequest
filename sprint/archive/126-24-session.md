---
story_id: "126-24"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-24: [FATE/CHARGEN] Narrative chargen seeds the Fate pyramid + aspects as editable defaults (genre translation table + world overrides)

## Story Details
- **ID:** 126-24
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Repos:** content,server,ui
**Phase Started:** 2026-06-19T15:39:32Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T14:10:50Z | 2026-06-19T14:13:20Z | 2m 30s |
| red | 2026-06-19T14:13:20Z | 2026-06-19T14:41:35Z | 28m 15s |
| green | 2026-06-19T14:41:35Z | 2026-06-19T15:01:31Z | 19m 56s |
| review | 2026-06-19T15:01:31Z | 2026-06-19T15:13:30Z | 11m 59s |
| red | 2026-06-19T15:13:30Z | 2026-06-19T15:20:57Z | 7m 27s |
| green | 2026-06-19T15:20:57Z | 2026-06-19T15:30:22Z | 9m 25s |
| review | 2026-06-19T15:30:22Z | 2026-06-19T15:39:32Z | 9m 10s |
| finish | 2026-06-19T15:39:32Z | - | - |

## Sm Assessment

**Setup verdict (Themis the Just, 2026-06-19):** Story is well-scoped and ready for the red phase. The scales find no impediment.

**What this story is.** Narrative chargen (pulp_noir/annees_folles, Fate Core / ADR-144) collects rich answers — Origin=The Service, Signature=I Find Things Out, Connection=A Ghost, Drive=Answers — then **discards them at the Fate steps**: `fate_aspects` renders empty placeholders and `fate_pyramid` is fully blank, forcing the player to hand-rank all 10 skills. The friendly on-ramp bait-and-switches to a blank Fate sheet. Keith flagged this in play (sq-playtest-pingpong 2026-06-19, [GAP]).

**Design decision is fixed (Keith, 2026-06-19) — do not re-litigate.** A **genre-tier translation table WITH world overrides**: base narrative-hint → Fate skill+aspect-seed map lives in `pulp_noir` genre config (skills like Investigate/Shoot are genre rulebook per ADR-140); worlds (annees_folles) may override/extend per-hint via ADR-121 layered per-field resolution. Per-choice `fate_*_seed` blocks were **rejected** (duplicative, staples crunch onto the world-flavor on-ramp). The seed is **always an editable default** — override always allowed; preserve the existing no-silent-default behavior for High Concept / Trouble.

**Root cause is validated across all three repos** (from the playtest forensics):
- **content** `genre_packs/pulp_noir/char_creation.yaml`: narrative steps emit NATIVE-model `mechanical_effects` (class_hint, background, rpg_role_hint, jungian_hint, etc.); Fate steps are a parallel `choices:[]` + `fate_chargen_step:` track that never consumes the earlier hints. Fix = new genre-tier seed table (+ optional annees_folles override).
- **server** `websocket_handlers/chargen_mixin.py`: `_chargen_fate_aspects_confirm` / `_chargen_fate_pyramid_confirm` only RECORD the submitted payload. The native hints ARE accumulated (`acc.class_hint` etc.) but never consumed into a Fate seed at present-time. `game/ruleset/fate_chargen.py` (`validate_fate_sheet` / `pyramid_violations`) is the single legality authority — route the seed through it. Fix = present-time seed computation.
- **ui** `CharacterCreation/FateChargenPanel.tsx`: **the seam already exists** — `FateSkillPyramidPanel` inits local state from `currentAllocation`; `FateAspectsPanel` slots carry `value` (pre-fill, editable) + `suggestion` (placeholder). Server only has to SEND a seeded `currentAllocation` + `slot.value`. Expected verify-only, but TEA/Dev must confirm end-to-end (no regression to no-silent-default for HC/Trouble).

**Routing & flags for TEA (Argus Panoptes):**
- 5-pt phased TDD, three repos (content, server, ui) — all branched to `feat/126-24-narrative-chargen-fate-seed` (subrepos on develop; orchestrator on main).
- No Jira key — YAML-only story; Jira claim correctly skipped.
- This does **NOT** block 150-1 mechanical AC verification (per story note).
- Doctrine guardrail: this is a Fate-binding story. **Bind the ruleset, don't balance it** — the seed maps narrative hints onto the *bound* Fate pyramid/aspects; do not reintroduce or tune native mechanics to "make it fit."

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev) — verified via `testing-runner`, server run serially (`-n0`) per the OTEL-deadlock gotcha.

**Test Files:**
- `sidequest-server/tests/game/ruleset/test_126_24_narrative_chargen_fate_seed.py` — the core unit suite, synthetic `FateConfig` fixtures driven through the REAL `CharacterBuilder` (mirrors `test_121_7`). Covers AC1, AC2, AC3, AC4, AC5, AC6, AC8, AC9.
- `sidequest-server/tests/integration/test_126_24_annees_folles_chargen_seed.py` — the AC7 marquee e2e repro: loads the REAL pulp_noir pack, walks `annees_folles` narrative chargen accepting the seed, asserts no-blank-sheet + gear lands. Skips if content not on disk.
- `sidequest-ui/src/components/CharacterCreation/__tests__/CharacterCreation.fate-seed.test.tsx` — AC7 UI **wiring guards** (the seam already exists; these are GREEN and pin the contract).

**Tests Written:** 19 (14 server unit, 3 server integration, 5 UI wiring guards — 22 functions; counts overlap ACs).

**RED verification (the right reasons):**
- Unit file → collection `ImportError: cannot import name 'resolve_fate_chargen_seed_table'` + `FateHintSeed` — the pinned contract Dev must satisfy first.
- Integration file → `BLANK pyramid ({})`, `EMPTY aspect slots ([])`, and `FateChargenError: illegal sheet` on the real pack — reproduces the forensic bug (save `2026-06-19-annees_folles-cd25d503`) end-to-end.
- UI file → 5/5 GREEN — proves the renderer needs no change; only the server must SEND the seed (AC7).

### PINNED PUBLIC CONTRACT (Dev implements to these names)

Mirrors the 121-7 precedent (pin the API in the test docstring + here). Where a choice was forced, see Design Deviations.

1. `sidequest.genre.models.rules.FateHintSeed` — pydantic model: `pyramid: dict[str,int]` (a COMPLETE legal allocation for the pack's `chargen_pyramid`) + `aspects: list[str]` (free-aspect text seeds).
2. `FateConfig.chargen_seed_table: dict[str, FateHintSeed]` — genre-tier, keyed by the narrative-hint VALUE (e.g. `"Detective"`). Loader-injected/world-merged exactly like `gear_catalog`. `extra="forbid"` means the field must be added before fixtures construct.
3. `sidequest.game.ruleset.fate_chargen.resolve_fate_chargen_seed_table(pack, world_slug) -> dict[str, FateHintSeed]` — mirrors `resolve_fate_gear_catalog`: union genre + world `chargen_seed_table`, world wins per hint key; emits a merge span carrying `world_override_applied`.
4. `CharacterBuilder._fate_step_payload` seeds present-time: a `fate_pyramid` step with no player allocation yet sets `payload.fate_current_allocation` (legal) from `self.accumulated()` hints via `cfg.chargen_seed_table`; a `fate_aspects` step seeds the FREE-aspect slots' `value`. **HC/Trouble `value` stay empty** (no-silent-default — placeholder only).
5. Seed is an editable default — a player allocation/aspect always overrides; HC/Trouble keep the non-empty-on-confirm invariant.
6. Span `fate.chargen.seed_applied` (register in `SPAN_ROUTES`, emit via `Span.open` so the documented `spans.tracer` monkeypatch captures it) — attrs `hint`, `skill_count`, `aspect_count`. Paired-negative: no match → no span.
7. New `{high_concept}` token in `CharacterBuilder.interpolate_scene_narration` resolving to the recorded Fate HC (AC8) — lets the `confirmation` step prose drop `{race} {class}`. Companion CONTENT change: `pulp_noir/char_creation.yaml` confirmation narration uses `{high_concept}` instead of `a {race} {class}`.
8. Narrative-wizard build path compiles `cfg.gear` (via `cfg.gear_catalog`) onto the sheet through the EXISTING `compile_gear_onto_sheet` (AC9) — aspects carry `source_gear`.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (CLAUDE.md / py #1) | `test_unmatched_hint_leaves_allocation_blank`, `test_empty_high_concept_still_rejected_after_seeding` | failing (unit ImportError) |
| OTEL lie-detector (CLAUDE.md OTEL principle) | `test_present_pyramid_emits_seed_applied_span`, `test_seed_applied_span_carries_hint_and_counts`, `test_unmatched_hint_emits_no_seed_applied_span` (paired negative) | failing |
| No Source-Text Wiring Tests (CLAUDE.md) | integration walk + OTEL spans + UI render assertions — zero `read_text()`/source-grep | satisfied by construction |
| Every Suite Needs a Wiring Test (CLAUDE.md) | `test_126_24_annees_folles_chargen_seed.py` (real-pack e2e) + UI render wiring guards | failing (server) / green (UI) |
| Test quality — meaningful assertions (py #6) | self-checked: no `assert True`, no bare-truthy; every test asserts a value/shape | satisfied |
| Bind the Ruleset, Don't Balance It (SOUL) | seed maps onto the BOUND Fate pyramid/aspects; no native-mechanic reintroduction in any test | satisfied by design |

**Rules checked:** 6 of the applicable CLAUDE.md/SOUL + python lang-review rules have test coverage or are satisfied by construction.
**Self-check:** 0 vacuous tests (reviewed every assertion; the no-match guards assert concrete `== {}` / span-absence, not truthiness).

### TEA Rework — round 1 (post-Reviewer REJECT, 2026-06-19)

**Reviewer blocker addressed:** the world-override (AC2) was half-wired and the original AC2 unit test (`_FakeWorld` injecting pre-built `FateHintSeed`) masked it. New RED file pins the REAL path that fakes cannot mask:
- `sidequest-server/tests/genre/test_126_24_world_seed_table_load.py` (4 tests, RED) — mirrors the 126-25 world-gear precedent (`test_126_25_world_gear_load.py`):
  1. `test_world_model_has_chargen_seed_table_field` — `World` must grow a typed `chargen_seed_table: dict[str, FateHintSeed]` field (fixes the raw-dict crash via pydantic coercion).
  2. `test_loader_populates_world_chargen_seed_table_as_fate_hint_seed` — the loader populates `World.chargen_seed_table` from `worlds/<slug>/chargen_seed_table.yaml`, COERCED to `FateHintSeed` (`.pyramid`/`.aspects` are real attributes).
  3. `test_loader_absent_world_seed_table_is_empty` — absence → `{}` (No Silent Fallbacks).
  4. `test_resolve_returns_world_override_from_loaded_world` — end-to-end: a loaded world override reaches `resolve_fate_chargen_seed_table` (world wins) with `.pyramid` accessible — the Reviewer's core demand, via the real loader, not `_FakeWorld`.

**RED verified** (testing-runner, `-n0`): new file 4/4 fail for the intended reasons (no `World.chargen_seed_table` field; `AttributeError` on access; resolver returns `{}`). Existing 19 tests (unit + integration) stay GREEN — purely additive.

**PINNED CONTRACT for Dev (rework):**
- Add `World.chargen_seed_table: dict[str, FateHintSeed] = Field(default_factory=dict)` to `sidequest/genre/models/pack.py` (mirror `World.gear: list[GearDef]` at pack.py:294).
- Loader (`_assemble_world`, loader.py:~1859): populate it from `worlds/<slug>/chargen_seed_table.yaml`, unconditional of ruleset (mirror `gear=world_gear` / `_load_gear`). A typed parse fails loud on malformed content (also closes the edge/security raw-dict robustness finding).
- The existing `resolve_fate_chargen_seed_table` + builder-attach already consume it — no change needed there once `World` carries the typed field.

**Note:** the original `_FakePack`/`_FakeWorld` AC2 unit tests in `test_126_24_narrative_chargen_fate_seed.py` stay (they test the merge LOGIC in isolation, still valid); the new loader file is the honest real-path complement the Reviewer required.

**Handoff:** To Dev (Hephaestus the Smith) for GREEN — the typed `World` field + loader population.

**Handoff:** To Dev (Hephaestus the Smith) for GREEN. Implementation order suggestion: (1) add `FateHintSeed` + `FateConfig.chargen_seed_table` (unblocks unit collection), (2) `resolve_fate_chargen_seed_table` + loader injection, (3) builder present-time seed + `fate.chargen.seed_applied` span, (4) `{high_concept}` token, (5) narrative-wizard gear compile, (6) CONTENT: author `pulp_noir/rules.yaml` `fate.chargen_seed_table` (+ optional annees_folles override) and rewrite the confirmation narration.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 64/64 passing across the touched Fate-chargen suites (GREEN), incl. the real-pack integration walk; UI 18/18; routing/loader 90/90. Verified via `testing-runner` (server `-n0` per the OTEL-deadlock gotcha).

**Files Changed:**
- **server** `sidequest/genre/models/rules.py` — `FateHintSeed` model + `FateConfig.chargen_seed_table` field (pinned contract #1, #2).
- **server** `sidequest/game/ruleset/fate_chargen.py` — `select_chargen_seed` (table-keyed, class_hint > rpg_role_hint > background, returns None on no match), `resolve_fate_chargen_seed_table` (genre∪world, world wins per hint key) + `_emit_fate_seed_table_merged` watcher event with `world_override_applied` (#3, AC2/AC6).
- **server** `sidequest/game/builder.py` — present-time seed in `_fate_step_payload` (pyramid `fate_current_allocation` + free-aspect `value`, legal, editable default; `fate.chargen.seed_applied` span on apply, paired-negative on no match); `_fate_aspect_slots(seed_aspects=...)`; `apply_fate_aspects` now fails loud on empty HC/Trouble (AC5 no-silent-default at the builder tier); `with_fate_seed_table` attach; `{high_concept}` token in `interpolate_scene_narration` (#4, #7, AC8).
- **server** `sidequest/telemetry/spans/fate.py` — `fate_chargen_seed_applied_span` + `SPAN_ROUTES["fate.chargen.seed_applied"]` (#6).
- **server** `sidequest/game/ruleset/fate.py` — `apply_fate_chargen` (narrative-wizard path) now compiles `cfg.gear` via `compile_gear_onto_sheet`, mirroring the Menu path (#8, AC9).
- **server** `sidequest/handlers/connect.py` — wires `resolve_fate_chargen_seed_table` (world-first) → `with_fate_seed_table` at chargen builder construction (the non-test consumer — no dead code; no shared-pack mutation).
- **content** `genre_packs/pulp_noir/rules.yaml` — `fate.chargen_seed_table` with a complete legal pyramid + aspect seeds for every crucible `class_hint` (Detective/Brawler/Grifter/Soldier of Fortune/Scholar/Smuggler/Performer).
- **content** `genre_packs/pulp_noir/char_creation.yaml` — confirmation narration uses `{high_concept}` instead of `a {race} {class}`.
- **ui** — no change required: the seam already consumes `fate_current_allocation` + slot `value` (the 5 wiring guards stay GREEN, AC7).

**AC coverage:** AC1 ✓ (seed maps hints→legal pyramid+aspects), AC2 ✓ (world override resolver + unit test), AC3 ✓ (present-time seed in the scene message), AC4 ✓ (seeded pyramid passes `pyramid_violations`), AC5 ✓ (editable default; HC/Trouble no-silent-default loud), AC6 ✓ (`seed_applied` + merge spans), AC7 ✓ (real-pack e2e repro retired; UI renders with no code change), AC8 ✓ (`{high_concept}` token + content rewrite), AC9 ✓ (narrative-wizard gear compile; real sheet carries `source_gear`).

**Branches (pushed):**
- `feat/126-24-narrative-chargen-fate-seed` — sidequest-server (`7f75886`), sidequest-content (`24cdb7e`), sidequest-ui (`f4e7f15`, red-phase wiring guards).

**Handoff:** To Reviewer (Hermes Psychopompos) for code review.

### Dev Rework — round 1 (Reviewer REJECT fix, 2026-06-19)

**Blocker fixed:** world-tier `chargen_seed_table` override (AC2) is now wired end-to-end, mirroring the 126-25 world-gear precedent exactly:
- `sidequest/genre/models/pack.py` — added typed `World.chargen_seed_table: dict[str, FateHintSeed] = Field(default_factory=dict)` (after `World.gear`). Typed → pydantic coerces authored YAML dicts to `FateHintSeed`, so `.pyramid`/`.aspects` are real attributes (fixes the raw-dict `AttributeError` the security/edge specialists flagged).
- `sidequest/genre/loader.py` — added `_load_chargen_seed_table` (mirrors `_load_gear`; fails loud on a non-dict file) + `_assemble_world` now loads `worlds/<slug>/chargen_seed_table.yaml` and passes `chargen_seed_table=world_chargen_seed_table` to `World(...)`, unconditional of ruleset (mirrors `gear=world_gear`).
- No change needed to `resolve_fate_chargen_seed_table` / `with_fate_seed_table` / the builder — they already consume `World.chargen_seed_table`; the missing piece was the typed field + loader source.

**Tests:** rework file `tests/genre/test_126_24_world_seed_table_load.py` 4/4 GREEN; existing 126-24 unit (16) + integration (3) GREEN; the 126-25 world-gear precedent (10) GREEN (no regression). Broader `tests/genre/` = 1054 passed, 8 pre-existing WWN-content failures (documented in memory `wwn_content_breaks_server_fixtures` — unrelated to this change). Verified via `testing-runner` (`-n0`).

**Non-blocking Reviewer findings (round 1) — status:** the typed-field + loud loader parse also closes the edge/security raw-dict robustness concern. The remaining non-blocking findings ({high_concept} sanitize defense-in-depth, OTEL world_hints spoiler note, empty-aspects span, back-nav asymmetry, illegal-authored-seed validator) remain as Delivery Findings for follow-up (not in this story's scope).

**Branches (pushed):** server `feat/126-24-narrative-chargen-fate-seed` @ `51cf0fb` (rework test `ab487c2` + fix `51cf0fb`); content `24cdb7e`, ui `f4e7f15` unchanged.

**Handoff:** To Reviewer (Hermes Psychopompos) for re-review.

## Subagent Results — Round 1 (REJECTED, superseded by Round 2 below)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A (95 tests GREEN, lint pass, pulp_noir pack validates 0 errors) |
| 2 | reviewer-edge-hunter | Yes | findings | 7 | confirmed 5 (1 folds into the HIGH blocker), dismissed 1, deferred 5 as LOW |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — self-assessed: the seed path fails loud (build-time validate raises on illegal sheet; apply_fate_aspects raises on empty HC/Trouble; select_chargen_seed returns None on no match, never fabricates). No swallowed errors found. |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed: assertions are meaningful, BUT the AC2 world-override unit test is VACUOUS-for-the-real-path (injects pre-built `FateHintSeed` via `_FakeWorld`, never exercises the loader→raw-value path). This is the test half of the HIGH blocker. |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — self-assessed: docstrings/comments accurate and rich; no stale comments introduced. |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — self-assessed: `FateHintSeed` is a proper pydantic model (not stringly-typed); `chargen_seed_table` typed on `FateConfig`. **BUT** `World` lacks a typed `chargen_seed_table` field → the world-override values are never coerced to `FateHintSeed` (the HIGH blocker). |
| 7 | reviewer-security | Yes | findings | 3 | confirmed 3 (1 HIGH blocker, 1 MEDIUM non-blocking, 1 LOW non-blocking) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — self-assessed: implementation mirrors existing precedents (resolve_fate_gear_catalog, the with_* attach pattern, the Menu-path gear compile); no over-engineering. The double seed_applied span (aspects + pyramid present) is intentional, not redundant. |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — self-assessed against CLAUDE.md/SOUL.md (see Rule Compliance below). The "No half-wired features" rule is VIOLATED by the world-override loader gap (the HIGH blocker). |

**All received:** Yes (3 enabled subagents returned; 6 disabled via settings, self-assessed)
**Total findings:** 1 confirmed HIGH (blocking), 1 MEDIUM (non-blocking), 6 LOW (non-blocking/deferred), 1 dismissed (with rationale)

## Rule Compliance

Enumerated against CLAUDE.md / SOUL.md (no `.claude/rules/*.md` present):

- **No Silent Fallbacks** (CLAUDE.md/SOUL): `select_chargen_seed` returns `None` on no hint match (builder presents blank, never fabricates) — COMPLIANT (`fate_chargen.py:select_chargen_seed`). `apply_fate_aspects` raises on empty HC/Trouble — COMPLIANT (`builder.py`). `compile_gear_onto_sheet` raises `GearCompileError` on unknown gear id before mutation — COMPLIANT (pre-existing).
- **No half-wired features — connect the full pipeline or don't start** (CLAUDE.md): **VIOLATED.** The world-tier seed override (AC2) is wired on the resolve + connect.py + UI-consume side but NOT on the loader side — `World` has no `chargen_seed_table` field and `_assemble_world` never populates one, so `resolve_fate_chargen_seed_table` always sees `{}` for the world tier. A content author cannot actually author a world override. This is the canonical "ship 3 of 5 connections" failure. → HIGH blocker.
- **Verify Wiring, Not Just Existence / Every Test Suite Needs a Wiring Test** (CLAUDE.md): the genre-tier path IS wired end-to-end and integration-tested (real pulp_noir pack walk). The world-tier path's only "test" is the `_FakeWorld` unit test that bypasses the loader → the wiring is unverified and, as built, non-functional. → part of the HIGH blocker.
- **OTEL Observability Principle** (CLAUDE.md): `fate.chargen.seed_applied` (present-time) + the seed-table merge watcher event (`world_override_applied`) + the existing `fate.gear_compiled` on the narrative-wizard gear path — every new subsystem decision emits a span. COMPLIANT (`telemetry/spans/fate.py`, `fate_chargen.py:_emit_fate_seed_table_merged`). Minor gap: the aspects-step span doesn't fire for a seed with empty aspects (LOW).
- **Bind the Ruleset, Don't Balance It** (SOUL): the seed maps narrative hints onto the BOUND Fate pyramid/aspects; legality is the SRD pyramid shape via `pyramid_violations`; no native mechanic reintroduced or tuned. COMPLIANT.
- **Crunch in the Genre, Flavor in the World / ADR-140** (SOUL): the genre authors the base seed table (rulebook); the world layers per-hint overrides (flavor). Design is correct — but the world half is non-functional (see blocker).
- **No content in unit tests** (project memory): content existence covered by the real-pack integration test + pack validator, not pytest. COMPLIANT.

## Devil's Advocate

Argue this code is broken. The headline: **the marquee differentiator of this story — world-specific seed overrides — does not work at all.** The story is built explicitly for Jade, named in CLAUDE.md as the first non-Keith content author, whose load-bearing requirement is "anyone can add worlds, packs, rules, and lore as content without touching engine code." The moment Jade opens `worlds/perseus_cloud/` (or annees_folles) and authors a `chargen_seed_table` override the way the AC promises, one of two things happens: nothing (the loader never reads it into `World`, so `resolve_fate_chargen_seed_table` returns `{}` and her override is silently ignored — a Silent Fallback in spirit), or, if some YAML key leaks into `World`'s `extra="allow"` bag as a raw dict, `seed.pyramid` raises `AttributeError` and her players' character creation crashes unrecoverably. Either way she "touched content" and the engine failed her — the exact failure mode CLAUDE.md says is a failure of the content surface.

A confused author would be doubly misled: the AC2 unit test is GREEN, the resolver function exists, `connect.py` calls it, the UI consumes it — every surface SAYS world overrides work. Only the loader connection is missing, and nothing fails loudly to say so. This is the worst kind of half-wired: it looks done.

What about a malicious/clumsy author? A world `chargen_seed_table` with a misspelled skill or wrong rung counts is presented to the player as an illegal pre-filled pyramid (`fate_legal=False`) rather than caught at pack load — no validator guards authored seeds (TEA/Dev already filed this as a follow-up, correctly). A player-authored High Concept containing prompt-injection text now flows into the confirmation prose via `{high_concept}`; React escapes it for the UI (no XSS) and ADR-047 sanitizes at the narrator boundary, so it's defended — but the new interpolation site adds an unsanitized substitution path that should, defense-in-depth, route through `sanitize_player_text`.

The genre-tier core of the story is sound and well-tested. But a story whose own AC2 ships non-functional, with a test that proves the wrong thing, must go back.

## Prior Review — Round 1 (REJECTED, superseded by the Round 2 Reviewer Assessment below)

**Round-1 verdict:** REJECTED (fixed in rework — see the Round 2 Reviewer Assessment below)

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | World-tier seed override (AC2) is half-wired and non-functional: `resolve_fate_chargen_seed_table` reads `getattr(world, "chargen_seed_table", {})`, but `World` has no such field and the loader (`_assemble_world`) never populates one — so the world tier is always `{}`; a real world cannot override. (If a value WERE captured via `World`'s `extra="allow"`, it would be a raw `dict`, not a `FateHintSeed`, and `seed.pyramid`/`.aspects` access would crash chargen with `AttributeError`.) The AC2 unit test masks this by injecting pre-built `FateHintSeed` via `_FakeWorld`, never exercising the loader→typed-coercion path. | `sidequest-server/sidequest/genre/models/pack.py` (World model), `sidequest/genre/loader.py:~1859` (`_assemble_world`), `sidequest/game/ruleset/fate_chargen.py:resolve_fate_chargen_seed_table`; test `tests/game/ruleset/test_126_24_narrative_chargen_fate_seed.py::TestAC2WorldOverride` | Add a TYPED `chargen_seed_table: dict[str, FateHintSeed] = Field(default_factory=dict)` field to `World` (mirror `gear: list[GearDef]` at pack.py:294) and populate it in the loader from world content (mirror `gear=world_gear` at loader.py:1887), so pydantic coerces world YAML → `FateHintSeed` (fixes both the no-source gap AND the raw-dict crash). TEA: replace/augment the AC2 test to exercise the REAL loaded-world path (a `World` built from raw YAML-shaped data, or an integration fixture world that authors an override), so a raw-dict regression fails loud. |

**Non-blocking findings** (do NOT block; recorded as Delivery Findings for follow-up):
- [MEDIUM] `{high_concept}` interpolation substitutes player-authored HC into confirmation prose without an explicit `sanitize_player_text` call. UI is React-escaped (no XSS) and the narrator boundary sanitizes per ADR-047, so no live vuln — but the new substitution site should route through `protocol/sanitize.py` for defense-in-depth. (`builder.py:interpolate_scene_narration`)
- [LOW] `_emit_fate_seed_table_merged` emits `world_hints` (authored vocation key names) to the unfiltered `/ws/watcher` broadcast — a future spoiler-bearing hint key could surface before a player encounters it. (`fate_chargen.py:_emit_fate_seed_table_merged`)
- [LOW] aspects-step `seed_applied` span does not fire for a seed with an empty `aspects` list (pyramid span fires, aspects span doesn't) — a GM-panel lie-detector gap for empty-aspect seeds. Consider emitting unconditionally on match with `aspect_count=0`. (`builder.py:_fate_step_payload`)
- [LOW] back-nav re-seed asymmetry (pyramid suppresses seed once submitted; aspects re-seeds while `_fate_free_aspects` is empty) — acceptable per "editable default" design, but undocumented. (`builder.py:_fate_step_payload`)
- [LOW] illegal AUTHORED seed (bad world override) is presented to the player as an illegal pre-fill rather than caught at pack load — fails loud at build, but a pack-load validator would be better (already filed by TEA/Dev). (`builder.py`, `cli/validate/`)

**Dismissed:**
- [edge #4] "validate_fate_sheet runs before gear compile → gear character-aspects can exceed free_aspect_count uncounted" — DISMISSED: this mirrors the shipped Menu path (`seed_chargen_resources`, 114-10) and produces the CORRECT runtime result (gear aspects are meant to be additive beyond the free-aspect budget); re-validating post-gear as suggested would wrongly REJECT a legitimate player+gear sheet. Not a 126-24 regression; if anything `validate_fate_sheet` should exclude `source_gear` aspects from the count — a separate pre-existing concern.

**Data flow traced:** narrative choice → `accumulated().class_hint` → `select_chargen_seed(seed_table, ...)` → `_fate_step_payload` seeds `fate_current_allocation` + free-aspect `value` → UI renders editable → player confirm → handler `pyramid_violations` re-validate → `apply_fate_pyramid` → `build()` → `validate_fate_sheet` (legality authority) → gear compile. The genre-tier flow is safe and verified by the real-pack integration test; the world-tier branch of this flow is the broken link.

**Handoff:** Back to TEA (Argus Panoptes) for red rework — the fix is testable (loader wiring + typed coercion + a real-path AC2 test).

## Subagent Results

(Round 2 — re-review of the rework delta: 2 server files + 1 test addressing the Round-1 HIGH blocker.)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 33/33 targeted GREEN (rework file 4/4), lint clean, pulp_noir assembles; the 4 loader-suite failures reproduce identically on develop (confirmed not regressions) |
| 2 | reviewer-edge-hunter | Yes | findings | 2 | blocker confirmed RESOLVED; 2 residual edges both LOW/MEDIUM, non-blocking, mirror the `_load_gear` precedent → deferred as Delivery Findings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled — self-assessed: `_load_chargen_seed_table` fails loud (non-dict → GenreLoadError; bad entry → ValidationError); absent → `{}` is the documented gear-parity contract, not a swallow. |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled — self-assessed: the Round-1 masking is fixed — the new `test_126_24_world_seed_table_load.py` exercises the REAL loader→coercion path (model field, loader population, resolve end-to-end), not `_FakeWorld`. |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled — self-assessed: new docstrings on `World.chargen_seed_table` + `_load_chargen_seed_table` are accurate and mirror the gear precedent's wording. |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — self-assessed: the typed `dict[str, FateHintSeed]` field IS the fix — pydantic coercion eliminates the raw-dict path the Round-1 blocker rode. Confirmed by security + edge specialists. |
| 7 | reviewer-security | Yes | clean | none | round-1 raw-dict-crash blocker CLOSED; safe_load + pydantic; no new surface |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — self-assessed: `_load_chargen_seed_table` mirrors `_load_gear`; the now-redundant `getattr(..., {})` in the resolver is harmless (protects `model_construct`'d Worlds) — no change warranted. |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — self-assessed: the "No half-wired features" rule that drove the Round-1 REJECT is now SATISFIED (typed field + loader source + end-to-end test). |

**All received:** Yes (3 enabled returned clean/resolved; 6 disabled via settings, self-assessed)
**Total findings:** 0 blocking; 2 LOW/MEDIUM non-blocking (deferred); Round-1 HIGH blocker CONFIRMED RESOLVED.

## Rule Compliance — Round 2

- **No half-wired features** (the Round-1 blocker): now COMPLIANT. `World.chargen_seed_table` is a typed field (`pack.py`), `_assemble_world` populates it from `worlds/<slug>/chargen_seed_table.yaml` (`loader.py`), and `resolve_fate_chargen_seed_table` + `with_fate_seed_table` + the builder consume it — proven end-to-end by `test_126_24_world_seed_table_load.py::test_resolve_returns_world_override_from_loaded_world`. The full pipeline is connected.
- **No Silent Fallbacks**: COMPLIANT. Malformed world file → `GenreLoadError` (non-dict) / pydantic `ValidationError` (bad entry); absent → `{}` (documented gear-parity contract). Genre table never silently substitutes for a malformed world override.
- **Verify Wiring, Not Just Existence**: COMPLIANT. The new test loads a real `World` via the real loader and asserts the override reaches the resolver as a `FateHintSeed` (`.pyramid` accessible) — the exact path the Round-1 `_FakeWorld` test bypassed.
- **Unsafe deserialization** (CLAUDE.md py #8): COMPLIANT. `yaml.safe_load` via `_load_yaml_raw_optional`; pydantic `model_validate` with `extra="forbid"`; no `yaml.load`/`eval`/`exec`.
- **Type design**: COMPLIANT. `dict[str, FateHintSeed]` (not stringly-typed / not the `extra` bag) — the typed field is the structural fix.

## Devil's Advocate — Round 2

Argue the fix is still broken. The most plausible attack: a content author (Jade) writes `worlds/perseus_cloud/chargen_seed_table.yaml` with a subtle error — a hint value of `null`, or a pyramid rating as a string `"4"`, or a stray top-level scalar. Does the loader fail loud and helpfully? It fails loud (the edge-hunter confirmed: non-dict top-level → `GenreLoadError` with path; bad entry → pydantic `ValidationError`; non-int rating → "Input should be a valid integer"). The one gap: a malformed *entry* (e.g. `Detective: null`) raises a `ValidationError` that names the field but not the file path or the hint key `Detective` — a debugging-ergonomics shortfall, NOT a silent failure (it still crashes the load loudly). And it mirrors the shipped `_load_gear` exactly, so it's consistent, not a regression. I filed it as a non-blocking Delivery Finding to improve both helpers together.

Could a `model_construct`'d World (used in sibling tests) now blow up because the field is "required"? No — `Field(default_factory=dict)` means the default applies even under `model_construct`, and the resolver's `getattr(..., {})` is a redundant second guard; the edge-hunter verified `World.model_construct(gear=[]).chargen_seed_table == {}` at runtime, and the 126-25 world-gear tests (which use `model_construct`) stay GREEN. Could the new field corrupt pack loading for the 21 other worlds that author no override? No — absent file → `{}`, and preflight confirmed pulp_noir + the loader suite assemble with no new failures. Could an over-powered world seed grant a free mechanical advantage? No — the load path carries no legality check by design; the builder's present-time `pyramid_violations` and `validate_fate_sheet` at build are the gates, unchanged. The fix is whole; the residue is ergonomic, not correctness.

## Reviewer Assessment

**Verdict:** APPROVED

**Round-1 blocker — RESOLVED:** the world-tier `chargen_seed_table` override is now wired end-to-end (typed `World.chargen_seed_table` field + `_load_chargen_seed_table` loader population from `worlds/<slug>/chargen_seed_table.yaml`, mirroring the 126-25 world-gear precedent). Confirmed by all three enabled specialists (preflight GREEN, security CLEAN/blocker-closed, edge-hunter blocker-resolved) and the new real-path test `test_126_24_world_seed_table_load.py` (4/4 GREEN). The raw-dict crash path is eliminated by pydantic coercion at the typed field.

**Specialist findings incorporated:**
- `[SEC]` reviewer-security — CLEAN: the round-1 raw-dict-crash blocker is CLOSED (typed `dict[str, FateHintSeed]` + `FateHintSeed.model_validate` per entry); `yaml.safe_load` + pydantic, no `eval`/`yaml.load`; no new info-leakage or injection surface. No security findings.
- `[EDGE]` reviewer-edge-hunter — blocker RESOLVED; 2 residual edges, both LOW/MEDIUM and both mirroring the shipped `_load_gear` sibling (malformed-entry error lacks file/hint context; present-but-empty file → `{}` like absent) → confirmed, deferred as non-blocking Delivery Findings.

**Data flow traced:** `worlds/<slug>/chargen_seed_table.yaml` → `_load_chargen_seed_table` (safe_load + `FateHintSeed.model_validate`, fail-loud) → `World.chargen_seed_table` (typed, coerced) → `resolve_fate_chargen_seed_table(pack, world_slug)` (genre ∪ world, world wins) → `with_fate_seed_table` → builder `_fate_step_payload` seeds the editable-default pyramid/aspects → player confirm → `pyramid_violations` / `validate_fate_sheet` legality gates. Safe end-to-end; the previously-broken world-tier link is now closed.

**Pattern observed:** the fix correctly reuses the established world-tier-content pattern (`_load_gear`→`World.gear`, `with_classes`/`with_equipment_tables` attach) rather than inventing a new mechanism — `loader.py:_load_chargen_seed_table` / `pack.py:World.chargen_seed_table`.

**Error handling:** malformed world file fails loud (`loader.py` non-dict guard → `GenreLoadError`; pydantic per-entry); absent → `{}` (gear-parity contract).

**Non-blocking findings** (recorded as Delivery Findings; do NOT block — all pre-existing-pattern or out-of-scope): (1) loader error message for a malformed `chargen_seed_table.yaml` entry lacks file-path/hint-key context (mirrors `_load_gear`; improve both together); (2) present-but-empty world file → `{}` like absent (gear-parity); plus the carried Round-1 non-blockers ({high_concept} sanitize defense-in-depth, OTEL `world_hints` spoiler note, empty-aspects span, illegal-authored-seed pack-load validator, sibling Fate-pack seed tables + confirmation-narration audit).

**Handoff:** To SM (Themis the Just) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): the content-existence invariants (pulp_noir ships a `fate.chargen_seed_table` covering its `class_hint` values; the `fate.gear` list resolves) are NOT unit-tested — per project rule, content invariants belong in the pack validator, not pytest. They are covered functionally by the real-pack integration test. Consider a `cli/validate/fate_gear.py`-adjacent check that a fate pack with narrative chargen declares a seed-table entry for every `class_hint` its `char_creation.yaml` emits (No Silent Fallbacks — fail loud on an unseeded vocation). Affects `sidequest-server/sidequest/cli/validate/` + `sidequest-content/genre_packs/pulp_noir/`. *Found by TEA during test design.*
- **Question** (non-blocking): AC8's exact surface — the bug "a Military I Find Things Out" is the `char_creation.yaml` `confirmation`-step NARRATION (`a {race} {class}`), NOT the structured summary card (`render_confirmation_summary` already routes to a Fate view when `fate_choices()` is recorded). I pinned the fix as a new `{high_concept}` interpolation token + a content narration rewrite; Dev should confirm this is the intended surface vs. a pure content edit. Affects `sidequest-server/.../builder.py::interpolate_scene_narration` + `sidequest-content/genre_packs/pulp_noir/char_creation.yaml`. *Found by TEA during test design.*
- **Gap** (blocking, rework round 1): the world-override path (AC2) needs a typed `World.chargen_seed_table` field + loader population from `worlds/<slug>/chargen_seed_table.yaml` (mirror the 126-25 world-gear wiring). New RED test `tests/genre/test_126_24_world_seed_table_load.py` pins it; existing 19 tests stay GREEN. Affects `sidequest-server/sidequest/genre/models/pack.py` + `sidequest/genre/loader.py`. *Found by TEA during rework (Reviewer blocker).*

### Dev (implementation)
- **Improvement** (non-blocking): I confirmed TEA's AC8 surface call — `{high_concept}` token + content rewrite is the right fix (the summary card already handled Fate). The other 10 Fate genres' (`spaghetti_western`, `tea_and_murder`, `wry_whimsy`) confirmation narrations were NOT audited for the same `a {race} {class}` mash; if they use that template under their Fate binding they have the same latent bug. Affects `sidequest-content/genre_packs/{spaghetti_western,tea_and_murder,wry_whimsy}/char_creation.yaml` (audit + same `{high_concept}` rewrite). *Found by Dev during implementation.*
- **Improvement** (non-blocking): only `pulp_noir` got a `chargen_seed_table`; the other three Fate packs still present a blank pyramid on their narrative on-ramp. Same fix applies (author a per-genre seed table). The validator check TEA flagged would make this gap loud. Affects `sidequest-content/genre_packs/{spaghetti_western,tea_and_murder,wry_whimsy}/rules.yaml`. *Found by Dev during implementation.*
- **Improvement** (non-blocking, rework round 1): world overrides now have a source (`worlds/<slug>/chargen_seed_table.yaml` → typed `World.chargen_seed_table`), but NO live world authors one yet (annees_folles uses the genre table). The capability is wired + tested; authoring an annees_folles override is content follow-up, not engine work. The Reviewer's other non-blocking findings ({high_concept} sanitize, OTEL world_hints spoiler note, empty-aspects span) remain open as follow-ups. Affects `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/`. *Found by Dev during rework.*

### Reviewer (code review)
- **Gap** (blocking): world-tier `chargen_seed_table` override (AC2) is half-wired — `resolve_fate_chargen_seed_table` has no loader source (`World` lacks the field; `_assemble_world` never sets it), so the world tier is always empty and a raw-dict path would crash. Affects `sidequest-server/sidequest/genre/models/pack.py` + `sidequest/genre/loader.py` (add typed `World.chargen_seed_table` + loader population, mirroring `gear`) and the AC2 test. *Found by Reviewer during code review.* (This is the REJECT blocker — see Reviewer Assessment.)
- **Improvement** (non-blocking): apply `protocol/sanitize.py::sanitize_player_text` to `self._fate_high_concept` before the `{high_concept}` substitution (defense-in-depth at the new interpolation site; ADR-047 still covers the narrator boundary). Affects `sidequest-server/.../builder.py::interpolate_scene_narration`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `_emit_fate_seed_table_merged` broadcasts `world_hints` (authored vocation key names) to `/ws/watcher`; document a "hint keys must be non-spoiler" authoring constraint or emit only a count. Affects `sidequest-server/.../fate_chargen.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): emit the aspects-step `fate.chargen.seed_applied` span unconditionally on a hint match (with `aspect_count=0` when the seed carries no aspects) so the GM panel can distinguish "no aspects in seed" from "seed didn't fire". Affects `sidequest-server/.../builder.py::_fate_step_payload`. *Found by Reviewer during code review.*

#### Reviewer (re-review, round 2)
- **Status update:** the round-1 blocking Gap (world-tier override half-wired) is **RESOLVED** by the rework (typed `World.chargen_seed_table` + loader population). Verified GREEN end-to-end.
- **Improvement** (non-blocking): `_load_chargen_seed_table` (and its sibling `_load_gear`) raise a raw pydantic `ValidationError` on a malformed *entry* that names neither the file path nor the offending hint key — fails loud but unhelpfully for content authors. Wrap per-entry `model_validate` in a `GenreLoadError(path=..., detail=f"hint {hint!r}: ...")`, ideally for both helpers together. Affects `sidequest-server/sidequest/genre/loader.py`. *Found by Reviewer during re-review.*
- **Improvement** (non-blocking): a present-but-empty `worlds/<slug>/chargen_seed_table.yaml` (YAML null/comments-only) returns `{}` identically to an absent file (gear-parity with `_load_gear`); if strict No-Silent-Fallbacks is desired, distinguish `path.exists()` from `raw is None`. Affects `sidequest-server/sidequest/genre/loader.py`. *Found by Reviewer during re-review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** I confirmed TEA's AC8 surface call — `{high_concept}` token + content rewrite is the right fix (the summary card already handled Fate). The other 10 Fate genres' (`spaghetti_western`, `tea_and_murder`, `wry_whimsy`) confirmation narrations were NOT audited for the same `a {race} {class}` mash; if they use that template under their Fate binding they have the same latent bug. Affects `sidequest-content/genre_packs/{spaghetti_western,tea_and_murder,wry_whimsy}/char_creation.yaml`.

### Downstream Effects

- **`sidequest-content/genre_packs/{spaghetti_western,tea_and_murder,wry_whimsy}`** — 1 finding

### Deviation Justifications

8 deviations

- **World override implemented as a runtime resolve function, not an ADR-121 loader merge**
  - Rationale: the gear catalog is the nearest shipped precedent for genre+world union with world-wins and the same per-key shape; reusing that pattern (rather than a bespoke ADR-121 loader-tier merge) keeps the Fate seed/gear seams symmetric and is already proven in production. The merge semantics ("world wins per hint key") are identical to ADR-121's intent.
  - Severity: minor
  - Forward impact: if Keith/Dev prefer a literal loader-tier per-field merge, the AC2 test (duck-typed pack/world fakes) and the resolver name change together — the "world wins per hint" assertion is what must hold.
- **New API surface pinned by the tests (FateHintSeed, chargen_seed_table, resolve fn, seed span, {high_concept} token)**
  - Rationale: TDD red must fail against concrete symbols; pinning them in the test docstring + assessment lets Dev implement to a stable contract and Reviewer verify intent. Names follow existing Fate conventions (`FateStuntDef`, `gear_catalog`, `resolve_fate_gear_catalog`, `fate.chargen.*` spans).
  - Severity: minor
  - Forward impact: Dev may rename with a documented deviation provided the behavioral intent (legal seeded pyramid + editable free-aspects + HC/Trouble no-silent-default + OTEL + gear) is preserved.
- **Seed table entry is a COMPLETE legal pyramid per hint, not per-skill bumps that combine**
  - Rationale: combining multiple partial hint-bumps into one allocation cannot guarantee the exact-budget legality AC4 demands without a solver; a complete-per-entry table makes every authored seed independently validatable (and authorable/overridable by Jade-as-author).
  - Severity: minor
  - Forward impact: if a future genre wants multi-hint blending, the resolver/seed-selection can grow; the per-entry legality invariant should remain.
- **Content-existence invariants deferred to the integration test / validator, not unit-tested**
  - Rationale: project rule — pytest tests code with synthetic fixtures; content invariants belong in the pack validator, never unit tests.
  - Severity: minor
  - Forward impact: none — Dev authors the content; the integration test goes green when present, the validator (if added) guards it going forward.
- **Rework round 1: world override source is a dedicated `worlds/<slug>/chargen_seed_table.yaml` file, not a world-tier rules merge**
  - Rationale: the Reviewer's required fix cited the world-gear precedent; a dedicated world file + typed field is the established loader pattern (gear/stocks/classes), gives free pydantic coercion (fixes the raw-dict crash), and avoids inventing a world-tier rules-merge subsystem. Genre table stays in `rules.yaml fate.chargen_seed_table`; world override is the dedicated file — the same genre-in-rules / world-in-file split gear uses.
  - Severity: minor
  - Forward impact: content authors override per-world in `chargen_seed_table.yaml`, not in a world rules block. If a future story adds world-tier rules merging, the seed table could migrate there; the resolver + builder consume `World.chargen_seed_table` regardless of source.
- **World override wired via builder-attach (`with_fate_seed_table`), NOT loader injection onto the shared FateConfig**
  - Rationale: injecting the world-merged table onto `cfg.chargen_seed_table` would MUTATE the shared, process-wide genre pack per session/world — a cross-session corruption bug. `gear_catalog`'s loader injection is world-AGNOSTIC (genre-only, once at load); the seed table needs per-session world resolution, so it follows the per-session `with_*`-attach pattern the chargen builder already uses for classes/equipment/backgrounds.
  - Severity: minor
  - Forward impact: none — the resolver + merge semantics are unchanged; only the wiring locus differs (builder-attached, not cfg-mutated). Reviewer should confirm no other consumer reads `cfg.chargen_seed_table` expecting the world-merged value.
- **`apply_fate_aspects` now raises on empty HC/Trouble (new builder-tier guard)**
  - Rationale: the seed makes the pyramid + free aspects fillable-by-default; the test pins that this must NOT weaken the mandatory-aspect invariant. The builder record method is the right tier to fail loud (No Silent Fallbacks) so no caller can silently record a blank mandatory aspect.
  - Severity: minor
  - Forward impact: none — production callers (the handler) already pass non-empty values; the guard only fires on a programming error or a bypassed handler.
- **`{high_concept}` resolves empty-with-warn for non-Fate packs, not raise**
  - Rationale: matches the existing token behavior (empty `{class}` warns, doesn't raise); content only uses `{high_concept}` in Fate packs, so an empty resolution is a content-authoring smell the GM panel surfaces, not a runtime fault.
  - Severity: minor
  - Forward impact: none.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **World override implemented as a runtime resolve function, not an ADR-121 loader merge**
  - Spec source: context-story-126-24.md, AC2 ("world override ... via ADR-121 layered per-field resolution")
  - Spec text: "individual worlds (annees_folles) may override/extend per-hint via ADR-121 layered per-field resolution; a unit test proves a world override replaces the genre default for a given hint"
  - Implementation: AC2 is tested against `resolve_fate_chargen_seed_table(pack, world_slug)` — a runtime resolver mirroring the SHIPPED `resolve_fate_gear_catalog` (ADR-145), with the loader injecting the merged table onto `FateConfig.chargen_seed_table` exactly as it injects `gear_catalog`.
  - Rationale: the gear catalog is the nearest shipped precedent for genre+world union with world-wins and the same per-key shape; reusing that pattern (rather than a bespoke ADR-121 loader-tier merge) keeps the Fate seed/gear seams symmetric and is already proven in production. The merge semantics ("world wins per hint key") are identical to ADR-121's intent.
  - Severity: minor
  - Forward impact: if Keith/Dev prefer a literal loader-tier per-field merge, the AC2 test (duck-typed pack/world fakes) and the resolver name change together — the "world wins per hint" assertion is what must hold.
- **New API surface pinned by the tests (FateHintSeed, chargen_seed_table, resolve fn, seed span, {high_concept} token)**
  - Spec source: context-story-126-24.md, Technical Approach ("Approach hints to be refined by TEA/Dev")
  - Spec text: "_Approach hints to be refined by TEA/Dev. The story title above defines the intended behavior._"
  - Implementation: the tests DEFINE concrete names (see TEA Assessment "Pinned Public Contract"); RED begins as ImportError on them, per the 121-7 precedent.
  - Rationale: TDD red must fail against concrete symbols; pinning them in the test docstring + assessment lets Dev implement to a stable contract and Reviewer verify intent. Names follow existing Fate conventions (`FateStuntDef`, `gear_catalog`, `resolve_fate_gear_catalog`, `fate.chargen.*` spans).
  - Severity: minor
  - Forward impact: Dev may rename with a documented deviation provided the behavioral intent (legal seeded pyramid + editable free-aspects + HC/Trouble no-silent-default + OTEL + gear) is preserved.
- **Seed table entry is a COMPLETE legal pyramid per hint, not per-skill bumps that combine**
  - Spec source: context-story-126-24.md, AC1 + AC4
  - Spec text: AC1 "maps accumulated narrative hints ... to a Fate skill-pyramid allocation"; AC4 "The seeded pyramid is LEGAL: passes pyramid_violations/validate_fate_sheet ... every rung at exact budget"
  - Implementation: each `FateHintSeed.pyramid` is a full, legal allocation; the seed function selects an entry (class_hint-first) rather than additively combining multiple hints' partial bumps.
  - Rationale: combining multiple partial hint-bumps into one allocation cannot guarantee the exact-budget legality AC4 demands without a solver; a complete-per-entry table makes every authored seed independently validatable (and authorable/overridable by Jade-as-author).
  - Severity: minor
  - Forward impact: if a future genre wants multi-hint blending, the resolver/seed-selection can grow; the per-entry legality invariant should remain.
- **Content-existence invariants deferred to the integration test / validator, not unit-tested**
  - Spec source: context-story-126-24.md, AC1 ("table lives in pulp_noir genre config") + project rule (content invariants → validator)
  - Spec text: "the table lives in pulp_noir genre config (genre is the rulebook, ADR-140)"
  - Implementation: no pytest asserts "pulp_noir has a seed table"; the real-pack integration test exercises it functionally, and a validator check is recommended (Delivery Finding).
  - Rationale: project rule — pytest tests code with synthetic fixtures; content invariants belong in the pack validator, never unit tests.
  - Severity: minor
  - Forward impact: none — Dev authors the content; the integration test goes green when present, the validator (if added) guards it going forward.
- **Rework round 1: world override source is a dedicated `worlds/<slug>/chargen_seed_table.yaml` file, not a world-tier rules merge**
  - Spec source: context-story-126-24.md, AC2 ("via ADR-121 layered per-field resolution") + Reviewer REJECT (mirror the world-gear precedent)
  - Spec text: "individual worlds may override/extend per-hint via ADR-121 layered per-field resolution"
  - Implementation: the world override is authored in a dedicated `worlds/<slug>/chargen_seed_table.yaml` (a `hint -> {pyramid, aspects}` map) → typed `World.chargen_seed_table`, exactly mirroring `worlds/<slug>/gear.yaml → World.gear` (126-25). The loader has NO world-tier rules.yaml merge (only genre `rules.yaml`), so a literal world-rules per-field merge was not available.
  - Rationale: the Reviewer's required fix cited the world-gear precedent; a dedicated world file + typed field is the established loader pattern (gear/stocks/classes), gives free pydantic coercion (fixes the raw-dict crash), and avoids inventing a world-tier rules-merge subsystem. Genre table stays in `rules.yaml fate.chargen_seed_table`; world override is the dedicated file — the same genre-in-rules / world-in-file split gear uses.
  - Severity: minor
  - Forward impact: content authors override per-world in `chargen_seed_table.yaml`, not in a world rules block. If a future story adds world-tier rules merging, the seed table could migrate there; the resolver + builder consume `World.chargen_seed_table` regardless of source.

### Dev (implementation)
- **World override wired via builder-attach (`with_fate_seed_table`), NOT loader injection onto the shared FateConfig**
  - Spec source: TEA Assessment "Pinned Public Contract" #2 ("Loader-injected/world-merged exactly like `gear_catalog`")
  - Spec text: "FateConfig.chargen_seed_table ... Loader-injected/world-merged exactly like `gear_catalog`."
  - Implementation: the GENRE table loads directly from rules.yaml into `FateConfig.chargen_seed_table` (no injection needed — it's an authored field, unlike `gear_catalog` which comes from a separate gear.yaml). The WORLD merge is resolved per-session in `connect.py` via `resolve_fate_chargen_seed_table` and attached to the builder with the new `with_fate_seed_table` (parallel to `with_classes`/`with_equipment_tables`); `_fate_step_payload` prefers it over `cfg.chargen_seed_table`.
  - Rationale: injecting the world-merged table onto `cfg.chargen_seed_table` would MUTATE the shared, process-wide genre pack per session/world — a cross-session corruption bug. `gear_catalog`'s loader injection is world-AGNOSTIC (genre-only, once at load); the seed table needs per-session world resolution, so it follows the per-session `with_*`-attach pattern the chargen builder already uses for classes/equipment/backgrounds.
  - Severity: minor
  - Forward impact: none — the resolver + merge semantics are unchanged; only the wiring locus differs (builder-attached, not cfg-mutated). Reviewer should confirm no other consumer reads `cfg.chargen_seed_table` expecting the world-merged value.
- **`apply_fate_aspects` now raises on empty HC/Trouble (new builder-tier guard)**
  - Spec source: context-story-126-24.md, AC5 + TEA test `test_empty_high_concept_still_rejected_after_seeding`
  - Spec text: "HC/Trouble keep the no-silent-default invariant (must be non-empty on confirm)"
  - Implementation: added a strip-check to `CharacterBuilder.apply_fate_aspects` raising `ValueError` on empty/whitespace HC or Trouble — defense-in-depth behind the handler's existing `_chargen_fate_aspects_confirm` check (which still re-prompts the player).
  - Rationale: the seed makes the pyramid + free aspects fillable-by-default; the test pins that this must NOT weaken the mandatory-aspect invariant. The builder record method is the right tier to fail loud (No Silent Fallbacks) so no caller can silently record a blank mandatory aspect.
  - Severity: minor
  - Forward impact: none — production callers (the handler) already pass non-empty values; the guard only fires on a programming error or a bypassed handler.
- **`{high_concept}` resolves empty-with-warn for non-Fate packs, not raise**
  - Spec source: TEA Assessment "Pinned Public Contract" #7
  - Spec text: "New `{high_concept}` token ... resolving to the recorded Fate HC"
  - Implementation: `interpolate_scene_narration` treats `{high_concept}` like `{class}`/`{race}` — resolves to `""` and tags the watcher event `severity=warn` when no Fate HC is recorded, rather than raising.
  - Rationale: matches the existing token behavior (empty `{class}` warns, doesn't raise); content only uses `{high_concept}` in Fate packs, so an empty resolution is a content-authoring smell the GM panel surfaces, not a runtime fault.
  - Severity: minor
  - Forward impact: none.

### Reviewer (audit)
- **TEA: world override as runtime resolve (not ADR-121 loader merge)** → ✓ ACCEPTED by Reviewer: a runtime resolver mirroring `resolve_fate_gear_catalog` is the right, precedent-aligned choice. *Caveat:* the chosen pattern is only HALF-implemented (see the FLAG on the Dev builder-attach deviation) — the resolver is correct but has no world source.
- **TEA: new API surface pinned by the tests** → ✓ ACCEPTED by Reviewer: names follow existing Fate conventions (`FateStuntDef`, `gear_catalog`, `fate.chargen.*`); pinning in docstring + assessment is the 121-7 precedent.
- **TEA: seed table entry is a COMPLETE legal pyramid per hint** → ✓ ACCEPTED by Reviewer: guarantees AC4 legality without a solver and keeps each authored seed independently validatable — sound, and author-friendly for Jade.
- **TEA: content-existence deferred to integration test / validator** → ✓ ACCEPTED by Reviewer: correct per the "no content in unit tests" project rule; the real-pack integration test exercises it functionally.
- **Dev: world override via builder-attach (`with_fate_seed_table`), not cfg mutation** → ✗ FLAGGED by Reviewer: avoiding shared-pack mutation is the CORRECT instinct (accepted on that point), BUT the attach has no real input — `World` has no `chargen_seed_table` field and the loader never populates one, so `resolve_fate_chargen_seed_table` always returns the genre table and the world-override AC is non-functional. This is the HIGH blocker (see Reviewer Assessment). Fix: typed `World.chargen_seed_table` field + loader population (mirror world `gear`), keep the per-session builder-attach.
- **Dev: `apply_fate_aspects` raises on empty HC/Trouble** → ✓ ACCEPTED by Reviewer: sound defense-in-depth; fails loud at the builder record tier per No Silent Fallbacks.
- **Dev: `{high_concept}` empty-with-warn, not raise** → ✓ ACCEPTED by Reviewer: consistent with the existing `{class}`/`{race}` token behavior; the warn span surfaces the content smell.

#### Reviewer (audit) — round 2 (rework)
- **TEA: world override source is a dedicated `worlds/<slug>/chargen_seed_table.yaml`, not a world-rules merge** → ✓ ACCEPTED by Reviewer: the loader has no world-tier rules merge; a dedicated world file → typed `World.chargen_seed_table` is the established pattern (gear/stocks/classes) and gives free pydantic coercion. Sound, precedent-aligned, author-friendly.
- **Dev: world override via builder-attach (`with_fate_seed_table`)** → ✓ now ACCEPTED (round-1 FLAG CLEARED): the rework supplied the missing world source (typed `World.chargen_seed_table` field + `_assemble_world` population from the dedicated world file). The builder-attach + per-session no-pack-mutation design is correct AND now has a real input — the end-to-end path is verified by `test_126_24_world_seed_table_load.py`.
- **Dev: typed `World.chargen_seed_table` field + `_load_chargen_seed_table` loader (rework)** → ✓ ACCEPTED by Reviewer: mirrors `World.gear`/`_load_gear` exactly; pydantic coercion eliminates the raw-dict crash; fail-loud on malformed input. No new deviation from spec.