---
story_id: "77-1"
jira_key: ""
epic: "77"
workflow: "tdd"
---

# Story 77-1: Seed-at-creation — quest_anchor + quest_log + active_stakes from PC drive/calling

## Story Details

- **ID:** 77-1
- **Jira Key:** (none — Jira disabled)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** server

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-03T02:21:33Z
**Round-Trip Count:** 1

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-02T00:00:00Z | 2026-06-03T01:35:57Z | 25h 35m |
| red | 2026-06-03T01:35:57Z | 2026-06-03T01:44:45Z | 8m 48s |
| green | 2026-06-03T01:44:45Z | 2026-06-03T01:55:08Z | 10m 23s |
| spec-check | 2026-06-03T01:55:08Z | 2026-06-03T01:56:28Z | 1m 20s |
| verify | 2026-06-03T01:56:28Z | 2026-06-03T01:59:35Z | 3m 7s |
| review | 2026-06-03T01:59:35Z | 2026-06-03T02:06:13Z | 6m 38s |
| red | 2026-06-03T02:06:13Z | 2026-06-03T02:09:15Z | 3m 2s |
| green | 2026-06-03T02:09:15Z | 2026-06-03T02:13:16Z | 4m 1s |
| spec-check | 2026-06-03T02:13:16Z | 2026-06-03T02:14:06Z | 50s |
| verify | 2026-06-03T02:14:06Z | 2026-06-03T02:16:13Z | 2m 7s |
| review | 2026-06-03T02:16:13Z | 2026-06-03T02:20:30Z | 4m 17s |
| spec-reconcile | 2026-06-03T02:20:30Z | 2026-06-03T02:21:33Z | 1m 3s |
| finish | 2026-06-03T02:21:33Z | - | - |

## Sm Assessment

**Setup Complete:** Yes
**Session file:** `.session/77-1-session.md` (this file)
**Story context:** `sprint/context/context-story-77-1.md` (committed, schema-valid — Business Context, Technical Guardrails, Scope Boundaries, AC Context + Assumptions)
**Branch:** `feat/77-1-seed-quest-spine-at-creation` (created off `sidequest-server` develop tip, incl. PR #585)
**Status:** epic-77.yaml → in_progress
**Jira:** disabled for this project (no claim)

**Story scope:** Server-only. Seed the campaign spine at character creation — write `quest_log` + `quest_anchors` + `active_stakes` from the PC's drive/calling, plus the `quest.seeded_at_creation` OTEL span. Implements ADR-137 Option A.

**Load-bearing context flags for TEA/Dev (from the committed story context + ADR-137 review):**
- **Option A does NOT close the gap for prose-only packs.** `Character.drive` defaults to `""` (`character.py:117`) and is populated only for genres with a drive-shaped scene (`builder.py:423`). wry_whimsy — the pack that motivated epic 77 — has no drive scene, so seed-at-creation yields an empty seed there. **Option B (typed tools, story 77-2) is the load-bearing fix for prose packs.** AC-1 requires verifying behavior against a no-drive pack.
- **Empty-drive path must degrade LOUDLY** — emit `quest.seeded_at_creation` with a WARNING-severity attribute on empty seed (No Silent Fallbacks). AC-2. The exact attribute key/shape is not pinned by ADR-137; Dev chooses one consistent with how the GM panel reads severity and documents it.
- **Do not touch** the orbital consumer (`orbital/course.py`) — that's 77-3. Do not build the typed tools (77-2) or promote `quest_anchors` to `WorldStatePatch` (77-3) here.
- Story `acceptance_criteria` are guardrail-framed (2 ACs); the positive/happy path (populated drive → non-empty spine) is implied by ADR-137 Option A but not literal — TEA should assert it and confirm scope with SM if ambiguous.

**ID-reuse / finish hazard (logged):** id `77-1` was previously the `[DESIGN]` story (ADR-137), completed and archived at `sprint/archive/77-1-session.md` (commit `6b025d7`). At finish, `pf sprint story finish 77-1` will archive THIS session to the same path, overwriting that design archive — SM to preserve/rename the old one at finish.

**Handoff:** To TEA (Igor) for the RED phase.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New engine behavior (seed-at-creation quest spine + OTEL span). Not a chore bypass.

**Test Files:**
- `sidequest-server/tests/game/test_quest_seed.py` — behavior/unit tests for `seed_quest_spine` (fast, `otel_capture` span assertions).
- `sidequest-server/tests/server/test_chargen_quest_seed_wiring.py` — mandatory wiring test driving the **real** chargen-commit path (`_chargen_confirmation`), proving the seed fires in production, not just as a helper.

**Tests Written:** 13 tests covering 2 ACs + the happy/calling-label paths + an out-of-scope-span guard + span-constant wiring.
**Status:** RED (failing — ready for Dev), verified for the right reasons:
- `test_quest_seed.py` → ImportError on `sidequest.game.quest_seed` (module absent — canonical RED for a new module).
- `test_chargen_quest_seed_wiring.py::test_quest_seed_fires_on_real_chargen_commit` → AssertionError: drove the full chargen commit (PC materialized at grimvault) and **zero** `quest.seeded_at_creation` spans fired — the seed is not wired.

**Contract pinned for Dev (Ponder):**
- New module `sidequest/game/quest_seed.py` → `def seed_quest_spine(snapshot: GameSnapshot, character: Character) -> None`, mutates the snapshot in place. Seed source = `character.drive`, falling back to `character.calling_label`.
- Populated source → `quest_log` ≥1 entry, `quest_anchors` ≥1 anchor, `active_stakes` non-empty AND referencing the source text (the "kansas" assertion pins *derived-from-drive*, not a placeholder). Span `quest.seeded_at_creation` with `has_stakes=True`, non-empty `quest_id`/`anchor_id`, `source_drive`==source, `severity` != "warning".
- Empty source (both blank) → NO fabrication (all three fields stay empty) + exactly one span with `severity="warning"`, `has_stakes=False`, `source_drive=""`. Never silent.
- New span constant `SPAN_QUEST_SEEDED_AT_CREATION = "quest.seeded_at_creation"`, registered in `SPAN_ROUTES` and re-exported from `sidequest.telemetry.spans` (model on `state_patch.py`'s `SPAN_QUEST_UPDATE` route, per story context). Closest existing template: `quest_seed_span`/`SPAN_QUEST_SEED` in `telemetry/spans/dungeon_setpiece.py`.
- Wire seam: `chargen_mixin.py` `_chargen_confirmation`, right after `materialized.characters = [character]` (~line 790), mirroring the `seed_lore_from_char_creation` call pattern.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| No Silent Fallbacks (SOUL/CLAUDE — headline rule for this story) | `test_empty_drive_degrades_loudly_with_warning_span`, `test_empty_drive_path_is_never_silent` | failing |
| OTEL Observability (every subsystem decision emits a routed span) | `test_seeded_at_creation_span_constant_is_exported_and_routed`, `test_populated_drive_span_fires_without_warning` | failing |
| python #6 test-quality (meaningful assertions) | self-check pass — no `assert True`, no bare truthy-on-always-None, no `let _=` equivalents; every test asserts a specific value | n/a |
| Scope discipline (only the one span this story) | `test_seed_does_not_emit_out_of_scope_spans` (parametrized ×4) | failing |

**Rules checked:** No Silent Fallbacks + OTEL Observability are the load-bearing rules for this server feature; the python lang-review list is mostly impl-side (silent-except, mutable-default, resource-leak) and re-checked at Dev/verify on the real diff. **Self-check:** 0 vacuous tests.

**Handoff:** To Dev (Ponder Stibbons) for implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/quest_seed.py` — NEW. `seed_quest_spine(snapshot, character)`: seed source = `drive` → fallback `calling_label`; populated → writes `quest_log["seed_drive"]`, appends `quest_anchors` `"seed_drive_anchor"`, sets `active_stakes` = source, emits `quest.seeded_at_creation` (severity=info, has_stakes=True). Empty drive AND calling → no fabrication + one span with severity=warning, has_stakes=False (No Silent Fallbacks). Does not touch `WorldStatePatch` or `orbital/course.py` (77-3 scope).
- `sidequest-server/sidequest/telemetry/spans/state_patch.py` — added `SPAN_QUEST_SEEDED_AT_CREATION = "quest.seeded_at_creation"` + its `SpanRoute` (component `quest_log`, the GM-panel-surfaced route). The only span this story adds.
- `sidequest-server/sidequest/server/websocket_handlers/chargen_mixin.py` — import + call `seed_quest_spine(materialized, character)` in `_chargen_confirmation` right after `materialized.characters = [character]`, mirroring the `seed_lore_from_char_creation` pattern. Wired before `replace_with`, so the canonical snapshot carries the spine.
- `sidequest-server/tests/game/test_quest_seed.py` — ruff import-org + format (TEA's RED file).
- `sidequest-server/tests/server/test_chargen_quest_seed_wiring.py` — added `_pg_isolation` autouse fixture (per-worker migrated DB, truncated per test) so the wiring test always hits the first-commit/materialize path the seed seam lives on.

**Tests:** 14/14 passing (GREEN) — 13 behavior + 1 wiring. Full server suite: **9721 passed, 360 skipped, 1 pre-existing unrelated failure** (`tests/handlers/test_aside_channel_wiring.py::test_aside_is_out_of_band_in_mp` — ADR-107 aside path, fails in isolation, zero import-graph overlap with this story's 4-file diff; not caused by this change). Lint + format clean on all changed files.
**Branch:** `feat/77-1-seed-quest-spine-at-creation` (pushed: e0379ee5 + 1905b76d on top of the RED commit 6834d0d7)
**TEA contract:** followed faithfully — used `severity` as the warning attribute key exactly as TEA pinned (no counter-deviation needed); seed source drive→calling_label as specified; span/seam/fields all per the contract.

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

Independently re-checked both ACs against the diff (`quest_seed.py`, `state_patch.py`, `chargen_mixin.py`):
- **AC-1 (no-drive verified, not assumed; loud-degrade):** empty-source branch fabricates nothing and emits a `severity="warning"` `quest.seeded_at_creation` span. Covered by `test_empty_drive_does_not_fabricate_a_spine` + `test_empty_drive_degrades_loudly_with_warning_span`. ✓
- **AC-2 (empty→warning; mirror populated→3 fields, derived, ADR-137 contract attrs):** populated branch sets `quest_log`/`quest_anchors`/`active_stakes` from the source and emits an `info` span with `quest_id`/`anchor_id`/`source_drive`/`has_stakes`. ✓

**Reuse-first (pragmatic-restraint):** no new infrastructure — reuses existing `GameSnapshot` fields, the `SpanRoute`/`SPAN_ROUTES` pattern (modeled on `SPAN_QUEST_UPDATE`), and the `seed_lore_from_char_creation` chargen wire seam. `WorldStatePatch` and `orbital/course.py` correctly left untouched (77-3 scope). Exemplary "Wire Up What Exists."

**Ambiguity note:** ADR-137 did not pin the warning-marker attribute key; TEA pinned `severity` and Dev implemented it (logged as TEA deviation, Option C — clarify). No code change warranted; the key is GM-panel-consistent (matches `validator.py`'s `severity=` convention).

**Architectural watch-out for downstream (non-blocking, informational):** the seed uses fixed ids `seed_drive` / `seed_drive_anchor` and `active_stakes` = the raw drive string. When 77-2 (typed `record_quest`/`set_stakes`) and 77-3 (`quest_anchors` → `WorldStatePatch`) land, they must treat this seed entry as the pre-existing turn-0 row (update/supersede it, not duplicate). This is consistent with ADR-137's one-mechanism consolidation and needs no change here.

**Decision:** Proceed to review (TEA verify → Reviewer).

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (no code changed in verify; Dev's full-suite GREEN stands — 9721 passed)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5 (quest_seed.py, state_patch.py, chargen_mixin.py, test_quest_seed.py, test_chargen_quest_seed_wiring.py)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding | medium: extract a `quest_seeded_at_creation_span(...)` helper to match the `state_patch_hp_span`/`quest_update_span` precedent, deduping the two inline `Span.open(...)` blocks in `quest_seed.py` |
| simplify-quality | clean | naming/types/docstrings/error-handling all conform; no dead code; wiring tests present |
| simplify-efficiency | clean | lean implementation, no over-engineering or premature abstraction |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 medium-confidence finding (below)
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Flagged (medium) — for Reviewer judgment:** `quest_seed.py` inlines the `Span.open(SPAN_QUEST_SEEDED_AT_CREATION, {...})` attribute dict twice (empty-seed + populated branches). The telemetry/spans convention (`quest_update_span`, `state_patch_hp_span`, `dungeon_setpiece.quest_seed_span`) wraps span emission in a typed `@contextmanager` helper. Extracting `quest_seeded_at_creation_span(*, quest_id, anchor_id, source_drive, has_stakes, severity, _tracer=None)` into `state_patch.py` (beside the constant) and calling it from `quest_seed.py` would match the pattern and dedupe. **TEA judgment:** legitimate convention alignment, low-risk, but organizational not functional — not auto-applied per the medium-confidence rule. Granny may request it or accept as-is; the current code is correct, tested, and the attribute set is identical across both call sites.

**Quality Checks:** All passing (Dev full-suite run: 9721 passed, 360 skipped; 1 pre-existing unrelated aside-channel failure documented in Delivery Findings).
**Overall:** simplify: clean (0 applied; 1 medium flagged)

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | tests GREEN (14), ruff check clean, 1 pre-existing format reflow (unrelated), 1 content-gate skip (ok), 1 pre-existing unrelated failure | confirmed 0, dismissed 0 (mechanical only — clean), deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (1 enabled subagent returned; 8 disabled via `workflow.reviewer_subagents`, pre-filled Skipped)
**Total findings:** 1 confirmed (HIGH, found by Reviewer — preflight is mechanical and cannot catch behavior clobbers), 0 dismissed, 1 deferred (verify's medium reuse note)

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `seed_quest_spine` **unconditionally overwrites** `snapshot.active_stakes` with the PC's drive/calling, clobbering **world-authored opening stakes**. `materialize_from_genre_pack` runs first and sets `snap.active_stakes = chapter.active_stakes` (`world_materialization.py:315-316`) from the FRESH opening chapter; the seed at `chargen_mixin.py:798` then overwrites it. Confirmed active on live worlds whose opening chapter (`session_range:[1,5]`) authors `active_stakes` — **flickering_reach** (`mutant_wasteland/worlds/flickering_reach/history.yaml:107`, the canonical playtest world) and **annees_folles** (`pulp_noir/.../history.yaml:14`), among ~10 worlds. A player finishing chargen in flickering_reach loses the authored opening stake, replaced by e.g. "Active: Fighter". Violates SOUL "Diamonds and Coal" (authored detail) and "Crunch in Genre, Flavor in World" (world-authored content authority); feeds degraded state to ADR-024/025 pacing. | `sidequest/game/quest_seed.py:67` (`snapshot.active_stakes = source`) | **Fill, don't clobber.** Seed `active_stakes` (and the quest/anchor) only when the spine field is NOT already populated by world/chapter content. When the world already authored a spine, defer — and emit the span noting the deferral (observability) rather than silently skipping or overwriting. `quest_log` writes are additive (distinct `seed_drive` key) and safe, but should follow the same fill-not-clobber intent for consistency. |

**Why GREEN missed it:** the wiring test runs against `caverns_and_claudes`, which authors no opening `active_stakes`, so the clobber never triggered. A test against a world that DOES author opening stakes (e.g. flickering_reach) would have caught it.

### Observations

- [HIGH] active_stakes clobber of world-authored opening stakes — `quest_seed.py:67` (see table; measured against `world_materialization.py:315-316` + `flickering_reach/history.yaml:107`).
- [VERIFIED] `quest_log` seed is additive, not destructive — `quest_seed.py:64` writes the distinct key `seed_drive`; the chapter materializer writes named keys (`world_materialization.py:281`). No key collision. Complies with No-Silent-Fallbacks (no overwrite).
- [VERIFIED] Empty-drive loud-degrade is correct — `quest_seed.py:51-62` emits the `severity="warning"` span and fabricates nothing; satisfies AC-1/AC-2 and CLAUDE.md No Silent Fallbacks. Evidence: branch returns after the span with no field writes.
- [VERIFIED] Span is routed, not flat-only — `state_patch.py:47` registers `SPAN_QUEST_SEEDED_AT_CREATION` in `SPAN_ROUTES` (component `quest_log`); GM panel will surface it (OTEL Observability Principle). Attribute types (str/bool) are OTEL-valid.
- [VERIFIED] Scope discipline — no `WorldStatePatch` field added, `orbital/course.py` untouched (77-3 scope); only the one span added (77-2/77-3 spans absent). Evidence: diff is 3 prod files, none touching course.py or WorldStatePatch.
- [VERIFIED] Idempotent on re-fire — `quest_anchors.append` guarded by membership check (`quest_seed.py:65`); `active_stakes`/`quest_log` are assignments. No duplicate anchors if the seam ever fires twice. (Seam is first-commit-only, `chargen_mixin.py:730`.)
- [LOW] [SIMPLE] Inline `Span.open(...)` dict duplicated across both branches; the telemetry/spans convention wraps emission in a typed `@contextmanager` helper (`quest_update_span`, `state_patch_hp_span`). Non-blocking; carried from verify's medium reuse finding. Recommend extracting `quest_seeded_at_creation_span(...)` alongside the constant — fold into the HIGH-fix rework.
- [MEDIUM] [coverage] No test exercises the seed against a world that authors opening `active_stakes`; add one (the guard test for the HIGH fix doubles as this).

### Rule Compliance

- **No Silent Fallbacks (CLAUDE.md/SOUL):** empty-seed path is loud (warning span) ✓. BUT the clobber is its own violation of the inverse — it silently *replaces* authored state. The fix must defer-loudly (span-noted), not silently overwrite. — VIOLATION (the HIGH finding).
- **Diamonds and Coal / Crunch-in-Genre-Flavor-in-World (SOUL):** world-authored `active_stakes` is deliberate flavor/authored content; the seed must not overwrite it. — VIOLATION (the HIGH finding).
- **OTEL Observability (CLAUDE.md):** the one subsystem decision emits a routed span ✓ COMPLIANT (sharpen: the defer path should also emit, per the fix).
- **python #1 silent-exception / #2 mutable-default / #7 resource-leak:** none present in `quest_seed.py` — no try/except, no mutable defaults, no resources. COMPLIANT.
- **python #3 type annotations:** `seed_quest_spine(snapshot: GameSnapshot, character: Character) -> None` fully annotated. COMPLIANT.
- **python #6 test-quality:** assertions are specific (value checks, not bare truthy); no `assert True`. COMPLIANT.
- **No Source-Text Wiring Tests (server CLAUDE.md):** wiring test uses OTEL span assertion + real chargen drive, not source grep. COMPLIANT.

### Devil's Advocate

I argued the code is broken, and it is. The headline: this story exists to fill an EMPTY spine (the wry_whimsy/oz turn-13 failure where `active_stakes: ""`), but the implementation does not check whether the spine is empty before writing — it writes unconditionally. The motivating bug was *absence*; the fix introduces *overwrite*. On the very world the project treats as canonical for playtests (flickering_reach), the authored opening stake — a sentence of deliberate, atmosphere-setting flavor the world author wrote — is destroyed and replaced by a label as thin as "Active: Fighter" the instant a character is created. A career-GM playing (Keith) would notice the opening stakes evaporate. Worse, it's invisible: no error, no warning span on the overwrite path (the info span fires as if all is well), and the GREEN suite is blind to it because the test world happens not to author stakes — a textbook "convincing green with zero mechanical honesty" that the OTEL principle exists to prevent, here defeated because the clobber masquerades as a successful seed. A confused author would wonder why their authored stakes never appear in play. A malicious input angle is minor (drive is chargen-bounded label text already in the narrator surface — no new injection/size surface; runtime bounds are 77-2's job), so no Critical. But the authored-content clobber is a real High: it changes live behavior across ~10 worlds, degrades pacing input, and contradicts the story's own premise. The fix is small (fill-not-clobber guard + a preserving test + emit a defer span), which is exactly why it should be done now rather than shipped and discovered in a playtest.

**Handoff:** Back to Dev (via TEA rework — the fix is testable).

## TEA Assessment (rework red — RT1)

**Tests Required:** Yes — pin the Reviewer's HIGH fill-not-clobber finding.
**Tests Added:** 3 (in `tests/game/test_quest_seed.py`), all failing against the current clobbering code (RED, right reason):
- `test_world_authored_active_stakes_is_not_clobbered` — pre-set `snapshot.active_stakes` (as `materialize_from_genre_pack` does from the opening chapter), seed with a drive, assert the authored stakes are preserved (current code overwrites → fails).
- `test_authored_spine_skips_seed_quest_and_anchor` — authored spine present → seed adds no `seed_drive` quest/anchor (defers entirely; current code grafts one → fails).
- `test_defer_path_emits_one_non_warning_span` — defer is observable: exactly one `quest.seeded_at_creation` span, `severity != "warning"`, `has_stakes=True`, `source_drive=""` (distinguishes defer from seeded-from-drive and from empty-warning; current code reports `source_drive="Get home to Kansas"` → fails).

**Regression check:** the 13 prior tests still pass (they build fresh `GameSnapshot` with `active_stakes==""`, so they never hit the defer path). The fix is purely additive guarding.

**Contract pinned for Dev (the fix):** in `seed_quest_spine`, BEFORE the source/empty logic, check whether the spine is already authored — `snapshot.active_stakes.strip()` non-empty. If so, **defer**: write nothing (preserve `active_stakes`, add no quest/anchor) and emit one `quest.seeded_at_creation` span with `severity="info"`, `has_stakes=True`, `source_drive=""`, `quest_id=""`, `anchor_id=""` (the defer marker). Otherwise proceed as today (seed-from-drive, or empty-drive warning). This makes the seed FILL an empty spine, never OVERWRITE an authored one. The verify-flagged reuse note (extract a `quest_seeded_at_creation_span` helper) is a reasonable companion cleanup now that there are three call sites — Dev's discretion.

**Status:** RED (3 failing). **Handoff:** To Dev (Ponder Stibbons) for the green fix.

## Dev Assessment (rework green — RT1)

**Implementation Complete:** Yes — Reviewer HIGH finding fixed.
**Files Changed (rework):**
- `sidequest/game/quest_seed.py` — added the **fill-not-clobber** guard at the top of `seed_quest_spine`: if `snapshot.active_stakes.strip()` is non-empty (a world/chapter-authored spine), **defer** — preserve the authored stakes, add no seed quest/anchor — and emit the span with `severity="info"`, `deferred=True`, `source_drive=""`, `has_stakes=True`. The seed-from-drive and empty-drive-warning paths are unchanged below the guard. Refactored all three emissions onto the new helper.
- `sidequest/telemetry/spans/state_patch.py` — extracted `quest_seeded_at_creation_span(*, quest_id, anchor_id, source_drive, has_stakes, severity, deferred=False, ...)` (point-event emitter, mirrors `state_patch_hp_span`), addressing verify's medium reuse finding now that there are three call sites; added `deferred` to the span route extract so the GM panel can distinguish defer from seed-from-drive.
- `tests/game/test_quest_seed.py` — ruff format on the 3 new rework tests (authored by TEA in rework red).

**Tests:** 17/17 passing (GREEN) — 16 unit (13 original + 3 defer) + 1 wiring. Full server suite: **9724 passed, 360 skipped, 1 pre-existing unrelated failure** (`test_aside_channel_wiring.py::test_aside_is_out_of_band_in_mp`, unchanged from RT0). Lint + format clean on changed files.
**Branch:** pushed `a9a5ca87` (atop the rework RED `3668d235`).

**Three GM-panel-distinguishable seed outcomes now:** real seed (`severity=info`, ids set, `source_drive`=drive), empty (`severity=warning`, `has_stakes=False`), deferred-to-authored (`severity=info`, `deferred=True`, ids empty, `source_drive=""`).

**Handoff:** To Architect (Leonard) for spec-check, then Reviewer (Granny) re-review.

## Architect Assessment (spec-check — rework RT1)

**Spec Alignment:** Aligned
**Mismatches Found:** None

The rework directly implements the Reviewer's HIGH fill-not-clobber requirement:
- **Defer signal is correct:** `snapshot.active_stakes.strip()` is the right "world-authored spine exists" test — `active_stakes` is exactly the field `materialize_from_genre_pack` populates from the opening chapter and the field that was being clobbered. Deferring on it preserves authored content (SOUL "Diamonds and Coal"). ✓
- **Defer is observable, not silent:** emits `quest.seeded_at_creation` with `severity="info"`, `deferred=True`, ids/`source_drive` empty — a distinct, GM-panel-readable third outcome alongside seed-from-drive and empty-warning. Honors the OTEL Observability Principle on the new branch. ✓
- **Reuse-first:** the `quest_seeded_at_creation_span` helper extraction matches the established `state_patch_hp_span`/`quest_update_span` convention and removes the triplicated inline dict — a genuine reuse improvement, not new infrastructure. ✓
- **Scope held:** still no `WorldStatePatch` field, `orbital/course.py` untouched; only the one span (now with an additive `deferred` attr). ✓

The earlier informational downstream note (77-2/77-3 must treat the `seed_drive` row as the turn-0 entry) is unchanged and still non-blocking.

**Decision:** Proceed to review (TEA verify → Reviewer re-review).

## TEA Assessment (verify — rework RT1)

**Phase:** finish (re-run on the rework diff)
**Status:** GREEN confirmed (no code changed in verify; Dev rework full-suite GREEN stands — 9724 passed)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5 (rework diff)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding (medium, out-of-scope) | VERIFIED the prior span-helper finding is RESOLVED (`quest_seeded_at_creation_span` extracted, 3 call sites, no dup). New: `_spans_named`/`_only_span` duplicated across 16+ test files codebase-wide. |
| simplify-quality | clean | naming, OTEL routing, fill-not-clobber guard, loud-degrade, wiring test — all conform. |
| simplify-efficiency | clean | minimal fill-not-clobber + helper extraction; no over-engineering. |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 0 (the one medium finding is deferred — see below)
**Noted/Deferred:** 1 — `_spans_named`/`_only_span` test-helper duplication is a **pre-existing, codebase-wide** pattern (16+ files: test_orbital_e2e, test_materializer, test_pov_swap_otel, …), NOT introduced by 77-1. Extracting it to a shared `tests/conftest.py` would touch 16+ files — out of scope for a quest-seed story and a scope-creep trap. Deferred to a dedicated test-hygiene story. The prior verify reuse finding (span helper) is now RESOLVED in the rework.
**Reverted:** 0

**Quality Checks:** All passing (Dev rework full-suite: 9724 passed, 360 skipped; 1 pre-existing unrelated aside-channel failure).
**Overall:** simplify: clean (prior finding resolved; 0 applied; 1 pre-existing cross-cutting finding deferred)

**Handoff:** To Reviewer (Granny Weatherwax) for re-review.

## Subagent Results (re-review RT1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 17 GREEN, ruff check clean, 1 pre-existing format reflow (chargen_mixin:1396, not this diff), 1 content-gate skip (ran clean) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | No | Skipped | disabled | Disabled via settings |
| 5 | reviewer-comment-analyzer | No | Skipped | disabled | Disabled via settings |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | No | Skipped | disabled | Disabled via settings |

**All received:** Yes (1 enabled returned; 8 disabled via settings)
**Total findings:** 0 new confirmed (the RT0 HIGH is now resolved — re-verified below), 0 dismissed, 1 deferred (cross-cutting test-helper dup)

## Reviewer Assessment (re-review RT1)

**Verdict:** APPROVED

The RT0 HIGH finding (unconditional `active_stakes` clobber of world-authored stakes) is **resolved**. Re-verified against the rework diff:

- [VERIFIED] **Fill-not-clobber guard is correct and correctly ordered** — `quest_seed.py:53` `if snapshot.active_stakes.strip():` precedes the source/empty logic, so a world/chapter-authored spine is preserved and the seed only fills an empty one. Defends flickering_reach (`history.yaml:107`) / annees_folles. Evidence: the guard returns before any `active_stakes`/`quest_log`/`quest_anchors` write.
- [VERIFIED] **Defer is observable, never silent** — the defer branch emits `quest_seeded_at_creation_span(..., severity="info", deferred=True, source_drive="")` (`quest_seed.py:54-61`); routed with the new `deferred` field (`state_patch.py`). Honors OTEL Observability on the new path.
- [VERIFIED] **Regression coverage exists** — `test_world_authored_active_stakes_is_not_clobbered`, `test_authored_spine_skips_seed_quest_and_anchor`, `test_defer_path_emits_one_non_warning_span` all GREEN; these would have caught the RT0 bug. The original 13 + wiring test still pass (16 unit + 1 wiring = 17).
- [VERIFIED] **Helper extraction sound** — `quest_seeded_at_creation_span` mirrors `state_patch_hp_span` (point-event open+close, `_tracer` override, `**attrs`); resolves the verify reuse finding; all three call sites route through it. No behavior change to the seed-from-drive or empty-warning paths.
- [VERIFIED] **Scope still held** — no `WorldStatePatch` field, `orbital/course.py` untouched; only the one span (now with an additive `deferred` attr).
- [LOW] Pre-existing `ruff format` reflow at `chargen_mixin.py:1396` — NOT this story's code (diff touches lines 44 + 789-795); ungated by project gates; non-blocking, noted for general hygiene.
- [deferred] `_spans_named`/`_only_span` test-helper duplication across 16+ files — pre-existing, cross-cutting; out of scope for this story (deferred to a test-hygiene story).

### Rule Compliance (re-review)

- **No Silent Fallbacks (CLAUDE.md/SOUL):** defer path emits an observable span (not silent), empty path warns. Now COMPLIANT (the RT0 violation — silent overwrite — is fixed).
- **Diamonds and Coal / Crunch-in-Genre-Flavor-in-World (SOUL):** world-authored stakes are now preserved. COMPLIANT.
- **OTEL Observability:** three distinguishable, routed outcomes (seed / warning / defer). COMPLIANT.
- **python #1/#2/#3/#6, No Source-Text Wiring Tests:** unchanged from RT0 — COMPLIANT.

### Devil's Advocate (re-review)

The clobber is fixed — but does the *defer signal* have a hole? I argued: "what if a world authors a `quest_log` entry but leaves `active_stakes` empty? The guard keys only on `active_stakes`, so the seed would still fire and graft a `seed_drive` quest alongside the world's quest." True — but in that case `active_stakes` is empty, so filling it from the drive is *fill*, not *clobber*, and the additive `seed_drive` key collides with nothing (distinct key). No authored content is destroyed; the worst case is a turn-0 spine that has both a world quest and a drive-stake, which is acceptable for Option A and gets reconciled by 77-2/77-4's one-mechanism consolidation. Second attack: "whitespace-only authored stakes?" `.strip()` handles it — a whitespace-only `active_stakes` is treated as empty and seeded, which is correct. Third: "does the defer span's `deferred=True` actually reach the GM panel?" Yes — added to the route extract, and the constant is re-exported (preflight confirmed, `test_..._exported_and_routed` GREEN). No new High/Medium. The fix is tight and the regression is now pinned by three tests. Approved.

**Handoff:** To SM for finish-story (via spec-reconcile if the workflow routes there).

## Delivery Findings

<!-- Agents append below. Never edit/remove another agent's entries. -->

### TEA (test design)
- **Question** (non-blocking): The story's two literal ACs are guardrail-framed (no-drive behavior + loud-degrade); the positive/happy path (populated drive → non-empty spine, stakes derived from drive) is implied by ADR-137 Option A but not written as an AC. Tests assert it anyway. Affects `sprint/current-sprint.yaml` (77-1 ACs could be tightened to name the happy path). *Found by TEA during test design.*
- **Improvement** (non-blocking): The wiring test is intentionally content-agnostic about whether caverns_and_claudes populates `drive` — it asserts one span fires + warning⟺empty-spine consistency rather than requiring populated fields. If chargen is later guaranteed to populate `drive` for caverns, the wiring test could assert the populated branch directly. Affects `sidequest-server/tests/server/test_chargen_quest_seed_wiring.py`. *Found by TEA during test design.*

### Dev (implementation)
- **Gap** (non-blocking): `tests/handlers/test_aside_channel_wiring.py::test_aside_is_out_of_band_in_mp` fails on the full suite AND in isolation, independent of this story (ADR-107 aside path; zero overlap with this 4-file diff). Pre-existing develop debt, surfaced by the full-suite gate — not introduced here. Affects `sidequest-server/tests/handlers/test_aside_channel_wiring.py` (needs its own fix/triage). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the caverns_and_claudes chargen PC lands with `drive=""` but `calling_label="Fighter"`, so the wiring test exercises the **populated (non-warning)** branch via the calling-label fallback. The empty/warning branch is covered by the unit tests, not the live caverns path. Affects `sidequest-server/tests/server/test_chargen_quest_seed_wiring.py`. *Found by Dev during implementation.*

### Reviewer (code review)
- **Conflict** (blocking): `seed_quest_spine` unconditionally overwrites `snapshot.active_stakes`, clobbering world-authored opening stakes set by `materialize_from_genre_pack` (`world_materialization.py:315-316`) — confirmed active on flickering_reach (`history.yaml:107`, opening chapter) and annees_folles, ~10 worlds total. Affects `sidequest-server/sidequest/game/quest_seed.py` (guard the write: fill the spine only when not already authored; emit the span on the defer path). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): no test covers the seed against a world that authors opening `active_stakes`; the guard test for the blocking fix should cover this. Affects `sidequest-server/tests/server/test_chargen_quest_seed_wiring.py` (or a new unit test with a pre-populated snapshot). *Found by Reviewer during code review.*

### Reviewer (re-review RT1)
- **Resolved** (was blocking, now closed): the HIGH `active_stakes` clobber is fixed by the fill-not-clobber defer guard (`quest_seed.py:53`); covered by 3 new GREEN tests + the original 13 + wiring. Affects `sidequest-server/sidequest/game/quest_seed.py` (no further action). *Verified by Reviewer during re-review.*
- **Improvement** (non-blocking, deferred): `_spans_named`/`_only_span` test helpers duplicated across 16+ test files codebase-wide (pre-existing, not this story). Affects `sidequest-server/tests/` (extract to shared conftest in a test-hygiene story). *Found by Reviewer during re-review.*

## Design Deviations

### TEA (test design)
- **Pinned `severity` as the warning-marker span attribute key**
  - Spec source: context-story-77-1.md, AC-2 / Technical Guardrails
  - Spec text: "emit `quest.seeded_at_creation` span carrying a WARNING-severity attribute on empty seed"
  - Implementation: tests assert the marker is `attrs["severity"] == "warning"` (mirroring the watcher `validator.py` `severity=` convention); the ADR-137 contract attributes (`quest_id`, `anchor_id`, `source_drive`, `has_stakes`) are asserted alongside.
  - Rationale: the story leaves the exact attribute key to Dev ("Dev chooses one consistent with how the GM panel reads severity"); TEA pins one concrete, GM-panel-consistent key so the RED contract is testable. Dev may rename with a deviation if the GM panel reads a different key.
  - Severity: minor
  - Forward impact: Dev must use `severity` as the attribute key (or log a counter-deviation + update the test).
- **Added positive-path + calling-label coverage beyond the 2 literal ACs**
  - Spec source: context-story-77-1.md, AC-2 (mirror clause) + Scope ("derived from the PC's drive/calling_label")
  - Spec text: "(mirror) that on the populated-drive path the span fires without the warning and the three fields … are non-empty and derived"
  - Implementation: added happy-path tests and a `calling_label`-only fallback test not enumerated as standalone ACs.
  - Rationale: AC-2's mirror clause + the drive/calling scope imply both; testing only the empty path would leave the spine's actual job uncovered.
  - Severity: minor
  - Forward impact: none — strictly more coverage.
- **RED for the unit module is an ImportError, not per-test assertion failures**
  - Spec source: TDD RED protocol
  - Spec text: "Write failing tests covering each AC"
  - Implementation: `tests/game/test_quest_seed.py` fails at collection (ImportError on the not-yet-created `quest_seed` module) rather than each test failing individually.
  - Rationale: canonical RED for a brand-new module; once Dev creates the module the tests collect and fail on assertions until implemented.
  - Severity: minor
  - Forward impact: none.
- **Pinned the defer-path span contract (rework RT1)**
  - Spec source: Reviewer Assessment HIGH finding + context-story-77-1.md Technical Guardrails
  - Spec text: "Fill, don't clobber … emit the span on the defer path (observability) rather than silently skipping or overwriting"
  - Implementation: tests pin the defer span as `severity="info"`, `has_stakes=True`, `source_drive=""`, `quest_id=""`, `anchor_id=""` — distinguishing defer from seeded-from-drive (`source_drive` set) and from empty-warning (`severity="warning"`, `has_stakes=False`).
  - Rationale: the Reviewer required defer to be observable, not silent; a concrete, GM-panel-distinguishable attribute set is needed for the RED contract. Dev may add an explicit `deferred=True` attr if clearer.
  - Severity: minor
  - Forward impact: Dev must emit the defer span with these attrs (or a documented superset).

### Dev (implementation)
- No deviations from spec. Implemented the TEA contract verbatim — seed source `drive`→`calling_label`, the three-field seed, the `quest.seeded_at_creation` routed span with `severity`/`has_stakes`/`source_drive`/`quest_id`/`anchor_id` attributes, and the `chargen_mixin._chargen_confirmation` wire seam. Accepted TEA's pinned `severity` attribute key (no rename).

### Dev (implementation — rework RT1)
- **Extracted `quest_seeded_at_creation_span` helper + added `deferred` span attr (beyond the strict fix)**
  - Spec source: verify TEA Assessment (Simplify Report, medium reuse finding) + Reviewer HIGH fix
  - Spec text: "Extract `quest_seeded_at_creation_span(...)` … matching the `state_patch_hp_span()`/`cwn_*_span()` precedent. Deduplicate the two inline spans."
  - Implementation: extracted the helper into `state_patch.py` and routed all three call sites through it (the fix added a third); added a `deferred` boolean attribute + route field to distinguish defer-to-authored from seed-from-drive on the GM panel.
  - Rationale: the fix introduced a third span call site, tipping the flagged-medium reuse finding into clearly-worth-doing; resolves it in the same PR rather than leaving it for a follow-up.
  - Severity: minor
  - Forward impact: none — pure dedup + an additive observability attribute.

### Reviewer (audit)
- **TEA: Pinned `severity` as the warning-marker span attribute key** → ✓ ACCEPTED by Reviewer: GM-panel-consistent (matches `validator.py` `severity=` convention); Dev implemented it faithfully. Sound.
- **TEA: Added positive-path + calling-label coverage beyond the 2 literal ACs** → ✓ ACCEPTED by Reviewer: AC-2's mirror clause and the drive/calling scope imply both; more coverage is correct.
- **TEA: RED via ImportError for the new module** → ✓ ACCEPTED by Reviewer: canonical RED for a new module.
- **Dev: No deviations from spec** → ✓ ACCEPTED as accurate re: the TEA contract — Dev implemented exactly what was pinned. **However**, the contract + spec themselves under-specified the fill-vs-clobber semantics, which is the source of the blocking finding below (not a Dev deviation from the contract, but a spec/contract gap).
- **UNDOCUMENTED (Reviewer):** Spec/context said "seed `active_stakes` from drive at session init" without an "only-if-empty" qualifier; code does an unconditional `snapshot.active_stakes = source`, which **overwrites world-authored opening stakes** (`world_materialization.py:315-316`; flickering_reach `history.yaml:107`). Neither TEA nor Dev logged this because the contract inherited the spec's silence and the test world (caverns) authors no opening stakes. Spec said *fill*; code does *overwrite*. Severity: **High** — resolution is the fill-not-clobber guard (rework). The story context AC should be tightened to "seed only when the spine is unauthored." → ✓ RESOLVED in rework RT1: `quest_seed.py:53` defer guard; 3 GREEN regression tests pin it.
- **Dev (rework RT1): Extracted `quest_seeded_at_creation_span` helper + added `deferred` attr** → ✓ ACCEPTED by Reviewer: a genuine reuse improvement (matches `state_patch_hp_span` convention) prompted by the third call site the fix introduced; the `deferred` attribute is additive observability. Sound, no behavior change to the seed/warning paths.

### Architect (reconcile)

Reviewed all in-flight deviation entries (TEA ×4, Dev ×2, Reviewer audit) against ADR-137, the story context, and the code. All are accurate, self-contained, and reference real paths/quotes (`quest_seed.py`, `world_materialization.py:315-316`, `mutant_wasteland/worlds/flickering_reach/history.yaml:107`, `state_patch.py`). No corrections needed.

**Definitive deviation manifest (1 substantive, resolved):**
- **Spec under-specified fill-vs-clobber semantics → caused a HIGH regression, now resolved.**
  - Spec source: `sprint/context/context-story-77-1.md` (Scope + AC Context) and ADR-137 Option A.
  - Spec text: "at session init, derive **one** `quest_anchor` + a `quest_log` entry + `active_stakes` from the PC's drive/calling" — stated as *fill the empty spine* (the motivating bug was `active_stakes: ""`), but with **no explicit "only-if-empty" qualifier**.
  - Implementation (RT0): unconditional `snapshot.active_stakes = source`, which overwrote world-authored opening stakes (`world_materialization.py:315-316` sets it from the fresh chapter; live on ~10 worlds incl. flickering_reach `history.yaml:107`, annees_folles). The test world (caverns) authors no opening stakes, so GREEN missed it; the Reviewer caught it.
  - Resolution (RT1): fill-not-clobber defer guard at `quest_seed.py:53` — when `active_stakes` is already authored, defer (preserve it, seed nothing) and emit an observable `deferred=True` span. Pinned by 3 GREEN regression tests.
  - Severity: was High; now resolved (no residual).
  - Forward impact: **(1)** the 77-1 story-context AC should be tightened to "seed only when the spine is unauthored" so the intent is explicit for future readers; **(2)** stories **77-2** (`record_quest`/`set_stakes`) and **77-4** (one-mechanism consolidation) must treat the `seed_drive` row + a deferred-to-authored spine as the pre-existing turn-0 state — update/supersede, never duplicate. Both are downstream-story notes, not changes to this story.

No ACs were deferred (both ACs DONE — AC-1 no-drive verified, AC-2 loud-degrade + mirror). No sibling-story AC conflicts. The deviation manifest is complete for the boss's audit.