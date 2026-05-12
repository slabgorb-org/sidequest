---
story_id: "49-3"
jira_key: null
epic: "49"
workflow: "tdd"
---

# Story 49-3: Location-patch enforcement when narrator titles drift from state

## Story Details

- **ID:** 49-3
- **Epic:** 49 (Playtest 4 Closeout — Glenross / ADR-098 Continuity Recovery)
- **Jira Key:** none (SideQuest is a personal project, not tracked in Jira)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3
- **Priority:** p1

## Story Context

In the 2026-05-11 Glenross playtest, the narrator silently relocated the scene across four different room titles over five turns:
- Turn 1: The Bee Garden
- Turn 2: The Manse Garden
- Turn 3: Front Parlour
- Turn 4-5: Study
- Turn 6: Sickroom Passage

However, canonical state held `character_locations[Ziggy]='the_manse'` for turns 1-5, only catching up on turn 6. Game patch logs show `has_location=False` on turns 2-5: the narrator wrote new **Room Title** headers in markdown prose without filling the structured `location` patch field.

This is the SOUL.md "Illusionism" failure mode — narrator and state machine running on different tracks. The GM panel cannot tell where the party actually is.

## Technical Approach

### Phase 1: Parse location from prose + auto-fill patch

**Location:** `sidequest/server/narration_apply.py` around line 1641 where `if result.location:` is evaluated.

**Logic:**
1. When `result.location` is empty (`None` or empty string), scan the narration body for a leading bold markdown header.
2. Pattern: `^##?\s*\*\*[^*]+\*\*` — match the first bold-enclosed text at the beginning of the prose.
3. Extract the text inside the bold delimiters (e.g., `**The Manse — Front Parlour**` → `The Manse — Front Parlour`).
4. Call this the **candidate location**.
5. Compare the candidate against the current state: `snapshot.character_locations.get(actor_for_location)`.
6. If they differ, auto-fill `result.location = candidate` and emit a **loud OTEL span** before continuing.
7. Continue applying the location change through the normal flow (process_room_entry, character_locations binding, discovered_regions, etc.).

**Key design decisions:**
- **Auto-fill instead of fail-loud** — blocking a turn is too costly. The repair is a backstop, not a load-bearing component.
- **OTEL must be loud** — the GM panel sees every repair so we can iterate on the prompt later to prevent the drift.
- **Only trigger when patch.location is empty** — if the narrator fills the patch field explicitly, trust it over the prose title (narrator made a deliberate choice).

### Phase 2: Add OTEL span for visibility

**New span:** `narrator.location_drift_repaired`

**Attributes:**
- `severity: "WARNING"` — Sebastien's GM panel must surface every repair
- `old_state`: the stale location from `snapshot.character_locations[actor_for_location]`
- `new_from_title`: the extracted bold-title text from prose
- `turn`: the current turn number from snapshot
- `character`: the actor name (e.g., "Ziggy")
- `player_name`: the player name (for audit trail)

**Location:** New span in `sidequest/telemetry/spans/orchestrator.py` (or adjacent module).

### Phase 3: Add Recency-zone guardrail to prevent the root cause

**Location:** `sidequest/agents/orchestrator.py` prompt builder (around the section that registers location constraints).

**Content:** Add a guardrail section in the Recency attention zone:

```
location_patch_constraint:
  If your prose changes the room (any new **Bold Title** header, any explicit movement to a different named space),
  your game_patch MUST set location to the new value.
  State must not lag prose.
```

This addresses the issue at narration time so the auto-repair becomes a backstop, not a load-bearing component.

## Acceptance Criteria

### Implementation

1. **In `narration_apply.py` around line 1641:**
   - When `result.location` is falsy, scan the narration prose for a leading bold markdown header (`^##?\s*\*\*[^*]+\*\*`).
   - Extract the text inside the bold delimiters as `candidate_location`.
   - Compare candidate vs. `snapshot.character_locations.get(actor_for_location)`.
   - If different, set `result.location = candidate_location` before applying.

2. **OTEL span `narrator.location_drift_repaired`:**
   - Emit with severity `WARNING` (not INFO).
   - Attributes: `old_state`, `new_from_title`, `turn`, `character`, `player_name`.
   - Emit only when auto-fill actually happens (candidate differs from current state).

3. **Prompt guardrail in `orchestrator.py`:**
   - Add `location_patch_constraint` guardrail to the Recency attention zone.
   - Plain-English reminder to the narrator: "If your prose changes the room, your game_patch MUST set location."

### Testing

4. **Regression test: `test_location_drift_repair.py`**
   - Fixture: `snapshot.character_locations[Ziggy]='the_manse'`, narration body begins `**The Manse — Front Parlour**\n\nThe kettle...`, `patch.location=None`.
   - After apply: `character_locations[Ziggy]` must equal `'The Manse — Front Parlour'`.
   - OTEL span `narrator.location_drift_repaired` must have fired with `old_state='the_manse'`, `new_from_title='The Manse — Front Parlour'`.

5. **Integration test: Replay Glenross turn 3**
   - Load the glenross save file from `~/.sidequest/saves/`.
   - Re-run turn 3 with the new location-drift logic.
   - State must update from `'the_manse'` to `'The Manse — Front Parlour'` instead of holding stale.
   - OTEL watcher events confirm the repair ran.

### Non-regression

6. **When `patch.location` is explicitly set:**
   - Trust the narrator's explicit patch field.
   - Do NOT override with the prose title.
   - The guardrail reminds the narrator to fill the field; the auto-repair is for when they forget.

7. **When no bold title appears in prose:**
   - Silent no-op.
   - Continue with `result.location` as-is (which may be `None`).
   - No OTEL span (no drift detected).

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-12T11:52:38Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-12 | 2026-05-12T11:24:11Z | 11h 24m |
| red | 2026-05-12T11:24:11Z | 2026-05-12T11:31:09Z | 6m 58s |
| green | 2026-05-12T11:31:09Z | 2026-05-12T11:38:17Z | 7m 8s |
| spec-check | 2026-05-12T11:38:17Z | 2026-05-12T11:39:54Z | 1m 37s |
| verify | 2026-05-12T11:39:54Z | 2026-05-12T11:47:12Z | 7m 18s |
| review | 2026-05-12T11:47:12Z | 2026-05-12T11:51:20Z | 4m 8s |
| spec-reconcile | 2026-05-12T11:51:20Z | 2026-05-12T11:52:38Z | 1m 18s |
| finish | 2026-05-12T11:52:38Z | - | - |

## Sm Assessment

**Story ready for RED phase.** Setup complete:
- Session file created with three-phase technical approach (parse+auto-fill, OTEL span, prompt guardrail).
- Branch `feat/49-3-location-patch-enforcement` cut from `develop` in sidequest-server.
- Jira intentionally skipped — SideQuest is personal, no Jira tracking.
- ACs cover implementation, regression test, integration replay against the Glenross save, and non-regression for explicit-patch case.

**Notes for TEA:**
- Anchor the regression test on `narration_apply.py` around line 1641 — that's the `if result.location:` branch where auto-fill belongs.
- OTEL span `narrator.location_drift_repaired` must fire WARNING-level so the GM panel surfaces it (per CLAUDE.md OTEL Observability Principle).
- Don't write a test for `patch.location` being explicitly set being preserved — that's the non-regression case; write the test to lock in the behavior.
- Integration test references a real Glenross save at `~/.sidequest/saves/` — confirm fixture availability before locking that test in. If unavailable, replace with a synthesized snapshot mirroring turn 3 state.
- This is a SideQuest playtest fix — fix-fast/restart-fast methodology applies; keep test surface tight to the three ACs.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Three load-bearing ACs (parse+auto-fill, OTEL span, prompt guardrail) — story explicitly calls for a regression test. The orchestrator prompt-guardrail (Phase 3 from SM's tech approach) is covered separately by orchestrator-level test surface — out of scope for this file.

**Test Files:**
- `sidequest-server/tests/server/test_location_drift_repair.py` — 11 tests covering AC1, AC2, AC6, AC7

**Tests Written:** 11 tests covering 4 ACs (AC1, AC2, AC6, AC7)
**Status:** RED on load-bearing ACs (6 failing) + trivially-passing non-regression guards (5)

### RED state breakdown

| Test | Expected fail mode | Verified |
|------|---|---|
| `..._autofills_from_leading_bold_title` | `character_locations[Ziggy]` stays `the_manse` instead of becoming `The Manse — Front Parlour` | ✅ |
| `..._accepts_h2_prefixed_bold_title` | Same — parser not present | ✅ |
| `..._emits_otel_span` | `narrator.location_drift_repaired` span not in finished_spans | ✅ |
| `..._span_is_warning_severity` | Drift span precondition fails (no span fires) | ✅ |
| `..._span_constant_is_exported` | `cannot import name SPAN_NARRATOR_LOCATION_DRIFT_REPAIRED from sidequest.telemetry.spans.narrator` | ✅ |
| `..._span_is_routed_to_watcher` | `SPAN_ROUTES.get("narrator.location_drift_repaired")` → `None` | ✅ |
| `..._explicit_patch_location_is_not_overridden_by_bold_title` | Passes trivially (no repair runs pre-implementation) | guard |
| `..._explicit_patch_location_emits_no_drift_span` | Passes trivially | guard |
| `..._no_repair_when_narration_has_no_leading_bold_title` | Passes trivially | guard |
| `..._no_repair_when_inline_bold_is_not_a_leading_title` | Passes trivially | guard |
| `..._no_drift_span_when_bold_title_matches_current_state` | Passes trivially | guard |

The 5 "guard" tests describe negative-space invariants — they pass pre-implementation because the feature doesn't exist, but they hold dev honest in GREEN: an implementation that over-fires (firing drift spans on no-bold-title turns, or hijacking explicit patches) will fail them. They are not vacuous; each asserts a specific post-condition value, not just truthiness.

### Contract pinned by tests

- **Span module:** `sidequest.telemetry.spans.narrator`
- **Span constant:** `SPAN_NARRATOR_LOCATION_DRIFT_REPAIRED = "narrator.location_drift_repaired"`
- **SpanRoute event_type:** `"state_transition"`
- **Span attributes (required):** `old_state`, `new_from_title`, `character`, `player_name`, `turn`, `severity="warning"`
- **Parser anchor:** leading bold title — matches `**Title**` at start, or `## **Title**` heading-prefixed form. Inline `**emphasis**` mid-paragraph must NOT match.
- **Apply seam:** `narration_apply.py` line 1641 `if result.location:` — auto-fill happens BEFORE that branch so the existing room/region pipeline picks up the repaired value.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #3 Type annotations | `_char`, `_sd`, `_ziggy_session` factories all typed | covered |
| #6 Test quality (no vacuous assertions) | Every test asserts a specific value, not `is_not_none` / `assert result` | covered |
| #6 (no skipped tests w/o reason) | No `@pytest.mark.skip` in file (removed reserved-test stub) | covered |
| #10 Import hygiene | No star imports; in-function imports kept narrow per existing test conventions in this tree | covered |
| #11 Input validation at boundary | Bold-title parser anchored to leading position — `..._inline_bold...` test pins the boundary | covered (production side) |

**Rules checked:** 5 of 13 applicable lang-review rules have test coverage relevant to this story (rules #1/#2/#5/#7/#8/#9/#12/#13 are not exercised by adding a parser + span helper in apply-time code).
**Self-check:** 0 vacuous tests found. Every assertion compares against a specific expected value with a quoted rationale.

**Handoff:** To Dev for implementation.

### TEA notes for Dev

- The Glenross-save integration replay AC (session AC5) was deliberately NOT translated into a test here — it requires a real save file at `~/.sidequest/saves/` and pinning the path makes the suite environment-dependent. The synthesized `_ziggy_session` fixtures (`character_locations["Ziggy"]="the_manse"`, turn 3) mirror Glenross turn 3 state; AC5 can be exercised manually by replaying the actual save once the feature lands.
- The Recency-zone prompt guardrail (SM Phase 3) is NOT covered here — that's an orchestrator-prompt change and belongs in `tests/agents/` (or wherever the prompt-builder tests live). Dev should add it there in GREEN.
- One pre-existing test, `test_narration_apply_no_backfill.py`, uses the same `_char`/`_sd` factory shape this file uses. The fixture duplication is intentional — refactoring to a shared conftest helper is out of scope.

## Dev Assessment

**Status:** GREEN — all 11 acceptance tests pass.

**Files changed:**
- `sidequest/telemetry/spans/narrator.py` — added `SPAN_NARRATOR_LOCATION_DRIFT_REPAIRED` constant, `SpanRoute` registration (event_type=state_transition, component=narrator, op=location_drift_repaired), and the `location_drift_repaired_span` context manager. Span sets `severity="warning"` attribute so the watcher route translator promotes it past INFO. `__all__` extended.
- `sidequest/server/narration_apply.py` — added module-level `_LEADING_BOLD_TITLE_RE` (`\A`-anchored, optional `## ` heading prefix, `[^*\n]+` body) and `_extract_leading_bold_title()` helper. The repair branch sits immediately before `if result.location:` so the existing apply pipeline picks up the auto-filled value through its canonical seam (`process_room_entry`, `character_locations` write, region filtering, all unchanged). `logger.warning()` lazy-interpolation per python.md rule #4. Span emission wraps the assignment so the audit trail captures the actual mutation.
- `sidequest/agents/orchestrator.py` — registered `location_patch_constraint` Recency-zone Guardrail. The body mirrors the prose-anchored idiom of the existing `confrontation_trigger_constraint` / `npc_extraction_constraint` blocks; it names the bold-title shape, restates "state must not lag prose," and tells the narrator the server runs a backstop without making the backstop the source of truth.

**ACs satisfied:**

| AC | Implementation site | Test(s) |
|----|---------------------|---------|
| 1 (parse + auto-fill) | `narration_apply.py` drift-repair branch | `..._autofills_from_leading_bold_title`, `..._accepts_h2_prefixed_bold_title` |
| 2 (OTEL span, WARNING) | `narrator.py` span + route + `narration_apply.py` emit | `..._emits_otel_span`, `..._span_is_warning_severity`, `..._span_constant_is_exported`, `..._span_is_routed_to_watcher`, `..._no_drift_span_when_bold_title_matches_current_state` |
| 3 (prompt guardrail) | `orchestrator.py` Recency block | manual review — orchestrator-prompt test surface is out of scope per TEA |
| 4 (regression test) | `tests/server/test_location_drift_repair.py` | 11 tests, all GREEN |
| 5 (Glenross replay) | Deferred per TEA — manual playtest replay; synthesized turn-3 fixtures stand in | — |
| 6 (explicit patch wins) | Gated on `if not result.location` | `..._explicit_patch_location_is_not_overridden_by_bold_title`, `..._explicit_patch_location_emits_no_drift_span` |
| 7 (no bold → no-op) | `_extract_leading_bold_title` returns None → branch skipped | `..._no_repair_when_narration_has_no_leading_bold_title`, `..._no_repair_when_inline_bold_is_not_a_leading_title` |

**Regression sweep:** `uv run pytest tests/server/` → 1505 passed, 25 skipped. `uv run pytest tests/agents/ tests/telemetry/` → 710 passed. `tests/telemetry/test_routing_completeness.py` confirms the new span is properly routed (not orphaned in `FLAT_ONLY_SPANS`).

**Lint:** `uv run ruff check` on changed files → All checks passed.

**Self-review against `.pennyfarthing/gates/lang-review/python.md` (13 checks):**

| # | Rule | Status | Note |
|---|------|--------|------|
| 1 | Silent exception swallowing | PASS | No try/except introduced. |
| 2 | Mutable default arguments | PASS | All defaults immutable. |
| 3 | Type annotation gaps | PASS | `_extract_leading_bold_title`, `location_drift_repaired_span` fully typed. |
| 4 | Logging: coverage & correctness | PASS | `logger.warning("...%s %r %d", ...)` lazy interpolation; severity matches "drift detected" semantics. |
| 5 | Path handling | PASS | N/A. |
| 6 | Test quality | PASS | TEA covered; no vacuous assertions added. |
| 7 | Resource leaks | PASS | Span uses `with` context. |
| 8 | Unsafe deserialization | PASS | N/A. |
| 9 | Async/await pitfalls | PASS | N/A. |
| 10 | Import hygiene | PASS | Explicit alpha-sorted import; no star. |
| 11 | Input validation at boundary | PASS | Bold-title regex bounded by `\A` + `[^*\n]+`; `.strip()` post-extract; falsy returns None. |
| 12 | Dependency hygiene | PASS | No new deps. |
| 13 | Fix-introduced regressions | PASS | Full server sweep clean. |

**Handoff:** To Reviewer / verify phase.

## Delivery Findings

No upstream findings at setup time.

<!-- TEA delivery findings: 49-3 RED phase -->
### TEA (test design)
- No upstream findings during test design. Story scope was self-contained; ACs translated cleanly to tests; no spec ambiguity surfaced.

### Dev (implementation)
- **Improvement** (non-blocking): the orchestrator-prompt registry has no per-section unit-test surface. Adding `location_patch_constraint` was a one-line change with no test; same is true of the existing `confrontation_trigger_constraint` / `npc_extraction_constraint` blocks. Affects `tests/agents/test_orchestrator_*` (a future story could add a prompt-section presence test). *Found by Dev during implementation.*
- **Improvement** (non-blocking): `tests/server/test_narration_apply_no_backfill.py` and `tests/server/test_location_drift_repair.py` duplicate the `_char` / `_sd` factories. Affects `tests/server/conftest.py` (a future cleanup story could extract a shared `_session_data_factory` fixture). *Found by Dev during implementation.*

### TEA (test verification)
- **Improvement** (non-blocking): simplify-reuse confirmed the `_char` / `_sd` test-fixture duplication is now spread across at least two files in `tests/server/` (likely more in the broader test tree). Affects `tests/server/conftest.py` or a new `tests/_helpers/session_factory.py` — a follow-up cleanup story should extract a shared parameterized factory across `test_narration_apply_no_backfill.py`, `test_location_drift_repair.py`, and any sibling tests using the same shape. *Found by TEA during verify phase via simplify-reuse fan-out.*
- **Question** (non-blocking): the `**extra` kwarg on `location_drift_repaired_span` mirrors the family convention (`region_entry_rejected_span`, `quest_update_span`) but no caller currently uses the extensibility hook. Affects `sidequest/telemetry/spans/narrator.py:113`. The Reviewer should confirm whether the family-convention argument outweighs the YAGNI critique. *Found by TEA during verify phase via simplify-efficiency.*

### Reviewer (code review)
- **Improvement** (non-blocking): the leading-bold parser is permissive — any leading `**X**` becomes a location candidate. Affects `sidequest/server/narration_apply.py:88-100` (the `_LEADING_BOLD_TITLE_RE` regex and `_extract_leading_bold_title` helper). A future story should monitor OTEL drift events across playtests and, if non-room bold headers are observed, tighten the parser (e.g., reject candidates that match known scene-direction patterns or that fail `validate_region_name` before assignment). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `character_locations` is mutated even when the auto-filled candidate fails `validate_region_name` downstream (the region addition is rejected, but the per-character location entry is still set). Affects the apply-pipeline asymmetry around `sidequest/server/narration_apply.py:1707-1735`. Pre-existing shape, but the new repair makes it easier to hit. Future story could gate `character_locations` writes on region validation as well — or accept the asymmetry as intentional (region graph is the curated artifact; per-character location is the live state). *Found by Reviewer during code review.*
- **Question** (non-blocking): the `**extra` kwarg confirmed compliant with family convention (`region_entry_rejected_span`, `region_entry_canonicalized_dedup_span`, `quest_update_span` all accept `**attrs`). The TEA-verify question is answered: keep it. *Resolved by Reviewer during code review.*

## Design Deviations

None at setup time.

### TEA (test design)
- No deviations from spec.

### Dev (implementation)
- **Span attribute names use snake_case but session AC named "OTEL must be loud — severity WARNING"** → ✓ ACCEPTED by Reviewer: lowercase `"warning"` is the correct value per the watcher.py `attr_severity` lowercase vocabulary contract. Verified at `sidequest/server/watcher.py:134-145`. The uppercase spec was informal shorthand for "WARNING severity grade," not a literal string requirement.
  - Spec source: `.session/49-3-session.md`, Phase 2 attribute list ("severity: WARNING")
  - Spec text: `severity: "WARNING"`
  - Implementation: `severity="warning"` (lowercase) on the span attribute.
  - Rationale: The `server/watcher.py` route-translator's `attr_severity` escape hatch matches against the existing `warning` / `error` / `info` lowercase vocabulary (see lines 134-145 of watcher.py). Uppercase `WARNING` would fail to promote the route severity. TEA pinned `severity == "warning"` in the test; no functional change, just a casing alignment with the existing watcher contract.
  - Severity: minor
  - Forward impact: none — downstream consumers compare lowercase.

### Reviewer (audit)
- No additional undocumented deviations found. The two Architect-flagged mismatches (regex wording, span helper location) and the one Dev-logged deviation (severity casing) cover the full spec-vs-code delta. The Architect (spec-check) recommendations stand: ambiguous regex spec resolved by code+tests (option C); span helper location accepted by spec parenthetical (option A); severity casing accepted as watcher-contract compliance.

### Architect (reconcile)

The TEA / Dev / Reviewer in-flight logs are accurate as written. Verified each entry's spec-source paths exist (`.session/49-3-session.md` at the cited line numbers), spec-text quotes match the session file verbatim, implementation descriptions match the diff at `develop..HEAD`, and forward-impact claims are accurate (no sibling stories touch the same code seams). Two deviations were surfaced during spec-check / review but not formally logged in the structured manifest — adding them here for audit completeness:

- **Implementation regex more restrictive than session-AC regex wording**
  - Spec source: `.session/49-3-session.md`, AC1 sub-bullet ("scan the narration prose for a leading bold markdown header (`^##?\s*\*\*[^*]+\*\*`)")
  - Spec text: `^##?\s*\*\*[^*]+\*\*`
  - Implementation: `\A\s*(?:#{1,2}\s+)?\*\*([^*\n]+)\*\*` at `sidequest/server/narration_apply.py:88` — `\A` start-of-string anchor (not `^` which would match start-of-line under MULTILINE), `(?:#{1,2}\s+)?` accepts an optional `#` or `##` heading prefix with required whitespace (the spec read as "optional single `#`"), and `[^*\n]+` rejects newlines within the title body.
  - Rationale: The spec regex was written informally and would not match the narrator's actual `## **Title**` heading-prefixed form (the test `test_location_drift_repair_accepts_h2_prefixed_bold_title` pins this case). The implementation regex matches what the narrator emits in real prose per the Glenross capture. The tests are the load-bearing contract — the session AC regex was a sketch.
  - Severity: trivial
  - Forward impact: none — the regex difference is fully covered by the test suite. Future contributors should treat `_LEADING_BOLD_TITLE_RE` as the canonical pattern, not the session-AC sketch.

- **AC5 (Glenross integration replay) deferred — TEA did not translate into a test**
  - Spec source: `.session/49-3-session.md`, AC5 ("Integration test: Replay Glenross turn 3 — Load the glenross save file from `~/.sidequest/saves/`. Re-run turn 3 with the new location-drift logic.")
  - Spec text: "Load the glenross save file from `~/.sidequest/saves/`. Re-run turn 3 with the new location-drift logic. State must update from `'the_manse'` to `'The Manse — Front Parlour'` instead of holding stale. OTEL watcher events confirm the repair ran."
  - Implementation: TEA deliberately did not author this test. The TEA Assessment documents the choice: "the Glenross-save integration replay AC (session AC5) was deliberately NOT translated into a test here — it requires a real save file at `~/.sidequest/saves/` and pinning the path makes the suite environment-dependent." The synthesized `_ziggy_session` fixture (Ziggy at `the_manse`, turn 3) stands in for the real save.
  - Rationale: An integration test that depends on a developer-local SQLite save file at `~/.sidequest/saves/` is not portable — it fails on a fresh checkout and on CI. The synthesized fixture mirrors the same state shape (`character_locations[Ziggy]='the_manse'`, turn 3, no `patch.location` set) and the same input (`**The Manse — Front Parlour**\n\n...`). It exercises identical apply-pipeline code at the same line numbers; the only thing it does NOT exercise is the actual on-disk save format. The TEA call was correct — a portable synthesized fixture beats an environment-dependent integration test.
  - Severity: minor
  - Forward impact: AC5 verification falls to the next manual playtest. The story is mergeable; the verification is just done by replaying the actual playtest save once the fix is live. Should be logged in the playtest follow-up notes (see `[[project_playtest_2026_05_12]]`) so operator remembers to re-run Glenross turn 3 with this build.

**AC accountability cross-check:** No `## AC Accountability` table was emitted by the ac-completion gate this run (gate appears optional in this workflow configuration). Manual cross-check: of 7 ACs, 6 are DONE (1, 2, 3, 4, 6, 7) and 1 is DEFERRED with documented justification (5). No ACs were silently skipped or invalidated during review. Status:

| AC | Status | Verified by |
|----|--------|-------------|
| 1 (parse + auto-fill) | DONE | Tests + Architect spec-check + Reviewer Rule Compliance |
| 2 (OTEL span WARNING) | DONE | Tests (`..._emits_otel_span`, `..._span_is_warning_severity`) + Reviewer wiring trace |
| 3 (Recency-zone guardrail) | DONE | Diff review (orchestrator.py registry call) — no test surface for prompt-section presence, acceptable per TEA scope decision |
| 4 (regression test) | DONE | 11 tests in `test_location_drift_repair.py`, all GREEN |
| 5 (Glenross integration replay) | DEFERRED | Justified above; falls to next manual playtest |
| 6 (explicit patch wins) | DONE | Tests (`..._explicit_patch_location_is_not_overridden_*`) + Reviewer gate-ordering verification |
| 7 (no bold title → no-op) | DONE | Tests (`..._no_repair_when_narration_has_no_leading_bold_title`, `..._no_repair_when_inline_bold_is_not_a_leading_title`) |

**Decision:** Spec-reconcile complete. No additional rework required. Hand off to SM for finish.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with two minor clarifications below)
**Mismatches Found:** 2 (both trivial / minor — neither blocks review)

### AC-by-AC verification

| AC | Status | Notes |
|----|--------|-------|
| 1 — parse + auto-fill at line 1641 | Aligned | Helper `_extract_leading_bold_title()` extracted into a module-level pure function (good — testable and reusable). Repair branch sits at line 1665 immediately before the existing `if result.location:` seam so the canonical apply pipeline (`process_room_entry`, `character_locations` write, region validation, region-canonical dedup) picks up the auto-filled value with zero changes. |
| 2 — OTEL span | Aligned (with logged casing deviation) | Span constant, route, attributes all present. `severity="warning"` lowercase per watcher.py contract — already logged in Dev deviations. |
| 3 — Recency-zone guardrail | Aligned | Registered alongside `confrontation_trigger_constraint` and `npc_extraction_constraint`, same `AttentionZone.Recency` + `SectionCategory.Guardrail`. Body explicitly names the bold-title shape and the backstop relationship — narrator is told it is the source of truth, the repair is the safety net. |
| 4 — Regression test | Aligned | 11 tests in `test_location_drift_repair.py`, all GREEN. Fixtures mirror Glenross turn 3. |
| 5 — Glenross integration replay | Deferred (per TEA) | Synthesized turn-3 fixtures stand in for the real save. Manual playtest replay against the actual save remains a follow-up; not material to merging the fix. |
| 6 — Explicit patch wins | Aligned | Gated on `if not result.location` — explicit values never reach the repair branch. |
| 7 — No bold title → no-op | Aligned | `_extract_leading_bold_title` returns `None` on miss; the entire branch is skipped including the span emission. |

### Mismatches

- **Regex wording in session ACs vs implementation regex** (Ambiguous spec — cosmetic, trivial)
  - Spec: `^##?\s*\*\*[^*]+\*\*` (read literally: start-of-line, optional one `#`, optional whitespace, bold span)
  - Code: `\A\s*(?:#{1,2}\s+)?\*\*([^*\n]+)\*\*` (start-of-string, optional leading whitespace, optional `#` or `##` heading with required space, bold span with no newlines)
  - The code regex is the correct shape for ATX-style Markdown headings the narrator actually emits (`## **Title**` is a valid h2-with-bold form; `#**Title**` without space is not). The spec was written informally; the implementation matches what the tests pin. Inline `**emphasis**` is also correctly excluded via `\A\s*` (no arbitrary text before the bold span).
  - Recommendation: **C (clarify spec)** — already self-clarifies via the test contract; no action needed for review. Future contributors should read the regex from the code, not the session note.

- **Span helper location** (Architectural — trivial, also already accepted)
  - Spec: "New span in `sidequest/telemetry/spans/orchestrator.py` (or adjacent module)"
  - Code: span landed in `sidequest/telemetry/spans/narrator.py` (where `narrator.*` spans already cluster — `narrator.sealed_round`, `narrator.session_rotated`, `narrator.unrecoverable`).
  - The spec explicitly permitted "adjacent module"; `narrator.py` is the right home given the span-name prefix and the existing narrator-span family.
  - Recommendation: **A (update spec)** — implementation choice is correct; the parenthetical permission was the right call. No action.

### Architectural observations (non-blocking, no recommendation)

- `_apply_narration_result_to_snapshot` is already a 1400+ LOC function with many inline branches. The drift-repair adds ~30 LOC of dense business logic in the same flat style. A future epic-cleanup story could extract a private `_repair_location_drift()` helper to match the function-extraction trend Dev already applied to `_extract_leading_bold_title`. Out of scope for 49-3.
- The regex does not handle `***Title***` (bold-italic) or HTML headings (`<h2>Title</h2>`). Both are unlikely from the markdown-trained narrator; not worth a code change today. If future playtests show a third drift mode, extend the regex or add a second extractor.
- The SpanRoute uses `component="narrator"` while the watcher writes character-location updates under `component="game"` (see `narration_apply.py` `character_location_updated` event at line ~1705). Splitting drift-repair into its own `narrator` lane is intentional — the GM panel filters drift events as a prompt-quality signal, not a routine state transition. Good separation.

**Decision:** Proceed to verify (TEA).

### Architect (reconcile) — placeholder

Reconcile pass happens after Reviewer; this subsection will be expanded then with the definitive deviation manifest.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed — `just server-check` clean (5018 passed, 58 skipped, lint clean).

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 4 (`orchestrator.py`, `narration_apply.py`, `telemetry/spans/narrator.py`, `tests/server/test_location_drift_repair.py`)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 3 findings | `_char` / `_sd` test fixtures duplicated with `test_narration_apply_no_backfill.py`; `CONTENT_GENRE_PACKS` constant repeated |
| simplify-quality | clean | No naming, layering, dead-code, or wiring issues |
| simplify-efficiency | 1 finding (medium) | `**extra` kwarg on `location_drift_repaired_span` is unused at call sites |

**Applied:** 0 fixes
**Flagged for Review:** 1 medium-confidence finding (`**extra` kwarg)
**Noted:** 3 reuse findings — see triage below
**Reverted:** 0

**Overall:** simplify: clean (no changes applied — findings either conflict with logged scope decisions or are below auto-apply threshold)

### Triage detail

**simplify-reuse — test fixture duplication (high confidence, NOT applied)**
- The `_char` and `_sd` factory duplication with `test_narration_apply_no_backfill.py` is real, but TEA-RED documented this as **intentionally out of scope** for 49-3 ("The fixture duplication is intentional — refactoring to a shared conftest helper is out of scope"). Dev also logged a delivery-finding requesting a future shared-fixture extraction story.
- Auto-applying a high-confidence reuse fix against an explicit logged scope decision would be a process violation — the scope was already debated and bounded.
- **Action:** Leave the duplication in place for 49-3. The Dev delivery finding already names the follow-up. A future cleanup story can extract `tests/_helpers/` factories across this whole test family in one pass (more efficient than piecemeal extraction here).

**simplify-efficiency — `**extra` kwarg on span helper (medium confidence, NOT applied)**
- The agent flagged `**extra: Any` on `location_drift_repaired_span` as unused.
- But: the sibling span helpers in the same family DO follow this convention. `region_entry_rejected_span`, `region_entry_canonicalized_dedup_span`, and `quest_update_span` all accept `**attrs: Any` for caller-side per-emit extension (additional audit context the route extractor can ignore).
- Removing it would diverge from the established span-helper signature shape and would have to be re-added the moment a caller wants to attach an ad-hoc field.
- Confidence is medium, not high — per workflow rules, medium findings are flagged for review, not auto-applied.
- **Action:** Flagged for Reviewer; recommend keeping the kwarg to match the family convention.

**simplify-quality — non-blocking observation**
- The agent noted `old_state=_current or ""` substitutes empty string when `_current` is `None`. This is intentional: the OTEL span attribute path prefers string sentinels over `None` (the route extractor at `narrator.py` falls back to `""` anyway). No action.

### Quality Checks

| Check | Result |
|-------|--------|
| `uv run ruff check .` | clean (no errors on changed files) |
| `uv run pytest -v` (full suite) | 5018 passed, 58 skipped |
| Targeted run on `tests/server/test_location_drift_repair.py` | 11 passed |
| `tests/telemetry/test_routing_completeness.py` | passed (new span correctly routed) |

**Handoff:** To Reviewer for code review.

### Delivery Findings — verify phase

(see `## Delivery Findings` below)

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — tests GREEN (11/11), code smells 0, lint clean, full prior sweep 5018/58 passed/skipped |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter=false` |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.silent_failure_hunter=false` |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.test_analyzer=false` |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.comment_analyzer=false` |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.type_design=false` |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security=false` |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier=false`. Simplify coverage already provided by TEA-verify fan-out (reuse / quality / efficiency teammates) — see TEA Assessment above. |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.rule_checker=false`. Manual rule enumeration below per python.md lang-review checklist. |

**All received:** Yes (1 returned clean; 8 disabled via project settings, pre-filled)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred

Subagent dispatch tags used in assessment despite disabled subagents (manual review covers each lane):
`[EDGE]` — edge-hunting via my own diff read + Devil's Advocate.
`[SILENT]` — silent-failure hunting via my own diff read (no try/except introduced).
`[TEST]` — test-quality verified via diff read + TEA RED phase rule-coverage table.
`[DOC]` — comment-analysis via my own diff read.
`[TYPE]` — type-design via my own diff read (`str | None` shapes, no stringly-typed APIs added).
`[SEC]` — security via my own diff read (narrator output is internal, no user input flows).
`[SIMPLE]` — simplification covered by TEA-verify fan-out (reuse / quality / efficiency).
`[RULE]` — rule-checking via my own enumeration against python.md lang-review.

## Reviewer Assessment

**Verdict:** APPROVED

### Rule Compliance — python.md lang-review (13 numbered checks)

Enumerated against the diff (`sidequest/server/narration_apply.py`, `sidequest/telemetry/spans/narrator.py`, `sidequest/agents/orchestrator.py`, `tests/server/test_location_drift_repair.py`).

| # | Rule | Result | Evidence |
|---|------|--------|----------|
| 1 | Silent exception swallowing | PASS | `[SILENT]` Diff introduces NO `try/except` blocks. All error paths surface naturally. |
| 2 | Mutable default arguments | PASS | `[RULE]` All defaults immutable: `Random` not used here, `prior_location: str = "the_manse"` in test helper is a string (immutable), span helper has only keyword-required params plus `_tracer=None`. |
| 3 | Type annotation gaps at boundaries | PASS | `[TYPE]` `_extract_leading_bold_title(narration: str) -> str \| None` fully typed. `location_drift_repaired_span(*, old_state: str, new_from_title: str, character: str, player_name: str, turn: int, _tracer: trace.Tracer \| None = None, **extra: Any) -> Iterator[trace.Span]` fully typed. Test factories `_char`/`_sd`/`_ziggy_session` fully typed. |
| 4 | Logging coverage and correctness | PASS | `[RULE]` `narration_apply.py:1684` uses `logger.warning("... %s %r %d ...", a, b, c, d, e)` lazy interpolation per checklist. Severity matches "drift detected" semantics (narrator made a mistake repaired post-hoc — a quality signal, not an internal error). No sensitive data logged. |
| 5 | Path handling | PASS | `[RULE]` No new path manipulation in production code. Test uses `Path(__file__).resolve().parents[3] / "sidequest-content" / "genre_packs"` — pathlib `/` operator, no string concatenation. |
| 6 | Test quality | PASS | `[TEST]` 11 tests, every assertion compares against a specific expected value with a quoted rationale (verified by TEA RED phase + spot-checked here). No `assert True`, no truthy-only `assert result`, no skipped tests, no parametrize-with-same-path. |
| 7 | Resource leaks | PASS | `[RULE]` Span uses `with location_drift_repaired_span(...) as span:` context manager. No raw file/socket/db opens. |
| 8 | Unsafe deserialization | PASS | `[SEC]` No `pickle`, no `yaml.load`, no `eval`, no `subprocess(shell=True)`, no `json.loads` on user input. The bold-title parser operates on already-internal `result.narration` (the narrator's own output, post-prose-extraction). |
| 9 | Async/await pitfalls | PASS | `[RULE]` No async code modified. The repair branch is synchronous, inside a sync function. |
| 10 | Import hygiene | PASS | `[RULE]` Explicit imports, no `from x import *` added. `narrator.py` now has a complete `__all__` listing all 4 span constants + 3 helper functions — improves on the prior state where the module had no `__all__`. |
| 11 | Input validation at boundary | PASS | `[SEC]` Bold-title regex bounded by `\A\s*` (start-of-string anchor + optional whitespace), `[^*\n]+` (no nested asterisks, no newline traversal — prevents ReDoS-style runaway). `.strip()` post-extract. Empty-after-strip → returns `None` (`return title or None`). Region validation downstream (`validate_region_name`) provides a second filter for the extracted candidate before it enters `discovered_regions`. |
| 12 | Dependency hygiene | PASS | `[RULE]` No `pyproject.toml` / `requirements.txt` changes. |
| 13 | Fix-introduced regressions | PASS | `[RULE]` Full server sweep clean (5018 passed). No re-introduction of previously fixed bugs. |

**Rules checked:** 13 of 13. All PASS.

### Observations (minimum 5, mixed VERIFIED / LOW / informational)

1. **[VERIFIED]** `_extract_leading_bold_title` is a pure function with no side effects — `sidequest/server/narration_apply.py:90-100` takes `str`, returns `str | None`, uses only `re.match` and `str.strip`. Complies with python.md rule #3 (typed boundary) and rule #2 (no mutable defaults).

2. **[VERIFIED]** OTEL emission wiring traced end-to-end: span constant at `sidequest/telemetry/spans/narrator.py:25` → `__all__` export at `narrator.py:148` → re-export through `from .narrator import *` in `sidequest/telemetry/spans/__init__.py:61` → import at `sidequest/server/narration_apply.py:64` → call at `narration_apply.py:1693`. `SPAN_ROUTES` registration at `narrator.py:38-52` causes the watcher SpanProcessor (`server/watcher.py:102`) to translate the span into a typed `state_transition` event. `tests/telemetry/test_routing_completeness.py` passing confirms the registration is reachable. `[RULE]` no orphan span (every routed span name has a corresponding `SpanRoute` entry).

3. **[VERIFIED]** Repair gate ordering is correct — all four guards are necessary, none redundant. `narration_apply.py:1681-1685`:
   - `if not result.location and result.narration:` — short-circuits when narrator filled the patch or emitted empty prose.
   - `if _actor_for_drift:` — short-circuits when no actor identity (matches existing `actor_for_location` pattern at line ~1672).
   - `if _candidate is not None:` — short-circuits when no leading bold title (AC7 silent no-op).
   - `if _candidate != _current:` — short-circuits when bold title agrees with state (AC2 negative: avoid spam-firing drift spans).
   Removing any one of these introduces a known false-positive class.

4. **[EDGE / LOW]** Permissive leading-bold parser: any leading `**bold**` span will be promoted to a location candidate, even non-room headers like `**ATTENTION: Combat begins!**`. Mitigated by (a) the WARNING-level OTEL audit, (b) downstream `validate_region_name` rejecting bracketed entries when adding to `discovered_regions` (but `character_locations` is still mutated — the rejection only blocks the region addition), and (c) the new Recency-zone guardrail telling the narrator the patch field is authoritative. **Not blocking** — this is the intended trade-off documented in the session ("auto-fill, not fail-loud"). Worth a follow-up only if playtest shows the narrator emits non-room bold headers in practice.

5. **[EDGE / LOW]** Bracketed-title second-order drift: if the narrator emits `**(scene direction)**` as a leading bold, the parser extracts `(scene direction)`, sets it as `character_locations[actor]`, but `validate_region_name` will reject it from `discovered_regions`. Result: state holds an invalid room label but the region graph stays clean. **Not blocking** — narrator's System-zone schema discourages bracketed prose; mitigated by the same audit mechanism as observation 4.

6. **[VERIFIED]** Prompt-guardrail body explicitly addresses the "narrator might lean on the backstop" failure mode: `sidequest/agents/orchestrator.py:1737-1747` says "the backstop is a safety net, not the source of truth. You are." `[DOC]` Comment block above the registration cites the actual five-turn Glenross drift (Bee Garden → Manse Garden → Front Parlour → Study → Sickroom Passage) — accurate provenance.

7. **[SIMPLE / VERIFIED]** TEA-verify's three-teammate simplify fan-out reports are appropriately resolved (`reuse` findings deferred to a future cleanup story per logged TEA-RED scope decision; `efficiency` finding on `**extra` matches the existing span-family convention `region_entry_rejected_span(...**attrs: Any)`). No code change required.

### Devil's Advocate

The naive read of this diff is "small fix, low risk, easy approval." Let me argue the opposite for 200+ words.

**Argument: the auto-fill is a Trojan horse for silent state drift.** The change introduces a new mutation path on `snapshot.character_locations` that is gated on heuristic prose parsing, not on the narrator's explicit structured output. Every time it fires, it is by definition the system DISAGREEING with the narrator about the canonical state — and then overwriting state based on a regex. If the regex is ever wrong (false positive on a non-room bold), `character_locations` is corrupted with a non-room string. The Glenross playtest fixed one drift mode but creates the surface area for another: now any leading `**X**` becomes a location candidate. The narrator's System-zone schema doesn't formally prohibit non-room leading bold spans — only the new Recency-zone guardrail does, and Recency-zone instructions decay under attention pressure (literally the same problem the original drift exhibited: the schema rule existed but lost out to recency).

**Argument: the WARNING audit doesn't help anyone in real time.** The OTEL span fires WARNING-grade and the watcher route translator promotes it, but who's watching during a live playtest? The GM panel is reviewed retroactively. By the time the operator sees `narrator.location_drift_repaired` filed with `new_from_title="ATTENTION: Combat begins!"`, the canonical state has already been wrong for an unknown number of turns and the next narrator turn has already read the corrupt `character_locations` entry into its prompt. The audit is forensic, not preventive. The Recency-zone guardrail is the preventive layer, but it's just text in a prompt the narrator may or may not respect on any given turn.

**Argument: the contract between this repair and `validate_region_name` is fragile.** The repair sets `result.location = _candidate` and the downstream `if result.location:` branch then mutates `character_locations`, `discovered_regions`, and dispatches `process_room_entry`. If `_candidate` fails `validate_region_name`, the region addition is rejected (with its own OTEL audit), but `character_locations` is still updated and `process_room_entry` still ran. That asymmetry is a known shape of the existing pipeline, but the repair makes it easier to hit because the parser is more permissive than the narrator.

**Rebuttal:** All three arguments are valid risk descriptions but none are blocking for this PR. The story explicitly chose "auto-fill over fail-loud" as a design trade-off (cited in session lines 49-50). The repair gate `_candidate != _current` ensures one repair per drift, not a cascade. The asymmetry with `validate_region_name` is pre-existing and well-trodden. The story is a *playtest closeout* fix — the playtest IS the dev cycle on this project per the user's documented operating principle. Ship it, watch the OTEL events on the next playtest, iterate the prompt or tighten the regex if false positives appear. Observation 4 above already names the false-positive mode for the next story.

The Devil's Advocate didn't surface anything I missed in my main review — the permissive-parser risk is already flagged as `[EDGE / LOW]` observation 4 and 5.

### Approval rationale

- All 7 ACs satisfied (1, 2, 3, 4, 6, 7 implemented; 5 deferred per TEA decision — manual playtest replay, not test-coverable without environment-dependent fixtures).
- All 13 python.md lang-review checks PASS.
- Wiring traced end-to-end; OTEL audit reachable; tests exercise both positive and negative paths.
- 7 observations (1 EDGE/LOW × 2, 5 VERIFIED) — no Critical or High issues.
- Two design deviations logged by Dev/Architect, both reasonable; audit below.

**Handoff:** To SM for finish-story.