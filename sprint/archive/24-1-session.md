---
story_id: "24-1"
jira_key: ""
epic: "24"
workflow: "trivial"
---
# Story 24-1: Define YAML schemas for world-grounding systems

## Story Details
- **ID:** 24-1
- **Jira Key:** (SideQuest personal — no Jira ticket)
- **Epic:** 24 — Procedural World-Grounding Systems
- **Workflow:** trivial
- **Repos:** sidequest-content, orchestrator
- **Type:** chore
- **Points:** 3

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-19T22:29:58Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-19 | 2026-05-19T22:14:13Z | 22h 14m |
| implement | 2026-05-19T22:14:13Z | 2026-05-19T22:20:56Z | 6m 43s |
| review | 2026-05-19T22:20:56Z | 2026-05-19T22:29:58Z | 9m 2s |
| finish | 2026-05-19T22:29:58Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- **Improvement** (non-blocking): Epic-24 context document
  `sprint/context/context-epic-24.md` is stale (references `low_fantasy`/
  `pinwheel_coast` and a Rust generator). Current-sprint.yaml epic-24
  description names `tea_and_murder`/`glenross` and a Python generator
  (ADR-082 retired Rust). The SM reconciled the divergence in the
  story-24-1 context but the epic context itself still misleads anyone
  who reads it first. Affects `sprint/context/context-epic-24.md`
  (replace world id throughout, replace "Rust generators" with "Python
  generators", refresh the Phase 1 stories table). *Found by Dev
  during implementation.*
- **Question** (non-blocking): PRD §1.1 shows a weather *input* schema
  AND a divergent *output* shape (the runtime injection uses
  `visibility`, `wind`, `narrative_hints` — none of which appear in the
  input rules). I authored the input schema (what story 24-1 owes) but
  the output shape — the prompt-zone payload 24-6 will inject — is
  unstated. Story 24-5 (Python weather generator) needs an output-shape
  decision before it can ship. Affects `docs/schemas/world-grounding/`
  (consider a sibling `weather_output.schema.json` when 24-5 starts).
  *Found by Dev during implementation.*

### Reviewer (code review)

- **Improvement** (non-blocking): The `pf validate context-story <id>`
  subcommand fails on every front-matter context file in the project —
  not specific to this story. `validate_context_file()` in
  `pf/context/validator.py` calls `yaml.safe_load()` on the full
  Markdown without stripping the front matter, so YAML sees the
  closing `---` as a second document and raises "expected a single
  document in the stream". The bulk `pf validate context` runner uses
  a different path and passes cleanly. Affects
  `pennyfarthing-dist/src/pf/context/validator.py:334` (strip front
  matter before `yaml.safe_load`). Not blocking 24-1 — preflight
  worked around it via the bulk path. *Found by Reviewer during code
  review.*
- **Question** (non-blocking): Schema-level cross-file referential
  integrity (weather `season` ids ↔ calendar season ids; economy
  goods ↔ commodity_baseline keys; npc_schedule slot ids ↔ calendar
  `time_precision`) is documented in prose but not enforceable in plain
  JSON Schema. When the future `pf validate world-grounding` validator
  ships, it should add a multi-file referential pass on top of
  per-file schema validation. Affects future validator work — not
  blocking 24-1. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- No deviations from spec.

### Reviewer (audit)

- **Dev declared "No deviations from spec."** → ✓ ACCEPTED by Reviewer:
  audited the full diff against the story-24-1 context. AC-by-AC
  enumeration in the Reviewer Assessment below confirms every spec point
  was honored. No undocumented divergences spotted.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (orchestrator only — content branch untouched):**
- `docs/schemas/world-grounding/README.md` — decision-of-record (AC-3),
  inventory table, file-placement convention, conventions, scope
  exclusions
- `docs/schemas/world-grounding/weather.schema.json` — pack-level
  climate rules (PRD §1.1)
- `docs/schemas/world-grounding/demographics.schema.json` — world-level
  settlement profiles (PRD §1.2)
- `docs/schemas/world-grounding/npc_schedule.schema.json` — archetype
  extension fragment for `schedule_template:` (PRD §1.3, satisfies
  AC-5: schedules embed in `archetypes.yaml`, NOT a new top-level file)
- `docs/schemas/world-grounding/economy.schema.json` — world-level
  trade routes + commodity baseline (PRD §2.1)
- `docs/schemas/world-grounding/establishment_templates.schema.json` —
  pack-level templates for unnamed establishments (PRD §2.2)
- `docs/schemas/world-grounding/calendar.schema.json` — world-level
  timekeeping with `time_precision` enum (PRD §2.3)
- `docs/schemas/world-grounding/quest_shapes.schema.json` — pack-level
  narrative structural templates with `pacing` enum tied to SOUL #10
  (PRD §3.1)
- `sprint/context/context-story-24-1.md` — story context written by
  SM during setup; committed here because it wasn't in the prior
  hygiene sweep
- `sprint/current-sprint.yaml` — status flip (backlog → started),
  branch + assignee metadata; written automatically by sm-setup

**AC-3 decision-of-record (recorded in README):** JSON Schema Draft
2020-12, not pydantic. Rationale: scope discipline (story repos are
content + orchestrator, NOT sidequest-server where pydantic lives),
AC-6 compliance (JSON Schema is inert by construction; pydantic models
would auto-couple via the pack loader), and validator alignment
(`pf validate locations` already consumes JSON Schema in this project).

**Tests:** N/A — trivial workflow chore. Verification was schema
self-validation:
- All 7 files parse as JSON
- All 7 schemas pass Draft 2020-12 metaschema validation
  (`Draft202012Validator.check_schema(s)`)
- All 7 `examples` blocks validate against their own schemas
- `pf validate context` passes (4 passed, 0 errors)

**AC-by-AC coverage:**
- AC-1 (schemas exist for all seven systems) — ✅ seven `.schema.json`
  files
- AC-2 (required vs optional explicit) — ✅ every schema uses
  `required:` arrays and every property has a `description`
- AC-3 (one validation seam chosen + documented) — ✅ README
  decision-of-record names JSON Schema and gives the three-reason
  rationale
- AC-4 (one example per schema) — ✅ every schema has an `examples:`
  block with a copy-paste-ready instance that validates against the
  schema
- AC-5 (NPC schedule extends archetypes.yaml) — ✅
  `npc_schedule.schema.json` is explicitly a fragment describing the
  `schedule_template:` field, with title "(archetype extension)" and a
  long description explaining it does NOT introduce a new top-level
  file
- AC-6 (no consumers yet) — ✅ orchestrator-only changes; no edits to
  `sidequest-server`, no edits to existing genre packs, no edits to
  `pf validate` family
- AC-7 (PRD cross-refs in headers) — ✅ each schema's top-level
  `description` cites the matching PRD section number

**Branch:** `feat/24-1-world-grounding-schemas` (pushed to origin)

**Handoff:** To Colonel Sherman Potter (Reviewer) for review.

## SM Assessment

**Setup complete.** Story 24-1 is the schema-gate for epic 24 (Procedural
World-Grounding). Trivial workflow, 3 points, content + orchestrator repos.

**Branches created:**
- orchestrator: `feat/24-1-world-grounding-schemas` (off main)
- sidequest-content: `feat/24-1-world-grounding-schemas` (off develop)

**Context:**
- Epic context: `sprint/context/context-epic-24.md` (note: stale —
  references `low_fantasy/pinwheel_coast` and Rust generator;
  current-sprint.yaml is authoritative: `tea_and_murder/glenross` and
  Python generator)
- Story context: `sprint/context/context-story-24-1.md` (authored this
  session; reconciles the stale epic context against the current sprint
  description; validates clean via `pf validate context`)
- PRD: `docs/prd/prd-procedural-world-grounding.md` — schema examples
  scattered through §1.1 .. §3.1

**Key constraint flagged to Dev:**
This is a chore, not a feature. AC-6 explicitly requires that nothing
imports the schemas yet — observable behavior should be unchanged after
the story lands. Schemas are documentation + future contracts. The
downstream stories (24-5/6/7) wire them in.

**Open decision routed to Dev (AC-3):**
Pick ONE seam for schemas — JSON Schema files (consumable by `pf validate`)
or pydantic models (consumable by `sidequest-server` at pack-load time).
Pydantic-leaning per the story-context assumption (the server already loads
packs through pydantic models), but Dev decides based on whichever
constraint dominates. Document the choice in the schema headers.

**Scope discipline:** Story title lists seven systems (weather, demographics,
calendar, economy, establishments, quest shapes, NPC schedules). Tier-3
systems (interior topology, world maps) are intentionally NOT in scope —
they are deferred to later phases.

**Handoff:** Major Charles Emerson Winchester III for the implement phase.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (incl. JSON syntax 7/7, Draft 2020-12 metaschema 7/7, internal $refs 7/7, examples-self-validate 7/7) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 returned clean, 8 skipped per `workflow.reviewer_subagents` config — right-sized for a documentation-only chore with no code paths, types, security surface, or test surface to audit)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred (preflight clean; the project rules in `.claude/rules/` and the lang-review checklists do not apply to JSON Schema documents)

## Rule Compliance

`.claude/rules/*.md` and the `lang-review/{python,typescript}` checklists govern code in those languages. The diff touches zero Python, zero TypeScript, zero code of any kind. The applicable rule surface is:

- **CLAUDE.md "No Silent Fallbacks":** N/A — no code branches in diff.
- **CLAUDE.md "No Stubbing":** ✓ Compliant — schemas are complete contracts with required/optional fields explicit. No placeholder TODOs or empty $defs.
- **CLAUDE.md "Don't Reinvent — Wire Up What Exists":** ✓ Compliant — the README cites the existing `pf validate locations` pattern (story 54-3) as the seam these schemas will plug into.
- **CLAUDE.md "Verify Wiring":** N/A — AC-6 explicitly forbids wiring; nothing imports these schemas. Verified by `git diff main...HEAD --name-only | grep -vE '^docs/|^sprint/'` returning empty.
- **CLAUDE.md "Every Test Suite Needs a Wiring Test":** N/A — no test suite is in scope.
- **SOUL.md principles:** N/A for static schema documents.

No rule violations.

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** YAML-author → `*.yaml` file under `genre_packs/<pack>/` (24-2/3/4 will populate; not in this diff) → future `pf validate world-grounding` reads schemas under `docs/schemas/world-grounding/` and validates the YAML → future Python generators (24-5) emit typed state mirroring these contracts. **Today's diff stops at step 1: the contract.** Safe because the contract is inert — nothing consumes it (verified end-to-end).

**Pattern observed:** Mirrors the existing `pf validate locations` JSON-Schema-on-disk pattern from story 54-3. Schemas live under `docs/schemas/world-grounding/` (orchestrator-owned per `repos.yaml`), `$schema` is Draft 2020-12, every schema has `$id`, every named subschema sets `additionalProperties: false` for strict catch-typos, every required field is explicit, every property has a human-readable `description`. README.md authored as the decision-of-record + inventory.

**Error handling:** N/A — no runtime code in diff. Schema-level guards (`minimum`, `maximum`, `minItems`/`maxItems`, closed `enum`) are in place where structurally expressible.

**Observations:**

- `[VERIFIED]` All seven `.schema.json` files pass JSON parsing, Draft 2020-12 metaschema validation, internal `$ref` resolution, and examples-validate-against-own-schema. Confirmed independently by Dev (`uv run --with jsonschema` block) and by preflight subagent. Evidence: every schema with `"$schema": "https://json-schema.org/draft/2020-12/schema"`; `docs/schemas/world-grounding/*.schema.json` lines 2 throughout. AC-1 + AC-2 + AC-4 satisfied.
- `[VERIFIED]` AC-3 decision-of-record at `docs/schemas/world-grounding/README.md:8-30` names JSON Schema (not pydantic) with three concrete reasons: scope discipline, AC-6 compliance (JSON Schema is inert; pydantic auto-couples), validator alignment with existing `pf validate locations`. Rule-compatible with CLAUDE.md's "Don't Reinvent — Wire Up What Exists" — explicit pointer to the existing seam.
- `[VERIFIED]` AC-6 enforced structurally, not just by promise: `git diff main...HEAD --name-only | grep -vE '^docs/|^sprint/'` returns empty. Zero edits to `sidequest-server`, `sidequest-ui`, `sidequest-content`, or `sidequest-daemon`. Nothing imports the schemas. The story is genuinely inert as the AC required.
- `[VERIFIED]` AC-5: `npc_schedule.schema.json:4` titled "NPC Schedule (archetype extension)" and the description explicitly states the schema is a fragment for the `schedule_template:` field embedded in `archetypes.yaml`, "NOT a new top-level YAML file" — preserving the PRD §1.3 intent.
- `[VERIFIED]` AC-7: every schema header carries a `PRD §X.Y` cross-ref. Spot-checked alignment — weather→§1.1, demographics→§1.2, npc_schedule→§1.3, economy→§2.1, establishment_templates→§2.2, calendar→§2.3, quest_shapes→§3.1. All match.
- `[LOW]` Parallel-array invariants are documented in prose but not structurally enforced: `weather.seasonPalette.conditions` length must equal `weights` length; `weather.seasonPalette.temp_range`, `establishment_templates.menuItem.price_range`, and `weather.specialEvent.duration_days` all imply `[min, max]` ordering. JSON Schema's `prefixItems` could tighten the *types* of slots but cannot easily enforce `arr[0] <= arr[1]` or cross-property length parity. Deferred to the future `pf validate world-grounding` validator layer, which can add semantic passes on top. The schema descriptions are clear; an author who reads them will not get this wrong without warning. Not blocking.
- `[LOW]` Cross-file referential integrity (weather `season` ids ↔ calendar season ids; economy `tradeRoute.goods` ↔ `commodity_baseline` keys; npc_schedule slot ids ↔ calendar `time_precision`) is documented but not enforceable per-file. Same disposition — the validator layer is the right home, not the schemas themselves. Story 24-1 properly scopes this as out-of-scope. Not blocking.
- `[LOW]` `npc_schedule.schema.json` is shaped as a complete-document envelope (`{required: ["schedule_template"], properties: {schedule_template: ...}, additionalProperties: false}`) rather than a bare sub-schema. This means it cannot be applied directly to a full archetype record (which carries other fields like name/stats and would fail `additionalProperties: false`). The intended use is `$ref`-splicing the `schedule_template` sub-schema into the future archetype schema. The README and the schema title make the intent clear; the author of the future archetype schema work will need to splice rather than apply-directly. Minor design-of-intent note. Not blocking.
- `[VERIFIED]` `docs/schemas/world-grounding/README.md` inventory table is accurate: seven rows, every named file exists in the diff, every PRD § matches the corresponding schema's header cross-ref. The "What this story explicitly does NOT do" section in the README usefully scopes against future-story creep.
- `[VERIFIED]` Sprint YAML change is minimal and mechanical: `sprint/current-sprint.yaml:321` flips story-24-1 status `backlog → started`, adds `started`, `branch`, `assignee` fields. Output of sm-setup. No structural drift to the rest of the sprint file.
- `[DOC]` Story context `sprint/context/context-story-24-1.md` reconciles the stale epic-24 context (which still references `low_fantasy/pinwheel_coast` and Rust) against the live sprint description (`tea_and_murder/glenross`, Python). Dev correctly logged this as a non-blocking upstream finding for follow-on by Phase-1 epic owners. The story itself stays inside its declared scope.

### Devil's Advocate

Argue this is broken.

A junior content author opens `weather.yaml` for tea_and_murder/glenross. They author `temp_range: [18, 5]` instead of `[5, 18]` — schema validates because the items are merely two `number`s with no ordering constraint. The generator at story 24-5 will sample uniformly between [18, 5]; numpy returns nothing useful and the prompt zone gets a NaN. Authors won't get a warning. Similarly, `weights: [30, 30]` paired with `conditions: ["clear", "rain", "fog"]` produces silent palette truncation downstream. The schemas accept it; only 24-5 will reject it, by which point three more weather YAMLs may have shipped.

Cross-file integrity is worse: a pack author defines `weather.yaml` seasons `spring/summer/autumn/winter` but the world's `calendar.yaml` calls its season "monsoon". Both files validate independently; the narrator gets to "monsoon" and finds no climate palette. The runtime path is undefined — does the generator crash? Pick a random season? Emit empty weather? The schemas have no answer. This is exactly the sort of latent invariant that bites months later in playtest when a corner case finally lights up.

`npc_schedule.schema.json` is shaped as a wrapper envelope (`{schedule_template: ...}`) rather than the sub-schema you'd splice. A future author who tries to validate an archetype record directly against this file will get rejection-by-`additionalProperties: false`. The README and title document the intent, but documentation isn't a contract.

The `time_precision` enum has four values — `hour`, `quarter_day`, `watch`, `scene` — but `npc_schedule.dailyRoutine` slot-ids are open. Author writes `time_precision: "watch"` in calendar.yaml and schedules using `dawn/midday/dusk/night` — both files validate. Generator behavior undefined.

`establishment_templates.schema.json` top-level uses `additionalProperties` openly to permit genre extension. Author misspells `tea_room` as `tearoom` — schema-valid, generator can't find the requested type.

`epoch.month_index` is zero-based; the schema permits any non-negative integer with `minimum: 0`. Author writes `month_index: 13` for a 12-month calendar; schema accepts, runtime confusion.

**Disposition of the Devil's Advocate findings:** All seven point at the same underlying class of issue — JSON Schema cannot express ordering, parallel-array, or cross-file constraints without external validator help. The story's design-of-record explicitly defers semantic validation to the future `pf validate world-grounding` command (logged above as a Reviewer Question finding). The story is graded on its declared scope (the contract, AC-1..AC-7), not on the validator that follows. Severity for all seven: LOW, addressable in the validator layer. None blocks approval.

**AC-by-AC final tally:** 1 ✓, 2 ✓, 3 ✓, 4 ✓, 5 ✓, 6 ✓, 7 ✓.

**Subagent dispatch coverage:** All eight specialist channels accounted for. `[EDGE]` boundary-condition concerns appear as the Devil's Advocate parallel-array and `temp_range` ordering findings, severity LOW. `[SILENT]` silent-failure analysis: no error paths in diff (documentation only), so no swallowed-error surface — verified by preflight (`code_files: 0`). `[TEST]` test-quality analysis: no tests authored or needed (trivial workflow chore, no runtime surface). `[DOC]` documentation: README + per-schema headers + cross-refs all audited above. `[TYPE]` type-design: applied as JSON Schema field-type analysis throughout the observations. `[SEC]` security: no auth/tenant/secrets surface in a static documentation diff. `[SIMPLE]` simplifier: schemas are minimal — every property earns its place; no over-engineered $defs trees. `[RULE]` project rule compliance: enumerated in the Rule Compliance section above, no violations.

**Handoff:** To SM (Hawkeye Pierce) for the finish phase.