---
story_id: "158-19"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-19: Per-expansion quests surface only one theme — quest binds deepest region (wide drowned_cavern band) + sparse projection skips diverse expansions

## Story Details
- **ID:** 158-19
- **Jira Key:** none (local sprint tracking)
- **Workflow:** tdd
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Priority:** p2

## Problem Statement

Per-expansion quests currently show only one theme (drowned_cavern / "Below the Black Water") across a full descent, even though beneath_sunden ships 5 themes with distinct quest templates. Regional themes diversify with depth (winding_catacomb at exp006, bone_crypt at exp008), but the quest mechanism does not reflect this variety.

### Root Causes

1. **Quest binds deepest region's theme:** expansion_quest.select_signature → _deepest. drowned_cavern's depth_band {0,60} is the widest, so it wins the deepest slot even at depth 42-52.
2. **Shallow zone single-theme by construction:** At depth_score 0–19, eligible theme_pool is exactly [drowned_cavern], so rng.choice has one element.
3. **Sparse projection skips diverse expansions:** reconcile_dungeon_quests_into_log only projects threads whose expansion_id == to_region's expansion. Multi-expansion-per-turn jumps pass THROUGH exp6-9 (diverse themes) without landing, so their quests never reach quest_log.
4. **Static title strings:** drowned_cavern.yaml quest_template.title is literal "Below the Black Water" with no {region}/{depth}/ordinal slot in expansion_quest._fill, so same-theme repeats are byte-identical.

### Acceptance Criteria

1. A single beneath_sunden descent crossing ≥3 expansions across ≥2 theme bands yields ≥2 DISTINCT quest titles in player-visible quest_log (not all drowned_cavern).
2. **Content:** theme depth_bands staggered so depth 0 has ≥2 eligible themes; drowned_cavern's max narrowed so it stops dominating the deepest-region slot deep in the dungeon. Exact band values are Keith's call (crunch/pacing).
3. **Server:** an expansion traversed/jumped-through during multi-region movement still projects its quest into quest_log — OR a documented, intentional decision that only landed-in expansions mint quests.
4. Same-theme expansions produce distinguishable quest titles (region/depth/ordinal token; needs a new slot in expansion_quest._fill).
5. **OTEL:** the dungeon.quest.bound span carries the bound theme id so the GM panel can verify which theme each quest used.
6. No regression to the working mint→project→complete path: the per-expansion quest still completes on its reach_deep beat.

## Sm Assessment

**Scope confirmed with operator (Keith, 2026-06-24).** Original 158-19 was filed as a four-root-cause quest-variety bug. Keith narrowed the lead: *"We have templates for the various generated dungeon. We are starved of templates in the easiest levels, and we need to provide variety."* The lead deliverable is **content authoring** — more shallow-depth-eligible quest-template themes for beneath_sunden so the opening descent isn't monotone (root cause #2). The binding/projection/title fixes (root causes #1, #3, #4) stay in scope as secondary; do not drop them, but the shallow-variety content is the headline.

**Why this story, why now:** p2, highest-value of the three p2s for player experience — every opening descent currently reads identically ("Below the Black Water"). Self-contained content+server; depth_band values are a Keith-owned crunch/pacing call (flag him in green, don't guess final numbers).

**Routing:** tdd / phased. Hand to TEA (Amos) for RED. The natural failing test is the cleanest invariant: `themes_for_depth(beneath_sunden, shallow)` returns >1 theme (target ≥3), plus the AC-1 descent test (≥3 expansions / ≥2 bands → ≥2 distinct titles). TEA: lock the shallow-variety invariant first; the binding/projection/title tests are secondary RED.

**Green-phase note (carry forward):** authoring new themes is creative content work — Dev should brainstorm genre-true theme concepts for beneath_sunden (WWN port; drowned/catacomb/crypt register) or pull in writer / scenario-designer, then validate with the cliche-judge agent. Don't ship cliché filler to hit a theme count.

**Gates:** session ✓, context ✓ (`sprint/context/context-story-158-19.md`), branches ✓ (both repos, `feat/158-19-shallow-quest-template-variety` off develop), Jira explicitly skipped (story is local-tracking, `jira: null`). Merge gate clear — only open PR is dependabot #1063 (deps bump, not story-linked).

## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavior-changing bug fix across content (theme depth_bands/titles) + server (projection, theme-on-span). Not a chore-bypass candidate.

**Test Files:**
- `sidequest-server/tests/dungeon/test_shallow_quest_template_variety.py` — 7 RED tests against the REAL beneath_sunden palette + REAL quest functions (no mocks).

**Tests Written:** 7 tests covering AC-1 through AC-5 (AC-6 guarded by existing e2e — see deviations)
**Status:** RED — verified via testing-runner. All 7 fail on `AssertionError` (not import/setup); file collects cleanly.

| Test | AC | Root cause | RED reason today |
|------|----|-----------|------------------|
| `test_shallow_depth_has_at_least_two_eligible_themes` | AC-2 (keystone) | #2 | depth 0 & 15 eligible == `[drowned_cavern]` only |
| `test_drowned_cavern_no_longer_dominates_deep_slot` | AC-2 | #1 | drowned band `{0,60}` still eligible at depth 50 |
| `test_shallow_band_offers_at_least_two_distinct_quest_titles` | AC-1 | #2 | exactly 1 bindable shallow title ("Below the Black Water") |
| `test_traversed_expansions_project_into_quest_log` | AC-3 | #3 | observer projects only the landed expansion (exp5), skips exp2-4 |
| `test_same_theme_expansions_produce_distinct_quest_titles` | AC-4 | #4 | two drowned expansions -> byte-identical static title |
| `test_quest_bound_span_carries_bound_theme` | AC-5 | — | `dungeon.quest.bound` span has no `theme` attribute |
| `test_span_route_surfaces_bound_theme_to_gm_panel` | AC-5 | — | SPAN_ROUTES extractor drops `theme` (GM panel can't see it) |

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| python lang-review #6 (test quality — meaningful assertions, no vacuous truthy/skip) | all 7 (each asserts a specific value/membership with a diagnostic message; zero `assert True`/bare-truthy/`@skip`) | satisfied |
| Wiring (CLAUDE.md "Every Test Suite Needs a Wiring Test") | `test_traversed_*` (real frontier observer), `test_quest_bound_span_*` (real `seed_expansion_quest` -> real OTEL span via global-tracer override), `test_span_route_*` (real `SPAN_ROUTES` extractor) | satisfied — behavior/end-to-end, not source-grep |

**Rules checked:** lang-review #6 is the applicable test-design rule for this content+behavior story; #1-5/#7-8 (silent except, mutable defaults, deserialization, resource leaks) govern the SOURCE/CONTENT fix — Dev must honor them in green, no test-design hit here.
**Self-check:** 0 vacuous tests found.

**Green-phase handoff notes for Dev (Naomi):**
- HEADLINE is content: author >=2 (SM target >=3) shallow-eligible themes for `beneath_sunden/themes/`. Keith's three seeds are in Delivery Findings (Animated Armory / Mushroom-Zombies / Skeleton Tomb Guardians). Run them past `cliche-judge` before merge.
- `depth_band` numbers (incl. drowned's narrowed max) are Keith's crunch/pacing call — flag him; the only hard floor my tests enforce is "drowned not eligible at depth 50" (playtest-grounded).
- AC-4 distinguisher: `expansion_quest._fill` needs a new region/depth/ordinal slot; my AC-4 test reads the stored payload title so either a YAML `{slot}` or seed-time injection passes.
- AC-5: thread the bound theme onto `quest_bound_span` AND into `SPAN_ROUTES[dungeon.quest.bound].extract` — both are asserted.
- AC-3 has an OR-escape (documented landed-only minting) — see TEA deviation if you take that path.

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-24T11:37:35Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-24T08:39:20Z | 2026-06-24T08:45:58Z | 6m 38s |
| red | 2026-06-24T08:45:58Z | 2026-06-24T09:15:37Z | 29m 39s |
| green | 2026-06-24T09:15:37Z | 2026-06-24T11:23:55Z | 2h 8m |
| review | 2026-06-24T11:23:55Z | 2026-06-24T11:37:35Z | 13m 40s |
| finish | 2026-06-24T11:37:35Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **Setup notes (Keith's clarification):** PRIMARY work is CONTENT AUTHORING — author more shallow-depth-eligible quest-template themes for caverns_and_claudes/beneath_sunden. The opening descents are monotone by construction because the shallow-eligible theme pool is exactly [drowned_cavern]. Target ≥3 eligible themes for depth 0–19. The depth_band values are a crunch/pacing call — Keith owns them. Secondary work: reconcile binding/projection logic and title templating.

### TEA (test design)
- **Improvement** (non-blocking): Keith handed three shallow-theme seeds for green-phase content authoring (2026-06-24, mid-RED) — green Dev/writer/scenario-designer should build the new shallow `themes/*.yaml` from these (depth_bands are Keith's call):
  1. **Animated Armory** — flying weapons; HD ½ → 1 creatures (low-CR, shallow-appropriate); big bad = an animated suit of armor.
  2. **Mushroom/Disease/Addiction Zombies** — fungal/plague-thralls; big bad = a spawner of some kind.
  3. **Skeleton Tomb Guardians** — skeletal wardens; big bad sealed in a coffin.
  These map cleanly to `reach_deep`/`set_piece` quest signatures (big_bad resolution is still deferred per `test_beneath_sunden_quest_templates.py`). Run the new themes past the `cliche-judge` agent before merge. *Found by TEA during test design.*

### GM (content authoring)
GM (Keith pulled in mid-green for the content half) delivered the CONTENT; the SERVER-CODE half (AC-3/4/5) remains for Dev. Content committed in sidequest-content `cf9a9eb`.

- **Done — content (AC-1, AC-2 shallow variety):** Widened all 5 existing theme `depth_band`s to `{0, null}` and authored 3 new themes (8 total): `skeleton_tomb` (The Standing Barrow), `fungal_warren` (The Spore-Fed Dark), `animated_armory` (The Oathbound Armoury). Result: **8 themes + 8 distinct quest titles eligible at every depth (0→120)**. All 3 new themes CLEAR cliche-judge (specialist granularity). Content tests green: `test_shallow_depth_has_at_least_two_eligible_themes`, `test_shallow_band_offers_at_least_two_distinct_quest_titles`, `test_every_beneath_sunden_theme_has_a_quest_template`; zero schema regressions.
- **Conflict (blocking — DESIGN CHANGE, Keith 2026-06-24):** The original AC-2 "narrow drowned_cavern's max so it stops dominating the deepest slot" is **overruled**. Keith's directive: random dungeon, not authored progression — themes broadly eligible at EVERY depth (≥5/stratum), depth tunes ENCOUNTERS (per-creature/set-piece depth_band + cookbook cr_bands), not themes. drowned is 1-of-8 everywhere, including deep (available, never forced). Affects `sidequest-server/tests/dungeon/test_shallow_quest_template_variety.py::test_drowned_cavern_no_longer_dominates_deep_slot` — it asserts drowned NOT eligible at depth 50 and now fails by design. **TEA/Dev must rework it** to the new invariant: "≥5 themes eligible at every depth (0, 15, 50, 120…)". See gm-decisions.md "Random-dungeon theme eligibility". *Found by GM during content authoring.*
- **Gap (blocking — Dev code, AC-3):** `test_traversed_expansions_project_into_quest_log` fails — `reconcile_dungeon_quests_into_log` / `make_expansion_quest_observer` (`sidequest/dungeon/expansion_quest.py`) project only the landed expansion; multi-expansion jumps skip the traversed ones. Code fix (Naomi). *Found by GM during content authoring.*
- **Gap (blocking — Dev code, AC-4):** `test_same_theme_expansions_produce_distinct_quest_titles` fails — `expansion_quest._fill` needs a region/depth/ordinal slot so two same-theme expansions get distinct titles (the per-theme titles are already distinct in content, but same-theme repeats are byte-identical without the distinguisher). Code fix (Naomi). *Found by GM during content authoring.*
- **Gap (blocking — Dev code, AC-5):** `test_quest_bound_span_carries_bound_theme` + `test_span_route_surfaces_bound_theme_to_gm_panel` fail — thread the bound theme onto `quest_bound_span` (`seed_expansion_quest` passes `theme=`; add `theme` to `SignatureBinding`) and add `theme` to `SPAN_ROUTES[SPAN_QUEST_BOUND].extract` in `sidequest/telemetry/spans/dungeon_quest.py`. Code fix (Naomi). *Found by GM during content authoring.*
- **Improvement (non-blocking — code risk):** `sunless_temple` is now eligible at shallow depth and uses the `roomcorridor` generator, which raises ValueError / degrades below 5×5. The materializer must validate region dims before interior dispatch (the carry-forward gotcha noted in `sunless_temple.yaml`, now exposed at shallow depth). Dev should verify dim-validation is live. *Found by GM during content authoring.*
- **Improvement (non-blocking — pre-existing):** The 5 existing themes' `creature_table`/`loot_table` refs (`blind_cave_eel`, `silt_pearl`, `crypt_warden`…) resolve to nothing — decorative/unwired (Plan 6 deferred); runtime creatures come from the region `look` → cookbook RACE → bestiary, loot from cookbook `loot_bias`. The 3 NEW themes use REAL bestiary ids (`hold_skeleton`, `the_seep`, `gnaw_swarm`, `wight`, `grave_ghoul`). Separate cleanup pass could real-ref the existing 5. *Found by GM during content authoring.*
- **RESOLVED — sunless_temple look-gap (supersedes the "validate dims" finding above), Keith 2026-06-24:** the earlier "validate region dims before dispatch" finding was a MIS-DIAGNOSIS. `sunless_temple` (built/roomcorridor) is unmaterializable in beneath_sunden: the cookbook ships no roomcorridor look (only depthfirst/cellular/prim) and `KNOWN_GENERATOR_BINDINGS` excludes roomcorridor — the materializer fail-loud'd at the look→theme seam (`_resolve_look_for_theme`), seed-dependently red across `test_session_*` / `test_region_projection_*`. Keeping roomcorridor would need server code (extend the binding set + author a look + dim validation) — out of the content lane. **Fix (content-only, committed `8e330ce`):** re-themed `sunless_temple` built→labyrinthine (depthfirst, params `{}`, braid 0.3), binding the existing necropolis look — undead faction + mausoleum-formal register fit the temple-of-the-dead better than cellular/sunken (ooze). Validated: `just content-validate caverns_and_claudes` PASS (0 errors); full dungeon suite green 3×. *Resolved by GM during green.*
- **Note (non-blocking — PRE-EXISTING, not this story):** the full server suite shows ~10 reds in WWN-dispatch / mutation / seam-crossing / scene-harness integration tests (`test_wwn_*_dispatch`, `test_seam_crossing_wiring`, `test_use_mutation_tool`, `test_102_7_*`, `test_103_10_*`). Verified pre-existing: stashing ALL 158-19 changes (both repos) and running them serially on a clean tree reproduces 6 fails; the remainder are parallel-run Postgres-pool teardown flakiness (`pool 'sidequest-save' is already closed`). None touch quests/themes/dungeon. The story's gate is the dungeon suite (523 green) + content validator (PASS); do not block the green exit on these. *Found by GM during green.*

### Dev (implementation)
- **Improvement** (non-blocking): `built`/roomcorridor themes are unsupported by beneath_sunden's materialization path — `KNOWN_GENERATOR_BINDINGS` excludes `roomcorridor` and no cookbook look binds it, so any future built theme fails loud at the look→theme seam (`_resolve_look_for_theme`). Resolved this story content-side (GM re-themed sunless_temple). Affects `sidequest/game/cookbook/loader.py` (`KNOWN_GENERATOR_BINDINGS`) + `genre_packs/caverns_and_claudes/worlds/beneath_sunden/cookbook/looks.yaml` (would need a roomcorridor look + dim-validation wiring before any built theme ships in this world). *Found by Dev during implementation.*
- **Note** (non-blocking): the ~10 full-server-suite reds (WWN-dispatch / mutation / seam-crossing / scene-harness) are PRE-EXISTING and unrelated — proven by stashing all 158-19 changes (both repos) and reproducing 6 on a clean tree serially; the rest are parallel-run Postgres-pool teardown flakiness. The story's green evidence is the dungeon suite (523 green) + content validator (PASS). *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking): the `feat/158-19-shallow-quest-template-variety` server branch carries an unrelated commit `dab123ef fix(158-11): preload authored NPCs as manual_origin + placed` (story 158-11 is **backlog**, with its own remote branch `origin/feat/158-11-harmund-fuelcount-seed-reconcile`). It is NOT in `origin/develop`, so the eventual 158-19 PR would merge 158-11's WIP under the wrong story. Affects `sidequest/game/world_materialization.py` + `tests/server/test_world_materialization_authored_npcs.py` (rebase the 158-19 branch onto clean `origin/develop` to drop `dab123ef`, or coordinate so 158-11 merges via its own branch — **before** SM creates/merges the 158-19 PR). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): stale module docstring in `tests/dungeon/test_shallow_quest_template_variety.py` (lists the overruled "narrow drowned_cavern's band" root cause and a blanket "RED until content lands" that no longer holds). Affects that file's header docstring (refresh to the random-dungeon doctrine + note AC-3/4/5 are now green). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): pre-existing silent fallbacks adjacent to the touched code — `select_signature` big_bad `name` → `"the master of this place"` (renders the big_bad quest unresolvable) and `_expansion_id_of` `except ValueError: return None` (masks malformed ids). Not introduced by 158-19; the big_bad path is unexercised by current content. Affects `sidequest/dungeon/expansion_quest.py` (a future story should fail loud per No Silent Fallbacks). *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **AC-6 regression guarded by existing e2e, no new test written**
  - Spec source: context-story-158-19.md, AC-6
  - Spec text: "No regression to the working mint->project->complete path: the per-expansion quest still completes on its reach_deep beat."
  - Implementation: Wrote no new AC-6 test; rely on the existing `tests/dungeon/test_expansion_quest_e2e.py::test_seed_project_resolve_and_spans` as the regression guard.
  - Rationale: That e2e already drives the full seed->project->resolve lifecycle through real functions with OTEL span assertions; duplicating it is redundant. My RED set is additive and the AC-4/AC-5 fixes must keep it green.
  - Severity: minor
  - Forward impact: Dev/Reviewer must keep test_expansion_quest_e2e.py green — a break there is the AC-6 regression signal.
- **AC-3 pins the "traversed projects" reading, not the OR-alternative**
  - Spec source: context-story-158-19.md, AC-3
  - Spec text: "an expansion traversed/jumped-through during multi-region movement still projects its quest into quest_log -- OR a documented, intentional decision that only landed-in expansions mint quests."
  - Implementation: `test_traversed_expansions_project_into_quest_log` asserts the first reading (jumped-through expansions project). The OR-alternative (documented landed-only decision) is not tested.
  - Rationale: "Still projects" is the lead behavior and the one that fixes the playtest bug (diverse intermediate expansions skipped). If green documents the landed-only decision instead, this one test must be revised to assert that documented behavior.
  - Severity: minor
  - Forward impact: Dev/Architect — choosing the landed-only path means revising this single test, not deleting the coverage.
- **AC-1 pinned as a content invariant, not a full-materializer descent**
  - Spec source: context-story-158-19.md, AC-1
  - Spec text: "A single beneath_sunden descent crossing >=3 expansions across >=2 theme bands yields >=2 DISTINCT quest titles in the player-visible quest_log."
  - Implementation: Pinned AC-1 via `test_shallow_band_offers_at_least_two_distinct_quest_titles` (shallow-eligible themes carry >=2 distinct quest_template titles) plus AC-2's eligibility tests, rather than driving the real materializer's RNG theme-assignment across a multi-turn descent.
  - Rationale: The monotony root cause is the shallow theme pool (AC-2); the content invariant is the necessary-and-sufficient condition for the player-visible promise and is refactor-stable, where a full materializer descent would couple to RNG internals.
  - Severity: minor
  - Forward impact: none — AC-2 eligibility + this title-distinctness test together enforce AC-1's outcome.
- **AC-2 drowned-domination floor uses depth 50, not a fixed band value**
  - Spec source: context-story-158-19.md, AC-2
  - Spec text: "drowned_cavern's max narrowed so it stops dominating the deepest-region slot deep in the dungeon. Exact band values are Keith's call (crunch/pacing)."
  - Implementation: `test_drowned_cavern_no_longer_dominates_deep_slot` asserts drowned is NOT eligible at depth_score 50.0 (a derived floor), not a specific max.
  - Rationale: Keith owns the exact number; 50 is the bug-repro floor grounded in the playtest DB (drowned wrongly at depth 42.2 and 52.8). Any narrowing below 50 satisfies it, leaving full pacing latitude.
  - Severity: minor
  - Forward impact: if Keith picks a max in [50, 60), this test fails and must be relaxed by agreement — flag him in green.

### Dev (implementation)
- **Reworked TEA test `test_drowned_cavern_no_longer_dominates_deep_slot` → `test_every_depth_offers_at_least_five_themes`**
  - Spec source: session Delivery Findings — GM "Conflict (blocking — DESIGN CHANGE, Keith 2026-06-24)"; gm-decisions.md "Random-dungeon theme eligibility"
  - Spec text (original AC-2): "drowned_cavern's max narrowed so it stops dominating the deepest-region slot deep in the dungeon"
  - Implementation: replaced the drowned-banishment assertion (drowned NOT eligible at depth 50 + bounded max) with the new random-dungeon invariant — ≥5 themes eligible at every stratum (0/15/50/120) and drowned stays 1-of-N including deep. Removed the now-unused `theme_eligible_at_depth` import and `_DROWNED_DOMINATION_DEPTH` constant.
  - Rationale: Keith overruled the original AC-2 framing mid-green (random dungeon: depth tunes ENCOUNTERS via cookbook cr_bands, not theme eligibility). The GM authored content to match (all themes {0,null}); the test must assert the new doctrine. GM explicitly authorized "TEA/Dev must rework it."
  - Severity: minor
  - Forward impact: none — the new invariant is the agreed doctrine; TEA's "drowned-domination floor uses depth 50" deviation above is superseded by this rework.
- **Updated pre-existing test `test_expansion_quest_select.py::test_big_bad_binds_deepest_region_with_big_bad` title assertion**
  - Spec source: context-story-158-19.md, AC-4
  - Spec text: "Same-theme expansions produce distinguishable quest titles (region/depth/ordinal token; needs a new slot in expansion_quest._fill)."
  - Implementation: AC-4's seed-time distinguisher appends `— Depth {n}` to the bound title, so this pre-existing exact-title assertion (`"The bone_crypt Stirs"`) now reads `"The bone_crypt Stirs — Depth 30"` (anchor exp001.r1 @ depth 30). Updated the assertion + added an AC-4 comment.
  - Rationale: AC-4 deliberately changes title generation; the old exact-match assertion encoded pre-AC-4 behavior. Updating it reflects the new intended behavior, not a workaround.
  - Severity: minor
  - Forward impact: none — single assertion, behavior now matches AC-4.
- **AC-4 distinguisher = depth token (chose "depth" from the AC's region/depth/ordinal menu)**
  - Spec source: context-story-158-19.md, AC-4
  - Spec text: "region/depth/ordinal token; needs a new slot in expansion_quest._fill"
  - Implementation: added a `{depth}` slot to `_fill` AND a seed-time `_distinguished_title` that appends `Depth {int(anchor.depth_score)}` when the title lacks an explicit `{depth}` slot (supports both the future YAML-slot path and today's slotless titles). Falls back to the anchor region id when a node has no depth_score (No Silent Fallbacks). The token is a pure function of the anchor region, so determinism holds (e2e `test_same_seed_same_quest` stays green).
  - Rationale: depth is the most player-meaningful "how deep does this one go" marker and is unique per descent in practice; the stored title is a working title the narrator reflavors (Amendment C).
  - Severity: minor
  - Forward impact: a YAML title may opt into `{depth}` explicitly later without double-appending.
- **AC-3 inference = inclusive expansion-id range (chose the "traversed projects" reading)**
  - Spec source: context-story-158-19.md, AC-3; TEA deviation "AC-3 pins the 'traversed projects' reading"
  - Spec text: "an expansion traversed/jumped-through during multi-region movement still projects its quest into quest_log — OR a documented landed-only decision"
  - Implementation: the frontier observer now projects every open expansion-quest thread whose expansion_id is in the inclusive range `[min(from_exp,to_exp), max(...)]`; a None/non-exp origin (entrance) falls back to the landed expansion only.
  - Rationale: implements the lead behavior TEA pinned (jumped-through expansions surface), not the OR-alternative; expansion ids are monotonic with descent so the range is the natural "what did we descend past" set.
  - Severity: minor
  - Forward impact: none — matches the pinned AC-3 test; resolution path (reached_region_ids) unchanged.

### Reviewer (audit)
- **TEA — AC-6 guarded by existing e2e** → ✓ ACCEPTED: reusing `test_expansion_quest_e2e` as the regression guard is sound; it stays green in this diff.
- **TEA — AC-3 pins the "traversed projects" reading** → ✓ ACCEPTED: Dev implemented exactly this reading (inclusive expansion-id range).
- **TEA — AC-1 pinned as content invariant** → ✓ ACCEPTED: eligibility + title-distinctness together enforce the player-visible promise; refactor-stable.
- **TEA — AC-2 drowned-domination floor uses depth 50** → ✓ ACCEPTED (superseded): Keith's mid-green random-dungeon design change overruled the drowned-narrowing framing; Dev's AC-2 rework replaces this test. Supersession documented and sound.
- **Dev — reworked AC-2 test to ≥5-themes/stratum** → ✓ ACCEPTED: matches Keith's documented design change + the shipped content (all themes {0,null}); GM-authorized. Residual: the module docstring still describes the overruled framing — LOW [DOC] finding, recommend cleanup.
- **Dev — updated big_bad title assertion for AC-4** → ✓ ACCEPTED: AC-4 deliberately changes title generation; the updated exact-match reflects the new behavior. (Minor brittleness to separator/token format noted, LOW.)
- **Dev — AC-4 distinguisher = depth token** → ✓ ACCEPTED: a valid choice from the AC's region/depth/ordinal menu; pure function of the anchor → determinism preserved. (Player-facing rawness mitigated by narrator reflavor — content reviewer should confirm.)
- **Dev — AC-3 inclusive expansion-id range** → ✓ ACCEPTED: implements the pinned reading; backtracking re-projection is an idempotent no-op (not a defect).

#### Undocumented (Reviewer-spotted)
- **Branch story-bleed:** the 158-19 branch carries `dab123ef fix(158-11)` (a separate backlog story with its own remote branch), absent from `origin/develop`. Not logged by SM/TEA/Dev. Severity: HIGH (merge-hygiene) — see the blocking delivery finding. Resolve before PR/merge.

## Branches

### sidequest-server
- **Branch:** feat/158-19-shallow-quest-template-variety
- **Strategy:** gitflow (develop base)

### sidequest-content
- **Branch:** feat/158-19-shallow-quest-template-variety
- **Strategy:** gitflow (develop base)
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server, `6bd033cc`):**
- `sidequest/dungeon/expansion_quest.py` — AC-3 traversed-expansion projection (inclusive from..to expansion-id range in the frontier observer); AC-4 `{depth}` slot in `_fill` + `_distinguished_title` seed-time depth token; `SignatureBinding.theme`; AC-5 `theme=` threaded to `quest_bound_span`.
- `sidequest/telemetry/spans/dungeon_quest.py` — AC-5 `theme` added to `SPAN_ROUTES[dungeon.quest.bound].extract`.
- `tests/dungeon/test_shallow_quest_template_variety.py` — AC-2 rework → `test_every_depth_offers_at_least_five_themes`; removed unused import/constant.
- `tests/dungeon/test_expansion_quest_select.py` — updated one big_bad title assertion for the AC-4 distinguisher.

**Content (sidequest-content, `8e330ce` — authored by GM):** `sunless_temple` re-themed built→labyrinthine (depthfirst/necropolis) resolving the roomcorridor look-gap; validated via `just content-validate caverns_and_claudes` (PASS, 0 errors).

**Tests:** 12 story/e2e + 523 dungeon GREEN (stable across 3 runs); ruff clean. AC-6 regression guard (`test_expansion_quest_e2e`) green. The ~10 full-suite reds are pre-existing/unrelated (WWN-dispatch/mutation/seam) — see Delivery Findings.

**Branches (pushed):**
- sidequest-server: `feat/158-19-shallow-quest-template-variety` @ `6bd033cc`
- sidequest-content: `feat/158-19-shallow-quest-template-variety` @ `8e330ce`

**Handoff:** To next phase (verify/review). PR creation deferred to SM finish.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 10 smells (1 medium, rest low); tests/lint green | confirmed 0 new-blocking, dismissed 2 (pre-existing), deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 8 (2 hi-conf, rest med/low) | confirmed 5 (LOW), dismissed 1 (false: tests green), deferred 0 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (2 hi-conf) | confirmed 2 (LOW [DOC]), dismissed 2 (low/no-op) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 5 violations (all LOW; 2 pre-existing) | confirmed 1 (LOW), dismissed 4 (2 pre-existing, 1 no-op, 1 cosmetic) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 8 confirmed (all LOW, non-blocking) + 1 BLOCKING delivery finding (branch story-bleed, code-external); 9 dismissed (with rationale)

## Reviewer Assessment

**Verdict:** APPROVED (code quality) — with ONE blocking merge-hygiene delivery finding for SM (branch story-bleed; not a code defect). No Critical/High code-severity findings.

**Scope reviewed:** the 158-19 changes only (`git diff dab123ef...HEAD` server + `origin/develop...HEAD` content). A third commit on the branch (`dab123ef fix(158-11)`) is OUT of 158-19 scope — see the blocking delivery finding.

### Data flow traced
Player region transition → `make_expansion_quest_observer._observer(from_region, to_region)` → computes inclusive expansion-id range → `reconcile_dungeon_quests_into_log` writes namespaced `dungeon:expN` QuestEntry rows into `snapshot.quest_log` (idempotent; never touches non-`dungeon:` entries) → resolve unchanged. Theme flow: `select_signature` → `deepest.theme` → `SignatureBinding.theme` → `seed_expansion_quest` passes `theme=b.theme` to `quest_bound_span` (**attrs) → span attribute `theme` → `SPAN_ROUTES[dungeon.quest.bound].extract` surfaces it to the GM panel. Safe: all inputs are internal game ids (no user-controlled boundary); no SQL/path/deserialization surface in the diff.

### Pattern observed
AC-4 distinguisher is a pure function of the anchor region (`_depth_token` → `Depth {int(depth_score)}`, falls back to region id) — preserves determinism (`test_same_seed_same_quest` green). `_distinguished_title` supports both a future YAML `{depth}` slot and today's seed-time append without double-appending. `expansion_quest.py:54,69`.

### Error handling
`resolve_expansion_quests` raises loudly on missing `expansion_id` (`expansion_quest.py:333`). `_depth_token` never returns blank (No Silent Fallbacks, `expansion_quest.py:58-66`). New code adds no swallowed exceptions.

### Confirmed findings (all LOW / non-blocking)
- `[DOC]` **Stale module docstring** — `tests/dungeon/test_shallow_quest_template_variety.py:1-25`. Lists original "root cause #1" (narrow drowned_cavern's band {0,60}) which Keith OVERRULED mid-story, and says "tests are RED until content lands" though content shipped (`cf9a9eb`/`8e330ce`) and the suite is green. Reworked `test_every_depth_offers_at_least_five_themes` asserts the opposite of root-cause-#1. Misleading to future readers. Recommend a docstring refresh (LOW).
- `[TEST]` **AC-3 test under-asserts** — `test_traversed_expansions_project_into_quest_log` asserts {exp2..exp5} but the observer also projects exp1 (the from-expansion); exp1's projection is untested, and the check is keys-only (no status/title quality). Core behavior IS pinned (intermediate expansions surface); e2e covers status. LOW.
- `[TEST]` **AC-4 / determinism tests robustness** — `test_same_theme_expansions_produce_distinct_quest_titles` doesn't assert exactly-one-thread-per-store or non-empty titles; the e2e determinism test doesn't assert the depth token is *present* (only that both sides agree). Token presence IS covered by `test_big_bad_…` (`"— Depth 30"`) and the distinctness test. LOW.
- `[TEST]` **AC-5 span test data coherence** — `test_quest_bound_span_carries_bound_theme` uses bone_crypt nodes + the drowned_cavern template; correct (theme comes from the deepest node, not the template) but reads as a mismatch. Cosmetic. LOW.
- `[RULE]`/`[TYPE]` **`quest_bound_span` theme via `**attrs`** — `theme` is not a typed keyword param (`dungeon_quest.py:60`); a typo at a future call site wouldn't be caught by pyright. Consistent with the helper's pre-existing `**attrs` design; high test coverage. LOW.

### Dismissed (with rationale)
- `[SILENT]`/`[RULE]` big_bad `name` → "the master of this place" fallback, and `_expansion_id_of` `except ValueError: return None` — **PRE-EXISTING** (verified: not in the `+` diff; 158-19 only added a *call site* to `_expansion_id_of`). The big_bad path is also unexercised by current content (all 8 themes use `reach_deep`). Out of 158-19 scope; flagged as a pre-existing note, not a story blocker.
- `[TEST]` "RED tests need `@pytest.mark.xfail`" — **false**: content shipped, preflight confirms 523 dungeon tests green (incl. these). The real residue is the stale docstring (above).
- `[RULE]` AC-3 backtrack direction — re-projecting expansions on an upward move is a **no-op**: reconcile is idempotent and those quests were already projected on descent; a visited expansion's quest belongs in the log regardless of direction. Not a defect.
- `[TEST]` 5-theme floor samples 4 strata — all 8 themes are `{0,null}` (eligible everywhere); content is validator-checked separately. LOW, accepted.

### Disabled-subagent domains (self-assessed)
- `[EDGE]` Boundary conditions: reviewed the range math myself — `sorted((from_exp,to_exp))` handles either direction; `to_exp is None` (entrance) → empty set (no projection), correct; None `from_region` → landed-only. No unhandled boundary.
- `[SEC]` Security: no user-controlled input in the diff; all ids are internal; no SQL/path/eval/deserialization. No concern.
- `[TYPE]` Type design: `SignatureBinding` gained a required `theme: str`; all 3 construction sites supply it (verified). `_fill`/`_distinguished_title`/`_depth_token` fully annotated. Sound.
- `[SIMPLE]` Simplicity: `_distinguished_title`'s `if "{depth}" not in template_title and token` — `token` is always non-empty so `and token` is redundant, but harmless and defensive. No over-engineering.

### Rule Compliance (lang-review/python.md — exhaustive)
1. Silent exceptions: new code adds none. `_expansion_id_of` swallow is pre-existing. **PASS (new code)**.
2. Mutable defaults: `_fill(depth: str = "")` immutable; no mutable defaults added. **PASS**.
3. Type annotations: all new public/helper fns fully annotated. One LOW: `theme` via `**attrs`. **PASS**.
4. Logging: module is intentionally OTEL-only (spans, not logs) per ADR-031/090/103; AC-5 adds the span attribute. **PASS**.
5. Path handling: only `_world_dir()` uses `Path(...).resolve()`/`parents`; no `open()` without encoding. **PASS**.
6. Test quality: no vacuous asserts, no unreasoned skips, no source-grep wiring; real behavior/OTEL/observer tests. LOW under-assertions noted. **PASS**.
7. Resource leaks: spans used as context managers; in-memory sqlite in tests is resource-free. **PASS**.
8. Unsafe deserialization: none. **PASS**.
9. Async pitfalls: all changed code is synchronous. **PASS**.
10. Import hygiene: specific imports, `from __future__ import annotations`, `__all__` present in dungeon_quest.py. **PASS**.
11. Input validation: no untrusted boundary in the diff. **PASS**.
12. Dependency hygiene: no dependency changes. **PASS**.
13. Fix-introduced regressions: `_fill` signature change is backward-compatible; `SignatureBinding.theme` supplied at all sites. **PASS**.

### Devil's Advocate
Argue the code is broken. (1) **The depth token leaks a raw Plan-3 unit** ("Depth 30") to a player-facing title — the spec explicitly says depth_score is "NOT player-facing." Counter: the stored title is a working title the narrator reflavors at surface (Amendment C); the AC menu explicitly offered "depth" as a token; acceptable, but a content reviewer should confirm the narrator actually reflavors it rather than surfacing it raw. (2) **The inclusive-range projection could flood the quest log** — a jump across many expansions projects every one in `[lo,hi]`, including expansions the player never has a thread for. Counter: reconcile filters by open-thread membership, so only expansions with real threads project; harmless. (3) **Backtracking re-projects shallower expansions** — semantically odd. Counter: idempotent + already-present; no duplicate, no harm. (4) **A malformed region id silently yields None** and skips projection. Counter: pre-existing, internal ids only; a corrupted id is a programming error elsewhere. (5) **The branch carries an unrelated story's commit** — this is the real landmine: a confused merge would ship backlog story 158-11's WIP under 158-19's PR. This is caught and flagged as blocking. (6) **A stale docstring** would mislead the content-author picking up the AC-2 follow-on into thinking they must "narrow drowned_cavern" — the exact overruled approach. Worth fixing. None of (1)-(4) are correctness defects; (5) is a merge-hygiene blocker handed to SM; (6) is a LOW doc cleanup. The code does what the ACs require, with OTEL wiring verified end-to-end.

### Verdict rationale
No Critical/High code-severity findings. AC-3/4/5 implemented and behaviorally tested; AC-6 regression guard green; content validated separately (GM). The one blocking item (branch story-bleed) is code-external and SM-owned. **APPROVED** for SM finish, gated on resolving the branch bleed before PR/merge.

**Handoff:** To SM for finish-story (resolve branch bleed first).