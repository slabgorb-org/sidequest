---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-4: Confrontation cutover — live IntentRouter wiring + retire begin_confrontation (atomic)

> **Story context written by TEA (Igor) during RED**, 2026-05-24. SM-setup
> skipped context creation (recurring failure per project memory
> `feedback_sm_setup_misfiles_session`). Logged as Design Deviation #1
> in the session file. The corrected ACs and the AC4-shape deviation
> (see "AC Reframing" below) are the load-bearing additions over the
> raw epic-59 AC text.

## Business Context

This is **the big migration** — the atomic cutover that retires the
narrator-self-reports-engagement model on the SDK confrontation path and
replaces it with the IntentRouter spine (ADR-113). After this story, the
narrator no longer signals confrontation engagement via `begin_confrontation`;
the IntentRouter classifies the player's intent pre-narrator and
`run_dispatch_bank` calls the confrontation handler before the narrator runs.
The narrator then narrates *already-real* state — the SOUL "Illusionism"
counter the epic exists to deliver.

Per the project memory rule `feedback_one_mechanism_per_problem`, this is
done in **one PR, no parallel window**. The 59-3 watcher (router-vs-engine
lie-detector, merged at `778dc44`) is the safety net during the flip — if
router decisions don't match engine engagement on the new live path, the
watcher fires `dispatch_engagement.confrontation.mismatch` spans on the GM
panel immediately.

**Player-visible impact:** Sebastien (mechanical-first) sees the
`intent_router.decompose` → `intent_router.dispatch.confrontation` →
`encounter.created` span chain on the GM panel — provable engagement
ordering, not narrator self-report. Keith (lie-detector) catches any
divergence the moment the router-vs-engine watcher chirps.

## Technical Guardrails

### Reuse-first inventory (per Architect pragmatic-restraint)

Every component already exists. Do not invent.

| Component | Location | Status |
|-----------|----------|--------|
| `IntentRouter` producer (59-2) | `sidequest/agents/intent_router.py` | Live; `IntentRouter.decompose(action=, state_summary=) → DispatchPackage` |
| SDK-Haiku adapter for router | `sidequest/agents/llm_factory.py` `build_intent_router_llm()` | Live |
| `DispatchPackage` / `PlayerDispatch` / `SubsystemDispatch` | `sidequest/protocol/dispatch.py` | Live; `degraded` field already removed (59-2) |
| `run_dispatch_bank` executor | `sidequest/agents/subsystems/__init__.py:160` | Live; topo-sorts, emits per-dispatch OTEL |
| Confrontation engine entrypoint | `sidequest/server/dispatch/encounter_lifecycle.py:217` `instantiate_encounter_from_trigger` | Live; same function `narration_apply` calls today |
| Watcher (59-3) | `sidequest/agents/dispatch_engagement_watcher.py` `run_dispatch_engagement_watcher` | Live; engagement witness for confrontation is `snapshot.encounter is not None AND snapshot.encounter.encounter_type == params["type"]` (pinned in 59-3 tests) |
| Subsystem handler shape | `subsystems/{reflect_absence,distinctive_detail_hint,npc_agency}.py` | Mirror these — `subsystems/confrontation.py` is the new file |
| Subsystem registry | `subsystems/__init__.py:117-128` `_register_defaults()` | Add `confrontation → handler` here |
| Live wiring site | `sidequest/server/websocket_session_handler.py:3172-3176` (dormant comment "Story 59-4 wires it in") | The IntentRouter call slots in here, pre-narrator |

### Architecture — the cutover surface

**New file:** `sidequest/agents/subsystems/confrontation.py`

```python
async def run_confrontation_dispatch(
    dispatch: SubsystemDispatch,
    *,
    snapshot: GameSnapshot,
    pack: GenrePack,
    player_name: str,
    npcs_present: list,
    additional_player_names: list[str] | None = None,
) -> SubsystemDispatchOutcome:
    """Engage confrontation engine BEFORE the narrator runs.

    Reads `dispatch.params["type"]` and calls
    `instantiate_encounter_from_trigger`. Mutates `snapshot.encounter`
    in place. Emits the same OTEL spans the existing
    `narration_apply.py:2528` consumer site emits.
    """
```

(Signature pinned by Dev during GREEN; mirror the existing handler shapes
in `subsystems/reflect_absence.py` etc. for `SubsystemDispatchOutcome`.)

**Live wiring site:** `websocket_session_handler._execute_narration_turn`
around line 3172. Today the function comments that "Intent Router…is not
yet on the live turn path — Story 59-4 wires it in" and leaves
`turn_context.dispatch_package = None`. The wiring is:

1. Build a state summary for the router from `snapshot` (reuse the
   slimmed snapshot per Story 110 / Architect lean — confirm with Dev
   during GREEN).
2. `package = await intent_router.decompose(action=action, state_summary=...)`.
3. `await run_dispatch_bank(package, context={"snapshot": snapshot, "pack": pack, "player_name": player_name, ...})`.
4. Assign `turn_context.dispatch_package = package` for the narrator
   prompt builder downstream consumers (redaction, narrator instructions).
5. Existing call to `run_narration_turn` proceeds — narrator sees the
   already-engaged snapshot.

After the narrator turn, the 59-3 watcher runs on
`(package, post_turn_snapshot)` as it already does.

### Retirement surface

| Site | Today | After 59-4 |
|------|-------|------------|
| `sidequest/agents/tools/begin_confrontation.py` | Live `@tool`-decorated function | Move file to `sidequest/agents/tools/_retired/begin_confrontation.py`. One-line module docstring: "Retired in Story 59-4 (ADR-113). Engagement is router-driven via `subsystems/confrontation.py`." |
| `sidequest/agents/tools/__init__.py:10-40` | Imports `begin_confrontation` in the barrel | Remove import. Sibling tool imports untouched. |
| `default_registry.tool_definitions()` | Contains `begin_confrontation` entry | Entry absent (consequence of the barrel removal — registry is import-driven). |
| `sidequest/agents/orchestrator.py:3321-3346` (`_assemble_turn_result_sdk` begin_confrontation lift) | Routes `result.confrontation` from the tool-call ledger | Block removed. `result.confrontation` is never set on the SDK path. |
| `sidequest/server/narration_apply.py:2528-2594` (`if result.confrontation:` branch) | Calls `instantiate_encounter_from_trigger` from the narrator's sidecar field | Block removed. Confrontation creation is router-driven only. The OTEL spans (`encounter_empty_actor_list_span`, etc.) move into the new `subsystems/confrontation.py` handler so they still fire on the new path. |
| `sidequest/agents/orchestrator.py:1100-1110` comment block | Explains why `confrontation` is intentionally NOT in `_SDK_TOOL_OWNED_FIELDS` (sidecar lift mechanism) | Update comment to reflect new doctrine: confrontation is now router-driven (subsystem handler), not narrator-emitted. The DICT ITSELF does not change — see AC4 reframing. |
| `sidequest/agents/narrator_prompts/output_only.md` | Contains §4 begin_confrontation routing rule (note: file was renamed from `output_only_sdk.md` per `narrator_prompts/AUDIT.md:51-53`) | §4 rewritten: confrontation engagement is router-driven, not narrator's concern. `begin_confrontation` removed from routing rules. |
| `docs/adr/111-narrator-guardrails-into-tool-descriptions.md` | Confrontation criteria routed to `begin_confrontation` tool description | Implementation-note appended: criteria migrate to IntentRouter's Haiku system prompt (`intent_router.py:_SYSTEM_PROMPT`). |

### AC Reframing (deviation from epic AC text)

**Epic AC4 text:** "Remove `confrontation` from `_SDK_TOOL_OWNED_FIELDS` (orchestrator.py:1088). Sibling fields untouched."

**Reality (verified `orchestrator.py:1091-1124` 2026-05-24):** `confrontation`
is NOT in this dict today, and an explicit 10-line comment block at
lines 1100-1110 explains exactly why (the SDK tool cannot create encounters
because `ctx.store.save` is clobbered by `room.save` at turn end). The
engagement mechanism is instead `result.confrontation` set in
`_assemble_turn_result_sdk` from the begin_confrontation tool-call ledger.

**TEA reframe (preserves AC intent):** Test AC4 as a **regression guard
plus dependent cleanups**:

1. `_SDK_TOOL_OWNED_FIELDS` still does NOT contain `confrontation` after
   the cutover (no one accidentally adds it during the migration).
2. Sibling fields (`status_changes`, `location`, `magic_working`,
   `beat_selections`, `days_advanced`, `affinity_progress`,
   `game_patch_dict`) remain present and unchanged — regression guard
   against scope creep.
3. The `_assemble_turn_result_sdk` begin_confrontation lift (lines
   3321-3346) is REMOVED — `result.confrontation` is never set on the
   SDK path post-cutover.
4. The `narration_apply.py:2528-2594` `result.confrontation` consumer
   branch is REMOVED — the field is not consumed anywhere.

The AC text predates re-inspection of the current orchestrator surface.
Architect (Leonard) flagged similar drift in 59-3's AC1 (span-name
ambiguity) — same fix here: log a Design Deviation, test the intent.

### Fail-loud discipline (project memory `feedback_no_fallbacks_hard`)

- IntentRouter failure (Haiku timeout, parse error, schema-invalid)
  raises `IntentRouterFailure`. The wiring site does ONE bounded retry
  (the router's `_MAX_TOTAL_ATTEMPTS = 2` is the retry boundary
  already). If both attempts fail, surface explicit failure — DO NOT
  proceed to narrator with no router output. AC7 pins this.
- No silent narrator-only continuation. No fallback to the old
  `begin_confrontation` path during the cutover. No "if router is
  unhealthy, route through sidecar."
- Confidence below threshold = correct intended non-engagement.
  Logged as a normal dispatch outcome. Not a fallback.

### One mechanism per problem (`feedback_one_mechanism_per_problem`)

After 59-4, the SDK confrontation engagement path has exactly ONE
producer (IntentRouter) and ONE engager (`run_confrontation_dispatch`
in `subsystems/confrontation.py`). The sidecar path is gone. No
parallel period. No feature flag. Tests must assert the sidecar path
is dead, not merely "preferred not to use."

### Test wiring (CLAUDE.md "Every Test Suite Needs a Wiring Test"
+ "No Source-Text Wiring Tests")

The AC5 live-wiring test drives a real fixture turn through
`_execute_narration_turn` with a stubbed `IntentRouter` whose
`decompose` returns a synthetic `DispatchPackage` containing a
confrontation dispatch. Assertion is: post-call, `snapshot.encounter`
is set, AND the OTEL spans fired in the expected ORDER
(router → bank → encounter.created), AND the narrator turn ran AFTER
the encounter was created.

No `read_text()` + regex assertions. Behavior or OTEL spans only.

## Scope Boundaries

**In scope:**

- New `sidequest/agents/subsystems/confrontation.py` handler that calls
  `instantiate_encounter_from_trigger`.
- Register `confrontation → run_confrontation_dispatch` in
  `subsystems/__init__.py:_register_defaults()`.
- Wire `IntentRouter.decompose` + `run_dispatch_bank` into
  `_execute_narration_turn` pre-narrator (lines ~3172-3176).
- Move `agents/tools/begin_confrontation.py` →
  `agents/tools/_retired/begin_confrontation.py`. Drop from
  `tools/__init__.py` barrel. Confirm `default_registry.tool_definitions()`
  no longer surfaces it.
- Remove the begin_confrontation→`result.confrontation` lift in
  `_assemble_turn_result_sdk` (orchestrator.py:3321-3346).
- Remove the `result.confrontation` consumer block in
  `narration_apply.py:2528-2594`. Relocate the OTEL spans
  (`encounter_empty_actor_list_span` etc.) into the new dispatch
  handler so coverage holds on the new path.
- Update the comment block at `orchestrator.py:1100-1110` to reflect
  the new doctrine. Do not modify the dict itself.
- Rewrite §4 of `narrator_prompts/output_only.md` — confrontation
  engagement is router-driven, not narrator's concern.
- Amend ADR-111 with the implementation note.
- Verify the 59-3 watcher still fires on the new live path
  (regression guard).

**Out of scope (deferred):**

- Magic_working dispatch handler — 59-5.
- Scenario_clue dispatch handler — 59-6.
- The three additive subsystems (npc_agency, distinctive_detail_hint,
  reflect_absence) live wiring — 59-7 (handlers exist but are not
  router-dispatched today).
- Playtest validation — 59-8.
- Removing `_validate_intent` / `_apply_narration_result_to_snapshot`'s
  intent-classification side-channel — survives the cutover for
  scenario-clue and magic_working until 59-5/6.
- The `_SDK_TOOL_OWNED_FIELDS` dict itself does not change (AC4
  reframe — see above).
- ADR-013's drift status — 59-2 already pointed it at 113 for the SDK
  path; no action here.

## AC Context

> AC text reproduced verbatim from `sprint/epic-59.yaml` 59-4. TEA
> commentary inline; deviations logged in session file.

### AC1: Fixture: synthetic player action ("I block his way and call the bluff") → IntentRouter dispatches `confrontation:negotiation` → handler creates StructuredEncounter on snapshot BEFORE narrator runs. Verified via OTEL spans: `intent_router.decompose` → `intent_router.dispatch.confrontation` → `encounter.created` in order, all in one round.

**Testable shape:** Stub the IntentRouter LLM client to return a
DispatchPackage with one confrontation dispatch (avoids real Haiku
call). Drive `run_dispatch_bank` through the new
`subsystems/confrontation.py` handler. Assert:

1. `snapshot.encounter is not None` after the bank call.
2. `snapshot.encounter.encounter_type == "negotiation"`.
3. OTEL spans fire in order: `intent_router.decompose` (or
   `intent_router_decompose_span` per actual span name in
   `intent_router.py:212`), then `intent_router_subsystem_span` for
   confrontation (per `subsystems/__init__.py:210`), then
   `encounter_confrontation_initiated_span` (per
   `encounter_lifecycle.py:329`). Confirm exact span names against
   the live emitters during RED — the AC text uses idealized names.
4. The narrator call site has NOT been invoked yet at the moment
   `snapshot.encounter` is set (ordering is the whole point).

**TEA note on span names:** AC1 names `encounter.created` but the actual
emitted span (per Explorer survey) is `encounter_confrontation_initiated_span`.
Use the LIVE span name from `encounter_lifecycle.py`. Log this as a Design
Deviation if Dev needs to rename for clarity.

### AC2: Retirement guard: assert `narration_apply.py` no longer instantiates an encounter from `result.confrontation` (search-based test on the function body OR behavioral: set `result.confrontation` manually, assert no encounter created).

**Testable shape:** Behavioral (CLAUDE.md "No Source-Text Wiring Tests"
forbids the search-based form). Construct a `NarrationTurnResult` with
`result.confrontation = "negotiation"`. Construct a snapshot with no
encounter. Invoke `_apply_narration_result_to_snapshot()` (or
equivalent). Assert `snapshot.encounter is None` after the call —
the consumer block at 2528-2594 has been removed, so the field is
ignored. No call to `instantiate_encounter_from_trigger` should fire.

### AC3: `begin_confrontation` tool removed from registry; importing it returns a deprecation re-export pointing at the dispatch handler (clean break, not a runtime shim).

**Testable shape:** Two assertions:

1. `from sidequest.agents.tools.default_registry import default_registry; "begin_confrontation" not in [t.name for t in default_registry.tool_definitions()]`.
2. Importing the original location raises `ImportError` or surfaces a
   deprecation stub pointing at `subsystems/confrontation.py`. AC text
   is ambiguous on which — TEA picks **ImportError + retired file at
   `_retired/begin_confrontation.py`**. (A runtime shim that silently
   no-ops would violate `feedback_no_fallbacks_hard`.)

### AC4 (REFRAMED — see AC Reframing above): `_SDK_TOOL_OWNED_FIELDS` does not contain `confrontation`, the begin_confrontation→`result.confrontation` lift is removed from `_assemble_turn_result_sdk`, the `result.confrontation` consumer in `narration_apply.py` is removed. Sibling fields and dict structure unchanged.

**Testable shape:** Four assertions (one for each cleanup):

1. `from sidequest.agents.orchestrator import _SDK_TOOL_OWNED_FIELDS; "confrontation" not in _SDK_TOOL_OWNED_FIELDS` — regression guard.
2. Every legacy key still present (`status_changes`, `location`, …) — sibling-untouched guard.
3. After running `_assemble_turn_result_sdk` with a synthetic
   tool-call ledger that contains a `begin_confrontation` call, the
   resulting `NarrationTurnResult.confrontation` is the dataclass
   default (empty/None) — the lift is gone. (If begin_confrontation is
   fully retired, this test may instead assert the symbol can't be
   constructed; pick whichever shape stays meaningful post-Dev.)
4. (Covered by AC2.)

### AC5: Live wiring test — drive the full turn pipeline (orchestrator → router → bank → narrator) end-to-end through a fixture; assert encounter creation happens BEFORE narrator turn, not after.

**Testable shape:** Mirror
`tests/server/test_location_description_emit.py::test_emit_sends_message_when_room_has_manifest`
shape. Construct a synthetic genre pack + snapshot. Stub the
IntentRouter LLM client (avoid Haiku spend). Stub the narrator LLM
backend to record when it was called. Invoke `_execute_narration_turn`.
Assert ordering via spans (router/bank spans precede narrator span)
AND via call-order on the narrator stub (`mock.call_count == 1` AND the
encounter was created before the narrator stub was invoked — check via
the order in which side effects appeared on the snapshot vs. the
narrator call).

**No `read_text()` or regex assertions.**

### AC6: ADR-111 updated; ADR-113's implementation-pointer updated to this story.

**Testable shape:** Documentation-only. The ADR-schema commit hook
enforces frontmatter integrity (project memory
`project_adr_schema_enforced_rules`). TEA does NOT write a test that
greps ADR markdown — that's a source-text wiring test. Instead:
spot-check during review that the ADR-111 implementation note and
ADR-113 implementation pointer reference 59-4. Log as Design Deviation
if Dev needs scope guidance.

### AC7: Failure path (Memory `feedback_no_fallbacks_hard`): mock router to raise → assert ERROR span emitted, one bounded retry attempted, then explicit failure surfaced (no silent narrator-only continuation).

**Testable shape:** Stub the router's LLM client to always raise.
Invoke `_execute_narration_turn`. Assert:

1. `intent_router_failed_span` fires at least once (per
   `intent_router.py:227-239`).
2. The bounded retry happens (`intent_router.py:_MAX_TOTAL_ATTEMPTS = 2`
   gives two attempts total). Inspect span count or call_count on the
   LLM stub.
3. After both attempts fail, the narrator is NOT called — assert via
   narrator stub call_count == 0.
4. The turn surfaces an explicit failure to the caller (raises or
   emits a user-visible error). NO silent fallback.

### AC8: The Story 59-1 ACs that targeted `advance_confrontation` invocation are formally superseded — note appended to 59-1's archived session and to ADR-111's commentary.

**Testable shape:** Documentation-only — same handling as AC6. Spot-check
in review. TEA does not write a grep-test on ADR markdown or session
archives.

**Additional TEA-authored test (not in AC list — wiring regression):**
"Watcher coverage holds on new live path." Drive the live pipeline
with a stubbed router that dispatches confrontation, but stub the
confrontation handler to no-op (simulate handler regression). Assert
`dispatch_engagement.confrontation.mismatch` span fires from the 59-3
watcher. Without this test, a future change to `subsystems/confrontation.py`
that silently breaks engagement would slip past the safety net.

## Assumptions

1. **59-3 has shipped** the `dispatch_engagement_watcher` module and the
   watcher is wired into the post-turn hook. Confirmed: 59-3 is `done`,
   commit `778dc44`, archive session present.
2. **59-2 has shipped** the IntentRouter with the SDK-Haiku adapter
   and `degraded` field removed. Confirmed via direct file inspection
   (`intent_router.py`, `dispatch.py`).
3. **The `_execute_narration_turn` wiring site is the right one** —
   the dormant comment at lines 3172-3176 says so explicitly. If Dev
   finds a different orchestrator entrypoint that fits better, log as
   Design Deviation.
4. **`output_only_sdk.md` is the renamed `output_only.md`** per
   `narrator_prompts/AUDIT.md:51-53`. If Dev finds another file with
   the begin_confrontation routing rule, treat as scope addition and
   log Deviation.
5. **`_assemble_turn_result_sdk` test isolation is feasible.** The
   function (orchestrator.py:3259) takes `extraction`, `raw_response`,
   `context`, `elapsed_ms`, `prompt_text`, token counts — TEA may need
   a synthetic context fixture. If too coupled, AC4 part 3 may need
   to be covered by an integration test through the live pipeline
   instead.

If any of these proves wrong during RED or GREEN, log under
`## Design Deviations` and notify SM (Captain Carrot) immediately.

---

**TEA (Igor):** Story context authored during RED phase due to
SM-setup skipping context creation. Deviation logged in session file.
**Date:** 2026-05-24
**Parent epic context:** `sprint/context/context-epic-59.md`
**Predecessor story context:** `sprint/context/context-story-59-3.md`
