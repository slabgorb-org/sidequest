---
story_id: "114-10"
jira_key: null
epic: "114"
workflow: "tdd"
---
# Story 114-10: Apply Fate gear model to pulp_noir, spaghetti_western, tea_and_murder, wry_whimsy

## Story Details
- **ID:** 114-10
- **Title:** Apply Fate gear model to pulp_noir, spaghetti_western, tea_and_murder, wry_whimsy
- **Jira Key:** none (Jira: skipped)
- **Workflow:** tdd (phased)
- **Repos:** server, content
- **Points:** 5
- **Priority:** p3
- **Type:** implementation
- **Depends On:** 114-9 (design complete)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-16T09:36:33Z
**Round-Trip Count:** 3

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-16T14:00:00Z | 2026-06-16T07:21:25Z | -23915s |
| green | 2026-06-16T07:21:25Z | 2026-06-16T08:17:31Z | 56m 6s |
| review | 2026-06-16T08:17:31Z | 2026-06-16T08:29:02Z | 11m 31s |
| green | 2026-06-16T08:29:02Z | 2026-06-16T08:44:02Z | 15m |
| review | 2026-06-16T08:44:02Z | 2026-06-16T09:03:48Z | 19m 46s |
| green | 2026-06-16T09:03:48Z | 2026-06-16T09:10:07Z | 6m 19s |
| review | 2026-06-16T09:10:07Z | 2026-06-16T09:21:22Z | 11m 15s |
| green | 2026-06-16T09:21:22Z | 2026-06-16T09:27:11Z | 5m 49s |
| review | 2026-06-16T09:27:11Z | 2026-06-16T09:36:33Z | 9m 22s |
| finish | 2026-06-16T09:36:33Z | - | - |

## Story Context

### Technical Approach

This story implements the Fate gear model (designed in 114-9, `docs/superpowers/specs/2026-06-15-fate-gear-model-design.md`) for four narrative-first Fate-bound genre packs: **pulp_noir, spaghetti_western, tea_and_murder, and wry_whimsy**. The approach applies three layers of change:

#### Layer 1: Engine (sidequest-server)

The runtime changes are minimal — the design spec defers all heavy lifting to existing Fate machinery:

1. **Model deltas** (`sidequest/game/fate_sheet.py`):
   - Add `AspectKind = Literal["high_concept", "trouble", "character", "situation", "consequence", "boost", "permission"]` (new `"permission"` kind for narrator-read capabilities, never engine gates).
   - Add `source_gear: str | None = None` field to both `Aspect` and `Stunt` (traceability for GM panel lie-detector and item-loss beats).

2. **Schema** (`sidequest/genre/models/inventory.py`):
   - New `GearGrantAspect` model: `text` (aspect phrase) + `kind` ("character" or "permission").
   - New `GearGrantStunt` model: `name` + `description` (no per-stunt cost field — cost is the count against `free_stunts`).
   - New `GearDef` model: `id`, `name`, `description`, `grants_aspects[]`, `grants_stunts[]`. No provenance field (every GearDef is bespoke-by-construction; Fate Core SRD has no equipment chapter).
   - Load and merge `gear.yaml` (genre + world tier, merged by `id` per ADR-145 D3 paradigm-neutral merge).

3. **Chargen compile** (in character creation flow):
   - For the chosen archetype, resolve `archetype.gear: [ids]` against merged `GearDef` set.
   - Materialize each `GearDef`: append `grants_aspects` entries to `FateSheet.aspects` (with `kind`, `source_gear` set); append `grants_stunts` entries to `FateSheet.stunts` (with `source_gear` set).
   - Validate **refresh invariant**: `refresh == base_refresh − max(0, total_stunts − free_stunts)`, where `total_stunts` = authored stunts + gear-granted stunts. Aspect-gear is free by construction; stunt-gear debits refresh (the only balance story).
   - Emit `fate.gear_compiled` OTEL span (attributes: archetype, per-GearDef: gear_id, aspects_placed, stunts_added, refresh_before/after/debited, permission_aspects count).

4. **Content validator** (`sidequest-validate`):
   - Fail loud if a `ruleset: fate` pack ships `inventory.yaml` (paradigm mismatch, No Silent Fallbacks).
   - Refresh invariant check: every archetype's authored refresh must satisfy the formula above.
   - Dangling gear ID check: no archetype references a gear `id` that does not exist in the merged `GearDef` set.
   - Permission-not-gated check: no resolver code path ever refuses an action for a missing permission aspect (The Zork Problem).

#### Layer 2: Content Migration (sidequest-content)

Per pack (pulp_noir, spaghetti_western, tea_and_murder, wry_whimsy):

1. **rules.yaml binding**:
   - Set `ruleset: fate`.
   - Remove `ruleset: native` or the entire `native:` block (no native engine on Fate path).
   - Add `fate:` block:
     ```yaml
     fate:
       base_refresh: 3          # SRD default; can be tuned per genre tone
       free_stunts: 3           # stunts free at base_refresh before refresh debited
     ```

2. **Inventory deletion**:
   - Delete `inventory.yaml` at both genre and world tiers.
   - Remove `starting_gold`, `currency`, `starting_equipment`, `item_catalog`, `philosophy` from any config (InventoryConfig is gone; Fate has no economy).

3. **Gear authoring** (`gear.yaml`):
   - **Genre tier:** shared signature gear (the coat, the badge, the tools, the hat — the archetypal flavor each archetype inherently carries).
   - **World tier:** world-distinct gear (optional; left empty if all gear is archetype-bundled). Example (wry_whimsy/oz, future-optional): the silver shoes as a `GearDef` with `findable: false` and an aspect grant (not a stunt — it is free and inert until found mid-game; the found path uses `create-an-advantage` anyway).
   - Schema per `GearDef`: `id` (unique within the pack, e.g. `noir_fedora`), `name` (presentation), `description` (flavor), `grants_aspects: [{text, kind}]`, `grants_stunts: [{name, description}]`.

4. **Archetype wiring** (`archetypes.yaml`):
   - Add `fate:` block to each archetype (alongside, not replacing, the existing archetype model):
     ```yaml
     fate:
       gear: [gear_ids...]       # list of gear IDs to grant at chargen
     ```
   - Each archetype already has an authored `refresh` (from 121-6 interactive Fate chargen). Validate it satisfies the refresh invariant for the gear it bundles.

5. **Validation** (`sidequest-validate` content validator):
   - No `inventory.yaml` under a fate pack.
   - Every archetype's refresh balances per the invariant.
   - No gear ID dangles (every id referenced is in the merged `GearDef` set).
   - No resolver path reads permission aspects as gates.

#### Layer 3: Scope Boundaries

**Out of scope (explicitly stated in spec):**
- Per-genre skill lists, aspects guidance, stunts authoring beyond gear (ADR-144 F4 territory; 121-6 settled interactively chargen separately).
- UI surfaces for gear/aspects (ADR-144 F3; separate stories).
- Wholesale `native` deletion (ADR-144 F5 — stays separate, gated).
- Carried inventory or mid-game gear economy (chargen-only; mid-game uses `create-an-advantage` / milestones, already in F1).

---

## Per-Pack Scope

### pulp_noir
- **Tone:** classic hardboiled detective noir (Spirit of the Century era Fate).
- **Likely gear archetype:** fedora, trench coat, smoking gun, contacts list, dame's lipstick kiss. Permission aspect: "Private investigator's license."
- **Worldbuilding:** 1950s urban, jazz-soaked.
- **Expected refresh:** 3 (SRD default, likely tuned down to 2 if genre reads darker).

### spaghetti_western
- **Tone:** operatic, dust-and-gunsmoke Leone standoff (Fate Core ships western support; conflict resolves on nerve and reputation, not HP).
- **Likely gear archetype:** weathered hat, saddlebags, the worn pistol with a history, a wanted poster with your face.
- **Worldbuilding:** high-desert, frontier honor codes.
- **Expected refresh:** 3.

### tea_and_murder
- **Tone:** cozy mystery, amateur sleuth, often female-led.
- **Likely gear archetype:** teapot and good china, notebook, the late victim's final letter, the vicar's gossip.
- **Worldbuilding:** English village, post-war/modern, tight-knit community.
- **Expected refresh:** 3 (though cozy rarely does combat, so refresh economy is largely idle; validate it anyway).

### wry_whimsy
- **Tone:** comedic, absurdist (Baum's Oz, not MGM's; Dorothy is a portal-hopper with agency, not a victim). Fate's aspects and compels drive comedy.
- **Likely gear archetype:** the gingham dress (aspect), the ruby shoes (either chargen or mid-game via `create-an-advantage`; if chargen, it's aspect-gear only — no power-gamer "teleport" stunt).
- **Worldbuilding:** fantastical, lighthearted, permission-aspects drive narrative ("the yellow brick road lets you walk it"; "the poppy field puts you to sleep").
- **Expected refresh:** 3, possibly 2 if the tone is lighter (author decision).

---

## Acceptance Criteria

Each must be demonstrable and OTEL-visible (the GM panel lie-detector proves gear fired):

1. **Engine models are extended (sidequest-server):**
   - `AspectKind` now includes `"permission"` literal.
   - `Aspect` and `Stunt` both carry `source_gear: str | None` field (None for hand-authored, str for gear-compiled).
   - `GearDef`, `GearGrantAspect`, `GearGrantStunt` are defined in `sidequest/genre/models/inventory.py`, strict with `extra="forbid"`.
   - `gear.yaml` is loaded and merged (genre + world, by `id`, reusing ADR-145 D3 paradigm-neutral merge).

2. **Chargen compile is wired (sidequest-server):**
   - Character creation resolves archetype `gear: [ids]` → merged `GearDef` set (fail loud on unknown id).
   - For each `GearDef`: aspects are appended to `FateSheet.aspects` with `kind` + `source_gear`; stunts to `FateSheet.stunts` with `source_gear`.
   - Refresh invariant is computed and validated (formula: `base_refresh − max(0, total_stunts − free_stunts)`, floor per SRD).
   - `fate.gear_compiled` OTEL span is emitted (archetype, gear_id, aspects_placed, stunts_added, refresh deltas, permission_aspect count).
   - **Wiring test:** a `ruleset: fate` pack's chargen path creates a character, bundles gear, and the span appears in OTEL.

3. **Content validator is enforced:**
   - `sidequest-validate` fails loud if a `ruleset: fate` pack ships `inventory.yaml`.
   - Refresh invariant check passes for every archetype in every pack.
   - Dangling gear ID check passes (no archetype references a missing id).
   - Permission-not-gated check passes (no resolver path reads permission as a gate).

4. **All four packs are migrated (sidequest-content):**
   - **pulp_noir:** `ruleset: fate`, `rules.yaml` has `fate: {base_refresh, free_stunts}`, no `native:` block, `inventory.yaml` deleted (genre + world), `gear.yaml` authored (genre-tier shared gear), archetypes wired with `fate: {gear: [ids]}` and authored refresh.
   - **spaghetti_western:** same as pulp_noir.
   - **tea_and_murder:** same as pulp_noir.
   - **wry_whimsy:** same as pulp_noir (may have optional world-tier gear if worlds are distinct; oz world might pre-author silver shoes as aspect-only gear, though mid-game placement via `create-an-advantage` is the spec-intended path).

5. **No validation errors from the pack validator:**
   - `sidequest-validate` runs clean on all four packs.
   - All archetypes balance their refresh against their gear.
   - All referenced gear IDs exist.

6. **GM panel can prove gear fired:**
   - A test session with a Fate character logs the `fate.gear_compiled` span.
   - The span attributes show which gear was materialized, which aspects placed, which stunts added, and the refresh delta.
   - The character's `FateSheet.aspects` and `FateSheet.stunts` carry `source_gear` pointers.

---

## TEA Assessment

**Tests Required:** Yes
**Reason:** Engine models + compile logic + validator + a four-pack migration — a behavior-rich contract.

**Test Files:**
- `tests/game/test_fate_gear_model.py` — model deltas: `AspectKind += "permission"`, `source_gear` on Aspect/Stunt, `GearDef`/`GearGrantAspect`/`GearGrantStunt` (strict, no economy fields), `FateConfig.base_refresh`/`free_stunts`.
- `tests/telemetry/test_fate_gear_compiled_span.py` — `fate_gear_compiled_span` emit + `SPAN_ROUTES["fate.gear_compiled"]` route (GM-panel lie detector).
- `tests/game/ruleset/test_fate_gear_compile.py` — chargen compile: materialize aspects/stunts with `source_gear`, the refresh invariant (`base_refresh − max(0, total_stunts − free_stunts)`, SRD floor), fail-loud on unknown gear id (no partial mutation), span emission.
- `tests/genre/test_fate_gear_loader.py` — `resolve_gear` genre/world by-id merge (world overrides, union, no dup ids).
- `tests/cli/validate/test_fate_gear_validator.py` — the four validator checks (no-inventory-under-fate, refresh invariant, dangling gear id, permission-never-a-gate behavioral).
- `tests/integration/test_114_10_four_pack_fate_gear.py` — parametrized real-pack end-state for all 4 packs: ruleset==fate, no inventory.yaml (genre + world), gear.yaml present + `GenrePack.gear` loaded, built PC gets a FateSheet with gear-sourced entries, pack loads + structural validate clean.

**Tests Written:** 6 files, ~50 tests covering all 6 ACs.
**Status:** RED (verified by testing-runner — all six files fail for the right reasons; zero test-file bugs; the 5 unit/span files fail on missing new symbols, the integration file's 14/44 passing tests prove the harness is sound).

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #1 silent exception swallowing | `test_unknown_gear_id_raises`, `test_fate_pack_with_inventory_is_an_error` (No Silent Fallbacks) | RED |
| #3 type annotation gaps at boundaries | `TestGearDef`, `TestAspectPermissionKind` (strict Literal/typed models) | RED |
| #6 test quality | Phase-C self-check: every test asserts a concrete value (no vacuous/`assert True`/always-None) | clean |
| #8 unsafe deserialization | `test_extra_forbidden`, `test_no_equipment_economy_fields` (extra="forbid" rejects YAML extras) | RED |
| #11 input validation at boundaries | `test_unknown_aspect_kind_still_rejected`, `test_rejects_non_character_non_permission_kind`, unknown-gear fail-loud | RED |

**Rules checked:** 5 of 5 applicable lang-review rules have test coverage (2/4/5/7/9/10/12/13 N/A — no mutable-defaults/logging-4xx/path-traversal/resource-handles/async/import-cycles/new-deps/regression surface in scope).
**Self-check:** 0 vacuous tests found.

**Wiring tests:** `test_114_10_four_pack_fate_gear.py` (built PC carries gear-sourced sheet entries via the production builder; real validator runs on real packs) + `test_compile_emits_fate_gear_compiled_span` + `test_span_is_routed_for_the_gm_panel` — proving the engine pieces are reachable from production paths, not just unit-correct.

**Handoff:** To Dev (Naomi Nagata) for GREEN. Mind the **blocking Delivery Finding**: full-scope absorbs 121-3/4/5 (native→fate migration of the 3 still-native packs) + 121-7 (Fate-archetype shape). The engine half (models/compile/span/validator) is unblocked; the content half is a large migration.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (blocking): 114-10's realized scope is ~6-8× its 5-point estimate. The Operator chose full-scope (2026-06-16), so this story absorbs **121-3/4/5** (native→fate migration of spaghetti_western, tea_and_murder, wry_whimsy — all still native d20 on disk) and **121-7** (the Fate-archetype shape with authored `refresh` + `fate.gear` wiring). Only pulp_noir is currently `ruleset: fate`. The story's `depends_on` lists only 114-9 (design); the three migrations + interactive-chargen engine are its real content prerequisites and are still backlog. Affects `sprint/epic-114.yaml` (re-point / re-link) and `sprint/epic-121.yaml` (121-3/4/5/7 are now subsumed — reconcile to avoid double-work). *Found by TEA during test design.*
- **Gap** (non-blocking): `sidequest-content/pack_schema.yaml` lists `inventory.yaml` as a REQUIRED genre file. Dropping it for fate packs will make the structural validator (`validate_pack_structure`) report a missing-required-file error unless the schema makes `inventory.yaml` conditional (absent for `ruleset: fate`) and treats `gear.yaml` as its fate-tier replacement. Affects `sidequest-content/pack_schema.yaml` and `sidequest/cli/validate/pack.py`. Pinned by `test_114_10_four_pack_fate_gear.py::TestValidatorClean::test_structural_validator_reports_no_errors`. *Found by TEA during test design.*
- **Question** (non-blocking): the Fate-archetype shape (`refresh` int + `fate: {gear: [ids]}` block) does not exist in the current archetype model — every pack's `archetypes.yaml` is the legacy native shape (`stat_ranges`, `typical_classes`, `ocean`). Dev must define it; the 121-6 design (`docs/superpowers/specs/2026-06-16-fate-interactive-chargen-design.md`) is the reference for the archetype-as-editable-template + refresh/stunt economy. My validator tests intentionally take primitive inputs (numbers, id lists) so they do NOT couple to whichever field names Dev chooses. Affects `sidequest/genre/models/` archetype model + the four packs' `archetypes.yaml`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): 121-7 (interactive Fate chargen — per-archetype skill-pyramid allocation, player-authored aspects, stunt selection, per-archetype gear bundling) is NOT delivered by 114-10. I implemented **pack-default** gear (`rules.fate.gear` — the shared signature kit every PC of a pack receives), which satisfies the gear model + refresh invariant end-to-end, but the archetype-as-editable-template with per-archetype refresh remains 121-7 work. 121-7 was kept `backlog` (not cancelled). Affects future chargen UX + `sidequest/genre/models/` archetype model. *Found by Dev during implementation.*
- **Improvement** (non-blocking): the server suite has a flaky parallel test `tests/server/test_space_opera_melee_e2e.py::test_melee_resolves_on_hp_depletion_with_otel` — passes serially (verified twice) but intermittently fails under `pytest-xdist`. Pre-existing (space_opera/SWN, untouched by 114-10); flagged so review doesn't attribute it to this story. *Found by Dev during implementation.*
- **Note**: baseline `develop` carries **260 pre-existing failures + 3 errors** (WN-owns-the-round in-flight per ADR-143/114; `_FakeClaudeClient` missing `send_stateless` SDK-fixture drift). 114-10 adds **zero net-new failures** and incidentally **fixes 1** (`test_fate_action_handler_wiring::test_handler_drives_dispatch_end_to_end`). Proven by full-suite node-id diff against baseline (commit 45c78bec + content efe9b91). *Found by Dev during implementation.*
- No new upstream findings during round-trip-1 rework — the pass cleared Reviewer findings only (dead-code removal + test tightenings + doc nits); the engine math, fail-loud paths, strict models, and OTEL routing were unchanged. Net-zero regression re-proven (260→259, +1 fix). *Found by Dev during rework.*
- No new upstream findings during round-trip-2 rework — cleared the rt1 REJECT (residual "merged" over-claim in `check_dangling_gear_ids` + the SPAN_ROUTES actor-coverage gap + two LOW test cosmetics). No production behavior changed (docstring + error-string + test assertions only). Net-zero regression re-proven (net-new vs baseline empty). *Found by Dev during rework.*
- No new upstream findings during round-trip-3 rework — cleared the rt2 REJECT exhaustively (all 5 "merged" over-claims purged, verified by a `grep -rn "merged"` acceptance gate returning zero; `gear_ids` added to the SPAN_ROUTES projection so the GM panel surfaces which gear fired; `match=` parity). One additive production change (route lambda now extracts `gear_ids`); net-zero regression re-proven (net-new vs baseline empty). *Found by Dev during rework.*

### Reviewer (code review)
- **Gap** (blocking): `resolve_gear` (`sidequest/game/ruleset/fate_gear.py`) has NO production consumer — the loader populates `FateConfig.gear_catalog` from genre-tier gear only (`loader.py:2042`) and `_load_single_world` never loads a world-tier `gear.yaml`. The world-tier gear merge the design specs is unwired dead code, and three docstrings (fate_gear.py module, `FateConfig.gear_catalog`, `GenrePack.gear`) claim a "genre + world merge" that does not happen. Affects `sidequest/game/ruleset/fate_gear.py`, `sidequest/genre/loader.py`, `sidequest/genre/models/{rules,pack}.py` (wire world-tier gear loading OR remove `resolve_gear` + `tests/genre/test_fate_gear_loader.py` and correct the docstrings to "genre-tier only"). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `refresh_debited` on the `fate.gear_compiled` span reports the clamped reduction (`base_refresh − refresh_after`), which undercounts the true stunt overrun when the SRD floor clamps (base=3/free=0/4 stunts → reports 2, overrun is 4). No pack ships stunt-gear today so the path is unexercised; clarify the span semantic or report the unclamped overrun. Affects `sidequest/game/ruleset/fate_gear.py`. *Found by Reviewer during code review.* (rt1: addressed by clarifying comment — span reports the actual post-floor reduction by design; accepted.)
- **Gap** (blocking, round-trip 1): the round-0 over-claim was only 3/4 cleared — `check_dangling_gear_ids` docstring + its author-facing error string still say "merged" when gear is genre-tier only. Affects `sidequest/cli/validate/fate_gear.py:72,77` (replace "merged" → "genre-tier"). *Found by Reviewer during code review (round-trip 1).*
- **Improvement** (non-blocking, round-trip 1): `test_span_is_routed_for_the_gm_panel` never asserts the SPAN_ROUTES lambda extracts `actor`, despite this rework declaring `actor` a load-bearing GM-panel field — the only coverage of the route's actor passthrough. Affects `tests/telemetry/test_fate_gear_compiled_span.py:86` (assert `extracted['actor']`). *Found by Reviewer during code review (round-trip 1).* (rt2: addressed — actor + extracted fields now asserted.)
- **Gap** (blocking, round-trip 2): the rt1 "merged" over-claim fix was incomplete — 2 PRODUCTION instances remain (`game/ruleset/fate_gear.py:39` GearCompileError docstring; `cli/validate/fate_gear.py:14` module docstring check #3) plus 3 test design-recounts (`test_fate_gear_validator.py:11`, `test_fate_gear_compile.py:5` and `:30`). Affects the gear-surface docstrings (replace "merged"→"genre-tier"); acceptance is a clean `grep -rn "merged"` over the gear files. *Found by Reviewer during code review (round-trip 2).*
- **Improvement** (non-blocking, round-trip 2): `gear_ids` is emitted on the `fate.gear_compiled` span but the `SPAN_ROUTES` projection lambda omits it, so the GM panel can't surface which gear fired from the routed event. Affects `sidequest/telemetry/spans/fate.py:396-403` (add `gear_ids` to the extract dict + assert it). *Found by Reviewer during code review (round-trip 2).* (rt3: RESOLVED — `gear_ids` now projected + asserted.)
- **Improvement** (non-blocking, round-trip 3): two surviving LOW niceties, neither gating — (1) `test_span_attributes_capture_a_refresh_debit` doesn't assert `refresh_before` (already covered by `test_span_emits_with_attributes`); (2) `compile_gear_onto_sheet` doesn't dedup `gear_ids` and `gear_catalog` is author-overwritable (no pack ships dup ids; validator unaffected). Reasonable future hardening. Affects `tests/telemetry/test_fate_gear_compiled_span.py`, `sidequest/game/ruleset/fate_gear.py`. *Found by Reviewer during code review (round-trip 3).*
- No blocking upstream findings at rt3 APPROVAL — the rt1→rt3 saga was a documentation-accuracy convergence ("merged" over-claim), now fully purged (grep gate zero); the OTEL `gear_ids` gap is closed; net-zero regression holds. *Found by Reviewer during code review (round-trip 3).*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

8 deviations

- **Validator checks pinned as pure functions, not against the archetype model**
  - Rationale: the Fate-archetype shape is 121-7 territory and undefined on disk; decoupling keeps the tests refactor-stable and lets Dev choose the archetype field names. The integration test proves the wiring against real packs.
  - Severity: minor
  - Forward impact: Dev wires these pure checks into the CLI validator + loader; a wiring test (the integration suite running the real validator) guards against them becoming dead code.
- **Compile entry point shape is TEA-chosen (`compile_gear_onto_sheet` / `resolve_gear` in a new `fate_gear.py`)**
  - Rationale: the design names the step but not a signature; this shape mirrors the existing `seed_chargen_resources`/span conventions and is unit-testable in isolation. The test encodes intent — Dev may rename, but the behavior (materialize with source_gear, compute refresh invariant, emit span, fail loud on unknown id) is the contract.
  - Severity: minor
  - Forward impact: Dev must wire the compile into the production chargen/builder path (the integration test's "built character has gear-sourced entries" is the wiring proof).
- **Permission-not-gated tested behaviorally, not by source inspection**
  - Rationale: the project forbids source-text wiring assertions; a behavioral proof survives refactor and fails on real breakage.
  - Severity: minor
  - Forward impact: none.
- **Per-genre skill lists NOT pinned (test omission, deliberate)**
  - Rationale: skill-list authoring is content design (the writer/scenario-designer lane), not a 114-10 engine/gear contract; over-pinning would couple the test to author choices and duplicate the 121-x ACs. The 121-2 pulp_noir test already pins pulp_noir's signature skills as its regression net.
  - Severity: minor
  - Forward impact: if the Operator wants per-pack skill lists enforced by test, that is a separate content-validation story; flagged here so the omission is explicit, not accidental.
- **Pack-default gear instead of per-archetype archetype-bundled gear (K-i partial)**
  - Rationale: the per-archetype editable-template shape (refresh allocation, per-archetype gear/stunt selection) IS 121-7 (interactive Fate chargen), which is not built. Pack-default "shared signature gear each archetype inherently carries" is a legitimate, honest subset that delivers the full gear model (compile + refresh invariant + span + source_gear traceability) end-to-end without stubbing the unbuilt archetype layer.
  - Severity: major (scope) — narrows the titular "apply to archetypes" to "apply to packs"
  - Forward impact: 121-7 (kept backlog) adds per-archetype gear with NO schema change — `FateConfig.gear` becomes the default and an archetype `fate.gear` overrides it; the compile fn already takes an explicit `gear_ids` list, so per-archetype wiring is a caller change only.
- **All authored gear is aspect-/permission-only (no stunt-gear shipped)**
  - Rationale: aspect-gear is the genre-true signature kit for these four narrative packs (coats, badges, notebooks — flavor, not mechanical advantage). Stunt-gear is available to authors but unused now (YAGNI); the validator enforces the invariant the moment any pack adds it.
  - Severity: minor
  - Forward impact: none — the debit path is live and tested.
- **wry_whimsy native confrontations block restored; tea_and_murder d20 class-kit test deleted (test reconciliation)**
  - Rationale: keeping native confrontation blocks as typed Fate flavor is consistent across all 4 packs and respects the F5 scope boundary; the class-kit test's subject is intentionally gone.
  - Severity: minor
  - Forward impact: F5 (wholesale native removal) will later drop these confrontation blocks + retire the verbal-confrontation tests together.
- **World-tier gear merge removed (`resolve_gear` deleted) — gear is genre-tier only (round-trip 1)**
  - Rationale: Reviewer round-trip-1 HIGH finding — `resolve_gear` had zero production consumers (dead code) and the docstrings over-claimed a merge the loader never performed (Verify Wiring / no half-wired features). No pack authors world-distinct gear, and the design defers the one example (Oz silver shoes) to mid-game `create-an-advantage` placement (YAGNI). Reviewer explicitly recommended removal over wiring.
  - Severity: minor
  - Forward impact: a future world-tier-gear story re-adds the by-id merge as a loader change (load world `gear.yaml`, merge, inject the merged set) — the compile fn already takes an explicit `gear_ids` list against a single GearDef set, so no compile-fn change is needed.

## Design Deviations

No deviations at setup; the story implements the design spec as written (114-9, `2026-06-15-fate-gear-model-design.md`).

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Validator checks pinned as pure functions, not against the archetype model**
  - Spec source: `2026-06-15-fate-gear-model-design.md` §"Chargen compile + the refresh invariant" / §Validator
  - Spec text: "for every archetype, given base_refresh and free_stunts ... the archetype's authored net refresh MUST equal base_refresh − max(0, total_stunts − free_stunts)"
  - Implementation: `check_refresh_invariant` / `check_dangling_gear_ids` / `check_no_inventory_under_fate` take primitive inputs (ints, id sets, bool) instead of a Fate-archetype object.
  - Rationale: the Fate-archetype shape is 121-7 territory and undefined on disk; decoupling keeps the tests refactor-stable and lets Dev choose the archetype field names. The integration test proves the wiring against real packs.
  - Severity: minor
  - Forward impact: Dev wires these pure checks into the CLI validator + loader; a wiring test (the integration suite running the real validator) guards against them becoming dead code.
- **Compile entry point shape is TEA-chosen (`compile_gear_onto_sheet` / `resolve_gear` in a new `fate_gear.py`)**
  - Spec source: design §"Decomposition handed to 114-10", items 1 & 3
  - Spec text: "Chargen compile step + fate.gear_compiled span" / "gear.yaml loader + genre/world by-id merge reuse"
  - Implementation: a module-level `compile_gear_onto_sheet(sheet, *, archetype, gear_ids, gear_defs, base_refresh, free_stunts, ...)` returning a `GearCompileResult`, plus `resolve_gear(genre_gear, world_gear)`.
  - Rationale: the design names the step but not a signature; this shape mirrors the existing `seed_chargen_resources`/span conventions and is unit-testable in isolation. The test encodes intent — Dev may rename, but the behavior (materialize with source_gear, compute refresh invariant, emit span, fail loud on unknown id) is the contract.
  - Severity: minor
  - Forward impact: Dev must wire the compile into the production chargen/builder path (the integration test's "built character has gear-sourced entries" is the wiring proof).
- **Permission-not-gated tested behaviorally, not by source inspection**
  - Spec source: design §P-i / SOUL.md "The Zork Problem"; project rule "No Source-Text Wiring Tests"
  - Spec text: "no resolver path may refuse an action for a missing permission aspect"
  - Implementation: assert a `kind="permission"` aspect invokes for +2 through the normal `FateRulesetModule.invoke_aspect` path (proving it is an ordinary invokable aspect, never a special gate) instead of grepping resolver source for a permission read.
  - Rationale: the project forbids source-text wiring assertions; a behavioral proof survives refactor and fails on real breakage.
  - Severity: minor
  - Forward impact: none.
- **Per-genre skill lists NOT pinned (test omission, deliberate)**
  - Spec source: 121-3/4/5 ACs (the absorbed migrations) specify per-genre Fate skill lists; design §"Out of scope" defers F4 skill authoring.
  - Spec text: e.g. 121-5 "Leone-standoff skills (Shoot/Ride/Physique/Provoke/Notice/Will)".
  - Implementation: the integration test asserts only the structural fate-binding contract (ruleset==fate, non-empty skills, routes to fate_conflict) — it does NOT pin specific skill names per pack.
  - Rationale: skill-list authoring is content design (the writer/scenario-designer lane), not a 114-10 engine/gear contract; over-pinning would couple the test to author choices and duplicate the 121-x ACs. The 121-2 pulp_noir test already pins pulp_noir's signature skills as its regression net.
  - Severity: minor
  - Forward impact: if the Operator wants per-pack skill lists enforced by test, that is a separate content-validation story; flagged here so the omission is explicit, not accidental.

### Dev (implementation)
- **Pack-default gear instead of per-archetype archetype-bundled gear (K-i partial)**
  - Spec source: design §K-i ("Starting gear is archetype-bundled, refresh priced in"); story context Layer 2 step 4 ("archetype wiring: fate.gear per archetype")
  - Spec text: "A pack's archetypes carry their signature gear; the gear-stunts are already accounted for in that archetype's authored refresh."
  - Implementation: gear is declared once at the pack level (`rules.fate.gear` → ids resolved against `gear.yaml`) and compiled onto every PC of that pack at chargen. There is no per-archetype `fate.gear` block (the Fate-archetype shape is undefined — 121-7 territory).
  - Rationale: the per-archetype editable-template shape (refresh allocation, per-archetype gear/stunt selection) IS 121-7 (interactive Fate chargen), which is not built. Pack-default "shared signature gear each archetype inherently carries" is a legitimate, honest subset that delivers the full gear model (compile + refresh invariant + span + source_gear traceability) end-to-end without stubbing the unbuilt archetype layer.
  - Severity: major (scope) — narrows the titular "apply to archetypes" to "apply to packs"
  - Forward impact: 121-7 (kept backlog) adds per-archetype gear with NO schema change — `FateConfig.gear` becomes the default and an archetype `fate.gear` overrides it; the compile fn already takes an explicit `gear_ids` list, so per-archetype wiring is a caller change only.
- **All authored gear is aspect-/permission-only (no stunt-gear shipped)**
  - Spec source: design §"refresh invariant" (stunt-gear debits refresh)
  - Spec text: "Stunt-gear MUST debit refresh."
  - Implementation: the engine fully implements + tests the stunt-gear refresh-debit path (`test_fate_gear_compile.py::TestRefreshInvariant`), but no pack authors stunt-gear — all four packs ship aspect/permission gear only, so every pack's refresh stays at base (3).
  - Rationale: aspect-gear is the genre-true signature kit for these four narrative packs (coats, badges, notebooks — flavor, not mechanical advantage). Stunt-gear is available to authors but unused now (YAGNI); the validator enforces the invariant the moment any pack adds it.
  - Severity: minor
  - Forward impact: none — the debit path is live and tested.
- **wry_whimsy native confrontations block restored; tea_and_murder d20 class-kit test deleted (test reconciliation)**
  - Spec source: design §"Boundary against ADR-144 F5" (native machinery stays); CLAUDE.md test-reconciliation precedent (caverns WWN migration, commit 13604312)
  - Spec text: "they do NOT delete native.py or the dial/beat/reprisal machinery. F5 stays separate."
  - Implementation: restored wry_whimsy's `confrontations:` block (the migration subagent over-removed it; spaghetti_western/tea_and_murder kept theirs) to fix 9 native-verbal-confrontation tests; deleted `test_tea_and_murder_class_kits.py` (asserts the d20 equipment economy the migration removes — no Fate analog).
  - Rationale: keeping native confrontation blocks as typed Fate flavor is consistent across all 4 packs and respects the F5 scope boundary; the class-kit test's subject is intentionally gone.
  - Severity: minor
  - Forward impact: F5 (wholesale native removal) will later drop these confrontation blocks + retire the verbal-confrontation tests together.
- **World-tier gear merge removed (`resolve_gear` deleted) — gear is genre-tier only (round-trip 1)**
  - Spec source: 114-9 design §"Decomposition handed to 114-10" item 3 ("gear.yaml loader + genre/world by-id merge reuse"); story context Layer 1 step 2
  - Spec text: "Load and merge ``gear.yaml`` (genre + world tier, merged by ``id`` per ADR-145 D3 paradigm-neutral merge)."
  - Implementation: removed the `resolve_gear` genre/world merge helper (and its unit test `tests/genre/test_fate_gear_loader.py`); gear is loaded at the genre tier only (`loader._load_gear` → `GenrePack.gear` → `FateConfig.gear_catalog`). World-tier `gear.yaml` loading/merge is deferred to a future story; the three docstrings that claimed the merge were corrected to "genre-tier only".
  - Rationale: Reviewer round-trip-1 HIGH finding — `resolve_gear` had zero production consumers (dead code) and the docstrings over-claimed a merge the loader never performed (Verify Wiring / no half-wired features). No pack authors world-distinct gear, and the design defers the one example (Oz silver shoes) to mid-game `create-an-advantage` placement (YAGNI). Reviewer explicitly recommended removal over wiring.
  - Severity: minor
  - Forward impact: a future world-tier-gear story re-adds the by-id merge as a loader change (load world `gear.yaml`, merge, inject the merged set) — the compile fn already takes an explicit `gear_ids` list against a single GearDef set, so no compile-fn change is needed.

### Reviewer (audit)
- **TEA: validator checks as pure functions** → ✓ ACCEPTED: decoupling from the undefined Fate-archetype shape is sound; the integration test proves the wiring.
- **TEA: compile entry-point shape (`compile_gear_onto_sheet`/`resolve_gear`)** → ✓ ACCEPTED for `compile_gear_onto_sheet`; ✗ FLAGGED for `resolve_gear` — it was authored + unit-tested but never wired into the loader (dead code). See the blocking finding below.
- **TEA: permission-not-gated tested behaviorally** → ✓ ACCEPTED: behavioral proof is correct and rule-checker independently verified no resolver gates on `kind=="permission"`.
- **TEA: per-genre skill lists not pinned** → ✓ ACCEPTED: skill-list authoring is content design; over-pinning would duplicate 121-x ACs.
- **Dev: pack-default gear instead of per-archetype (K-i partial)** → ✓ ACCEPTED: honest subset; the full gear model (compile + invariant + span + traceability) is delivered end-to-end, and per-archetype gear is a caller-only change later. Major-scope deviation is well-documented.
- **Dev: aspect-/permission-only gear (no stunt-gear)** → ✓ ACCEPTED: the debit path is live + tested; YAGNI for content. (Note: the untested floor-clamp `refresh_debited` semantic surfaces only with stunt-gear — see findings.)
- **Dev: wry_whimsy confrontations restored / class-kit test deleted** → ✓ ACCEPTED: consistent with the F5 boundary and the caverns reconciliation precedent. Minor doc nit: the restore comment says "typed Fate flavor" but the beats use native stat names — flagged as a LOW doc finding.
- **Dev (rt1): World-tier gear merge removed (`resolve_gear` deleted) — gear is genre-tier only** → ✓ ACCEPTED by Reviewer: this is exactly the round-0 recommendation (remove the dead helper + its test, correct docstrings to genre-tier-only, defer world-tier merge as YAGNI). Verified the removal is complete — `resolve_gear` has zero references repo-wide and no dangling imports (rule-checker grep) — and the forward-impact note is correct (re-adding the by-id merge is a loader-only change). CAVEAT: the docstring correction the deviation depends on is itself **incomplete** — `check_dangling_gear_ids` still says "merged" (round-1 HIGH below); that is a code-accuracy bug, not a flaw in the deviation.
- **rt2 audit:** the round-trip-2 Dev pass introduced **no new design deviations** (it was finding-clearing only — doc/error-string + test assertions). The deviation above remains the single Dev deviation in flight; its dependent docstring purge is still incomplete (rt2 HIGH — 2 production "merged" over-claims survive). Nothing new to stamp.
- **rt3 audit (FINAL):** the round-trip-3 Dev pass introduced **no new design deviations** (doc purge + one additive route key + test assertions). The world-tier-gear-merge deviation above is now **fully consistent** — its dependent docstring purge is COMPLETE (the rt2 caveat is resolved; `grep -rn "merged"` returns zero over-claims across the gear surface). The deviation stands ACCEPTED with no outstanding caveat. ✓ APPROVED.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server — engine):**
- `sidequest/game/fate_sheet.py` — `AspectKind += "permission"`; `source_gear` on `Aspect` + `Stunt`
- `sidequest/genre/models/inventory.py` — `GearGrantAspect`, `GearGrantStunt`, `GearDef` (strict, no economy fields)
- `sidequest/genre/models/rules.py` — `FateConfig` gains `base_refresh`, `free_stunts`, `gear`, `gear_catalog`
- `sidequest/telemetry/spans/fate.py` — `fate_gear_compiled_span` + `SPAN_ROUTES["fate.gear_compiled"]`
- `sidequest/game/ruleset/fate_gear.py` (NEW) — `resolve_gear` merge + `compile_gear_onto_sheet` + `GearCompileResult`
- `sidequest/cli/validate/fate_gear.py` (NEW) — `check_no_inventory_under_fate` / `check_refresh_invariant` / `check_dangling_gear_ids`
- `sidequest/genre/loader.py` — load `gear.yaml` (genre), inject into `FateConfig.gear_catalog`, fail-loud `_validate_fate_gear`; `GenrePack.gear`
- `sidequest/game/ruleset/fate.py` — Fate seed compiles `cfg.gear` onto the chargen sheet (after the `chargen.seeded` span)
- `sidequest/genre/models/pack.py` — `GenrePack.gear` field
- `tests/genre/test_tea_and_murder_class_kits.py` — DELETED (stale d20 economy test)

**Files Changed (sidequest-content — migration):**
- `pulp_noir`, `spaghetti_western`, `tea_and_murder`, `wry_whimsy`: each → `ruleset: fate`, `fate:` block with `base_refresh/free_stunts/gear`, authored `gear.yaml`, deleted `inventory.yaml` (genre + world), stripped d20 config, removed `power_tiers.yaml`/`equipment_tables.yaml`/native `classes.yaml` where they referenced d20-only scaffolding. wry_whimsy confrontations block restored.

**Tests:**
- All 6 TEA target files GREEN (~50 tests); four-pack integration **44/44**; 121-2 pulp_noir migration unaffected.
- Full server suite: **zero net-new failures vs baseline** (260→260; +1 fixed), proven by node-id diff. One flaky parallel test (space_opera, pre-existing) noted.
- ruff check + format clean.

**Branches:** `feat/114-10-fate-gear-four-packs` (server + content), committed — NOT pushed (SM finish owns push/PR).

**Handoff:** To verify/review.

### Round-Trip 1 Rework (green, 2026-06-16)

Cleared the Reviewer REJECT — every finding addressed:

**HIGH (blocking) — dead code + over-claiming docstrings:** removed `resolve_gear`
+ `tests/genre/test_fate_gear_loader.py`; corrected the three docstrings
(`fate_gear.py` module, `FateConfig.gear_catalog`, `GenrePack.gear`) to
"genre-tier only" (world-tier gear merge deferred to a future story — see the new
Design Deviation entry).

**Test tightenings (MEDIUM/LOW):**
- `test_refresh_floors_per_srd` → asserts `== 1` + `result.refresh_after`/`refresh_debited`
- validator `TestRefreshInvariant` → added the SRD-floor boundary case (deep overrun → floor saves it)
- `TestMaterialization` → new `test_result_reports_materialization_counters` asserting the returned `GearCompileResult` counters
- integration `TestGearAuthored` → dropped vacuous `hasattr`, now `len(gear) >= 1`
- integration `test_pack_loads_without_raising` → now asserts default gear ids resolve against loaded GearDefs (proving the load-time dangling-gear-id gate ran)
- `test_unknown_id_does_not_partially_mutate` → stunt-gear sibling added; asserts `sheet.stunts` (and aspects) untouched on a failed compile
- span `test_span_emits_with_attributes` → asserts `gear_ids` + `actor`

**Doc/lint (LOW):** loader `FateConfig` hoisted to a top-level import; `set(cfg.gear)`
hoisted to a local; `cli/validate/fate_gear` "Four checks" → "Three content checks";
wry_whimsy confrontations comment "typed Fate flavor" → "typed NATIVE flavor"
(spaghetti_western header already documents standoff_rules as "typed-but-unconsumed
content" — covered, no edit). Also fixed a pre-existing `ruff I001` import-sort in the
two edited test files.

**Tests:** targeted 8-file run **120 passed, 0 failed**; full suite **zero net-new
failures vs the develop baseline** (260→259 failures, +1 incidental fix —
`test_fate_action_handler_wiring::test_handler_drives_dispatch_end_to_end`; errors
stable 3→3). ruff check + format clean on all changed files.

**Rework commits (NOT pushed — SM owns push/PR):** server `eed12c1e`, content `4032052`
on `feat/114-10-fate-gear-four-packs`.

### Round-Trip 2 Rework (green, 2026-06-16)

Cleared the rt1 Reviewer REJECT:

**HIGH (blocking) — residual over-claim:** the round-0 "merged"-docstring fix was 3/4
complete; `check_dangling_gear_ids` (cli/validate/fate_gear.py) still said gear "must
exist in the **merged** GearDef set" (docstring, line 72) and emitted "(not in the
**merged** gear.yaml set)" as an **author-facing** validation error (line 77). Corrected
both to "genre-tier" — the over-claim is now fully purged (4/4).

**MEDIUM (test):** `test_span_is_routed_for_the_gm_panel` never asserted the SPAN_ROUTES
extract lambda passes through `actor` (the only coverage of that route's actor field, and
actor is a load-bearing GM-panel field). Added `actor` to the mock attributes and asserted
`extracted['actor']` plus the other extracted fields. (The route already extracted actor at
`telemetry/spans/fate.py:398` — this was a pure coverage gap.)

**LOW (test cosmetics):** `test_overpaid_refresh_is_also_flagged` now asserts the error
names the archetype (`"The Ascetic" in err`, parity with the unpaid case); dropped the
vacuous `all(... source_gear is None)` lines in `test_unknown_id_does_not_partially_mutate`
(the `== []` checks subsume them).

**Deferred (non-blocking):** the carried LOW EDGE — `gear_ids` dedup / author-overwritable
`gear_catalog` — is a behavior change with no test demand; left as a Delivery Finding per
minimalist discipline (the validator's dangling-id check is unaffected; no pack ships dup ids).

**Tests:** targeted 8-file run **120 passed, 0 failed**; full suite **zero net-new failures
vs the develop baseline** (now 260 == baseline 260; the rt1 incidental +1 fix
`test_fate_action_handler_wiring` did not reproduce under xdist this run — a known OTEL/xdist
flake on a baseline test, immaterial to the net-zero invariant). ruff check + format clean on
all changed files.

**Rework commit (NOT pushed — SM owns push/PR):** server `fc8d58a5` on
`feat/114-10-fate-gear-four-packs` (no content changes this round).

### Round-Trip 3 Rework (green, 2026-06-16)

Cleared the rt2 Reviewer REJECT — this time exhaustively, with a grep acceptance gate.
Root cause of the rt1/rt2 churn: the fixes chased the reviewer's cited line numbers
instead of the *class* of over-claim. rt3 greps the whole gear surface and purges all 5.

**HIGH (2 production "merged" over-claims):**
- `game/ruleset/fate_gear.py:39` — `GearCompileError` docstring (runtime-visible exception
  that contradicted its own module docstring) → "genre-tier".
- `cli/validate/fate_gear.py:14` — validator module docstring check #3 → "genre-tier".

**MEDIUM (3 test design-recounts, purged for consistency):**
- `tests/cli/validate/test_fate_gear_validator.py:11`; `tests/game/ruleset/test_fate_gear_compile.py:5`
  and `:30` (dropped the explicit "(genre + world)").

**MEDIUM (OTEL completeness):** `gear_ids` was emitted on the `fate.gear_compiled` span but
the `SPAN_ROUTES` projection lambda dropped it — the GM panel couldn't see WHICH gear fired.
Added `gear_ids` to the route extract (`telemetry/spans/fate.py`) + asserted it in the route test.

**LOW:** `test_unknown_id_does_not_partially_mutate` now pins `pytest.raises(match="ghost_gun")`
for parity with its sibling.

**ACCEPTANCE GATE met:** `grep -rn "merged"` over all 9 gear-surface files returns **zero**
over-claims.

**Tests:** targeted 8-file run **120 passed, 0 failed**; full suite **zero net-new failures
vs the develop baseline** (now 259 == baseline−1; the OTEL/xdist flake passed this run).
ruff check + format clean on all changed files.

**Rework commit (NOT pushed — SM owns push/PR):** server `3ba76af0` on
`feat/114-10-fate-gear-four-packs` (no content changes this round).

## Subagent Results

_Round-trip 3 re-review (2026-06-16). Supersedes the rt0/rt1/rt2 tables (preserved in git). Toggles unchanged: preflight/test_analyzer/comment_analyzer/rule_checker enabled; 5 disabled._

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | tests 120/120 green, ruff clean, net-new 0 vs baseline, grep gate ZERO, tree clean |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer + rule-checker (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer + rule-checker #1 (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | clean | 1 LOW | both rt3 changes CONFIRMED-GENUINE; 1 LOW (refresh_before not asserted in one span test — already covered by test_span_emits_with_attributes) → non-blocking, "nothing blocks" |
| 5 | reviewer-comment-analyzer | Yes | clean | 0 | "merged" over-claim FULLY purged (grep ZERO); gear_ids route comment accurate; loader.py:745 "world-tier privilege" is a correct ADR-145 boundary note, not an over-claim |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer + rule-checker #3 (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer + rule-checker #8/#11 (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain assessed by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | clean | 0 | exhaustive "merged" sweep ZERO hits; gear_ids fully wired (emit→route→assert, no half-wiring); rule #13 no regression; "NOTHING BLOCKS" |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled and self-assessed)
**Total findings:** 0 blocking; 1 LOW non-blocking (already covered elsewhere). Convergence.

### Rule Compliance (python.md + SOUL/CLAUDE rules) — round-trip 3

| Rule | Governed elements in diff | Verdict |
|------|---------------------------|---------|
| #6 test quality | both rt3 test changes CONFIRMED-GENUINE — `gear_ids` route assertion hits a real lambda key; `match="ghost_gun"` pins a message the production raise actually emits (rule-checker + test-analyzer concur) | COMPLIANT |
| #10 import hygiene | rt3 changed no imports | COMPLIANT |
| #13 fix-introduced regressions | rt3 is doc + one additive route key + 2 test assertions; the only route consumer asserts individual keys (not exact-dict), so the added `gear_ids` key cannot break it (rule-checker verified) | COMPLIANT |
| No Silent Fallbacks | compile still fails loud on unknown gear id; `match=` now pins it | COMPLIANT |
| **Accurate docs / no over-claiming** | **RESOLVED** — all 5 "merged" over-claims purged; `grep -rn "merged"` over the gear surface returns ZERO (comment-analyzer + rule-checker + preflight independently confirm) | COMPLIANT (was VIOLATION) |
| OTEL | **RESOLVED** — `gear_ids` now in the SPAN_ROUTES projection (emit→route→assert fully wired, no half-wiring); GM panel can surface which gear fired | COMPLIANT (was PARTIAL) |
| Strict models / Bind the Ruleset / fail-loud | unchanged — all COMPLIANT | COMPLIANT |

### Devil's Advocate (round-trip 3)

Assume it's still broken. Where would I look? The recurring crack was the "merged" over-claim — so I ran the same `grep -rn "merged"` over all ten gear-surface files myself, and it returns nothing (exit 1, zero hits). Comment-analyzer and rule-checker ran it independently and concur. I widened the net to "genre + world" / "world-tier merge" / "world tier" to catch a reworded survivor: the only gear-adjacent hit is `loader.py:745` "bespoke gear is a world-tier privilege" — which is a *correct* ADR-145 boundary statement (bespoke gear belongs at the world tier; the genre tier is SRD-only), not a claim that a merge happens now. So the over-claim is genuinely, exhaustively gone — not "the cited lines fixed" but the whole class. The remedy that worked was the grep acceptance gate; that is the lesson, now in the dev sidecar.

The OTEL hole I opened in rt2 (the route dropping `gear_ids`) is closed and the wiring is real on all three legs: the emit fn writes `gear_ids` onto the span, the route lambda extracts it, the routing test asserts it. Adding a key to the route's projection is strictly additive — rule-checker confirmed the sole consumer asserts individual keys, never an exact-dict equality, so nothing downstream breaks. The one surviving finding is a LOW: `test_span_attributes_capture_a_refresh_debit` doesn't assert `refresh_before`, but the very next test (`test_span_emits_with_attributes`) pins `refresh_before == 3`, so the field is covered — a redundancy gap, not a blind spot. Net-zero regression holds (zero net-new vs baseline; the only delta is a known OTEL/xdist flake passing this run). The engine math, fail-loud paths, strict models, and OTEL routing were solid throughout; the entire rt1→rt3 saga was a documentation-accuracy convergence, never a correctness defect. Nothing blocks. Approve.

## Reviewer Assessment

**Verdict:** APPROVED (round-trip 3 re-review)

The recurring "merged" over-claim is **fully purged** — all 5 instances corrected to "genre-tier", and the `grep -rn "merged"` acceptance gate I set in rt2 returns **zero** hits across the gear surface (confirmed independently by preflight, comment-analyzer, and rule-checker). The OTEL gap (the SPAN_ROUTES projection dropping `gear_ids`) is **closed and fully wired** — emit→route→assert, rule-checker verified no half-wiring and no exact-dict consumer that an added key could break. Both rt3 test changes are CONFIRMED-GENUINE. Preflight fully green: 120/120 targeted, ruff check + format clean, **zero net-new failures vs the develop baseline**, working tree clean. Rule-checker: zero violations; "NOTHING BLOCKS." No Critical/High findings remain.

**Data flow traced:**
- chargen gear: `archetype/cfg.gear` (ids) → `compile_gear_onto_sheet` resolves against the genre-tier GearDef set → fails loud (`GearCompileError`, message pins the id) on unknown id BEFORE any mutation → materializes aspects/stunts with `source_gear` → recomputes refresh (SRD floor) → emits `fate.gear_compiled`. Safe: no partial mutation, no silent fallback.
- OTEL lie-detector: `fate.gear_compiled` span carries `gear_ids/actor/archetype/counts/refresh_*` → `SPAN_ROUTES["fate.gear_compiled"]` now projects all of them (incl. `gear_ids`) → GM panel can verify which gear materialized. Fully wired end-to-end.

**Pattern observed:** the route lambda follows the established `(span.attributes or {}).get(key, default)` idiom used by every other `SpanRoute` in `telemetry/spans/fate.py` — consistent, refactor-stable.

**Error handling:** `compile_gear_onto_sheet` resolves all ids first and raises `GearCompileError` (ValueError) with the offending id before mutating — verified by `test_unknown_id_does_not_partially_mutate` (sheet stays empty) + `match="ghost_gun"`.

**Non-blocking (carried to Delivery Findings, not gating):**
- [LOW] `[TEST]` `test_span_attributes_capture_a_refresh_debit` doesn't assert `refresh_before` — but `test_span_emits_with_attributes` already pins `refresh_before == 3`, so the field is covered.
- [LOW] `[EDGE]` `compile_gear_onto_sheet` doesn't dedup `gear_ids`; `gear_catalog` is author-overwritable (carried from round 0, Optional). No pack ships dup ids; the validator's dangling check is unaffected. A reasonable future hardening, not a defect today.

**Resolved this round (tagged):**
- `[DOC]` All 5 "merged" over-claims purged → "genre-tier"; `grep -rn "merged"` over the gear surface returns ZERO (comment-analyzer CLEAN, rule-checker sweep ZERO). The recurring rt1/rt2 documentation-accuracy violation is fully cleared. ✓
- `[RULE]` rule-checker exhaustive pass: 0 violations; Verify-Wiring satisfied (`gear_ids` emit→route→assert fully wired, no half-wiring); No-Silent-Fallbacks intact; Accurate-docs now COMPLIANT. ✓
- `[TEST]` both rt3 test changes CONFIRMED-GENUINE (test-analyzer); 1 LOW (refresh_before) non-blocking, already covered elsewhere. ✓

**Domain self-assessments (disabled subagents):**
- `[SEC]` No new attack surface (rt3 is doc + one route key + test assertions). Clean (rule-checker #8/#11 concur).
- `[TYPE]` Models strict + typed; unchanged. Clean (rule-checker #3 concur).
- `[SILENT]` Every failure path raises; no swallow. Clean (rule-checker #1 concur).
- `[EDGE]` Only the carried-over dedup/overwrite LOW (non-blocking, Optional). `[SIMPLE]` rt3 net-simplifies (doc corrections + one additive key); no new complexity.

**The rt1→rt3 saga in one line:** a documentation-accuracy convergence (the "merged" over-claim), never a correctness defect — the engine math, fail-loud, strict models, and OTEL routing were solid from round 0. Process lesson (fix the class with a grep gate, not the cited line) captured in the dev sidecar.

**Handoff:** To SM for finish-story (PR creation + merge). Branch `feat/114-10-fate-gear-four-packs` (server + content), committed, NOT pushed.