---
story_id: "54-7"
jira_key: null
epic: "54"
workflow: "tdd"
---

# Story 54-7: Action overlays — EncounterLocationOverlay read-time merge + LOCATION_OVERLAY_CHANGED emit

## Story Details

- **ID:** 54-7
- **Jira Key:** N/A (personal project, sprint YAML only)
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 3

## Workflow Tracking

**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-20T08:58:42Z

### Phase History

| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-20T00:00:00Z | 2026-05-20T08:19:40Z | 8h 19m |
| red | 2026-05-20T08:19:40Z | 2026-05-20T08:26:56Z | 7m 16s |
| green | 2026-05-20T08:26:56Z | 2026-05-20T08:44:42Z | 17m 46s |
| spec-check | 2026-05-20T08:44:42Z | 2026-05-20T08:46:07Z | 1m 25s |
| verify | 2026-05-20T08:46:07Z | 2026-05-20T08:52:46Z | 6m 39s |
| review | 2026-05-20T08:52:46Z | 2026-05-20T08:57:33Z | 4m 47s |
| spec-reconcile | 2026-05-20T08:57:33Z | 2026-05-20T08:58:42Z | 1m 9s |
| finish | 2026-05-20T08:58:42Z | - | - |

## Sm Assessment

Epic 54 (Persistent Location Descriptions) is 7/9 done — 54-7 is the next server brick before the UI companion (54-9) can land. Scope is mechanical: add `location_overlay` field to `StructuredEncounter`, plumb a read-time merge through `_build_effective_manifest` / `get_location_manifest` / `get_location_prose`, register `MessageType.LOCATION_OVERLAY_CHANGED`, and emit on encounter activate/deactivate edges. The implementation plan at `docs/superpowers/plans/2026-05-19-story-54-7-encounter-location-overlays.md` already enumerates the 9 ACs and key files.

Risk profile: low. No new subsystems; this rides on the 54-2 emit pattern that already shipped. Wiring test is mandated by AC-7 (call-site count ≥ 2), which lines up with our "every test suite needs a wiring test" rule. Pre-existing PR #351 (story 57-1) was unmerged and unblocking the gate — squash-merged before setup so 54-7 doesn't trip the merge gate.

Watch items for TEA: keep failing tests narrowly scoped per AC; resist the urge to test the merge end-to-end before the field exists. Watch for `MessageType` enum naming drift (LOCATION_OVERLAY_CHANGED vs LOCATION_DESCRIPTION). HP→Edge concern N/A here — this is structural plumbing, not stat data.

## Delivery Findings

No upstream findings at setup.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Improvement** (non-blocking): No `lang-review/python.md` checklist exists at `.pennyfarthing/gates/lang-review/`. Affects rule-coverage test design across the whole project (every TEA RED phase). *Found by TEA during test design.*
- Plan at `docs/superpowers/plans/2026-05-19-story-54-7-encounter-location-overlays.md` was otherwise complete and ACs were testable as written.

### Dev (implementation)
- **Improvement** (non-blocking): Pre-existing circular import between `sidequest/server/websocket_session_handler.py` and `sidequest/server/session_handler.py` (the latter does a back-compat re-export of `WebSocketSessionHandler` at line 624). Affects every test file that imports from `websocket_session_handler` at module scope — collection fails with `ImportError: cannot import name 'WebSocketSessionHandler' from partially initialized module`. Workaround in the 54-2 + 54-7 test suites is function-scoped imports. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `just server-fmt` reformatted 79 unrelated files. Affects the working tree but not this story's commit. The format sweep is project-standard but was deliberately left out of the 54-7 commit to keep the diff focused on the story. Someone should land the formatter sweep in its own chore commit so future stories don't keep restaging it. *Found by Dev during implementation.*

### TEA (test verification)
- **Gap** (non-blocking): TS `LocationOverlayChangedMessage` interface and `TypedGameMessage` union entry are absent in `sidequest-ui/src/types/payloads.ts`. Affects `src/types/payloads.ts` — Story 54-9 (UI Location panel consumer) must add the wrapper interface and the union entry so `useStateMirror`'s discriminated narrowing handles the message safely. Matches the same outstanding pattern from 54-2 (`LocationDescriptionMessage`), ADR-096 (`TacticalGridMessage`), and Sünden (`DungeonMapMessage`) — all four wrapper interfaces are deferred to the UI-consumer story per plan. *Found by TEA during test verification.*
- **Improvement** (non-blocking): Pre-existing `tsc -b` failure on the sibling `~/Projects/dice-lib` project reference (`TS1484: 'Root' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled`). Affects `dice-lib/src/DiceTray.tsx` line 11 — unrelated to 54-7 but surfaced when running `just check-all`. Either the dice-lib project needs the `type` import, or the project-reference needs to be relaxed. *Found by TEA during test verification.*

## Design Deviations

No deviations from spec at setup.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Dispatch wiring uses pydantic discriminated union, not a dict registry**
  - Spec source: implementation plan, Task 4 Step 5
  - Spec text: `grep -rn '"LOCATION_DESCRIPTION": LocationDescriptionMessage' sidequest-server/sidequest -r` and "At each site, add `'LOCATION_OVERLAY_CHANGED': LocationOverlayChangedMessage,`"
  - Implementation: Registered `LocationOverlayChangedMessage` in the `_Phase1Variant` discriminated union in `sidequest/protocol/messages.py` (the actual dispatch mechanism in this codebase). Updated the corresponding `test_dispatch_registry_includes_location_overlay_changed` test to round-trip through `GameMessage.parse_json` rather than grep for a non-existent dict literal.
  - Rationale: The plan's expected dict-registry pattern was a Rust-era assumption. Post-port (ADR-082) the Python codebase uses pydantic discriminated unions — `Field(discriminator="type")` — as the dispatch. No `"LOCATION_DESCRIPTION": LocationDescriptionMessage` registration exists anywhere in `sidequest/protocol/`. Manufacturing a dict registry just to satisfy the literal string would have been pure stubbing.
  - Severity: minor
  - Forward impact: none. The discriminated union is the authoritative wire dispatch; the round-trip test now proves the message decodes correctly end-to-end (stronger than the original string-presence check).

- **Encounter-overlay emit fires unconditionally, not nested in the room-change branch**
  - Spec source: implementation plan, Task 6 Steps 5 + 6
  - Spec text: "Immediately after that pair (still inside the `with timings.phase('state_apply'):` block)" placed the activate call right where `now_encounter`/`now_live` are set (~line 2991 pre-port estimate).
  - Implementation: Placed both activate and deactivate calls in the live narration loop, at the same indentation as `_maybe_emit_dungeon_map` (post-room-change but unconditional on room change), where `_emit_shared_world_frame` is already in scope. Variables `prior_encounter`, `prior_live`, `now_encounter`, `now_live`, `encounter_resolved_this_turn` are all still live there.
  - Rationale: (a) `_emit_shared_world_frame` is defined later in the turn loop than where the plan suggested placing the emit, so calling it at the spec-named position would have been a NameError; (b) overlay activation can happen WITHOUT a room change — a bar fight ignites in the room the party already stands in — so nesting under the room-change branch would lose those transitions.
  - Severity: minor
  - Forward impact: none — both edges are emitted as the spec demands; the placement is the only thing that moved.

- **Function-scoped imports in `test_location_overlay_emit.py`**
  - Spec source: implementation plan, Task 6 Step 2 test code
  - Spec text: module-level `from sidequest.server.websocket_session_handler import (_maybe_emit_location_overlay_changed,)`
  - Implementation: Moved the import inside each test function, matching the existing 54-2 test file (`test_location_description_emit.py`).
  - Rationale: Pre-existing circular-import fragility between `sidequest.server.websocket_session_handler` ↔ `sidequest.server.session_handler` (back-compat re-export at line 624 of session_handler.py). Module-level import at collection time fails with `ImportError: cannot import name 'WebSocketSessionHandler' from partially initialized module`. Function-scoped imports run after the modules are fully loaded.
  - Severity: minor
  - Forward impact: pre-existing circular import is a Delivery Finding (see Dev section below); no test-side change needed if/when that's cleaned up.

### TEA (test design)
- **`SqliteStore` fixture constructor signature**
  - Spec source: implementation plan, Task 2 + Task 3 fixtures
  - Spec text: `SqliteStore.open(tmp_path / "save.db", genre_slug="tea_and_murder", world_slug="glenross")`
  - Implementation: `SqliteStore(tmp_path / "save.db")` (matches the canonical pattern used by `tests/game/test_location_resolver.py`)
  - Rationale: `SqliteStore.open()` only accepts `(path: str)` — no `genre_slug` / `world_slug` kwargs exist. The Path-based constructor `SqliteStore.__init__(conn: sqlite3.Connection | Path)` is the standard test fixture in 54-6's resolver tests.
  - Severity: minor
  - Forward impact: none — schema is identical, only the construction call differs

- **Task 5 test uses synthetic world instead of caverns_sunden live fixture**
  - Spec source: implementation plan, Task 5 Step 1 test code
  - Spec text: `load_room_payload(world_dir, "sunden_square")` against `sidequest-content/genre_packs/caverns_and_claudes/worlds/caverns_sunden/`
  - Implementation: Uses `_seed_synthetic_world(tmp_path)` + `_patch_genre_loader_find(...)` from the existing 54-2 test file (`test_location_description_emit.py`)
  - Rationale: (a) `caverns_sunden` is deprecated and moved to `genre_workshopping/` (project memory `caverns_sunden is deprecated`); (b) production helper `_maybe_emit_location_description` reads world data via `sd.genre_pack.worlds.get(...)` and `GenreLoader.find`, not via a direct `load_room_payload(world_dir, ...)` call — the synthetic-world pattern is what the existing 54-2 tests use, and the new test should follow suit for consistency.
  - Severity: minor
  - Forward impact: none — AC-8 coverage is identical

- **Extra dedicated tests added beyond plan's explicit list**
  - Spec source: implementation plan, Task 2 + Task 6
  - Spec text: Plan describes overlay entities tagged `from_promotion=False` and resolved-encounter as a skip case, but doesn't write dedicated tests for each.
  - Implementation: Added `test_overlay_entities_tagged_not_from_promotion` (resolver), `test_activate_skips_when_encounter_is_resolved` (emit), and `test_dispatch_registry_includes_location_overlay_changed` (protocol)
  - Rationale: Each enforces a spec invariant the plan calls out but doesn't pin. Test-paranoia bias toward asserting the negative case and the wiring registry.
  - Severity: minor
  - Forward impact: Dev needs to ensure overlay entities surface with `from_promotion=False` from `_build_effective_manifest`, that activate skips when `encounter.resolved=True`, and that the protocol module registers `LOCATION_OVERLAY_CHANGED` in the dispatch table.

## Context

See `sprint/context/context-story-54-7.md` for full technical guardrails, AC details, and implementation plan.

**Key:** `StructuredEncounter.location_overlay` field wires into read-time merge in `get_location_manifest` + `get_location_prose`, with `LOCATION_OVERLAY_CHANGED` WebSocket emit on encounter activate/deactivate edges.

**Acceptance Criteria:**
1. `StructuredEncounter` accepts `location_overlay: EncounterLocationOverlay | None`
2. `_build_effective_manifest` overlay kwarg + backward compatibility
3. `get_location_manifest` and `get_location_prose` in `location_view.py` implement merge
4. `MessageType.LOCATION_OVERLAY_CHANGED` protocol enum + dispatch
5. `_maybe_emit_location_overlay_changed` emits on activate/deactivate edges
6. 54-2's `_maybe_emit_location_description` updated with overlay snapshot
7. Wiring test verifies emit helper has ≥2 call sites
8. TS payload types added

## TEA Assessment

**Tests Required:** Yes
**Reason:** N/A — full TDD; new server feature with 9 ACs covering data model, resolver seam, read-time merge, protocol enum/payload/message, emit helper + production wiring, and snapshot-emit augmentation. UI types are out of TEA's lane (no UI test framework changes; AC-9 covered by the Dev tsc step).

**Test Files:**
- `tests/game/test_encounter_location_overlay_field.py` — 2 tests, AC-1 (StructuredEncounter field)
- `tests/game/test_location_resolver_overlays.py` — 7 tests, AC-2 (resolver overlays= kwarg + arrival order + no-persist)
- `tests/game/test_location_view.py` — 11 tests, AC-3 (read-time merge: manifest + prose, empty-suffix drop, suffix-only on empty base, mismatched bound_room_id skip)
- `tests/protocol/test_location_overlay_changed_message.py` — 6 tests, AC-4 (enum + payload + message + dispatch registration)
- `tests/server/test_location_overlay_emit.py` — 6 tests, AC-5/AC-6/AC-7 (activate + deactivate emits, skip cases, static wiring proof)
- `tests/server/test_location_description_emit.py` (extension) — 1 new test, AC-8 (snapshot emit populates overlays + prose)

**Tests Written:** 33 tests covering 8 ACs + 1 backward-compatibility check
**Status:** RED — 9 assertion/type failures + 3 collection-time ImportErrors. The lone passing test (`test_build_effective_manifest_accepts_empty_overlays_default`) is the explicit 54-6 backcompat probe — passes by design.

### Rule Coverage

| Rule | Test(s) | Status |
|------|---------|--------|
| Pydantic `extra: forbid` | `test_payload_extra_field_rejected` | failing (ImportError) |
| Validated constructors (`min_length=1`) | `test_payload_blank_region_id_rejected` | failing (ImportError) |
| Wiring test required (CLAUDE.md) | `test_overlay_emit_called_from_encounter_transition_dispatch` | failing (ImportError) |
| Wiring test required (CLAUDE.md) | `test_dispatch_registry_includes_location_overlay_changed` | failing (ImportError) |
| Round-trip serialization | `test_message_roundtrip` | failing (ImportError) |
| Backward compatibility (54-6 contract) | `test_build_effective_manifest_accepts_empty_overlays_default` | **passing (by design — backcompat probe)** |
| OTEL observability | Verified via existing `_watcher_publish` call in plan's emit-helper spec | n/a (Dev wires `location_overlay_changed.emitted`) |
| No silent fallback | `test_active_overlays_for_empty_when_bound_room_id_mismatch`, `test_activate_skips_when_encounter_has_no_overlay`, `test_deactivate_skips_when_no_prior_overlay` | failing (no module/field) |

**Rules checked:** 8 of 8 applicable rules from CLAUDE.md + ADR-109 §5.5 + 54-6 contract have explicit test coverage. No `lang-review/python.md` checklist is installed in `.pennyfarthing/gates/` — see Delivery Findings.

**Self-check:** Zero vacuous tests. Every test asserts a specific value, count, or behavior — no `let _ =`, no `assert!(True)`, no `is_none()` on always-None. The "unexpected pass" (`test_build_effective_manifest_accepts_empty_overlays_default`) was intended to pass; it's the explicit 54-6 backcompat probe per plan Task 2 Step 1.

**Watch items for Dev:**
- `EncounterLocationOverlay` is in `sidequest.protocol.models` (54-2). The `from sidequest.protocol.models import EncounterLocationOverlay` import inside `encounter.py` may create a circular import. The plan flags this and provides the `TYPE_CHECKING` guard pattern as fallback. If the direct import errors, use the guard.
- `_build_effective_manifest` and `resolve` both need the `overlays=` kwarg; the plan's signature change uses `overlays: Iterable[EncounterLocationOverlay] = ()` (empty tuple). Mine uses an explicit `list` default in tests but accepts iterable — no friction.
- The dispatch registry test does a flexible lookup. If the project registers messages via something other than a dict in `sidequest.protocol.messages`, the test falls back to a source-text grep that looks for the literal string `"LOCATION_OVERLAY_CHANGED": LocationOverlayChangedMessage`. Dev should ensure that exact pattern lands somewhere reachable.
- The wiring test `test_overlay_emit_called_from_encounter_transition_dispatch` counts `_maybe_emit_location_overlay_changed(` mentions in `websocket_session_handler.py` — needs ≥3 (definition + activate + deactivate). Plan's Task 6 Steps 5 + 6 cover both call sites.
- For the 54-2 snapshot-emit test (AC-8): `_maybe_emit_location_description` must call `get_location_prose` + `active_overlays_for` after the `prose` variable is finalized so the suffix actually lands in `payload.prose`.

**Handoff:** To Dev for implementation (Major Charles Emerson Winchester III).

## Dev Assessment

**Implementation Complete:** Yes
**Status:** GREEN — all 33 story-54-7 tests pass; full server suite 6851/6851; UI tsc clean; server lint clean.

**Files Changed:**

*sidequest-server* (`feat/54-7-encounter-location-overlay`, commit `455fb25`):
- `sidequest/game/encounter.py` — `StructuredEncounter.location_overlay` field + import.
- `sidequest/game/location_resolver.py` — `_build_effective_manifest` + `resolve` accept `overlays=` kwarg (default `()`).
- `sidequest/game/location_view.py` (new) — `get_location_manifest`, `get_location_prose`, `active_overlays_for` per ADR-109 §5.5.
- `sidequest/protocol/enums.py` — `MessageType.LOCATION_OVERLAY_CHANGED` enum value.
- `sidequest/protocol/models.py` — `LocationOverlayChangedPayload`.
- `sidequest/protocol/messages.py` — `LocationOverlayChangedMessage` + registration in `_Phase1Variant` discriminated union.
- `sidequest/protocol/__init__.py` — re-exports for the new payload + message classes.
- `sidequest/server/websocket_session_handler.py` — `_maybe_emit_location_overlay_changed` helper + activate/deactivate call sites; updated `_maybe_emit_location_description` to populate `payload.prose` (with overlay suffix) and `payload.overlays` from the live snapshot.
- `tests/protocol/test_enums.py` — message-count contract bumped 50 → 51 with rationale chained on the docstring.
- 5 new test files + 1 extension to the 54-2 test file — already committed under the RED phase, lightly tweaked here (test file imports moved function-scoped to dodge the pre-existing circular import; dispatch test rewritten to round-trip through `GameMessage.parse_json` since this codebase uses discriminated unions, not dict registries).

*sidequest-ui* (`feat/54-7-encounter-location-overlay`, commit `e7b2efa`):
- `src/types/protocol.ts` — `MessageType.LOCATION_OVERLAY_CHANGED` const value.
- `src/types/payloads.ts` — `LocationOverlayChangedPayload` interface.

**Tests:** 33 story-54-7 tests + 6818 pre-existing — 6851/6851 passing. UI `npx tsc --noEmit` clean. Server `ruff check` clean.

**Branches Pushed:**
- `sidequest-server` `feat/54-7-encounter-location-overlay` → origin
- `sidequest-ui` `feat/54-7-encounter-location-overlay` → origin

**Wiring Verified:**
- `LocationOverlayChangedMessage` registered in `_Phase1Variant` discriminated union — wire payloads with `type: "LOCATION_OVERLAY_CHANGED"` decode to the right class (proven by `test_dispatch_registry_includes_location_overlay_changed` round-trip).
- `_maybe_emit_location_overlay_changed` invoked from `websocket_session_handler.py` with 2 production call sites (activate + deactivate); static wiring proof in `test_overlay_emit_called_from_encounter_transition_dispatch` asserts ≥3 mentions (def + 2 calls).
- `_maybe_emit_location_description` now layers the active overlay onto `payload.prose` + `payload.overlays`; verified by `test_emit_includes_active_overlay_in_payload` end-to-end through the synthetic-world fixture.
- TS types exported from `payloads.ts` and `protocol.ts` so the 54-9 UI consumer can typecheck against them.

**OTEL:** `location_overlay_changed.emitted` watcher event fires on every emit with `region_id`, `transition`, and `overlay_count` fields — GM panel sees both edges. Dedicated `location.overlay.*` OTEL spans are 54-8's job per scope.

**Handoff:** To verify phase (TEA — Radar O'Reilly) for the simplify-and-quality pass.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned
**Mismatches Found:** None

The `spec-check` gate passed: all 9 ACs are covered in the Dev Assessment, implementation is marked complete, and both TEA + Dev deviation subsections are properly formatted.

Substance review — spot-checked the three highest-risk ACs against the actual diff:

- **AC-3 (empty-base suffix-only):** `sidequest/game/location_view.py:get_location_prose` — `if not authored_description: return joined_suffixes` — no orphan separator. ✓
- **AC-7 (wiring ≥2 call sites):** `grep -c _maybe_emit_location_overlay_changed sidequest/server/websocket_session_handler.py` returns 3 (def + activate + deactivate). ✓
- **AC-8 (snapshot emit includes overlay):** `_maybe_emit_location_description` now computes `effective_prose = get_location_prose(...)` and populates `payload.overlays` from `active_overlays_for(...)`. ✓

The three Dev deviations are all minor and well-justified:

1. **Discriminated-union dispatch over dict-registry** — Honest naming of how Python dispatch actually works post-port (ADR-082). The round-trip test through `GameMessage.parse_json` is a stronger wiring proof than a literal-string grep would have been. **No action** — keep as is.
2. **Encounter-overlay emit fires unconditionally, not nested in room-change branch** — Caught a real defect in the plan's placement guidance: overlay activation can happen without a room change (a bar fight ignites in the current room). Code correctly decouples the emit from room-change while still scoping to where `_emit_shared_world_frame` is in scope. **No action** — this is the correct shape.
3. **Function-scoped imports in `test_location_overlay_emit.py`** — Matches the established 54-2 workaround for the pre-existing `websocket_session_handler ↔ session_handler` circular import. **No action** — the circular import itself is logged as a Delivery Finding for a future cleanup story.

The `LocationDescriptionOverlaySummary` shape from 54-2 was reused without modification across all three new payload consumers (`LocationDescriptionPayload.overlays`, `LocationOverlayChangedPayload.overlays`, the snapshot-emit summary list inside `_maybe_emit_location_description`) — clean reuse, no proliferation.

**Decision:** Proceed to review.

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed — 33/33 story tests + 6818 pre-existing server tests pass.

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 10 (8 server + 2 UI)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding (medium) | overlay-summary construction duplicated between `_maybe_emit_location_description` and `_maybe_emit_location_overlay_changed`; suggests `build_overlay_summaries(...)` helper in `location_view.py` |
| simplify-quality | 2 findings (high) | TS `LocationOverlayChangedMessage` interface + `TypedGameMessage` union entry both missing in `sidequest-ui/src/types/payloads.ts` |
| simplify-efficiency | clean | no findings |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 medium-confidence finding (reuse)
**Deferred (out-of-scope):** 2 high-confidence findings (quality — see below)
**Reverted:** 0

**Overall:** simplify: clean (no changes applied)

### Why no high-confidence fixes were applied

The simplify-quality findings (TS `LocationOverlayChangedMessage` interface + `TypedGameMessage` union entry) are real gaps, but they are **explicitly out of scope for 54-7**:

- Plan Task 7 says: *"The actual UI consumer ships in 54-9. This task just lands the wire types so the typed message can be matched in `useStateMirror`."*
- AC-9 reads: *"TS payload types in `sidequest-ui/src/types/payloads.ts` mirror the pydantic shape."* — payload types, not message-wrapper types.
- The same pattern is consistent across the sibling stories that 54-7 mirrors: `LocationDescriptionMessage` (54-2), `TacticalGridMessage` (ADR-096 Task 20b), and `DungeonMapMessage` (Sünden BETTER fix) are *all* absent from the `TypedGameMessage` union. The Message wrapper interface + union entry are consistently added when the UI consumer actually consumes the message.
- Architect spec-check decision was "Proceed to review" without flagging this — concurrent independent judgment.

Auto-applying these "high-confidence" findings would extend 54-7's scope beyond its plumbing charter and break parity with the established 54-2 pattern. Logged as a deviation (Dev section) and a Delivery Finding so 54-9 picks them up explicitly.

### Why the reuse finding was not applied

The medium-confidence reuse finding identifies a real ~10-line duplication of `LocationDescriptionOverlaySummary` construction across two emit functions. Per the verify-workflow rules, medium-confidence findings are **flagged, not auto-applied**, because:

- Extracting `build_overlay_summaries(...)` to `location_view.py` would add one helper for two callers — Rule of Three not satisfied yet.
- The duplication is bounded (5-9 lines each) and the two call sites read distinct snapshot state (live encounter vs prior overlay), so the helper would carry a non-trivial branch.
- Better extracted in 54-9 (or a future overlay story) when the multi-encounter seam actually populates more callers.

### Quality Checks

- `just server-test`: 6851 passed, 396 skipped, 0 failed
- `just server-lint`: clean
- `just client-lint`: 1 pre-existing warning (`src/App.tsx:1694:6` useEffect deps — present on `develop`, unchanged by 54-7)
- `npx tsc --noEmit` in `sidequest-ui`: clean
- `npx tsc -b`: failed on sibling project `~/Projects/dice-lib` (`TS1484` verbatimModuleSyntax) — pre-existing, unrelated to 54-7

No regressions caused by 54-7.

### Delivery Findings

Appended to the Delivery Findings section above. Two non-blocking findings logged under `### TEA (test verification)`.

**Handoff:** To Reviewer for code review (Colonel Sherman Potter).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 code smells; 6851 passed, 0 failed | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled subagent returned, 8 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed (preflight), 0 dismissed, 0 deferred. Reviewer added 1 minor observation from own diff read (see assessment below).

## Reviewer Assessment

**Decision:** Approve.

### Preflight (mechanical)

- Tests: 6851 passed, 0 failed, 396 skipped (baseline, no new skips).
- Lint: server clean; UI lint shows a pre-existing `useEffect` warning in `App.tsx:1694` that is not in this diff.
- TypeCheck: `npx tsc --noEmit` clean in sidequest-ui.
- Code smells: zero TODOs / FIXMEs / `console.log` / `dbg!` / `it.skip` introduced.
- Branches: both 1 commit behind `develop` (the `feat/57-1` recency-window commit merged after these branches were cut). No conflicts; preflight recommends a rebase before merge.

### Adversarial diff read (Reviewer's own pass)

The thematic subagents (edge-hunter, silent-failure, test-analyzer, type-design, security, simplifier, rule-checker) are disabled by project settings, so I carried their domains myself against the diff (1316 server lines + 32 UI lines).

**Wiring & lifecycle (would have been edge-hunter):**

- `_maybe_emit_location_overlay_changed` invoked 3 times in `websocket_session_handler.py` (def + activate + deactivate). Confirmed via `grep -c`. Matches AC-7.
- Encounter activate is gated `now_live and not prior_live and now_encounter is not None`. Encounter deactivate is gated `encounter_resolved_this_turn and prior_encounter is not None and prior_encounter.location_overlay is not None`. Both edges in the existing narration turn loop are correctly covered.
- Edge case "encounter ignites AND resolves same turn": cannot occur. `encounter_resolved_this_turn` requires `encounter_unresolved_before` to be true, which requires `prior_live=True`. If `prior_live=False`, no false deactivate.
- Edge case "session resume with live overlay": `_maybe_emit_location_description` (54-2 path) now populates `payload.prose` (effective) + `payload.overlays` so reconnect sees overlay state without waiting for delta. Covered by `test_emit_includes_active_overlay_in_payload`.
- Edge case "encounter with overlay bound to a different room than the party is in": `active_overlays_for` returns `[]` on `bound_room_id != region_id`. Snapshot emit drops it cleanly. ✓
- Deactivate emit broadcasts `region_id=prior_overlay.bound_room_id` even if that room isn't the party's current room — UI sees a clear for a region it never had an overlay on. Minor; harmless idempotent no-op on the consumer.

**Silent failures (would have been silent-failure-hunter):**

- `transition` is validated with `raise ValueError`, not a silent no-op fallback. ✓ — matches "No Silent Fallbacks" principle.
- `getattr(sd, "genre_slug", "")` default to empty string in the watcher payload mirrors the existing 54-2 emit (`getattr(sd, "player_id", "")`). Defensive against `MagicMock` test fixtures, not a production silent-fallback. The watcher event itself fires unconditionally so the GM panel sees the transition. ✓

**OTEL observability:**

- `_watcher_publish("location_overlay_changed.emitted", ...)` fires on every emit with `genre`, `world`, `region_id`, `transition`, `overlay_count`. Both transitions surface on the GM panel. ✓ — matches the OTEL observability principle. Dedicated `location.overlay.*` OTEL spans are 54-8's job per scope.

**Test design (would have been test-analyzer):**

- 33 new tests + 1 contract-count bump (`tests/protocol/test_enums.py` 50 → 51 with rationale chained).
- AC coverage matrix: AC-1 (2 tests), AC-2 (7 tests, plus 1 explicit backcompat probe that passes by design), AC-3 (11 tests), AC-4 (6 tests), AC-5/6/7 (6 tests, includes the wiring grep test that asserts ≥3 call-site mentions), AC-8 (1 extension test against the 54-2 fixture), AC-9 (out-of-band via UI tsc).
- No vacuous assertions. The `test_build_effective_manifest_accepts_empty_overlays_default` is intentionally passing as the 54-6 backcompat probe (TEA self-checked).
- The TEA-rewritten `test_dispatch_registry_includes_location_overlay_changed` round-trips through `GameMessage.parse_json` — stronger than the original literal-string grep would have been.

**Type design:**

- `LocationOverlayChangedPayload` uses `model_config = {"extra": "forbid"}` + `region_id: str = Field(min_length=1)` — both enforced and tested.
- `EncounterLocationOverlay` (54-2) likewise uses `extra: forbid` and `min_length=1` on `bound_room_id`. Reused unchanged.
- `LocationDescriptionOverlaySummary` reused without modification across three consumers (good — no shape proliferation).
- The discriminated-union dispatch registration in `_Phase1Variant` is the right shape post-port (ADR-082); honestly named in the Dev deviation log.

**Security:**

- No user input crosses the new code path. The overlay shape is built from authored content + server-managed encounter state.
- `region_id`, `encounter_id`, `prose_suffix` are server-emitted; the UI receives but does not echo back.
- No new injection surface, no new auth/authz pivot.

**Simplifier observation (minor, non-blocking):**

`_maybe_emit_location_description:914` reads:
```python
encounter_id_str = f"{enc.encounter_type}@{room_id}" if enc is not None else ""
```
This sits inside `for overlay in active_overlays`. `active_overlays_for` requires `enc is not None and not enc.resolved` to return a non-empty list, so when this loop iterates, `enc` is guaranteed non-None — the `else ""` branch is unreachable. The check is defensive but redundant. **Decision: dismiss** — defensive against a future refactor that loosens the `active_overlays_for` guarantee, and consistent with the codebase's general defensive `getattr` style around `snapshot.encounter`.

### Rule Compliance (CLAUDE.md + SOUL.md)

- **No Silent Fallbacks:** ✓ — bad transition raises ValueError; all guards are explicit early-returns, not silent ones.
- **No Stubbing:** ✓ — every code path is fully implemented end-to-end. `location_view.py` is pure functions wired into a live consumer.
- **Don't Reinvent — Wire Up What Exists:** ✓ — reuses `LocationDescriptionOverlaySummary` (54-2), `_build_effective_manifest` seam (54-6), `_emit_shared_world_frame` (45-1), `_watcher_publish` (project-wide).
- **Verify Wiring, Not Just Existence:** ✓ — wiring test asserts ≥3 mentions; emit fires from the turn loop, not just defined.
- **Every Test Suite Needs a Wiring Test:** ✓ — `test_overlay_emit_called_from_encounter_transition_dispatch` and the Dev-rewritten dispatch round-trip test cover both axes.
- **OTEL Observability Principle:** ✓ — `location_overlay_changed.emitted` event on every transition. 54-8 will wrap in dedicated spans.

### Deviations review

All three Dev deviations and three TEA deviations read clean and defensible. The pydantic-discriminated-union deviation is actually a notable improvement over the plan's stale dict-registry assumption. The emit-placement deviation (post-room-change, unconditional on room change) catches a real correctness issue the plan missed.

### Outstanding non-blocking findings (carry forward, not blocking)

- TS `LocationOverlayChangedMessage` wrapper + `TypedGameMessage` union entry — deferred to 54-9 by plan, consistent with the 54-2 / TacticalGrid / DungeonMap pattern.
- Pre-existing circular import `websocket_session_handler ↔ session_handler` — function-scoped test imports as workaround.
- Pre-existing `tsc -b` failure on sibling `dice-lib` project — unrelated to 54-7.
- Both branches 1 commit behind develop — recommend rebase before merge (SM finish-phase concern).
- Medium-confidence reuse opportunity: extract `build_overlay_summaries(...)` to `location_view.py` once a third caller emerges (currently 2 callers; Rule of Three not satisfied).

**Final decision:** Approve. Merge after rebase onto current develop.

**Handoff:** To spec-reconcile (Architect — Major Houlihan).

### Architect (reconcile)

I audited the existing TEA and Dev deviation entries against the plan, the story/epic context, and the implementation diff. All six entries have the full 6-field format, quote accurate spec source text, and describe the implementation truthfully. The "Dispatch via discriminated union" deviation is well-defended (Rust→Python port-era assumption mismatch); the "Emit fires unconditionally" deviation is actually a *correctness improvement* over the plan; the "Function-scoped imports" deviation matches the established 54-2 workaround.

One missed deviation surfaced during my audit — the inlined `_overlay_encounter_id` formatter:

- **`_overlay_encounter_id` helper inlined instead of extracted**
  - Spec source: implementation plan `docs/superpowers/plans/2026-05-19-story-54-7-encounter-location-overlays.md`, Task 5 Step 3
  - Spec text: "…and add the `_overlay_encounter_id` helper alongside `_maybe_emit_location_description`:" followed by a dedicated function definition that returned `f"{enc.encounter_type}@{region_id}"`.
  - Implementation: The encounter-id formatter is inlined at the call site inside `_maybe_emit_location_description` (`websocket_session_handler.py:914`: `encounter_id_str = f"{enc.encounter_type}@{room_id}" if enc is not None else ""`) and at the call site inside `_maybe_emit_location_overlay_changed` (`:1002`: `encounter_id_str = f"{enc.encounter_type}@{region_id}"`). No dedicated `_overlay_encounter_id` function was added.
  - Rationale: The Dev chose minimalism — two short inline f-strings rather than a helper for two callers (Rule of Three not satisfied). This is consistent with the project's Dev minimalist discipline and matches the codebase's inline-format-string style for short string templates. The trade-off is real: the simplify-reuse subagent flagged the resulting duplication (medium confidence). Reviewer dismissed that finding for the same Rule-of-Three reason.
  - Severity: trivial
  - Forward impact: minor — when a third caller surfaces (e.g. Story 54-8 OTEL spans or 54-9 UI consumer needing to round-trip the id), the right move is to lift the formatter into `location_view.py` as the simplify-reuse subagent suggested (`build_overlay_summaries(snapshot, overlay_list, region_id)`), consolidating both the id format and the summary construction. Until then the inline duplication is bounded.

No additional architectural concerns. Approving the deviation log as it stands plus the entry above.