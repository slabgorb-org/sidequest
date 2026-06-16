---
story_id: "114-13"
jira_key: "none"
epic: "114"
workflow: "tdd"
---
# Story 114-13: road_warrior: decide + optionally let combat classes start with CWN-category weapons

## Story Details
- **ID:** 114-13
- **Jira Key:** none (personal project, no Jira integration)
- **Workflow:** tdd (phased: setup → red → green → review → finish)
- **Epic:** 114 (SRD-sourced inventory)
- **Type:** refactor
- **Points:** 2
- **Priority:** p3
- **Repos:** server,content
- **Stack Parent:** none (not stacked)

## Context

CWN/WWN equipment extractors emit catalog items with `category="melee_weapon"` and `category="ranged_weapon"` (sidequest/cli/cwn_equip_extract/cwn_equip_extract.py:204,227 and wwn_equip_extract.py:194,220).

However, the chargen-loadout path and the personal-weapon guard/strike path currently key on the bespoke `category: "weapon"` string (sidequest/server/dispatch/chargen_loadout.py:87,221; sidequest/game/builder.py:2484).

Story 114-5 (CWN equipment extractor) is merged on develop. road_warrior is a CWN-bound pack.

**Goal:** Widen the personal-weapon guard + strike path to accept `melee_weapon`/`ranged_weapon` in addition to bespoke `category:weapon`, so road_warrior combat classes can start with and strike using CWN-category weapons.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T02:36:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T02:00:00Z | 2026-06-16T02:02:25Z | 2m 25s |
| red | 2026-06-16T02:02:25Z | 2026-06-16T02:17:41Z | 15m 16s |
| green | 2026-06-16T02:17:41Z | 2026-06-16T02:28:18Z | 10m 37s |
| review | 2026-06-16T02:28:18Z | 2026-06-16T02:36:57Z | 8m 39s |
| finish | 2026-06-16T02:36:57Z | - | - |

## Branches
- **Strategy:** github-flow on both subrepos; develop is the integration branch
- **Branch (server):** feat/114-13-road-warrior-cwn-weapon-categories
- **Branch (content):** feat/114-13-road-warrior-cwn-weapon-categories

## Sm Assessment

**Verdict:** Ready for RED. Premise verified live during setup — not stale.

**Why this story, now:** Picked over 114-10 (the other open epic-114 story) because 114-10's
four target packs (pulp_noir/spaghetti_western/tea_and_murder/wry_whimsy) are being actively
reshaped onto `ruleset: fate` by epics 118/120/121 — 114-10 needs a premise re-check first.
114-13 is road_warrior (CWN-bound), so it sits clear of that Fate churn. Dependency 114-5 is
merged (`0e70d6d6`); this story has no `depends_on`.

**Premise confirmed (SM context-discovery, not implementation):**
- Extractors emit `category="melee_weapon"` / `"ranged_weapon"`
  (`cwn_equip_extract.py:204,227`, `wwn_equip_extract.py:194,220`).
- Consumers still gate on bespoke `category:"weapon"`
  (`chargen_loadout.py:87,221`, `builder.py:2484`).
- So road_warrior combat classes cannot start with / strike using CWN-category weapons today.
  That gap IS the story.

**Scope guidance for TEA/Dev (route, not prescribe):**
- "Decide + optionally" in the title means there is a real decision baked in: confirm the
  desired behavior (combat classes SHOULD start with CWN-category weapons) before widening.
  The conservative read is yes — widen the guard + strike path to accept
  `melee_weapon`/`ranged_weapon` alongside `weapon`.
- Two repos: server is the code change; content (road_warrior) is the data that exercises it.
  Drive the test against the REAL road_warrior pack, not a synthetic fixture — both the
  chargen-loadout path AND the strike/guard path must be covered (these are separate paths;
  a guard fix that no-ops at chargen, or vice-versa, is a known trap in this codebase).
- Watch for the project rule: combat-mutation features must wire BOTH resolution paths.

**Definition of done:** road_warrior combat class starts with a CWN-category weapon and can
strike with it end-to-end; OTEL span/coverage for the widened guard; full server suite gated
against the documented pre-existing baseline (do NOT mislabel baseline failures as regressions).

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Question** (blocking): The story's "decide + optionally" fork is now a hard test
  assumption — combat classes MUST start with CWN-category weapons. SM ruled yes
  (conservative, 2026-06-15); Reviewer/Keith should confirm before GREEN locks it.
  Affects `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/inventory.yaml`
  (re-categorize bespoke personal weapons to CWN, or repoint starting_equipment at the
  verbatim genre CWN catalog). *Found by TEA during test design.*
- **Gap** (non-blocking): The title names the "strike path" but it is ALREADY
  category-agnostic — `resolve_damage_spec_from_beat_and_actor` resolves by the item's
  `damage` field / name, never by category. No strike-path code change is needed; it is
  locked by `test_road_warrior_combat_dispatch.py::test_road_warrior_strike_depletes_ablative_hp_on_real_turn`.
  Affects `sidequest/game/ruleset/combat_rules.py` (no change — do not balance/gate it).
  *Found by TEA during test design.*
- **Improvement** (non-blocking): If Dev RETIRES the `pistol` id (replace-with-genre-CWN
  path) instead of re-categorizing in place, the hardcoded fixture
  `weapon = {"id": "pistol"}` at `tests/server/test_road_warrior_combat_dispatch.py:128`
  must be repointed at the class's new starting weapon id or it goes RED. *Found by TEA during test design.*
- **Gap** (non-blocking): The narrator-mint guard widening touches the inventory subsystem
  (`sidequest/server/narration_apply.py` ~4607 allowlist) — per CLAUDE.md OTEL principle it
  must emit a watcher/OTEL event for the category-acceptance decision (the inventory watcher
  seam already exists on this path). Consider a shared `WEAPON_CATEGORIES` constant rather
  than the scattered `"weapon"` literals (also `builder.py:2484`). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): Chose re-categorize-in-place over replace-with-verbatim-CWN.
  The verbatim genre-tier CWN gear (`cwn_light_pistol`, `cwn_shotgun`…) stays available but
  unused by the_circuit loadouts. A future ADR-145 pass could retire the bespoke flavor
  weapons entirely in favor of the verbatim catalog. Affects
  `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/inventory.yaml`.
  *Found by Dev during implementation.*
- **Improvement** (non-blocking): `sidequest/game/builder.py:2484` still hardcodes
  `category: "weapon"` as the item_hint stub default (harmless — hints are upgraded from the
  catalog in `chargen_loadout._upgrade_hint_items_from_catalog`). A shared `WEAPON_CATEGORIES`
  constant would centralize the taxonomy if more guards appear. Affects `sidequest/game/builder.py`.
  *Found by Dev during implementation.*
- **Question** (non-blocking, restated): implemented the "decide" fork as conservative-yes per the
  SM ruling (combat classes start with CWN-category weapons). Final confirmation rests with
  Reviewer/Keith (see TEA's blocking Question). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the narrator-mint guard emits on off-taxonomy category
  coercion but not on absent/empty category (`if category_raw and ...` short-circuits). This is
  a benign default (misc) for an optional field — verified NOT a regression (pre-114-13 `develop`
  had no emit at all for any coercion) and emitting per category-less item would be GM-panel noise.
  A `narrator_item_category_missing` emit could be added if the panel later wants full coverage.
  Affects `sidequest/server/narration_apply.py`. *Found by Reviewer during code review.* [SILENT]
- **Improvement** (non-blocking): `name_val`/`desc_val` (narrator/LLM output) are length-unbounded;
  `name_val` is now also echoed into the coercion watcher event. Single-tenant, self-hosted,
  LLM-sourced → low risk, and consistent with existing watcher events that already echo item names,
  but a `MAX_ITEM_NAME_LEN` cap at the boundary would bound save-row bloat + watcher frame size.
  Affects `sidequest/server/narration_apply.py`. *Found by Reviewer during code review.* [SEC]
- **Improvement** (non-blocking, pre-existing): `chargen_loadout._item_dict_minimal` hardcodes
  category `"equipment"`, which is not in the narrator-mint allowlist; the two code paths do not
  intersect at runtime today. Out of scope for 114-13. Affects
  `sidequest/server/dispatch/chargen_loadout.py`. *Found by Reviewer during code review.* [SILENT]

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **Encoded the "decide" fork as a hard CWN-only requirement**
  - Spec source: session `## Sm Assessment`; story title
  - Spec text: "decide + optionally let combat classes start with CWN-category weapons"
  - Implementation: tests REQUIRE strike-class starting weapons to carry `melee_weapon`/`ranged_weapon` (CWN-only, excluding legacy `weapon`)
  - Rationale: an untested fork cannot drive RED; SM holds spec authority and ruled the fork yes
  - Severity: minor
  - Forward impact: if Keith rules NO, `test_the_circuit_*` must be relaxed (see blocking Question above)
- **Did not add a failing strike-path test**
  - Spec source: story title
  - Spec text: "widen the ... strike path to accept melee_weapon/ranged_weapon"
  - Implementation: no new strike-path RED test; the strike resolver is already category-agnostic
  - Rationale: a RED test for already-correct behavior would be vacuous; existing dispatch test locks it
  - Severity: minor
  - Forward impact: none — strike path needs no code change
- **Widened an existing passing test predicate**
  - Spec source: story title / ADR-145 (bind, don't author)
  - Spec text: "widen the personal-weapon guard ... not just bespoke category:weapon"
  - Implementation: `test_road_warrior_combat_dispatch.py` predicates changed from `== "weapon"` to `in {weapon, melee_weapon, ranged_weapon}`
  - Rationale: those tests ARE the guard; without widening they would false-RED after the content re-categorization
  - Severity: minor
  - Forward impact: none

### Dev (implementation)
- **OTEL emitted on the coercion (reject) path, not per accepted item**
  - Spec source: session `## Delivery Findings` → TEA Gap (non-blocking, OTEL)
  - Spec text: "must emit a watcher/OTEL event for the category-acceptance decision"
  - Implementation: emit `inventory / narrator_item_category_coerced` only when a narrator category is off-taxonomy and coerced to `misc`; accepted weapon categories remain observable via the existing per-item `item_recipient_resolved` inventory watcher events on this path
  - Rationale: emitting per accepted item is noisy on the happy path; the previously-silent signal worth surfacing is the coercion (No Silent Fallbacks + lie-detector)
  - Severity: minor
  - Forward impact: none — acceptance is still observable via existing events

### Reviewer (audit)
- **TEA: Encoded the "decide" fork as a hard CWN-only requirement** → ✓ ACCEPTED by Reviewer:
  SM held spec authority and ruled conservative-yes; the implementation is a content category swap
  + an additive allowlist entry, fully reversible. TEA's blocking Question (Keith confirmation) is
  noted but non-blocking for a p3, trivially-reversible content change.
- **TEA: Did not add a failing strike-path test** → ✓ ACCEPTED by Reviewer: independently verified —
  `resolve_damage_spec_from_beat_and_actor` resolves by `damage`/name, never category; a RED test
  for already-correct behavior would be vacuous. Existing dispatch test locks it (passed in preflight).
- **TEA: Widened an existing passing test predicate** → ✓ ACCEPTED by Reviewer: the
  `_PERSONAL_WEAPON_CATEGORIES` widening IS the guard; necessary to avoid false-RED after the
  content re-categorization.
- **Dev: OTEL emitted on the coercion (reject) path, not per accepted item** → ✓ ACCEPTED by
  Reviewer: correct signal-to-noise choice; acceptance remains observable via existing per-item
  inventory watcher events. (See Reviewer Improvement re: also emitting on absent-category — non-blocking.)
- **No undocumented deviations found.** The diff matches the logged decisions exactly.

## TEA Assessment

**Tests Required:** Yes

**Test Files:**
- `sidequest-server/tests/server/test_114_13_road_warrior_cwn_weapon_categories.py` — NEW.
  Drives the real road_warrior pack via `load_genre_pack` + `resolve_inventory(pack, "the_circuit")`
  and the real narration-apply seam `_apply_narration_result_to_snapshot`.
- `sidequest-server/tests/server/test_road_warrior_combat_dispatch.py` — widened the existing
  personal-weapon guard predicate (`== "weapon"` → CWN set).

**Tests Written:** 5 new test cases (incl. 2 parametrized) + 2 widened existing guards.

**Status:** RED — verified `4 failed, 3 passed` (`uv run pytest -n0` with `SIDEQUEST_DATABASE_URL` set):
- FAIL `test_the_circuit_combat_classes_start_with_a_cwn_category_weapon` (the decision + content)
- FAIL `test_the_circuit_has_no_legacy_bespoke_personal_weapon_category` (content)
- FAIL `test_narrator_minted_cwn_weapon_keeps_its_cwn_category[ranged_weapon]` (server guard — proved `ranged_weapon`→`misc`)
- FAIL `test_narrator_minted_cwn_weapon_keeps_its_cwn_category[melee_weapon]` (server guard — proved `melee_weapon`→`misc`)
- PASS (by design) `test_the_circuit_still_declares_personal_weapons` (anti-vacuous anchor)
- PASS (by design) the two widened guards in `test_road_warrior_combat_dispatch.py`

### Rule Coverage

| Rule (CLAUDE.md / lang-review) | Test(s) | Status |
|------|---------|--------|
| Wiring test (real loader + real prod seam, not source-grep) | `test_the_circuit_*` (real `load_genre_pack`/`resolve_inventory`); narrator test drives real `_apply_narration_result_to_snapshot` | failing/anchor |
| Meaningful assertions (no vacuous) | all — anti-vacuous anchor guards the two "absence" asserts | pass |
| OTEL observability on subsystem change | flagged to Dev as a Delivery Finding (narrator-mint inventory seam must emit a watcher event) | deferred to GREEN |
| No silent fallbacks (fail-loud) | tests assert on real resolved catalog/category, not stubs | failing |

**Rules checked:** wiring + meaningful-assertion + OTEL flagged; the OTEL emit is Dev's GREEN-phase obligation.
**Self-check:** 0 vacuous tests found.

**Implementation pointers for Dev (Inigo Montoya):**
- Content (`the_circuit/inventory.yaml`): make strike-class starting weapons carry CWN categories
  (`melee_weapon`/`ranged_weapon`). Two valid paths (TEA stayed path-agnostic): re-categorize the
  bespoke world weapons in place (keeps ids — safest for the line-128 fixture), OR repoint
  `starting_equipment` at the verbatim genre CWN catalog (`cwn_light_pistol`, `cwn_shotgun`…).
- Server (`narration_apply.py` ~4607 allowlist): add `melee_weapon`, `ranged_weapon` so a
  narrator-granted CWN weapon keeps its category; emit the OTEL/watcher event for that decision.
- Do NOT touch the strike-damage resolver — it is already category-agnostic (see Delivery Finding).
- Gate against the full server-suite pre-existing baseline; do not mislabel baseline failures as regressions.

**Handoff:** To Dev for GREEN implementation (server + content).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content/genre_packs/road_warrior/worlds/the_circuit/inventory.yaml` — re-categorized
  the 5 bespoke personal weapons (pistol, sawed_off_shotgun, crossbow → `ranged_weapon`; tire_iron,
  chain → `melee_weapon`) to CWN categories per their melee/ranged tags. Ids + damage unchanged.
  Mounted/rig weapons left at `category: weapon` (vehicular, out of scope). Updated the stale
  pistol comment.
- `sidequest-server/sidequest/server/narration_apply.py` — added `melee_weapon`/`ranged_weapon`
  to the narrator-mint items_gained allowlist; emit `inventory/narrator_item_category_coerced`
  watcher event on the off-taxonomy coercion path (OTEL lie-detector).

**Tests:**
- Target tests GREEN: `4 formerly-RED → pass`, plus the widened guards + anchor (7 in the new
  file all pass; `test_road_warrior_combat_dispatch.py` all pass).
- Affected/at-risk suites GREEN: 94 passed across chargen_loadout, inventory_resolve,
  inventory_union_merge, cwn_inventory_wiring, item_gain_catalog_resolution,
  road_warrior_cwn_combat_e2e, 114_14_neon_road_world_migration, vessel_calibration,
  120_2_verbatim_baseline.
- Full server suite: `171 failed, 11430 passed, 1600 skipped` — the 171 matches the documented
  pre-existing baseline exactly (zero net-new). The 8 failures that name-matched my blast-radius
  grep are all SDK-hermeticity (`build_async_anthropic` LlmClientError) or chargen fixture
  baselines (`InvalidChoiceError`, missing corpus files) — confirmed by root cause, NOT one
  touches weapon/category/inventory behavior.
- Lint + format clean on both changed files.

**Branches (pushed):**
- server: `feat/114-13-road-warrior-cwn-weapon-categories` (commits: TEA `e920f532` tests + Dev guard)
- content: `feat/114-13-road-warrior-cwn-weapon-categories` (Dev re-categorization)

**ACs / DoD met:**
- ✅ combat classes start with a CWN-category personal weapon (decision: conservative-yes per SM)
- ✅ no legacy bespoke `category: weapon` on damaging non-mounted personal weapons
- ✅ personal-weapon guard accepts melee_weapon/ranged_weapon (narrator-mint + widened test guards)
- ✅ OTEL coverage for the guard (coercion watcher event)
- ✅ strike path untouched (already category-agnostic; locked by existing dispatch test)

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 10 targeted tests green, content loads (92 items), 0 smells |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 2 | downgraded 1 (High→Low, non-blocking), dismissed 1 (pre-existing/out-of-scope) |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | Yes | findings | 2 | both Low/non-blocking, deferred as Improvements |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (Rule Compliance done by Reviewer manually below) |

**All received:** Yes (3 enabled returned; 6 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 4 non-blocking (1 downgraded High→Low, 3 Low/deferred), 1 dismissed (pre-existing, non-intersecting path)

## Reviewer Assessment

**Verdict:** APPROVED

This is a small, well-scoped change: re-categorize 5 bespoke road_warrior personal weapons to the
CWN `melee_weapon`/`ranged_weapon` categories (content), and widen one narrator-mint category
allowlist to accept those categories with an additive OTEL coercion emit (server). The RED tests
TEA wrote now pass; no Critical/High survives scrutiny.

**Data flow traced:** narrator `items_gained[*]` entry → `_narrator_item_dict` → `category_raw`
allowlist check → inventory item dict → snapshot (`character.core.inventory.items`). Narrator output
is the project's "semi-trusted" boundary; category is allowlist-bounded (off-taxonomy → `misc`, now
with a loud watcher event); name/desc are str-coerced. Safe for a single-tenant self-hosted server.

**Pattern observed:** additive allowlist widening + guarded watcher emit at
`sidequest/server/narration_apply.py:4606-4636`; mirrors the existing `_watcher_publish` inventory
pattern (e.g. `recipient_missing` at line ~3336). Good pattern adherence.

**Error handling:** the coercion path now fails loud (warning watcher event) on off-taxonomy
categories; the absent-category benign default stays silent (see [SILENT] finding — non-blocking).

### Rule Compliance (Python lang-review checklist — Reviewer-enumerated, rule_checker disabled)

| # | Rule | Applies? | Verdict |
|---|------|----------|---------|
| 1 | Silent exception swallowing | no new try/except | ✓ compliant — no except blocks added |
| 2 | Mutable default args | no new defaults | ✓ n/a |
| 3 | Type annotations at boundaries | `_narrator_item_dict` pre-existing internal helper; new test helpers annotated | ✓ compliant |
| 4 | Logging coverage/correctness | new watcher emit uses `severity="warning"` (correct for an anomalous-but-recoverable event); no f-string log misuse | ✓ compliant |
| 6 | Test quality (vacuous asserts) | new tests assert specific values; anti-vacuous anchor `test_the_circuit_still_declares_personal_weapons` guards the two absence-asserts; widened predicates still assert | ✓ compliant |
| 8 | Unsafe deserialization | none (`entry` is upstream Pydantic-parsed; no pickle/eval/yaml.load) | ✓ compliant |
| 11 | Input validation at boundaries | category allowlist-bounded; name/desc str-coerced but length-unbounded | △ minor — see [SEC] (non-blocking) |
| — | No Silent Fallbacks (SOUL/CLAUDE) | off-taxonomy coercion now emits; absent-category benign default unchanged | ✓ compliant (improvement noted) |
| — | OTEL on subsystem change (CLAUDE) | coercion watcher event added; acceptance observable via existing per-item events | ✓ compliant |
| — | Bind the Ruleset (SOUL) | content adopts CWN categories; strike path untouched (no native-vs-bound balancing) | ✓ compliant |

### Observations

- [VERIFIED] Content re-categorization is safe — the only production site touching `category=="weapon"`
  is a stub *default assignment* at `builder.py:2484` (upgraded from catalog), NOT a filter; no consumer
  filters the_circuit weapons by category. Evidence: full-tree grep, and strike resolver
  `combat_rules.py` keys on `damage`/name not category.
- [VERIFIED] Mounted/rig weapons correctly left at `category: weapon` — `vessel_calibration` tests
  (which key on `category=="weapon" & mounted/rig tags`) pass unchanged.
- [SILENT][LOW] Absent/empty narrator category coerces to `misc` without a watcher event — benign
  default for an optional field, NOT a regression (pre-114-13 `develop` had no emit at all). Non-blocking.
- [SEC][LOW] `name_val`/`desc_val` length-unbounded; `name_val` echoed into the coercion watcher event.
  Single-tenant self-hosted LLM output → low risk; a `MAX_ITEM_NAME_LEN` cap would be a tidy follow-up.
- [SILENT][LOW] Pre-existing: `chargen_loadout._item_dict_minimal` category `"equipment"` not in the
  narrator allowlist; non-intersecting paths. Out of scope — dismissed for this story.
- [EDGE] (rule_checker/edge-hunter disabled — Reviewer-checked): `str(entry.get("category","") or "")`
  handles None/non-str categories; empty `items_gained` is a no-op; `_is_mounted` tolerates missing tags.
- [TEST] (test-analyzer disabled — Reviewer-checked): new tests are behavioral against the real pack +
  the real `_apply_narration_result_to_snapshot` seam; parametrized over both CWN categories; no coupling
  to implementation internals beyond the documented category contract.
- [DOC] (comment-analyzer disabled — Reviewer-checked): the stale `pistol` comment was correctly updated
  to the CWN-category rationale; new comments are accurate.
- [TYPE] (type-design disabled — Reviewer-checked): `_PERSONAL_WEAPON_CATEGORIES` frozenset; category
  remains string-typed (pre-existing system-wide design; not in scope to newtype here).
- [SIMPLE] (simplifier disabled — Reviewer-checked): minimal, additive change; the
  `_PERSONAL_WEAPON_CATEGORIES` constant is duplicated across two test files — acceptable test-local
  duplication, not worth extracting.
- [RULE] see Rule Compliance table above — all applicable rules compliant.

### Devil's Advocate

Suppose this change is broken. The most dangerous move in this diff is the content re-categorization:
if ANY production code branched on `category == "weapon"` to decide that an item is a *personal* strike
weapon, silently flipping five weapons to `melee_weapon`/`ranged_weapon` would make road_warrior
combatants unable to find their own guns — a catastrophic, invisible combat regression a passing unit
suite might miss if it used synthetic fixtures. I treated that as the primary threat: a full-tree grep
shows the only `category=="weapon"` site is a stub default assignment in `builder.py`, and the actual
strike resolver (`combat_rules.resolve_damage_spec_from_beat_and_actor`) keys on the `damage` field and
catalog id, never the category — so a re-categorized weapon still resolves its dice. The
`road_warrior_cwn_combat_e2e` and `vessel_calibration` suites (real pack, real dispatch) pass, which is
the wiring proof that matters. Second threat: the narrator-mint widening. A confused or prompt-injected
narrator could emit a junk category — but the allowlist still coerces anything unknown to `misc`, and
now emits a watcher warning, so the failure mode is *more* visible than before, not less. A malicious
narrator emitting a giant item name is the only residual concern (unbounded `name_val` → save bloat +
big WebSocket frame), but it is single-tenant, self-hosted, LLM-sourced, and bounded only by the model's
own output — rated low, logged as a follow-up. Third: did the test-widening hide a real failure? The
widened predicates still require a damaging, non-mounted weapon; they were green before AND after, and
the *new* stricter tests (CWN-only category) are what actually drove the change. A confused future
editor could re-add a bespoke `category: weapon` personal weapon — but `test_the_circuit_has_no_legacy_
bespoke_personal_weapon_category` now fails loudly if they do. Nothing here reaches Critical or High.

**Handoff:** To SM (Vizzini) for finish-story.