---
story_id: "158-4"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 158-4: NPC roster place-name leak — narrator NpcMention place-names register as NPCs (Torchdeep/Torchhold)

## Story Details
- **ID:** 158-4
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server
- **Type:** bug
- **Points:** 3
- **Priority:** p2

## Summary

Narrator-invented dwarfhold place names (`Torchdeep`, `Torchhold`) are getting registered into `snapshot.npcs` as phantom NPCs with `disp=0` and `creature_id=None`. These are NOT camp NPCs and have no creature backing — they are narrator-invented place names that appeared in prose.

**Critical scoping facts (driver-established):**
- These place names are NOT in any beneath_sunden content file (full grep is empty) — they are narrator-invented
- A content place-name guard / known-location skip-set will NOT catch them — they are not known locations
- This is NOT a content fix; the auto-mint path (`session_helpers._auto_mint_prose_only_npcs`) is honorific/role-keyed and would NOT mint a bare "Torchdeep"
- The leak is most likely in the narrator's structured **NpcMention** emission reconciling into `snapshot.npcs` — the narrator listed a place as an NPC in its `narrate` tool call
- The principled fix is at the **tool-contract / mention-reconcile layer**, not content
- The bug is INTERMITTENT (generation-variance) — RED cannot rely on a live playtest repro; the failing test must be a deterministic unit/integration test

## Suggested Investigation Seams

Search in sidequest-server:
- `NpcMention` tool-call handling
- `_auto_mint_prose_only_npcs` in session_helpers.py
- NPC reconcile into snapshot in narration_apply.py / session_helpers.py

The fix likely needs a **place-vs-person discriminator** at the mention-reconcile layer.

## Acceptance Criteria

1. **AC1:** A deterministic unit/integration test exists that feeds a known place-name NpcMention through the reconcile path and asserts it does NOT land in `snapshot.npcs` (covers the intermittent generation-variance issue with a deterministic fixture)
2. **AC2:** The mention-reconcile layer (tool-contract point) discriminates places from persons and rejects place-only mentions before snapshot registration
3. **AC3:** An OTEL watcher event is emitted when a mention is rejected/classified as a place so the GM panel can verify the guard fired (per project OTEL observability doctrine)
4. **AC4:** Beneath_sunden playtest re-verify shows no phantom place-name NPCs in the roster (coverage of the original symptom under real play)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-23T04:36:14Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| red | 2026-06-23T03:54:01+00:00 | 2026-06-23T04:09:01Z | 15m |
| green | 2026-06-23T04:09:01Z | 2026-06-23T04:17:52Z | 8m 51s |
| review | 2026-06-23T04:17:52Z | 2026-06-23T04:25:45Z | 7m 53s |
| red | 2026-06-23T04:25:45Z | 2026-06-23T04:29:05Z | 3m 20s |
| green | 2026-06-23T04:29:05Z | 2026-06-23T04:31:09Z | 2m 4s |
| review | 2026-06-23T04:31:09Z | 2026-06-23T04:36:14Z | 5m 5s |
| finish | 2026-06-23T04:36:14Z | - | - |
| green | - | 2026-06-23T04:17:52Z | unknown |
| review | 2026-06-23T04:17:52Z | 2026-06-23T04:25:45Z | 7m 53s |
| red | 2026-06-23T04:25:45Z | 2026-06-23T04:29:05Z | 3m 20s |
| green | 2026-06-23T04:29:05Z | 2026-06-23T04:31:09Z | 2m 4s |
| review | 2026-06-23T04:31:09Z | 2026-06-23T04:36:14Z | 5m 5s |
| finish | 2026-06-23T04:36:14Z | - | - |
| review | - | 2026-06-23T04:25:45Z | unknown |
| red | 2026-06-23T04:25:45Z | 2026-06-23T04:29:05Z | 3m 20s |
| green | 2026-06-23T04:29:05Z | 2026-06-23T04:31:09Z | 2m 4s |
| review | 2026-06-23T04:31:09Z | 2026-06-23T04:36:14Z | 5m 5s |
| finish | 2026-06-23T04:36:14Z | - | - |
| finish | - | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

### TEA (test design)
- **Gap** (blocking): The Step-3 reconcile place-guard is necessary but NOT sufficient — something must SET `NpcMention.is_place=True` for a narrator-invented place, or the guard never fires in production (Verify Wiring, Not Just Existence). `npcs_present` is sourced from the post-narration extractor via `merge_sidecar_extraction_npcs_present` (ADR-150). Affects the producer seam in `sidequest/server/narration_apply.py` (`merge_sidecar_extraction_npcs_present` / `SidecarExtraction`) and the extractor's classification schema/prompt. Dev must wire the producer to classify places AND confirm that producer is server-side (in scope) vs daemon-side (scope question — story is `repos: server` only). *Found by TEA during test design.*
- **Improvement** (non-blocking): Step 3 now has three sibling decline-guards (creature 2974, epithet 3003, and the new place guard). Consider whether the place check belongs at the top of the mention loop (a place should never match/update an existing `Npc` in Step 1 either) rather than only in the Step-3 novel branch. The RED tests assert end-behavior (not minted + span) and are location-agnostic, so either placement passes. Affects `_apply_npc_mentions` in `narration_apply.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Resolved** (was TEA's blocking Gap): The producer is now wired — `sidecar_extractor.py` `npcs_present` gained a `WithJsonSchema` per-mention schema (mirroring `_ITEMS_GAINED_ITEM_SCHEMA`) documenting `is_place`, plus a tool-description instruction telling the post-narration reader to flag a location proper-noun. The extractor IS server-side (in scope), so no scope expansion. `from_value` (orchestrator.py:3728 path) carries the flag through to `_apply_npc_mentions`. Full pipeline connected; no half-wired feature. *Found by Dev during implementation.*
- **Improvement** (non-blocking): Place classification now depends on the Haiku sidecar extractor honoring the new `is_place` schema/prompt — the same LLM-judgment reliability profile as the existing `is_creature` flag (neither is deterministically unit-testable; both rely on the reader following the schema). AC4's live beneath_sunden re-verify is the production confirmation that the extractor flags Torchdeep-class names. Affects `sidequest/agents/sidecar_extractor.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Gap** (blocking): `detect_sidecar_extraction_mismatch` is `is_place`-blind, so a correctly-declined place fires a false-positive `sidecar_extraction.mismatch` span (LIVE via `websocket_session_handler.py:1189`) — completing the `is_place` flag's wiring across all three `npcs_present` consumers is required (No Half-Wired Features). Affects `sidequest/agents/sidecar_extractor.py:384` (skip `is_place` entries before the `name not in known` check; add a regression test asserting no mismatch span fires for an `is_place` entry). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): consider whether `from_value` should treat a non-bool/falsy `is_place` value loudly rather than silently coercing to False (low risk — tool schema constrains to boolean). Affects `sidequest/agents/orchestrator.py:462`. *Found by Reviewer during code review.*
- RT1 re-review: No new upstream findings. The RT0 blocking finding is resolved (mismatch witness now skips is_place; regression-tested). *Found by Reviewer during code review (RT1).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

### TEA (test design)
- **AC4 (live beneath_sunden re-verify) has no automated test**
  - Spec source: context-story-158-4.md / SM Assessment, AC4
  - Spec text: "Beneath_sunden playtest re-verify shows no phantom place-name NPCs in the roster (coverage of the original symptom under real play)"
  - Implementation: AC4 is covered out-of-band by the DRIVER (manual live descent). The deterministic reconcile-guard tests in `tests/server/test_158_4_place_name_leak.py` drive the real production seam `_apply_npc_mentions` as the automated proxy for the symptom.
  - Rationale: AC1 explicitly precludes a deterministic live-play repro — the leak is generation-variance and was not reproduced on the last two playtest draws. An automated live-play test would be flaky/non-deterministic, violating AC1's own constraint.
  - Severity: minor
  - Forward impact: DRIVER must manually re-verify on a live beneath_sunden descent post-merge; no code impact.
- **Test encodes `is_place` (bool flag) + `npc.place_skipped` span as the concrete discriminator/contract**
  - Spec source: context-story-158-4.md / SM Assessment, AC2 + AC3
  - Spec text: "The mention-reconcile layer (tool-contract point) discriminates places from persons and rejects place-only mentions" / "An OTEL watcher event is emitted when a mention is rejected/classified as a place"
  - Implementation: RED pins a specific contract — `NpcMention.is_place: bool = False` (parallel to `is_creature`), parsed by `from_value`, plus a Step-3 guard emitting `npc.place_skipped` — rather than leaving the discriminator abstract.
  - Rationale: A bare proper-noun place is structurally indistinguishable from a person name, and DRIVER confirmed the names are not in content, so a heuristic / known-location skip-set cannot catch them. A producer-set flag (the exact mechanism `is_creature` already uses) is the only reliable discriminator.
  - Severity: minor
  - Forward impact: Dev MAY rename the field/span but MUST preserve the behavioral + OTEL assertions, AND must wire the producer to set the flag (see Delivery Findings — blocking Gap).

### Dev (implementation)
- No deviations from spec. Implemented the contract TEA pinned exactly (`is_place` field + `from_value`, the decline guard, the `npc.place_skipped` span), and additionally wired the producer (extractor `npcs_present` schema/prompt) per AC2 ("discriminates places from persons") + TEA's blocking Delivery Finding + the No-Half-Wired-Features rule — completion of scope, not a deviation. Guard placed at the mention-loop top per TEA's non-blocking Improvement finding (a place should never touch `npcs`/pool at all); the location-agnostic RED tests pass either way.

### Reviewer (audit)
- **TEA: "AC4 has no automated test"** → ✓ ACCEPTED by Reviewer: sound — AC1 explicitly precludes a deterministic live-play repro (generation-variance); out-of-band DRIVER GM-panel verify is the correct coverage. (Caveat: that verify is undermined by the false-positive mismatch finding below — fixing it protects AC4.)
- **TEA: "Test encodes is_place + npc.place_skipped as the discriminator"** → ✓ ACCEPTED by Reviewer: the flag mirrors the existing `is_creature` precedent exactly; a string/known-location heuristic provably cannot distinguish a place from a person name, so a producer-set flag is the only reliable discriminator. Faithful realization of AC2/AC3.
- **Dev: "No deviations; producer wiring is scope completion; guard at loop-top"** → ✓ ACCEPTED by Reviewer (placement + producer-wiring intent) — BUT see the UNDOCUMENTED gap below: the producer-wiring claim ("full pipeline connected; no half-wired feature") is **incomplete**.
- **UNDOCUMENTED (Reviewer):** Spec/rule said wire the `is_place` flag across the pipeline (No Half-Wired Features). Code wires it into `from_value` + the reconcile guard but NOT into the third `npcs_present` consumer, `detect_sidecar_extraction_mismatch` (sidecar_extractor.py:384), which now emits a false-positive `sidecar_extraction.mismatch` for correctly-declined places. Not documented by Dev. Severity: M (blocking for rework — rule-matching). → ✗ FLAGGED (see Reviewer Assessment).
  - → ✓ RESOLVED (Reviewer RT1): fixed in commit `d2920c82` — the mismatch witness now skips `is_place` entries; regression-tested (`0f3e9066`). All three `npcs_present` consumers read the flag. The flag is no longer half-wired.

## Sm Assessment

**Routing:** Phased `tdd` workflow → handing off to **TEA (Fezzik)** for the RED phase. Setup complete: session file, context doc (`sprint/context/context-story-158-4.md`), and server branch `feat/158-4-npc-place-name-leak` (off `develop`) all verified present. Merge gate clear at setup (0 open server PRs, 0 in-progress stories). No Jira (project tracks via sprint YAML).

**Scope guard — this story is ONLY sub-bug (b).** Sub-bug (a) (authoring the camp roster: Brecca Half-Hand et al.) is already FIXED + DRIVER-VERIFIED via content #495 and server #1051/#1052. Do not touch the authored-roster path. 158-4 = the place-name LEAK only.

**The one-line bug:** narrator-invented place names (`Torchdeep`/`Torchhold`) reconcile into `snapshot.npcs` as phantom NPCs (`disp=0`, `creature_id=None`). They are NOT in any content file — content guards won't catch them. Fix site is the **mention-reconcile / tool-contract layer**, not content, and not (per DRIVER) the honorific-keyed `_auto_mint_prose_only_npcs` auto-mint path.

**Key RED-phase risk (call this out, Fezzik):** the bug is INTERMITTENT — generation variance, NOT reproduced on the last two playtest draws. So RED CANNOT lean on a live playtest repro. The failing test must be a **deterministic unit/integration test** that drives a known place-name NpcMention through the reconcile path and asserts it does NOT land in `snapshot.npcs`. Build the fixture; don't wait for a lucky draw.

**OTEL is an AC, not optional (AC3):** per project doctrine the guard must emit a watcher event when a mention is rejected/classified as a place, so the GM panel can confirm it fired. RED should pin that span too — a green guard with no OTEL is a half-fix.

**Investigation seams for RED to confirm (do not pre-decide the fix):** `NpcMention` tool-call handling, npc reconcile into snapshot in `session_helpers.py` / `narration_apply.py`. Likely needs a place-vs-person discriminator at the reconcile point.

Fezzik — write the failing test, watch it fail, then hand to Inigo. The four ACs are in the context above.

---
## TEA Assessment

**Tests Required:** Yes
**Reason:** Behavioral bug fix at a real production seam — needs RED coverage of the reconcile guard + OTEL contract.

**Test Files:**
- `sidequest-server/tests/server/test_158_4_place_name_leak.py` — drives the real `_apply_npc_mentions` seam with synthetic `NpcMention`s (no LLM); mirrors the `test_126_32_narrated_npc_binding.py` doctrine (behavior + OTEL-by-string-literal).

**Tests Written:** 6 (4 functions; 2 are parametrized over Torchdeep/Torchhold) covering AC1–AC3.
**Status:** RED (verified failing — see below)

### RED verification (testing-runner, RUN_ID 158-4-tea-red)
All 6 fail for the missing production change, not test defects:
- `test_place_mention_is_not_minted_as_npc[Torchdeep|Torchhold]` → `TypeError: NpcMention.__init__() got an unexpected keyword argument 'is_place'`
- `test_place_mention_emits_skip_span[Torchdeep|Torchhold]` → same TypeError
- `test_person_mention_still_mints_when_not_a_place` → same TypeError (negative/surgical-guard test; passes once the field exists and the guard is place-only)
- `test_npc_mention_from_value_parses_is_place` → `AttributeError: 'NpcMention' object has no attribute 'is_place'`

No typos / import errors / broken fixtures. Spans referenced by string literal (`"npc.place_skipped"`) so a constant rename fails behaviorally, not at collection.

### Root cause (mapped, for Dev)
`_apply_npc_mentions` Step-3 novel branch (`sidequest/server/narration_apply.py:2965-3170`) declines the namer for `is_creature` (2974, `npc.creature_preserved`) and descriptive epithets (3003, `npc.epithet_preserved`), but a bare proper-noun PLACE is neither → falls to the `else` person branch (3066) → minted as `NpcPoolMember(drawn_from="narrator_invented")` at 3151-3170 → later promoted into `snapshot.npcs` (disp=0, creature_id=None).

### Suggested fix shape (Dev has latitude; preserve the assertions)
1. Add `is_place: bool = False` to `NpcMention` (`agents/orchestrator.py:391`, parallel to `is_creature`); parse it in `NpcMention.from_value` (dict branch, ~448).
2. Add a Step-3 PLACE guard that DECLINES the mint entirely (no pool member, no Npc) when `mention.is_place`, mirroring the creature/epithet guards.
3. Add `SPAN_NPC_PLACE_SKIPPED = "npc.place_skipped"` + `npc_place_skipped_span(npc_name, turn_number)` in `telemetry/spans/npc.py` (twin of `npc_creature_preserved_span`), and emit it from the guard.
4. **Wire the producer** (blocking Delivery Finding): ensure the narrator emission / post-narration extractor (`merge_sidecar_extraction_npcs_present` / `SidecarExtraction`) actually SETS `is_place` for place mentions — a guard with no producer is a half-fix.

### Rule Coverage

| Rule (python lang-review) | Test(s) | Status |
|------|---------|--------|
| #6 test quality — no vacuous assertions | all 6 assert concrete values (`== []`, `is True`, `len == 1`, span `npc_name == place_name`) | self-checked clean |
| #6 test quality — guard doesn't over-fire | `test_person_mention_still_mints_when_not_a_place` | failing (RED) |
| OTEL doctrine — subsystem decision emits a span | `test_place_mention_emits_skip_span` (asserts `npc.place_skipped`) | failing (RED) |
| Wiring test — drives real production seam | all tests call the real `_apply_npc_mentions`; `from_value` parse-boundary pinned | failing (RED) |
| No Silent Fallbacks — flag defaults False, backward-compatible | `test_npc_mention_from_value_parses_is_place` (default + bare-string → False) | failing (RED) |

**Rules checked:** test-quality (#6) + OTEL doctrine + wiring (CLAUDE.md) — the applicable rules for a behavioral reconcile fix. Path/async/deserialization/etc. checks are N/A (no such code in the test).
**Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Inigo Montoya) for GREEN.

### Red Phase — Rework RT1 (Reviewer-rejected: mismatch false-positive)

**Finding addressed:** Reviewer's blocking Gap — `detect_sidecar_extraction_mismatch` is `is_place`-blind, so a correctly-declined place fires a false-positive `sidecar_extraction.mismatch` span (LIVE; pollutes the channel AC4 reads).

**Tests added (2):** `tests/agents/test_sidecar_extractor.py` (alongside the existing AC4 mismatch tests, reusing `_empty_emit`/`_snapshot`/`_make_mock_llm`/`otel_capture`):
- `test_no_mismatch_span_for_a_flagged_place` — a `{"name":"Torchdeep","is_place":True}` mention must emit NO `sidecar_extraction.mismatch` span.
- `test_mismatch_skip_is_surgical_place_skipped_person_still_flagged` — a place + an unseated person → exactly ONE mismatch (the person); proves the skip is surgical, not over-suppressing.

**RED verified** (testing-runner RUN_ID 158-4-tea-red-rt1): both fail for the production gap — test 1 sees 1 mismatch span (Torchdeep), test 2 sees 2 (Torchdeep + Mordecai). No fixture/import issues. Self-check: 0 vacuous assertions.

**Fix for Dev:** in `detect_sidecar_extraction_mismatch` (sidecar_extractor.py:384), skip entries with a truthy `is_place` before the `name not in known` check (e.g. `if isinstance(mention, dict) and mention.get("is_place"): continue`).

**Handoff:** To Dev (Inigo Montoya) for GREEN (RT1).

---
## Dev Assessment

**Implementation Complete:** Yes

**Files Changed (4 production, all sidequest-server):**
- `sidequest/agents/orchestrator.py` — `NpcMention.is_place: bool = False` (twin of `is_creature`) + `from_value` dict-branch parse.
- `sidequest/server/narration_apply.py` — `_apply_npc_mentions` declines an `is_place` mention at the mention-loop top (before any Step-1/2/3 store touch) and emits `npc_place_skipped_span`; added the span import.
- `sidequest/telemetry/spans/npc.py` — `SPAN_NPC_PLACE_SKIPPED = "npc.place_skipped"` + `SPAN_ROUTES` entry (component `npc_registry`, op `place_skipped`) + `npc_place_skipped_span` context manager. Auto-re-exported via `from .npc import *`.
- `sidequest/agents/sidecar_extractor.py` — **producer wiring**: `npcs_present` gains `WithJsonSchema(_NPCS_PRESENT_ITEM_SCHEMA)` documenting `is_place` + a tool-description instruction so the post-narration reader flags a location proper-noun out of the roster.

**Approach:** Added the `is_place` discriminator end-to-end (extractor schema/prompt → `from_value` → reconcile guard → OTEL span), mirroring the existing `is_creature` precedent at every seam. The guard sits at loop-top so a place never matches/updates an existing `Npc` nor mints — closing the phantom-roster leak (disp=0, creature_id=None). No native mechanic was tuned; this is a pure mention-reconcile gate.

**Tests:** 93/93 passing (GREEN) — testing-runner RUN_ID 158-4-dev-green.
- New: `tests/server/test_158_4_place_name_leak.py` — 6/6 (place declined ×2, skip-span ×2, surgical-guard negative, from_value parse).
- Regression-clean: sidecar extractor (21), 151-4/5/6 sidecar cutover (47), 126-32 npc binding (4), npc_wiring (5), routing-completeness (2 — new span routed). 0 skipped.
- Lint: `ruff check` clean; `ruff format --check` clean (5 files).

**Branch:** `feat/158-4-npc-place-name-leak` (pushed to origin).

**ACs:** AC1 ✅ (deterministic fixture tests), AC2 ✅ (discriminator at the tool-contract point — extractor schema + reconcile guard), AC3 ✅ (`npc.place_skipped` OTEL span + SPAN_ROUTES to GM panel), AC4 ⏳ (out-of-band DRIVER live beneath_sunden re-verify — see deviations; inherently non-deterministic per AC1).

**Handoff:** To Reviewer (Westley) for code review.

### Green Phase — Rework RT1 (Reviewer finding: mismatch false-positive)

**Fix:** `sidequest/agents/sidecar_extractor.py` `detect_sidecar_extraction_mismatch` — skip `is_place` entries (`if isinstance(mention, dict) and mention.get("is_place"): continue`) before the unseated-name check. Completes the `is_place` flag's wiring across all three `npcs_present` consumers (from_value + reconcile guard + mismatch witness). Matches the existing `isinstance(mention, dict)` guard style on the next line.

**Tests:** 55/55 passing (GREEN) — testing-runner RUN_ID 158-4-dev-green-rt1.
- Rework: `test_no_mismatch_span_for_a_flagged_place` ✅, `test_mismatch_skip_is_surgical_place_skipped_person_still_flagged` ✅.
- Pre-existing AC4 mismatch tests STILL pass (skip is surgical, lie-detector not neutered): `test_mismatch_span_fires_when_extractor_invents_an_npc` ✅, `test_no_mismatch_span_when_extraction_agrees_with_state` ✅.
- Regression-clean: full test_sidecar_extractor.py (23), test_158_4_place_name_leak.py (6), 151-5 cutover (24), routing-completeness (2). 0 skipped.
- Lint: `ruff check` clean; `ruff format --check` clean.

**Commit:** `d2920c82` (pushed). **Handoff:** To Reviewer (Westley) for re-review (RT1).

---
## Subagent Results

_(Current = Re-review RT1, on the incremental rework diff `9b4f842a...HEAD`. RT0 results in italics for history.)_

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 | N/A (RT1: 31/31 green, lint+format clean, scope confirmed additions-only, 0 smells) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Yes | clean | 0 | RT1 clean (symmetry of the two guards verified; tests pin the over-suppression boundary). _RT0: 3 findings → 1 confirmed (fixed), 2 dismissed._ |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings (test-quality assessed by Reviewer) |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (type design assessed by Reviewer) |
| 7 | reviewer-security | Yes | clean | 0 | RT1 clean (evade-the-lie-detector angle is self-defeating — is_place also declines from roster). _RT0: 1 LOW, dismissed._ |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings (rules assessed by Reviewer) |

**All received:** Yes (RT1: 3 enabled returned all-clean; 6 disabled pre-filled)
**Total findings:** RT1 — 0 new findings; the single RT0 blocking finding (mismatch false-positive) is RESOLVED (verified fixed + regression-tested)

### Rule Compliance

Enumerated against `python.md` lang-review + CLAUDE.md `<critical>` rules + OTEL doctrine:

- **OTEL Observability (CLAUDE.md):** `npc.place_skipped` span added + `SPAN_ROUTES` entry → routes to GM panel. ✓ for the guard. **✗ INCOMPLETE** — the sibling co-consumer `detect_sidecar_extraction_mismatch` emits a *false-positive* `sidecar_extraction.mismatch` for a correctly-declined place (see finding [SILENT]-1). The fix half-satisfies the doctrine: it adds a true span but pollutes another.
- **No Half-Wired Features / Verify Wiring (CLAUDE.md `<critical>`):** the `is_place` flag has THREE consumers of `npcs_present`: `from_value` (✓ orchestrator.py:462), the reconcile guard (✓ narration_apply.py:2575), and `detect_sidecar_extraction_mismatch` (✗ sidecar_extractor.py:384 — unaware of the flag). 2 of 3 wired → violation.
- **No Silent Fallbacks:** `is_place` defaults False with loud span on decline; no silent swallow on the guard path. ✓ (the default-False parse matches the `is_creature`/`disengaged` sibling convention — [SILENT]-2 LOW, dismissed).
- **python.md #6 test quality:** new tests assert concrete values (`== []`, `is True`, `len == 1`, span `npc_name == place_name`); includes a surgical-guard negative test + a parse-boundary test. No vacuous assertions. ✓
- **python.md #3 type annotations:** `is_place: bool = False` fully annotated; span helper fully typed. ✓
- **python.md #8 unsafe deserialization / #11 input validation:** new LLM-sourced flag is `bool()`-coerced; `additionalProperties:True` schema is guidance only, `from_value` reads named `.get()` keys. No injection surface. ✓
- **Bind-the-Ruleset (SOUL.md):** no native mechanic tuned; pure mention-reconcile gate. ✓

### Observations

- `[VERIFIED]` Call-site type contract safe — `_apply_npc_mentions(mentions=list(result.npcs_present))` at narration_apply.py:5743; `result.npcs_present` is always `list[NpcMention]` (built via `from_value` in merge_sidecar_extraction_npcs_present / orchestrator.py:3728), so `mention.is_place` (2575) cannot AttributeError. Matches the existing `mention.is_creature` direct-access convention.
- `[VERIFIED]` Guard placement at loop-top (narration_apply.py:2575, before Step-1 at 2594) — a true place never updates an existing Npc's last_seen nor mints. Matches TEA's design rationale; behavior-asserting tests pass.
- `[VERIFIED]` Hide-the-villain is bounded — encounter opponents are seated pre-narrator in `snapshot.encounter.actors` (a separate store, side-adjudicated in merge before the guard); a place-flagged mention cannot erase a seated opponent. Worst case = one-turn stale last_seen on a mis-flagged real NPC.
- `[SILENT][MEDIUM]` `detect_sidecar_extraction_mismatch` (sidecar_extractor.py:384) fires a false-positive `sidecar_extraction.mismatch` span for a correctly-flagged place — it has no `is_place` awareness. LIVE in production via websocket_session_handler.py:1189. Pollutes the lie-detector channel AC4's DRIVER verify reads. **Confirmed — blocking for rework.**
- `[SEC][LOW]` Adversarial narration could set is_place=true on a real opponent's re-mention, skipping its one-turn last_seen/dev-tick update (not a removal; cannot change side or disable combat). Non-exploitable; same trust profile as is_creature. Dismissed (noted).
- `[SILENT][LOW]` `from_value` defaults is_place=False (orchestrator.py:462) — a falsy LLM value (`0`/`null`) would silently re-enable the leak, but the tool schema constrains the field to boolean. Dismissed — matches sibling-flag convention; non-blocking.

### Devil's Advocate

Argue this PR is broken. The strongest case is the one the silent-failure hunter found and I verified live: **this fix lies to its own lie-detector.** The project's whole observability doctrine (CLAUDE.md, emphatically) is that the GM panel is how you tell a working subsystem from Claude improvising. AC4 is literally "DRIVER re-verifies on a live beneath_sunden descent" — through that panel. Yet the moment this feature works correctly and declines "Torchdeep," the still-`is_place`-blind `detect_sidecar_extraction_mismatch` shouts `sidecar_extraction.mismatch: extractor reported 'Torchdeep' not seated by the engine`. A DRIVER scanning the panel for the place-leak would see that exact string and reasonably conclude the bug is NOT fixed — the fix sabotages its own acceptance check. That is worse than cosmetic: it inverts the verification signal. A confused operator misreads success as failure; a future reviewer sees a "mismatch" and reopens a closed bug. Second angle: the flag is half-wired — a classic SideQuest failure mode the CLAUDE.md `<critical>` rules name explicitly. The author wired the producer (extractor schema) and two consumers but missed the third consumer of the same field, which is precisely the "ship 3 of 5 connections and call it done" trap the rules forbid. Third angle (weaker): a malicious narration mis-flagging a real NPC — but I verified that's bounded to a one-turn stale timestamp, not state corruption. The first two angles are real and actionable; they elevate this from "approve with a follow-up" to "fix it in this story, where the flag was born." The functional fix is correct and well-tested; it is simply incomplete across the field's consumers.

**Verdict:** REJECTED (one MEDIUM finding that matches the `<critical>` no-half-wired-features rule — may not be dismissed — and interferes with AC4's own verification path). Rework is small and testable.

## Reviewer Assessment

**Verdict:** APPROVED (Re-review RT1)

_RT0 was REJECTED on one finding — `detect_sidecar_extraction_mismatch` was `is_place`-blind, firing a false-positive `sidecar_extraction.mismatch` span on correctly-declined places (a half-wired flag + AC4-channel pollution). The rework (commits `0f3e9066` test, `d2920c82` fix) resolved it: the mismatch detector now skips `is_place` entries (`sidecar_extractor.py:392`), with two regression tests pinning the fix and its surgical boundary. All RT0 sub-findings are now closed; the RT0 Rule Compliance / Observations / Devil's Advocate above are retained as history._

**RT1 result:** All three enabled specialists returned CLEAN on the incremental diff. No new findings. The `is_place` flag is now wired across all THREE `npcs_present` consumers — `from_value` (orchestrator.py:462), the reconcile guard (narration_apply.py:2575), and the mismatch witness (sidecar_extractor.py:392) — closing the No-Half-Wired-Features gap.

**RT1 specialist incorporation:**
- `[SILENT]` silent-failure-hunter — CLEAN. The new `is_place` `continue` (sidecar_extractor.py:392) is not a silent failure: it suppresses the same predicate the reconcile guard suppresses (symmetric, verified), reads the flag at the correct pre-parse layer (`.get("is_place")` on the raw dict), and cannot diverge from `from_value`'s `bool(...)` cast for any schema-conforming or -violating input. The two regression tests pin the over-suppression boundary.
- `[SEC]` security — CLEAN. No deserialization/injection in the 9-line change; the evade-the-lie-detector vector is informational/self-defeating (the same `is_place` flag also declines the entity from the roster via the reconcile guard, so a flagged entry never enters state).
- `[PREFLIGHT]` 31/31 green, ruff check + format clean, scope additions-only, 0 smells.

**Data flow traced:** narrator prose → sidecar extractor (`npcs_present` dict w/ `is_place`) → split: (a) `detect_sidecar_extraction_mismatch` now SKIPS is_place (✓ no false span); (b) `merge_…`/`from_value` → `_apply_npc_mentions` loop-top guard declines + emits `npc.place_skipped` (✓). The two guards are symmetric on the same predicate at different parse stages — verified consistent (no schema-conforming or schema-violating input can make them disagree).

**Pattern observed:** the mismatch skip mirrors the existing `isinstance(mention, dict)` guard already on the next line (sidecar_extractor.py:394) — minimal, idiomatic, with a load-bearing comment naming the mechanism and failure mode.

**Error handling:** both guards are loud where it matters (the reconcile path emits a span + log); the mismatch skip correctly suppresses only a diagnostic false-positive, granting no capability and changing no state.

**Security:** clean — the evade-the-lie-detector vector is self-defeating (the same flag declines the entity from the roster, so a flagged entry never enters state).

**Tests:** RT1 31/31 green (full sidecar extractor suite + 158-4 reconcile + routing-completeness); both RT0 pre-existing AC4 mismatch tests still pass (skip is surgical). AC4 remains the DRIVER's out-of-band live re-verify (per accepted deviation).

**Handoff:** To SM (Vizzini) for finish-story.