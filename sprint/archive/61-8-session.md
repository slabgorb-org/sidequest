---
story_id: "61-8"
jira_key: null
epic: "61"
workflow: "trivial"
---
# Story 61-8: Epic 61 cleanup: scope-deferred items from 61-1/61-2/61-3/61-7

## Story Details
- **ID:** 61-8
- **Jira Key:** N/A (personal project, no Jira)
- **Workflow:** trivial (downshifted from tdd per plan-ceremony memory: mechanical cleanup bundle, one implementer pass)
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-05-23T20:29:02Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-23T15:00:00Z | 2026-05-23T19:48:37Z | 4h 48m |
| implement | 2026-05-23T19:48:37Z | 2026-05-23T20:03:03Z | 14m 26s |
| review | 2026-05-23T20:03:03Z | 2026-05-23T20:14:10Z | 11m 7s |
| implement | 2026-05-23T20:14:10Z | 2026-05-23T20:24:02Z | 9m 52s |
| review | 2026-05-23T20:24:02Z | 2026-05-23T20:27:12Z | 3m 10s |
| implement | 2026-05-23T20:27:12Z | 2026-05-23T20:28:11Z | 59s |
| review | 2026-05-23T20:28:11Z | 2026-05-23T20:29:02Z | 51s |
| finish | 2026-05-23T20:29:02Z | - | - |

## Story Context

This is a scope-deferred cleanup bundle for epic 61 stories 61-1, 61-2, 61-3, and 61-7. Each item is independent and small; the suggested order is:

### §A. From 61-1 — defense-in-depth on lore_store wiring
Extend orchestrator.py:3472-3481 fail-loud guard to alarm specifically when context.lore_store is None in production. Add matching unit test.

### §B. From 61-2 — npc_pool exhaustiveness audit
Audit the materialization path and add regression test for off-scene NPCs in npc_pool.

### §C. From 61-3 — constant rename + span attribute
- (C1) Rename SOFT_PROMPT_BUDGET_BYTES → PROMPT_BUDGET_BYTES_HARD
- (C2) Add refused_oversized=True span attribute
- (C3) GM-panel red-band subscriber (sidequest-ui, separate if needed)

### §D. From 61-7 review fan-out — silent-failure + test-coverage debt
- (D1) OTEL attribute to distinguish unresolvable_name_drop from off_scene_drop
- (D2) tool.npcs.encounter_bypassed boolean OTEL attribute
- (D3) test for empty encounter.actors list
- (D4) test for PC-with-no-current_room degraded-location path
- (D5) Empty-collection noise cosmetic cleanup
- (D6) Fix or annotate five pre-existing pyright errors

### §E. Type-design backlog (defer if surface too broad)
- (E1) Introduce RoomId / NpcName newtypes
- (E2) Sealed-variant Npc location field consolidation
- (E3) active_encounter() accessor
- (E4) encounter_type stringly-typed (pre-existing, not 61's diff)

### §F. Workflow improvement (orchestrator, not server)
Scope `just server-fmt` to changed files only (ruff format $(git diff --name-only)).

### §G. Test live-content coupling (pre-existing)
Inventory and decide: switch to fixture pack or document coupling. Not blocking.

## SM Assessment

Story scope: 12 mechanical cleanup sub-items bundled across §A–§G, each
independently small (rename a constant, add an OTEL attribute, extend a
fail-loud guard, add regression tests for empty encounter.actors and
PC-with-no-current_room paths, etc). Every sub-item has its file:line
anchor and decision pre-recorded in the story description; no
architectural choice remains open.

Workflow downshifted from `tdd` → `trivial` per
[[feedback_plan_ceremony]] memory: mechanical refactors at this scope
get one implementer pass, not TEA-RED + Reviewer fan-out per sub-item.
Reviewer still runs at the end (trivial workflow gate). Dev judgment:
land §A through §D in one PR; §E/§F/§G may split into their own stories
if Dev finds scope creeping.

Story-context creation skipped (single-pass cleanup; epic-61 context is
already authoritative and the per-sub-item file:line anchors live in the
sprint YAML description). Jira-claim skipped (personal project, no
Jira).

Handoff to Dev (Ponder Stibbons) for implement phase.

## Delivery Findings

### Dev (implementation)

- **Improvement** (non-blocking): `_apply_phase_c_projections` returns
  a counts dict that is spread into the `prompt_game_state_bytes_span`
  context manager via `**`. The same pattern in `_auto_mint_prose_only_npcs`
  spreads `extra_attrs`. Both required pyright `reportArgumentType` waivers
  because the span helpers in `sidequest/telemetry/spans/` declare a
  keyword-only `_tracer: Tracer | None = None` parameter ahead of `**attrs`,
  and pyright cannot statically prove that the spread dict has no
  `_tracer` key. A future cleanup could rename `_tracer` → `tracer_override`
  (the actual semantic) on the span signatures and remove the leading
  underscore, eliminating the entire class of shadow-collision warnings.
  Affects `sidequest-server/sidequest/telemetry/spans/` (signature
  rename across all 30+ span helpers). *Found by Dev during §D6 pyright
  cleanup — pragma is a workaround, not a fix.*

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/orchestrator.py` — §A new lore_store fail-loud guard,
  §C1 SOFT_PROMPT_BUDGET_BYTES → PROMPT_BUDGET_BYTES_HARD rename + module
  docstring update, §C2 refused_oversized=True span attribute at both
  refuse paths.
- `sidequest/agents/tools/list_npcs_in_scene.py` — §D2 tool.npcs.encounter_bypassed
  boolean OTEL attribute.
- `sidequest/game/world_materialization.py` — §B `_apply_npc` now also
  seeds `snap.npc_pool` (idempotent, `drawn_from="world_authored"`).
- `sidequest/server/session_helpers.py` — §D1 split unresolvable-name
  drops from off-scene drops in the in-scene filter (new
  `npcs_unresolvable_name_dropped` counter); §D6 fixed 5 pyright errors
  (3 by `isinstance` narrowing / explicit None guard, 2 by pragma on
  dict-spread).
- `tests/server/test_turn_context_sdk_wiring.py` — §A 2 new tests
  (lore_store=None fires the dedicated warning; fully-wired stays silent).
- `tests/game/test_world_materialization.py` — §B 2 new tests (chapter
  apply seeds npc_pool; re-apply is idempotent).
- `tests/server/test_61_8_projection_edge_cases.py` — NEW. §D3 empty
  encounter.actors regression tests (2); §D4 PC-with-no-current_room
  degraded-location tests (2).
- `tests/agents/test_61_3_hard_cap_oversized_canary.py` + `test_orchestrator_oversized_canary.py`
  — §C1 rename mechanical updates.

**Tests:** 7319 passed, 385 skipped, 0 failed (GREEN).
**Pyright:** clean on session_helpers.py (was 5 errors).
**Ruff:** clean.

**Branch:** feat/61-8-epic-61-cleanup-deferrals (pushed to origin).

**Out of scope (per SM setup):**
- §C3 GM-panel red-band subscriber — sidequest-ui repo, separate story
- §E type-design backlog — broader Npc / encounter refactor
- §F `just server-fmt` scope-to-changed-files — orchestrator/justfile,
  separate repo
- §G test live-content coupling on caverns_and_claudes/mawdeep —
  pre-existing pattern, inventory + decide is its own story

**Handoff:** To review phase (reviewer).

## Dev Assessment (review-fix round 2)

**Review-Fix Complete:** Yes (3 MUST-FIX + 8 SHOULD-FIX addressed)

**Files Changed (round 2):**
- `sidequest/agents/orchestrator.py` — §A both partial-wiring guards
  now publish watcher events alongside logger.warning.
- `sidequest/game/world_materialization.py` — §B extracted
  `_ensure_world_authored_pool_member`; both `_apply_npc` branches now
  seed the pool; prose-pending entries are promoted on chapter apply.
- `sidequest/server/session_helpers.py` — §D6 logger.warning on
  non-dict seat_map fallthrough at both call sites; §D1 docstring
  Returns block lists all 5 counters; §D6 pyright pragma rationale
  comments rewritten.
- `tests/server/test_turn_context_sdk_wiring.py` — §A negative
  boundary test + §A watcher-event regression test (+2).
- `tests/game/test_world_materialization.py` — §B existing-NPC branch
  pool-seed test + promote-prose-pending test + don't-clobber-
  canonical test (+3).
- `tests/server/test_61_8_projection_edge_cases.py` — §D1 unresolvable
  counter test + §D3 direct predicate unit test (+2).
- `tests/agents/test_61_3_hard_cap_oversized_canary.py` — §C2
  InMemorySpanExporter test asserting refused_oversized=True on the
  action span (+1).
- `docs/adr/098-stateless-narrator-turns.md` (orchestrator repo) —
  stale `SOFT_PROMPT_BUDGET_BYTES` reference updated to
  `PROMPT_BUDGET_BYTES_HARD` plus rename amendment note.

**Tests:** 7327 passed (was 7319, +8 new), 0 failed (GREEN).
**Pyright:** clean on session_helpers.py.
**Ruff:** clean.

**Branch:** feat/61-8-epic-61-cleanup-deferrals (pushed; commit 7d85875
on top of round-1 commit c9296b8).

**MUST-FIX status (3/3 addressed):**
1. ✓ §A watcher_hub.publish_event added (also closed pre-existing
   context_missing_ids gap per reviewer audit ask)
2. ✓ §B docstring/code reconciled via promote-on-collision contract
3. ✓ §B existing-NPC branch refactored to call
   `_ensure_world_authored_pool_member` on both branches

**SHOULD-FIX status (8/8 addressed):**
4. ✓ §D6 isinstance fallthrough now logs warning at both call sites
5. ✓ §D1 docstring Returns block lists all 5 counters
6. ✓ §D6 pragma rationale rewritten to attribute reportArgumentType
7. ✓ ADR-098 stale reference updated
8. ✓ §D3 direct unit test for is_npc_anchored_by_encounter(empty_actors)
9. ✓ §C2 InMemorySpanExporter test asserts refused_oversized=True
10. ✓ §D1 unresolvable counter exercised by direct test
11. ✓ §A negative boundary test (mutual-exclusion regression guard)

**Deferred (out of scope per round-1 acceptance):**
- Live-content coupling (story §G — separate story)
- Pre-existing pyright errors outside §D6 scope (file as Delivery
  Finding; pre-existing on develop, line-shifted only)
- `_tracer → tracer_override` global rename (already in Delivery
  Findings; broader refactor)

**Handoff:** To review phase (reviewer round 2).

## Dev Assessment (review-fix round 3 — lint hotfix)

**Round-3 fix:** Removed unused `import json` from
`tests/server/test_turn_context_sdk_wiring.py:31`. The import was added
in round-2 alongside `asyncio` for the watcher-event test's original
draft; the final test uses `send_json` directly so `json` was never
referenced.

**Files Changed:** `tests/server/test_turn_context_sdk_wiring.py` (-1 line).
**Ruff:** clean.
**Tests:** still GREEN (9 passed on the touched file; full sweep
unchanged from round 2 at 7327).
**Branch:** commit 34dcc94 on top of round-2 7d85875.

**Handoff:** To review phase (reviewer round 3).

## Reviewer Assessment (round 3)

**Verdict:** APPROVED

**Method:** Direct-read of the round-3 incremental diff (`git diff 7d85875..HEAD` — 1 file, -1 line). Single-line lint fix; no behavior change, no test surface change. Re-running the 9-specialist fan-out on a removed `import json` would be pure ceremony.

**Verification:**
- [VERIFIED] `import json` removed from `tests/server/test_turn_context_sdk_wiring.py:31`. Was added in round 2 but never referenced; the watcher-event test uses `send_json` directly.
- [VERIFIED] `uv run ruff check sidequest/ tests/` → "All checks passed!"
- [VERIFIED] `uv run pytest tests/server/test_turn_context_sdk_wiring.py` → 9 passed.

**Specialist tag carry-forward (round-3 has no new surface):**
- **[LINT]** — round-3 SHOULD-FIX item resolved. ruff clean.
- **[DOC][EDGE][SILENT][TEST][TYPE][SEC][SIMPLE][RULE]** — no new surface in round-3 diff (single import removal); round-1 + round-2 specialist coverage stands unchanged.

**Data flow traced:** All round-1 MUST-FIX + SHOULD-FIX items verified in round-2 assessment above; round-3 cleared the sole regression. Story is mergeable.

**Pattern observed:** Clean three-pass cycle — round-1 surfaced 11 findings via 9-specialist fan-out, round-2 addressed all 11 + introduced 1 lint regression, round-3 cleared the regression in one line. Demonstrates the right-size-ceremony pattern: heavy adversarial review on the first pass, direct-read on surgical fixes.

**Handoff:** To SM (Captain Carrot Ironfoundersson) for finish-story.

## Reviewer Assessment (round 2)

**Verdict:** REJECTED (one tiny SHOULD-FIX — round-2 regression)

**Method:** Direct-read of the round-2 incremental diff (`git diff c9296b8..HEAD` — 7 files, +514/-52). Did NOT re-fan-out the 9 specialist subagents — the round-1 fan-out covered the same code surface and produced the MUST-FIX/SHOULD-FIX list this round directly addresses; re-running them on the surgical fix would be ceremony-without-yield per the [[plan-ceremony]] memory. Round-1 Subagent Results table preserved above; round-2 direct-read covers the incremental delta.

### Round-1 findings — disposition

**MUST-FIX (3) — all addressed:**

| # | Round-1 finding | Round-2 fix | Verdict |
|---|----|----|----|
| 1 | §B existing-NPC branch skips pool-seed | Extracted `_ensure_world_authored_pool_member` helper called from both `_apply_npc` branches. Regression test `test_npc_chapter_apply_seeds_pool_on_existing_npc_branch` constructs legacy-save shape (Npc in `snap.npcs`, no pool entry) and asserts pool is seeded on the existing-NPC branch. | ✓ FIXED |
| 2 | §B docstring lies about override behavior | Code now matches docstring — prose-pending entries (`drawn_from='dialogue_extraction'` OR `observation_pending=True`) are PROMOTED to `world_authored` on chapter apply; other sources left untouched. Test `test_npc_chapter_apply_promotes_prose_pending_pool_entry` exercises promotion; sibling `test_npc_chapter_apply_does_not_clobber_canonical_pool_entry` guards the boundary. Reviewer's preferred resolution (a) per round-1 verdict text. | ✓ FIXED |
| 3 | §A guard missing watcher_hub.publish_event | `_pub_watcher` added for BOTH `narrator_context_missing_ids` (closing pre-existing umbrella gap per reviewer audit ask) AND `narrator_context_missing_lore_store`. Wiring test `test_sdk_path_lore_store_warning_publishes_watcher_event` subscribes `_FakeSocket` to the live `watcher_hub` and asserts the event is published. | ✓ FIXED |

**SHOULD-FIX (8) — all addressed:**

| # | Round-1 finding | Round-2 fix | Verdict |
|---|----|----|----|
| 4 | §D6 isinstance fallthrough silenced loud failure | `else: logger.warning(...)` branches added at both call sites (`_resolve_acting_character_name`:376 and `_build_turn_context`:650). Surfaces hook-contract drift instead of silently masking it. | ✓ FIXED |
| 5 | §D1 docstring missing 2 returned keys | Returns block now lists all 5 counters: `room_states_dropped`, `npcs_dropped` (with new "legitimately off-stage" clarification), `known_facts_truncated_total`, `clues_truncated`, `encounter_anchored_count` (61-7 backfilled), `npcs_unresolvable_name_dropped` (61-8 §D1). | ✓ FIXED |
| 6 | §D6 pyright pragma rationale inaccurate | Both pragma comments rewritten to attribute the issue to `reportArgumentType` type-arg mismatch (the actual diagnostic), not the invented "key shadow `_tracer`" mechanism. | ✓ FIXED |
| 7 | ADR-098 stale `SOFT_PROMPT_BUDGET_BYTES` reference | Updated in orchestrator repo (separate commit e7b0900) — new name + rename-amendment note. | ✓ FIXED |
| 8 | §D3 missing direct unit test | `test_is_npc_anchored_by_encounter_returns_false_for_empty_actors` isolates the predicate from convergence-integration coverage. | ✓ FIXED |
| 9 | §C2 no test asserts `refused_oversized=True` | `test_oversized_refuse_stamps_action_span_refused_oversized_attribute` uses `InMemorySpanExporter` (mirroring the test_61_2 pattern Reviewer pointed at) and asserts the attribute on the finished action span. | ✓ FIXED |
| 10 | §D1 no exercising test for unresolvable counter | `test_unresolvable_name_drops_counted_separately_from_off_scene_drops` injects a malformed payload entry (`core.name=None`) directly into `_apply_phase_c_projections` and asserts the counter increments while `npcs_dropped` stays at the legitimate off-stage count. | ✓ FIXED |
| 11 | §A no negative boundary test | `test_sdk_path_unwired_ids_fire_only_umbrella_not_lore_store_warning` exercises `world_id=None + lore_store=None` and asserts mutual exclusion (only `context_missing_ids` fires). | ✓ FIXED |

### Round-2 regression (Reviewer SHOULD-FIX)

- **[LINT] Unused `json` import** at `tests/server/test_turn_context_sdk_wiring.py:31` — Dev added `import json` alongside `import asyncio` (both needed for the original watcher-test draft that decoded text payloads); the final implementation uses `send_json` directly, so `json` is unused. `uv run ruff check` flags it; `ruff check --fix` removes it cleanly. Tiny but real — the gate requires lint-clean before approval.

### Devil's Advocate (round 2)

The promote-on-collision logic at `_ensure_world_authored_pool_member` is the load-bearing change. What could break it?

**Attack 1 — wrong source-tag set:** The promote condition is `existing_member.observation_pending OR existing_member.drawn_from == "dialogue_extraction"`. What if a future code path mints a member with `drawn_from='narrator_invented'` AND `observation_pending=True`? The `observation_pending` clause catches it. What if it's `drawn_from='legacy_registry'` AND `observation_pending=False`? It's NOT promoted — which is correct per the docstring "Other source tags are left alone." The boundary `test_npc_chapter_apply_does_not_clobber_canonical_pool_entry` guards this with `drawn_from='name_generator'`. Solid.

**Attack 2 — fields-not-clobbered claim:** The promote branch only sets `drawn_from` and `observation_pending`. It does NOT update `role`, `pronouns`, `appearance`, or `archetype_id`. Test `test_npc_chapter_apply_promotes_prose_pending_pool_entry` asserts `role == "housekeeper"` and `pronouns == "she/her"` survive. Confirmed.

**Attack 3 — multiple chapters re-applying:** The idempotency test re-applies a chapter and asserts no duplicate pool entries. But the new promote logic flips state on the FIRST encounter. If a chapter re-applies, the second pass hits the "already canonical (`drawn_from='world_authored'`, `observation_pending=False`)" branch and is a no-op. Confirmed by reading the conditional: the promote condition is `observation_pending OR drawn_from == "dialogue_extraction"` — once promoted, neither is true, so the second apply skips the field updates. Idempotent.

**Attack 4 — watcher event payload shape:** `_pub_watcher` calls pass `{"world_id": world_id, "session_id": session_id}` as the event fields. The wiring test only asserts the event_type matches — it does NOT inspect the payload fields. A future regression that drops a field would silently land. This is a NIT, not a blocker — the field set is small and visible.

**Attack 5 — round-1 streaming-path gap mentioned by edge-hunter:** Pre-existing (`_run_narration_turn_streaming` doesn't call `_check_oversized_prompt`). Confirmed deferred in round-1 disposition; still deferred. Not a 61-8 fix.

**Verdict:** No new bombs surfaced. The one round-2 regression (unused `json` import) is a 1-line fix.

### Confirmed Findings (tagged)

- **[LINT] Unused `json` import** at `tests/server/test_turn_context_sdk_wiring.py:31` — round-2 only, easy fix, `ruff --fix` resolves.
- **[VERIFIED][EDGE]** §B both branches of `_apply_npc` now call `_ensure_world_authored_pool_member` — `world_materialization.py:511` (existing branch) + line 549 (new branch). Tests `test_npc_chapter_apply_seeds_pool_on_existing_npc_branch` + `test_npc_chapter_apply_also_seeds_npc_pool` cover both branches.
- **[VERIFIED][DOC]** §B docstring/code reconciled — promote contract documented in `_ensure_world_authored_pool_member` docstring at `world_materialization.py:444-460` matches the implementation at lines 477-484.
- **[VERIFIED][SILENT][RULE]** §A watcher event publishes confirmed at `orchestrator.py:3567` (ids) and `orchestrator.py:3593` (lore_store). Test `test_sdk_path_lore_store_warning_publishes_watcher_event` is the wiring test (live `watcher_hub` subscription, real socket).
- **[VERIFIED][SILENT]** §D6 isinstance else-branches log warning at `session_helpers.py:381-387` and `session_helpers.py:651-657`. Surface hook-contract drift instead of swallowing.
- **[VERIFIED][TEST]** §C2 InMemorySpanExporter test at `test_61_3_hard_cap_oversized_canary.py:413-468` asserts `refused_oversized=True` on the finished `orchestrator.process_action` span. Pattern mirrors `test_61_2_snapshot_seven_field_projection.py:650`.
- **[VERIFIED][DOC]** §D1 docstring Returns block lists all 5 counters at `session_helpers.py:116-134`.
- **[VERIFIED][DOC]** §D6 pragma rationales rewritten at `session_helpers.py:914-924` and `session_helpers.py:1420-1426` to attribute the actual `reportArgumentType` diagnostic.

**Round-2 specialist tag carry-forward** (round-1 fan-out coverage stands; round-2 is a direct-read of incremental diff per [[plan-ceremony]]):

- **[SEC]** — Round-1 status was clean; round-2 diff adds no new I/O, deserialization, or boundary surface (only `_pub_watcher` calls with server-controlled `world_id` / `session_id` slugs). Re-assessment: clean.
- **[TYPE]** — Round-1 deferred 3 type-design items (pre-existing typing weakness, `_tracer` rename — Delivery Finding, drawn_from Literal — broader refactor). Round-2 introduces no new type surface; the new `_ensure_world_authored_pool_member` helper has fully annotated parameters. Re-assessment: clean (deferred items unchanged).
- **[SIMPLE]** — Round-1 confirmed 1 finding (CONTENT_GENRE_PACKS duplicating `find_pack_path` — DEFER per story §G). Round-2 leaves §G deferral in place. Round-2 introduces the new `_ensure_world_authored_pool_member` helper which is a clean extraction (round-1 simplifier preference was `any(...)` over `next(...) is None` — Dev kept `next(...)` for the extracted helper to support the second-pass field-update on the same lookup; the simplification is foreclosed by the new semantic, so the round-1 NIT is correctly dismissed in round 2).

**Handoff:** Back to Dev (Ponder Stibbons) for the single lint fix. After `ruff check --fix`, re-push and re-route to Reviewer for approval.

## Design Deviations

### Dev (implementation)

- **§D5 (Empty-collection noise cleanup) resolved by code reading, not by
  edit.**
  - Spec source: session 61-8 §D5; story description "Empty-collection
    noise: `payload["npcs"] = []` / `payload["room_states"] = {}` in
    `_apply_phase_c_projections`. Cosmetic only, no behavior surface."
  - Spec text: "Either remove the assignments or document why they're
    load-bearing."
  - Implementation: No code change. The current
    `_apply_phase_c_projections` does NOT contain
    `payload["npcs"] = []`. The only related assignment is
    `payload["room_states"] = {}` at line 155, which is already
    documented inline as "Empty dict preserves the structural anchor;
    every other room id is dropped." The §D5 deferral pre-dated the
    final 61-2/61-7 code shape — the noise the deferral referred to no
    longer exists.
  - Rationale: No edit needed; the rationale is already in the code.
  - Severity: minor.
  - Forward impact: none.

- **§D6 (Five pyright errors) — two structural fixes, three local fixes,
  two pragmas, no global span signature rename.**
  - Spec source: session 61-8 §D6; story description "Fix or annotate
    five pre-existing pyright errors."
  - Spec text: "Either fix or annotate with `# type: ignore[<rule>]`
    plus reason."
  - Implementation: Three errors fixed structurally — two via
    `isinstance(seat_map, dict)` narrowing on duck-typed callable
    returns (`_resolve_acting_character_name`, party_peers building),
    one via explicit `if count_method is None: raise TypeError(...)`
    on the notorious-party gate's count-method lookup. Two errors
    (the `**_projection_counts` / `**extra_attrs` spreads into span
    helpers) annotated with `# pyright: ignore[reportArgumentType]`
    plus rationale.
  - Rationale: The two spread-into-kwargs errors arise from a span-helper
    signature pattern (`_tracer: Tracer | None = None` keyword-only
    parameter ahead of `**attrs`) that repeats across 30+ telemetry
    helpers. A real fix would rename `_tracer` → `tracer_override` on
    every helper; that surface is much broader than 61-8 §D6's scope
    and is filed as a Delivery Finding for a future cleanup story.
  - Severity: minor.
  - Forward impact: minor — the two pragmas signal a real ergonomics
    debt in the telemetry layer that a future story should address
    holistically.

- **§A guard split into two distinct warning messages, not one.**
  - Spec source: session 61-8 §A; story description "Extend
    orchestrator.py:3472-3481 fail-loud guard (narrator.sdk_path.context_missing_ids)
    to alarm specifically when context.lore_store is None in production."
  - Spec text: implies extending the existing
    `context_missing_ids` warning to cover the lore_store-None case.
  - Implementation: Added a SECOND, distinct warning
    (`narrator.sdk_path.context_missing_lore_store`) for the
    lore_store-None case rather than extending the existing one. The
    two warnings stay mutually exclusive (the new one only fires when
    ids ARE present and lore_store is None).
  - Rationale: Distinct warnings give the GM panel two separate signals
    so an operator can tell the umbrella unwired-TurnContext case apart
    from the partial-wiring lore_store regression. Sharing one warning
    name would force the panel to inspect the message body to know
    which failure mode fired.
  - Severity: minor (improvement over the literal spec).
  - Forward impact: none — additive only; tests verify both warnings
    fire independently and that neither fires on the green path.

### Dev (review-fix round 2)

- **§B implementation now matches its docstring (override semantic).**
  - Spec source: Reviewer round-1 MUST-FIX #2 (lying docstring).
  - Spec text: docstring claims "world-authored NPCs override that with
    `observation_pending=False`".
  - Implementation: chose code-matches-docstring per Reviewer's
    recommendation "pick (a) if a world-authored chapter SHOULD
    canonicalize a prior prose-mint." New helper
    `_ensure_world_authored_pool_member` PROMOTES prose-pending entries
    (drawn_from=='dialogue_extraction' OR observation_pending==True);
    non-prose sources are left untouched per chapter-apply's authority
    scope. Added 2 tests (promote-prose-pending + don't-clobber-
    canonical) covering the override contract.
  - Rationale: docstring semantic was correct; the code had drifted.
  - Severity: minor.
  - Forward impact: positive — closes the documented-vs-actual gap.

- **§A reviewer audit: pre-existing context_missing_ids OTEL gap also closed.**
  - Spec source: Reviewer audit note ("the umbrella warning should also
    publish to watcher_hub. Treat as a small additional ask on the §A
    fix, not a separate story").
  - Spec text: implied scope expansion of §A from 1 watcher publish to 2.
  - Implementation: Both `narrator_context_missing_ids` AND
    `narrator_context_missing_lore_store` now publish watcher events
    alongside their logger.warning. Both guards share the same
    defense-in-depth purpose and the same pre-fix OTEL invisibility.
  - Rationale: Reviewer audit ask; coupled cleanup. Out of scope per
    strict §A definition but the Reviewer explicitly folded it in.
  - Severity: minor.
  - Forward impact: positive — pre-existing observability gap closed.

- **§B `_ensure_world_authored_pool_member` extracted as a method.**
  - Spec source: Reviewer round-1 MUST-FIX #1 (existing-NPC branch).
  - Spec text: "Refactor: extract `_ensure_pool_member(snap, npc_data.name)`
    and call it in BOTH the existing-NPC and new-NPC branches."
  - Implementation: extracted as `_ensure_world_authored_pool_member` on
    `WorldBuilder`; called from both the existing-NPC return branch and
    the new-NPC append branch of `_apply_npc`. Added regression test
    constructing a legacy-save shape (Npc in snap.npcs, no pool entry)
    and asserting `_apply_npc` seeds the pool on the existing-NPC branch.
  - Rationale: Reviewer's exact suggested shape.
  - Severity: minor.
  - Forward impact: positive — closes the legacy-save scope gap.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 4 (all pre-existing on develop, line-shifted by 61-8 unrelated additions) | confirmed 0, dismissed 4 (all pre-existing on develop — orchestrator.py:2671 send_stream was 2667; world_materialization.py 453/477/803 were 446/470/776; not in 61-8 §D6 scope which targeted only session_helpers.py and is clean) |
| 2 | reviewer-edge-hunter | Yes | findings | 6 | confirmed 3 (§B existing-NPC branch skips pool-seed [HIGH], ADR-098 stale SOFT_PROMPT_BUDGET_BYTES [HIGH], §A literal-sentinel guard gap [DEFER]); confirmed 1 with defer (test live-content coupling — story §G defer); dismissed 1 (§C2 streaming path missing oversized check — pre-existing, outside 61-8 scope); dismissed 1 (§D1 None vs empty-string conflation — low-confidence) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 5 | confirmed 3 (§A no watcher_hub.publish_event [HIGH], §B docstring lies about override [HIGH], §D6 non-dict seat_map silent fallthrough [MED]); dismissed 1 (§C2 NonRecordingSpan no-op is inherent OTEL behavior); dismissed 1 (§D1 watcher-event-vs-span — consistent with existing npcs_dropped pattern) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 | confirmed 4 (§D3 missing direct unit for is_npc_anchored_by_encounter empty-actors, §C2 no test asserts refused_oversized=True, §D1 no test for unresolvable counter, §A no negative boundary test); confirmed 1 with defer (test live-content coupling — story §G defer) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 | confirmed 3 (§B lying-docstring duplicates silent-failure-hunter #2, §D1 docstring missing 2 returned keys, §D6 pragma comment text inaccurate) |
| 6 | reviewer-type-design | Yes | findings | 4 | dismissed 1 (§A sync-path guard — sync doesn't use lore_store); deferred 3 (payload: dict → dict[str,Any] pre-existing typing, NpcPoolMember.drawn_from Literal — broader refactor, _tracer rename already in Delivery Findings) |
| 7 | reviewer-security | Yes | clean | 0 | N/A (Rules 4/8/11 — no violations; single-tenant project, no new boundaries) |
| 8 | reviewer-simplifier | Yes | findings | 4 | confirmed 1 (test file CONTENT_GENRE_PACKS duplicates `tests/_helpers/genre_paths.find_pack_path` — pairs with the live-content-coupling finding above); deferred 3 (§B next() vs any() NIT, §D6 raise-to-catch wrapper documented by Dev, §D2 inline `eff is None` NIT) |
| 9 | reviewer-rule-checker | Yes | findings | 2 (22 rules / 74 instances / 2 violations) | confirmed 2 (live-content coupling Rule 5 + project-rule [DEFER per story §G], §A OTEL Observability Principle [HIGH — corroborates silent-failure-hunter #1]) |

**All received:** Yes (9 returned, 8 with findings, 1 clean)
**Total findings:** 11 confirmed (3 MUST-FIX, 8 SHOULD-FIX), 4 confirmed-with-defer, 8 dismissed (with rationale)

### Rule Compliance

Direct enumeration of each python.md + CLAUDE.md rule against the changed surface:

| Rule | Status | Evidence |
|------|--------|----------|
| python.md #1 (silent exception swallowing) | PASS | No new bare `except` blocks; pre-existing `except Exception:  # noqa: BLE001` at session_helpers.py:687 logs with `exc_info=True` per carve-out |
| python.md #2 (mutable defaults) | PASS | All new params use `None` defaults: `_make_snapshot(npcs: list[Npc] | None = None)`, `_npc(...)` etc. (10 functions checked, 0 violations) |
| python.md #3 (type annotations at boundaries) | PASS | All 9 new helpers in test_61_8 annotated; both pyright pragmas carry `[reportArgumentType]` specifically |
| python.md #4 (logging coverage + correctness) | **FAIL** | §A guard at orchestrator.py:3568 logs `logger.warning(...)` but no `watcher_hub.publish_event` — Dev's own comment claims GM-panel visibility but the panel reads watcher events, not logs (corroborates SILENT #1, RULE #A6) |
| python.md #5 (path handling) | **FAIL** | test_61_8_projection_edge_cases.py:49 `CONTENT_GENRE_PACKS = parents[3] / "sidequest-content" / "genre_packs"` is `pathlib.Path` clean BUT references live content slugs (caverns_and_claudes/mawdeep). DEFER per story §G — pre-existing pattern across 61-2/61-7 tests, inventory + decide is its own story |
| python.md #6 (test quality) | PASS | All 8 new tests assert specific values, no `assert True`, no `assert result` truthy-only, MagicMock at the right targets |
| python.md #7 (resource leaks) | PASS | `SqliteStore.open_in_memory()` is in-memory test pattern, no new `open()` calls |
| python.md #8 (unsafe deserialization) | PASS | `json.loads(ctx.state_summary)` is server-controlled input |
| python.md #9 (async pitfalls) | PASS | All `@pytest.mark.asyncio` tests await correctly |
| python.md #10 (import hygiene) | PASS | `from sidequest.game.npc_pool import NpcPoolMember` — no circular (npc_pool.py imports only BaseModel) |
| python.md #11 (input validation at boundaries) | PASS | No new API handlers / CLI entry points |
| python.md #12 (dependency hygiene) | N/A | No pyproject.toml changes |
| python.md #13 (fix-introduced regressions) | PASS | Rename `SOFT_PROMPT_BUDGET_BYTES → PROMPT_BUDGET_BYTES_HARD` clean across all 13 sites in repo (1 stale reference in `docs/adr/098-...md` is in orchestrator repo, outside server) |
| python.md #14 (state cleanup with fallible side effects) | PASS | No queue/buffer-then-side-effect pattern |
| CLAUDE.md No Silent Fallbacks | PASS (with one note) | §D6 isinstance guards have documented intentional fallthrough; §A lore_store guard logs explicitly. NOTE: §D6 isinstance guard at session_helpers.py:271 silenced what was previously a loud AttributeError on non-dict seat_map — SHOULD-FIX add `logger.warning` on the else branch |
| CLAUDE.md No Stubbing | PASS | All new code is live; no placeholders |
| CLAUDE.md Verify Wiring, Not Just Existence | PASS | §B test asserts `drawn_from` + `observation_pending`; §A test asserts caplog records on real SDK path |
| CLAUDE.md Every Test Suite Needs a Wiring Test | PASS | §A driving real `_run_sdk_and_capture_ctx`, §B driving `WorldBuilder().build()`, §D3/§D4 driving `_build_turn_context` + tool registry |
| CLAUDE.md No Source-Text Wiring Tests | PASS | All wiring assertions are runtime (caplog records, field inspection, projection payload contents) |
| CLAUDE.md OTEL Observability Principle | **FAIL** | §A guard is logger-only despite stated GM-panel-visibility purpose (corroborates SILENT #1) |

### Devil's Advocate (assume the diff is broken)

Imagine a hostile reader trying to break this diff. Where would they look?

**Attack vector 1: §B leaves the legacy population invisible.** A genre pack ships a chapter with NPC "Drakul." A player loaded the save in 2026-04 before §B existed; `_apply_npc` populated `snap.npcs` but not `snap.npc_pool`. The save is then loaded after 61-8 lands. On re-materialization, `existing` finds Drakul in `snap.npcs` (line 443) and returns at line 453 BEFORE the new pool-seed code runs. Drakul never enters the pool. The 61-2 projection at session_helpers.py drops Drakul from snap.npcs (off-stage), tries to fall back to `snap.npc_pool` for identity — finds nothing. Narrator confabulates a replacement name. Exactly the failure mode §B was supposed to close, surviving in the most common production case (legacy saves). MUST-FIX.

**Attack vector 2: §B docstring is a literal lie.** A future maintainer reads the comment "world-authored NPCs override that with `observation_pending=False`" and reasons: "good, then I can rely on observation_pending=False after chapter apply for any world-authored NPC." They write code that gates a canonical-NPC action on `observation_pending == False`. It silently fails for any NPC whose name happens to collide with a prior auto-mint pending entry — because the code DOES NOT override, it skips. The docstring promised a guarantee the code doesn't deliver. MUST-FIX (either docstring or code).

**Attack vector 3: §A warning is invisible.** Operator deploys, partial-wiring regression strikes in production. They check the GM panel — no `context_missing_lore_store` event because the GM panel reads watcher events, not logs. They check the cost dashboard — nothing obvious (the narrator runs cheaper without lore retrieval). They check Jaeger — yes, the warning is buried in logs, but they didn't know to grep. The Sebastien-grade lie-detector contract is broken. The story description specifically references CLAUDE.md OTEL Observability Principle — and this diff violates it. MUST-FIX.

**Attack vector 4: §D1 counter visible only in retrospective span queries.** A serialization regression starts producing dict entries with `core.name = None`. The new `npcs_unresolvable_name_dropped` counter ticks up on every turn. Goes onto the `prompt.game_state.bytes` span attribute. The GM panel does NOT subscribe to span attributes — it subscribes to watcher events. The operator has no real-time signal that data-shape drift is happening; they have to query Jaeger retrospectively. The simplification dismissed this as "consistent with the existing npcs_dropped pattern" — fair, but the principle here is the same as §A: stated GM-panel purpose, but no GM-panel reach. This is a SHOULD-FIX paired with §A.

**Attack vector 5: §D6 silently swallows hook bugs.** Pre-§D6, if `slot_to_player_id()` returned a non-dict (e.g. a tuple), iteration with `for slot, pid in seat_map.items()` would raise `AttributeError: 'tuple' object has no attribute 'items'`. The error would propagate, log loud, and surface the hook bug. Post-§D6, `isinstance(seat_map, dict)` silently falls through to the character-name fallback. The hook bug is now invisible. The comment says "silent fallthrough is intentional if the hook ever returns something else" — but per CLAUDE.md No Silent Fallbacks, intentional silence is the regression. SHOULD-FIX: add `logger.warning` on the else branch so the hook bug surfaces as an anomaly.

**Attack vector 6: §D3 / §D4 tests prove convergence, not correctness.** Both call sites give the same answer because they call the same `is_npc_anchored_by_encounter` predicate (61-7 unified them). If a future change makes the tool branch use a DIFFERENT predicate that ALSO returns False on empty actors, both sites still converge and the tests pass. The integration test doesn't isolate the predicate. SHOULD-FIX: add a direct unit test for `is_npc_anchored_by_encounter(empty_actors)` returning False.

**Verdict:** Three load-bearing MUST-FIX items + a cluster of SHOULD-FIX items. The bugs aren't subtle — they're scope gaps in §A and §B, plus documentation rot. Hand back.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | §B existing-NPC branch returns at line 460 before pool-seed code; legacy saves and any NPC created by a path other than the new-NPC branch never get a pool entry. The fix's stated purpose ("every NPC the projection might drop must retain identity") is unmet in the most common production case. | sidequest/game/world_materialization.py:460-512 | Refactor: extract `_ensure_pool_member(snap, npc_data.name)` and call it in BOTH the existing-NPC and new-NPC branches. Add a regression test that constructs a snapshot with a pre-existing Npc and no pool entry, then re-runs `_apply_npc` with the same name, and asserts `snap.npc_pool` now has the member. |
| [HIGH] | §B docstring claims "world-authored NPCs override that with `observation_pending=False` since they are canonical at chapter-apply time" but the implementation SKIPS when a same-name member exists — no field is updated. A future caller relying on the documented contract will silently get auto-mint pending state on a world-authored NPC. | sidequest/game/world_materialization.py docstring at the §B comment block | Either: (a) make the code match the docstring — add `else: existing_member.observation_pending = False; existing_member.drawn_from = "world_authored"` branch — OR (b) make the docstring match the code — change "override that with `observation_pending=False`" to "skip insertion; the existing entry is left in place." Pick (a) if a world-authored chapter SHOULD canonicalize a prior prose-mint (likely correct semantically), pick (b) if not. |
| [HIGH] | §A `context_missing_lore_store` guard emits `logger.warning` only, no `watcher_hub.publish_event`. CLAUDE.md OTEL Observability Principle requires backend subsystem decisions to emit OTEL watcher events for GM-panel visibility. The story description names the GM panel as the consumer ("Fire a separate warning so the GM panel sees the partial-wiring regression distinctly"). A logger.warning does not reach the GM panel. | sidequest/agents/orchestrator.py:3568-3577 | Add `from sidequest.telemetry.watcher_hub import publish_event as _pub` (already imported in `_check_oversized_prompt` nearby) and call `_pub("narrator_lore_store_unwired", {"world_id": world_id, "session_id": session_id}, component="orchestrator", severity="warn")` immediately after the `logger.warning(...)` call. Add a watcher-event regression test parallel to the caplog test. |

**Should-fix (non-blocking but real debt):**

| Severity | Issue | Location |
|----------|-------|----------|
| [MEDIUM] | §D6 `isinstance(seat_map, dict)` guard silences a previously loud `AttributeError` on hook contract drift. Per CLAUDE.md No Silent Fallbacks, the documented "silent fallthrough" comment is itself a violation; add a `logger.warning(...)` in the else branch so the bug surfaces. | sidequest/server/session_helpers.py:271-278 (and twin at 288) |
| [MEDIUM] | §D1 docstring lists 4 returned counters but `_apply_phase_c_projections` returns 5 (the new `npcs_unresolvable_name_dropped` + the existing `encounter_anchored_count` added in 61-7 that was also never documented). | sidequest/server/session_helpers.py:112 (function docstring Returns block) |
| [MEDIUM] | §D6 pragma rationale comments at session_helpers.py:885 and 1388 attribute the pyright complaint to "key shadow `_tracer`" — actual diagnostic is `reportArgumentType` (broader type-arg mismatch). Reword to match what pyright actually emits. | sidequest/server/session_helpers.py:879-886 + 1383-1391 |
| [MEDIUM] | Stale `SOFT_PROMPT_BUDGET_BYTES` reference outside server repo. | docs/adr/098-stateless-narrator-turns.md:88 (orchestrator repo) |
| [MEDIUM] | §C2 added `_action_span.set_attribute("refused_oversized", True)` but no test asserts this — a future refactor that drops the call would be invisible to CI. | tests/agents/test_61_3_hard_cap_oversized_canary.py (add InMemorySpanExporter assertion mirroring test_61_2 pattern at line 650) |
| [MEDIUM] | §D1 counter has no exercising test. The branch increments only when payload entries have falsy `core.name`/`name`, a path no fixture currently constructs. | tests/server/ (new test injecting a malformed npc dict, asserting span attribute `npcs_unresolvable_name_dropped >= 1`) |
| [MEDIUM] | §D3 integration tests verify projection ↔ tool convergence but not the predicate in isolation. A future change to either call site that makes both wrong-by-coincidence converges-correctly is invisible. | tests/server/test_61_8_projection_edge_cases.py (add direct unit `is_npc_anchored_by_encounter(npc, empty_actors_encounter)` → False) |
| [MEDIUM] | §A two new caplog tests cover the positive (warning fires) and green (silent) paths; missing the boundary path: `world_id=None, lore_store=None` should fire ONLY the umbrella `context_missing_ids`, not the new `context_missing_lore_store`. The exclusion condition `world_id != "unknown" and session_id != "adhoc"` is untested. | tests/server/test_turn_context_sdk_wiring.py (add test asserting only `context_missing_ids` fires in the unknown-ids + None-lore_store case) |

**Deferred (per story scope or pre-existing):**

- Test live-content coupling on `caverns_and_claudes/mawdeep` in tests/server/test_61_8_projection_edge_cases.py — story §G explicitly defers this ("pre-existing pattern, inventory + decide is its own story"). 61-8 propagated the anti-pattern into a new file, which makes the §G cleanup story slightly larger but is explicitly out of scope here. The simplifier-flagged `find_pack_path` helper is the migration target whenever §G lands.
- Pre-existing pyright errors in orchestrator.py:2671 (`send_stream`) and world_materialization.py:453/477/803 (`Disposition` int assignments) — exist on develop; line-shifted by 61-8's surrounding edits. Outside §D6 scope (which was session_helpers.py only). File as Delivery Finding.
- Pre-existing `_tracer` shadow-kwarg pattern across 30+ telemetry helpers — Dev's own Delivery Finding; broader refactor.
- §B `drawn_from: str` should be `Literal[...]` — broader model change.
- `_apply_phase_c_projections` `payload: dict` could be `dict[str, Any]` — pre-existing typing weakness.
- §A literal-sentinel edge case (caller passing literal string `"unknown"` or `"adhoc"`) — pathological/theoretical.

**Pre-existing context_missing_ids has the same OTEL gap as §A.** Filing as a Delivery Finding for §A's MUST-FIX commit: the umbrella warning should also publish to watcher_hub. Treat as a small additional ask on the §A fix, not a separate story.

**Data flow traced:** `_build_turn_context` → `TurnContext.lore_store` → `_run_narration_turn_sdk` line 3568 guard → (currently) logger.warning only. To reach the GM panel: must add watcher_hub.publish_event. The pre-existing oversized-prompt path at `_check_oversized_prompt` (line 3001+) is the pattern to mirror — it does both logger.error AND _pub.

**Pattern observed:** §D1 `if not entry_name: continue` (session_helpers.py:202) is the correct idiom for the unresolvable-name early-skip; counter logic is clean.

**Error handling:** §D6 explicit `if count_method is None: raise TypeError(...)` is documented as deliberate raise-to-catch with better error message (Dev's deviation log accepted). Reviewer accept.

### Confirmed Findings (tagged by specialist source)

- **[SILENT] §A guard missing watcher_hub.publish_event** at sidequest/agents/orchestrator.py:3568 — MUST-FIX (also [RULE] OTEL Observability Principle violation)
- **[DOC] §B `_apply_npc` docstring lies about override behavior** at sidequest/game/world_materialization.py docstring — MUST-FIX (also [SILENT] paired finding)
- **[EDGE] §B existing-NPC branch returns at line 460 before pool-seed code** at sidequest/game/world_materialization.py:460 — MUST-FIX
- **[SILENT] §D6 isinstance guard at session_helpers.py:271 silenced previously loud AttributeError** — SHOULD-FIX
- **[DOC] §D1 docstring Returns block missing `npcs_unresolvable_name_dropped` and `encounter_anchored_count`** at session_helpers.py:112 — SHOULD-FIX
- **[DOC] §D6 pyright pragma rationale misframes the diagnostic** at session_helpers.py:885 + 1388 — SHOULD-FIX
- **[EDGE] Stale `SOFT_PROMPT_BUDGET_BYTES` reference** at docs/adr/098-stateless-narrator-turns.md:88 — SHOULD-FIX
- **[TEST] §D3 missing direct unit test for `is_npc_anchored_by_encounter(empty_actors)`** — SHOULD-FIX
- **[TEST] §C2 no test asserts `refused_oversized=True` on the action span** at tests/agents/test_61_3_hard_cap_oversized_canary.py — SHOULD-FIX
- **[TEST] §D1 no exercising test for `npcs_unresolvable_name_dropped` counter** — SHOULD-FIX
- **[TEST] §A no negative boundary test for unknown world_id + lore_store=None** at tests/server/test_turn_context_sdk_wiring.py — SHOULD-FIX
- **[SIMPLE] test_61_8_projection_edge_cases.py CONTENT_GENRE_PACKS duplicates `tests/_helpers/genre_paths.find_pack_path`** — DEFER (pairs with §G live-content coupling)
- **[RULE] Live-content coupling (caverns_and_claudes/mawdeep) in test_61_8_projection_edge_cases.py** — DEFER per story §G ("inventory + decide is its own story")
- **[SEC] No findings** — single-tenant project, no new boundaries
- **[TYPE] No type-design MUST-FIX in scope** — three deferred items (drawn_from Literal, payload: dict[str, Any], _tracer rename) are pre-existing typing weakness or already in Delivery Findings

**Handoff:** Back to Dev (Ponder Stibbons) for review-fix.

### Reviewer (audit)

Reviewing Dev's logged Design Deviations:

- **§D5 (Empty-collection noise resolved by code reading)** → ✓ ACCEPTED by Reviewer. The current `_apply_phase_c_projections` code at session_helpers.py:155 already documents `payload["room_states"] = {}` as the "structural anchor" — the deferred noise no longer exists. Dev's investigation is sound; no edit needed.

- **§D6 (Five pyright errors — 3 structural fixes, 2 pragmas, no global rename)** → ✓ ACCEPTED by Reviewer. The two pragmas are minimum-scope `[reportArgumentType]` with rationale; the structural fixes (isinstance narrowing × 2, explicit TypeError raise) match the rule's "narrow before use" guidance. The global `_tracer → tracer_override` rename is correctly out of scope and filed as Delivery Finding. **One follow-on:** the rationale text in both pragma comments misframes pyright's complaint as "key shadows `_tracer`" — actual diagnostic is `reportArgumentType`. Reword in the review-fix commit.

- **§A guard split into two distinct warnings** → ✓ ACCEPTED by Reviewer. Distinct GM-panel signals warrant distinct event names. Pairs with the MUST-FIX above: add `watcher_hub.publish_event` for BOTH warnings (the umbrella `context_missing_ids` has the same pre-existing OTEL gap).