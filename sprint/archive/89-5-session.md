---
story_id: "89-5"
jira_key: ""
epic: "89"
workflow: "tdd"
---
# Story 89-5: Story 5 — Chargen surface + CRUNCH FLAGS (Keith's mechanics call): Earthman gravity-boon as a world-tier origin trait that MUST resolve to a REAL engine consumer (no unwired crunch — document the tier exception + verify the consumer); green four-arm physiology (fiction-only vs light trait); Mentalist/Super-scientist expressed as classes-vs-Foci. Touches the engine only where a consumer is required.

## Story Details
- **ID:** 89-5
- **Jira Key:** (none — Jira integration not enabled)
- **Workflow:** tdd
- **Points:** 8
- **Stack Parent:** none (not stacked)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T22:47:55Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T21:13:21Z | 2026-06-05T21:15:09Z | 1m 48s |
| red | 2026-06-05T21:15:09Z | 2026-06-05T21:48:14Z | 33m 5s |
| green | 2026-06-05T21:48:14Z | 2026-06-05T22:34:15Z | 46m 1s |
| review | 2026-06-05T22:34:15Z | 2026-06-05T22:39:52Z | 5m 37s |
| green | 2026-06-05T22:39:52Z | 2026-06-05T22:46:32Z | 6m 40s |
| review | 2026-06-05T22:46:32Z | 2026-06-05T22:47:55Z | 1m 23s |
| finish | 2026-06-05T22:47:55Z | - | - |

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — engine-touching crunch story; full red phase executed.

**Keith's mechanics calls (recorded 2026-06-05, via AskUserQuestion):**
1. Mentalist + Super-scientist = **Full Callings** (classes, not Foci) — follows the 89-4 staged hooks.
2. Earthman gravity boon = **STR edge (+2, via `stat_bonuses`) + Mighty-Leap-style Race-source ability + OTEL event**.
3. Green-Martian four arms = **fiction-only** (no native-origin crunch).

**Test Files:**
- `sidequest-server/tests/genre/test_barsoom_chargen_surface.py` — world-tier chargen surface contract (5 tests): world `char_creation` replaces genre; exactly one Earthman origin w/ `race_hint` + `stat_bonuses {STR: 2}`; ≥2 native origins; native origins crunch-free (four arms fiction-only); pulp class surface without doom Callings.
- `sidequest-server/tests/integration/test_barsoom_chargen.py` — builder wiring (6 tests): Earthman build carries boon end-to-end (accumulator + Race-source leap ability w/ engine-facing mechanical_effect); `chargen.origin_trait.applied` OTEL event w/ origin/stat_bonuses/ability_names attrs; native build gets nothing; genre-tier injected "Earthman" gets nothing (world-tier scoping tripwire — passes today by design); Mentalist + Super-scientist seed populated SpellcastingState through the WORLD scenes.
- `sidequest-server/tests/game/test_barsoom_cast_beat_live_content.py` — live-content cast gate (3 tests): both Barsoom casters see cast_spell in the real combat confrontation; Warrior stays excluded.
- AMENDED `tests/genre/test_heavy_metal_loads_wwn_classes.py` — chassis grows 5→7 Callings; cast_spell class_filter 3→5.
- AMENDED `tests/integration/test_wwn_heavy_metal_chargen.py` — `_CASTERS` += Mentalist/Super-scientist (full Effort-formula assertions ride for free).

**Tests Written:** 14 new + 2 amended files; **RED = 16 failed / 17 passed, 0 collection errors** (verified by testing-runner AND direct `uv run pytest -n0` cross-check — counts agree; session file integrity verified post-runner).
**Status:** RED (failing — ready for Dev)
**Commit:** `test: add failing tests for 89-5 ...` on `sidequest-server` `feat/89-5-barsoom-chargen-crunch-flags`.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality (no vacuous asserts) | self-check pass — every assert pins a specific value w/ message; parametrized cases hit distinct content paths | done |
| No Silent Fallbacks | `test_earthman_boon_is_world_tier_not_engine_hardcode` (no global race hardcode); chassis count==5 filter only passes via loud `_validate_class_filter_refs` | failing/red |
| Verify Wiring / wiring test per suite | `test_barsoom_chargen.py` (real builder), `test_barsoom_cast_beat_live_content.py` (real pack + beat filter) | failing/red |
| OTEL Observability | `test_earthman_boon_emits_origin_trait_otel_event` (+ absence negatives) | failing/red |
| No Source-Text Wiring Tests | complied — OTEL-event + fixture-driven behavior assertions only; zero `read_text()` on source | done |
| Crunch-in-genre / flavor-in-world (ADR-120) | surface tests pin trait to barsoom world scenes; Callings at genre tier per the wwn seam | failing/red |

**Rules checked:** 13-rule python checklist reviewed; #6 applies to test code (pass). #1/#3/#4 apply to Dev's builder seam — Reviewer to enforce on the green diff.
**Self-check:** 0 vacuous tests found.

**Dev guidance (Agent Smith):**
- Content (sidequest-content, branch exists): `heavy_metal/classes.yaml` += mentalist/super_scientist Callings (full wwn_magic, saving_throws, ≥1 signature ability, starting_prepared from the 89-4 seeds: phantom_bowmen+mind_veil / disintegration_ray+invisibility_compound); `rules.yaml` cast_spell class_filter += both display_names (hook comment marks the spot); NEW `worlds/barsoom/char_creation.yaml` (origins incl. Earthman w/ stat_bonuses, native origins crunch-free, pulp class choices, stat/equipment generation directives — world list REPLACES genre).
- Engine (sidequest-server, small seam): origin-trait ability seeding in `builder.py` (mirror `_seed_class_abilities`; source=Race) + `chargen.origin_trait.applied` event + SpanRoute registration (ADR-132). The STR edge needs NO engine change (`stat_bonuses` is pre-wired).
- Document the D5 tier exception (world-tier mechanical origin trait) where the trait is authored.

**Handoff:** To Dev for implementation (GREEN).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (33/33 green, lint/format pass, trees clean, branches pushed, loader gate pass; 2 pyright errors pre-existing on develop) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered personally (see [EDGE] items) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — domain covered personally (see [SILENT] items) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — domain covered personally (see [TEST] finding R3) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — comments audited personally (hook comment updated correctly) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — OriginTraitDef shape audited personally |
| 7 | reviewer-security | Yes | findings | 1 (low-confidence: stat_bonuses repr in OTEL attr) | confirmed 0, dismissed 0, deferred 1 (low confidence + first-party-content-only vector; logged as R4 observation) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — diff is minimal-by-construction (TDD) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — Rule Compliance section below is the manual equivalent |

**All received: Yes** (2 enabled returned; 7 disabled via workflow.reviewer_subagents)
**Total findings:** 3 confirmed (mine), 0 dismissed, 1 deferred

## Reviewer Assessment

**Verdict: REJECTED — two blocking content defects in the new barsoom chargen surface; engine seam is sound.**

### Findings

- **R1 [CRITICAL] [EDGE] Every barsoom chargen confirm is gate-blocked in live play — scenes never set `rpg_role_hint`.**
  Evidence chain: `builder.py:2398` forms `resolved_archetype` ONLY when BOTH `jungian_hint` AND `rpg_role_hint` accumulated (`if acc.jungian_hint is not None and acc.rpg_role_hint is not None`); `worlds/barsoom/char_creation.yaml` sets `jungian_hint` on 9 choices and `rpg_role_hint` on ZERO; heavy_metal DOES declare archetype axes (`archetype_constraints.yaml` + global `archetypes_base.yaml`), so the 45-6 gate (`chargen_mixin.py` `_gate_archetype_resolution`) classifies the resulting `resolved_archetype=None` as **BLOCKED_PARTIAL `missing_axes_with_pack_axes`** — the documented *pumblestone* playtest-3 failure: "pack declares axes but the chargen scenes accumulated at most one hint... chargen scenes malformed." The genre crucible pairs both hints on every class choice (`char_creation.yaml:104-242`: tank/dps/healer/control/...); the barsoom calling scene must do the same.
  **Required fix (content):** add a valid `rpg_role_hint` to each calling choice — Warrior→`tank`, Expert→`jack_of_all_trades`, Mentalist→`control`, Super-scientist→`dps` (valid ids per `archetypes_base.yaml:126-150`).
- **R2 [HIGH] [EDGE] `jungian_hint: warrior` is not a valid jungian axis id** (valid twelve: caregiver/ruler/artist/innocent/sage/explorer/outlaw/magician/hero/lover/jester/everyman — `archetypes_base.yaml:5-115`). Used at `worlds/barsoom/char_creation.yaml:93` (Green Martian origin) and `:154` (Blade calling). `resolve_archetype` raises `GenreValidationError("Unknown Jungian archetype")` (`shim.py:104-105`) → gate `resolver_raised` → chargen rejected for those picks even after R1 is fixed.
  **Required fix (content):** `warrior` → `hero` at both sites.
- **R3 [HIGH] [TEST] Test gap that let R1/R2 through:** the red suite walks `CharacterBuilder.build()` (which doesn't run archetype resolution — that lives in `chargen_mixin`), so nothing validates that world chargen scenes accumulate a resolvable (jungian, rpg_role) pair. **Required fix (test):** add a content-shape test asserting (a) every barsoom class-choice path yields BOTH hints, and (b) every `jungian_hint`/`rpg_role_hint` value in barsoom scenes exists in `archetypes_base.yaml` axes and the (j,r) pair is not forbidden by `archetype_constraints.yaml` — drive `resolve_archetype` directly with each pair (the real resolver, not string-matching). Without this, the next world surface re-ships the same live-play breakage.

### Observations (verified good)

- **[VERIFIED] [PRE]** Preflight green: 33/33 story tests, scoped ruff check+format pass, both working trees clean and branches pushed; loader gate confirms 7 classes + 5-name class_filter. Pyright's 2 errors exist identically on develop (pre-existing, not this story's debt).
- **[VERIFIED] [SILENT]** No silent fallbacks introduced: `beat_filter.py` WWN cast arm exits via explicit `continue` branches (no default substitution); `builder.py` origin-trait seam fires only on `acc.origin_trait is not None` with no fallback path; loader still fails loud on dangling class_filter names (`_validate_class_filter_refs`) — proven by the count==5 chassis test passing only after both Callings exist. Complies with the No Silent Fallbacks critical rule.
- **[VERIFIED] [SEC]** Security panel clean across all 6 rule categories: yaml.safe_load throughout the loader; `OriginTraitDef` and the `MechanicalEffects.origin_trait` field both `extra="forbid"` (`character.py:77,98`); prompt-injection posture unchanged (origin_trait text rides the IDENTICAL first-party path as `mutation_hint`/class-ability text; HTML surfaces escape()); OTEL attrs carry no PII/secrets.
- **[VERIFIED] [TYPE]** `OriginTraitDef` mirrors `AbilityDefinition`'s dual-voice shape with required `name/genre_description/mechanical_effect` (no Optional soup), `involuntary` defaulted; accumulator is last-one-wins, documented, matching every sibling single-value hint. Complies with the pack-content model convention.
- **[VERIFIED] [EDGE]** The `beat_filter` WWN-arm change preserves the B/X arm byte-for-byte (gate-2 + slots/prepared path untouched below the new early-exit); universal (`class_filter: None`) cast_spell beats skipping the WWN economy is PRE-EXISTING behavior (the universal branch predates this diff) — not introduced. Warrior-exclusion negative covered by live test.
- **[VERIFIED] [DOC]** The 89-4 BARSOOM HOOK comment in `rules.yaml` was rewritten to RESOLVED state (not deleted, not left stale); `beat_filter.py` change carries the chassis-contract citation; the D5/§9 tier exception is documented at length in the `char_creation.yaml` header — the documentation AC of the story title is met.

### Rule Compliance

| Rule (lang-review python.md / project) | Instances checked | Result |
|---|---|---|
| #1 silent exceptions | beat_filter.py, builder.py diff hunks — no try/except added | compliant |
| #2 mutable defaults | OriginTraitDef fields, AccumulatedChoices.origin_trait (None default) | compliant |
| #3 type annotations at boundaries | OriginTraitDef fields typed; builder seam uses existing annotations; SpanRoute lambda matches siblings | compliant |
| #4 logging | no new error paths requiring logging; OTEL event added per OTEL principle | compliant |
| #6 test quality | 33 tests, no vacuous asserts (TEA self-check + spot-check of differential/negative tests) — but see R3 coverage GAP | compliant w/ gap (R3) |
| #8 unsafe deserialization | yaml.safe_load (loader, unchanged); no pickle/eval | compliant |
| #10 import hygiene | function-local span import mirrors existing file pattern (BACKSTORY_COMPOSED); no star imports added | compliant |
| No Silent Fallbacks (CLAUDE.md critical) | beat_filter early-exits, builder None-guard, loader fail-loud | compliant |
| Verify Wiring (CLAUDE.md critical) | origin_trait: world YAML→loader→accumulator→build→abilities+OTEL proven by integration tests; **BUT the chargen_mixin archetype-gate leg is NOT covered → R1/R2 escaped** | violation via R1-R3 |
| OTEL Observability (CLAUDE.md important) | chargen.origin_trait.applied emitted + SpanRoute registered (GM-panel routable) | compliant |
| Crunch-in-genre/Flavor-in-world (SOUL.md) | tier exception documented in-file per D5/§9; Callings genre-tier per the wwn seam (TEA deviation log) | compliant |

### Devil's Advocate

Suppose I am wrong that the engine seam is sound. What would break it? A player could stack origin traits — but the accumulator is last-one-wins and only barsoom authors one; a malicious *content* author could put an essay in `stat_bonuses` keys and have it surface in the GM panel verbatim (the security panel's deferred low) — single-operator content makes this theoretical, but R4 notes it. What would a confused author do? Copy the Earthman choice as a template for a new origin and inherit the crunch by accident — the file header warns loudly, and the four-arms-fiction-only test fails on any native crunch; acceptable. What does a stressed runtime produce? `build()` emitting the OTEL event on a span that isn't recording is a no-op — same as every sibling event. The genuinely broken thing I found is not hypothetical: NO ONE — not TEA's 14 tests, not preflight's 33-green, not the security panel — exercised the archetype-resolution leg of the production chargen path, and that leg rejects every single barsoom character a real player would make. Two YAML lines of missing rpg_role_hint per calling and one bad jungian id would have shipped as "fully green." The tests proved the boon wiring while the surface that delivers it was dead on arrival. That is precisely the half-wired-feature failure mode this project's rules exist to catch, and it is why the verdict below is not negotiable.

**Verdict: REJECTED** — R1 (CRITICAL), R2 (HIGH), R3 (HIGH) must be fixed by Dev (content edits + one guard test) before re-review. The engine changes themselves (origin-trait seam, beat_filter WWN arm, span route) are approved-as-implemented; no changes requested there.

## Reviewer Assessment — Round 2 (rework verification)

**Verdict: APPROVED.**

Delta reviewed: content `6877fef` (+6/-2, char_creation.yaml) + server `b5468898` (new guard test). Verified personally with line-level evidence:

- **R1 FIXED [VERIFIED]** — all four calling choices carry a valid `rpg_role_hint` (Warrior hero/tank at char_creation.yaml:153-155; Expert jack_of_all_trades:165; Mentalist control:175; Super-scientist dps:185). Builder now forms the (j/r) pair; 45-6 gate passes.
- **R2 FIXED [VERIFIED]** — `grep 'jungian_hint: warrior'` over the file returns nothing; both sites now `hero`.
- **R3 FIXED [VERIFIED, non-vacuous]** — `tests/genre/test_barsoom_archetype_pairs.py` 2/2 green; oracle proven real by direct probe: `resolve_archetype('warrior','tank',...)` RAISES `GenreValidationError: Unknown Jungian archetype: 'warrior'` while the fixed `('hero','tank')` resolves to "Covenant-Shield" (weight common) through live axes + constraints. The test would have caught the original defects.
- Full suite green per rework assessment (10960 passed / 0 failed); story suite + guard tests re-verified directly this round.
- Deferred from round 1 (unchanged): security panel's low-confidence stat_bonuses-repr-in-OTEL note — defense-in-depth only, first-party content, no action required this story.

The engine seam was approved in round 1; the content defects are corrected and tripwired. **APPROVED — proceed to finish.**

## Dev Assessment (rework — review R1/R2/R3)

**Implementation Complete:** Yes (rework round 1)

**Fixes applied:**
- **R1** `worlds/barsoom/char_creation.yaml` — all four calling choices now carry `rpg_role_hint` (Warrior→tank, Expert→jack_of_all_trades, Mentalist→control, Super-scientist→dps); builder forms the (j/r) pair, 45-6 gate passes.
- **R2** same file — `jungian_hint: warrior` → `hero` (Green Martian origin + Blade calling).
- **R3** NEW `sidequest-server/tests/genre/test_barsoom_archetype_pairs.py` (2 tests): every class choice carries BOTH hints; every (origin × calling) last-wins accumulation resolves through the REAL `resolve_archetype` against live axes/constraints without raising. All four effective pairs — (hero,tank), (explorer,jack_of_all_trades), (magician,control), (sage,dps) — resolve.

**Tests:** guard tests 2/2; **full suite 10960 passed / 0 failed** (direct `uv run pytest`). Lint + format clean.
**Commits:** server `b5468898` (guard test), content `6877fef` (hint fixes) — both pushed.

**Handoff:** back to The Merovingian for re-review.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-server/sidequest/genre/models/character.py` — `OriginTraitDef` + `MechanicalEffects.origin_trait` (world-authored dual-voice Race-source trait)
- `sidequest-server/sidequest/game/builder.py` — accumulator (last-wins) + build-time seeding onto `Character.abilities` + `chargen.origin_trait.applied` emit
- `sidequest-server/sidequest/telemetry/spans/chargen.py` — span constant + `SpanRoute` registration (ADR-132; GM-panel visible)
- `sidequest-server/sidequest/game/beat_filter.py` — WWN arm: `class_filter` is the only class gate for `cast_spell` (see Dev deviation; B/X unchanged)
- `sidequest-content/genre_packs/heavy_metal/classes.yaml` — Mentalist (WIS) + Super-scientist (INT) full Callings, 89-4 seeds as `starting_prepared`
- `sidequest-content/genre_packs/heavy_metal/rules.yaml` — `cast_spell` `class_filter` 3→5, hook comment resolved
- `sidequest-content/genre_packs/heavy_metal/worlds/barsoom/char_creation.yaml` — NEW world-tier surface: 5 origins (Earthman carries the documented D5/§9 tier exception: `stat_bonuses {STR: 2}` + `Gravity-Born Leap` origin_trait), natives fiction-only, pulp-only class scene

**Tests:** story suite 33/33; **full server suite 10959 passed / 0 failed, 345 skipped** (direct `uv run pytest`, post-rebase). Lint + format clean on changed files (scoped ruff).
**Branches:** `feat/89-5-barsoom-chargen-crunch-flags` pushed in BOTH repos (server `5e0f83ef`, content `8e0/…` tip after rebase onto develop d050300 / b0aded30 — mid-story sync pulled in #371 barsoom tropes/legends + #372/#704 from parallel clones).

**ACs (TEA contracts):** all green — Callings exist + filter wired + chargen seeds spellcasting through the WORLD surface; Earthman boon end-to-end (accumulator STR edge + Race-source leap ability + OTEL event with origin/stat_bonuses/ability_names); native + genre-tier negatives hold (no boon outside barsoom); four arms fiction-only; tier exception documented in the world YAML header.

**Handoff:** To TEA for verify (simplify + quality-pass), then The Merovingian for review.

## Sm Assessment

**Setup complete — routing to TEA (The Architect) for the red phase.**

- **Story:** 89-5 (epic 89 Barsoom, 8 pts, p1, workflow `tdd`/phased). Last open story in the epic; all content stories (89-1..89-4, 89-6 authoring) are merged to `sidequest-content` develop.
- **Repos:** `sidequest-server` + `sidequest-content`; feature branch `feat/89-5-barsoom-chargen-crunch-flags` created and checked out in both. Both subrepos PR to their own `develop`; orchestrator targets `main`.
- **Contexts:** `sprint/context/context-story-89-5.md` (technical approach + ACs) and `sprint/context/context-epic-89.md` written by sm-setup.
- **Jira:** explicitly skipped — integration not enabled for this project.
- **Scope (Keith's mechanics call, from the story title):**
  1. Earthman gravity-boon as a world-tier origin trait that resolves to a REAL engine consumer — no unwired crunch; document the tier exception; verify the consumer (wiring test mandatory).
  2. Green four-arm physiology: decide fiction-only vs light trait.
  3. Mentalist/Super-scientist expressed as classes-vs-Foci; wire `cast_spell` `class_filter` to the new Callings (89-4 left a BARSOOM HOOK comment in `heavy_metal/rules.yaml` and `starting_prepared` seeds in `spells_wwn.yaml` headers; `_validate_class_filter_refs` fails loud on unbacked names, so classes must land before the filter edit).
  4. Engine touched only where a consumer is required; OTEL events on any new subsystem decision.
- **Risk noted for TEA:** backlog story 90-2 alleges the WWN/ADR-126 magic plugin is not instantiated — if true, casting-path wiring tests in this story may surface that seam. Treat as a finding, not silent scope creep.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Improvement** (non-blocking): Backlog story 90-2's "WWN magic plugin not instantiated" allegation is orthogonal to mechanical casting — `resolve_spellcast` lives in `WwnRulesetModule` (sidequest/game/ruleset/wwn.py) and is live; the ADR-126 MagicPlugin registry ships only innate_v1/learned_v1/item_legacy_v1 (no WWN plugin) and governs narrator magic-working validation, not spell slots.
  Affects `sidequest-server/sidequest/magic/plugins/__init__.py` (90-2 scoping should target narrator-working validation, not the cast path).
  *Found by TEA during test design.*
- **Gap** (non-blocking): `MechanicalEffects.stat_bonuses` is the pre-wired consumer for the STR edge (applied additively by `generate_stats` under every strategy) — Dev needs NO engine change for the stat half of the boon. The leap-ability half + `chargen.origin_trait.applied` OTEL event need a small builder seam (mirror `_seed_class_abilities` + `SPAN_CHARGEN_CLASS_ABILITIES_SEEDED`; register a SpanRoute in telemetry/spans/chargen.py per ADR-132 so the GM panel sees it).
  Affects `sidequest-server/sidequest/game/builder.py` (origin-trait ability seeding + OTEL emit).
  *Found by TEA during test design.*

### Dev (implementation)

- **Gap** (non-blocking): The WWN cast gate was dead for ALL casters on the `beats_available_for` path — gate 2 (`encounter_beat_choices`) contradicted the chassis contract ("class_filter is the only gate") and filtered `cast_spell` for the doom Callings too. Fixed this story on the WWN arm; epic 90's live-verification stories should re-baseline against the fixed gate.
  Affects `sidequest-server/sidequest/game/beat_filter.py` (fixed in 5e0f83ef; 90-3/90-4 should confirm live engagement).
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): The pre-existing live-pack validator failures (barsoom `tropes.yaml` + `legends/`) were resolved upstream mid-story by content PR #371 (parallel clone); after rebasing both feature branches onto the moved develops, the full suite is 10959 passed / 0 failed.
  Affects `sidequest-content/genre_packs/heavy_metal/worlds/barsoom/` (no further action).
  *Found by Dev during implementation.*


## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned prime requisites for the new Callings (Mentalist=WIS, Super-scientist=INT)**
  - Spec source: design spec §7 Story 5 / 89-4 BARSOOM HOOK comments
  - Spec text: hooks name the Callings and their starting_prepared seeds but no prime_requisite
  - Implementation: tests assert WIS (will-projection tradition) and INT (vanished science) in `_EXPECTED_CLASSES`
  - Rationale: the chassis test format requires a prime; canon-faithful picks consistent with the doom casters' INT/CHA pattern; heavy_metal attribute_map carries all six keys
  - Severity: minor
  - Forward impact: Dev/content may contest with a better canon argument — change the test row + classes.yaml together
- **Pinned doom-Callings excluded from the barsoom chargen surface**
  - Spec source: context-epic-89.md
  - Spec text: "True to source = heroic Frazetta pulp, NOT grimdark doom"
  - Implementation: `test_barsoom_class_surface_offers_pulp_callings_not_doom` asserts Necromancer/Elementalist/Pact-born absent from barsoom scene class_hints
  - Rationale: faithful Barsoom has no necromancers; the world surface REPLACES the genre crucible, so exclusion is contentable
  - Severity: minor
  - Forward impact: none — world-tier only; doom worlds unaffected
- **TEA-defined OTEL contract name `chargen.origin_trait.applied`**
  - Spec source: CLAUDE.md OTEL Observability Principle / SM assessment item 4
  - Spec text: "OTEL events on any new subsystem decision"
  - Implementation: tests require this exact event name with origin/stat_bonuses/ability_names attributes
  - Rationale: mirrors the existing `chargen.class_abilities.seeded` naming family
  - Severity: minor
  - Forward impact: Dev must use this name (and should register a SpanRoute per ADR-132)
- **One negative test passes pre-implementation (not strictly RED)**
  - Spec source: story title ("world-tier origin trait")
  - Spec text: "Earthman gravity-boon as a world-tier origin trait"
  - Implementation: `test_earthman_boon_is_world_tier_not_engine_hardcode` passes today (no boon exists anywhere) and acts as a tripwire against a global race-string hardcode
  - Rationale: a scoping negative cannot fail before the positive exists; paired with failing positives it pins the tier boundary
  - Severity: minor
  - Forward impact: none — it must STAY green after implementation
### Dev (implementation)
- **WWN cast-gate fix in beat_filter (engine change beyond the planned builder seam)**
  - Spec source: session scope item 4 / TEA live-content test contract
  - Spec text: "Touches the engine only where a consumer is required" + "the rules.yaml class_filter is the only gate that should offer it" (heavy_metal chassis contract)
  - Implementation: `beats_available_for` + `cast_spell_rejection_reason` now treat `class_filter` as the ONLY class gate for `cast_spell` on the WWN arm (spellcasting is not None); gate 2 (`encounter_beat_choices`) no longer applies to it
  - Rationale: the two contracts conflicted — the chassis test (passing since 87-2) forbids `cast_spell` in any class's `encounter_beat_choices`, while gate 2 required it, silently starving EVERY WWN caster (doom Callings included) of the beat on this path. The fix honors the documented contract; B/X arm byte-for-byte unchanged
  - Severity: moderate
  - Forward impact: epic 90 (live crunch verification) should re-baseline — the gate was dead for all WWN casters in any `beats_available_for` consumer before this fix
- **Direct pytest instead of the testing-runner helper for GREEN verification**
  - Spec source: dev agent definition (testing-runner protocol)
  - Spec text: "Spawn testing-runner to verify GREEN state"
  - Implementation: ran `uv run pytest` directly (story suite -n0, then full suite twice: pre-rebase 10947 passed/2 pre-existing failures, post-rebase 10959 passed/0 failed)
  - Rationale: project memory documents the helper overwriting `.session/` files and fabricating per-test output; TEA already cross-checked the helper against direct runs this story. Direct counts are the trustworthy artifact
  - Severity: minor
  - Forward impact: none — full-suite green is verified and reproducible