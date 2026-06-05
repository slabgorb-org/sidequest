---
story_id: "82-7"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 82-7: Wire AffinityState tier promotion + OTEL + player-facing delta (ADR-021 track 2; game/character.py ~:55-57,102-103)

## Story Details
- **ID:** 82-7
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** 82-3 (split child)
- **Branch:** feat/82-7-wire-affinity-tier-promotion
- **Branch Strategy:** gitflow (feat/{STORY_ID}-{SLUG})

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-05T11:05:20Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-05T10:37:46Z | 2026-06-05T10:39:19Z | 1m 33s |
| red | 2026-06-05T10:39:19Z | 2026-06-05T10:51:18Z | 11m 59s |
| green | 2026-06-05T10:51:18Z | 2026-06-05T10:56:57Z | 5m 39s |
| review | 2026-06-05T10:56:57Z | 2026-06-05T11:05:20Z | 8m 23s |
| finish | 2026-06-05T11:05:20Z | - | - |

## Sm Assessment

**Story:** 82-7 — Wire AffinityState tier promotion + OTEL + player-facing delta (ADR-021 track 2). Split child of 82-3; siblings 82-6 (milestone→level-up) and 82-8 (item narrative_weight/WealthTier) are already done, so this closes the last of the three "overstated ADR-021" tracks.

**Scope (per epic 82 wiring doctrine):** AffinityState tier promotion is P6-deferred dead data today (`game/character.py ~:55-57,102-103`). To count as *wired* this story must deliver all three:
1. A real production consumer that drives AffinityState tier promotion (not data-model-only).
2. An OTEL/watcher event on the promotion decision — the GM panel is the lie-detector; no span = not wired.
3. A player-facing advancement delta (mechanics-first: Sebastien/Jade must see the tier change in a player-facing surface).

**Pattern to follow:** Mirror the wiring approach landed in siblings 82-6 and 82-8 (consumer + OTEL + player-facing delta) for consistency.

**Workflow:** tdd / phased. 3 pts, sidequest-server only. Routing to tea for RED — failing tests should assert the promotion engine fires, the OTEL event emits, and the player-facing delta surfaces.

**Decision:** Setup complete, gate ready, session + context + branch verified. Proceed to RED.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Greenfield engine wiring (ADR-021 track 2) — promotion engine, OTEL emit, and player-facing delta all need behavioral coverage + a wiring test.

The story context had **no ACs recorded** ("TEA to define during RED"). I derived the contract by faithfully mirroring the two landed sibling tracks (82-6 milestone→level-up, 82-8 gold→WealthTier), as the epic mandates ("mirror the sibling pattern").

**Test Files (all RED — fail at collection on missing symbols):**
- `tests/genre/test_models/test_affinity_tier.py` — pure resolver `resolve_affinity_tier(progress, tier_thresholds) -> int` (9 cases: floor, inclusive boundary, below-boundary, multi-tier crossing, top-clamp, no-ladder, negative, tabulated walk). Mirror of `test_milestone_levelup.py`.
- `tests/integration/test_affinity_tier_otel_wiring.py` — engine `apply_affinity_tier_ups(snapshot, progression) -> list[AffinityTierUp]`: tier mutation + `progression.affinity_tier_up` watcher emit (component=progression) + returned delta + 6 guard/no-phantom cases (below-threshold, unmatched affinity_id, no-thresholds, already-at-top no-refire, transient-list reset, multi-affinity, multi-PC). Mirror of `test_levelup_otel_wiring.py`.
- `tests/server/test_affinity_tier_turn_wiring.py` — **wiring test**: engine fires inside the real `_execute_narration_turn`; `PartyMember.affinity_advancements` surface (reflection tripwire + behavioral populate via `party_member_from_character` + negative) + mutable-default tripwire on `Character.last_affinity_tier_ups`. Mirror of `test_levelup_turn_wiring.py`.

**Tests Written:** 21 tests across 3 files, defining the full contract.
**Status:** RED — verified by testing-runner (RUN_ID 82-7-tea-red): all three files fail at collection with `ImportError` on exactly `resolve_affinity_tier`, `AffinityTierUp`, `apply_affinity_tier_ups`. No tests executed (correct — symbols don't exist).

**Contract Dev must implement (GREEN):**
1. `resolve_affinity_tier(progress: float, tier_thresholds: list[int]) -> int` in `genre/models/progression.py` (sibling of `resolve_level`/`resolve_wealth_tier`). tier = count of thresholds reached (`progress >= threshold`, ascending), clamped to `len(thresholds)`; empty/negative → 0 (No Silent Fallbacks).
2. `AffinityTierUp(ProtocolBase)` in `protocol/models.py`: `character_name, affinity_id, before, after, driver` (driver=`"affinity"`).
3. `Character.last_affinity_tier_ups: list[AffinityTierUp] = Field(default_factory=list, exclude=True)` (transient, per-turn — list because several affinities can advance in one turn).
4. `apply_affinity_tier_ups(snapshot, progression) -> list[AffinityTierUp]` in `server/dispatch/encounter_lifecycle.py`: per-character clear-then-loop over `character.affinities`, match `AffinityState.affinity_id == Affinity.name` in `progression.affinities`, skip unmatched / no-ladder, promote on `new_tier > before`, set `state.tier`, emit `_watcher_publish("state_transition", {field:"progression.affinity_tier_up", character_name, affinity_id, before, after, driver}, component="progression")`, append delta to `character.last_affinity_tier_ups`.
5. Call `apply_affinity_tier_ups(snapshot, sd.genre_pack.progression)` in `websocket_session_handler.py` right after `apply_level_ups(...)` (~line 1290).
6. `PartyMember.affinity_advancements: list[AffinityTierUp] = []` in `protocol/models.py` + populate it from `character.last_affinity_tier_ups` in `views.party_member_from_character`.

### Rule Coverage

| Rule (python.md) | Test(s) | Status |
|------|---------|--------|
| #6 test quality — distinct parametrize paths | `test_threshold_table` (8 distinct boundary cases) | failing (collection) |
| #6 test quality — no vacuous truthy | `test_tier_up_returns_player_facing_delta_record` pins `driver == "affinity"` (not bare truthy) | failing (collection) |
| #2 mutable defaults — no shared list | `test_last_affinity_tier_ups_is_not_a_shared_mutable_default` | failing (collection) |
| #9 async pitfalls — commented `asyncio.sleep` | all async tests comment the sleep ("let the async watcher publish drain") | failing (collection) |
| No-Silent-Fallbacks doctrine | `test_unmatched_affinity_id_is_silent`, `test_affinity_with_no_thresholds_never_promotes`, resolver `test_no_thresholds_is_tier_zero` | failing (collection) |
| OTEL Observability (lie-detector) | `..._publishes_state_transition`, `..._fires_inside_the_real_narration_turn` | failing (collection) |
| Wiring test (mandatory) | `test_affinity_tier_up_fires_inside_the_real_narration_turn` (real turn path, no source-text grep) | failing (collection) |

**Rules checked:** 4 of 13 lang-review rules are test-design-applicable (the rest are Dev implementation-side); all 4 covered. **Self-check:** 0 vacuous tests — every test pins specific values.

**Handoff:** To Dev (The White Rabbit) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes — all six contract pieces from the TEA Assessment landed, mirroring siblings 82-6/82-8 exactly.

**Files Changed:**
- `sidequest/genre/models/progression.py` — `resolve_affinity_tier(progress, tier_thresholds) -> int` pure resolver (count-of-reached, ascending, top-clamped; empty/negative → 0).
- `sidequest/protocol/models.py` — `AffinityTierUp` protocol delta (`character_name/affinity_id/before/after/driver`) + `PartyMember.affinity_advancements: list[AffinityTierUp]` field.
- `sidequest/game/character.py` — `Character.last_affinity_tier_ups: list[AffinityTierUp] = Field(default_factory=list, exclude=True)` transient per-turn list (+ import).
- `sidequest/server/dispatch/encounter_lifecycle.py` — `apply_affinity_tier_ups(snapshot, progression)` engine: clear-then-loop, match `affinity_id == Affinity.name`, skip unmatched/no-ladder, promote on `new_tier > before`, emit `progression.affinity_tier_up` watcher event (component=progression), append delta (+ imports).
- `sidequest/server/websocket_session_handler.py` — engine fires in the real turn pipeline right after `apply_level_ups` (+ import).
- `sidequest/server/views.py` — `party_member_from_character` copies `character.last_affinity_tier_ups` → `member.affinity_advancements`.

**Tests:** Step 1 story tests 29/29 passing (GREEN, verified by testing-runner RUN_ID 82-7-dev-green). Step 2 regression (genre models + level-up/wealth-tier siblings) 245 passing, 28 pre-existing skips, 0 failures.
**Quality:** `ruff check` clean, `ruff format --check` clean. `pyright` 12 errors on both base and head — **0 new** type errors introduced (all pre-existing noise in disposition/views, outside the added code; confirmed via stash compare).
**Branch:** `feat/82-7-wire-affinity-tier-promotion` (pushed).

**Wiring confirmed end-to-end:** engine is imported and called in `_execute_narration_turn` (not just unit-callable), emits an OTEL event the GM panel reads, and the delta reaches the player via `PartyMember`. The mandatory wiring test (`test_affinity_tier_up_fires_inside_the_real_narration_turn`) drives the real turn path and passes.

**Handoff:** To verify phase (TEA simplify + quality-pass).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (2 style notes) | N/A — 274 passed, 0 failed, lint+format clean |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings; boundaries spot-checked by Reviewer (see [EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings; silent-path audit done by Reviewer + rule-checker (see [SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 7 | confirmed 1 (Medium), 6 noted Low (non-blocking) |
| 5 | reviewer-comment-analyzer | Yes | findings | 5 | confirmed 1 (Low: stale P6-deferred), 4 noted Low |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings; type invariants spot-checked by Reviewer + rule-checker #3 (see [TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings; no boundary/auth surface in diff — verified by Reviewer + rule-checker #11 (see [SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings; complexity spot-checked by Reviewer (see [SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 4 (3× rule #6, 1× rule #9) | all test-code-only, Low; production code 0 violations |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 1 confirmed Medium (non-blocking), 13 noted Low (non-blocking), 0 Critical/High, 0 production-code violations

## Reviewer Assessment

**Verdict:** APPROVED

Story 82-7 wires ADR-021 track 2 (affinity tier promotion) faithfully mirroring the two landed siblings (82-6 milestone→level-up, 82-8 wealth tier). The production code is clean: the rule-checker found **0 violations across 67 instances** in all 13 lang-review checks + 4 CLAUDE.md doctrine rules; preflight is fully green (274 passed); my own adversarial read found no correctness defect. All findings are test-hygiene or doc-staleness at Low/Medium severity — none block per the severity rubric.

**Observations (tagged by source):**

- `[VERIFIED]` **Production consumer is real, not stubbed** — `apply_affinity_tier_ups` is called in `_execute_narration_turn` right after `apply_level_ups` (websocket_session_handler.py:1295-1296), and `test_affinity_tier_up_fires_inside_the_real_narration_turn` drives the real turn and asserts the OTEL event fires. Complies with CLAUDE.md "Verify Wiring, Not Just Existence."
- `[VERIFIED]` **OTEL lie-detector present** — promotion emits `state_transition` / `component=progression` / `field=progression.affinity_tier_up` (encounter_lifecycle.py), a new distinct key mirroring the sibling `progression.level_up`. Complies with the OTEL Observability Principle.
- `[VERIFIED]` **Player-facing surface wired end-to-end** — `views.party_member_from_character` copies `character.last_affinity_tier_ups` → `PartyMember.affinity_advancements`, proven by `test_party_member_from_character_populates_affinity_advancements_after_tier_up`. Mechanics-first delta is legible to the player (Sebastien/Jade).
- `[RULE]` Production code: **0 violations** (rule-checker, 67 instances). New public functions fully type-annotated (#3); `Field(default_factory=list)` not mutable defaults (#2); no silent exception swallowing (#1); import hygiene clean (#10). Three Low rule-#6 findings (bare-truthy guards `assert deltas`/`assert crossings`/`assert member.affinity_advancements`) — each is immediately followed by `[0]`-indexed specific field assertions that fail on a wrong list, so they cannot pass a regression silently; `assert len(...) == 1` would be stricter. One Low rule-#9 (uncommented `asyncio.sleep(0)` at turn-wiring:110) — inherited verbatim from sibling `test_levelup_turn_wiring.py:99`.
- `[TEST]` **[MEDIUM — confirmed]** The defining contract of the list field (several affinities advancing in one turn) is untested. `test_multi_affinity_only_crossers_advance` seeds fire=100/ice=0, so a buggy `return`-after-first-append would still pass it (ice never crosses). I verified the implementation is in fact correct (`continue` + append per crossing), so this is a **coverage gap, not a defect** — non-blocking (Medium per rubric), recorded as a delivery finding for follow-up/verify.
- `[TEST]` **[LOW]** Dead span scaffolding (`TracerProvider`/`WatcherSpanProcessor`/`monkeypatch.setattr(spans_module,'tracer')`) in both async test files — `_watcher_publish` (=`publish_event`) broadcasts directly to `watcher_hub` subscribers, so the tracer patch is inert; captured events come from the `_Sock` subscription. Harmless and inherited verbatim from the sibling 82-6 harness; assertions remain valid.
- `[TEST]` **[LOW]** Tautological `assert character.last_affinity_tier_ups == []` (turn-wiring:237) right after construction tests the default-factory against itself; the meaningful negative check is the `member.affinity_advancements == []` line that follows.
- `[DOC]` **[LOW]** `AffinityState` class docstring still reads "P6-deferred … not needed for narration" (character.py:55-57) — now stale: the field is mutated every turn. Recorded as a delivery finding.
- `[DOC]` **[LOW]** Resolver described as "mirrors `resolve_wealth_tier`'s ascending-cap walk" in test docstrings — the algorithms differ (count-of-crossed vs first-container walk). Cosmetic.
- `[EDGE]` (subagent disabled — Reviewer spot-check): boundary cases are well covered by `test_threshold_table` (below/on/above each of 3 thresholds + cap), no-ladder, unmatched-id, already-at-top, negative progress. The `min(tier, len(thresholds))` clamp in `resolve_affinity_tier` is **redundant** (sum can't exceed len) but harmless/defensive — `[SIMPLE]` Low. Degenerate edge: a `tier_threshold` of `0` would conflict with the `if progress <= 0: return 0` guard, but a zero threshold is nonsensical authoring (tier 0 is the floor) — non-issue.
- `[SILENT]` (subagent disabled — Reviewer + rule-checker): the `if not thresholds: continue` and `if new_tier <= before: continue` skips are **intentional documented no-phantom guards**, not silent fallbacks — both explicitly tested. No swallowed errors; no try/except added.
- `[TYPE]` (subagent disabled — Reviewer + rule-checker #3): `AffinityTierUp` is a proper `ProtocolBase` model with typed required fields; engine signature fully annotated; runtime import (not `TYPE_CHECKING`) is correct because Pydantic v2 evaluates annotations at class creation.
- `[SEC]` (subagent disabled — Reviewer + rule-checker #11): no new boundary — inputs are validated Pydantic model instances from session state, outputs are read-only outbound projection; no SQL/HTML/path/user-input surface.
- `[SIMPLE]` (subagent disabled — Reviewer): implementation is minimal and mirrors the sibling; only the redundant clamp noted above.

**Data flow traced:** `AffinityState.progress` (session state) → `apply_affinity_tier_ups` (turn pipeline) → `resolve_affinity_tier` → tier mutation + `AffinityTierUp` delta → `character.last_affinity_tier_ups` → `views.party_member_from_character` → `PartyMember.affinity_advancements` → client. Safe: all typed, no user-input boundary, transient delta cleared each turn (no stale resurfacing).

**Pattern observed:** Faithful sibling-mirror of `apply_level_ups` (encounter_lifecycle.py) — same OTEL convention, same transient-`exclude=True` delta, same clear-then-loop structure. Good consistency.

### Rule Compliance

| Rule | Governed symbols in diff | Verdict |
|------|--------------------------|---------|
| #1 silent exceptions | resolve_affinity_tier, apply_affinity_tier_ups, all new fields, views populate | ✅ compliant (no try/except) |
| #2 mutable defaults | Character.last_affinity_tier_ups, PartyMember.affinity_advancements, both fn signatures | ✅ `default_factory=list`; no bare-list defaults |
| #3 type annotations | resolve_affinity_tier, apply_affinity_tier_ups, AffinityTierUp (5 fields), 2 model fields | ✅ fully annotated |
| #6 test quality | 21 tests | ⚠️ 3 Low bare-truthy guards + 1 tautological + multi-crossing gap (Medium); all non-blocking |
| #9 async pitfalls | sleep(0) calls, get_event_loop() | ⚠️ 1 Low uncommented sleep(0), deprecated get_event_loop() — both inherited from sibling |
| #10 import hygiene | character.py, encounter_lifecycle.py, protocol/models.py imports | ✅ explicit, no star, no cycles |
| #11 input validation | all (no boundary surface) | ✅ N/A — internal typed models only |
| No Silent Fallbacks | no-ladder skip, no-crossing skip | ✅ intentional documented guards, tested |
| No Stubbing / wiring | production call site + views populate | ✅ real consumers, behaviorally tested |
| OTEL Observability | apply_affinity_tier_ups emit | ✅ component=progression, distinct field key |

### Devil's Advocate

Let me argue this code is broken. **First attack — the list never fills with more than one item.** The entire reason a new protocol type and list field were introduced (Dev's logged deviation) is "several affinities advance in one turn." Yet not one test seeds two affinities both above threshold on the same character. If Dev had written `return crossings` inside the inner loop instead of `continue`, every existing test would still pass — `test_multi_affinity_only_crossers_advance` has ice at progress 0, so the early return after fire's append produces exactly the asserted `["fire"]`. So the marquee feature could be silently half-broken and the suite would be green. *Mitigation:* I read the actual implementation — it uses `continue` and appends per crossing; the path is correct. The gap is coverage, not behavior. Recorded as a Medium follow-up.

**Second attack — stale "P6-deferred" lies to the next reader.** `AffinityState`'s docstring says the field is deferred and "not needed for narration," but this PR makes it live and mutated every turn. A future dev refactoring narration could delete or skip it trusting the docstring. *Mitigation:* doc-only; the code is wired and tested. Low, recorded.

**Third attack — the inert OTEL harness fools a debugger.** Both async test files install a TracerProvider + span processor + tracer monkeypatch that does nothing for this path. A maintainer debugging a failure would chase the span machinery while the real signal flows through the `watcher_hub` subscription. *Mitigation:* harmless, inherited from the reviewed sibling; assertions are valid.

**Fourth attack — unsorted/zero thresholds.** A content author who writes `tier_thresholds: [50, 10, 25]` gets a count-based result that's correct-but-surprising; a `[0, …]` ladder collides with the `progress <= 0` guard. *Mitigation:* matches the existing ascending-convention of wealth tiers; degenerate authoring, flagged as a content note in the deviation log. None of these rise to Critical/High. The change is sound.

**Handoff:** To SM for finish-story.

## Impact Summary

**Story Status:** APPROVED by Reviewer, ready to finish

**Scope Completed:** All three wiring tracks per epic-82 doctrine:
1. ✅ Real production consumer: `apply_affinity_tier_ups` called in `_execute_narration_turn` turn pipeline (not data-model-only stub)
2. ✅ OTEL/watcher event: `state_transition` / `component=progression` / `field=progression.affinity_tier_up` emits on each tier promotion (GM panel lie-detector present)
3. ✅ Player-facing delta: `PartyMember.affinity_advancements` surfaces list of `AffinityTierUp` records (mechanics-first legible to Sebastien/Jade)

**Implementation Quality:**
- Tests: 29/29 passing (21 story tests + 245 regression, 0 failures)
- Lint: Clean (`ruff check`, `ruff format` both pass on changed files)
- Type Safety: 0 new type errors introduced
- Production Code Rule Violations: 0 across all 13 CLAUDE.md rules + 4 doctrine checks

**Key Findings (non-blocking):**
- **Medium (coverage gap):** Multi-affinity tier-up contract is correct but under-tested — test seeds only single-affinity crossings. Reviewer verified implementation uses `continue` (not `return`) and appends per crossing; recorded as follow-up test improvement.
- **Low (doc staleness):** `AffinityState` class docstring still says "P6-deferred … not needed for narration"; field is now live and mutated every turn. Recorded as follow-up doc update.
- **Low (redundant but harmless):** `min(tier, len(tier_thresholds))` clamp in resolver is defensive but unnecessary (count can't exceed len).

**Data Flow Verification (end-to-end):**
`AffinityState.progress` (session state) → `apply_affinity_tier_ups` (turn pipeline) → `resolve_affinity_tier` → tier mutation + OTEL event + `AffinityTierUp` delta → `character.last_affinity_tier_ups` → `views.party_member_from_character` → `PartyMember.affinity_advancements` → client UI

**Critical Caveat (non-blocking Question findings):**
No production code currently seeds `Character.affinities` at chargen or increments `AffinityState.progress` at runtime. The promotion engine is fully wired and correct, but in real play it's a zero-op: no affinities to iterate, no progress to cross. Epic-82's own wiring doctrine states "a subsystem that can't actually engage isn't live." This story's scope is the **promotion engine** (complete and tested); the **feed** (chargen seeding + runtime accumulator) is a separate follow-up story (recommend 82-follow-up-1, 82-follow-up-2 in backlog). The engine is ready; the content flow is not. Reviewer approved as-is; findings logged for follow-up.

**Design Deviations (accepted):**
- New `AffinityTierUp` protocol type (not reusing `AdvancementDelta`) — necessary to carry `affinity_id` (which scalar lacks) and support multiple crossings/turn via list field
- Threshold semantics = count-of-reached, ascending, top-clamped — mirrors existing wealth-tier convention; assumes packs author thresholds ascending

**Verdict:** Ready to finish. All acceptance criteria met (wired engine, OTEL event, player-facing surface). Non-blocking findings logged for future refinement. No blockers.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): Nothing feeds `AffinityState.progress` for *character* affinities at runtime — so once promotion is wired, no PC will ever cross a threshold in real play. The narrator-emitted `affinity_progress: list[tuple[str,int]]` signal routes to **resource pools** via `apply_resource_patches` (`encounter_lifecycle.py ~:1593`), NOT to `character.affinities`. The sibling track-1 had its feed (`award_turn_xp` → `core.xp`) already live; track-2's feed does not exist. Affects `server/dispatch/encounter_lifecycle.py` / the turn pipeline (a `progress` accumulator for character affinities). Story 82-7's title scopes the *promotion engine* (progress → tier + OTEL + delta), which my tests pin; whether the accumulation feed is in-scope here or a follow-up is a Dev/Architect call — flag loudly either way so the wiring isn't declared "live" while no PC can actually advance (epic 82's own anti-pattern). *Found by TEA during test design.*
- **Gap** (non-blocking): `AffinityState.affinity_id` is matched against `Affinity.name` (the `Affinity` model has no `id` field). Packs must author `progression.affinities[].name` to equal the `affinity_id` seeded onto characters, or promotion silently no-ops (correctly, per No-Silent-Fallbacks — but worth a content-authoring note). Affects pack `progression.yaml` authoring + chargen affinity seeding. *Found by TEA during test design.*

### Reviewer (code review)
- **Improvement** (non-blocking): Add a multi-crossing test — one character with two affinities (e.g. fire=100 and ice=100) both above threshold in the same call — asserting `len(deltas)==2`, `len(last_affinity_tier_ups)==2`, and two OTEL events with correct `affinity_id` attribution. This is the defining contract of the list field and is currently the only path a `return`-instead-of-`continue` regression could break undetected. Affects `tests/integration/test_affinity_tier_otel_wiring.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): `AffinityState` docstring still says "P6-deferred … not needed for narration" but the field is now mutated every turn by `apply_affinity_tier_ups`. Update the marker to reflect it is live. Affects `sidequest/game/character.py` (~:53-57). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The `min(tier, len(tier_thresholds))` clamp in `resolve_affinity_tier` is redundant (the `sum(...)` can never exceed `len`). Harmless; could be simplified to just the `sum`. Affects `sidequest/genre/models/progression.py`. *Found by Reviewer during code review.*

### Dev (implementation)
- **Question** (non-blocking): **Corroborates TEA's accumulation-source finding.** I confirmed during implementation that the promotion engine is now fully wired (turn pipeline → engine → OTEL → PartyMember), but **no production code increments `AffinityState.progress` for character affinities** — and crucially, **no chargen path seeds `Character.affinities` either** (the field defaults to `[]`). So in real play today the engine is a correct no-op: zero affinities to iterate, zero progress to cross. This story's title scopes the *promotion engine* (which is complete and tested), but per epic-82's own wiring doctrine ("a subsystem that can't actually engage isn't live"), a true track-2 "live" status needs two follow-ups: (1) seed `Character.affinities` at chargen from the pack's `progression.affinities`, (2) a runtime accumulator that feeds `progress` (e.g. on affinity-tagged actions, mirroring `award_turn_xp` → `core.xp`). Affects chargen (`game/character_builder*` / affinity seeding) and the turn pipeline (`encounter_lifecycle.py`). Recommend filing as 82-follow-up stories. *Found by Dev during implementation.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **New `AffinityTierUp` protocol type + list semantics rather than reusing `AdvancementDelta`**
  - Spec source: context-story-82-7.md (no ACs — "TEA to define during RED"); epic-82 mandate "mirror the sibling pattern"
  - Spec text: "Wire AffinityState tier promotion + ... + player-facing delta"; siblings surface `AdvancementDelta`/`LevelUp` (single, no entity id)
  - Implementation: defined a distinct `AffinityTierUp(character_name, affinity_id, before, after, driver)` and a **list** surface (`Character.last_affinity_tier_ups`, `PartyMember.affinity_advancements`) instead of reusing the single-valued `AdvancementDelta`
  - Rationale: an affinity delta must carry *which* affinity (`affinity_id`), which `AdvancementDelta` lacks; and a character can cross thresholds on multiple affinities in one turn, so a single-slot field (like track-1's `advancement`) would drop crossings
  - Severity: minor
  - Forward impact: adds a new protocol type + UI list field (vs one scalar) — UI consuming `affinity_advancements` must iterate
- **Threshold semantics chosen as count-of-reached, ascending, top-clamped**
  - Spec source: ADR-021 track 2; sibling `resolve_wealth_tier` (progression.py ~:205)
  - Spec text: `Affinity.tier_thresholds: list[int]` (no documented mapping rule)
  - Implementation: `tier = count(t for t in thresholds if progress >= t)`, clamped to `len(thresholds)`; empty/negative → 0
  - Rationale: mirrors `resolve_wealth_tier`'s inclusive ascending-cap walk and `resolve_level`'s top-clamp; assumes packs author thresholds ascending (as wealth tiers are)
  - Severity: minor
  - Forward impact: packs authoring thresholds out of ascending order would mis-resolve — a content note, consistent with the existing wealth-tier convention

### Dev (implementation)
- No deviations from spec. Implemented the TEA contract exactly (all six pieces, symbol names, signatures, OTEL field, and turn-pipeline placement as specified); the design decisions were TEA's, logged above.

### Reviewer (audit)
- **TEA: New `AffinityTierUp` protocol type + list semantics** → ✓ ACCEPTED by Reviewer: sound — affinity advancement must carry `affinity_id` (which scalar `AdvancementDelta` lacks) and must support multiple crossings/turn; list is the correct shape. (Note: the list's multi-crossing path is correct but under-tested — logged as a non-blocking delivery finding.)
- **TEA: Threshold semantics = count-of-reached, ascending, top-clamped** → ✓ ACCEPTED by Reviewer: consistent with the wealth-tier ascending convention; the `min()` clamp is redundant-but-harmless (noted). Unsorted/zero-threshold authoring is a degenerate content-author case, acceptable per the existing convention.
- **Dev: No deviations from spec** → ✓ ACCEPTED by Reviewer: confirmed — the implementation matches the TEA contract symbol-for-symbol; production code has 0 rule violations.
- No undocumented deviations found by Reviewer.