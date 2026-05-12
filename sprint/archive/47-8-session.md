---
story_id: "47-8"
jira_key: ""
epic: "47"
workflow: "bdd"
---
# Story 47-8: Coyote Object salvage hooks — design (ADR + scenario seed)

## Story Details
- **ID:** 47-8
- **Jira Key:** (None — project does not use Jira per CLAUDE.md)
- **Workflow:** bdd (design phase taken by architect — see Delivery Finding; the `architecture` workflow is too heavy for a 3-pt ADR)
- **Epic:** 47 — Magic System Coyote Reach v1
- **Points:** 3
- **Priority:** p3
- **Stack Parent:** none

## Context

This is the design phase (BDD first phase) for integrating Coyote Object mechanics into the Magic system Phase 5 pipeline. Story ships an ADR specifying salvage hooks semantics and a scenario test seed that will be executed in downstream implementation.

**Related Stories:**
- **47-3** (completed) — Magic Phase 5: five named confrontations wired (the_standoff, the_salvage, the_bleeding_through, the_quiet_word, the_long_resident)
- **47-4** (completed) — Rig MVP Phase C: the_tea_brew confrontation wiring
- **47-5** (completed) — Magic Phase 6: multiplayer playtest
- **47-6, 47-7** (completed) — Tea ritual fixes
- **47-9** (completed) — Proactive innate_v1 firing
- **47-10** (completed) — C&C memorization wiring

**Blocking:** None identified. Prior confrontation infrastructure (47-3) is complete and shipped.

**Unblocks:** Downstream 47-x stories that implement Coyote Object auto-fire semantics and salvage-triggered confrontations.

## Workflow Tracking
**Workflow:** bdd
**Phase:** finish
**Phase Started:** 2026-05-12T21:07:44Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-12T20:26:36Z | 2026-05-12T20:26:36Z | - |
| design | 2026-05-12T20:26:36Z | 2026-05-12T20:49:44Z | 23m 8s |
| red | 2026-05-12T20:49:44Z | 2026-05-12T20:52:43Z | 2m 59s |
| green | 2026-05-12T20:52:43Z | 2026-05-12T20:54:15Z | 1m 32s |
| review | 2026-05-12T20:54:15Z | 2026-05-12T21:07:44Z | 13m 29s |
| finish | 2026-05-12T21:07:44Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

- **[ux-designer] Conflict, blocking:** Workflow→agent misroute. BDD workflow assigns `design` phase to `ux-designer`, but this story's scope is entirely a mechanical/architecture ADR — salvage hook triggers, ledger-bar pool bindings, mandatory advancement outputs, OTEL span design, multi-player projection per ADR-037. There is no UI/UX surface to wireframe; the player-facing surface is narrative output from existing confrontation pipeline (already shipped in 47-3). Recommend the design phase be owned by **architect** for this story. Routing handed off via Skill invocation of `/pf-architect`. The Cook found no pepper to throw — there are no user-facing decision points in scope.

- **[tea] Gap, non-blocking:** `sprint/context/context-story-47-8.md` was never created during setup phase. SM's `sm-setup MODE=setup` did not produce a story context file. The session file itself covered the AC surface adequately (3 ACs explicit in §Acceptance Criteria) so the design phase wasn't blocked, but downstream `pf validate context` calls fail. Not fixing this in-flight — would extend a 3-pt story scope. Recommend SM (or sm-setup helper) add story-context generation for ADR-only stories under BDD-like workflows.

- **[tea] Gap, non-blocking:** `pf validate adr` flags 322 errors across the ADR tree (including all post-096 ADRs and including SUPERSEDED.md / README.md which are not ADRs). Validator drift, pre-existing — ADR-099 fails the same checks as ADR-098 (recently merged), so this is not a 47-8 regression. Skipping fixes here; should be its own story.

- **[tea] Gap, non-blocking:** `scripts/playtest.py` is referenced in `justfile:381` (target `playtest-scenario`) but does not exist on disk. The new `scenarios/coyote_salvage_smoke.yaml` cannot be exercised end-to-end until that script is restored. The scenario seed is still authored correctly as a spec for downstream implementation. Confirm/restore the script when 47-8 hooks land in implementation.

- **[reviewer] Forward impact bundle for the downstream salvage-hooks implementation story (consolidated from 9-subagent review):**
  1. **`fire_phase` vs `salvage_phase_default` relationship** must be locked down in the implementation story — single-source-of-truth field, not two overlapping ones. Recommend dropping `salvage_phase_default` from items; the confrontation's `fire_phase` is sufficient for v1.
  2. **`fire_phase: "discovery"` semantics** — schema accepts this value but ADR doesn't specify what firing at discovery time means for the outcome catalog (`item_acquired` doesn't fit pre-inventory). Either constrain to `"acquisition"` for v1 (mark `"discovery"` reserved) or fully specify the discovery-phase outcome path.
  3. **NPC-gift acquisition path** — when an NPC hands a Coyote Object directly to a player (no room-entry, no discovery), acquisition fires without a preceding discovery beat. Specify whether the evaluator (a) emits a synthetic discovery span with `skip_reason: "npc_gift"` then proceeds, or (b) suppresses the confrontation until a discovery beat is injected. Lock the choice.
  4. **Simultaneous dual-actor acquisition race** — both actors declaring "I grab the panel" in the same submit-and-wait turn. Specify ownership arbitration at the inventory-mutation layer BEFORE the evaluator runs; defer to ADR-036 turn coordination.
  5. **Save migration with already-acquired Coyote Objects** — on legacy save load, populate `resolved_salvage_objects` from the actor's existing inventory (any in-inventory `coyote_object: true` item is treated as resolved). Prevents re-firing the_salvage on items the character already "owns" narratively.
  6. **Runtime narrator tagging** — ADR mentions narrator may tag a generic item as `coyote_object: true` at runtime, but does not specify the JSON sidecar field, validation rules, or downstream behavior (does it trigger discovery on existing in-room presence, or only on next observation?). Lock the protocol.
  7. **`coyote_object` flag must NOT silently default to `false`** — implementation MUST require explicit `coyote_object: true | false` on `item_legacy_v1` items in worlds with `salvage_conditions` confrontations, and the loader MUST raise `ItemLoaderError` (or warn loudly at minimum) when the flag is absent. Violates "No Silent Fallbacks" rule otherwise.
  8. **Remote-player narration leak (security)** — shared acquisition narration must be gated by per-player `observed_salvage_objects` via the ADR-028 Perception Rewriter. A remote player who has never entered the room must not receive narration that identifies the artifact by name or category.
  9. **Type definitions to encode at red phase:** `SalvageDiscovery` Pydantic model (defined in ADR Implementation Notes); `object_class: Literal["coyote_object"]`; `fire_phase: Literal["discovery", "acquisition"]`; `@model_validator(mode="after")` on `ConfrontationDefinition` enforcing the "exactly one of three condition blocks" invariant for `auto_fire=True`.
  10. **Scenario extensions** the impl story should ADD to `scenarios/coyote_salvage_smoke.yaml` (beyond the in-flight test-design fixes): (a) outcome-branch turns (clear_win and clear_loss) exercising the `item_acquired` materialization and pool deltas; (b) a save/load checkpoint between discovery and acquisition; (c) a simultaneous-acquisition turn for two actors; (d) a runtime-tagging turn promoting `spare_o_ring_kit` to `coyote_object: true` mid-scene.
  11. **Schema-simplification candidates** for impl-story consideration (each defensible to defer): cut `cooldown_turns` from v1 schema (No Stubbing); collapse two per-player sets to `Dict[object_id, Literal["observed","resolved"]]` (eliminates degenerate state); collapse two evaluators to one phase-keyed evaluator (single OTEL site).
  12. **`lineage` character field path** — the scenario seed uses `lineage: voidborn|hegemony` at the player level; confirm this maps to an actual character attribute (likely via the chargen system per ADR-016) or rewrite the fixture to the real representation, or lineage-dependent assertions will silently pass.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- No deviations from spec. Architect's deliverables (ADR-099 + scenario seed YAML) shipped as authored during the design phase; Dev added no code under this story per chore bypass.

## Acceptance Criteria

Per epic-47.yaml, story 47-8 is scheduled for design phase only:

1. ADR authored documenting Coyote Object mechanical model:
   - Salvage hook trigger conditions and evaluation
   - Auto-fire hooks for salvage discovery/acquisition
   - Ledger bar pool binding (sanity, control, awareness, or custom)
   - Mandatory advancement outputs (item_acquired, control_tier_advance, status_add_wound, etc.)
   - OTEL span design for observability

2. Scenario test seed in `scenarios/` that exercises the Coyote Object hook flow:
   - Fixture defining a salvageable object in a room
   - Condition assertions on discovery vs. acquisition phases
   - Expected OTEL span emissions

3. Design spec includes:
   - Semantics of "salvage" vs. "acquire" phases
   - Pool resource deltas and threshold crossing triggers
   - Multi-player projection rules (ADR-037 per-player vs. shared state)

---

## Reviewer Assessment

**Verdict:** APPROVE with findings.
**Off with whose head?** Nobody's. The design is sound, but I'm not rubber-stamping — many findings logged below across all 9 specialist subagents.

### Specialist Tag Coverage

- [EDGE] 10 findings (5 high-confidence DEFERRED to impl story per Forward Impact bundle; 2 FIXED in-flight; 3 medium DEFERRED)
- [SILENT] 4 findings (1 FIXED, 3 DEFERRED — coyote_object loader-side enforcement, None-return distinction, save-migration)
- [TEST] 9 findings (5 FIXED in-flight, 4 DEFERRED as scenario-extension obligations)
- [DOC] 8 findings (6 FIXED in-flight, 1 DEFERRED — fire_phase/salvage_phase_default disambig, 1 DISMISSED)
- [TYPE] 6 findings (4 DEFERRED to impl story for concrete Pydantic model authoring; 2 DISMISSED as pre-existing codebase patterns)
- [SEC] 2 findings (1 DEFERRED — remote-player narration leak; 1 DISMISSED — GM panel is dev-only)
- [SIMPLE] 6 findings (2 FIXED in-flight, 3 DEFERRED to impl-story judgment, 1 DISMISSED)
- [RULE] 3 hard violations + 1 borderline — 3 FIXED in-flight (ADR-088 frontmatter, missing_tag enum); 1 DEFERRED (coyote_object silent default → loader requirement)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|------------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | YELLOW (pre-existing) | 5 server failures all pre-existing on develop (victoria `classes.yaml` not yet committed; story 49-4 tests landed ahead of content file). 0 failures attributable to 47-8. Ruff lint clean. Client lint clean (1 pre-existing warning). 0 code smells. | **Dismiss** — pre-existing red noted in Delivery Findings already covered by separate work; the 47-8 diff is docs-only and introduced nothing. |
| 2 | reviewer-edge-hunter | Yes | findings | 10 findings: (a) zero-condition guard, (b) compound-trigger out-of-scope statement, (c) `fire_phase: discovery` outcome path undefined, (d) discovered-never-acquired set reaping unspecified, (e) NPC-gift path (acquired without discovery), (f) simultaneous dual-actor acquisition race, (g) save-load with already-acquired item, (h) `cooldown_turns` semantic ambiguity, (i) narrator runtime-tagging mechanism unspecified, (j) Turn 2 span-emission semantics. | **Defer to impl story** — (a)(b)(c)(d)(e)(f)(g)(i) are real spec gaps the implementation story must lock down before red phase; documented in Delivery Findings. **Confirm and fix** — (h) cooldown comment fixed in-flight; (j) span-emission semantics fixed in-flight ("emitted on every evaluation"). |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 4 findings: (a) `coyote_object` missing flag defaults to false silently, (b) `None` return for `missing_tag` weaker than raise, (c) Turn 1 acquisition negative assertion lacks `object_id` scope, (d) legacy-save migration could double-fire on already-acquired items. | **Confirm and fix** — (c) object_id added to Turn 1 negative assertion in-flight. **Defer to impl story** — (a)(b) become loader-side requirements (no silent default; raise on missing_tag at load time, not runtime); (d) migration strategy locked down in impl story. All documented in Delivery Findings. |
| 4 | reviewer-test-analyzer | Yes | findings | 9 findings: (a) Turn 1 vacuous `otel_span_not_emitted_for` (no object_id), (b) Turn 1 vacuous `confrontation_active: null`, (c) Turn 2 missing `narration_beat_emitted: false`, (d) Turn 3 missing `per_player_state_unchanged` for Sira, (e) AC1 outcome turns missing, (f) save/load not exercised, (g) simultaneous dual-actor acquisition not exercised, (h) runtime-tagging not exercised, (i) Turn 4 player_receives is subset-check not exclusion. | **Confirm and fix** — (a)(b)(c)(d)(i) all fixed in-flight in the scenario YAML (Turn 1 negative scoped to object_id; Turn 1 confrontation_active scoped to the_salvage+Sira+active:false; Turn 2 adds narration_beat_emitted: false; Turn 3 adds per_player_state_unchanged: Sira; Turn 4 adds player_must_not_receive: Calix CONFRONTATION_OVERLAY). **Defer to impl story** — (e)(f)(g)(h) become scenario-extension obligations on the implementation story. |
| 5 | reviewer-comment-analyzer | Yes | findings | 8 findings: (a) stale `cooldown_turns` inline comment, (b) `fire_phase` vs `salvage_phase_default` relationship undefined, (c) `observed_objects_by_actor` parameter name mismatch, (d) `narration_beat_id` type ambiguous, (e) `apply_inventory_changes` is a phantom function, (f) ADR-014 missing from `related` list, (g) scenario assertion types not in current runner, (h) Coyote Reach / Coyote Star terminology lag in linked spec. | **Confirm and fix** — (a) comment rewritten in-flight; (c) parameter renamed; (d) type pinned to `LoreFragment.id`; (e) phantom function references all replaced with `items_gained processing in narration_apply.py`; (f) ADR-014 added to `related`; (g) header comment added to scenario. **Defer to impl story** — (b) fire_phase vs salvage_phase_default disambiguation is a real spec gap. **Dismiss** — (h) terminology lag in a linked spec is not 47-8's responsibility. |
| 6 | reviewer-type-design | Yes | findings | 6 findings: (a) `SalvageConditions.object_class` should be Literal not str, (b) `fire_phase` should be Literal, (c) `SalvageDiscovery` return type undefined, (d) cross-field `@model_validator` placement unspecified, (e) per-player set str typing weak (pre-existing pattern), (f) `FireConditions.bond_tier_min` Literal (pre-existing). | **Defer to impl story** — (a)(b)(c)(d) are all real type-design specs the implementation story must lock at red. The ADR's Implementation Notes mention them at the prose level; the impl story will encode them as concrete Pydantic models. **Dismiss as pre-existing** — (e)(f) are codebase-wide patterns, not 47-8 regressions; valid future-cleanup but not this story. |
| 7 | reviewer-security | Yes | findings | 2 findings: (a) remote-player narration leak (shared acquisition narration may expose Coyote Object identity to a player who has not yet discovered it — medium), (b) OTEL span attributes carry `object_id` / `room_local_id` and could leak if the GM dashboard endpoint is reachable from player origins (low). | **Defer to impl story** — (a) is a real design gap; the ADR's "narration is shared" clause needs gating by per-player `observed_salvage_objects` via the ADR-028 Perception Rewriter. Documented in Delivery Findings. **Dismiss** — (b) GM panel is a dev tool for Keith/Sebastien per the project's memory note ("GM panel audience"); the dashboard endpoint is not player-facing today. Worth tracking but not a 47-8 design failure. |
| 8 | reviewer-simplifier | Yes | findings | 6 findings: (a) cut `cooldown_turns` entirely per No Stubbing, (b) collapse two per-player sets to `Dict[str, Literal["observed","resolved"]]`, (c) collapse two evaluators to one phase-keyed evaluator, (d) "once per pair" span language vs Turn 2 every-evaluation assumption (contradiction), (e) rename `otel_span_not_emitted_for` → `otel_span_not_emitted`, (f) A1 rejection rationale uses observability argument where it should use bait/bite. | **Confirm and fix** — (d) span emission semantics rewritten in-flight to "emitted on every evaluation"; (e) assertion key renamed in-flight. **Defer to impl story (judgment call)** — (a)(b)(c) are real simplification candidates worth considering at red, but each has a defensible counter (cooldown is a one-line schema field that signals future extension; two sets are clearer than a Dict in the codebase's idiom; two evaluators have different call sites). The impl story can collapse if the case is clear at red. **Dismiss** — (f) rationale wording is stylistic; A1's rejection conclusion is correct. |
| 9 | reviewer-rule-checker | Yes | findings | 3 hard violations + 1 borderline: (a) `supersedes: null` → `supersedes: []` per ADR-088; (b) `implementation-status: planned` invalid → `deferred`; (c) `coyote_object` silent default-to-false; (d) borderline: `skip_reason: "missing_tag"` contradicts scenario Turn 5 expectation. | **Confirm and fix** — (a)(b) frontmatter fixed in-flight; index regenerated clean. (d) ADR rewritten in-flight to remove `missing_tag` from the acquisition skip_reason enum and to clarify mundane items short-circuit before the evaluator (no span). **Defer to impl story** — (c) become a loader-side requirement: explicit `coyote_object: true | false` required on item_legacy_v1 items in worlds with `salvage_conditions` confrontations; raise on missing flag. Documented in Delivery Findings. |

**Subagent count:** 9/9 received. All received: Yes. All findings have decisions documented above with rationale.

### Subagent-tagged findings summary

[DOC] reviewer-comment-analyzer surfaced 8 documentation defects in the ADR text and scenario YAML: stale `cooldown_turns` inline comment (FIXED in-flight, comment rewritten); `fire_phase` vs `salvage_phase_default` relationship undefined (DEFERRED to impl story, documented in Delivery Findings); `observed_objects_by_actor` parameter name mismatch (FIXED — renamed to `observed_salvage_objects`); `narration_beat_id` type ambiguous (FIXED — pinned to `LoreFragment.id`); phantom function `apply_inventory_changes` (FIXED — replaced with the actual `items_gained processing in narration_apply.py`); ADR-014 missing from `related` list (FIXED); scenario assertion types not in current runner (FIXED — header comment added warning that the new types require downstream implementation); Coyote Reach / Coyote Star terminology lag in a linked spec (DISMISSED — not 47-8's responsibility).

[RULE] reviewer-rule-checker surfaced 3 hard rule violations + 1 borderline against ADR-088 frontmatter schema and project rules: `supersedes: null` → `supersedes: []` per ADR-088 (FIXED in-flight); `implementation-status: planned` invalid enum value → `deferred` (FIXED in-flight); `coyote_object` missing flag silently defaults to false — violates "No Silent Fallbacks" (DEFERRED to impl story; loader-side requirement documented in Delivery Findings to raise on missing flag); borderline contradiction between `skip_reason: "missing_tag"` in ADR and Turn 5 `otel_span_not_emitted` for the mundane o-ring kit (FIXED — ADR rewritten to specify mundane items short-circuit before the evaluator, `missing_tag` removed from skip_reason enum). All other project rules (No Stubbing, Don't Reinvent, Verify Wiring, Every Test Suite Needs a Wiring Test, OTEL Observability, No Jira, all six SOUL principles checked) verified compliant.

[TEST] reviewer-test-analyzer surfaced 9 scenario-design defects: Turn 1 vacuous `otel_span_not_emitted_for` lacked `object_id` scope (FIXED — `object_id: the_hopper_panel` added); Turn 1 vacuous `confrontation_active: null` (FIXED — scoped to `the_salvage`/Sira/active:false); Turn 2 missing `narration_beat_emitted: false` (FIXED — added); Turn 3 missing `per_player_state_unchanged` for Sira tests per-player isolation in only one direction (FIXED — added); AC1 outcome turns missing — no turn drives the confrontation to any outcome branch (DEFERRED to impl story; impl-story scenario extension obligation documented); save/load not exercised (DEFERRED — impl-story extension); simultaneous dual-actor acquisition not exercised (DEFERRED — impl-story extension); runtime narrator tagging not exercised (DEFERRED — impl-story extension); Turn 4 `player_receives` is a subset-check not an exclusion check, so a confrontation-overlay broadcast to Calix would pass (FIXED — `player_must_not_receive: Calix CONFRONTATION_OVERLAY` added).

[EDGE] reviewer-edge-hunter surfaced 10 path-enumeration findings. Most substantive (high confidence, all DEFERRED to impl story as Forward Impact items #2-#6 in Delivery Findings): `fire_phase: "discovery"` outcome path undefined; NPC-gift acquisition path (acquired without discovery); simultaneous dual-actor acquisition race; save-load with already-acquired Coyote Object causes double-fire; narrator runtime-tagging mechanism unspecified. Medium-confidence finds also deferred: zero-condition guard explicit error message; compound-trigger out-of-scope statement; discovered-never-acquired set reaping policy; `cooldown_turns` semantic ambiguity (FIXED in-flight via comment rewrite); Turn 2 span-emission semantics (FIXED in-flight — every-evaluation emission).

[SILENT] reviewer-silent-failure-hunter surfaced 4 finds. `coyote_object` missing flag silent-defaults to false (DEFERRED to impl story, loader-side requirement documented); `None` return for `missing_tag` weaker than raise — paired with [RULE]'s missing_tag concern (FIXED in-flight — missing_tag removed from skip_reason enum, becomes loader-bug not runtime skip); Turn 1 acquisition negative assertion lacks `object_id` scope (FIXED in-flight); legacy-save migration could double-fire on already-acquired items (DEFERRED — impl-story migration strategy documented in Forward Impact #5).

[TYPE] reviewer-type-design surfaced 4 substantive + 2 pre-existing finds. `SalvageConditions.object_class` should be `Literal["coyote_object"]` not bare str (DEFERRED to impl story — concrete Pydantic model lands at red); `fire_phase` should be `Literal["discovery","acquisition"]` (DEFERRED — same); `SalvageDiscovery` return type undefined in ADR (DEFERRED — impl story authors the model per Forward Impact #9); cross-field `@model_validator` placement unspecified (DEFERRED — impl-story locks the placement). Pre-existing codebase-wide weaknesses around raw-str IDs (DISMISSED — not a 47-8 regression) and `FireConditions.bond_tier_min: str` instead of Literal (DISMISSED — pre-existing pattern, worth future cleanup but not 47-8).

[SEC] reviewer-security surfaced 2 finds (no secrets, no PII, no credentials in any file). Medium: shared acquisition narration may expose a Coyote Object's existence to a remote player who has never discovered it (DEFERRED to impl story per Forward Impact #8 — gate shared narration via per-player `observed_salvage_objects` through ADR-028 Perception Rewriter). Low: OTEL span attributes carry `object_id` and `room_local_id` in plaintext; if the GM dashboard were ever reachable from player origins, it would leak (DISMISSED — GM panel is a dev tool for Keith/Sebastien per project memory; not player-facing today, but worth tracking as a non-blocking observation).

[SIMPLE] reviewer-simplifier surfaced 6 simplification candidates. High-confidence "once per pair" span language vs every-evaluation contradiction (FIXED in-flight); rename `otel_span_not_emitted_for` → `otel_span_not_emitted` (FIXED in-flight). Three high-confidence schema-shape candidates DEFERRED to impl story as Forward Impact #11 with judgment-call latitude — each is genuinely defensible to keep: cut `cooldown_turns` from v1 (No Stubbing argument is strong, but it's a one-line schema field that signals future extension); collapse the two per-player sets to `Dict[object_id, Literal["observed","resolved"]]` (eliminates degenerate state; the impl story decides at red); collapse the two evaluators to one phase-keyed evaluator (different call sites give the two-function design real legs). A1 rejection rationale wording (DISMISSED — stylistic; the rejection conclusion is correct).

## Reviewer-assessed findings (own read, distinct from subagent results) The ambiguities are spec gaps the implementation story must resolve before red phase; none of them invalidate the architecture (three trigger shapes, two phases, OTEL coverage, ADR-037 alignment hold up).

### What I checked

- ADR-099 internal consistency (Context → Decision → Consequences chain)
- Cross-references against actual files: `confrontations.yaml` (the_salvage shape verified), `confrontations.py` (FireConditions/auto_fire_trigger machinery verified), magic implementation design spec
- ADR linkage: ADR-014, 028, 033, 037, 058, 090, 093 all exist in the index
- Scenario seed structural consistency against `scenarios/asymmetric_smoke.yaml`
- Cross-cutting rules (no silent fallback, every test suite needs a wiring test, OTEL on every subsystem decision) — all addressed in the ADR's Implementation Notes
- ADR index regeneration ran clean post-tag-fix

### Findings (design ambiguities; non-blocking for design-phase merge)

1. **[major] Two-field overlap: `fire_phase` (on `salvage_conditions`) vs `salvage_phase_default` (on items).** ADR-099 §Decision shows both fields but does not specify their relationship. `fire_phase: acquisition` on the confrontation says "this conf fires on acquisition"; `salvage_phase_default: acquisition` on the item could be either (a) a per-item override of phase, (b) a fallback if the conf doesn't specify, or (c) redundant. The implementation story MUST disambiguate. Recommended resolution: drop `salvage_phase_default` from items; the confrontation's `fire_phase` is sufficient for v1.

2. **[major editorial] Contradictory comment on `cooldown_turns`.** L82 YAML example annotates `cooldown_turns: 0` with "per-object lifetime — discovery+acquisition each fire at most once per object_id per actor." But L182-189 §Cooldown semantics says the once-per-object invariant is enforced by `resolved_salvage_objects` set membership, and `cooldown_turns` is "reserved for future worlds; v1 leaves it unused." The L82 comment ascribes meaning to an unused field. Implementation story should fix the comment OR remove `cooldown_turns` from v1 schema.

3. **[minor] `visible_object_ids` parameter undefined.** The `evaluate_salvage_discovery` signature names `visible_object_ids` but the ADR doesn't say what populates it — items physically in the room, items the actor perceived per ADR-028 (Perception Rewriter), or something else. The implementation story needs guidance; recommend "items in room + items the actor's perception-filter has surfaced" as the v1 default.

4. **[minor] `narration_beat_id` LoreFragment content unspecified.** §OTEL spans references a "LoreFragment minted for the beat" but doesn't say what the LoreFragment contains (text source, scope, expiration). A LoreFragment without content is a dangling ID. Recommend the implementation story specify: text drawn from item metadata's `narrator_register` field (if present) or a default register-keyed template.

5. **[minor] Discovery hook site bounded to room-entry.** §Hook sites L104-106 says discovery is called "from the room-entry / room-snapshot pipeline (same site as `find_eligible_room_autofire`)." If the narrator introduces a previously hidden Coyote Object mid-scene (a panel under the captain's hand starts humming AFTER the player was already in the room), the room-entry hook will not re-evaluate. Recommend a second hook site on inventory/visibility delta — or explicit ADR text that mid-scene reveals route through the existing narrator-discretionary path until a future story extends discovery.

6. **[minor] Item Legacy backfill obligation unstated.** §Consequences §Item Legacy plugin integration says "most Item Legacy items are Coyote Objects in Coyote Star" but L212 specifies "missing flag defaults to `false`." Implementation story will need to backfill `coyote_object: true` on existing Item Legacy items in `coyote_star/magic.yaml` (and any other world that wants the behavior). Not in 47-8's scope, but the migration must be tracked.

### Scenario seed findings

- **[minor] `lineage` character attribute not verified in game model.** The scenario fixture sets `lineage: voidborn` and `lineage: hegemony` on Sira and Calix. The magic.yaml references voidborn lineage as a concept (innate_v1 native delivery mechanism) but `lineage` as a top-level character attribute is not visible in the magic config files I checked. Implementation story should confirm this maps to an actual character field (likely via the chargen system per ADR-016) or rewrite the fixture to use the actual representation.

- **[minor] New assertion types (`otel_span_emitted`, `otel_span_not_emitted_for`, `per_player_state`, `per_player_state_unchanged`) are not present in existing scenario harness.** This is acceptable for a *seed* (the YAML defines what the harness should support) but the implementation story must extend the playtest harness — or the scenario stays as documentation only. Combine with TEA's pre-existing finding that `scripts/playtest.py` is missing.

### What I did NOT find

- No silent fallbacks introduced. ADR explicitly tightens the validator rule (auto_fire: true requires exactly one trigger block).
- No half-wired claim. The story correctly defers implementation to a downstream story rather than shipping a stub.
- No OTEL gaps. Two new spans authored with full attribute lists.
- No security concerns (docs-only diff; no secrets, no auth surface).
- No type-system gaps in the proposed model (`SalvageConditions` is extra=forbid, mirroring `FireConditions`).
- No cliché in the design (genre-mechanics work is mechanically novel — three trigger shapes is a real taxonomy, not a copy of either prior pattern).

### Verdict reasoning

The ADR's central architecture is correct: three trigger shapes (bar-DSL / room-entry / salvage) is a clean taxonomy; the two-phase model maps to the bait/bite doctrine of ADR-014; per-player projection follows ADR-037; OTEL coverage closes Sebastien's GM-panel gap. The findings are clarifications the implementation story must resolve before red, not architectural errors. Approving the design phase ships the load-bearing decisions and lets the implementation work proceed against a real spec rather than waiting on round-trip revisions.

Findings 1 and 2 should ideally be fixed in the ADR before merge, but since they are clarifications about fields whose runtime behavior is not yet implemented, deferring to the implementation story is acceptable provided the findings are visible (recorded here in the session and surfaced as forward impact in the Dev Assessment downstream).

### Project-rules verification

| Rule (CLAUDE.md / SOUL.md) | Status | Evidence |
|---------------------------|--------|----------|
| No silent fallbacks | ✓ | ADR §Implementation Notes: validator raises `ConfrontationLoaderError` on missing condition block |
| No stubs / no half-wired features | ✓ | Implementation deferred to a downstream story, not stubbed in 47-8 |
| Verify wiring, not just existence | ✓ | ADR §Implementation Notes requires "integration test confirms the apply_inventory_changes → evaluate_salvage_acquisition → dispatch_confrontation chain runs end-to-end" |
| Every test suite needs a wiring test | ✓ | Same — integration test mandated by ADR |
| OTEL Observability Principle | ✓ | Two new spans with full attribute lists; positioned as Sebastien's lie detector |
| No Jira / personal project rule | ✓ | Session and commit reference no Jira keys |

**Handoff:** to SM (Mad Hatter) for the finish ceremony.

## Dev Assessment

**Implementation Complete:** Yes (chore bypass — no production code in scope)
**Decision:** Mirror TEA's chore bypass. Design-only story; deliverables are markdown ADR + YAML scenario spec authored during the design phase by architect. Nothing for Dev to implement.

**Files Changed (orchestrator only):**
- `docs/adr/099-coyote-object-salvage-hooks.md` — new ADR (author: architect)
- `scenarios/coyote_salvage_smoke.yaml` — new scenario seed (author: architect)
- `docs/adr/README.md` — auto-regenerated by `scripts/regenerate_adr_indexes.py`
- `CLAUDE.md` — auto-regenerated by `scripts/regenerate_adr_indexes.py`

**Server/Content branches:** Created by sm-setup, no commits added. The ADR specifies code targets in `sidequest-server/sidequest/magic/` and item-tag extensions in `sidequest-content/`, but those changes are the downstream implementation story's scope, not 47-8's. The empty branches can be deleted at story-finish time or left for the implementation story to rebase on.

**Tests:** N/A — chore bypass per TEA Assessment. No new tests; no existing tests broken. (`just check-all` is not exercised under chore bypass.)

**Branch:** `feat/47-8-coyote-object-salvage-hooks-design` (orchestrator only, pushed to origin: commit `5752bfc`).

**Self-review:**
- [x] All acceptance criteria met (see Architect + TEA Assessments)
- [x] Code follows project patterns (ADR frontmatter matches ADR-098, scenario YAML mirrors `scenarios/asymmetric_smoke.yaml`)
- [x] No half-wired features — the ADR is fully written; the scenario seed is fully authored; the implementation work is correctly scoped to a downstream story rather than half-shipped here
- [x] Error handling — N/A for a design story; ADR §Implementation Notes specifies the validator rule (no silent fallback) for the downstream story

**Handoff:** To Reviewer (Queen of Hearts) for ADR + scenario seed review.

## TEA Assessment

**Phase:** finish (BDD)
**Decision:** Chore bypass — no failing tests written.

**Reason:** This story is design-only. Per the agent definition's chore bypass criteria, "Documentation updates (README, docs/)" qualify for bypass. The two deliverables — `docs/adr/099-coyote-object-salvage-hooks.md` (markdown ADR) and `scenarios/coyote_salvage_smoke.yaml` (spec fixture) — are documentation/data artifacts. No production code is in scope under this story; the SalvageConditions model, evaluators, SPAN_ROUTES entries, and per-player state slices specified in ADR-099 are deferred to a downstream implementation story (per the Architect Assessment's Forward Impact section).

**Rule coverage:** N/A — there is no code under test, hence no language-specific lang-review rules apply. SOUL principles (notably the OTEL Observability Principle, "no silent fallback", "verify wiring not just existence") are addressed at the *design* level inside ADR-099 itself: the validator-rule tightening "auto_fire: true requires exactly one of trigger / conditions / salvage_conditions" is the no-silent-fallback rule made explicit in the spec; the SPAN_ROUTES additions answer the OTEL principle; the integration-test requirement in §Implementation Notes (`apply_inventory_changes → evaluate_salvage_acquisition → dispatch_confrontation` end-to-end) answers the wiring-test rule. Test enforcement of these rules lands when the implementation story runs RED.

**AC coverage status:**

| AC | Artifact present | Verified | Notes |
|----|------------------|----------|-------|
| AC1 ADR documenting Coyote Object mechanical model | `docs/adr/099-coyote-object-salvage-hooks.md` | Yes — file exists, registered in regenerated index | Trigger conditions, auto-fire phases, ledger-bar pool, mandatory outputs, OTEL span design all present |
| AC2 Scenario test seed exercising the hook flow | `scenarios/coyote_salvage_smoke.yaml` | Yes — file exists, parses as YAML, references real pack/world | Two-player fixture, five hook behaviors, expected OTEL span attrs |
| AC3 Design spec includes salvage/acquire semantics, pool deltas, MP projection | ADR-099 §Decision + §Multi-player projection | Yes | Two-phase semantics, sanity/bond pool binding, ADR-037 per-player rules locked in |

**Verification performed (no tests, just artifact sanity):**

- `docs/adr/099-coyote-object-salvage-hooks.md` exists; `python3 scripts/regenerate_adr_indexes.py` ran clean (no warnings) after the tag fix from `[magic, ...]` → `[genre-mechanics]`.
- `scenarios/coyote_salvage_smoke.yaml` exists and is well-formed YAML structurally consistent with `scenarios/asymmetric_smoke.yaml` (the closest existing multi-player + assertions scenario).
- `pf validate adr` shows pre-existing drift across the entire ADR tree (322 errors including SUPERSEDED.md and post-096 ADRs); ADR-099 fails the same body-field checks as ADR-098 — not a 47-8 regression. Recorded as Delivery Finding.

**Hand-off:** Dev should also chore-bypass — no implementation work under this story. Dev exit goes straight to Reviewer for ADR + scenario seed review.

## Architect Assessment

**Phase:** finish (BDD)
**Phase owner per workflow:** ux-designer
**Actual author:** architect — user override per routing question; no UX surface in scope.

### Deliverables

1. **ADR-099 — Coyote Object Salvage Hooks** (`docs/adr/099-coyote-object-salvage-hooks.md`)
   - Status: accepted, 2026-05-12
   - Tags: genre-mechanics
   - Related: ADR-014 (bait/bite), ADR-033 (confrontation engine), ADR-037 (multiplayer split), ADR-093 (calibration)
   - Generated indexes regenerated; no warnings

2. **Scenario seed** (`scenarios/coyote_salvage_smoke.yaml`)
   - Two-player fixture in Coyote Star / derelict_hopper
   - Exercises five hook behaviors: first-time discovery (triggered=true), repeat discovery (skip already_observed), per-player discovery split, acquisition firing the_salvage with full attrs, control item (non-coyote_object) emitting no spans

### Design summary

Introduces a third auto-fire shape — the **salvage-hook trigger** — alongside the existing bar-DSL trigger (47-3) and room-entry trigger (47-4). Two phases share one confrontation:

- **Discovery** — actor becomes aware of a coyote_object in their visible scope. Emits `magic.salvage_discovery` OTEL span + a narration beat (the bait, ADR-014). Per-player scope (ADR-037). Records to `observed_salvage_objects` set on per-player MagicState slice. No confrontation fires.
- **Acquisition** — actor's inventory mutation chain materializes a coyote_object. `magic.salvage_acquisition` OTEL span fires + `the_salvage` confrontation enters active state via the existing `dispatch/confrontation.py` flow. Per-actor scope.

Auto-fire invariant tightened: `auto_fire: true` MUST set exactly one of `auto_fire_trigger | fire_conditions | salvage_conditions`. Validator enforces; no silent fallback.

### Acceptance criteria coverage

| AC | Covered by | Notes |
|----|------------|-------|
| AC1 ADR documenting Coyote Object mechanical model | ADR-099 §Decision | All required surfaces: trigger conditions, auto-fire phases, ledger-bar pool binding, mandatory advancement outputs, OTEL span design |
| AC2 Scenario test seed exercising the hook flow | `scenarios/coyote_salvage_smoke.yaml` | Fixture with coyote_object + control item; discovery + acquisition assertions; expected OTEL span attrs |
| AC3 Design spec includes salvage/acquire semantics, pool deltas, MP projection | ADR-099 §Decision, §Multi-player projection | Two-phase semantics explicit; pool binding sanity/bond preserved from 47-3; ADR-037 per-player rules locked in |

### Deviations from spec

- **None blocking.** The story scope (ADR + scenario seed) was authored as specified.
- **Routing deviation:** BDD workflow's `design` phase is assigned to `ux-designer`; this story's ADR work was authored by architect per user routing decision. Recorded in Delivery Findings.
- **No item-YAML changes shipped.** The ADR specifies `coyote_object: bool` and `salvage_phase_default` fields on item definitions, but item-loader extension is downstream-story work (red/green/review phases under a separate story, since 47-8 is design-only).

### Forward impact

- Downstream implementation story should plan: ~30 LOC SalvageConditions model, ~80 LOC two evaluators, two SPAN_ROUTES entries, per-player state slice extensions, item-schema additive flags, validator rule tightening, integration test for the inventory→evaluator→dispatch chain.
- The scenario seed's `fixture:` block (items_in_room overlay) requires a small extension to the playtest harness if it doesn't already support pre-populating room contents; the implementation story should confirm or extend.

### Reuse audit (per architect's pragmatic-restraint)

- **Reused (no new code):** `dispatch/confrontation.py` flow, `apply_inventory_changes` mutation chain, per-player `MagicState` slice (47-3), `SPAN_ROUTES` registry, `LoreFragment` for narration beats, existing the_salvage outcome catalog and pool binding.
- **New code:** `SalvageConditions` model (~30 LOC), two evaluators (~80 LOC), two SPAN_ROUTES entries, two per-player state-slice fields. Validator rule tightened (~5 LOC). Item-tag schema additive (~10 LOC across loader). Total ~125 LOC for a load-bearing mechanic — proportionate.
- **Rejected:** new confrontation pair (would split one event into two), `FireConditions` overload (would muddle two distinct trigger domains), narrator-emitted explicit `salvage_working` block (would re-create the narrator-discretionary failure mode).

## Sm Assessment

**Story:** 47-8 — Coyote Object salvage hooks design (ADR + scenario seed). 3 pts, p3, BDD workflow, design phase only (downstream stories will implement red/green/review).

**Scope:**
- ADR documenting Coyote Object mechanical model: salvage hook triggers, auto-fire on discovery/acquisition, ledger-bar pool binding, mandatory advancement outputs, OTEL design.
- Scenario test seed in `scenarios/` exercising the hook flow (fixture + discovery vs. acquisition condition assertions + expected OTEL spans).
- Multi-player projection rules per ADR-037 (per-player vs. shared state).

**Routing note:** BDD workflow's `design` phase points to **ux-designer** per workflow YAML, but this story is an ADR for a magic-system mechanic — architect territory, not UX. The handoff will report `ux-designer` per the resolve-gate output; **user should redirect to architect** if appropriate, or accept ux-designer if they want UX framing on the player-facing surface of salvage hooks. Story is design-only, so the design phase agent does the bulk of the work.

**Context ready:** Magic Phase 5 confrontations already wired (47-3 shipped `the_salvage` among five named confrontations). Salvage semantics need to extend into auto-fire hooks here. Rig MVP Phase C spec exists at `docs/superpowers/specs/2026-04-29-rig-mvp-coyote-reach-design.md`. No blockers.

**Branches:** Created in orchestrator (off main), server (off develop), content (off develop).

**No Jira** — project does not use Jira (per CLAUDE.md + memory).

## References

- **Magic Phase 5 Plan:** docs/superpowers/plans/2026-04-28-magic-system-coyote-reach-v1.md
- **Rig MVP Phase C Design:** docs/superpowers/specs/2026-04-29-rig-mvp-coyote-reach-design.md
- **ADR-037 Shared-World / Per-Player State Split**
- **ADR-059 Monster Manual — Server-Side Pre-Generation**
- **Previous Confrontation Infrastructure:** sidequest-server/sidequest/magic/confrontations.py, sidequest-content/genre_packs/space_opera/worlds/coyote_star/confrontations.yaml

## Branches

- **Orchestrator:** feat/47-8-coyote-object-salvage-hooks-design (off main)
- **Server:** feat/47-8-coyote-object-salvage-hooks-design (off develop)
- **Content:** feat/47-8-coyote-object-salvage-hooks-design (off develop)