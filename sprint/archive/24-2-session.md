---
story_id: "24-2"
jira_key: ""
epic: "24"
workflow: "trivial"
---

# Story 24-2: Author tea_and_murder/glenross weather rules (climate zones, seasonal conditions, special events)

## Story Details

- **ID:** 24-2
- **Jira Key:** (none — SideQuest does not use Jira)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking

**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-20T11:02:17Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-20T10:32:50Z | 2026-05-20T10:45:39Z | 12m 49s |
| implement | 2026-05-20T10:45:39Z | 2026-05-20T10:52:14Z | 6m 35s |
| review | 2026-05-20T10:52:14Z | 2026-05-20T11:02:17Z | 10m 3s |
| finish | 2026-05-20T11:02:17Z | - | - |

## Sm Assessment

**Context:** Story 24-2 is Phase 1 of Epic 24 (Procedural World-Grounding Systems). This story author a weather YAML configuration for the tea_and_murder/glenross world, following the Monster Manual pattern (ADR-059). The schema definition itself (story 24-1) is a prerequisite, but content authoring can proceed in parallel once the epic context is understood.

**Target deliverable:** A `weather.yaml` file in `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/` containing:
- Climate zone definitions (e.g., rolling moorlands, highlands, lowlands, coastal marshes if applicable to glenross geography)
- Seasonal conditions and transitions (glenross seasons mapped to Glenross calendar if available in world.yaml or lore)
- Special weather events (storm patterns, fog conditions, seasonal phenomena unique to the region)
- Mechanical grounding (how weather surfaces in narration — flavor text candidates, tension shifts, environmental hazards)

**Scoping notes:**
1. Check `world.yaml` in glenross to understand existing geography, climate tone, and calendar structure
2. Reference `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/cartography.yaml` for regional divisions (climate zones should map to physical regions)
3. Cross-check with `history.yaml`, `lore.yaml`, and `cultures.yaml` for weather-relevant cultural detail (e.g., how weather affects NPCs or settlements)
4. Trivial workflow: no TDD, no test setup — implement and review in series

**No Jira.** No `--jira` flags. This is content authoring in sidequest-content, not API code.

## Discovery Findings

### Glenross World Context

**Finding: Glenross has established geography, history, and culture; weather authoring is greenfield content.**

Scope: `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/`

Glenross is the flagship world for the tea_and_murder genre pack. Existing context includes:

1. **world.yaml** — Contains world metadata, theme, axis_snapshot (emotional tone axes), and visual description
2. **cartography.yaml** — Detailed region divisions (36KB file, suggesting rich geography; presume multiple climate zones per cartography definitions)
3. **history.yaml** — 35KB history file; may contain seasonal/climate-relevant narrative detail
4. **cultures.yaml** — 2KB summary; points to cultures/directory with per-culture detail (4 cultures)
5. **lore.yaml**, **legends.yaml** — Environmental and cultural lore; may reference seasonal/weather phenomena
6. **npcs.yaml**, **portrait_manifest.yaml** — NPC and asset manifest; may flag NPCs with weather-dependent routines
7. **openings.yaml** — 76KB opening narrations; potential template text for weather-grounded prose style

**No existing weather.yaml** — Confirmed. Greenfield authoring.

**Climate inference from existing files:**
- Tea_and_murder is cosy/gothic mystery genre — weather likely emphasizes fog, damp, seasonal gloom, tea-shop ambiance
- Glenross likely has moorland or coastal climate (Scottish aesthetics); presume cold winters, damp springs, short summers, extended autumns
- Multiple regions in cartography suggest climate variation (highlands ≠ lowlands; coast ≠ interior)

**Type:** Discovery finding — greenfield scope, existing context confirmed
**Urgency:** non-blocking (normal scope clarification)

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

No deviations documented at setup.

### Dev (implementation)
- **File placed at pack level, not world level**
  - Spec source: SM Assessment in this session (lines 34, 41) — says
    `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/weather.yaml`
  - Spec text: "A `weather.yaml` file in `sidequest-content/genre_packs/tea_and_murder/worlds/glenross/`"
  - Implementation: Authored at `sidequest-content/genre_packs/tea_and_murder/weather.yaml` (pack level, alongside `pack.yaml` / `rules.yaml`)
  - Rationale: Three higher-authority sources unanimously require pack
    placement. (a) The JSON schema `docs/schemas/world-grounding/weather.schema.json`
    title is literally "Weather (pack level)" and its description says
    "Authored once per pack; lives at sidequest-content/genre_packs/<pack>/weather.yaml".
    (b) The schema README placement convention table lists weather as
    `pack` level. (c) The current-sprint.yaml epic-24 description states
    "weather/demographics/calendar YAML go in sidequest-content/genre_packs/<pack>/
    alongside existing top-level pack files, NOT in a layered system/ folder."
    The schema's root structure (`climate_zones:` with worlds referencing
    zones by id) is incompatible with world-level placement — putting one
    weather.yaml per world would duplicate climate-zone rules and break
    the "world picks a zone id" indirection that 24-5's generator needs.
  - Severity: minor
  - Forward impact: low — the world-level path would still have parsed and
    validated against the schema (it would just live in the wrong place);
    story 24-5's generator will look for the file at pack level per the
    schema description, so the pack-level path is what the consumer
    actually wants. SM Assessment likely conflated "weather rules for the
    glenross world" (true) with "weather.yaml lives in worlds/glenross/"
    (false per schema). Demographics (24-3) IS world-level per the schema
    placement table — that one stays under `worlds/glenross/`.

### Reviewer (audit)
- **Dev's pack-vs-world-level deviation** → ✓ ACCEPTED by Reviewer: Dev
  correctly identified that the SM Assessment cited the wrong placement.
  The JSON schema is unambiguous ("Weather (pack level)" in the title,
  "lives at sidequest-content/genre_packs/<pack>/weather.yaml" in the
  description) and the current-sprint.yaml epic-24 description
  independently mandates pack placement. Three authoritative sources
  agree; SM Assessment is the outlier. Deviation logged with thorough
  rationale and forward-impact analysis. No further action needed for
  this story; recommend SM-setup template/prompt be updated to consult
  `docs/schemas/world-grounding/README.md` placement table before
  authoring deliverable paths (captured as a Delivery Finding).
- **Undocumented deviation: condition-label/special-event-name overlap
  (gold_afternoon, early_snow, whiteout)** — Spec source: schema's
  conditions and special_events are described as distinct generator
  channels (weather.schema.json descriptions for `seasonPalette.conditions`
  and `climateZone.special_events`). Code does: deliberately reuses three
  label strings in both channels for the same zone+season. Not documented
  by Dev. Severity: LOW. Rationale: the schema's prose at
  weather.schema.json:34 ("Sampled before the per-scene roll; if one fires,
  it takes precedence for its duration") provides a precedence rule that
  resolves the apparent conflict, so the YAML is consistent with the
  schema's intent — but Dev should have flagged this as an intentional
  design choice. Captured as a Delivery Finding for 24-5 implementer.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content/genre_packs/tea_and_murder/weather.yaml` (new, +287 lines) —
  pack-level weather rules with two climate zones (`glen_floor`, `highland_pass`),
  four-season palettes per zone, and 10 named special events grounded in
  glenross lore (haar, harvest gale, hogmanay blizzard, gold afternoon,
  false spring, midge calm, early snow, whiteout, hill inversion, stalking
  morning).

**Validation:**
- JSON Schema Draft 2020-12: `uvx --from check-jsonschema check-jsonschema
  --schemafile docs/schemas/world-grounding/weather.schema.json
  sidequest-content/genre_packs/tea_and_murder/weather.yaml` → `ok -- validation done`
- Structural sanity check: all required keys present; per-season
  `conditions` / `weights` arrays length-matched; temp ranges well-formed;
  every special_event carries name + chance.

**Tests:** N/A — trivial workflow, content authoring (no test surface). The
schema validator IS the test; manual schema check passes.

**Branch:** `feat/24-2-glenross-weather-rules` (sidequest-content) — pending push

**Wiring posture:** Intentionally NOT wired. Story 24-1 chose JSON-schema-only
inert authoring; consumers belong to 24-5 (Python weather generator) and 24-6
(prompt-zone injection). This file is greenfield-ready for those stories;
pack loader does not import it today, by design.

**Content-design notes for Reviewer:**
- Season ids are the conventional `spring/summer/autumn/winter`. Story 24-4
  (glenross calendar) MUST use the same ids or prompt-zone alignment fails
  (called out in the schema as a hard contract).
- Climate-zone choice (`glen_floor` vs `highland_pass`) maps to the
  cartography's village-vs-pass divide: the Long Pass (`cartography.yaml:1119`)
  has its own scene register — chase scenes, body discoveries, exposure
  deaths (legends.yaml frozen-cairn man). Two zones rather than one lets
  the narrator say "the village is mild, the pass is in cloud" on the
  same scene.
- Conditions vocabulary is Highland-local (`smirr`, `haar`, `hill_fog`,
  `gloaming`-adjacent) rather than generic. The narrator receives the
  label verbatim per schema description.
- Special events lean genre-functional: `harvest_gale` blocks the pass
  road, `hogmanay_blizzard` cuts the railway (sealed-village setup),
  `early_snow` enables body discoveries, `midge_calm` drives suspects
  indoors. Each one is a setup that should make the GM panel smile.

**Handoff:** To review (trivial workflow goes setup → implement → review → finish)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (3 INFO notes on intentional condition/event shadowing) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 3 | 0 confirmed-for-action, 0 dismissed, 3 deferred (all are missing-infra observations out of scope for this content story; matches Dev's own delivery findings) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | 1 confirmed (LOW), 2 dismissed (subagent read stale epic-24.yaml backlog; current-sprint.yaml + legends.yaml line 32 are authoritative and confirm both contested comments) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 5 | 3 confirmed-downgraded-to-LOW (R9 shadowing — see Devil's Advocate; pattern is schema-consistent), 1 confirmed (R13 LOW), 1 confirmed (R14 LOW) |

**All received:** Yes (4 enabled, 4 returned; 5 disabled, pre-filled per gate spec)
**Total findings:** 7 confirmed (all LOW), 2 dismissed (with rationale), 3 deferred

### Rule Compliance

Rule-checker enumerated 17 rules across 68 instances with line-cited verdicts; full table embedded in the Devil's Advocate below. Summary:

| Rule | Source | Instances | Violations | Verdict |
|------|--------|-----------|------------|---------|
| R1–R7 | weather.schema.json | 30 | 0 | Compliant |
| R8 | schemas/README.md | 14 | 0 | Compliant |
| R9 (open-enum prose) | schemas/README.md + schema | 21 | 3 — shadowing pattern | LOW (see Devil's Advocate; schema's precedence rule resolves the apparent conflict) |
| R10 (pack placement) | schemas/README.md | 1 | 0 | Compliant (Dev's deviation against SM Assessment is the correct call — see Deviation Audit) |
| R11 (Diamonds & Coal) | SOUL.md | 10 | 0 | Compliant — comment depth tracks narrative weight |
| R12 (Genre Truth) | SOUL.md | 10 | 0 | Compliant — Highland palette, Christie-tier exposure lethality |
| R13 (Crunch/Flavor) | SOUL.md | 2 | 1 | LOW — pack currently single-world, comments are world-bound but file structure is generic |
| R14 (The Test) | SOUL.md | 10 | 1 — `drives_indoors` | LOW — label encodes outcome not condition; consumer not built so harmless today |
| R15 (No Stubbing) | CLAUDE.md | 1 | 0 | Compliant |
| R16 (No Silent Fallbacks) | CLAUDE.md | 1 | 0 | Compliant |
| R17 (Don't Reinvent) | CLAUDE.md | 7 | 0 | Compliant — first weather.yaml in the repo; this IS the exemplar |

### Devil's Advocate

Suppose this code is broken. What would a stressed consumer, a confused author, or a malicious editor do?

**The shadowing problem (R9 × 3).** A condition label `gold_afternoon` lives in glen_floor/autumn's conditions palette (line 89) alongside a special_event also called `gold_afternoon` (line 153). Same for `early_snow` (lines 237 and 260) and `whiteout` (lines 254 and 273). A naïve consumer that samples both channels without precedence will surface "gold_afternoon" with NO effects (rolled from palette) and "gold_afternoon" with effects/duration (fired from special_event) and treat them as the same thing. Worse: a downstream narrator receives the string "gold_afternoon" twice in adjacent turns and re-uses the same prose, defeating the very anti-mode-collapse mission Epic 24 exists to serve. **But:** the schema's prose at `weather.schema.json:34` already prescribes the resolution: `special_events` are "Sampled before the per-scene roll; if one fires, it takes precedence for its duration." So the consumer's contract is `if special_event_rolled: emit_event; else: sample_palette`. Under that contract, a palette-roll of `gold_afternoon` is *the routine version* and an event-fire is *the marked version* — and the narrator gets to distinguish them by presence/absence of effects. This is actually a reasonable two-channel design once the precedence is honored. **Risk if not honored:** ambiguity in 24-5's generator. **Mitigation:** could rename palette entries to `golden_light`, `late_season_snow`, `near_whiteout` (5-minute Dev fix) or rely on 24-5 honoring the schema's precedence rule. I am taking the latter path because the schema already encodes the precedence and the YAML is consistent with it — but I'm flagging this as a Delivery Finding for 24-5 to read before they pick a strategy.

**The over-binding problem (R13).** A reader who has never seen glenross opens this file and sees "glen_floor" / "highland_pass" — they will *think* this is a glenross-specific file, not a tea_and_murder-pack file. If tea_and_murder ever grows a second world (Cotswolds village, Sussex coast, Yorkshire dales — all plausible BritBox subgenres), they must add zones. The current zones don't generalize; the existing structure can grow new ones additively. This is not a bug today (single world, comprehensive coverage). It IS a debt note for the day a second world arrives. **Mitigation:** Delivery Finding for whichever future story adds the second tea_and_murder world.

**The agency problem (R14).** `drives_indoors` (line 186) names an outcome ("characters end up indoors"), not a condition ("midges make outdoor activity miserable"). If the narrator ingests this label literally and writes "The midges drive you indoors," that's a Test violation — the player did not ask to go indoors. **But:** the consumer is unbuilt. The label only matters when 24-5 decides what to do with the `effects:` array. **Mitigation:** rename suggestion captured in Delivery Findings. Not blocking — the YAML is the only place that mentions `drives_indoors` and renaming it now (or in a follow-up content polish) is trivial.

**The stress-test angles.**
- *Stress-test 1: Massive future world.* A new world with 6 climate zones drops in. Does the schema explode? No — `climate_zones` is `additionalProperties: $ref → climateZone` — unbounded growth allowed. ✓
- *Stress-test 2: Future calendar story uses different season ids.* Author of 24-4 invents "lambing/heatherbloom/stagrut/dark" instead of spring/summer/autumn/winter. Prompt-zone injection silently misaligns; narrator gets no weather. The header comment at lines 22-24 explicitly flags this hard contract. ✓ (Caller's problem, called out.)
- *Stress-test 3: Editor adds a condition without a weight.* Schema can't catch length-parity mismatch (test-analyzer F3); generator IndexErrors. **This is a real future failure mode.** Mitigation: deferred to schema-validator follow-up story. Same Delivery Finding as 24-5's responsibility list.
- *Stress-test 4: All special_events fire simultaneously.* Total chance budget in glen_floor.special_events = 0.06+0.05+0.07+0.10+0.05+0.18 = 0.51 (per-day or per-scene depending on 24-5's interpretation). If 24-5 reads this as per-day independent rolls, the village gets a named weather event every other day. If per-scene, ~50% of scenes have a named event. The schema is ambiguous about cadence ("Per-day (or per-scene, see 24-5)"). **Mitigation:** deferred to 24-5.

The devil's advocate uncovered one mitigation that wasn't in the original findings: the schema cadence ambiguity (per-day vs per-scene chance). Adding this as a Delivery Finding for 24-5.

## Reviewer Assessment

**Verdict:** APPROVED

Pure YAML content authoring; the file conforms to its schema (validated end-to-end with `check-jsonschema`), to the placement convention, and to the cosy-Edwardian-mystery genre register. Detail distribution tracks narrative weight (Diamonds and Coal honored), every special event has an inline comment explaining its narrative purpose, condition vocabulary is intentionally Highland-local (`smirr`, `haar`, `hill_fog`) per the schema's "narrator receives label verbatim" contract. No Critical or High severity findings.

**Data flow traced:** Today: weather.yaml → (nothing). The file is intentionally inert per story 24-1's design; consumers belong to 24-5 (Python generator → `proposed weather state`) and 24-6 (prompt-zone injection → narrator). Tomorrow's path will be: weather.yaml → 24-5 generator (palette sample + event roll with precedence-resolution) → 24-6 zone injection → narrator prompt → narrator selects → `SceneSetting.weather` (currently `str` at `sidequest-server/sidequest/genre/models/scenario.py:132`, migrating to typed in 24-5/6). Safe today because the file has no consumer; the consumer contract is owned by 24-5 per `docs/schemas/world-grounding/README.md`.

**Pattern observed:** Two-channel weather model — routine `conditions[]` palette + rare named `special_events[]` — with the schema's prose (`weather.schema.json:34`) prescribing event-takes-precedence-over-palette. The YAML deliberately uses this pattern, including three intentional name overlaps (`gold_afternoon`, `early_snow`, `whiteout`) where the same string appears in both channels. Per the schema's precedence rule this is consistent — the event-fire produces effects + duration, the palette-roll produces the bare label.

**Error handling:** N/A at YAML level; downstream invariants (`len(conditions) == len(weights)`, `temp_range` ordering) hold for all 8 palettes by hand-count but cannot be enforced by JSON Schema structurally — flagged for future `pf validate world-grounding`.

**Findings (all LOW, none blocking):**

| Severity | Issue | Location | Tag | Notes |
|----------|-------|----------|-----|-------|
| [LOW] | Comment claims "Distillery starts in earnest from August (see lore.yaml)" — the specific phrasing is in world.yaml:11, not lore.yaml (lore.yaml mentions distillery+August separately). Cross-reference points to the secondary rather than primary source. | weather.yaml:61 | [DOC] | Optional polish; lore.yaml does support the broader claim |
| [LOW] | `gold_afternoon` condition label (glen_floor/autumn) shadows `gold_afternoon` special_event name in same zone+season | weather.yaml:89 vs 153 | [RULE] | Intentional per two-channel design; resolved by schema precedence rule at weather.schema.json:34; flagged for 24-5 implementer |
| [LOW] | `early_snow` condition label (highland_pass/autumn) shadows `early_snow` special_event name in same zone+season | weather.yaml:237 vs 260 | [RULE] | Same pattern as above |
| [LOW] | `whiteout` condition label (highland_pass/winter) shadows `whiteout` special_event name in same zone+season | weather.yaml:254 vs 273 | [RULE] | Same pattern as above |
| [LOW] | Pack-level file's zone ids (`glen_floor`, `highland_pass`) and comments are glenross-specific (River Allt Ross, the kirk, the Long Pass references). Will not generalize to a hypothetical second tea_and_murder world. | weather.yaml:39, 188 | [RULE] | Pack has one world today; refactor is cheap (add zones, don't remove) when a second world lands |
| [LOW] | `drives_indoors` effect label (midge_calm) names a character outcome rather than an environmental condition. Authoring comment "forcing a suspect into a parlour" reinforces the outcome framing. Risk: narrator could read this as agency-violating. | weather.yaml:186 | [RULE] | Rename to `outdoor_activity_intolerable` or similar in a content polish pass; harmless today (no consumer) |
| [LOW] (deferred) | No automated CI/pre-commit hook validates this file against its schema. `check-jsonschema` was a one-off Dev-time run. | (infra-level) | [TEST] | Out of scope for 24-2 content story; matches Dev's own delivery finding; appropriate for a future `pf validate world-grounding` story |

**Dismissed findings (with rationale):**
- [DOC dismissed] Comment-analyzer F2: "Story 24-4 reference is wrong." Subagent read stale `sprint/epic-24.yaml` (pre-retarget backlog still says low_fantasy/pinwheel_coast). The authoritative source is `sprint/current-sprint.yaml`, and `pf sprint story field 24-4 title` returns "Author tea_and_murder/glenross calendar (months, days, moons, festivals, time precision)." Comment is correct.
- [DOC dismissed] Comment-analyzer F3: "'fifty years' is arithmetically wrong." `legends.yaml:32` reads literally `era: "fifty years ago; burnt 1862-63"` — the in-world voice rounds to fifty years even though arithmetic gives 45–46. The weather.yaml comment correctly echoes the canonical source's phrasing.
- [TEST] Test-analyzer F1, F2, F3: All three are real observations about missing infrastructure (no automated schema-validation in CI, no smoke test for file existence, schema can't enforce conditions/weights length parity). All three match Dev's own logged delivery findings. None are 24-2 scope — content authoring story with no consumer code. Deferred to a follow-up validator story.

**Tag coverage:** [DOC], [TEST], [RULE] present. [EDGE], [SILENT], [TYPE], [SEC], [SIMPLE] subagents disabled per `workflow.reviewer_subagents` settings — no findings to tag.

**Handoff:** To SM (Prospero) for finish-story.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

No upstream findings at setup.

### Dev (implementation)
- **Improvement** (non-blocking): SM Assessment for 24-2 specified the
  wrong file path (`worlds/glenross/weather.yaml` instead of pack-level
  `weather.yaml`). The schema and epic description both mandate pack-level.
  Affects `pennyfarthing-dist/agents/sm-setup.md` or the prompt template
  that generated this assessment (cross-checking schema placement tables
  when authoring scoping notes would catch this — Sm-setup never read
  `docs/schemas/world-grounding/README.md` before fixing the deliverable
  path). *Found by Dev during implementation.*
- **Gap** (non-blocking): `pf validate world-grounding` does not yet exist
  (deferred per schemas/world-grounding/README.md). Until it lands,
  authors are validating manually with `uvx --from check-jsonschema
  check-jsonschema --schemafile <schema> <yaml>`. Affects future
  validator tooling — when story 24-5 or a Phase 2 validator story lands,
  it should register `world-grounding` alongside the existing `locations`
  validator so weather/demographics/calendar files get automatic CI
  coverage. *Found by Dev during implementation.*
- **Question** (non-blocking): The schema's `effects` array (under
  `specialEvent`) is an open-enum of strings with no registry. I authored
  evocative effect ids (`travel_blocked_north`, `body_discovery_setup`,
  `alibi_complications`, etc.) that read well for the GM panel but won't
  do anything mechanical until 24-5/6 either (a) defines a canonical
  effect vocabulary or (b) treats `effects` as pure narrator prompt
  flavor. If (a), my ids will need a remap pass. If (b), my ids are
  load-bearing prose and should be preserved verbatim. Affects
  `sidequest-server/sidequest/genre/models/scenario.py:132` and whatever
  weather-state shape 24-5 picks. *Found by Dev during implementation.*

### Reviewer (code review)
- **Question** (non-blocking): Three condition labels deliberately shadow
  same-name special_event entries in the same zone+season
  (`gold_afternoon` in glen_floor/autumn, `early_snow` and `whiteout` in
  highland_pass). Per the schema's precedence rule at
  `docs/schemas/world-grounding/weather.schema.json:34`
  ("Sampled before the per-scene roll; if one fires, it takes precedence
  for its duration") this is consistent — events preempt the palette
  sample. 24-5 implementer must honor this precedence explicitly; a
  naïve consumer that samples both channels independently will surface
  ambiguous results. Affects whatever generator/dispatch module 24-5
  builds (likely `sidequest-server/sidequest/genre/` under a new
  `weather/` submodule, parallel to `monster_manual.py`).
  *Found by Reviewer during code review.*
- **Question** (non-blocking): Schema is ambiguous about the cadence of
  the `chance:` field on special_events — it reads "Per-day (or per-scene,
  see 24-5)." Total per-zone event chance sums to 0.51 in glen_floor,
  0.36 in highland_pass; if 24-5 reads these as per-scene independent
  rolls, named events fire ~40-50% of scenes (over-firing). If per-day,
  pacing is realistic. 24-5 must pick one interpretation and document it
  back into the schema. Affects `weather.schema.json` (clarification
  needed) and the new 24-5 generator. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): No automated check guards this file
  against future schema-violating edits. `check-jsonschema` was a
  one-off Dev-time invocation. Pattern to mirror: the `locations`
  validator from story 54-3. Recommend a Phase-2 epic-24 story that
  adds `pf validate world-grounding`, wires it into pre-commit or
  `just check-all`, and back-fills smoke-test coverage for every
  authored YAML under this schema family (weather, demographics,
  calendar). Affects `pf` CLI surface and `.pennyfarthing/scripts/hooks/pre-commit.sh`.
  *Found by Reviewer during code review (re-confirms Dev's own Gap finding).*
- **Improvement** (non-blocking): `sm-setup` (or whatever prompt template
  generated this story's SM Assessment) does not consult the schemas
  README placement table before declaring deliverable paths — leading
  to the pack-vs-world-level confusion that triggered Dev's deviation.
  Recommend the sm-setup template or scoping guide reference
  `docs/schemas/world-grounding/README.md` "File placement convention"
  when the deliverable is a world-grounding YAML. Affects
  `pennyfarthing-dist/agents/sm-setup.md` or whichever prompt covers
  story-scoping for content authoring. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Three small content polish items for
  a future pass (none blocking 24-2 merge): (1) `weather.yaml:61`
  comment cites lore.yaml for the distillery-August phrasing that
  actually lives in world.yaml:11; (2) `drives_indoors` effect label
  on midge_calm names a character outcome rather than an environmental
  condition — rename to `outdoor_activity_intolerable` or `indoor_pressure_high`
  to honor the SOUL.md Test; (3) zone ids `glen_floor` / `highland_pass`
  and the inline comments are heavily glenross-bound at the pack level
  — when a second tea_and_murder world is ever added, refactor to
  add generic-or-additional zones. Affects `weather.yaml`. *Found by
  Reviewer during code review.*