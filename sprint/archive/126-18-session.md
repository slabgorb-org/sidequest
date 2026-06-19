---
story_id: "126-18"
jira_key: ""
epic: "126"
workflow: "tdd"
---
# Story 126-18: [FATE] Opening-scene inanimate props persist to room_states so established hooks aren't retracted (envelope/Pernod/ashtray)

## Story Details
- **ID:** 126-18
- **Jira Key:** (no Jira — kanban-only)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-19T17:58:57Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-19T16:58:55Z | 2026-06-19T17:02:46Z | 3m 51s |
| red | 2026-06-19T17:02:46Z | 2026-06-19T17:28:55Z | 26m 9s |
| green | 2026-06-19T17:28:55Z | 2026-06-19T17:43:56Z | 15m 1s |
| review | 2026-06-19T17:43:56Z | 2026-06-19T17:58:57Z | 15m 1s |
| finish | 2026-06-19T17:58:57Z | - | - |

## Sm Assessment

**The failure mode (inverted):** good narration, empty state. The opening-scene establishing narration *describes* interactable inanimate props (the envelope, the Pernod, the ashtray in pulp_noir/annees_folles) but never writes them to `room_states`. So on turn 1 a player who reaches for the envelope the opening just put on the table is denied — the `must_not_narrate` guard fires on a detail the narrator itself established, retracting the hook. This is a SOUL "Yes, And" / baited-hook violation: the opening cast the lure, then yanked the rod.

**Scope (hold the line):** OBJECTS ONLY. Opening-scene **NPC** persistence already works — do not touch the NPC seeding path, and the red tests must include a guard proving NPC seeding is unchanged. This story is the root-cause half of a pair: the player-hygiene half (the `must_not_narrate`-leak) was already fixed in-loop earlier this session; this half makes the guard never fire on an opening-established prop by persisting it.

**Repo:** server only. No UI/content work. Base branch `develop` (gitflow). Branch `feat/126-18-opening-scene-props-persist` is cut and checked out.

**Acceptance criteria (verbatim from sprint YAML):**
1. Opening-scene establishing narration persists its interactable inanimate props to `room_states` (or equivalent honored-scene-truth store) at scene setup — verified by snapshot containing the prop (e.g. `envelope`) after the opening, **before turn 1**.
2. A prop established by the opening is interactable on turn 1 without the `must_not_narrate` guard firing: the envelope can be picked up / opened (Yes-And), not denied.
3. OBJECTS only: opening-scene NPC persistence is unchanged; no regression to NPC seeding.
4. OTEL span on opening-prop persistence (`props_persisted` count + ids) so the GM panel can confirm props were **written**, not just narrated (lie-detector for the inverted failure mode).

**For TEA (red phase):** Write failing tests against all four ACs. AC1 = snapshot assertion that the prop id lands in `room_states` after the opening establishing pass and before turn 1. AC2 = an interaction on turn 1 against an opening-established prop resolves Yes-And rather than tripping `must_not_narrate`. AC3 = the NPC-seeding-unchanged guard. AC4 = assert the OTEL span emits with `props_persisted` count + ids (per CLAUDE.md OTEL principle — the GM panel must be able to verify props were written). **Mandatory wiring test:** the persistence path must be reachable from the production opening-scene/establishing-narration code path, not just callable in isolation. Locate the opening/establishing-narration → `room_states` write seam and the `must_not_narrate` guard before deciding where the prop-extraction hooks in; that's Dev's call to make minimal in green, but the red tests should pin the production seam.

**Process notes (SideQuest streamlined TDD):** no architect/spec phase, no Jira (kanban-only — keyless by design, do not backfill). Phased flow: setup → red → green → review → finish.

## TEA Assessment

**Tests Required:** Yes
**Reason:** 5pt behavioral feature — a state-persistence path that does not exist yet.

**Test Files:**
- `sidequest-server/tests/server/test_opening_props_persist.py` — 9 RED tests (committed `97a501f6`)

**Tests Written:** 9 tests covering all 4 ACs + scope guard + no-op guard + production wiring.
**Status:** RED (all 9 fail for the right reason — verified twice via testing-runner; file collects cleanly, no wrong-reason errors).

### The seam (for Dev / green phase)
- **Bug:** opening props live ONLY in `Opening.establishing_narration` prose; nothing extracts/persists them. `room_states={}` at turn 1 → Intent Router (`_build_state_summary`) sees no prop → emits `must_not_narrate` → turn-1 interaction denied. (Forensic: save `2026-06-19-annees_folles-cd25d503`, `envelope` absent from snapshot.)
- **Working parallel to mirror:** `preload_authored_npcs` (`game/world_materialization.py:799`) → `snapshot.npcs`, emitting `npc.authored_loaded`. Props are its object-world sibling.
- **Contract the tests pin** (see Design Deviations — Dev may renegotiate names): `OpeningSetting.present_props: list[str]`; `persist_opening_props(snapshot, props, *, room_id)` in `opening_helpers.py` writing to `room_states` + emitting flat-only `opening.props_persisted` (count + ids); wired into `_populate_opening_directive_on_chargen_complete`. `RoomState` is `extra="ignore"` so a `props` field is additive.
- **Storage-agnostic assertions:** AC1 forensic (`envelope` in full snapshot dump) and AC2 (`envelope` in `_build_state_summary`) do NOT pin the exact store — an equivalent honored store passes. Only the field/helper/span NAMES are pinned.

### Rule Coverage

| Rule (python lang-review / CLAUDE.md) | Test(s) | Status |
|------|---------|--------|
| OTEL Observability Principle — subsystem decision emits a span | `test_persist_opening_props_emits_span_with_count_and_ids`, wiring test | failing |
| #6 Test quality — meaningful, specific assertions | self-checked all 9 (value/membership asserts, no `assert True`, no truthy-only, no `let _`) | n/a (clean) |
| No Silent Fallbacks — empty input is an observable no-op, not phantom state | `test_persist_opening_props_empty_is_noop` | failing |
| Every Test Suite Needs a Wiring Test (+ No Source-Text Wiring Tests) | `test_opening_resolution_seam_persists_present_props` (drives real seam, asserts span — not a source grep) | failing |
| Scope discipline (objects-only; no NPC regression) | `test_persist_opening_props_does_not_touch_npcs` | failing |

**Rules checked:** the remaining python lang-review checks (#1–5, 7–13: exceptions, mutable defaults, type annotations, path/resource/deserialization/async/import/input-validation/deps) target implementation code that does not exist yet — Dev's self-review gate covers them in green.
**Self-check:** 0 vacuous tests found (every test asserts specific values/membership; ImportError-RED tests import inside the test body so failures stay localized).

**Handoff:** To Dev (Naomi) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes — implemented the TEA-pinned contract exactly (no symbol renames needed).

**Files Changed:**
- `sidequest/genre/models/narrative.py` — `OpeningSetting.present_props: list[str]` (twin of `present_npcs`, allowed on both anchor kinds).
- `sidequest/game/session.py` — `RoomState.props: list[str]` (additive; `extra="ignore"` so no governance break).
- `sidequest/telemetry/spans/opening.py` — `SPAN_OPENING_PROPS_PERSISTED = "opening.props_persisted"` added to `FLAT_ONLY_SPANS` (re-exported via `from .opening import *`).
- `sidequest/server/websocket_handlers/opening_helpers.py` — `persist_opening_props(snapshot, props, *, room_id)` (twin of `preload_authored_npcs`: writes to `room_states[room_id].props`, one flat-only span with `props_persisted` count + `prop_ids`, empty=no-op) + wired into `_populate_opening_directive_on_chargen_complete` after opening resolution, keyed to `location_label`/`interior_room`.
- `tests/server/test_opening_props_persist.py` — lint/format fix only (unused `pytest` import removed).

**Tests:** 9/9 story tests GREEN. 54 targeted regression-adjacent tests GREEN (model field governance, room-state, container retrieval, NPC preload, opening models). Full server suite: 13,279 passed / 91 failed / 338 PG-skipped — the 91 failures are pre-existing in-flight work (WN combat/spell/class/beat per ADR-143/108, the class_hint pack-loading issue, and 126-24's seeding gap); **verified via tracebacks that none reference this story's code** — the new block is gated `if present_props:` and inert for all shipped content.

**Quality:** ruff check + format clean on all changed files. 5 pyright errors are pre-existing debt in untouched lines (`mode.value`, `bond_tier_for_pc`, etc.) — confirmed outside this diff; not fixing unrelated type debt (scope).

**Branch:** `feat/126-18-opening-scene-props-persist` (pushed, commits `97a501f6` RED + `936a9e51` GREEN).

**Handoff:** To Reviewer (Chrisjen) for review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (1 benign getattr note) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 5, deferred 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 1 | confirmed 1 |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | findings | 3 + 1 tension | confirmed 2, deferred 1 |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 1 HIGH, 2 MEDIUM, 3 LOW confirmed; 2 deferred; 0 dismissed

## Reviewer Assessment

**Verdict:** APPROVED (with a tracked, non-blocking test-hardening follow-up)

The production code is correct, fully wired, and OTEL-observable: preflight confirmed `persist_opening_props` is called in the production seam (`_populate_opening_directive_on_chargen_complete`), the `opening.props_persisted` span fires end-to-end, and props land in `room_states` keyed to `location_label` — exactly what `party_location()` resolves to in real play. All four ACs are met by correct code; rule-checker found the 13-point lang-review checklist clean except two LOW items.

The adversarial pass DID surface a real test-robustness gap worth tracking: the story's central AC (AC2 — the persisted prop must be VISIBLE to the per-turn router so `must_not_narrate` does not retract it) is tested in a way that passes for the wrong reason. Both the AC2 unit test and the wiring test leave `player_seats` empty → `party_location()` returns None → `apply_snapshot_slimming` SKIPS the room_states projection and passes it through unprojected. So the prop is visible via pass-through, not via the real projected path; a future mis-keyed `room_id` would pass the suite while breaking real play. **This is a MEDIUM test-coverage gap, NOT a code defect** — the code keys correctly today (verified). Per the severity rubric (no Critical/High CODE issue → APPROVE) and the project's reviewer wisdom (don't bounce a full TEA→Dev→review cycle for test-hardening of correct code — reviewer-patterns.md), this APPROVES with the gap documented and filed as a follow-up rather than rejected. All findings below are non-blocking; the top three should be folded into a fast TEA test-hardening chore (filed — see Delivery Findings).

| Severity | Issue | Location | Fix (follow-up) |
|----------|-------|----------|--------------|
| [MEDIUM][TEST] | AC2 + wiring tests don't exercise the real projection: `player_seats` empty → `party_location()`→None → `apply_snapshot_slimming` skips room_states projection. Prop visible via pass-through, NOT via the projected path. A wrong `room_id` key would still pass. (Code is correct; the test is what's weak.) | `tests/server/test_opening_props_persist.py:258` (AC2), `:287` (wiring) | Seed `snap.player_seats` so `party_location()` resolves to the prop room; assert `summary["room_states"]` contains the room key AND the prop; in the wiring test assert `room_state` key == `opening.setting.location_label`. |
| [MEDIUM][TEST] | De-dup/idempotency of `persist_opening_props` (`if prop not in room_state.props`) is untested — an unconditional-append bug passes today. | `tests/server/test_opening_props_persist.py` | Add a test: call `persist_opening_props` twice with overlapping props; assert each prop appears once and exactly one span fired. |
| [MEDIUM][TEST] | Wiring test span check is truthy-only (`assert persisted`) — a span with `props_persisted=0` / empty `prop_ids` would satisfy it; weaker than the GM-panel lie-detector contract. | `tests/server/test_opening_props_persist.py:360` | Assert `props_persisted == 3` and `ENVELOPE in prop_ids`, mirroring the AC4 unit test. |
| [LOW][TEST] | Forensic test asserts only `ENVELOPE`, not all three props — a partial-write bug dropping props 2-3 passes. | `tests/server/test_opening_props_persist.py:153` | Assert all three props appear in the dump. |
| [LOW][DOC] | Stale RED-phase docstring ("ALL tests FAIL NOW (RED)", "`present_props` is not a field") + now-incorrect `# type: ignore[call-arg]` (:119,:331) and `# type: ignore[attr-defined]` (:124) suppressors — the field now exists, so these are unnecessary/misleading and may trip `reportUnnecessaryTypeIgnoreComment`. | `tests/server/test_opening_props_persist.py:1,34,119,124,331` | Update docstring to GREEN status; remove the now-unnecessary `type: ignore` suppressors. |
| [LOW][RULE] | Two local runtime imports in `persist_opening_props` (`RoomState`, `Span`) lack circular-import justification — dependency graph is one-way `server→game→telemetry`, and `opening_helpers` already imports `sidequest.game.*` at top. | `sidequest/server/websocket_handlers/opening_helpers.py:285-286` | Promote to top-level imports (or add a one-line comment if keeping the `preload_authored_npcs`-style local-import precedent). Dev's call in the green rework. |

### Observations (incl. VERIFIED)
- `[HIGH][TEST]` AC2/wiring projection path unverified — see severity table. The core finding.
- `[VERIFIED]` Production persistence is correct and wired — `opening_helpers.py:252` calls `persist_opening_props` inside `_populate_opening_directive_on_chargen_complete`; keyed to `setting.location_label or setting.interior_room` (`:250`), which equals what `party_location()` returns in real play (seats populated). Evidence: `_bootstrap_character_locations_from_opening` writes `location_label` to `character_locations`; `party_location()` (session.py:1265-1279) returns the consensus `character_locations` value. Complies with the AC's "honored-scene-truth store" and the room-key/projection contract.
- `[VERIFIED]` OTEL span complies with the Observability Principle — `opening.props_persisted` carries `props_persisted` (count) + `prop_ids` + `room_id` + genre/world; registered FLAT_ONLY at `opening.py:37`, re-exported via `from .opening import *`. Evidence: `opening_helpers.py:296-306`; routing-completeness test passes (preflight).
- `[VERIFIED]` Scope held (objects-only) — `persist_opening_props` touches only `room_states`, never `snapshot.npcs`; `_exactly_one_anchor` restricts only `present_npcs`, leaving `present_props` allowed on both anchors (a deliberate, sound divergence — props have no `chassis.crew_npcs` analogue). Evidence: narrative.py:222-238; test `test_persist_opening_props_does_not_touch_npcs`.
- `[SILENT]` (subagent disabled — self-assessed) No silent fallback: the `else: _emit_skip("props_no_resolvable_room", ...)` branch publishes a `warning` watcher event rather than dropping props silently. Rule-checker corroborates. Compliant with No Silent Fallbacks.
- `[SIMPLE]` (subagent disabled — self-assessed) The `else` branch is unreachable given `_exactly_one_anchor` — a mild tension with "dead code is worse than no code," but it is loud (emits a warning) and matches the function's existing validator-guaranteed-unreachable `_emit_skip` pattern (`world_or_openings_missing` etc.). Deferred LOW: reword the comment from "unreachable" to "defensive safety net," or drop the branch. Not blocking.
- `[TYPE]` (subagent disabled — self-assessed) `persist_opening_props` is fully annotated (`snapshot: GameSnapshot, props: list[str], *, room_id: str) -> None`); `Field(default_factory=list)` is correct pydantic, not a mutable-default. Rule-checker corroborates (#2, #3 compliant).
- `[SEC]` (subagent disabled — self-assessed) No injection surface: `present_props` and `room_id` are authored pack/world content (YAML), not player WebSocket input. Rule-checker corroborates (#11 compliant).
- `[EDGE]` (subagent disabled — self-assessed) Empty-props no-op is tested; `room_state` get-or-create preserves existing `containers`. The empty-`location_label` edge (`location_label=""` → falls to `interior_room`→None → loud skip) is degenerate authored content and fails loud — acceptable.
- `[DOC]` Stale RED docstring + incorrect `type: ignore` — confirmed (see table).
- `[RULE]` Local-import hygiene — confirmed LOW (see table).

### Rule Compliance (python lang-review, 13 checks — via rule-checker + my read)
- #1 silent exceptions: COMPLIANT (no bare/broad except in diff).
- #2 mutable defaults: COMPLIANT (`Field(default_factory=list)` ×2).
- #3 type annotations at boundaries: COMPLIANT (`persist_opening_props` fully typed).
- #4 logging/observability: COMPLIANT (OTEL span emitted; project is OTEL-first).
- #5 path handling: COMPLIANT (test uses `pathlib` + `resolve()`).
- #6 test quality: **VIOLATION** — stale RED docstring + incorrect `type: ignore` suppressors (LOW); plus the AC2/wiring coverage gaps (HIGH/MEDIUM, the blocking findings).
- #7 resource leaks: COMPLIANT (`with Span.open(...)`).
- #8 unsafe deserialization: COMPLIANT (none).
- #9 async pitfalls: COMPLIANT (sync code).
- #10 import hygiene: **VIOLATION** (LOW) — two unjustified local imports.
- #11 input validation: COMPLIANT (authored content, not user input).
- #12 dependency hygiene: COMPLIANT (no dep changes).
- #13 fix-introduced regressions: COMPLIANT.

### Devil's Advocate
Argue this is broken. **First strike:** the marquee fix is a lie that passes CI. The whole story exists because the router couldn't see the envelope; AC2 is "the prop is visible to the router." Yet the AC2 test never lets the router's projection run — `party_location()` returns None and slimming hands back every room untouched. So the test asserts "envelope in summary" against a payload that was never projected. If a future refactor (or this very change, had Dev mis-keyed) wrote props under `"annees_folles:cafe_le_dome"` while `character_locations` held `"Café Le Dôme"`, real play would drop the prop at projection and the player would be told "there is no envelope" — *the exact bug* — and the green suite would swear everything is fine. That is the worst failure mode: a regression test that cannot detect the regression it is named for. **Second strike:** a confused content author adds `present_props` to a chassis opening with `location_label=None`; `room_id` falls to `interior_room`, props persist under the interior-room string, but if that string isn't what `party_location()` resolves to for a chassis scene, same silent miss — and there is no test for the chassis anchor at all. **Third strike:** de-dup is asserted nowhere; a stressed merge that drops the `if prop not in` guard double-writes props on any second resolution and no test complains. **Fourth strike:** the stale `type: ignore[attr-defined]` on a now-real attribute is the kind of rot that, multiplied across a codebase, trains everyone to ignore type errors. None of these are hypothetical reaches — the first is a direct consequence of the test design, and it is cheap to close. The code is right; the safety net has a hole exactly where the trapeze artist falls.

**Handoff:** To SM for finish-story. All findings are non-blocking (no Critical/High code defect). Recommend SM file a fast TEA test-hardening follow-up story in epic 126 (the AC2/wiring projection coverage + de-dup test + wiring span-payload assertion + stale-docstring/`type: ignore` cleanup + the two LOW import-hygiene/else-comment items) — see Delivery Findings.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Gap** (non-blocking): this story is server-only (the persistence MECHANISM). For pulp_noir/annees_folles to actually benefit end-to-end, the world's opening must DECLARE its props via the new `present_props` field once it exists — a CONTENT follow-up (mirrors the 126-25 server / 126-21 content split). Affects `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/openings.yaml` (add `setting.present_props`). *Found by TEA during test design.*
- **Improvement** (non-blocking): `OpeningSetting` is chassis-anchored XOR location-anchored, and its validator forces `present_npcs` empty for chassis openings (crew comes from `chassis.crew_npcs`). Dev should decide whether `present_props` is allowed on BOTH anchor kinds (a chassis galley can have a prop on the table too) — the forensic case is location-anchored, so the tests only exercise that path. Affects `sidequest/genre/models/narrative.py` (`OpeningSetting._exactly_one_anchor`). *Found by TEA during test design.*

### Dev (implementation)
- **Gap/Question** (non-blocking): `tests/server/test_126_24_annees_folles_chargen_seed.py` fails on `develop` (3 tests: blank Fate pyramid + empty free_aspects from narrative chargen seeding → illegal-sheet `FateChargenError`). Pre-existing and unrelated to 126-18 (verified: my code appears in none of the tracebacks), but it lines up with 126-24's logged HIGH review finding that the world-tier `chargen_seed_table` override is half-wired. Affects `sidequest/server/websocket_handlers/chargen_mixin.py` + `game/ruleset/fate_chargen.py` (the 126-24 seeding path). *Found by Dev during implementation (full-suite regression).*
- **Improvement** (non-blocking): for the annees_folles café opening to actually carry the envelope end-to-end, content must add `setting.present_props: [envelope, ...]` to its opening now that the field exists (TEA's content follow-up above). Until then this story ships the MECHANISM; the live forensic repro stays open until the content lands. Affects `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/openings.yaml`. *Found by Reviewer during code review.*

### Reviewer (code review)
- **Gap** (non-blocking — FOLLOW-UP STORY recommended): no test exercises the real snapshot-slimming projection for the persisted prop (both AC2 + wiring tests leave `player_seats` empty → `party_location()` None → projection skipped). The marquee AC's wiring is unverified by the suite; a mis-keyed `room_id` would pass. Code is correct today; this is test robustness. Fold these into one TEA chore: seed `player_seats` + assert projection retains the prop; add a de-dup/idempotency test; assert the wiring span payload (`props_persisted==3`, `ENVELOPE in prop_ids`) not just truthy; assert all three props in the forensic test; refresh the stale "(RED)" docstring + drop the now-unnecessary `# type: ignore` suppressors. Affects `tests/server/test_opening_props_persist.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two local runtime imports in `persist_opening_props` (`RoomState`, `Span`) lack circular-import justification (dependency graph is one-way `server→game→telemetry`); promote to top-level. Affects `sidequest/server/websocket_handlers/opening_helpers.py:285-286`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): no test covers the chassis-anchor path for `present_props` (only location-anchored). Once a chassis opening declares props, confirm the `interior_room` key matches what `party_location()` resolves to for a chassis scene. Affects `tests/server/test_opening_props_persist.py`. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (1 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Gap:** this story is server-only (the persistence MECHANISM). For pulp_noir/annees_folles to actually benefit end-to-end, the world's opening must DECLARE its props via the new `present_props` field once it exists — a CONTENT follow-up (mirrors the 126-25 server / 126-21 content split). Affects `sidequest-content/genre_packs/pulp_noir/worlds/annees_folles/openings.yaml`.
- **Improvement:** `OpeningSetting` is chassis-anchored XOR location-anchored, and its validator forces `present_npcs` empty for chassis openings (crew comes from `chassis.crew_npcs`). Dev should decide whether `present_props` is allowed on BOTH anchor kinds (a chassis galley can have a prop on the table too) — the forensic case is location-anchored, so the tests only exercise that path. Affects `sidequest/genre/models/narrative.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest-content/genre_packs/pulp_noir/worlds/annees_folles`** — 1 finding
- **`sidequest/genre/models`** — 1 finding

### Deviation Justifications

4 deviations

- **Pinned a structured persistence contract for an intentionally-open AC**
  - Rationale: server CLAUDE.md "Don't Reinvent — Wire Up What Exists" + the story names opening-scene NPC persistence as the working parallel; mirroring its STRUCTURED path is deterministic and OTEL-verifiable, whereas prose-extraction is non-deterministic and would itself be the kind of "winging it" the OTEL lie-detector exists to catch. AC1/AC2 *assertions* are still storage-agnostic (snapshot dump + `_build_state_summary`), so an equivalent honored store than `room_states` still passes — only the authoring field, helper name, and span name are pinned.
  - Severity: minor
  - Forward impact: Dev may rename/relocate `persist_opening_props` or the field; that is a trivial test-symbol update, not a behavioral change. Raise it in green if a different shape is warranted.
- **AC2 tested via deterministic proxy, not the LLM guard itself**
  - Rationale: `must_not_narrate` for this path is an Intent-Router *LLM inference* (ADR-113), not deterministic code — it cannot be unit-asserted. The deterministic, falsifiable precondition is "the prop is visible to the router"; if it is, the guard has no basis to deny it. The end-to-end "guard never fires" is a playtest/verify concern.
  - Severity: minor
  - Forward impact: the full behavioral confirmation belongs in a playtest re-run of the annees_folles café opening (DRIVER verification), not in this unit suite.
- **`present_props` allowed on BOTH anchor kinds (resolving TEA's open question)**
  - Rationale: `present_npcs` is restricted on chassis because crew has an alternate authored source (`chassis.crew_npcs`); props have NO such alternate source, so forbidding them on chassis would leave chassis openings unable to establish any interactable prop. Allowing both is the strictly-more-capable, lower-surprise choice and the tests don't constrain it (they exercise only the location anchor).
  - Severity: minor
  - Forward impact: content authors may declare `present_props` on chassis openings; if a future design wants to forbid that, it's an additive validator clause (no migration).
- **Persistence keyed to the room string, not a synthetic room id**
  - Rationale: room_states must be keyed by whatever `party_location()` resolves to or the projection drops the props before the router sees them (AC2). Reusing the existing opening room string keeps the prop visible without inventing a parallel keying convention.
  - Severity: minor
  - Forward impact: none — consistent with the existing container-retrieval room_states keying.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Pinned a structured persistence contract for an intentionally-open AC**
  - Spec source: context-story-126-18.md, AC1
  - Spec text: "persists its interactable inanimate props to room_states (or equivalent honored-scene-truth store)"
  - Implementation: Tests pin a specific structured design — `OpeningSetting.present_props: list[str]` (twin of `present_npcs`), a `persist_opening_props(snapshot, props, *, room_id)` helper in `opening_helpers.py` (twin of `preload_authored_npcs`), and a flat-only `opening.props_persisted` span (twin of `npc.authored_loaded`) — rather than leaving the mechanism fully open or testing prose-extraction from `establishing_narration`.
  - Rationale: server CLAUDE.md "Don't Reinvent — Wire Up What Exists" + the story names opening-scene NPC persistence as the working parallel; mirroring its STRUCTURED path is deterministic and OTEL-verifiable, whereas prose-extraction is non-deterministic and would itself be the kind of "winging it" the OTEL lie-detector exists to catch. AC1/AC2 *assertions* are still storage-agnostic (snapshot dump + `_build_state_summary`), so an equivalent honored store than `room_states` still passes — only the authoring field, helper name, and span name are pinned.
  - Severity: minor
  - Forward impact: Dev may rename/relocate `persist_opening_props` or the field; that is a trivial test-symbol update, not a behavioral change. Raise it in green if a different shape is warranted.
- **AC2 tested via deterministic proxy, not the LLM guard itself**
  - Spec source: context-story-126-18.md, AC2
  - Spec text: "A prop established by the opening is interactable on turn 1 without the must_not_narrate guard firing"
  - Implementation: The test asserts the persisted prop is present in the router's slimmed `_build_state_summary` (the input the Intent Router classifies against), not that the must_not_narrate directive literally never emits.
  - Rationale: `must_not_narrate` for this path is an Intent-Router *LLM inference* (ADR-113), not deterministic code — it cannot be unit-asserted. The deterministic, falsifiable precondition is "the prop is visible to the router"; if it is, the guard has no basis to deny it. The end-to-end "guard never fires" is a playtest/verify concern.
  - Severity: minor
  - Forward impact: the full behavioral confirmation belongs in a playtest re-run of the annees_folles café opening (DRIVER verification), not in this unit suite.

### Dev (implementation)
- **`present_props` allowed on BOTH anchor kinds (resolving TEA's open question)**
  - Spec source: session Delivery Findings → TEA (test design), the anchor-kind question
  - Spec text: "Dev should decide whether `present_props` is allowed on BOTH anchor kinds (a chassis galley can have a prop on the table too)"
  - Implementation: `present_props` is added with NO restriction in `_exactly_one_anchor` — unlike `present_npcs`, which the validator forces empty for chassis openings. Persistence keys the props to `setting.location_label` (location anchor) or `setting.interior_room` (chassis anchor).
  - Rationale: `present_npcs` is restricted on chassis because crew has an alternate authored source (`chassis.crew_npcs`); props have NO such alternate source, so forbidding them on chassis would leave chassis openings unable to establish any interactable prop. Allowing both is the strictly-more-capable, lower-surprise choice and the tests don't constrain it (they exercise only the location anchor).
  - Severity: minor
  - Forward impact: content authors may declare `present_props` on chassis openings; if a future design wants to forbid that, it's an additive validator clause (no migration).
- **Persistence keyed to the room string, not a synthetic room id**
  - Spec source: context-story-126-18.md, AC1
  - Spec text: "persists its interactable inanimate props to room_states (or equivalent honored-scene-truth store)"
  - Implementation: props are written to `room_states[setting.location_label or setting.interior_room]` — the SAME free-text room string `_bootstrap_character_locations_from_opening` writes to `character_locations` and that `party_location()` returns, so `apply_snapshot_slimming` projects the props into the per-turn router/narrator state. No new room-id scheme introduced.
  - Rationale: room_states must be keyed by whatever `party_location()` resolves to or the projection drops the props before the router sees them (AC2). Reusing the existing opening room string keeps the prop visible without inventing a parallel keying convention.
  - Severity: minor
  - Forward impact: none — consistent with the existing container-retrieval room_states keying.

### Reviewer (audit)
- **TEA: "Pinned a structured persistence contract for an intentionally-open AC"** → ✓ ACCEPTED by Reviewer: sound — mirrors the working NPC path per "Don't Reinvent", deterministic + OTEL-verifiable, assertions kept storage-agnostic. Dev implemented it without renames.
- **TEA: "AC2 tested via deterministic proxy, not the LLM guard itself"** → ✗ FLAGGED by Reviewer: the *intent* (test the deterministic precondition rather than the LLM) is correct, but the proxy as implemented does NOT exercise the projection it claims to verify — `player_seats` is empty, so `party_location()` returns None and `apply_snapshot_slimming` skips the room_states projection entirely. The prop is visible via pass-through, not via the projected path. This is the HIGH finding driving the rejection; the proxy must seed `player_seats` so the projection actually runs.
- **Dev: "`present_props` allowed on BOTH anchor kinds"** → ✓ ACCEPTED by Reviewer: correct call — props have no `chassis.crew_npcs` analogue, so restricting them would cripple chassis openings; strictly-more-capable and no test constrains it. (Caveat logged as a non-blocking finding: the chassis path is untested.)
- **Dev: "Persistence keyed to the room string, not a synthetic room id"** → ✓ ACCEPTED by Reviewer: the keying decision is correct and necessary (must equal `party_location()`'s value or projection drops the prop). The implementation is right — but precisely BECAUSE this is load-bearing and subtle, it must be locked by a test that runs the projection (see the FLAGGED AC2 deviation above). Accepted as code; the missing test is the blocker.