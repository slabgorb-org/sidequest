---
story_id: "151-4"
jira_key: ""
epic: "151"
workflow: "tdd"
---
# Story 151-4: [NARRATOR] Sidecar cutover I — transactional fields (items×4, gold, companions×2) off game_patch to the extractor (ADR-150 step 4)

## Story Details
- **ID:** 151-4
- **Jira Key:** (none — no_jira project)
- **Workflow:** tdd
- **Repos:** server
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T04:20:05Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T03:09:43+00:00 | 2026-06-19T03:09:43+00:00 | 0m |
| red | 2026-06-19T03:09:43+00:00 | 2026-06-19T03:38:46Z | 29m 3s |
| green | 2026-06-19T03:38:46Z | 2026-06-19T04:00:54Z | 22m 8s |
| review | 2026-06-19T04:00:54Z | 2026-06-19T04:14:06Z | 13m 12s |
| green | 2026-06-19T04:14:06Z | 2026-06-19T04:17:16Z | 3m 10s |
| review | 2026-06-19T04:17:16Z | 2026-06-19T04:20:05Z | 2m 49s |
| finish | 2026-06-19T04:20:05Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### TEA (test design)
- **Gap** (blocking): the WS handler must MOVE the extractor call before apply and call the merge seam.
  `run_sidecar_extraction_watcher` currently runs at `websocket_session_handler.py:1223` — AFTER
  `_apply_narration_result_to_snapshot` at `:1145`. The cutover needs the order: extractor → capture its
  `SidecarExtraction` → `merge_sidecar_extraction_transactional(result, extraction)` → apply. The wiring test
  (`test_merge_seam_wired_into_session_handler`) only asserts the import is present (reflection, per CLAUDE.md);
  Dev must guarantee the call ordering. Affects `sidequest/server/websocket_session_handler.py` (relocate + merge call).
  *Found by TEA during test design.*
- **Question** (non-blocking): retiring the 7 fields at `extract_structured_from_response` also strips them from
  `game_patch_dict` (orchestrator.py:3545 feeds both). If forensics/cost auditing needs the raw transactional
  fields on `game_patch_dict`, move the retirement to `_build_shared_result_kwargs` (orchestrator.py:3635-3644)
  and retarget `test_extract_structured_retires_transactional_field_from_game_patch` accordingly. Affects
  `sidequest/agents/orchestrator.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the design keeps `_apply_narration_result_to_snapshot` UNCHANGED, so the existing
  apply-mechanics suites (`test_gold_change_apply`, `test_companion_recruit_apply`,
  `test_mp_item_recipient_attribution`) must stay GREEN with zero edits. If Dev finds one breaking, the
  implementation has drifted from the pinned "apply untouched, merge upstream" design — re-check before editing
  those tests. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): the pre-existing integration baseline is large (~73 failures in
  `tests/integration/`) and entirely WWN-combat / spell / chargen / lore (epic-108 de-nativization,
  e.g. `no_strike_beat`, missing `cast_spell` beat) plus hermeticity (`build_async_anthropic`, real-SDK
  transport). Root-caused each blast-radius candidate: `test_106_4_item_use_beat` fails on
  `dice.opponent_reprisal_skipped reason=no_strike_beat` (combat content, not the items_consumed change).
  This story adds ZERO new failures — my additions are exception-wrapped (`run_sidecar_extraction_watcher`
  catches all → returns None) and None-guarded (merge only runs when extraction present), so they cannot
  raise into the turn. *Found by Dev during implementation.*
- **Question** (non-blocking, RESOLVED): TEA's `game_patch_dict` forensics concern does not apply — the
  retirement is in `extract_structured_from_response` (the narrator-result mapper), while `game_patch_dict`
  is built from the SEPARATE `_extract_game_patch_json` (orchestrator.py:3545), untouched. Raw transactional
  fields remain available for forensics/cost auditing. *Found by Dev during implementation.*
- **Improvement** (non-blocking): for 151-5, extend `merge_sidecar_extraction_transactional` to also source
  `npcs_present` enrichment + the cosmetic fields (mood/visual_scene/footnotes) at the same pre-apply seam,
  and remove their retired keys from `extract_structured_from_response` + `output_only.md`. The seam and the
  extractor-runs-before-apply ordering are now in place. *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking, for 151-7 validation gate): the extractor path is now load-bearing, but the
  "extractor exhausted retries → transactional merge skipped this turn" decision has no dedicated turn-level
  OTEL span — only the per-attempt `sidecar_extraction.failed` ERROR spans fire (failure IS loud, but the
  GM panel cannot cleanly distinguish "extractor failed → fields empty" from "genuinely empty turn"). Add a
  `sidecar_extraction.merge_skipped` (or reuse the crashed-span with `reason="exhausted_retries"`) before the
  `return None` in `run_sidecar_extraction_watcher`. Corroborated by silent-failure + security subagents.
  Affects `sidequest/agents/sidecar_extractor.py` / `sidequest/server/websocket_session_handler.py`.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, 151-2 model hardening): `SidecarExtraction` (151-2) uses Pydantic v2 default
  `extra="ignore"`, so off-schema Haiku keys are silently dropped — safe (no propagation) but No-Silent-Fallbacks
  prefers loud. Add `model_config = {"extra": "forbid"}` (matches `advance_confrontation.py` etc.); the existing
  schema_invalid retry/fail path then handles divergence loudly. Affects `sidequest/agents/sidecar_extractor.py`.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking, 151-5 territory): moving the extractor BEFORE apply changes the
  `sidecar_extraction.mismatch` (npcs_present) timing — it now checks the extractor's NPCs against the
  pre-apply (router-seated) cast, so a narrator-improvised NPC not yet auto-minted fires a mismatch span where
  post-apply it would not. Observability-only (applies nothing); npcs_present is 151-5. 151-5 should reconcile
  the mismatch semantics. Affects `sidequest/agents/sidecar_extractor.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, LOW): the empty-narration cost gate (`run_sidecar_extraction_watcher`, returns
  None on whitespace-only narration) emits only `logger.debug` and no span — now load-bearing (no transactional
  apply on that turn). Low risk (no prose ⇒ no transaction to apply). Consider `logger.info` + a skipped span.
  *Found by Reviewer during code review.*
- No new upstream findings during re-review (R1) — the delta was test-only; production code unchanged.
  *Found by Reviewer during re-review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **Pinned a dedicated merge seam instead of threading the extraction into the apply**
  - Spec source: context-story-151-4.md, "Technical Guardrails" / AC2
  - Spec text: "wire the `narration_apply` consumers to read the **extractor output** instead of the `game_patch` sidecar"
  - Implementation: pinned a NEW function `narration_apply.merge_sidecar_extraction_transactional(result, extraction)` that copies the 7 transactional fields from the `SidecarExtraction` onto the `NarrationTurnResult` post-narration, leaving `_apply_narration_result_to_snapshot` UNCHANGED — rather than adding a `sidecar_extraction` parameter to the apply and re-sourcing its sub-blocks.
  - Rationale: mirrors the established sibling cutover 151-3 (retire-at-parse-boundary + source-from-new-producer, apply untouched). Keeping the apply unchanged means the ~14 existing apply-mechanics tests (`test_gold_change_apply`, `test_companion_recruit_apply`, `test_mp_item_recipient_attribution`) stay valid with zero churn, and the recipient-resolution / gold-clamp / companion-dedup / catch-loop machinery is reused verbatim (Don't Reinvent). The extractor is post-narration so its output isn't available at result-assembly (unlike 151-3's pre-narrator action_rewrite), forcing the merge to be a distinct pre-apply step rather than an assembler edit.
  - Severity: minor
  - Forward impact: 151-5 (npcs_present + cosmetic) should extend the SAME merge seam for its fields; the seam name is now load-bearing for the epic.
- **Pinned the retirement at `extract_structured_from_response` (the parse boundary)**
  - Spec source: ADR-150 §Testing strategy; context-story-151-4.md AC3
  - Spec text: "A retirement guard asserts `narration_apply` no longer reads the migrated field from the `game_patch` sidecar once its cutover lands."
  - Implementation: the retirement guard asserts `extract_structured_from_response` no longer surfaces the 7 fields out of the game_patch — the exact function (and shape) where 151-3 retired `action_rewrite`.
  - Rationale: this is the single parse boundary where the game_patch becomes the structured result; retiring here makes the field provably never reach `narration_apply` from the sidecar, satisfying the guard behaviourally (no source grep). Consistent with the in-epic precedent.
  - Severity: minor
  - Forward impact: see Delivery Finding re: `game_patch_dict` forensics — Dev may need to move the retirement to `_build_shared_result_kwargs` if the raw forensic dict must keep the fields.
- **AC1 (extractor produces the fields) is not re-tested here — only scope-locked**
  - Spec source: context-story-151-4.md AC1
  - Spec text: "Extracted: the 151-2 extractor produces the field from synthetic prose."
  - Implementation: AC1 is already GREEN via Story 151-2's `tests/agents/test_sidecar_extractor.py` (the extractor produces all 11 bucket-B fields incl. these 7). This file adds only a scope-lock (`test_transactional_fields_are_a_subset_of_bucket_b`) tying the cutover's 7 fields to the canonical `BUCKET_B_FIELDS`.
  - Rationale: re-testing extractor production would duplicate 151-2 and couple two stories' suites; the scope-lock catches field-name drift cheaply.
  - Severity: minor
  - Forward impact: none.

### Dev (implementation)
- **Updated four existing tests that pinned the pre-cutover game_patch-sourcing contract**
  - Spec source: ADR-150 §Decision (transactional fields move producer); TEA tests in `test_151_4_sidecar_cutover_transactional.py`
  - Spec text: "moving a field from narrator-emitted to extractor-derived should not run both producers in parallel … each field migrates in one change"
  - Implementation: inverted `test_orchestrator.py::test_extract_structured_extracts_items_gained` → `…no_longer_surfaces_items_gained`, `…extracts_gold_change` → `…no_longer_surfaces_gold_change`, `test_run_narration_turn_extracts_items_gained` → `…no_longer_surfaces_items_gained_from_game_patch`; converted `test_61_12_output_format_compaction.py::test_items_fields_all_still_named` → `…retired_from_narrator_output` and REMOVED `test_items_fields_block_compacted` (its measured block no longer exists); flipped one assertion in `test_narrator_sdk_hybrid_split.py::test_assemble_turn_result_still_applies_sidecar_on_non_sdk_path` (`gold_change == -19` → `is None`).
  - Rationale: these pinned the OLD contract (game_patch surfaces the transactional fields + output_only.md instructs them), which the cutover deliberately retires. Mirrors exactly how 151-3 inverted `test_extract_structured_extracts_action_rewrite` → `…no_longer_surfaces_action_rewrite` in the same file. The apply-mechanics suites stayed untouched and green (TEA's "apply unchanged" design held).
  - Severity: minor
  - Forward impact: none — the new contract is now pinned by both `test_151_4_*` and these inverted tests.
- **Retired by surfacing EMPTY (keys kept), not by dropping the keys**
  - Spec source: TEA deviation "Pinned the retirement at `extract_structured_from_response`"
  - Spec text: retirement guard asserts the 7 fields are not surfaced
  - Implementation: set the 7 fields to `[]` / `None` in the `extract_structured_from_response` return (keys present) rather than deleting them, so the shared assembler `_build_shared_result_kwargs`'s subscript access (`extraction["items_gained"]`, `extraction["gold_change"]`) stays safe with no further edit.
  - Rationale: minimal change; satisfies the retirement guard (`not surfaced`) while preserving the downstream subscript contract.
  - Severity: trivial
  - Forward impact: none. Resolves TEA's `game_patch_dict` Question finding — forensics use the SEPARATE `_extract_game_patch_json` (orchestrator.py:3545), which I did NOT touch, so the raw transactional fields are preserved on `game_patch_dict`.

### Reviewer (audit)
- **TEA — Pinned a dedicated merge seam instead of threading into the apply** → ✓ ACCEPTED: sound; mirrors the 151-3 cutover shape, reuses the apply machinery verbatim, and keeps the ~14 existing apply suites green (verified — `test_gold_change_apply`/`test_companion_recruit_apply`/`test_mp_item_recipient_attribution` all pass unchanged).
- **TEA — Pinned the retirement at `extract_structured_from_response`** → ✓ ACCEPTED: same function where 151-3 retired `action_rewrite`; the parse-boundary retirement makes the field provably never reach apply from the game_patch.
- **TEA — AC1 not re-tested, only scope-locked** → ✓ ACCEPTED: AC1 is GREEN via 151-2's suite; the scope-lock test guards field-name drift cheaply. No duplication.
- **Dev — Updated four existing tests to the retirement contract** → ✓ ACCEPTED: correct test-contract evolution; mirrors 151-3's `action_rewrite` test inversion exactly. The inverted assertions are behaviourally meaningful (assert empty on values verified non-empty pre-cutover). Removing the now-moot `test_items_fields_block_compacted` is correct — its measured block no longer exists.
- **Dev — Retired by surfacing EMPTY (keys kept), not dropping keys** → ✓ ACCEPTED: necessary for the shared assembler's subscript access (`extraction["items_gained"]`, `extraction["gold_change"]`); confirmed `game_patch_dict` forensics unaffected (separate `_extract_game_patch_json`).

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5-pt cutover story changing observable behaviour (transactional sidecar fields move
producer); fixture-based RED tests per ADR-150 §Testing strategy.

**Test Files:**
- `tests/server/test_151_4_sidecar_cutover_transactional.py` — 22 tests (19 RED, 3 green-staying
  scope guards), driving the REAL `extract_structured_from_response`, `merge_sidecar_extraction_transactional`
  (the pinned new seam), and `_apply_narration_result_to_snapshot` with synthetic
  `SidecarExtraction` / `NarrationTurnResult` / game_patch fixtures. No live content.

**Tests Written:** 22 tests covering the 6 ACs.
**Status:** RED (19 failing — ready for Dev). Verified via targeted run (`pytest <file>`), NOT the
testing-runner (project memory: it cache-clobbers the live session file). Lint + format: clean.

RED breakdown (all failing for the correct, intended reason):
- 7 × `test_extract_structured_retires_transactional_field_from_game_patch[*]` — **AssertionError**
  (field still surfaced; retirement not yet done). AC3.
- 1 × `test_output_only_md_no_longer_instructs_transactional_fields` — **AssertionError** (instructions
  still present). AC3.
- 11 × merge/apply/attribution/catch-loop/wiring — **ImportError** on `merge_sidecar_extraction_transactional`
  (seam not built). AC2/AC4/AC5 + wiring.

Green-staying scope guards (PASS now, lock the 151-4↔151-5 boundary):
- `test_transactional_fields_are_a_subset_of_bucket_b`
- `test_extract_structured_keeps_deferred_bucket_b_fields` (npcs_present/scene_mood still flow)
- `test_output_only_md_keeps_deferred_field_instructions`

Harness soundness verified out-of-band (simulated post-merge by setting `result` fields directly and
driving the real apply): gold purse 50→31 + 1 `economy.gold_change`; single + multi-recipient items land on
the named seated PC (Red→Ritali, Blue→Catalina); companion recruit + `recruited_by` + `party.recruit`;
unmatched discard → 1 `inventory.narrator_extracted` span with `unmatched_discards_count=1`. Companion-dedup
path mirrors the already-passing `test_companion_recruit_apply.py::test_duplicate_recruit_is_silent_no_op`.
So once the merge seam + retirement + output_only.md edits land, the 19 RED tests go GREEN.

### AC → test map
| AC | Coverage |
|----|----------|
| AC1 Extracted | Pre-covered by 151-2 `test_sidecar_extractor.py`; scope-locked here (deviation logged) |
| AC2 Applied from extractor | `test_merge_copies_all_seven…`, `…overwrites_stale_result_fields_no_fallback`, 3× `test_extraction_<field>_applied_via_merge_then_apply` |
| AC3 Retired | 7× parametrized parse-boundary retirement + `test_output_only_md_no_longer_instructs_transactional_fields` (+ 2 scope guards) |
| AC4 Loud net intact | `test_extraction_unmatched_discard_fires_catch_loop_span`, `test_extraction_duplicate_companion_fires_dedup_catch_loop` |
| AC5 Attribution preserved | `test_merge_preserves_item_recipient_attribution`, `…multi_recipient_item_split`, `…companion_recruited_by_attribution` |
| AC6 Full suite green | Design keeps apply UNCHANGED → existing apply suites stay valid (see Delivery Finding) |

### Rule Coverage (python.md / CLAUDE.md)
| Rule | Test(s) | Status |
|------|---------|--------|
| Every Test Suite Needs a Wiring Test (+ No Source-Text grep) | `test_merge_seam_wired_into_session_handler` (reflection on `wsh.__dict__`) | RED |
| No Silent Fallbacks (#1) | `test_merge_overwrites_stale_result_fields_no_fallback` (empty extraction overwrites, no fallback) | RED |
| OTEL Observability (#4) | `test_extraction_unmatched_discard_fires_catch_loop_span` (span asserted) | RED |
| Test quality (#6) — no vacuous asserts | self-check: every test asserts a specific value/span attr; the only truthy-style check (`assert not surfaced`) is on a value verified non-empty pre-cutover | pass |
**Rules checked:** 4 of the applicable lang-review rules have explicit test coverage (the rest target
implementation Dev writes — re-checked at verify).
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Inigo Montoya) for implementation — build the merge seam, retire the parse boundary +
output_only.md, relocate the extractor + call the merge in the WS handler (see Delivery Findings).

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (sidequest-server):**
- `sidequest/server/narration_apply.py` — new `merge_sidecar_extraction_transactional(result, extraction)`
  seam (copies the 7 transactional fields from `SidecarExtraction` onto `NarrationTurnResult`; extraction is
  the sole source, overwrite-not-merge); `NarrationTurnResult` + `SidecarExtraction` added to TYPE_CHECKING.
- `sidequest/agents/orchestrator.py` — `extract_structured_from_response` retires the 7 transactional fields
  (surfaced empty; keys kept for the shared assembler's subscript safety). Forensic `game_patch_dict`
  untouched (separate `_extract_game_patch_json`).
- `sidequest/agents/narrator_prompts/output_only.md` — removed the items/gold/companions instruction block
  (npcs_present + cosmetic fields retained for 151-5).
- `sidequest/server/websocket_session_handler.py` — imported the merge seam; moved
  `run_sidecar_extraction_watcher` to run BEFORE `_apply_narration_result_to_snapshot`, merging its output
  onto the result; removed the old post-apply shadow pass.
- Tests updated to the retirement contract (deviation logged): `tests/agents/test_orchestrator.py` (3),
  `tests/agents/test_61_12_output_format_compaction.py` (1 inverted + 1 removed),
  `tests/agents/test_narrator_sdk_hybrid_split.py` (1 assertion).

**Tests:** GREEN.
- 22/22 in `test_151_4_sidecar_cutover_transactional.py` pass.
- 188/188 across the full blast radius (151-4 + orchestrator + 61-12 + sdk-hybrid + sidecar_extractor +
  151-1 + action_rewrite + the 3 existing apply suites) pass — run serially (`-n0`) to avoid an xdist
  thread-shutdown flake.
- `ruff check` + `ruff format --check`: clean on all 7 changed files.

**Regression check (AC6):** No new failures attributable to this story. The pre-existing baseline is the
epic-108 WWN-combat de-nativization (`no_strike_beat` / missing `cast_spell` beat) + hermeticity
(`build_async_anthropic`, real-SDK transport) — all in subsystems this story does not touch. Each
blast-radius candidate root-caused to a combat-content or test-fixture cause, never the transactional fields
(e.g. `test_106_4_item_use_beat` → `dice.opponent_reprisal_skipped reason=no_strike_beat`). One server test
(`test_102_5 … production_dispatch`) was an xdist flake — passes serially.

**Self-review (judgment checks):**
- [x] Wired end-to-end: the WS handler runs the extractor before apply and calls the merge; the apply
  consumes the now-extractor-sourced fields through unchanged machinery.
- [x] Follows project patterns: mirrors the 151-3 cutover shape exactly (same epic).
- [x] All ACs met (see TEA AC→test map; all green).
- [x] No silent fallbacks: extractor failure → None → merge skipped → transactional fields stay empty (loud
  span), never a fall-back to the retired game_patch.

**Handoff:** To Reviewer (Westley) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (136/136 tests green; 0 new smells; ruff clean) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — self-checked (dice-replay double-apply, empty/None extraction) |
| 3 | reviewer-silent-failure-hunter | Yes | findings | 3 | confirmed 3 (all non-blocking), dismissed 0, deferred 3 → Delivery Findings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled — self-checked (no vacuous asserts; dead `_item` helper found) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled — self-checked (docstrings/comments accurate) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled — self-checked (merge annotations, gold int\|None) |
| 7 | reviewer-security | Yes | findings | 2 | confirmed 2 (non-blocking), dismissed 0, deferred 2 → Delivery Findings; firewall CLEAN |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled — self-checked (found dead `_item` helper) |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled — self-did Rule Compliance (python.md) below |

**All received:** Yes (3 enabled returned; 6 disabled via settings, self-checked their domains)
**Total findings:** 1 blocking ([SIMPLE] dead code), 5 confirmed non-blocking (observability), dismissed 0

## Reviewer Assessment

**Verdict:** REJECTED

The cutover is correct and the load-bearing security check is clean — but a dead test helper this PR introduced must not merge (project doctrine: *delete dead code in the same PR*, an explicitly-corrected recurring failure). Single, trivial green-rework fix.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [LOW][SIMPLE] | Dead `_item` helper — defined, zero callers (the item tests use inline dicts) | `tests/server/test_151_4_sidecar_cutover_transactional.py:126-136` | Remove the unused `_item` helper. (LOW on the severity scale, but the explicit "delete dead code in the same PR" rule makes it a required pre-merge fix → green-rework.) |

**Why only green-rework (not red):** the sole required fix is dead-code removal (no failing-test logic). The five observability findings below are confirmed valid but **non-blocking** and routed to follow-up stories (151-5 / 151-7) — see Delivery Findings.

### Rule Compliance (python.md — enumerated over the diff)
- **#1 Silent exception swallowing:** `merge_sidecar_extraction_transactional` has no try/except — `[VERIFIED]` no swallow. Handler `if sidecar_extraction is not None:` is a guard, not a swallow; the watcher's failure path fires ERROR log + per-attempt `sidecar_extraction.failed` spans (`sidecar_extractor.py:231,339`) — failure is loud. The *aggregate* merge-skip span is a non-blocking gap (Delivery Finding). **Compliant** (with a noted refinement).
- **#2 Mutable default args:** merge fn + retirement edits have no default args. **Compliant.**
- **#3 Type annotations at boundaries:** `merge_sidecar_extraction_transactional(result: NarrationTurnResult, extraction: SidecarExtraction) -> NarrationTurnResult` fully annotated; types added to the TYPE_CHECKING block (narration_apply.py:19-20). **Compliant.**
- **#4 Logging coverage/correctness:** no new error paths in the diff's production edits that lack logging. **Compliant.**
- **#6 Test quality:** all 22 new tests assert specific values/span attrs (no vacuous `assert True`/bare-truthy) — the only `assert not surfaced` is on values verified non-empty pre-cutover. **VIOLATION (test hygiene): dead `_item` helper** (the blocking finding). Otherwise compliant.
- **#8 Unsafe deserialization:** `SidecarExtraction.model_validate` (Pydantic v2) — no pickle/eval/yaml. **Compliant** (note: `extra="ignore"` default → hardening Delivery Finding).
- **#9 Async pitfalls:** `await run_sidecar_extraction_watcher(...)` correctly awaited before the merge/apply; the watcher is a coroutine. **Compliant.**
- **#10 Import hygiene:** TYPE_CHECKING imports for annotations; no star imports/cycles. **Compliant.**

### Observations (all 8 dispatch tags)
- `[SIMPLE]` Dead `_item` helper at `test_151_4_sidecar_cutover_transactional.py:126` — confirmed zero callers (`grep` shows only the def). **Blocking (doctrine).**
- `[SILENT]` Merge-skip on extractor-None has no aggregate OTEL span — confirmed by silent-failure-hunter; **non-blocking** (per-attempt fail spans + ERROR log already make failure loud). → 151-7.
- `[SEC]` `SidecarExtraction` lacks `extra="forbid"` (151-2 model) — off-schema keys silently dropped (safe, no propagation); **non-blocking** hardening. → follow-up. Perception firewall **CLEAN**: `[VERIFIED]` the extractor receives only `result.narration` = scrubbed public prose (`_scrub_public_prose` at orchestrator.py:1337); `private_prose_segments` is never read by the extractor and untouched by the merge (security subagent traced this end-to-end).
- `[TYPE]` (self-checked, subagent disabled) `gold_change: int | None` copied verbatim by the merge; `list(...)` shallow-copies (dicts shared, but the extraction is discarded post-merge — no aliasing hazard). `[VERIFIED]` `NarrationTurnResult` is a non-frozen dataclass so field assignment works.
- `[EDGE]` (self-checked) dice-replay re-entry (`_execute_narration_turn` at :3509, `suppress_intent_router=True`) re-runs the extractor+merge+apply — but this is a **faithful source-swap**: the pre-151-4 game_patch path also applied on both passes, and the 151-2 shadow extractor already ran on both. No *new* double-apply introduced. `[VERIFIED]` apply's `is_dice_replay` gate (narration_apply.py:5152) only skips the NPC-mention sub-block, not items/gold/companions — unchanged by this story.
- `[EDGE]` npcs_present mismatch-span now fires pre-apply (narrator-improvised NPCs) — observability-only, 151-5 territory. Non-blocking.
- `[TEST]` (self-checked) wiring test is reflection-based (`merge_... in wsh.__dict__`) — proves import, not call-ordering. Acceptable (the behavioral merge→apply tests prove the mechanism; full-turn ordering is verified by code review). `[VERIFIED]` ordering correct at websocket_session_handler.py:1159-1166 (extractor → merge → apply).
- `[DOC]` (self-checked) docstrings + the handler comment accurately describe the cutover; the "loud span fired" phrase is technically the per-attempt fail span (precise enough). No stale docs.
- `[RULE]` (self-did, rule-checker disabled) python.md enumeration above — one violation (#6 test hygiene / dead code), rest compliant.

**Data flow traced:** narrator prose → `extract_structured_from_response` (7 transactional fields retired → empty) → `result` → (post-narration) `run_sidecar_extraction_watcher` reads scrubbed prose → `SidecarExtraction` → `merge_sidecar_extraction_transactional` overwrites the 7 fields on `result` → `_apply_narration_result_to_snapshot` applies via unchanged recipient/gold/companion machinery. Safe because: the game_patch is provably dead (retirement test), the extraction is the sole source (overwrite test), attribution dicts are copied verbatim (recipient/recruited_by tests), and private prose never enters the extractor (firewall verified).

### Devil's Advocate
Assume this is broken. **Attack 1 — double application on dice turns.** The extractor now runs inside `_execute_narration_turn`, which the dice-replay re-enters with `suppress_intent_router=True`. If the replay narration re-describes "you pocket the ring," the extractor re-extracts it and the merge+apply re-applies → a duplicate ring. *Verdict:* real risk, but **pre-existing** — the old game_patch path applied on both passes too, and the apply's `is_dice_replay` gate (unchanged) doesn't gate item/gold/companion lanes. This story is a faithful 1:1 source-swap; it neither introduces nor worsens the double-apply window. Flagged for 151-7's playtest gate, not this story. **Attack 2 — the extractor is the single point of failure for ALL transactional state.** A persistently-failing Haiku extractor means items/gold/companions silently stop applying. *Verdict:* failure is loud (ERROR log + `sidecar_extraction.failed` spans), and ADR-150 explicitly accepts "catch-loops are the net." The missing aggregate merge-skip span (Delivery Finding) would sharpen the signal but failure is not silent. **Attack 3 — perception leak.** Could a private per-PC segment ride the extractor into a public field? *Verdict:* No — verified the extractor receives scrubbed public prose only; `private_prose_segments` is set separately at assembly and never touched. **Attack 4 — a confused narrator still emits items_gained in the game_patch.** *Verdict:* silently dropped at retirement (by design, mirrors 151-3 action_rewrite); the extractor re-derives from prose. If BOTH the narrator emits it AND the extractor fails, the item is lost with only the fail spans as signal — an accepted ADR-150 trade-off, sharpened by the deferred detection-span Delivery Finding. **Attack 5 — empty/degraded narration.** A stall-phrase turn skips the extractor (cost gate) → no transactional apply. *Verdict:* correct (no prose ⇒ no transaction); low risk. None of these rise to Critical/High; the firewall — the one that could have — is clean.

**Handoff:** Back to Dev for the dead-code removal (green-rework).

## Dev Rework (R1)

**Reviewer finding addressed:** [LOW][SIMPLE] dead `_item` helper.
**Change:** removed the unused `_item` helper AND the related unused `items=` param on the `_pc`/`_core`
fixtures (no test pre-loads a PC with items — the item tests build `SidecarExtraction` dicts inline). Test-only
diff (`-18/+3`); production code untouched.
**Verify:** 22/22 `test_151_4_sidecar_cutover_transactional.py` green (serial); `ruff check` + `format --check`
clean. Commit `73667ea1`, pushed.
**Non-blocking findings (Reviewer):** left as Delivery Findings for follow-up (merge-skip span → 151-7;
`extra="forbid"` → 151-2 hardening; npcs_present mismatch timing → 151-5; empty-narration span → LOW). Not
in scope for this rework per the Reviewer's routing.

**Handoff:** To Reviewer (Westley) for re-review.

## Subagent Results

_(Re-review, Round-Trip 1. Delta since R0 review = commit `73667ea1`, TEST-ONLY: `-18/+3` in
`test_151_4_sidecar_cutover_transactional.py`. Production code byte-identical to R0 — verified via
`git diff 4c97268f...HEAD --name-only` = single test file.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (22/22 green; dead `_item` gone; ruff clean) | confirmed 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled — N/A (production unchanged) |
| 3 | reviewer-silent-failure-hunter | Yes | carried-forward | 3 (R0) | All non-blocking (R0) — production unchanged; still Delivery Findings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Self-checked: blocking dead-code finding RESOLVED |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled — N/A |
| 6 | reviewer-type-design | No | Skipped | disabled | Self-checked: production unchanged |
| 7 | reviewer-security | Yes | carried-forward | 2 (R0) | Non-blocking (R0) — production unchanged; firewall CLEAN; still Delivery Findings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Self-checked: dead `_item` helper + unused `items=` param REMOVED |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Self-did Rule Compliance in R0 (python.md); production unchanged |

**All received:** Yes (preflight re-run on the new commit; silent-failure + security carried forward — production code byte-identical, so their R0 analysis stands)
**Total findings:** 0 blocking (the R0 dead-code blocker is RESOLVED), 5 confirmed non-blocking (unchanged, Delivery Findings)

## Reviewer Assessment

**Verdict:** APPROVED

The Round-Trip 0 blocking finding — `[SIMPLE]` dead `_item` helper — is resolved: `git diff 4c97268f...HEAD`
is a single test-only file (`-18/+3`), the helper and its related unused `items=` param are gone (`grep "def _item"`
= no match), and `test_151_4_sidecar_cutover_transactional.py` is 22/22 green with ruff clean. Production code
is **byte-identical** to the R0 review, whose substantive findings stand:

- `[SEC]` **Perception firewall (ADR-105) CLEAN** — `[VERIFIED]` the extractor receives only `result.narration`
  = scrubbed public prose (`_scrub_public_prose`, orchestrator.py:1337); `private_prose_segments` is never read
  by the extractor and untouched by the merge.
- `[SILENT]` Merge has no silent fallback — `[VERIFIED]` `merge_sidecar_extraction_transactional` overwrites
  unconditionally; extractor failure is loud (ERROR log + `sidecar_extraction.failed` spans); the missing
  aggregate merge-skip span is a confirmed **non-blocking** Delivery Finding (→ 151-7).
- `[SIMPLE]` Dead-code blocker **RESOLVED** this round.
- `[TYPE]` Merge annotations correct; `gold_change: int|None` copied verbatim; no aliasing hazard (extraction
  discarded post-merge). `[EDGE]` dice-replay re-entry is a faithful source-swap (no new double-apply).
  `[TEST]` reflection wiring test + behavioral merge→apply tests; ordering verified by code review.
  `[DOC]` docstrings/comments accurate. `[RULE]` python.md compliant (the one R0 violation — test hygiene /
  dead code — is now fixed).

**Data flow traced (R0, still valid):** narrator prose → `extract_structured_from_response` (7 fields retired
→ empty) → `result` → post-narration extractor (scrubbed prose) → `SidecarExtraction` → merge overwrites →
`_apply_narration_result_to_snapshot` via unchanged recipient/gold/companion machinery. Safe.

**Pattern observed:** faithful mirror of the 151-3 cutover (retire-at-parse-boundary + source-from-new-producer,
apply untouched) at `orchestrator.py:1342` / `narration_apply.py:3601` / `websocket_session_handler.py:1159`.

**Error handling:** extractor failure → None → merge skipped (loud per-attempt spans), never a game_patch
fallback — `narration_apply.py` + `websocket_session_handler.py:1164`.

**Handoff:** To SM for finish-story.