---
story_id: "77-4"
jira_key: "77-4"
epic: ""
workflow: "tdd"
---
# Story 77-4: One-mechanism cleanup — retire quest_updates lane + strip apply_world_patch quest/stakes paths

## Story Details
- **ID:** 77-4
- **Jira Key:** 77-4
- **Workflow:** tdd
- **Stack Parent:** 77-3 (quest_anchors promoted to first-class WorldStatePatch field, merged in PR #626)

## Story Context

Story 77-4 is the fourth story in epic 77 (Quest & Stakes Substrate), following story 77-3's work to promote `quest_anchors` to a first-class WorldStatePatch field. This story completes the substrate by retiring the legacy update mechanism:

1. **Retire the quest_updates lane:** The `WorldStatePatch.quest_updates` field (dict[str, str], status-only) was widened in 77-2 to the structured `quest_log` field (dict[str, QuestEntry]). The legacy lane is now superseded and should be removed entirely from:
   - WorldStatePatch model definition
   - apply_world_patch handler (the coercion at 1381-1385 in session.py)
   - All call sites and tests

2. **Strip apply_world_patch quest/stakes paths:** Per the spec, the apply_world_patch tool escape hatch is intentionally **not** exposed to narrator for `quest_log`, `quest_updates`, or `active_stakes` (see sidequest/agents/tools/apply_world_patch.py:35-50, lines 44-49). This story confirms the escape hatch code correctly rejects these paths and removes any draft/WIP code that would open them.

## Critical Context: Premise Verification

**IMPORTANT: Prior-story finding flagged for verification during RED phase:**

Story 77-3 revealed that the field "world_data_updates" referenced in epic 77's original design story specs **DOES NOT EXIST** in sidequest-server codebase. 

Therefore, this story's premise must be verified:
- The "quest_updates lane" DOES exist as `WorldStatePatch.quest_updates: dict[str, str] | None` (confirmed live, line 501 in session.py)
- The "apply_world_patch quest/stakes paths" in the TOOL are **intentionally NOT exposed** per the escape-hatch design (confirmed lines 44-49 in apply_world_patch.py)

**What this means for TEA/Architect during RED:**

1. The task is **NOT** to remove exposed paths from apply_world_patch — they were never exposed in v1 spec.
2. The task **IS** to remove the internal `quest_updates` field from WorldStatePatch and all its handling, since it was only a coercion bridge during the 77-2 widening.
3. Tests may reference quest_updates as legacy fixtures — these should migrate to quest_log.

This is a straightforward cleanup, NOT a feature removal. Confirm the test premise during RED before writing GREEN.

## Workflow Tracking
**Workflow:** tdd
**Phase:** setup
**Phase Started:** 2026-06-04T00:00:00Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-04T00:00:00Z | - | - |

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Conflict** (blocking-for-broad, non-blocking-for-narrow): Story premise conflates two distinct fields. `WorldStatePatch.quest_updates` (session.py:501) is DEAD (no producer); the LIVE legacy lane the in-code 77-4 markers target is the separate `NarrationTurnResult.quest_updates` pipeline. SM ruled NARROW now / BROAD held (escalated to Neo + Keith for scope+sizing). *Found by TEA during test design.*
- **Gap** (non-blocking): NARROW GREEN migration list for Dev (Agent Smith) — these break with `extra_forbidden` once the field is excised and must be migrated to `quest_log` or removed:
  - Production: `sidequest/game/session.py:501` (field + comments 497-499), `:1381-1385` (apply-branch coercion reader of `patch.quest_updates`).
  - Tests: `tests/game/test_session.py:115` `test_apply_patch_quest_updates`; `tests/game/test_quest_entry_widening.py:131` `test_legacy_quest_updates_apply_coerces_to_quest_entry`.
  - (NOT NARROW — held for BROAD: `narration_apply.py` writer, `websocket_session_handler.py:2237-2241`, `SPAN_QUEST_UPDATE`, `orchestrator.py` extraction/NarrationTurnResult.quest_updates.)
- **Question** (for BROAD ruling): if BROAD lands, does the narrator prompt drop `quest_updates` (and extraction loudly reject a stray emission), or is a migration shim required? Silently dropping status-only updates violates No Silent Fallbacks. *Raised by TEA; awaiting Neo/Keith.*

### Dev (implementation)

- **Gap → RESOLVED** (was non-blocking): TEA's "narrator prompt drops quest_updates" question had no concrete prompt to edit — there is **no narrator-facing prompt string** that lists `quest_updates` as an emittable game_patch field (grep of `sidequest/` across `.py/.md/.j2/.yaml` found only code accessors, doc-comments, and one log-count line). The "contract" was the extraction lane itself. So step 8 reduced to cutting the extraction lane (done) + scrubbing the doc-comments/log line that described it (done). The clean path now structurally cannot emit `quest_updates`; the auto-forward guard catches any stale narrator emission. *Found by Dev during implementation.*
- **Conflict** (non-blocking, scoping — see Design Deviation below): `SPAN_QUEST_UPDATE`/`quest_update_span` has a **second consumer** — the trope-resolution handshake (`narration_apply.py:6025`), test-protected by `test_trope_resolution_handshake.py::test_quest_log_write_emits_quest_update_span` ("do NOT author a new span… the existing SPAN_QUEST_UPDATE route is what the GM panel reads"), plus `test_watcher_events.py` + `test_spans.py` assert the constant exists. Fully deleting the span (literal step 5/7) would regress 3 GREEN test files. Retained the constant + helper; retired only the quest_updates *lane's* use of it. Affects `sidequest/telemetry/spans/state_patch.py`, `sidequest/server/narration_apply.py:6025` (no change needed there — it keeps working). *Found by Dev during implementation.*

## Design Deviations

No deviations at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Scope narrowed to dead-field excision per SM ruling; BROAD live-lane retirement held**
  - Spec source: `.session/77-4-session.md` story text §1; SM dispatch
  - Spec text: "Retire the quest_updates lane … WorldStatePatch model definition, apply_world_patch handler coercion (1381-1385), All call sites and tests"
  - Implementation: RED covers ONLY `WorldStatePatch.quest_updates` excision (the dead field). The LIVE lane (`NarrationTurnResult.quest_updates` → narration_apply writer → SPAN_QUEST_UPDATE → websocket telemetry) that the in-code 77-4 markers also target is NOT tested — held pending the BROAD scope+sizing ruling (Neo/Keith).
  - Rationale: SM ruled narrow-now/broad-held; broad changes live narrator behavior + carries a No-Silent-Fallbacks risk beyond the 3pt sizing.
  - Severity: major
  - Forward impact: a follow-up (or rescoped 77-4) must handle the live lane; the narrow excision is independently safe (dead code).

- **"Apply-branch / no-reader" asserted via reflection + behavioral guard, not source-grep**
  - Spec source: SM dispatch ("the apply branch is gone; no production reader of patch.quest_updates remains")
  - Spec text: "the apply-branch coercion (session.py:1381-1385) is gone; no production reader of patch.quest_updates remains"
  - Implementation: `test_world_patch_has_no_quest_updates_field` interrogates `WorldStatePatch.model_fields` (runtime reflection — the CLAUDE.md 'No Source-Text Wiring Tests' sanctioned tripwire), and `test_apply_world_patch_unrelated_patch_has_no_dangling_quest_updates_reader` is a behavioral guard (a leftover `patch.quest_updates` reader would AttributeError on any apply). No `read_text()`/regex on production source.
  - Rationale: source-text wiring assertions are forbidden; field excision structurally removes the reader (AttributeError otherwise).
  - Severity: minor
  - Forward impact: none

- **One green removal-safety guard among the RED tests (intentional)**
  - Spec source: TDD RED discipline
  - Spec text: "tests must fail for the right reason in RED"
  - Implementation: 3 RED drivers fail now (DID NOT RAISE ×2, field-present ×1); the 4th (`..._no_dangling_quest_updates_reader`) passes today and is a regression guard that only fails on a half-done removal.
  - Rationale: SM explicitly listed "no production reader remains" as a deliverable; the only non-source way to enforce it is a behavioral guard, which is green pre-removal.
  - Severity: minor
  - Forward impact: none

### Dev (implementation)

- **SPAN_QUEST_UPDATE constant + helper RETAINED, not deleted (literal step 5/7 said "DROP")**
  - Spec source: team-lead GREEN dispatch, steps 5 & 7 ("DROP SPAN_QUEST_UPDATE", "SPAN_QUEST_UPDATED is the sole successor span", websocket "no SPAN_QUEST_UPDATE reference")
  - Spec text: "Replace the narration_apply writer … DROP SPAN_QUEST_UPDATE. … SPAN_QUEST_UPDATED (\"quest.updated\") is the sole successor span."
  - Implementation: Retired only the **quest_updates lane's** use of `SPAN_QUEST_UPDATE`. The constant + `quest_update_span` helper are KEPT because the **separate trope-resolution handshake** (`narration_apply.py:6025`) is a second consumer that writes `quest_log["trope_{id}"]` wrapped in `quest_update_span` — and three GREEN test files mandate it: `test_trope_resolution_handshake.py::test_quest_log_write_emits_quest_update_span` ("do NOT author a new span… the existing SPAN_QUEST_UPDATE route is what the GM panel reads"), `test_watcher_events.py::test_on_end_emits_typed_event_for_quest_update_span`, and `test_spans.py` (`assert SPAN_QUEST_UPDATE == "quest_update"`). Deleting the constant would regress all three. The quest_updates **lane** no longer fires it (the auto-forward guard fires the new `quest.updates.legacy_emitted` instead), which fully satisfies the RED contract (`test_legacy_quest_updates_in_game_patch_auto_forwards_to_quest_log` asserts `quest_update` does NOT fire on that path — and it doesn't).
  - Rationale: The story scope is the quest_updates LANE (ADR-137 AC-3), not trope-resolution telemetry. Atomic ≠ destroying a shared, test-protected span used by an out-of-scope subsystem. No-regressions wins over the literal "delete the constant" wording; the behavioral RED contract is met either way.
  - Severity: major
  - Forward impact: if a future story wants the trope handshake off the legacy span too, it must migrate `narration_apply.py:6025` to a trope-specific or `quest.updated` span AND rewrite `test_trope_resolution_handshake.py:218` + the `test_watcher_events`/`test_spans` references. Out of scope for 77-4.

- **Auto-forward guard reads `result.game_patch_dict`, fires new `quest.updates.legacy_emitted` (per ruled contract D)**
  - Spec source: team-lead step 5 + RED test `test_legacy_quest_updates_in_game_patch_auto_forwards_to_quest_log`
  - Spec text: "if game_patch still carries a quest_updates key, forward it to record_quest update-mode (upsert into quest_log…) AND fire a LOUD OTEL span quest.updates.legacy_emitted … NEVER silent-drop, NEVER raise/crash the turn."
  - Implementation: Exactly as specified — guard reads `result.game_patch_dict.get("quest_updates")`, `upsert_quest_status` per entry (the shared status-only mechanism record_quest update-mode uses), fires `quest_updates_legacy_emitted_span` (new, routed to a `state_transition`/`component=quest_log` event for GM-panel visibility), logs a WARNING, never raises. Per-item `isinstance(str,str)` guards skip malformed entries without crashing.
  - Rationale: Direct implementation of the ruled No-Silent-Fallbacks contract.
  - Severity: minor (records the design, not a divergence)
  - Forward impact: none

### Architect (reconcile)

- **Post-review hardening: `legacy_emitted` span counts corrected to actual forwards + `skipped_count` + non-dict signal (compliance fix, not drift)**
  - Spec source: ADR-137 §OTEL spans (the "GM panel must prove the substrate is engaged, not improvised" invariant) + Keith's auto-forward ruling
  - Spec text: "The GM panel must be able to prove the substrate is engaged, not improvised."
  - Implementation: The original GREEN (`6205204`) emitted `updates_count = len(all entries)`, which over-counted when some entries had non-str status — a span that mis-reports what landed is exactly the "lie-detector that lies" the OTEL principle forbids. The hardening loop (RED `e36e479` → GREEN `cbf8fea`) corrected the as-built span contract: gate on **key presence** (absent key = clean path, stays silent), `updates_count`/`quest_ids` = the items that ACTUALLY forwarded (str status), `skipped_count` = dropped items (non-str status), and a **present non-dict value** (list/str/number/None) now emits `legacy_emitted` with `updates_count=0, skipped_count=1` rather than passing silently. Empty dict = benign no-op (no span). Never raises. Verified the else-branch and per-item split in `narration_apply.py:2914-2950`.
  - Rationale: This is a correction INTO OTEL compliance, not a departure from spec — recorded so the audit trail explains why the span's attribute semantics differ between `6205204` and `cbf8fea`.
  - Severity: minor
  - Forward impact: none — the final `legacy_emitted` contract (forwarded/skipped split, non-dict signal) is the durable shape any GM-panel consumer should read.

- **ADR-137 OTEL table is stale vs as-built (auto-forward guard span absent; SPAN_QUEST_UPDATE retained) — session record suffices**
  - Spec source: `docs/adr/137-quest-stakes-substrate.md`, §OTEL spans table + the `quest.updated` note ("the old span may co-fire until 77-4 cuts the legacy quest_updates lane")
  - Spec text: "`quest.updated` is the successor to `SPAN_QUEST_UPDATE` (the old span may co-fire until 77-4 cuts the legacy quest_updates lane)."
  - Implementation: As-built (i) added `quest.updates.legacy_emitted` — a No-Silent-Fallbacks guard span NOT in ADR-137's OTEL table (it is the implementation of Keith's auto-forward ruling, which is itself beyond the ADR's literal "retire the lane" text); and (ii) **retained `SPAN_QUEST_UPDATE`** post-lane-retirement because the trope-resolution handshake (`narration_apply.py:6038`) is a second, test-protected consumer the ADR's OTEL note did not account for — so the note's implication that the old span fully goes away after 77-4 is now partially inaccurate. ADR-137's §Decision and §AC-3 (retire the quest_updates lane; one create/evolve mechanism) remain **accurate as-built**: the lane is fully retired, `record_quest`/`set_stakes` are the one mechanism.
  - Rationale: The ADR's core decision is correct as-built; only the OTEL-table specifics drifted (a new guard span + a retained shared span). Per the spec-authority hierarchy, the session deviation record is the correct durable home for these implementation-level OTEL details; forcing a coordinated orchestrator-repo ADR edit now is disproportionate. Captured for the optional epic-close ADR-137 reconciliation addendum (see spec-reconcile verdict).
  - Severity: minor
  - Forward impact: minor — folds into the epic-close ADR-137 freshness note (shared with 77-3) + the SPAN_QUEST_UPDATE trope-rename follow-up.

## TEA Assessment

**Phase:** red (NARROW complete; BROAD held) | **Tests Required:** Yes

**Test File:** `sidequest-server/tests/game/test_quest_updates_retirement.py` (NARROW scope)

**Tests Written:** 4 (3 RED drivers + 1 removal-safety guard) covering the WorldStatePatch.quest_updates excision contract.
**Status:** RED confirmed — `3 failed, 1 passed in 0.04s` (direct `uv run pytest -n0`).

| Test | Asserts | RED reason (now) |
|------|---------|------------------|
| `test_world_patch_construction_rejects_quest_updates` | construction trips extra_forbidden | DID NOT RAISE (field still accepted) |
| `test_world_patch_model_validate_rejects_quest_updates_payload` | load-path trips extra_forbidden | DID NOT RAISE (field still accepted) |
| `test_world_patch_has_no_quest_updates_field` | field absent from model_fields (reflection) | field still present |
| `test_apply_world_patch_unrelated_patch_has_no_dangling_quest_updates_reader` | apply has no dangling reader (guard) | PASS today (guard) |

**Scope:** NARROW only (dead `WorldStatePatch.quest_updates`). BROAD live-lane retirement (`NarrationTurnResult.quest_updates` → record_quest, cut SPAN_QUEST_UPDATE) NOT written — escalated to Neo/Keith.

**GREEN targets for Dev (NARROW):** remove field (session.py:501 + comments 497-499) and apply branch (1381-1385); migrate the 2 existing tests that construct `WorldStatePatch(quest_updates=...)` (test_session.py::test_apply_patch_quest_updates, test_quest_entry_widening.py::test_legacy_quest_updates_apply_coerces_to_quest_entry) to quest_log or remove them.

**Self-check:** 0 vacuous assertions. Reflection used instead of source-grep (CLAUDE.md No Source-Text Wiring Tests honored).

**Handoff:** Awaiting SM — NARROW ready for Dev; BROAD blocked on scope ruling.

---

## TEA Assessment — ATOMIC BROAD (supersedes the NARROW assessment above)

**Phase:** red | **Scope:** ATOMIC BROAD (Keith ruling — full ADR-137 AC-3 retirement in one PR) | **Tests Required:** Yes

**Test File:** `sidequest-server/tests/game/test_quest_updates_retirement.py` (NARROW folds in as a subset)
**Commits:** 5a29990 (NARROW) + 8ec1a39 (BROAD expansion)
**Status:** RED confirmed — `6 failed, 2 passed in 0.30s` (direct `uv run pytest -n0`). 8 tests.

| Test | Scope | RED reason (now) |
|------|-------|------------------|
| test_world_patch_construction_rejects_quest_updates | A | DID NOT RAISE (field accepted) |
| test_world_patch_model_validate_rejects_quest_updates_payload | A | DID NOT RAISE |
| test_world_patch_has_no_quest_updates_field | A | field in model_fields |
| test_apply_world_patch_unrelated_patch_has_no_dangling_quest_updates_reader | A | PASS (removal-safety guard) |
| test_narration_turn_result_has_no_quest_updates_field | B | field in NarrationTurnResult |
| test_apply_world_patch_allowlist_drops_quest_and_stakes_paths | C | /active_stakes still allowlisted |
| test_legacy_quest_updates_in_game_patch_auto_forwards_to_quest_log | D | update not landed + no legacy_emitted span (failed on assertion, not setup) |
| test_upsert_quest_status_status_only_path_intact | E | PASS (atomicity guard) |

### Design Deviations — ATOMIC BROAD addendum (TEA)
- **Scope expanded NARROW→ATOMIC BROAD per Keith ruling.** The earlier "BROAD held" deviation is superseded: the live `NarrationTurnResult.quest_updates` lane IS retired this story. Severity: major. Forward impact: none — single atomic PR.
- **Auto-forward (No-Silent-Fallbacks) contract codified as the ruled behavior.** A game_patch still carrying `quest_updates` is forwarded to record_quest update-mode (lands in quest_log) + fires `quest.updates.legacy_emitted`; never silent-dropped, never raises. Tested via the real `_apply_narration_result_to_snapshot` path (DB-free, room_for). Severity: major. Forward impact: none.
- **`/active_stakes` removed from the apply_world_patch escape-hatch allowlist** (set_stakes is the typed home post-77-2). Asserted via the runtime `_SUPPORTED_PATHS` dict (not source-grep). Severity: minor.
- **Tool-dispatch & DB-gated paths asserted via runtime-data/behavioral proxies, not live tool dispatch.** `pg_store_with` requires a DB (skips here), so item-6 rejection is proven through the allowlist dict and the atomicity guard through `upsert_quest_status` + the existing DB-gated `test_record_quest` tool test. Severity: minor.

### GREEN targets for Dev (Agent Smith) — ATOMIC, single PR, in dependency order
1. **Prove successor first (atomicity):** confirm record_quest update-mode covers status-only cases (already live, 77-2) BEFORE cutting — no zero-writer window.
2. Remove `WorldStatePatch.quest_updates` field (session.py:501 + comments 497-499) and apply branch (1381-1385).
3. Remove `NarrationTurnResult.quest_updates` field (orchestrator.py:472) and the 3 extraction sites (orchestrator.py:1258, 3219-3220, 3549-3550).
4. Replace the narration_apply writer (2890-2902) with the **auto-forward guard**: read `result.game_patch_dict.get("quest_updates")`; if present → upsert into quest_log (record_quest update-mode semantics) + fire `quest.updates.legacy_emitted` (loud, GM-visible); never silent-drop, never raise. Remove `SPAN_QUEST_UPDATE` emission (quest.updated is the sole successor).
5. `apply_world_patch.py`: drop `/active_stakes` from `_SUPPORTED_PATHS` (116) + its dispatch branch (195-196).
6. websocket_session_handler.py:2237-2241 — drop the `result.quest_updates` telemetry reference.
7. Narrator game_patch prompt contract (server-side agents/) — remove `quest_updates` so the clean path never emits it.
8. Migrate/remove legacy tests: test_session.py::test_apply_patch_quest_updates, test_quest_entry_widening.py::test_legacy_quest_updates_apply_coerces_to_quest_entry, plus any in the quest_updates test-reference set (integration/test_state_patch_wiring, server/test_event_log_wiring, server/test_turn_telemetry_wiring, e2e/test_sync_wiring, etc.).

**Self-check:** 0 vacuous assertions; reflection/runtime-data used instead of source-grep (CLAUDE.md honored); auto-forward test exercises the REAL apply path (no mocks of the path under test). 2 green guards are intentional (removal-safety + atomicity).

**Handoff:** Awaiting SM routing → Dev (Agent Smith) for the atomic GREEN.

## Dev Assessment

**Implementation Complete:** Yes (ATOMIC BROAD — full ADR-137 AC-3 lane retirement, one PR)

**Commit:** 6205204 on feat/77-4-retire-quest-updates-lane (sidequest-server, pushed), atop TEA's 5a29990 (NARROW RED) + 8ec1a39 (BROAD RED).

**Files Changed (7 production + 9 tests, +180/-118):**
- `sidequest/game/session.py` — removed `WorldStatePatch.quest_updates` field + apply-path coercion; updated QuestEntry/upsert_quest_status docstrings.
- `sidequest/agents/orchestrator.py` — removed `NarrationTurnResult.quest_updates` field + all 3 extraction sites (extraction dict, streaming kwarg, shared presentation dict); scrubbed contract doc-comments + the log-count line.
- `sidequest/server/narration_apply.py` — replaced the quest_updates writer with the No-Silent-Fallbacks **auto-forward guard** (reads raw `game_patch_dict`, upserts into quest_log, fires `quest.updates.legacy_emitted`, never raises); added the span import. Kept `quest_update_span` import (trope handshake still uses it).
- `sidequest/telemetry/spans/state_patch.py` — added `SPAN_QUEST_UPDATES_LEGACY_EMITTED` + state_transition route + `quest_updates_legacy_emitted_span` emitter. **Retained** `SPAN_QUEST_UPDATE` (trope handshake consumer — see deviation).
- `sidequest/agents/tools/apply_world_patch.py` — dropped `/active_stakes` from `_SUPPORTED_PATHS` + dispatch branch + docstrings (set_stakes is the typed home).
- `sidequest/server/websocket_session_handler.py` — removed the dangling `result.quest_updates` PatchSummary block.
- `sidequest/agents/tools/record_quest.py` — docstring accuracy (lane retired).
- Tests migrated: `test_dispatch.py` + `test_state_patch_wiring.py` (→ drive `game_patch_dict`, assert auto-forward / `legacy_emitted` route); removed field-exercising tests in `test_session.py` + `test_quest_entry_widening.py` (superseded by retirement file, left pointer comments); stripped dead `quest_updates={}` kwargs from 4 result-fixture helpers + the magic-dispatch Mock neutralizer.

**Tests:** 8/8 retirement tests GREEN. Focused green set (retirement + all migrated + the 3 SPAN_QUEST_UPDATE-dependent files I preserved) = 170 passed. Verified via direct `uv run pytest -n0` (NOT testing-runner).

**Regressions:** ZERO. Full suite: **26→20 failed** with my changes (the 6 RED retirement tests fixed; the remaining 20 failed / 72 errors are pre-existing DB-env `MissingDatabaseUrlError`, proven identical by re-running with changes stashed = 26 failed/72 errors at RED baseline). DB-gated `test_record_quest.py::test_update_existing_quest_changes_status_and_fires_quest_updated` (the full-tool atomicity proof) skips without `SIDEQUEST_DATABASE_URL`.

**Lint/format:** `ruff check` + `ruff format --check` clean on all 7 production files.

**Atomicity:** Successor (`upsert_quest_status` / record_quest update-mode) proven intact BEFORE the cut (test E, green guard). No two-writer or zero-writer window. Single coherent PR.

**Branch:** feat/77-4-retire-quest-updates-lane (pushed)

**Handoff:** To review/verify. KEY FLAG for Reviewer (The Merovingian): I retained `SPAN_QUEST_UPDATE` rather than deleting it (literal step 5/7) — it has a separate, test-protected trope-handshake consumer out of scope for the quest_updates lane. The RED contract (legacy span must not fire on the auto-forward path) is fully met. See Design Deviations.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None — one load-bearing deviation (SPAN_QUEST_UPDATE retained) RATIFIED.
**Verification:** Re-verified the committed GREEN (`6205204`, 16 files, +180/-118) against HEAD myself — successor, raw-patch attr, trope consumer, and escape-hatch all confirmed in source, not taken on report.

### The deviation ruling (the spec-check call SM asked for)

**RATIFIED — preserving `SPAN_QUEST_UPDATE` for the trope-resolution handshake is CORRECT, and ADR-137 AC-3 remains fully satisfied.**

AC-3's end-state is "one create/evolve lane … zero structurally-dead fields, zero discouraged duplicate writers" — the target is the **quest_updates writer LANE, not the span string**. Verified the lane is fully retired: `NarrationTurnResult.quest_updates` field gone (orchestrator.py:469), `WorldStatePatch.quest_updates` field + apply-coercion gone (session.py:497/1381), all 3 extraction sites gone (orchestrator.py:1253/3214/3541), the apply-writer replaced, and the legacy span **no longer fires from the quest_updates path** (the `with quest_update_span(...)` block at the old writer is deleted; the new guard fires `quest.updates.legacy_emitted` instead — RED-asserted that `quest_update` does NOT fire there).

The trope-resolution handshake (`narration_apply.py:6038`, documented 5981-82) is a **different subsystem** — it writes `quest_log["trope_{id}"]` on a *resolved trope*, which is not a quest_updates write and not a competing create/evolve affordance the narrator selects. Its use of the shared `SPAN_QUEST_UPDATE` is a legitimate, test-protected GM-panel surface (3 tests mandate it, incl. one explicitly stating "do NOT author a new span"). Deleting the constant would (a) regress those 3 tests and (b) **delete a live observability surface for an unrelated subsystem — itself a violation of the OTEL principle.** The literal "DROP SPAN_QUEST_UPDATE" GREEN-brief wording was lane-scoped intent; Dev correctly read scope over literal text. SM's read is confirmed: AC-3 targets the writer, not the span name; the trope handshake is not a quest_updates writer.

**Q2 — trope-handshake span migration:** correctly **OUT OF SCOPE for 77-4**. It's ADR-128 trope-subsystem territory; migrating it requires rewriting 3 tests that encode a deliberate trope-subsystem design decision. *Minor naming-debt forward note (non-blocking, NOT required):* post-77-4, `SPAN_QUEST_UPDATE`'s sole remaining caller is the trope handshake, so the name `"quest_update"` now slightly misrepresents its only purpose. IF a future trope-subsystem story touches this surface, consider renaming to a trope-scoped span for clarity — but renaming churns a live GM-panel route, so it is not obviously worth a dedicated story. Logged for awareness only.

### Atomicity (Q3) — CONFIRMED, no two-writer / zero-writer window

Single PR (`6205204`). The successor — `record_quest` update-mode → `quest.updated` span (record_quest.py UPDATE branch sets `existing.status`, fires `quest_updated_span`) — has been **live since 77-2, before this PR cut the legacy lane** ⇒ no zero-writer window. The cut is atomic within the PR (typed field + 3 extraction sites + apply-writer all removed together) ⇒ no two-writer window. Post-cut quest_log status writers are `record_quest` (typed tool), the trope handshake (different subsystem), world-materialization, and the auto-forward guard (drift safety net) — **none is a duplicate quest_updates lane.**

### Guard-not-theater (Q4) — CONFIRMED genuinely loud + non-destructive

The auto-forward guard (narration_apply.py:2890-2920) genuinely **lands** the update — `upsert_quest_status(snapshot.quest_log, …)` mutates real quest_log state (per-item `isinstance(str,str)` guarded) — and **fires loud**: `quest_updates_legacy_emitted_span` → `SPAN_ROUTES[SPAN_QUEST_UPDATES_LEGACY_EMITTED]` → `state_transition`/`component=quest_log` event (`op=legacy_updates_auto_forwarded`, carries `quest_ids_json` + `updates_count` + player + turn), GM-panel visible — plus a `logger.warning`. It **never raises** (live-turn safety, per Keith's auto-forward ruling). It reads `result.game_patch_dict` — the RAW extracted patch, exactly where drift lands now that the typed field is gone. Not decorative.

**Design strength noted:** the two stray-key surfaces are handled differently and correctly — **hard reject** via `extra="forbid"` on the *deprecated* `apply_world_patch` escape hatch (a ToolResult error on a path the narrator is told not to use), **soft auto-forward** on the *live narration* path (no turn crash). Both honor No-Silent-Fallbacks; the split is the right call for playgroup safety.

### Escape-hatch (AC-3 third bullet) — CONFIRMED

`apply_world_patch` allowlist: `/active_stakes` removed (`set_stakes` is the typed home); `/quest_log` + `/quest_updates` were never on it. ADR-137 AC-3 "strip /quest_log, /quest_updates, /active_stakes from apply_world_patch" end-state achieved.

**Decision:** PASS — proceed to TEA verify. The SPAN_QUEST_UPDATE-retained deviation is ratified; the naming-debt forward note is awareness-only and not a finish blocker.

---

## TEA Verify Verdict — PASS (ATOMIC BROAD)

**Phase:** verify | **Diff:** 6205204 (7 prod + 9 test files, +180/-118) | **Verdict:** PASS — ready for Reviewer. No code changes required.

### Simplify Report
**Teammates:** reuse, quality, efficiency (haiku, parallel) | **Files analyzed:** 7

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | clean | upsert_quest_status reuse by the auto-forward guard is intentional (shared status-only successor), not duplication. |
| simplify-quality | clean | Type-safe guard, clean extraction-site removals, SPAN_QUEST_UPDATE retention correct + documented, no orphaned refs. |
| simplify-efficiency | 1 minor | `list(quest_ids)` in state_patch.py:~278 is a redundant copy (param already list[str]); error-recovery path, 1-5 items. Double-iteration in the guard is JUSTIFIED (distinct purposes). |

**Applied:** 0 (zero high-confidence). **Flagged:** 1 low (redundant `list()` — not worth a regression-risking change on an error-recovery path). **Reverted:** 0. **Overall:** simplify: clean.

### Quality Gates
- **ruff check** (7 files): PASS. **ruff format --check** (7 files): PASS (already formatted).
- **Retirement suite** `tests/game/test_quest_updates_retirement.py`: **8 passed**.
- **Dev's migrated/touched set** (test_session, test_quest_entry_widening, test_state_patch_wiring, test_dispatch, test_event_log_wiring, test_turn_bridge_diagnostic, test_turn_telemetry_wiring, test_sync_wiring, test_magic_working_dispatch): **67 passed, 8 skipped**.
- **Full suite:** **8897 passed, 1446 skipped, 20 failed, 72 errors** (33s).

### Zero-regression spot-check (Dev's 26→20 claim)
CONFIRMED. The 20 failed + 72 errors are all `MissingDatabaseUrlError` (verbatim traceback), identical to the established 77-3 DB-env baseline. Sanity grep across all 20 FAILED names for `quest_updates|quest_update|narration_apply|legacy_emitted|active_stakes|apply_world_patch` → **zero hits**; 77-4 touches no DB/persistence code. The 6 previously-failing RED retirement tests now pass (folded into the 8897). No new regressions.

### Authenticity (item 3)
- **Auto-forward guard test drives the REAL consumer:** `test_legacy_quest_updates_in_game_patch_auto_forwards_to_quest_log` calls the real `_apply_narration_result_to_snapshot` via `room_for` (MagicMock is only the SaveRepository, NOT the path under test). Grep confirmed no mock of the consumer.
- **Span behavior authentic:** the passing test asserts (a) the update LANDS (`quest_log["q_witch"].status == "resolved"`), (b) `quest.updates.legacy_emitted` fires, AND (c) the legacy `quest_update` span does NOT fire on that path (line 178). All three hold in GREEN.
- **Migrated tests non-vacuous/coupled:** test_state_patch_wiring asserts the real hub-routed `state_transition` (op=`legacy_updates_auto_forwarded`, count, player, turn, JSON quest_ids) through `WatcherSpanProcessor` — genuine wiring, not existence. test_dispatch asserts the behavioral `quest_log` landing.
- **No coverage hole:** the two removed tests (test_session::test_apply_patch_quest_updates, test_quest_entry_widening::test_legacy_quest_updates_apply_coerces_to_quest_entry) exercised the RETIRED `WorldStatePatch.quest_updates` field only; the surviving 77-2 `quest_log` widening/QuestEntry-coercion tests remain in test_quest_entry_widening.py.

### ADR-137 AC-3 coverage
All 8 surface items + the No-Silent-Fallbacks guard covered and green. SPAN_QUEST_UPDATE retention (Neo's ratified deviation) is test-protected (test_trope_resolution_handshake.py).

**Handoff:** To Reviewer (The Merovingian). One non-blocking note: the redundant `list()` micro-copy in state_patch.py — Reviewer's discretion.

## Reviewer Assessment

**Verdict:** APPROVED (1 MEDIUM + 2 LOW observations — all NON-BLOCKING)
**Reviewer:** The Merovingian (adversarial review of 6205204, 7 prod + 9 test files, +380/-118) — independently verified, did not trust upstream prose. Ran the full 8-probe sweep SM set.

**Data flow traced (verified myself):** legacy `quest_updates` field removed from BOTH transient
carriers (NarrationTurnResult, WorldStatePatch) + all 3 extraction sites + both apply writers +
the websocket PatchSummary. A stale raw-patch `quest_updates` key is now caught by the
auto-forward guard in `_apply_narration_result_to_snapshot` (narration_apply.py:2904) →
`upsert_quest_status` into quest_log → `quest.updates.legacy_emitted` span (routes to
state_transition/quest_log, GM-panel reachable, verified registered) + `logger.warning`. Guard is
on the REAL production path (websocket_session_handler.py:963).

**The 8 probes, answered:**
1. **Lane genuinely retired?** YES. Grep-confirmed every surviving `quest_updates` reference in
   `sidequest/` is a comment/docstring or the new guard — zero surviving writer/reader/field/extraction.
2. **Guard malformed-input behavior** — empirically exercised 8 shapes (see findings). Well-formed
   forwards + fires span ✓. Never raises ✓ (by construction — no risky ops, NOT via swallow). But two
   gaps found (MEDIUM + LOW below).
3. **Span loud enough / prod-reachable?** YES — guard on the real websocket narration path; new span
   route registered (state_transition/quest_log); integration test drives emit→WatcherSpanProcessor→hub.
4. **Atomicity (resume/replay)?** SAFE. `quest_updates` was transient-only — never persisted (confirmed
   no persistence-layer reference). No half-cut window; the lane is cut atomically in one commit.
5. **/active_stakes hard-reject?** CORRECT. Unsupported path → `ToolResult.error(recoverable=True)`
   pointing to `set_stakes` (confirmed `set_stakes.py` exists + registered) — loud-but-recoverable, not
   a crash, not a silent drop. Hard-reject is right for the tool surface (recoverable-error channel exists);
   soft auto-forward is right for the raw-patch surface (no such channel). Asymmetry justified.
6. **SPAN_QUEST_UPDATE retention?** RATIFIED DEVIATION HOLDS. `quest_update_span` survives ONLY at the
   trope-resolution handshake (narration_apply.py:6038, independent `fresh_writes` / trope_<id> keys — no
   shared state with the retired lane). The quest_updates path no longer fires it (test-asserted at
   retirement test line 178). Confirmed independent.
7. **New swallowed errors?** NONE. The guard "never raises" by using only non-throwing ops, not by
   swallowing — the correct pattern. No new bare-except across the 7 files.
8. **Coverage drop?** NONE. The 2 removed tests exercised the DELETED field only; the integration wiring
   test was UPDATED (not dropped) to drive the new guard through the real hub. Surviving 77-2 quest_log
   widening/coercion tests remain.

**FINDINGS:**

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| [MEDIUM] | Auto-forward span MISREPORTS forwarded updates + silent per-item drop. Empirically: `{q1:5}` → span fires `quest_ids=["q1"]`, `updates_count=1`, but quest_log stays EMPTY (non-str status skipped by the per-item `isinstance(status,str)` guard). `{q1:"active", q2:9}` → span `quest_ids=[q1,q2]`, `count=2`, but only q1 lands. The `quest.updates.legacy_emitted` span (the project's "lie detector") claims forwards that did NOT happen, and the dropped item has no distinct signal — undetectable from the span alone since `quest_ids` includes ALL str keys. | narration_apply.py:2906-2918 | Build `quest_ids` + `updates_count` from items that ACTUALLY forwarded (str key AND str status); add a `skipped_count` attr so malformed items are LOUD not silent. |
| [LOW] | Non-dict `quest_updates` is ENTIRELY silent. Empirically: `quest_updates: ["q1"]` or `"resolved"` → no span, no warning, nothing. No state loss (non-dict carries no forwardable mapping), but the stale-contract signal the guard exists to provide is absent for non-dict shapes. | narration_apply.py:2905 | Fire a warning/span for any present, non-empty, non-dict `quest_updates` so the contract violation is observable. |
| [LOW] | Redundant `list()` copy (already flagged by TEA/simplify). | state_patch.py:~278 | Cosmetic; error-recovery path. Drop the copy or leave — Dev's call. |

**Why MEDIUM, not blocking:** the MEDIUM affects a retired-lane / stale-narrator edge only (the clean
path no longer emits the key). Critically, it is NOT a data-loss regression — a non-str status
(`5`/`None`/`{x:y}`) was NEVER a valid applicable status; the new per-item guard SKIPPING it is strictly
SAFER than the old guard-less writer (which would have forwarded garbage or crashed). The only defect is
OTEL count/claim accuracy, and the span DOES fire (operator sees legacy emission occurred). Per the
severity table, no Critical/High → does not block. Recommend the MEDIUM as a fast follow-up.

**Verification I ran myself** (memory: testing-runner hallucinates — counts verified by hand):
47 passed (retirement + integration wiring + widening + session); 358 passed in telemetry + dispatch
(zero regressions); ruff clean on all 7 prod files; runtime malformed-shape matrix (8 inputs);
runtime span-route registration + import resolution. The 20 failed/72 errored in the full suite are
the pre-existing `MissingDatabaseUrlError` (DB unset) — structurally unrelated to this DB-free diff;
corroborates TEA.

**Deviation audit:** SPAN_QUEST_UPDATE retention (2nd consumer = trope handshake) — ACCEPTED, ratified by
Neo, independence verified. /active_stakes drop → set_stakes — ACCEPTED, typed home confirmed present.

**Handoff:** To SM (Morpheus) for finish-story. MEDIUM finding recommended as follow-up (Reviewer's call:
non-blocking — ship-able as-is).

---

## TEA Re-RED — Hardening (Reviewer MEDIUM: legacy_emitted span accuracy)

**Phase:** red (hardening) | **Commit:** e36e479 | **Trigger:** Reviewer-approved-with-MEDIUM (SM not deferring).

**Bug:** the auto-forward guard's `quest.updates.legacy_emitted` span — this guard's GM-panel lie-detector — reports the RAW input keys/count, not what actually forwarded into quest_log, and non-dict input is entirely silent. A lie-detector that lies violates the No-Silent/OTEL AC this story exists to honor.

**3 new failing tests** (in tests/game/test_quest_updates_retirement.py), verified RED via direct `uv run pytest -n0` — `3 failed, 8 passed`:
| Test | Corrected contract | RED evidence (now) |
|------|--------------------|--------------------|
| test_legacy_emitted_span_counts_only_forwarded_items | {q1:"active",q2:9} → span quest_ids==["q1"], updates_count==1, skipped_count==1 | span reports updates_count=2, quest_ids_json='["q1","q2"]' (raw keys — the lie) |
| test_legacy_emitted_span_reports_all_skipped_drop | {q1:5} → quest_log empty, span fires updates_count==0 AND skipped_count==1 | span reports updates_count=1 (raw len), no skipped_count attr |
| test_non_dict_legacy_quest_updates_emits_signal_not_silent | quest_updates=["junk"] → an observable quest.updates.legacy* span fires; never raises | no span fires at all (silent drop) |

**Existing guarantees held green:** valid str-status items still land + the original auto-forward test still passes + the guard never raises.

### GREEN targets for Dev (small deltas)
1. `narration_apply.py` guard: build forwarded-ids/count from items that actually upserted (str key AND str status); track skipped items (non-str status, or non-str key).
2. `state_patch.py` `quest_updates_legacy_emitted_span`: pass forwarded `quest_ids`/`updates_count` + add `skipped_count` (and/or `skipped_ids`) attribute + route field.
3. Non-dict `quest_updates`: emit an observable `quest.updates.legacy*` span (legacy_emitted with count=0/skipped, or a distinct legacy_malformed) + logger.warning; never silent, never raise.
4. (Ride-along) the redundant `list(quest_ids)` micro-copy in state_patch.py.

**Handoff:** Awaiting SM → Dev for GREEN.

## Dev Assessment — Hardening Pass (Reviewer MEDIUM, rides same atomic PR)

**Commit:** cbf8fea on feat/77-4-retire-quest-updates-lane (pushed), atop TEA's hardening re-RED e36e479.

**Why:** the `quest.updates.legacy_emitted` span is the guard's lie-detector; it was reporting raw input keys rather than what actually landed. TEA added 3 failing tests (e36e479).

**Changes (2 files, +75/-29):**
- `sidequest/server/narration_apply.py` — guard now gates on key PRESENCE (absent key = clean path, silent), partitions dict items into forwarded (str status → upsert) vs skipped (non-str), fires the span with `quest_ids`/`updates_count` = forwarded-only + `skipped_count` = dropped; a present non-dict value (list/str/number/None) fires the observable signal with `skipped_count=1` (never silent, never raises).
- `sidequest/telemetry/spans/state_patch.py` — added `skipped_count` to the emitter + the state_transition route's fields; removed the redundant `list()` micro-copy (TEA flag).

**Tests:** 11/11 retirement green (8 prior + 3 hardening). 114-test focused set green (incl. migrated wiring/dispatch + the 3 SPAN_QUEST_UPDATE-dependent files). Never-raises + valid-item forwarding preserved.

**Regressions:** ZERO — full suite 20 failed / 72 errors (pre-existing DB-env, unchanged); passed 8898→8901 (+3 hardening).

**Lint/format:** clean on both files.

## Reviewer Delta Re-Review (cbf8fea over 6205204)

**Verdict:** ✅ APPROVED — delta CLEARS. The MEDIUM and non-dict LOW I raised are genuinely fixed,
not papered over. Verified independently by re-running my original malformed matrix (now 12 shapes)
against cbf8fea.

**Scope reviewed:** ONLY the hardening delta (narration_apply.py guard + state_patch.py emitter/route).
The core retirement is unchanged and stays approved.

**The fix, verified empirically (span attrs read directly off finished spans):**

| Input shape | OLD (the lie) | NEW (cbf8fea) | landed | raises? |
|-------------|---------------|---------------|--------|---------|
| absent key (clean path) | no span | no span (silent) ✓ | {} | no |
| `{q1:5}` non-str status | span count=1 ids=["q1"] (LIE) | fwd=0 ids=[] **skipped=1** | {} | no |
| `{q1:"active", q2:9}` mixed | span ids=[q1,q2] (LIE) | fwd=1 ids=["q1"] **skipped=1** | {q1:active} | no |
| `{q1:{x:y}}` nested | span ids=["q1"] (LIE) | fwd=0 ids=[] **skipped=1** | {} | no |
| `{q1:None}` | span ids=["q1"] (LIE) | fwd=0 ids=[] **skipped=1** | {} | no |
| list / bare-str / int / float / None payload | **SILENT** | span fwd=0 **skipped=1** (observable) | {} | no |
| empty dict `{}` | no span | no span (benign no-op) ✓ | {} | no |
| well-formed `{q1:done}` | span ids=["q1"] | fwd=1 ids=["q1"] skipped=0 (unchanged) | {q1:done} | no |

**The 5 delta probes, answered:**
1. **Span reports ONLY actually-forwarded items in ALL shapes?** YES — verified across 12 shapes.
   `quest_ids` + `updates_count` now derive from the forwarded-only partition; the lie is eliminated.
   My exact MEDIUM example `{q1:"active", q2:9}` now reports `ids=["q1"]`, not `[q1,q2]`.
2. **Skipped item genuinely OBSERVABLE (not just moved silence)?** YES — `skipped_count` is on the
   emitter attrs AND in the `SPAN_ROUTES` extract lambda; I drove the route directly and confirmed
   `skipped_count` reaches the hub `state_transition` event (=2 for a 2-skip fake span). The GM panel
   sees every drop.
3. **Every non-dict shape fires a signal?** YES — list, bare-str, int, float, AND None all fire
   `quest.updates.legacy_emitted` with `skipped_count=1`. No residual silent non-dict shape.
4. **New silent path from presence-gating?** NO. Only two silent paths remain, both defensible:
   absent key (the normal clean path — correct) and empty-dict `{}` (well-formed, zero items, no drop
   and no forward — a benign no-op, principled-ly distinct from a malformed non-dict which DOES fire).
   The `if _forwarded_ids or _skipped:` gate draws exactly the right line. No silent path hides a drop.
5. **Never-raises + happy-path intact?** YES — all 12 shapes return without raising; happy-path
   forwarding unchanged (lands + fwd=1). The `quest_ids_json` serialization change
   (`dumps(list(x), sort_keys=True)` → `dumps(x)`) is a no-op for lists (sort_keys only affects dicts;
   the list copy was redundant) — the integration/hub test contract is preserved (single-item output
   identical). The TEA-flagged `list()` micro is removed.

**Verification I ran myself:** 12-shape malformed matrix with direct span-attr assertions; route-extract
hub propagation of `skipped_count`; 12 passed (retirement incl. re-RED + integration wiring); 358 passed
telemetry + dispatch (zero regressions); ruff clean on both changed files.

**No new findings. All three prior findings resolved** (MEDIUM span-lie fixed; non-dict LOW fixed;
list() micro removed). This is the final review gate — clean.

**Handoff:** To SM (Morpheus) for spec-reconcile + finish-story.

## Architect Assessment (spec-reconcile)

**Status:** RECONCILED — clear for finish.

Re-verified the final commit stack (`5a29990` + `8ec1a39` + `6205204` + `e36e479` + `cbf8fea`) against HEAD myself, including the post-review hardening, and cross-checked ADR-137/128/114.

### 1. Design Deviations record — COMPLETE & accurate (durable audit trail)

All entries verified against the as-built. The complete set:
- **TEA:** NARROW-scope (superseded by the BROAD addendum), reflection-not-grep assertions, the intentional green removal-guard.
- **TEA (BROAD addendum):** scope expanded NARROW→ATOMIC BROAD per Keith; auto-forward No-Silent contract codified; `/active_stakes` stripped from the escape hatch; runtime-proxy assertions where DB-gated.
- **Dev:** `SPAN_QUEST_UPDATE` constant retained (2nd consumer = trope handshake) — **ratified at spec-check**; auto-forward guard reads `result.game_patch_dict`.
- **Architect (reconcile, added this phase):** (i) the post-review hardening that corrected the `legacy_emitted` span to report actual forwards + `skipped_count` + non-dict signal (a correction INTO OTEL compliance, recorded so the audit trail explains the attribute-semantics change between `6205204` and `cbf8fea`); (ii) the ADR-137 OTEL-table staleness (guard span absent + `SPAN_QUEST_UPDATE` retained).

No additional deviations beyond these. No AC deferrals to audit (ATOMIC BROAD delivered the full AC-3 surface; nothing deferred).

### 2. ADR-137 reconciliation CALL → **(a) NO ADR amendment required to finish 77-4.**

Rationale (same standard as 77-3): **ADR-137's §Decision and §AC-3 are accurate as-built.** The quest_updates lane is fully retired and `record_quest`/`set_stakes` + the creation seed are the one create/evolve mechanism — exactly the declared end-state. The only drift is OTEL-table-level: (i) the `quest.updates.legacy_emitted` guard span is an addition implementing Keith's auto-forward ruling (itself beyond the ADR's literal "retire the lane" text), and (ii) `SPAN_QUEST_UPDATE` is retained for the trope-resolution handshake — a consumer the ADR's OTEL note didn't account for, making its "old span goes away after 77-4" implication partially inaccurate. Neither touches the decision; both are implementation-level and correctly housed in the session deviation record. Forcing a coordinated orchestrator-repo ADR edit now is disproportionate.

**Optional, non-blocking — epic-close batching only (NOT a 77-4 finish gate).** Fold into the shared ADR-137 reconciliation addendum at epic close. Do NOT edit ADR-137 from the server workspace; do NOT gate 77-4 on it. 77-4 portion text:

> **Implementation reconciliation — 77-4 (2026-06-04).** The quest_updates lane retirement (§AC-3) shipped as-decided: the legacy lane (`NarrationTurnResult.quest_updates`, `WorldStatePatch.quest_updates`, the 3 extraction sites, the apply-writer) is fully retired and `record_quest`/`set_stakes` are the one create/evolve mechanism. Two OTEL-table refinements vs this ADR: (1) a No-Silent-Fallbacks guard span `quest.updates.legacy_emitted` was added — a narrator game_patch still carrying a retired `quest_updates` key is auto-forwarded to `quest_log` (via `upsert_quest_status`) and the loud span fires (reporting forwarded count + `skipped_count` + non-dict signal), never silent-dropped, never crashing the live turn (playgroup safety); (2) `SPAN_QUEST_UPDATE` is **retained, not removed** — post-retirement its sole remaining consumer is the trope-resolution handshake (a separate, test-protected GM-panel surface), so the "old span co-fires until 77-4 cuts the lane" note now reads: the lane no longer fires it, but the trope subsystem legitimately still does.

### 3. Sibling ADRs — no contradiction.

- **ADR-128 (trope governor / seed deck):** zero references to `SPAN_QUEST_UPDATE`/`quest_update`/`quest_log` (grep-confirmed). The retained span is the trope handshake's GM-panel surface — an implementation detail ADR-128's text does not govern, so retaining it does not step on ADR-128. **No contradiction.** (The optional future trope-scoped rename, if it happens, would be an ADR-128-adjacent code-cleanup story — see batch list.)
- **ADR-137:** core decision accurate as-built (§2 above). No contradiction; only optional OTEL-table freshness.
- **ADR-114 (ablative HP substrate):** zero `quest_updates`/`quest_log`/`SPAN_QUEST` coupling (grep-confirmed); orthogonal subsystem. **No contradiction.**

### Epic-close batch list (reminder, as requested) — now THREE items:

1. **ADR-137 freshness addendum (77-3 portion)** — story-numbering drift + `quest.anchor.added` → `quest_anchors_present`/`consumed`. Text in `.session/77-3-session.md` spec-reconcile verdict.
2. **ADR-137 freshness addendum (77-4 portion)** — `quest.updates.legacy_emitted` guard span + `SPAN_QUEST_UPDATE` retained-for-tropes. Text above. *(Items 1 & 2 can land as ONE ADR-137 reconciliation addendum.)*
3. **`SPAN_QUEST_UPDATE` trope-scoped rename** — a code-cleanup follow-up story (ADR-128-adjacent), NOT an ADR edit: post-77-4 the span's sole caller is the trope handshake, so the name `"quest_update"` is now slightly stale. Optional; renaming churns a live GM-panel route, so only worth doing if a future trope story touches that surface.

**Decision:** RECONCILED. ADR call = **(a)**. Proceed to finish ceremony (PR → merge → archive). The three epic-close items are batched for SM's discretion at epic close, none blocking 77-4.
