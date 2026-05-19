---
story_id: "54-5"
jira_key: null
epic: "54"
workflow: "trivial"
branch: "feat/54-5-beneath-sunden-settlement-entities-backfill"
---
# Story 54-5: Content backfill — caverns_and_claudes/beneath_sunden settlement rooms — add entities[] to existing descriptions, validator-clean

## Story Details
- **ID:** 54-5
- **Jira Key:** None (personal project, no Jira)
- **Workflow:** trivial
- **Epic:** 54 (Persistent Location Descriptions)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-19T21:06:31Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-19 | 2026-05-19T20:33:13Z | 20h 33m |
| implement | 2026-05-19T20:33:13Z | 2026-05-19T20:55:37Z | 22m 24s |
| review | 2026-05-19T20:55:37Z | 2026-05-19T21:03:27Z | 7m 50s |
| implement | 2026-05-19T21:03:27Z | 2026-05-19T21:04:44Z | 1m 17s |
| review | 2026-05-19T21:04:44Z | 2026-05-19T21:06:31Z | 1m 47s |
| finish | 2026-05-19T21:06:31Z | - | - |

## Story Context

**Scope:** Content backfill task to add `entities[]` typed descriptors to existing settlement room YAML files in the caverns_and_claudes/beneath_sunden world.

**Upstream Materials:**
- Story 54-3 (merged 2026-05-19, PR #352) — `pf validate locations` validator with well-formedness, binding resolution, and prose-manifest coherence checks
- Story 55-1 (merged 2026-05-19, PR #350) — procedural Beneath Sünden megadungeon materialized 12 settlement rooms with auto-generated entities[] already present (exp001.r0-r5, exp002.r0-r5)

**Key Finding:** The beneath_sunden/rooms/ directory was populated by story 55-1's procedural materialization, and all 12 settlement rooms currently have well-formed entities[] with proper bindings and affordances. This story's task is to verify these are validator-clean and complete the content backfill pattern from story 54-4 (glenross landmark conversion).

**In-Scope Material:**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/` — 12 settlement YAML files (exp001.r0-r5, exp002.r0-r5)

## Delivery Findings

No upstream findings at setup time. All entities are present and well-formed from the procedural generation. Validator availability verified (PR #352 merged).

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **Gap** (non-blocking): SM-setup briefed the story as "verify 12 settlement room YAMLs are validator-clean" based on the untracked `genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/` directory left on disk from a 55-1 materializer run. The actual backfill target was `cartography.yaml` — the two authored surface regions (`ropefoot`, `the_dropmouth`) had `landmarks[]` but no `entities[]`, mirroring 54-4's tea_and_murder/glenross gap. Affects `sprint/context/context-story-54-5.md` (if it exists) and the story description in current-sprint.yaml — the scope sentence should read "convert beneath_sunden cartography landmarks[] to typed entities[]" rather than "settlement rooms". *Found by Dev during implementation.*
- **Gap** (non-blocking): The `rooms/` directory at `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/` contains 12 YAMLs (exp001.r0-r5, exp002.r0-r5) produced by 55-1's procedural materializer. They are untracked, schema-correct, and validator-passing (0 errors / 122 warnings — PROSE_DRIFT only). Per `cartography.yaml`'s preamble comments, the deep is "GENERATED, not authored" and the procedural lane is intentionally fenced out of static authoring. These files should either be added to `.gitignore` for `worlds/*/rooms/` OR the materializer should write to a runtime cache outside the content tree. Affects `sidequest-content/.gitignore` (or `sidequest-server/sidequest/game/...` materializer output path). *Found by Dev during implementation.*
- **Gap** (non-blocking): The `pf validate locations` adapter is still not registered — `pf validate` lists no `locations` subcommand. The validator must be invoked as `uv run python -m sidequest.cli.validate locations`. This was an explicit deferred finding from 54-3 (pennyfarthing-dist branch could not be created in that session). A 1-pt follow-up to wire the pf adapter would let CI gate content packs against `pf validate locations`. Affects `pennyfarthing/pennyfarthing-dist/` (pf validate registration) and `justfile` `check-all` recipe. *Found by Dev during implementation.*
- **Improvement** (non-blocking): caverns_and_claudes/pack.yaml has no `generic_allowlist[]` block. Adding generic English nouns (wall, ceiling, water, ankle, knee, rope, road, stone, etc.) plus cavern-vocabulary proper nouns (Black, Something, One, Rope) would silence 122 PROSE_DRIFT warnings across beneath_sunden, leaving only meaningful coherence issues. This is the natural completion of 54-4's deferred allowlist authoring, now that 54-3's validator consumes the field. Affects `sidequest-content/genre_packs/caverns_and_claudes/pack.yaml`. *Found by Dev during implementation.*
- **Question** (non-blocking): The Ropefoot region prose names a "winch-keeper" stationed at the winch-house. Per 54-4's policy ("no NPCs introduced just to satisfy bindings"), I did not bind the entity to an NPC and beneath_sunden has no `npcs.yaml`. If the camp warrants a warm cast (winch-keeper, fire-tender, etc.) the natural place to author it is alongside this story's siblings — but it isn't this story's scope. Affects `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml` (would need to be created). *Found by Dev during implementation.*

### Reviewer (code review)

- **Improvement** (non-blocking): Systemic affordance vocabulary drift continues. After 54-4 flagged it in glenross and deferred to a follow-up audit, 54-5 introduces three more bare-verb instances (`warm`, `rig`, `descend` — one being rejected in this story, two carried forward to the systemic audit). Each story's contribution is small; the population is growing. A dedicated story to (a) document the bare-vs-compound convention as a YAML schema rule, and (b) sweep all wired packs for compliance, would close the gap. Affects `sidequest-server/sidequest/protocol/models.py::LocationEntity.affordances` (validator addition) and all `cartography.yaml` files under wired packs. *Found by Reviewer during code review.*
- **Gap** (non-blocking): No per-pack content-shape wiring test exists for any world. Both 54-4 (glenross) and 54-5 (beneath_sunden) ship without an assertion that authored `entities[]` survives the round-trip from YAML → Pydantic → live `GenrePack`. The right home is a new test (e.g. `tests/genre/test_authored_entities_present.py`) that iterates wired packs and asserts each region has the expected entity ids. Per CLAUDE.md "Every Test Suite Needs a Wiring Test" — this is now a back-pressure violation for the whole epic, not a 54-5-specific issue. Affects `sidequest-server/tests/genre/` (new test file). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `rooms/` directory at `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/` is untracked-but-on-disk in both clones. Dev already filed this as a gitignore/cache-location gap. Confirming the priority: this is a near-term papercut — every clone of the repo with that materializer run sitting on disk will see noise in `git status`. A `.gitignore` rule for `worlds/*/rooms/` under packs whose cartography declares `navigation_mode: region` would be the minimal fix. Affects `sidequest-content/.gitignore`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (2 Gap, 0 Conflict, 1 Question, 0 Improvement)
**Blocking:** None

- **Gap:** The `rooms/` directory at `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/rooms/` contains 12 YAMLs (exp001.r0-r5, exp002.r0-r5) produced by 55-1's procedural materializer. They are untracked, schema-correct, and validator-passing (0 errors / 122 warnings — PROSE_DRIFT only). Per `cartography.yaml`'s preamble comments, the deep is "GENERATED, not authored" and the procedural lane is intentionally fenced out of static authoring. These files should either be added to `.gitignore` for `worlds/*/rooms/` OR the materializer should write to a runtime cache outside the content tree. Affects `sidequest-content/.gitignore`.
- **Question:** The Ropefoot region prose names a "winch-keeper" stationed at the winch-house. Per 54-4's policy ("no NPCs introduced just to satisfy bindings"), I did not bind the entity to an NPC and beneath_sunden has no `npcs.yaml`. If the camp warrants a warm cast (winch-keeper, fire-tender, etc.) the natural place to author it is alongside this story's siblings — but it isn't this story's scope. Affects `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/npcs.yaml`.
- **Gap:** No per-pack content-shape wiring test exists for any world. Both 54-4 (glenross) and 54-5 (beneath_sunden) ship without an assertion that authored `entities[]` survives the round-trip from YAML → Pydantic → live `GenrePack`. The right home is a new test (e.g. `tests/genre/test_authored_entities_present.py`) that iterates wired packs and asserts each region has the expected entity ids. Per CLAUDE.md "Every Test Suite Needs a Wiring Test" — this is now a back-pressure violation for the whole epic, not a 54-5-specific issue. Affects `sidequest-server/tests/genre/`.

### Downstream Effects

Cross-module impact: 3 findings across 3 modules

- **`sidequest-content`** — 1 finding
- **`sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden`** — 1 finding
- **`sidequest-server/tests`** — 1 finding

### Deviation Justifications

1 deviation

- **Story scope reinterpreted: cartography.yaml authoring, not rooms[] verification.**
  - Rationale: The cartography.yaml work is what mirrors 54-4 exactly. The rooms/ artifacts represent a separate gap (materializer output committal policy, see Delivery Findings) and should not be conflated with hand-authored content.
  - Severity: minor
  - Forward impact: minor — story description in current-sprint.yaml should be amended at the SM finish step or in a future correction; reviewer should confirm the scope reinterpretation before merge.

## Design Deviations

None at setup time.

### Dev (implementation)

- **Story scope reinterpreted: cartography.yaml authoring, not rooms[] verification.**
  - Spec source: Session `## Story Context` — "verify these are validator-clean and complete the content backfill pattern from story 54-4 (glenross landmark conversion)"
  - Spec text: "12 settlement YAML files (exp001.r0-r5, exp002.r0-r5)" were named in setup as the in-scope material
  - Implementation: Authored `entities[]` on the two regions of `cartography.yaml` (ropefoot + the_dropmouth) — the actual 54-4-mirror target. The `rooms/` YAMLs are runtime-generated materializer artifacts and were left untracked. The 54-4 pattern is "convert authored `landmarks[]` to typed `entities[]`" — the procedurally-generated rooms don't fit that pattern because their entities[] are auto-generated, not hand-authored.
  - Rationale: The cartography.yaml work is what mirrors 54-4 exactly. The rooms/ artifacts represent a separate gap (materializer output committal policy, see Delivery Findings) and should not be conflated with hand-authored content.
  - Severity: minor
  - Forward impact: minor — story description in current-sprint.yaml should be amended at the SM finish step or in a future correction; reviewer should confirm the scope reinterpretation before merge.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` — added `entities[]` block to both regions (`ropefoot`, `the_dropmouth`). 6 total entities authored: 6 `real_object` (all with `location_feature` bindings using `<region>_<noun>` ref convention), 0 `flavor_only`, 0 `yes_and`. `landmarks[]` preserved on both regions per spec §10.

**Verification:**
- `uv run python -m sidequest.cli.validate locations --genre-packs-root .../caverns_and_claudes` → **0 errors, 122 warnings** (all warnings are PROSE_DRIFT, none referencing the two authored regions' entities — they're generic English in unrelated rooms/ content out of scope).
- Pydantic strict pack load: all 6 entities parse, all 6 have non-null bindings, all binding refs are unique within their region.
- Cross-story: matches the AC-5 contract `validate_locations_in_world` exercised by 55-1's integration test.

**Tests:** 6782/0/396 (server suite, no drift from baseline). Duration 2m05s.

**Branch:** `feat/54-5-beneath-sunden-settlement-entities-backfill` on `sidequest-content` (pushed; commit `fab31a6`).

**Repo scope:** content-only (matches session REPOS field). No server/UI changes.

**Self-Review (judgment checks):**
- [x] Code wired to consumers — `Region.entities[]` is the field 54-7 overlays and 54-9 UI panel will read; data is loaded by the existing `CartographyConfig` loader path (no new wiring needed for content).
- [x] Follows project patterns — mirrors 54-4 conventions (real_object + location_feature binding, `<region>_<noun>` ref, compound-verb affordances).
- [x] All ACs met within reinterpreted scope (see Design Deviations).
- [x] No error handling needed — content YAML, validator-enforced.

**Handoff:** To Portia (reviewer) for trivial-workflow review phase. Reviewer should focus on:
(a) the scope-reinterpretation deviation (cartography.yaml vs rooms/);
(b) entity authoring style — labels match landmark names, ids are kebab-snake unique within region;
(c) binding ref convention `<region>_<noun>` consistency;
(d) affordance vocabulary — used compound verbs (`listen_pawl`, `read_names`, `chalk_descent_time`) per the 54-4 Reviewer "specific narrative beat" recommendation;
(e) whether to also act on Delivery Findings now (especially the rooms/ gitignore gap and the deferred generic_allowlist).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — all mechanical checks pass (0 errors, Pydantic load returns expected entity counts) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings (`workflow.reviewer_subagents.edge_hunter=false`) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 2 | 1 confirmed (HIGH→downgraded LOW, inherited from 54-4 deferral, not net-new), 1 deferred (MEDIUM systemic — follow-up story per 54-4 precedent) |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | 1 dismissed (commit body "Convert" wording matches 54-4 commit convention; not stale, just imprecise verb — see rationale) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings (content-only YAML, no type design surface) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings (content-only YAML, no security surface) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings (no code complexity surface) |
| 9 | reviewer-rule-checker | Yes | findings | 2 | 1 confirmed blocking (warm bare verb — mirrors 54-4 `receive` reject), 1 deferred (rig/descend warnings — systemic 54-4 carry-forward) |

**All received:** Yes (4 returned, 5 skipped per settings, 3 confirmed findings)
**Total findings:** 2 confirmed (1 blocking, 1 inherited), 1 dismissed (rationale below), 2 deferred (systemic, follow-up)

### Rule Compliance (CLAUDE.md + project conventions)

The diff is content-only YAML; Python lang-review rules do not apply to data files. Project rules from CLAUDE.md (orchestrator + content + server), SOUL.md, ADR-109, and the 54-4 reviewer's documented affordance convention apply.

| Rule | Source | Check Target | Status |
|------|--------|--------------|--------|
| 1. No Stubbing | CLAUDE.md | 6 entities have live consumer (resolve_location_entity tool via 54-6) | ✓ all 6 compliant |
| 2. Verify Wiring | CLAUDE.md | cartography→loader→Region.entities→tool→narrator chain end-to-end | ✓ all 6 compliant |
| 3. Wiring test per suite | CLAUDE.md | per-pack content shape assertion | ✗ — gap inherited from 54-4 deferral, not net-new; deferred to follow-up wiring test story |
| 4. No Silent Fallbacks | CLAUDE.md | extra=forbid on LocationEntity[Binding]; ValidationError on malformed | ✓ all 6 compliant |
| 5. Diamonds and Coal | SOUL.md | tier reflects narrative weight (all 6 are real_object, all warrant it per prose) | ✓ all 6 compliant |
| 6. yes_and never authored | ADR-109 | runtime-only tier | ✓ all 6 compliant (0 yes_and) |
| 7. Genre Truth | SOUL.md | affordances are setting-appropriate verbs | ✓ all 6 compliant |
| 8. <region>_<noun> ref | 54-4 convention | binding.ref naming + real_object has binding | ✓ all 6 compliant; id==ref everywhere |
| 9. Compound-verb affordance | 54-4 reviewer | "specific narrative beat" over bare verbs | ✗ 1 violation (`warm`), 2 warnings (`rig`, `descend`) |
| 10. Unique entity ids | 54-4 convention | within-region uniqueness | ✓ ropefoot 4/4 unique, the_dropmouth 2/2 unique, cross-region 6/6 unique |

### Devil's Advocate

Suppose this content ships and three months later a player at Ropefoot says "I warm myself by the fire." The narrator consults the entity manifest, sees `ropefoot_kept_fire.affordances = [warm, tend_fire]`, and faces an interpretive problem: what does "warm" mean? Warm hands? Warm the body? Warm an object held to the fire? The bare verb gives the narrator no object to anchor on, so it falls back on default interpretation — which in a Claude-driven narration system means improvisation, exactly the failure mode SOUL.md's "OTEL is a lie detector" principle was written to catch. Compare with `tend_fire`, the sibling affordance: the narrator knows the object (the fire) and the action (tending — feeding fuel, stirring embers), and can ground a specific beat. This is not theoretical concern — the 54-4 reviewer rejected glenross for the exact same problem (`manse.parlour.affordances: [receive]` was rejected because `receive` had no clear player-side action). The convention exists because experience showed bare verbs degrade narration quality.

Now suppose a player asks "Can I take the rope?" The validator passes — `the_dropmouth_rope` has `descend` as an affordance, which sounds like the player taking the rope to descend. But `descend` as written is a bare verb whose implied object (the shaft) is recoverable only from region context. A narrator under context pressure (which happens — see ADR-098, ADR-111) might miss the implicit object and offer the player "descend" as a stand-alone action with no destination. Less acute than `warm` because the shaft is the only thing descendable here, but a vector for narrator confusion.

Counter-argument the dev would make: "Compound verbs reduce vocabulary expressiveness; bare verbs let the narrator pick the surface form." That's not how compound verbs work in this manifest — they're tokens that flag the narrator's attention, not user-visible labels. The narrator paraphrases. The 54-4 reviewer's convention is sound, and the present diff has one clear violation and two near-misses.

Worst case: this ships with `warm` unfixed, and 6 months from now a vocabulary audit story (the 54-4 deferred systemic finding) finds 30+ bare-verb instances across content, of which `warm` is one. Cost of fixing now: 1 line edit. Cost of fixing later in a sweep: the same line edit, in a batch of 30. Either is cheap. But the **precedent** matters — every story that ships with a known bare-verb violation makes the systemic audit harder to justify.

## Reviewer Assessment

**Verdict:** REJECTED (green rework — single content-quality fix, no test changes)

**Data flow traced:** `cartography.yaml` → `_load_single_world` → `_load_cartography` → `CartographyConfig.model_validate` → `Region.model_validate` → `LocationEntity.model_validate` (per region). 6 new entities ride the same schema path that 54-4 established for glenross. Live downstream consumer: `resolve_location_entity` tool (sidequest-server/sidequest/agents/tools/resolve_location_entity.py:104, `_authored_entities_for(ctx, region_id)` walks `ctx.genre_pack.worlds[world_id].cartography.regions[region_id].entities`). Pydantic strict-load confirms `{'ropefoot': 4, 'the_dropmouth': 2}`. 54-9 UI panel and 54-7 overlay model will consume `entities[]` directly once they ship.

**Pattern observed:** Mirrors 54-4 exactly — additive `entities[]` blocks alongside preserved `landmarks[]`, all 6 entities `real_object` with `location_feature` bindings, ref convention `<region>_<noun>` with id==ref. ropefoot 4/4 + the_dropmouth 2/2 = 6/6 well-formed. cartography.yaml:78 (ropefoot) and :156 (the_dropmouth). Pattern fidelity is otherwise strong.

**Error handling:** N/A — pure content. `extra="forbid"` on `LocationEntity` and `LocationEntityBinding` is the gate; malformed YAML raises `ValidationError` at load. No silent fallback paths.

**Severity table — findings actionable in this story:**

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW] [RULE][DOC] | `ropefoot_kept_fire.affordances` contains bare verb `warm`; sibling `tend_fire` on the same entity demonstrates the compound form. Per the 54-4 reviewer's documented "specific narrative beat" convention (bare verbs = unstructured narrator hints; compound verbs = grounded beats). Mirrors 54-4's `manse.parlour.receive` rejection. Narrator-quality risk per Devil's Advocate analysis above. | `genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` (ropefoot entities, the `warm` line under `ropefoot_kept_fire.affordances`) | Replace `warm` with `warm_by_fire` (preferred — matches `tend_fire` idiom) or `warm_hands` (also acceptable). One-line edit. |

**Dismissed findings (with rationale):**
- [DOC] **Commit body's opening "Convert landmarks[] to typed entities[]" verb is imprecise (additive, not strict conversion)** — DISMISSED. The exact same wording appears verbatim in 54-4's merged commit ec50f2f ("convert 12 region landmarks[] to typed entities[]"). It is an established Pennyfarthing-convention idiom for this story type. The body's subsequent sentence ("landmarks[] preserved per spec §10 (additive backfill, no behavior change until 54-7/54-9 wire the runtime consumers)") clarifies the additive semantics. Not stale, just terse — consistent with established repo voice.

**Deferred to Delivery Findings (non-blocking, future story):**
- [RULE] `ropefoot_rigging_benches.rig` bare verb (rule-checker WARN, line ~116) — contextually-recoverable object (a delver's kit); lower severity than `warm`. Defer to the 54-4-flagged systemic affordance vocabulary audit.
- [RULE] `the_dropmouth_rope.descend` bare verb (rule-checker WARN, line ~176) — structurally special seam action into the procedural deep, implied object is the shaft from region context; lower severity than `warm`. Defer to the same systemic audit.
- [TEST] No per-pack content-shape assertion that `pack.worlds["beneath_sunden"].cartography.regions["ropefoot"].entities` is non-empty (test-analyzer HIGH downgraded to LOW). Same gap was logged by 54-4 reviewer and deferred to 54-6; 54-6 shipped tool-level wiring tests but not content-level assertions. Net-new gap is zero — this is a 54-4 carry-forward. Right place for the fix is a cross-world content-shape sweep test, not in this 2-pt trivial story.
- [TEST] Affordance vocabulary is `list[str]` with no validator (test-analyzer MEDIUM) — architectural concern across LocationEntity globally, not story-scoped. Same as 54-4's "systemic affordance vocabulary drift" deferral.

**Handoff:** Back to Dev (Puck) for the single lint-grade content fix listed above. Suite green throughout — this is a `green rework` cycle (no test changes needed). Estimated effort: 1 line edit + recommit + repush + Portia recheck.

### Design Deviation Audit

The session's `## Design Deviations` section contains one Dev entry:

- **Story scope reinterpreted: cartography.yaml authoring, not rooms[] verification.** → **✓ ACCEPTED by Reviewer.**
  Rationale: The reinterpretation is sound and necessary. The SM-setup briefing was based on the untracked `rooms/` directory left on disk from a 55-1 materializer run, but that content is procedurally generated (per cartography.yaml's preamble: "no dungeon region exists below the_dropmouth by design", "The deep is GENERATED, not authored here"). Hand-authoring the `landmarks[]→entities[]` conversion on the two surface regions is the actual 54-4 mirror target. The `rooms/` artifacts represent a separate gap (gitignore policy for materializer output) appropriately surfaced as a Delivery Finding rather than conflated with this story's scope. Dev's judgment was correct.

### Reviewer (audit)
- No undocumented spec deviations detected. The dev's single deviation entry covers the scope reinterpretation completely.

## Dev Assessment (rework round 1)

**Reviewer findings addressed:** The single LOW [RULE][DOC] blocking finding from Portia's REJECTED verdict landed as a single one-line commit (`5aa4937`).

**Files Changed (rework):**
- `sidequest-content/genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` — 1 insertion, 1 deletion:
  1. `ropefoot_kept_fire.affordances`: `warm` → `warm_by_fire`. Matches sibling `tend_fire` compound idiom and 54-4's "specific narrative beat" convention.

**Verification (re-run):**
- Validator: **0 errors, 122 warnings** (PROSE_DRIFT unchanged from round-0).
- Pydantic strict-load confirms `pack.worlds['beneath_sunden'].cartography.regions['ropefoot'].entities[1].affordances == ['warm_by_fire', 'tend_fire']`.
- All 6 entities still parse; ids and bindings unchanged.

**Dismissed-finding response:** Two reviewer warnings (`rig` on ropefoot_rigging_benches, `descend` on the_dropmouth_rope) were explicitly deferred by Portia to the systemic affordance-vocabulary follow-up story she logged as a Reviewer Delivery Finding. No code change needed for either — the deferral is documented and the precedent matches 54-4's "systemic affordance vocabulary drift" deferral.

**Branch:** `feat/54-5-beneath-sunden-settlement-entities-backfill` on `sidequest-content` (rework commit `5aa4937` pushed; prior commit `fab31a6` is the bulk backfill).

**Handoff:** Back to Portia (reviewer) for re-verification of the one-line fix. Round-trip count is now 1.

## Reviewer Assessment (rework round 1)

**Verdict:** APPROVED

**Data flow traced:** Rework diff is content-only; same load path as round-0 (`CartographyConfig.model_validate` → `Region.model_validate` → `LocationEntity.model_validate`). 6/6 entities still validate; the single affordance swap only changes one string token inside an existing `list[str]` field — schema shape unchanged.

**Pattern observed:** Surgical 1-edit cleanup at `genre_packs/caverns_and_claudes/worlds/beneath_sunden/cartography.yaml` (line 98 — the `warm` → `warm_by_fire` swap inside `ropefoot_kept_fire.affordances`). Net diff: +1 / -1. No collateral, no scope creep, no new YAML structure. Now matches sibling `tend_fire` idiom and 54-4's documented compound-verb convention.

**Error handling:** N/A — pure content; schema is the gate; Pydantic strict load passes; validator returns 0 errors.

**Round-0 findings closure status:**
- 1 actionable [LOW] [RULE][DOC] finding (`warm` bare verb) → CLOSED by rework commit `5aa4937`.
- 1 dismissed finding (commit body "Convert" wording) → still correctly dismissed (54-4 idiom).
- 4 deferred findings (rig/descend bare-verb warnings, affordance vocab unpinned, content-shape wiring test, rooms/ gitignore) → still appropriately deferred to follow-up stories; surfaced as Reviewer Delivery Findings.

**Round-1 verification (preflight re-run):**
- HEAD `5aa4937` on `feat/54-5-beneath-sunden-settlement-entities-backfill`, pushed to origin.
- Validator: 0 errors, 122 warnings (PROSE_DRIFT unchanged — non-blocking, all pre-existing).
- Pydantic strict-load: `ropefoot_kept_fire.affordances == ['warm_by_fire', 'tend_fire']`.
- Scope: 1 file changed, +1/-1; no other touched lines.

**Handoff:** To SM (Prospero) for the finish phase. Branch `feat/54-5-beneath-sunden-settlement-entities-backfill` on `sidequest-content` is ready to PR-and-merge: two commits — `fab31a6` (bulk backfill, +56) + `5aa4937` (rework, +1/-1). Validator stayed at 0 errors throughout.

## Sm Assessment

**Setup Complete:** Yes
**Story Selected:** 54-5 — Content backfill, caverns_and_claudes/beneath_sunden settlement rooms
**Workflow:** trivial (phased: setup → implement → review → finish)
**Branch:** `feat/54-5-beneath-sunden-settlement-entities-backfill` (in sidequest-content)
**Repos:** content
**Jira:** N/A — SideQuest is a non-Jira project per project policy

**Key Context for Dev:**
- 54-3 validator (`pf validate locations`) is the verification tool — merged today 2026-05-19, PR #352
- 55-1 already materialized all 12 settlement room YAMLs with auto-generated `entities[]` (exp001.r0-r5, exp002.r0-r5)
- Story scope is verification + any cleanup the validator surfaces, NOT initial authoring
- Pattern to mirror: story 54-4 (glenross landmark conversion)

**Verification Path:** Run `pf validate locations` against the beneath_sunden world; fix any failures; ensure CI-clean.

**Handoff:** To Puck (dev) for implement phase.