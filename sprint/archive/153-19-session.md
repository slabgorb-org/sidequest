---
story_id: "153-19"
jira_key: null
epic: "153"
workflow: "tdd"
---
# Story 153-19: [PLAYTEST-DATA-ODDITIES] nottavello header latch + stale Adventurer location key + active_stakes class-name + npcs None-rows

## Story Details
- **ID:** 153-19
- **Jira Key:** none (local sprint, no Jira)
- **Workflow:** tdd
- **Epic:** 153 — Playtest follow-ups
- **Stack Parent:** none
- **Type:** bug
- **Points:** 3
- **Repo:** sidequest-server

## Story Summary

Four data-oddity bugs in snapshot/projection serialization recur across multiple worlds. This story fixes the in-scope cluster: oddities 2–4 (stale "Adventurer" location key, active_stakes class-name serialization, npcs None-rows filtering). **Oddity 1 (nottavello header latch) is DEFERRED into the location-single-authority effort (server PR #1029) per 2026-06-22 scope amendment.**

## In-Scope Work
- **Oddity 2:** Clean up pre-name placeholder key from `character_locations` at character finalization.
- **Oddity 3:** Fix stakes population/serialization so `active_stakes` carries a description, not the PC class name.
- **Oddity 4:** Filter `None` entries from `npcs` collection before snapshot serialization.
- **Integration test AC:** Verify at least one oddity (2–4) is absent via the real snapshot/projection path.

## Out-of-Scope (Deferred)
- **Oddity 1:** nottavello header latch / session-create location seeding (folded into location-single-authority PR #1029).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T14:57:01Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T14:14:08Z | 2026-06-22T14:15:53Z | 1m 45s |
| red | 2026-06-22T14:15:53Z | 2026-06-22T14:39:35Z | 23m 42s |
| green | 2026-06-22T14:39:35Z | 2026-06-22T14:45:58Z | 6m 23s |
| review | 2026-06-22T14:45:58Z | 2026-06-22T14:57:01Z | 11m 3s |
| finish | 2026-06-22T14:57:01Z | - | - |

## Delivery Findings

### TEA (test design)
- **Question** (non-blocking): The literal `None` rows in `snapshot.npcs` (oddity 4) have no confirmed origin — every `npcs.append` site (`session.py:1801` `_npc_from_patch`, `world_materialization.preload_authored_npcs`, `encounter_lifecycle`, `monster_manual_inject`) builds a real `Npc`, never `None`. The `None` is a serialization/round-trip artifact (likely an empty MM-patch slot or a `model_construct`/save-import path dumped to null). The RED tests target the EXPOSURE boundary per Fix Direction #4 (filter before the snapshot is exposed), which neutralizes the symptom regardless of origin. Affects `sidequest/server/snapshot_slimming.py` (`_apply_phase_c_projections` — add an unconditional None-filter + `npcs_none_dropped` count). Dev MAY additionally hunt the source if cheap, but it is not required to green this story. *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `sidequest/game/world_materialization.py` has 3 PRE-EXISTING pyright errors (`int` not assignable to `Disposition` at lines ~506/~545/~928, in `_apply_npc`/`_apply_character`/`preload_authored_npcs`) — NOT introduced by this story's diff (my new `prune_orphan_character_locations` is clean). Flagged so the Reviewer doesn't attribute them to 153-19. Affects `sidequest/game/world_materialization.py` (the `Npc.disposition` field is typed `Disposition` but seeded with bare `int`). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): `active_stakes` reaches the narrator snapshot allowlist with no `sanitize_player_text` at the seed→snapshot→prompt boundary. PRE-EXISTING (story 77-1 write sites, NOT introduced by 153-19 — this diff only narrowed the `source` value). Low risk today because `drive`/`calling_label` are pack-authored YAML choice labels (builder.py `acc.backstory_label`/`acc.class_label`), not player free-text, so ADR-047's trigger isn't met. Defense-in-depth hardening for a future story if a free-text drive path is ever added. Affects `sidequest/game/quest_seed.py` (wrap `source` with `sanitize_player_text` at the write). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): the `pruned_keys` OTEL span attribute is unsanitized and published over the no-auth `/ws/watcher` endpoint + persisted in telemetry. Impact is bounded: `pruned_keys` holds ORPHAN keys (the discarded `"Adventurer"` placeholder), not live player names (those are valid keys and kept), the GM panel is a dev-only surface where character names already appear, and it never reaches the narrator prompt. `/ws/watcher` no-auth is the pre-existing ADR-119 (partial) gap. Affects `sidequest/game/world_materialization.py` / `sidequest/server/watcher.py` (optional: sanitize `pruned_keys`, or land `/ws/watcher` under ADR-119 auth). *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)
- **Oddity 1 / AC-1 intentionally untested (deferred)**
  - Spec source: session scope amendment (2026-06-22); context-story-153-19.md AC-1
  - Spec text: "Header shows resolved location on turn 1 ... never a raw region id like nottavello"
  - Implementation: No red tests written for oddity 1; folded into the location-single-authority effort (server PR #1029 + Plans 2-3)
  - Rationale: Operator-approved scope cut — oddity 1 is a session-create location-seeding bug overlapping the in-flight location-authority refactor; fixing the symptom here would race the root-cause work
  - Severity: minor
  - Forward impact: oddity 1 resolves in the location-single-authority effort, not 153-19
- **Oddity 2 tested via a TEA-defined contract function + always-fire span, not a content-coupled chargen assertion**
  - Spec source: context-story-153-19.md AC-2, AC-5
  - Spec text: "clean up the pre-name placeholder key from character_locations at character finalization"
  - Implementation: Defined contract `prune_orphan_character_locations(snapshot) -> int` (in `world_materialization.py`) + an always-fire `character_locations.orphan_pruned` span; wiring proven by asserting the span fires on the real chargen commit (content-agnostic), not by asserting an orphan key on a specific pack
  - Rationale: caverns_and_claudes (the only chargen wiring harness) does NOT author a nameless protagonist, so it cannot reproduce the "Adventurer" key — a content-coupled wiring assertion could not be RED-guaranteed. The always-fire-span pattern (precedent: quest_seed/77-1) gives a content-agnostic wiring proof and satisfies the OTEL Observability Principle
  - Severity: minor
  - Forward impact: Dev must create the named function + span constant (routed in SPAN_ROUTES); if Dev relocates the function, the game-test import must move in lockstep
- **Oddity 3 fix interpreted as loud-degrade (empty stakes + warning span), not substitute-description**
  - Spec source: context-story-153-19.md AC-3
  - Spec text: "active_stakes contains a stakes description string, not the PC's class name"
  - Implementation: When the only seed source is a `calling_label` equal to `char_class` (the bare-class-name case), `seed_quest_spine` must take the existing empty-source LOUD-degrade path (active_stakes="", severity="warning"), not fabricate a substitute description
  - Rationale: with no drive and only a bare class-name calling there is no meaningful stakes to seed; inventing one would violate No Silent Fallbacks. A flavorful calling_label that differs from char_class is unaffected (guard test pins the 77-1 contract)
  - Severity: minor
  - Forward impact: the calling_label fallback narrows to exclude calling_label==char_class; whether chargen should leave calling_label empty when it equals the archetype is a separate concern, out of scope here
- **Oddity 4 fixed at the snapshot-exposure boundary, not at the (unconfirmed) source of the None rows**
  - Spec source: context-story-153-19.md AC-4, Fix Direction #4
  - Spec text: "filter None entries from the npcs collection before serialization / before the snapshot is exposed"
  - Implementation: Tests drive `_apply_phase_c_projections` (the production exposure projection) and assert literal None rows are filtered + reported in a new `npcs_none_dropped` count; no test targets where None first enters `snapshot.npcs`
  - Rationale: every `npcs.append` site builds a real Npc; the None origin is an unpinned serialization artifact (see Delivery Findings). Fix Direction #4 explicitly calls for filtering at exposure, which neutralizes the symptom regardless of origin
  - Severity: minor
  - Forward impact: defensive filter at the projection boundary + an additive `npcs_none_dropped` projection counter

### Dev (implementation)
- **Oddity 2 prune call placed after the location backfill, not immediately after `materialized.characters = [character]`**
  - Spec source: session TEA Assessment → Dev contract (oddity 2)
  - Spec text: "call the prune in chargen_mixin._chargen_confirmation right after `materialized.characters = [character]` (chargen_mixin.py:1495)"
  - Implementation: Called `prune_orphan_character_locations(materialized)` ~30 lines later, right after the `world_history` location-backfill loop (chargen_mixin.py:~1526), still inside the same first-commit finalization block
  - Rationale: pruning AFTER the real PC's `character_locations` key is backfilled means the prune operates on the final dict — it removes the orphan placeholder while the real key is already present, so there is zero risk of the prune running before the real key exists. The contract's intent (prune at finalization) is fully satisfied
  - Severity: trivial
  - Forward impact: none — same finalization seam, same observable result (wiring test green)

### Reviewer (audit)
- **TEA — Oddity 1 / AC-1 intentionally untested (deferred)** → ✓ ACCEPTED by Reviewer: Operator-approved scope cut; the overlap with the location-single-authority effort (PR #1029) is real and documented in the session + context. Correct call.
- **TEA — Oddity 2 contract-function + always-fire span, not content-coupled** → ✓ ACCEPTED by Reviewer: caverns_and_claudes verifiably authors no nameless protagonist (confirmed: its history.yaml seeds locations but no `characters:` entry), so a content-coupled wiring assertion could not be RED-guaranteed. The always-fire-span proof mirrors the 77-1 precedent and satisfies the OTEL principle. Preflight confirmed the wiring test fired green.
- **TEA — Oddity 3 loud-degrade interpretation** → ✓ ACCEPTED by Reviewer: correct per No Silent Fallbacks — a bare class name is not a meaningful stake, and the guard test (`test_flavorful_calling_label_differing_from_class_still_seeds`) pins the 77-1 flavorful-calling fallback so the narrowing can't over-correct.
- **TEA — Oddity 4 exposure-boundary fix, not source** → ✓ ACCEPTED by Reviewer: Fix Direction #4 explicitly directs filtering at exposure; verified every `npcs.append` site builds a real `Npc`, so the None origin is genuinely a serialization artifact. The deferred source-hunt is captured as a non-blocking Delivery Finding (TEA) — appropriate.
- **Dev — Oddity 2 prune call placed after the location backfill** → ✓ ACCEPTED by Reviewer: placing the prune AFTER the real PC's location key is backfilled is in fact MORE correct than the literal contract wording — it prunes the final dict with the real key already present, so the orphan placeholder goes and the live key stays. Same finalization block, observable result identical (wiring test green). Trivial, sound.

**Tests Required:** Yes
**Status:** RED (failing — ready for Dev)
**Branch:** `feat/153-19-data-oddities-projection-cleanup` (server). Commit `9cc6b87a`.

**Test Files:**
- `tests/game/test_quest_seed.py` — oddity 3, +3 tests appended
- `tests/server/test_61_8_projection_edge_cases.py` — oddity 4, +2 tests appended
- `tests/game/test_153_19_character_location_cleanup.py` — oddity 2 unit/contract, NEW (5 tests)
- `tests/server/test_153_19_character_location_cleanup_wiring.py` — oddity 2 wiring, NEW (1 test)

**Tests Written:** 11 new tests covering AC-2, AC-3, AC-4, AC-5. (AC-1 deferred — see deviations; AC-6 is a process gate, no test.)

**RED verification** (`uv run pytest -n0`, local `slabgorb` PG role):
- Oddity 2 unit (5 tests): collection `ImportError` on `prune_orphan_character_locations` (function not yet created) — RED.
- Oddity 2 wiring (1 test): 0 `character_locations.orphan_pruned` spans on the real chargen commit (cleanup not wired) — RED.
- Oddity 3 (3 tests): 2 RED (`active_stakes == "Channeler"`); 1 GREEN guard (`test_flavorful_calling_label_differing_from_class_still_seeds` — pins the 77-1 calling fallback so the fix can't over-correct).
- Oddity 4 (2 tests): RED — literal `None` rows survive the degraded-location skip path; the room-scoped path crashes (`AttributeError` on `None.get("core")`) — both the documented symptom.
- **No regressions:** full `test_quest_seed.py` = 2 failed / 17 passed; full `test_61_8` = 2 failed / 6 passed.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| lang-review #6 test-quality (no vacuous assertions) | all 11 new tests assert specific values — no `assert True`, no bare-truthy `assert result`, no `let _ =` | pass |

**Rules checked:** lang-review #6 is the only checklist rule that governs RED test-writing; #1–#5 and #7–#13 govern Dev's GREEN implementation code and are enforced by the python-review gate on the implementation diff.
**Self-check:** 0 vacuous tests.

### Dev contract (GREEN — Agent Smith)
- **Oddity 2:** add `prune_orphan_character_locations(snapshot) -> int` to `sidequest/game/world_materialization.py` (drop every `character_locations` key with no matching `character.core.name`; return count); add `SPAN_CHARACTER_LOCATIONS_PRUNED = "character_locations.orphan_pruned"` to `telemetry/spans/state_patch.py` + route in `SPAN_ROUTES` + an always-fire helper carrying `pruned_count`; CALL the prune in `chargen_mixin._chargen_confirmation` right after `materialized.characters = [character]` (chargen_mixin.py:1495 — the orphan seam).
- **Oddity 3:** in `seed_quest_spine`, when the only seed source is `calling_label` AND it equals `char_class` (case-insensitive), take the existing loud-degrade path (no seed, `severity="warning"`) instead of seeding the bare class name. Keep the flavorful-calling fallback intact.
- **Oddity 4:** in `_apply_phase_c_projections` (`snapshot_slimming.py`), unconditionally filter literal `None` entries from `payload["npcs"]` (OUTSIDE the `current_room_id` gate — the skip path is the live conduit) and report the count in a new `npcs_none_dropped` key in the returned counts dict.

**Handoff:** To Dev (Agent Smith) for GREEN implementation.

---

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 33/33 passing (GREEN) across the 4 story test files; +49 passing in the regression sweep on touched subsystems. No regressions.
**Branch:** `feat/153-19-data-oddities-projection-cleanup` (pushed to origin). Impl commit `feat(153-19): fix data-oddities 2-4`.

**Files Changed (production):**
- `sidequest/game/quest_seed.py` — oddity 3: `seed_quest_spine` drops a `calling_label` that equals `char_class` (case-insensitive) from the seed source, so a bare class name ("Channeler") degrades loudly instead of becoming `active_stakes`.
- `sidequest/game/world_materialization.py` — oddity 2: new `prune_orphan_character_locations(snapshot) -> int`.
- `sidequest/server/websocket_handlers/chargen_mixin.py` — oddity 2 wiring: calls the prune at chargen finalization (after the location backfill; see deviation).
- `sidequest/telemetry/spans/state_patch.py` — oddity 2 OTEL: `SPAN_CHARACTER_LOCATIONS_PRUNED` constant + `SPAN_ROUTES` entry + always-fire `character_locations_pruned_span` helper.
- `sidequest/server/snapshot_slimming.py` — oddity 4: `_apply_phase_c_projections` filters literal `None` npc rows unconditionally (before the `current_room_id` gate) + reports `npcs_none_dropped`.

**Verification** (`uv run pytest -n0`, local `slabgorb` PG):
- Story files: 33 passed (quest_seed 20, char-location-cleanup unit 5, projection-edge-cases 8, char-location-cleanup wiring 1) — the oddity-3 guard test stays green (77-1 contract preserved).
- Regression: 49 passed (test_61_7, test_82_10 slimming, test_chargen_quest_seed_wiring, test_153_13 fate drive seed, quest_entry_widening, character_chargen_fields).
- `ruff check` + `ruff format --check`: clean on all 5 changed files.
- `pyright`: 0 NEW errors from this diff (3 pre-existing `Disposition` errors flagged in Delivery Findings).

**ACs:** AC-2 ✅ (orphan key pruned + wired + OTEL), AC-3 ✅ (no class-name stakes), AC-4 ✅ (no None rows + counter), AC-5 ✅ (wiring tests on the real chargen + projection paths), AC-6 ✅ (no new tracking items filed). AC-1 deferred (scope amendment).

**Handoff:** To verify/review phase.

---

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 1 benign (content-pack skip guard) | N/A — 63/63 tests green, ruff lint+format clean on all 5 files |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [SILENT]) |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [TEST]) |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [DOC]) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [TYPE]) |
| 7 | reviewer-security | Yes | findings | 2 (1 medium, 1 low) | both dismissed-as-blocking (pre-existing / dev-only) → captured as non-blocking Delivery Findings (see [SEC]) |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings — assessed manually (see [RULE]) |

**All received:** Yes (2 enabled subagents returned; 7 disabled via `workflow.reviewer_subagents` and assessed manually by Reviewer)
**Total findings:** 0 confirmed blocking, 2 dismissed-as-blocking (captured as non-blocking Delivery Findings), 0 deferred

## Rule Compliance

Enumerated against `.pennyfarthing/gates/lang-review/python.md` + SOUL.md + CLAUDE.md across all 5 production files:
- **#1 silent exceptions:** no try/except added; no swallowed errors. ✓
- **#2 mutable defaults:** `character_locations_pruned_span(..., pruned_keys: list[str] | None = None)` uses `None` default, not `[]`. ✓
- **#3 type annotations:** `prune_orphan_character_locations(snapshot: Any) -> int` annotated; span helper kwargs typed. `snapshot: Any` matches the file convention (`preload_authored_npcs(state: Any)`). ✓
- **#4 logging:** no error paths added; OTEL spans are the observability surface. ✓
- **#6 test quality:** all 11 new assertions are specific (exact dict equality, exact counts, specific span attrs) — no vacuous `assert True`/bare-truthy. ✓
- **#7 resource leaks:** span emitted via `with Span.open(...)` context manager. ✓
- **#10 import hygiene:** deferred local import of `character_locations_pruned_span` inside the function avoids a `game/`←`telemetry/` circular; wildcard re-export (`from .state_patch import *`) surfaces the new public names (preflight confirmed resolution). ✓
- **#13 fix regressions:** narrow/additive fixes; regression sweep (test_61_7, test_82_10, test_chargen_quest_seed_wiring, test_153_13) green. ✓
- **SOUL/CLAUDE — No Silent Fallbacks:** always-fire prune span, always-set `npcs_none_dropped`, loud-degrade warning span for oddity 3. ✓
- **SOUL/CLAUDE — OTEL Observability Principle:** oddity 2 new routed span; oddity 4 counter flows to `prompt.game_state.bytes`; oddity 3 reuses the warning span. ✓
- **CLAUDE — No Source-Text Wiring Tests:** the oddity-2 wiring test asserts an OTEL span fired (the #1 recommended pattern), not a source grep. ✓
- **#5/#8/#9/#11/#12:** N/A (no path handling, deserialization, async, boundary input, or deps changed).

### Devil's Advocate

Assume this code is broken. **Attack 1 — the prune nukes a live PC's location.** `prune_orphan_character_locations` builds `valid` from `snapshot.characters` and deletes any `character_locations` key not in it. If a caller invokes it when `characters == []`, EVERY location key is destroyed. Is that reachable? The sole wiring is `chargen_mixin._chargen_confirmation`, immediately after `materialized.characters = [character]` and the location backfill — `characters` is provably non-empty (one PC just built and assigned). No other caller exists in the diff. The function is also self-consistent: it can never delete a live character's key because `valid` is derived from the same `characters` it checks against. Safe. **Attack 2 — mutation during iteration.** It deletes from `character_locations` while... no — `orphans` is materialized as a list comprehension FIRST, then deletion iterates `orphans`, not the dict. No `RuntimeError: dictionary changed size during iteration`. Safe. **Attack 3 — the None-filter drops real NPCs and gaslights the narrator into an empty world.** The §D4 doctrine (and its regression test) requires off-stage NPCs to survive the degraded-location skip path. The filter is `entry is not None` — a real NPC dict survives; only literal `None` is removed. test_61_8 (8 tests incl. the §D4 pass-through) is fully green. Safe. **Attack 4 — a confused/malicious player crafts a character name that breaks something.** Names with commas make `pruned_keys` ambiguous (comma-joined), and `<system>`-style names appear in GM-panel telemetry — but `pruned_keys` carries orphan/placeholder keys ("Adventurer"), not live player names, and the surface is dev-only telemetry, never the narrator prompt (captured as a non-blocking finding regardless). **Attack 5 — oddity 3 over-corrects and strips a legitimate stake.** Only when `calling_label.casefold() == char_class.casefold()` exactly; a flavorful calling differs and is preserved (guard test pins it). **Attack 6 — empty/None inputs:** `char_class` is non-blank-validated; `(character.char_class or "")` guards None anyway; `payload.get("npcs")` + `isinstance(list)` guards a missing/non-list npcs key. No new crash path found. The devil's advocate surfaced nothing beyond the two non-blocking telemetry/sanitization findings already captured.

## Reviewer Assessment

**Verdict:** APPROVED

A tight, minimal, well-tested 3-fix cluster (oddities 2–4). 63/63 tests green (story + regression sweep), ruff lint+format clean, zero new pyright errors, no debug code. Implementation matches the TEA contract; all four design deviations are sound and stamped ACCEPTED. Both security findings are non-blocking (pre-existing surface / dev-only telemetry) and captured as Delivery Findings.

**Observations (tagged by domain; 7 specialist subagents disabled → assessed manually):**
- **[VERIFIED] data flow traced** — (a) `character_locations`: chargen finalization → `prune_orphan_character_locations` removes orphans → snapshot/projection; the stale `"Adventurer"` key is gone, live key kept (`world_materialization.py:816-820`). (b) `active_stakes`: `seed_quest_spine` no longer emits the bare class name; the value flows to `build_confrontation_payload` "stakes" (`quest_seed.py:74-78`). (c) `npcs`: `model_dump` → `_apply_phase_c_projections` filters `None` before the narrator state_summary (`snapshot_slimming.py:184-195`).
- **[EDGE]** (manual) [VERIFIED] empty-`characters` prune wipe is unreachable — sole call site guarantees a seated PC; comprehension-then-delete avoids mutation-during-iteration; `payload.get("npcs")`+`isinstance` guards a missing/non-list key. evidence: `world_materialization.py:816-819`, `snapshot_slimming.py:192`.
- **[SILENT]** (manual) [VERIFIED] no swallowed errors — prune always emits its span (even count 0), `npcs_none_dropped` always set, oddity 3 degrades with a `severity="warning"` span. No silent fallbacks. evidence: `state_patch.py:441-445`, `quest_seed.py:71-78`.
- **[TEST]** (manual) [VERIFIED] 11 tests, all specific assertions; RED→GREEN confirmed; the `test_flavorful_calling_label_differing_from_class_still_seeds` guard pins the 77-1 contract against over-correction; wiring tests drive the real chargen + projection paths (OTEL-span wiring, not source grep).
- **[DOC]** (manual) [VERIFIED] docstrings on the new function + span helper are accurate; inline comments correctly explain the unconditional-filter rationale and the deferred-import-for-circular pattern. No stale/misleading comments.
- **[TYPE]** (manual) [VERIFIED] `-> int` return + typed span kwargs + `None` (not mutable) default. The 3 pyright `Disposition` errors are PRE-EXISTING in untouched code (`_apply_npc`/`_apply_character`/`preload_authored_npcs`), not from this diff (Delivery Finding by Dev).
- **[SEC]** (subagent, enabled) 2 findings, both dismissed-as-blocking with evidence: (1) `active_stakes` sanitization is a PRE-EXISTING gap (77-1 write sites, not this diff) with a pack-authored source (ADR-047 player-free-text trigger not met); (2) `pruned_keys` telemetry carries orphan/placeholder keys (not live names) on a dev-only surface. Both captured as non-blocking Delivery Findings.
- **[SIMPLE]** (manual) [VERIFIED] minimal — one choke-point per oddity, no over-engineering, no dead code. The None-filter is a 5-line comprehension; the prune is a set-difference loop.
- **[RULE]** (manual) [VERIFIED] enumerated against lang-review python.md + SOUL/CLAUDE (see Rule Compliance) — compliant on every applicable rule (#2 mutable-default, #7 resource, #10 import hygiene, No-Silent-Fallbacks, OTEL, No-Source-Text-Wiring-Tests).

**Pattern observed:** always-fire OTEL span + per-decision counter (the 77-1 / §D1 precedents) at `state_patch.py` and `snapshot_slimming.py` — consistent with the codebase's lie-detector doctrine.
**Error handling:** guards for missing/non-list npcs payload (`snapshot_slimming.py:192`) and None `char_class`/`calling_label` (`quest_seed.py:74-76`); no new failure path.
**Handoff:** To SM (Morpheus) for finish-story.

---

## Sm Assessment

**Setup complete — routing to TEA (The Architect) for the `red` phase.**

**Story:** 153-19, server-only TDD bug. Full context at `sprint/context/context-story-153-19.md`.

**Scope decision (Operator-approved, 2026-06-22):** The original story bundled four playtest data-oddities. Oddity 1 (nottavello header latch) is a session-create *location-seeding* bug that overlaps the in-flight **location-single-authority** effort (server PR #1029 "Plan 1: engine-authoritative lateral region travel"; Plans 2–3 sever the narrator's `location_drift_repaired` title-scrape authority — the exact mechanism oddity 1 relies on). To avoid racing that root-cause work, the Operator chose to **defer oddity 1** and fold it into that effort. **153-19 is now scoped to oddities 2–4 only.** The context file and session summary both carry the scope amendment.

**In scope for red tests (oddities 2–4):**
- **Oddity 2:** stale `Adventurer` placeholder key persists in `character_locations` after character finalization → clean up at finalization. AC-2.
- **Oddity 3:** `active_stakes` mis-populated with PC class name (`"Channeler"`) instead of a stakes description → fix at stakes serialization / seating layer. AC-3.
- **Oddity 4:** snapshot `npcs` roster carries 7× `None` rows when `authored_npcs_seeded=0` (empty MM-patch slots survive serialization); `npc_pool` is already correct → filter `None` before snapshot exposure. AC-4.
- **Wiring AC (AC-5):** at least one test drives the real snapshot/projection path (not an isolated helper) and asserts one oddity is absent.

**Out of scope — do NOT write tests/code:** Oddity 1 / AC-1 (deferred, see above). No new snapshot/projection architecture. No re-filing the 150-11/150-12 family on other worlds (AC-6 closes it).

**TEA guidance:** Write failing tests for oddities 2–4 through the real snapshot/projection path per the OTEL principle — assert the dirty rows/values are absent. AC-5 (wiring) is mandatory: at least one integration-level test on the production snapshot path.

**Jira:** none — local sprint, story id is the key. Claim explicitly skipped.

**Branch:** `feat/153-19-data-oddities-projection-cleanup` (off origin/develop, server repo).