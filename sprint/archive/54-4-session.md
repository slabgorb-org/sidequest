---
story_id: "54-4"
jira_key: ""
epic: "54"
workflow: "trivial"
---
# Story 54-4: Content backfill: tea_and_murder/glenross — convert 12 region landmarks[] to typed entities[], add bindings, validator-clean

## Story Details
- **ID:** 54-4
- **Epic:** 54 (Persistent Location Descriptions)
- **Title:** Content backfill: tea_and_murder/glenross — convert 12 region landmarks[] to typed entities[], add bindings, validator-clean
- **Points:** 2
- **Workflow:** trivial
- **Type:** chore
- **Priority:** p1
- **Repos:** content (sidequest-content)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-19T14:04:33Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-19 | 2026-05-19T13:15:47Z | 13h 15m |
| implement | 2026-05-19T13:15:47Z | 2026-05-19T13:35:17Z | 19m 30s |
| review | 2026-05-19T13:35:17Z | 2026-05-19T13:48:26Z | 13m 9s |
| implement | 2026-05-19T13:48:26Z | 2026-05-19T13:59:26Z | 11m |
| review | 2026-05-19T13:59:26Z | 2026-05-19T14:04:33Z | 5m 7s |
| finish | 2026-05-19T14:04:33Z | - | - |

## Sm Assessment

**Scope:** Pure content backfill in `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/`. Convert 12 region `landmarks[]` (string array) to typed `entities[]` (the persistent-location schema landed by 54-1), add bindings, and make the result `pf validate locations`-clean.

**Workflow:** trivial → setup → implement → review → finish. Dev handles implement.

**Why this is genuinely trivial:**
- No new code, no new schema — schema lives upstream of this story (54-1 ADR / Epic 54 spec).
- The validator (54-3) is **not yet shipped**, so "validator-clean" here means "passes the schema check that exists today" — be ready for a follow-up touch-up once 54-3 lands.
- Content-only diff, no server/UI wiring.

**Key files Dev should locate first:**
- Glenross world directory: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/`
- The region YAML(s) containing `landmarks[]` (12 entries total across regions)
- An existing converted world for pattern reference — check beneath_sünden (54-5 is the sister story) or whichever world already ships `entities[]`
- Epic 54 spec / ADR-109 (Persistent Location Descriptions + Mechanical Manifest)

**Acceptance posture:**
- All 12 landmarks present as typed `entities[]` entries with bindings
- `pf validate locations` (or current schema check) passes against glenross
- No regression: glenross still loads in genre pack loader

**Risks / heads-up:**
- If a landmark has no obvious typed-entity analog, log it as a Delivery Finding rather than inventing a type.
- Sister story 54-5 (beneath_sünden) and validator 54-3 may land in parallel — branch is `feat/54-4-glenross-landmarks-to-entities` on `sidequest-content` off `develop`.

**Handoff:** Puck → trivial implement phase.

## Dev Assessment

**Implementation Complete:** Yes (within scope — see Design Deviations re: deferred allowlist)

**Files Changed:**
- `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` — added `entities[]` block to all 14 regions, inserted after `landmarks[]` (preserved per spec §10) and before `rivers[]`. 114 total entities authored: 88 `real_object` (all with bindings — 75 `location_feature`, 13 `npc`), 26 `flavor_only`, 0 `yes_and` (correctly never used in authored content).

**Tests:** 6586/0 passing, 396 skipped (matches baseline); duration 112s. GREEN.

**Verification:**
- YAML parses cleanly (both touched files).
- All 14 regions pass `Region.model_validate` (Pydantic v2 strict load).
- 0 duplicate entity ids within any region; 0 unresolved `npc` bindings against `worlds/glenross/npcs.yaml` (13 authored NPCs).
- AC-1: every region has a non-empty `entities[]` array — 14/14.
- AC-2: every `tier=real_object` has a binding — 88/88. (54-3 validator will confirm binding-resolution semantics.)
- AC-3: zero `tier=yes_and` entities — confirmed (runtime-only tier).
- AC-4: deferred to 54-3 — validator does not exist yet (see Design Deviations).
- AC-5: not run — requires `just up` smoke. Renders unchanged because the loader still reads legacy `landmarks[]`; manifest is purely additive.
- AC-6: legacy `landmarks[]` preserved on all 14 regions — confirmed.

**Branch:** `feat/54-4-glenross-landmarks-to-entities` on `sidequest-content` (pushed).

**Repo scope:** content-only (matches session REPOS field). The plan's `generic_allowlist[]` work was the only thing that would have crossed into server; that has been deferred to 54-3 per "no stubs" and recorded as a deviation.

**Handoff:** To reviewer (trivial workflow → review phase). Reviewer should focus on: (a) entity authoring style — labels match prose, ids are kebab-snake unique within region; (b) binding choices — `location_feature` ref naming convention `<region>_<noun>`; (c) the deferred-allowlist deviation; (d) the unmapped Albert MacGregor NPC question.

## Dev Assessment (rework round 1)

**Reviewer findings addressed:** All four MEDIUM/LOW content-quality fixes from Portia's REJECTED verdict landed as a single commit (`ded85e7`).

**Files Changed (rework):**
- `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` — 2 insertions, 4 deletions:
  1. `examining_couch.binding.ref`: `surgery_consulting_room` → `surgery_examining_couch` (per-object naming convention now consistent with sibling surgery entities).
  2. `notice_board.binding.ref`: `village_notice_board` → `post_office_notice_board` (`<region>_<noun>` convention; the cross-region `village_*` namespace question is now a Reviewer Delivery Finding for 54-3).
  3. `manse.parlour.affordances`: removed `receive` (was a non-player-facing verb; left `sit`).
  4. `chapel_porch.affordances`: removed `read_noticeboard` (was duplicate of `chapel_noticeboard.affordances: [read]`; left `shelter`).

**Tests:** 6586/0 passing, 396 skipped — identical to baseline; rework took the suite from green back to green. Duration 113s.

**Verification (re-run):**
- YAML parses cleanly.
- All 14 regions still pass `Region.model_validate` (Pydantic v2 strict load).
- 88/88 `real_object` entities still have bindings.
- 114 total entities (88 real_object / 26 flavor_only / 0 yes_and) — count unchanged.
- 0 duplicate ids within any region.
- 0 unresolved `npc` bindings.

**Dismissed-finding response:** Portia explicitly dismissed two HIGH-confidence specialist findings — (a) caley→hamish_sinclair binding (intentional v1 proxy per plan; v2 improvement already filed in Dev Delivery Findings), and (b) kirk vestry missing `inspect_register` (kirk's landmark prose doesn't mention a register; the chapel is canonically where the parish register lives). No code change needed for either.

**Branch:** `feat/54-4-glenross-landmarks-to-entities` on `sidequest-content` (rework commit `ded85e7` pushed; prior commit `ec50f2f` is the bulk backfill).

**Handoff:** Back to Reviewer (Portia) for re-verification of the four fixes. Round-trip count is now 1.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **Gap** (non-blocking): `PackMeta` (`sidequest-server/sidequest/genre/models/pack.py`) is `extra="forbid"` and does not declare a `generic_allowlist: list[str]` field. Adding the allowlist block to `tea_and_murder/pack.yaml` breaks pack loading immediately (10 tests fail). The plan and Story 54-4 AC both list the allowlist as part of this story, but the schema field belongs in 54-3 (which also ships the consumer — the validator). Author the allowlist block + the `PackMeta` field + the consumer **together** in 54-3 so the field has a non-test consumer at land time (no stub). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `Region` model accepts both `landmarks: list[Any]` and `entities: list[LocationEntity]`. The new content adds an `entities[]` block alongside the legacy `landmarks[]` array per spec §10, but no consumer reads `entities[]` end-to-end yet — 54-6 (runtime resolver), 54-7 (overlays), and 54-9 (UI) are still queued. The data is correct; it's just not visible until those land. *Found by Dev during implementation.*
- **Question** (non-blocking): `the_railway_halt` description names "Albert MacGregor" stationmaster, but there is no `albert_macgregor` row in `worlds/glenross/npcs.yaml`. Per plan policy ("no NPCs introduced just to satisfy bindings"), I did not bind him. If 54-3's validator emits a coherence warning for the unbound proper noun, the right fix is to add him to `npcs.yaml` as part of the warm cast — he is named in prose and is the obvious gossip-source for travel events. Affects `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/npcs.yaml`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `the_glenross_arms.caley` (the publican's dog) is bound `kind: npc, ref: hamish_sinclair` as a proxy — there is no NPC id for the dog. The plan explicitly endorses this v1 routing. v2 may want a non-anthropic NPC tier (or `kind: creature`) so dogs, cats, and pigs can be addressed without proxying through their owner. Affects `sidequest-server/sidequest/protocol/models.py::LocationEntityBinding.kind` literal list. *Found by Dev during implementation.*
- **Question** (non-blocking): Story title and Story Context say "12 region landmarks[]" but `cartography.yaml` has 14 regions (`the_glenross_arms`, `the_post_office`, `the_tea_rooms`, `the_school`, `the_surgery`, `the_manse`, `st_margarets_chapel`, `the_kirk_of_st_maelrubha`, `the_railway_halt`, `the_bridge`, `the_distillery`, `castle_ross`, `the_cricket_ground`, `the_long_pass`). The plan correctly lists all 14. All 14 were backfilled. Affects `sprint/context/context-story-54-4.md` (descriptive only — count drift, no functional impact). *Found by Dev during implementation.*

### Reviewer (code review)

- **Improvement** (non-blocking): `the_cricket_ground.verandah` is `tier: real_object` with a binding (`cricket_verandah`), but the verandah is not in the region's `landmarks:` list — it appears only in the region description prose ("a wooden, lime-washed, slate-roofed clubhouse with a verandah"). Sibling pavilion sub-features (`boundary_rope`, `meadow`) are correctly `flavor_only`. Author should decide: promote verandah to landmarks[] (it does have player-facing affordances like `sit`/`watch_play`), or downgrade to flavor_only. Affects `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:1077`. *Found by Reviewer during code review.*

- **Improvement** (non-blocking): Systemic affordance vocabulary drift across the diff — bare verbs (`inspect`, `search`, `read`) are used interchangeably with compound forms (`inspect_register`, `read_names`, `read_noticeboard`) with no documented rule. A future author copying this file as a template will propagate the drift. Recommend a separate story (or part of 54-3 / 54-6) that documents an affordance vocabulary convention (suggested split: bare verbs = unstructured narrator hint; compound verbs = specific narrative beat) and audits existing packs against it. Affects `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` (and any other pack that ships `entities[]` post-54-2). *Found by Reviewer during code review.*

- **Gap** (non-blocking): No test asserts on the `entities[]` shape of any pack. The existing `test_tea_and_murder_class_kits.py` tests load tea_and_murder, which exercises `CartographyConfig.model_validate` over glenross — so the new `entities[]` block is *implicitly* schema-smoked. But a regression that, say, broke `LocationEntity` would surface as a test failure with no signal pointing at content. Per CLAUDE.md's "every test suite needs a wiring test" rule, Story 54-6 (runtime resolver) is the right place to land a real wiring test that asserts `pack.worlds["glenross"].cartography.regions[*].entities` is non-empty for every authored world. Affects `sidequest-server/tests/genre/` (new test in 54-6). *Found by Reviewer during code review.*

- **Question** (non-blocking): Does the project want a shared/cross-region `location_feature` ref namespace, or are all refs strictly `<region>_<noun>`? The `village_notice_board` ref on the_post_office's notice_board entity (line 181) is the only candidate for shared semantics — the noticeboard is physically at the post office but conceptually a village utility. Either pattern is defensible; the file convention should pick one and document it. This decision belongs in 54-3 (validator), which has to decide whether `village_*` refs resolve against a separate registry from `<region>_*` refs. Affects `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:181` and `sidequest-server/sidequest/cli/validate/locations.py` (54-3 owns). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 3 findings (1 Gap, 0 Conflict, 1 Question, 1 Improvement)
**Blocking:** None

- **Question:** Story title and Story Context say "12 region landmarks[]" but `cartography.yaml` has 14 regions (`the_glenross_arms`, `the_post_office`, `the_tea_rooms`, `the_school`, `the_surgery`, `the_manse`, `st_margarets_chapel`, `the_kirk_of_st_maelrubha`, `the_railway_halt`, `the_bridge`, `the_distillery`, `castle_ross`, `the_cricket_ground`, `the_long_pass`). The plan correctly lists all 14. All 14 were backfilled. Affects `sprint/context/context-story-54-4.md`.
- **Improvement:** Systemic affordance vocabulary drift across the diff — bare verbs (`inspect`, `search`, `read`) are used interchangeably with compound forms (`inspect_register`, `read_names`, `read_noticeboard`) with no documented rule. A future author copying this file as a template will propagate the drift. Recommend a separate story (or part of 54-3 / 54-6) that documents an affordance vocabulary convention (suggested split: bare verbs = unstructured narrator hint; compound verbs = specific narrative beat) and audits existing packs against it. Affects `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml`.
- **Gap:** No test asserts on the `entities[]` shape of any pack. The existing `test_tea_and_murder_class_kits.py` tests load tea_and_murder, which exercises `CartographyConfig.model_validate` over glenross — so the new `entities[]` block is *implicitly* schema-smoked. But a regression that, say, broke `LocationEntity` would surface as a test failure with no signal pointing at content. Per CLAUDE.md's "every test suite needs a wiring test" rule, Story 54-6 (runtime resolver) is the right place to land a real wiring test that asserts `pack.worlds["glenross"].cartography.regions[*].entities` is non-empty for every authored world. Affects `sidequest-server/tests/genre/`.

### Downstream Effects

Cross-module impact: 3 findings across 3 modules

- **`sidequest-content/genre_packs/tea_and_murder/worlds/glenross`** — 1 finding
- **`sidequest-server/tests`** — 1 finding
- **`sprint/context`** — 1 finding

### Deviation Justifications

2 deviations

- **Deferred per-pack `generic_allowlist[]` authoring to 54-3**
  - Rationale: 54-2 shipped `LocationEntity` types but did **not** wire `generic_allowlist` into `PackMeta`. The drift between plan and shipped 54-2 state is the surface area 54-3 will need to close anyway (it adds both the field and the validator that reads it). Deferring is safer than splitting it across two stories and shipping dead schema.
  - Severity: minor
  - Forward impact: minor — Story 54-3 must add `generic_allowlist: list[str] = Field(default_factory=list)` to `PackMeta` AND author the per-pack content (recommended 35 entries enumerated in this plan's Task 1) simultaneously. The validator-clean AC for 54-4 (AC-4) is verifiable only after 54-3 ships; warnings volume on coherence checks may be higher than expected until that allowlist lands.
- **AC-4 `pf validate locations` verification deferred (validator does not exist yet)**
  - Rationale: Plan explicitly lists "Depends on: 54-2, 54-3." 54-3 is unscheduled. The structural work is complete; binding resolution + prose-coherence checks will validate when 54-3 lands. SM Assessment acknowledged this (`"validator (54-3) is not yet shipped, so 'validator-clean' here means 'passes the schema check that exists today' — be ready for a follow-up touch-up once 54-3 lands"`).
  - Severity: minor
  - Forward impact: minor — Story 54-3 must rerun the validator against this backfill at land time. Any `BINDING_UNRESOLVED` / `DUPLICATE_ENTITY_ID` / `PROSE_DRIFT` warnings that surface there are reasonably scoped fixups (label tweaks, allowlist additions, or one or two NPC introductions like `albert_macgregor`).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **Deferred per-pack `generic_allowlist[]` authoring to 54-3**
  - Spec source: `docs/superpowers/plans/2026-05-19-story-54-4-glenross-entities-backfill.md` Task 1; `sprint/context/context-story-54-4.md` Key Files (mentions `generic_allowlist[]` additions); Scope Boundaries In-scope item 3.
  - Spec text: "Per-pack `generic_allowlist[]` additions for unflagged prose words." (story context); Task 1 of the plan adds a 35-entry block to `genre_packs/tea_and_murder/pack.yaml`.
  - Implementation: Did NOT add the `generic_allowlist:` block to `pack.yaml`. The `PackMeta` Pydantic model (`sidequest-server/sidequest/genre/models/pack.py`) is `extra="forbid"` and does not declare this field — adding the YAML block alone crashes pack loading and breaks 10 tests. The field is co-owned with the validator (54-3); landing it here without the consumer is a stub by CLAUDE.md's "No Stubbing" rule.
  - Rationale: 54-2 shipped `LocationEntity` types but did **not** wire `generic_allowlist` into `PackMeta`. The drift between plan and shipped 54-2 state is the surface area 54-3 will need to close anyway (it adds both the field and the validator that reads it). Deferring is safer than splitting it across two stories and shipping dead schema.
  - Severity: minor
  - Forward impact: minor — Story 54-3 must add `generic_allowlist: list[str] = Field(default_factory=list)` to `PackMeta` AND author the per-pack content (recommended 35 entries enumerated in this plan's Task 1) simultaneously. The validator-clean AC for 54-4 (AC-4) is verifiable only after 54-3 ships; warnings volume on coherence checks may be higher than expected until that allowlist lands.

- **AC-4 `pf validate locations` verification deferred (validator does not exist yet)**
  - Spec source: AC-4 in `sprint/context/context-story-54-4.md`; Task 3 Step 3 in the plan.
  - Spec text: "`pf validate locations tea_and_murder glenross` exits 0 with zero hard errors."
  - Implementation: The validator CLI (`pf validate locations` / `sidequest.cli.validate.locations`) is owned by Story 54-3, which is still in `backlog`. Only `sidequest.cli.validate.projection_check` currently exists. Verified instead via direct Pydantic model load (`Region.model_validate` over all 14 regions, 14/14 OK), YAML parse (`python3 -c "yaml.safe_load(...)"` OK), and the full `just server-test` suite (6586/0/396 GREEN).
  - Rationale: Plan explicitly lists "Depends on: 54-2, 54-3." 54-3 is unscheduled. The structural work is complete; binding resolution + prose-coherence checks will validate when 54-3 lands. SM Assessment acknowledged this (`"validator (54-3) is not yet shipped, so 'validator-clean' here means 'passes the schema check that exists today' — be ready for a follow-up touch-up once 54-3 lands"`).
  - Severity: minor
  - Forward impact: minor — Story 54-3 must rerun the validator against this backfill at land time. Any `BINDING_UNRESOLVED` / `DUPLICATE_ENTITY_ID` / `PROSE_DRIFT` warnings that surface there are reasonably scoped fixups (label tweaks, allowlist additions, or one or two NPC introductions like `albert_macgregor`).

### Reviewer (audit)

- **Dev deviation: Deferred per-pack `generic_allowlist[]` authoring to 54-3** → ✓ ACCEPTED by Reviewer. PackMeta is `extra="forbid"` at `sidequest-server/sidequest/genre/models/pack.py` and does not declare the field; landing the YAML block alone breaks 10 tests in `test_tea_and_murder_class_kits.py` and `test_trope_time_skip_e2e.py`. Bundling the field add, the consumer (validator), and the per-pack content together in 54-3 is the right "no half-wired features" call. Recorded as a blocking dependency of 54-3.

- **Dev deviation: AC-4 `pf validate locations` verification deferred (validator does not exist yet)** → ✓ ACCEPTED by Reviewer. Confirmed via `ls sidequest-server/sidequest/cli/validate/` — only `projection_check.py` exists; `locations.py` is owned by Story 54-3 (still `backlog`). The substitute verification — Pydantic `Region.model_validate` over all 14 regions + full server suite — exercises the schema path that the loader will actually run at runtime, which is the meaningful gate today. 54-3 inherits a binding-resolution rerun against this backfill.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 6586/0/396 green, no smells, YAML parses, Region model validates 14/14 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 (1 high-confidence misread, 2 medium) | confirmed 1, dismissed 1, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 6 (3 high, 3 medium) | confirmed 4, dismissed 1, deferred 1 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 2 (1 high, 1 low) | confirmed 1, dismissed 1 |

**All received:** Yes (4 active specialists returned; 5 disabled per `workflow.reviewer_subagents`)
**Total findings:** 6 confirmed, 2 dismissed (with rationale), 3 deferred (logged to Delivery Findings)

### Rule Compliance

Enumerated against the project rules I extracted for the rule-checker (story AC + plan convention + SOUL.md + LocationEntity schema). Rule-checker corroborates this exhaustively across all 114 entities.

- **AC-1** (every region has non-empty `entities[]`) — 14/14 regions compliant. **VERIFIED.**
- **AC-2** (every `tier=real_object` has a binding) — 88/88 entities compliant. Schema-level. **VERIFIED.** Binding-resolution semantics ARE the 54-3 validator's job; see [RULE] finding F4 for one convention drift that will likely surface there.
- **AC-3** (no `tier=yes_and` in authored content) — 0/114 violations. **VERIFIED.**
- **AC-6** (legacy `landmarks[]` preserved on every region) — 14/14 preserved unchanged in diff. **VERIFIED.**
- **`binding.kind` literal** (must be one of "location_feature"/"npc"/"item"/"clue"/"scenario_clue") — 88/88 use `location_feature` or `npc`. **VERIFIED.**
- **Entity `id:` is snake_case** — 114/114 compliant. **VERIFIED.**
- **`label:` mirrors prose with definite article when prose uses it** — 114/114 compliant within author tolerance (minor synonym shifts like "gravestones" → "headstones" judged acceptable; specialist agreed). **VERIFIED.**
- **No binary assets committed** — 819-line YAML-only diff. **VERIFIED.**
- **No stubs / skeleton entities** — all entities grounded in landmark or description prose. **VERIFIED.**
- **Diamonds-and-Coal calibration** — 26 flavor_only assignments individually scrutinised by rule-checker, all correctly tiered (atmosphere/set-dressing vs mechanically-engageable). Named NPCs all correctly `real_object`. **VERIFIED.**
- **Spoiler protection (glenross fully unspoiled)** — entities expose existing prose mechanically; no new canonical facts introduced. **VERIFIED.**
- **`<region>_<noun>` ref convention** (authoring plan rule, not schema) — 64/65 location_feature refs compliant; ONE drift (`village_notice_board` in `the_post_office`) → see [RULE] F4. Plus one off-convention compound that the comment-analyzer caught separately → see [DOC][RULE] F1.

### Devil's Advocate

If this content is broken, where would it surface? The diff is YAML data with no runtime consumer wired today — the existing class-kit tests do load the pack (good: implicit smoke), but nothing reads `entities[]` end-to-end yet. So "broken" here can only mean either (a) schema rejection at load time (ruled out — 6586/0 green and Pydantic `Region.model_validate` accepts every region), or (b) authoring drift that bites a future consumer.

Future consumers: **54-3 validator** (binding resolution + prose-coherence + convention check), **54-6 runtime resolver** (renders entities to UI), **54-9 Location UI** (player-facing manifest). What would each find?

54-3 will trip on `surgery_consulting_room` ref under the `<region>_<noun>` convention (the room-named ref smells like a typo, especially because `surgery_door`/`surgery_dispensary` follow the per-object pattern). It will also trip on `village_notice_board` (cross-region naming) — though this one is plausibly an intentional shared-feature pattern that just isn't documented. It will trip on the asymmetric verb tokens (`read` vs `read_noticeboard` on the same physical object) when it runs coherence on the chapel.

54-6 will see `affordances: [receive]` on `manse_parlour` and try to render it as a player option. "Receive" is what the *minister* does in the parlour — a player can't "receive." A confused player will see an action they cannot perform. The Zork Problem doctrine in SOUL.md is specifically: never let the interface imply actions that aren't actually open. `receive` violates that subtly.

54-9 might surface duplicate-looking entities to the player at the chapel: `chapel_porch` offers `read_noticeboard`, and the noticeboard entity itself offers `read`. Same physical object, two differently-named actions. Player squints.

A malicious or confused author looking at this file as a template — copying it for `tea_and_murder/another_world` — will absorb the affordance vocabulary drift (bare `inspect` vs `inspect_<noun>` vs `search` for the same kind of container check) and propagate it. That's the systemic risk the comment-analyzer correctly identified.

What a stressed filesystem produces: nothing different. Pure data. What an unexpected config does: nothing — schema is permissive.

The malicious user: harder to imagine here. The content is unspoilable Glenross — there's no token leakage, no auth surface, no injection vector. The worst case is an entity label that contains a YAML control character; spot-checking the labels finds none.

Net of devil's advocate: my findings stand. The drift items are not theoretical — they actively misshape what 54-3 / 54-6 will see when they try to read this manifest. Four of them have one-line fixes; the systemic affordance vocabulary issue is bigger and deserves to be deferred to a vocab-doc story.

## Reviewer Assessment

**Verdict:** REJECTED (green rework — content-quality fixes only, no test changes)

**Data flow traced:** `cartography.yaml` → `_load_single_world` → `_load_cartography` → `CartographyConfig.model_validate` → `Region.model_validate` → `LocationEntity.model_validate` (per region). The new `entities[]` blocks ride the same schema path the loader already exercised before this diff; 14/14 regions validate. Future consumers (54-3 validator, 54-6 resolver, 54-9 UI) will read `entities[]` directly — none ship today, so runtime impact is gated on those.

**Pattern observed:** Authored cartography manifest, three-tier (real_object / flavor_only / never-authored yes_and) per ADR-109. Per-region location_feature refs follow `<region>_<noun>` convention with two drift exceptions (see findings). NPC bindings use `npcs.yaml` ids cleanly (13 distinct refs, all resolve). Pattern fidelity is otherwise strong across all 14 regions.

**Error handling:** N/A — pure content. Schema (`extra="forbid"` on `LocationEntityBinding`, `LocationEntity`) is the gate; load failure raises `GenreLoadError`. No silent fallbacks introduced.

**Severity table — findings actionable in this story:**

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] [DOC][RULE] | `examining_couch.binding.ref = surgery_consulting_room` violates per-object naming convention used by all other surgery entities (`surgery_door`, `surgery_dispensary`, `surgery_telephone`, `surgery_waiting_bench`). Will trip 54-3's binding-resolution. | `genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:400` | Change ref to `surgery_examining_couch` |
| [MEDIUM] [RULE] | `notice_board.binding.ref = village_notice_board` violates `<region>_<noun>` convention in the_post_office region. Either deliberate shared-feature pattern (needs explicit documentation note in the file) or a typo. | `genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:181` | Either rename ref to `post_office_notice_board`, OR add a one-line YAML comment above the entity explaining the shared-village-feature intent |
| [LOW] [DOC] | `manse.parlour.affordances` contains `receive` — inverts the player-action convention (everywhere else affordances are verbs a player can perform: `enter`, `sit`, `read`, `knock`). `receive` is what the minister does. Violates SOUL.md "Zork Problem" doctrine subtly: implies an action the player can't actually take. | `genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:501` | Remove `receive` (the parlour's purpose is conveyed by the region description already), or replace with `meet_with` |
| [LOW] [DOC] | Duplicate, inconsistently-named affordances for the same physical object: `chapel_porch.affordances` has `read_noticeboard`; `chapel_noticeboard.affordances` has bare `read`. A narrator surfacing both will offer the player two differently-labelled actions for the same interaction. | `genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:541` and `:549` | Standardize on one token — recommend bare `read` on both (`chapel_porch` shouldn't carry `read_noticeboard` because the porch entity isn't itself the noticeboard) |

**Dismissed findings (with rationale):**
- [TEST][RULE] **`caley.binding.ref = hamish_sinclair` is a "semantic mismatch / silent fallback"** (test-analyzer HIGH, rule-checker HIGH) — DISMISSED. This is intentional v1 proxy routing per the authoring plan (`docs/superpowers/plans/2026-05-19-story-54-4-glenross-entities-backfill.md` lines 230-231: *"Caley the dog binds to `hamish_sinclair` as a proxy — there is no NPC id for Caley. v2 may mint a non-anthropic NPC; for v1 the binding routes engagement to Hamish, which is the right behavior — Caley belongs to Hamish."*). Dev's Delivery Finding already files the v2 improvement (request `kind: creature` or non-anthropic NPC tier). Neither specialist had the plan context. Not a fallback — a documented intentional design.
- [DOC] **kirk vestry missing `inspect_register` affordance** (comment-analyzer MEDIUM) — DISMISSED. The chapel vestry has the affordance because its landmark prose explicitly names *"the vestry with the rector's robes and the parish register."* The kirk vestry is added as a real_object but the kirk's landmark list does NOT name the parish register — it lives at the chapel (St Margaret's) per the prose. The asymmetry is faithful to source prose, not an author oversight.

**Deferred to Delivery Findings (non-blocking, future story):**
- [DOC] verandah cricket_ground tier inconsistency (medium-confidence) — logged below
- [DOC] Systemic affordance vocabulary drift (medium-confidence, spans whole diff) — logged below
- [TEST] No explicit assertion on `entities[]` shape (test-analyzer medium) — logged below; 54-6 wiring tests should cover this

**Handoff:** Back to Dev (Puck) for the four lint-grade content fixes listed above. Suite green throughout — this is a `green rework` cycle, not a `red rework`. Estimated effort: ~4 line edits + recommit + repush + Portia recheck.

---

## Subagent Results (rework round 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 6586/0/396 green, 113s; YAML+Pydantic clean; 0 smells; rework commit confirmed 2 ins / 4 del |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes (round 0 result still authoritative) | clean | none new | All three round-0 findings unchanged: (a) "no test asserts on entities[]" remains a Delivery Finding for 54-6 wiring; (b) caley=hamish_sinclair was dismissed round 0 (plan-documented); (c) tier-vs-binding test deferred to 54-3 per dev's deviation. No NEW test concerns introduced by 4-line diff. |
| 5 | reviewer-comment-analyzer | Yes (round 0 result still authoritative + new manual check) | clean | none new | All three confirmed round-0 findings ADDRESSED by rework: examining_couch ref fixed (line 400), parlour `receive` dropped (line 501), chapel_porch `read_noticeboard` dropped (line 540). Two deferred findings (verandah tier, vocab drift) still stand as Delivery Findings. Kirk-vestry asymmetry dismissed round 0 (faithful to prose). |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes (round 0 result still authoritative + new manual check) | clean | none new | Both round-0 violations resolved: Rule 6 `village_notice_board` → `post_office_notice_board` (now `<region>_<noun>` compliant); Rule 11 caley=hamish_sinclair dismissed round 0 (intentional v1 proxy per plan). All 13 rules and 114 entities re-spot-checked manually against the rework diff — no new instances introduced. |

**All received:** Yes (4 active specialists; 5 disabled per `workflow.reviewer_subagents` settings)
**Total findings:** 0 new, 4 addressed (round-0 confirmed findings closed by rework), 2 still dismissed (with rationale), 3 still deferred (Delivery Findings to 54-3 / 54-6)

### Rework Re-check (Reviewer manual verification)

Independently re-verified the rework against the round-0 findings table via direct YAML inspection:

| Round-0 Finding | Status | Evidence |
|-----------------|--------|----------|
| [DOC][RULE] examining_couch ref convention | ✓ CLOSED | `cartography.yaml:400` now reads `ref: surgery_examining_couch` — matches per-object pattern of all sibling surgery entities |
| [RULE] notice_board ref convention | ✓ CLOSED | `cartography.yaml:180` now reads `ref: post_office_notice_board` — matches `<region>_<noun>` pattern. Cross-region `village_*` namespace question now logged as Reviewer Delivery Finding for 54-3 |
| [DOC] `receive` affordance on parlour | ✓ CLOSED | `cartography.yaml:501` — `- receive` line removed; manse.parlour.affordances now `[sit]`. SOUL.md Zork Problem doctrine respected |
| [DOC] chapel duplicate read tokens | ✓ CLOSED | `cartography.yaml:540` — `- read_noticeboard` removed from chapel_porch; only chapel_noticeboard itself now carries `read`. No more duplicate-action UI risk |

Additional collateral checks I ran (none mandated by the protocol; doing them anyway):
- No orphan references to either retired ref (`village_notice_board`, `surgery_consulting_room`) anywhere in the file — confirmed by Python search.
- No empty `affordances: []` arrays created as a side-effect of the drops — both affected entities still carry at least one verb.
- Cross-region ref-collision audit: only `hamish_sinclair` (×2 — `hamish` + Caley proxy, plan-documented) and `rev_murchison` (×2 — manse + kirk, NPCs legitimately appear in multiple regions) repeat. Neither is a concern.

### Devil's Advocate (rework round)

The rework is too small to break much, but: could the renamed refs collide with something OUTSIDE this diff? Specifically, does `surgery_examining_couch` or `post_office_notice_board` accidentally clash with a ref defined in another world or pack? Quick check: `grep -r "surgery_examining_couch\|post_office_notice_board"` across `sidequest-content/genre_packs/**` — neither string occurs anywhere else. Safe.

Could dropping `receive` strand a downstream consumer? No — `entities[]` has no shipped consumer; the only thing reading the affordances list today is Pydantic strict-load (which accepts any `list[str]`). The narrator's eventual prompt (54-6/54-7) hadn't shipped under round-0, hadn't shipped under round-1 either, and is upstream-pure of this content.

Could the kept `surgery_examining_couch` ref STILL be wrong at runtime? It will only matter when 54-3's binding-resolution check runs. The validator hasn't shipped — but the ref now matches the per-object convention every other surgery entity uses, so 54-3 has no idiomatic reason to reject it. If 54-3 ends up using a registry that requires `location_feature` records be pre-declared elsewhere (e.g., in `interior/` or similar), that's a separate problem affecting ALL 75 location_feature refs in this content — not unique to this rework, and explicitly Story 54-3's design space.

I find nothing new to flag. Approval is correct.

## Reviewer Assessment (rework round 1)

**Verdict:** APPROVED

**Data flow traced:** rework diff is content-only; same load path as round-0 (`CartographyConfig.model_validate` → `Region.model_validate` → `LocationEntity.model_validate`). 14/14 regions still validate; the two ref renames only affect string content, not schema shape; the two affordance drops only shorten existing `list[str]` fields.

**Pattern observed:** Surgical 4-edit cleanup that closes every actionable round-0 finding without introducing new ones at `genre_packs/tea_and_murder/worlds/glenross/cartography.yaml:180,400,501,540`. Net diff: +2 / -4. No collateral, no scope creep, no new YAML structure.

**Error handling:** N/A — pure content; schema is the gate; Pydantic strict load passes.

**Round-0 findings closure status:**
- 4 actionable findings → ALL ADDRESSED (closed by this rework)
- 2 dismissed findings → still correctly dismissed (caley proxy is plan-documented; kirk vestry asymmetry is prose-faithful)
- 3 deferred findings → still appropriately deferred to follow-up stories (verandah tier, affordance vocab drift, entities[] wiring test) and surfaced as Reviewer Delivery Findings for 54-3 / 54-6 to pick up

**Handoff:** To SM (Prospero) for the finish phase. Branch `feat/54-4-glenross-landmarks-to-entities` on `sidequest-content` is ready to PR-and-merge: two commits — `ec50f2f` (bulk backfill, 819 ins) + `ded85e7` (rework, +2/-4). Suite stayed green throughout (6586/0/396).