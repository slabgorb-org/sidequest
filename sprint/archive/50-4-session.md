---
story_id: "50-4"
jira_key: null
epic: "50"
workflow: "tdd"
---

# Story 50-4: Trope rate_per_day between-session advancement

## Story Details
- **ID:** 50-4
- **Epic:** 50
- **Workflow:** tdd
- **Stack Parent:** none
- **Points:** 5
- **Priority:** p2

## Story Context

The Trope Engine (ADR-018) defines two passive advancement rates:
- **rate_per_turn:** Ticks forward during live gameplay (e.g., 0.02 per turn)
- **rate_per_day:** Ticks forward between sessions when the game is not actively running (e.g., 0.05)

The Python port (ADR-082, 2026-04) carried the data model (`TropeDefinition.passive_progression.rate_per_day` in genre packs) but left the advancement logic unimplemented. The narrator currently emits `beat_selections` during play, which `narration_apply.py` records on `active_tropes`, but between-session advancement is missing entirely.

**Problem:** Tropes stall at session boundaries. A trope at 0.45 progress just before save-and-exit stays at 0.45 on reload; the world feels static rather than "alive" (per ADR-018 consequence).

**Solution:** On session load (after game state is hydrated from the SQLite save file), advance each active trope's progress by `(rate_per_day * elapsed_days)` before the session enters play. This ensures that stories continue to build momentum even during out-of-game time.

## Acceptance Criteria

1. **AC1 — Load-Time Advancement:** When a session is loaded from persistent storage, each active trope with a non-zero `rate_per_day` is advanced by `(trope.passive_progression.rate_per_day * days_elapsed)`. Days elapsed is calculated as `(now_timestamp - last_session_timestamp) / 86400`.

2. **AC2 — Beat Firing on Load:** If advancement crosses a beat threshold, the beat fires immediately (same semantics as in-game firing: record in `beats_fired`, emit OTEL span, do NOT call the narrator — the beat was earned passively, not from player action).

3. **AC3 — Progress Clamp:** Trope progress never exceeds 1.0. If advancement would push progress > 1.0, clamp to 1.0 and mark the trope as RESOLVED.

4. **AC4 — No Advance on First Load:** A newly-created trope (from world materialization) has `last_session_timestamp=None`. The advancement logic skips them (no time has passed yet).

5. **AC5 — OTEL Emission:** Each loaded session emits a `SPAN_TROPE_BETWEEN_SESSION_ADVANCE` event per trope that advanced, with:
   - `trope_id`
   - `days_elapsed`
   - `progress_before`, `progress_after`
   - `beats_fired_count` (count of beats that crossed thresholds during this advance pass)
   - `new_status` (if the trope resolved)

6. **AC6 — Integration Test:** Test covers:
   - Load a session from a save file created N days ago
   - Verify at least one trope advanced by the expected delta
   - Verify beats that crossed thresholds are recorded
   - Verify OTEL spans emitted
   - Verify progress is clamped to 1.0 if needed
   - Verify newly-created tropes (from prior save that hadn't been created yet) are skipped
   - Wiring test confirms the advancement call is in the production code path for session loading (not mocked away)

## Architecture Context

### Call Site
The load-time advancement should be triggered **after** the session is deserialized from the SQLite save file and **before** the first turn is dispatched. The call signature is:

```python
def advance_tropes_between_sessions(
    session: GameSession,
    now_timestamp: float,
) -> dict[str, dict[str, Any]]:
    """Advance each active trope by rate_per_day.
    
    Returns a dict mapping trope_id → {
        'progress_before': float,
        'progress_after': float,
        'beats_fired': list[float],
        'new_status': str | None,
    }
    """
```

The caller (server session load handler) passes `now_timestamp = time.time()` and the session's `created_at` / `last_save_time` field to compute `elapsed_days`.

### Data Model Context
- **TropeState** (`sidequest/game/session.py:413–431`) carries `id`, `status`, `progress`, `beats_fired` counter.
- **PassiveProgression** (`sidequest/genre/models/tropes.py:29–39`) carries `rate_per_day` (float).
- **TropeDefinition** (`sidequest/genre/models/tropes.py:42–60`) carries escalation beats at thresholds.
- Session is hydrated with `active_tropes: list[TropeState]` and has access to genre pack via `session.genre`.

### Rust Reference
The Rust implementation (`sidequest-api/src/trope.rs`) carried `TropeState::advance_between_sessions()` calling `tick()` iteratively per elapsed day. Python implementation should be similar: for each trope, for each beat in its definition, check if `progress_before < beat.at <= progress_after`, and if so, record the beat and emit OTEL span.

### OTEL Telemetry
Define `SPAN_TROPE_BETWEEN_SESSION_ADVANCE` in `sidequest/telemetry/spans/trope.py` following the pattern of `SPAN_TROPE_TICK`. The span should be emitted **once per trope that advanced**, with the delta fields above.

## Related Stories / Blockers
- **50-3:** PartyPanel companions wiring (done, independent)
- **50-5:** Scenario wire discover_clue (done, independent)
- **50-10, 50-11:** Disposition refactor (done, independent)
- No blockers; 50-4 is independent of the disposition work and scenario work.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Improvement** (non-blocking): Story `Architecture Context` shows the public function
  signature with `session: GameSession` and a `dict[trope_id → dict[...]]` return value.
  The closest existing analogue (`trope_tick.tick_tropes`) takes `snapshot: GameSnapshot, pack, *, now_turn` and returns `None`, mutating in place. Tests pin the
  consistent shape: `advance_tropes_between_sessions(*, snapshot, pack, now)` returning `None`. OTEL spans carry the per-trope diagnostic the return-dict would have. *Found by TEA during test design.*
- **Question** (non-blocking): AC5 names a `beats_fired_count` span attribute; the
  existing `trope_resolve` span uses `beats_fired_total` (cumulative). The contract test
  pins `beats_fired_count` (count of beats fired *during this advance pass*, not cumulative)
  because it matches the AC text and gives the GM panel a per-event delta. Dev should
  surface the per-pass count, not the running total. *Found by TEA during test design.*

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

## Design Deviations

None yet.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (verify)

- **Improvement** (non-blocking): Test-helper duplication between `tests/game/test_trope_tick.py` and `tests/game/test_trope_advance_between_sessions.py`. `_trope_def`, `_pack_with`, and `_seed_snapshot` are near-identical between the two files; simplify-reuse flagged extraction to `tests/game/conftest.py`. Out of 50-4 scope (requires divergent-signature reconciliation on `_seed_snapshot`). Affects `tests/game/conftest.py` and both test files. *Found by TEA during test verification.*
- **Improvement** (non-blocking): `_spans_named(exporter, name) -> list` is duplicated across ~9 OTEL test files in the repo. simplify-reuse flagged extraction to `tests/game/conftest.py` as a shared utility. Out of 50-4 scope (cross-cutting). Affects many `tests/**/*.py` files. *Found by TEA during test verification.*
- **Question** (non-blocking): pre-existing TypeScript errors at `sidequest-ui/src/App.tsx:722:11` and `sidequest-ui/src/__tests__/turn-status-wire-shape-wiring.test.tsx:35:9` block `just check-all` aggregate gate. These were already failing on develop before 50-4 (verified via `git diff --name-only develop` showing zero UI files in my diff). The UI typecheck failure is unrelated to this story but blocks the aggregate gate; recommend a tracking story to fix the `GameMessage` ↔ `Record<string, unknown>` cast. Affects `sidequest-ui/src/App.tsx`, `sidequest-ui/src/__tests__/turn-status-wire-shape-wiring.test.tsx`. *Found by TEA during test verification.*

### Reviewer (code review)

- **Improvement** (non-blocking): `PassiveProgression.rate_per_day` is typed `float` with default `0.0` but no constraint excluding NaN / negative. The engine's `if rate <= 0: continue` skips both zero and negative, but `NaN <= 0` is `False` → NaN rates would proceed and produce NaN-tainted progress arithmetic. Pack YAML never authors NaN today, but a `Field(ge=0.0)` validator on `PassiveProgression.rate_per_day` would harden the data boundary. Affects `sidequest/genre/models/tropes.py:34-35`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): If a legacy save has a tz-naive `last_saved_at` (none exist today — both writers in `persistence.py` use `datetime.now(tz=UTC)`), the subtraction `now - last_saved_at` raises `TypeError`, which propagates through `connect.py` and breaks the connect for that slug. Per user policy on legacy saves (throwaway, no migrations) this is not blocking, but a defensive `if last_saved.tzinfo is None: return` or coercion-on-load would make the engine robust to a wider class of save files. Affects `sidequest/game/trope_advance.py:75-77`. *Found by Reviewer during code review.*

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 0 (no console.log, no test skips, no TODOs, no dangerouslySetInnerHTML) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via settings |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via settings |

**All received:** Yes (1 enabled returned clean, 8 disabled per `workflow.reviewer_subagents` settings)
**Total findings:** 2 [LOW] confirmed (NaN hardening + tz-naive defense), 0 dismissed, 0 deferred

Note on disabled subagents: with 8 of 9 specialists toggled off, I am personally covering their domains in the manual review below (tagged where applicable). Per the agent rules, this is acknowledged as reduced coverage; the simplify domain was already covered during TEA verify with the same 3 subagents (`simplify-reuse`, `simplify-quality`, `simplify-efficiency`).

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:**
- **Save** → `persistence.py:369` writes `snapshot.model_copy(update={"last_saved_at": datetime.now(tz=UTC)})` to SQLite. `last_saved_at` is always tz-aware on the write path.
- **Load** → `connect.py:309` `store.load()` returns `SavedSession` whose `snapshot` carries the tz-aware `last_saved_at` (pydantic v2 deserializes ISO+offset strings as tz-aware).
- **Advance** → `connect.py:356-360` calls `advance_tropes_between_sessions(snapshot=snapshot, pack=genre_pack, now=datetime.now(tz=UTC))`. Both datetimes tz-aware → subtraction succeeds.
- **Bind** → `connect.py:478` `room.bind_world(snapshot=snapshot, ...)` lands the mutated snapshot on the room. `bind_world` is idempotent (verified at `session_room.py:38-42`: `if self._snapshot is not None: return`) — Player B in an MP race has their advance mutations silently discarded; A's already-applied mutations remain canonical.
- **OTEL** → per advancing trope, `Span.open(SPAN_TROPE_BETWEEN_SESSION_ADVANCE, {...})` emits → routed by `SPAN_ROUTES[SPAN_TROPE_BETWEEN_SESSION_ADVANCE]` to the watcher hub as `state_transition` events on `component="tropes"`. GM panel can read elapsed_days + beats_fired_count per event.

**Pattern observed:**
- The new engine mirrors `tick_tropes` (same file directory, same duck-typed pack, same keyword-only signature, same `Span.open` idiom) at `sidequest/game/trope_tick.py:79-141`. A reader who knows the per-turn engine can navigate the per-day engine without retraining. Good follow-the-pattern discipline.

**Error handling:**
- No `try/except` in the engine. Every failure mode is converted to an early-return guard *before* state mutation: `last_saved is None` → return; `delta_seconds <= 0` → return; `status != "progressing"` → continue; `tdef is None or passive_progression is None` → continue; `rate <= 0` → continue; `progress_after <= progress_before` → continue. This matches CLAUDE.md "No Silent Fallbacks" — every guard has a single clear meaning and never silently substitutes a default.
- The wire site's `connect.py:356-360` has no `try/except` either — an exception would propagate. Looking at the surrounding code, `_backfill_magic_state_on_resume` at `connect.py:342` has no try/except either, so the advance call follows the same convention. Loud failure on bad data is the agreed pattern here.

**Findings (severity-tagged):**

| Tag | Severity | Issue | Location | Notes |
|-----|----------|-------|----------|-------|
| [VERIFIED] | — | Engine signature is keyword-only with type annotations on all params and return type | `trope_advance.py:57-62` | Complies with `.pennyfarthing/gates/lang-review/python.md` rule #3 (type annotations at public boundaries). |
| [VERIFIED] | — | OTEL span is registered in `SPAN_ROUTES` AND not in `FLAT_ONLY_SPANS` | `telemetry/spans/trope.py:36-37, 141-156` | Component is `"tropes"`, all 6 AC5 attributes routed (`trope_id`, `days_elapsed`, `progress_before`, `progress_after`, `beats_fired_count`, `new_status`). Wire test `TestSpanRoutedThroughWatcher` confirms re-export from package init. |
| [VERIFIED] | — | Engine writes to `trope.progress`, `trope.beats_fired`, `trope.status` only — never touches narrator-owned fields | `trope_advance.py:89-138` | Grep confirms no `narrative_log`, `quest_log`, or `notes` mutation. Test `test_passive_fire_does_not_record_narrative_entry` pins this. Matches AC2 "do NOT call the narrator". |
| [VERIFIED] | — | Wire call sits INSIDE `if saved is not None:` branch | `connect.py:340, 356-360` | Belt-and-suspenders for AC4: both the function (None check) and the wire site (branch placement) gate against first-load advancement. Chargen-new-session path at `connect.py:507-517` never hits the call. |
| [VERIFIED] | — | MP race safety | `connect.py:356 (advance) → connect.py:478 (bind)` ↔ `session_room.py:38-42 (bind early-return)` | Player A's mutations flow into room via bind. Player B's mutations on local snapshot are discarded by idempotent bind; B observes A's already-applied state via `snapshot = room.snapshot` at `connect.py:482`. Correct — re-advancing on a duplicate load would double-count, and the architecture prevents that. |
| [VERIFIED] | — | Resolve-condition gate is consistent with the in-session engine | `trope_advance.py:118-125` vs `trope_tick.py:257-276` | Both require `progress >= 1.0 AND beats_fired >= len(escalation)`. Diverges from the literal AC3 wording (which says "if clamped, mark resolved") — flagged in Architect's spec-check Mismatch 1, recommendation A (update spec, code is the better reading). I ACCEPT that recommendation. |
| [VERIFIED] | — | Beat-firing semantics match the Rust reference summary | `trope_advance.py:107-114` | Window is `progress_before < beat.at <= progress_after` (exclusive lower, inclusive upper). Inclusive upper is necessary so an `at=1.0` beat fires when progress clamps to 1.0 (`test_progress_at_one_without_all_beats_does_not_resolve` proves this). |
| [DOC] | — | Module docstring + function docstring are present, accurate, and reference ADR-018 | `trope_advance.py:1-41, 63-73` | Manual review of docstrings against implementation: every claim in the docstring corresponds to a guard or behavior in code. Pin both with `TestEngineModuleHygiene::test_module_has_docstring` and `test_public_function_has_docstring`. |
| [TYPE] | — | `pack: Any` is duck-typed; documented in docstring and matches existing convention | `trope_advance.py:60, 65-67` | python.md rule #3 allows `Any` "only with a comment explaining why" — docstring satisfies this. |
| [SIMPLE] | LOW | Pack YAML schema permits NaN/negative `rate_per_day` | `sidequest/genre/models/tropes.py:34-35` | Engine handles `<= 0` correctly but NaN bypasses the guard (`NaN <= 0` is `False`). Hardening at the pydantic boundary (`Field(ge=0.0)`) would prevent a class of data-corruption bugs at the source rather than the consumer. Not blocking — no pack ships NaN today. See Delivery Finding above. |
| [SEC] | LOW | tz-naive `last_saved_at` would raise `TypeError` at the subtraction | `trope_advance.py:79` | Per user policy `feedback_legacy_saves`, legacy saves are throwaway. Current writers always emit tz-aware. The risk is theoretical for the current playgroup but a defensive `if last_saved.tzinfo is None: return` is cheap insurance. Not blocking. See Delivery Finding above. |
| [TEST] | — | All 6 ACs have AC-tagged test classes; 33 tests; 0 vacuous assertions | `tests/game/test_trope_advance_between_sessions.py` (and wire test) | `_spans_named` returns lists with `.name == name`; every span assertion is on `attrs.get(...)` against a concrete value; no `assert True` or `assert result`. Property-shape (`{1, 2}`) is explicitly justified in test 5's docstring. |
| [EDGE] | — | All boundary cases covered by tests | TestAC1 (8), TestAC2 (5), TestAC3 (3), TestAC4 (2), TestAC5 (5) | Zero rate, dormant, resolved, missing pack def, missing passive_progression, missing trope id, negative elapsed, fractional days, single-beat-crossing, multi-beat-crossing, refire-prevention, clamp-without-overshoot, never-saved → all explicit. |
| [SILENT] | — | Zero silent fallbacks in the engine | `trope_advance.py:75-138` | Every early return has a code-level reason that's surfaced as "no span emitted." The GM panel observably distinguishes "engine ran and nothing moved" from "engine never ran" — the former produces an "engine engaged but no work" turn aggregate via the existing `turn.tropes` aggregate at a turn boundary; the latter would show silence. Acceptable. |
| [RULE] | — | python.md rules #1, #3, #6 satisfied; #2/#4/#5/#7-#13 N/A | per-rule below | See Rule Compliance section. |

### Rule Compliance (manual enumeration vs `.pennyfarthing/gates/lang-review/python.md`)

| Rule | Applicable? | Verdict | Evidence |
|------|-------------|---------|----------|
| #1 Silent exception swallowing | Yes (no try/except in diff) | Compliant | No `try`/`except` introduced in diff. Engine uses early-return guards instead of swallowing. |
| #2 Mutable default arguments | No (no defaults in engine; tests use immutable `tuple` for thresholds) | N/A | `_trope_def(thresholds: tuple[float, ...] = (0.25, ...))` — tuple is immutable. |
| #3 Type annotation gaps | Yes (public boundary) | Compliant | `advance_tropes_between_sessions(*, snapshot: GameSnapshot, pack: Any, now: datetime) -> None`. `Any` documented in docstring. |
| #4 Logging coverage | N/A — no logging in engine; OTEL spans are the project-mandated diagnostic per CLAUDE.md | N/A | Engine emits OTEL via `Span.open`, no `logger.*` calls. |
| #5 Path handling | N/A — no path manipulation in diff | N/A | — |
| #6 Test quality | Yes | Compliant | Self-checked 33 tests for vacuous assertions; none found. Every test asserts on concrete values, typed predicates, or known-set membership. |
| #7 Resource leaks | N/A — no I/O in engine; `Span.open` context manager handles span lifetime | N/A | — |
| #8 Unsafe deserialization | N/A — no pickle/yaml/eval/subprocess in diff | N/A | — |
| #9 Async/await pitfalls | N/A — synchronous engine | N/A | — |
| #10 Import hygiene | Yes (new module + new import in connect.py) | Compliant | No star imports in new code, no circular imports (verified by `uv run pytest` passing; would surface as ImportError otherwise). |
| #11 Security: input validation at boundaries | N/A — engine consumes server-side data (genre pack + snapshot), not user input | N/A | The wire site's inputs (snapshot, genre_pack) are server-controlled. |
| #12 Dependency hygiene | N/A — no dependency changes | N/A | — |
| #13 Fix-introduced regressions | Yes | Compliant | Full server suite re-run by Dev (5196 pass) and TEA verify (5196 pass). No regressions surfaced. |

### Devil's Advocate

The code looks clean. Let me argue it is not.

**"It silently double-applies on server restart."** No — verified above. Server restart re-loads the *unmutated* SQLite snapshot (no save happened between load+restart in a no-save crash); a save IS performed (with updated `last_saved_at`) between the advance and any orderly restart. Either way, the elapsed delta in the next computation is anchored to a stable on-disk timestamp.

**"NaN sneaks in through a malicious pack."** Real but exotic. Pack YAML doesn't ship NaN; pydantic accepts NaN floats but no shipped pack contains them. If a future malicious or accidental NaN lands, `rate <= 0` returns False for NaN → engine proceeds → progress becomes NaN → no beats fire (NaN comparisons all False) → resolved gate fires `False` → trope stays `progressing` with `progress=NaN`. The GM panel sees a NaN span attribute. Probably OTEL-serializer-tolerant (NaN serializes as `NaN` in JSON). User-visible damage: that trope is stuck forever — `progress_after <= progress_before` is True for NaN comparisons after the first NaN write, so subsequent loads no-op. Annoying, recoverable, low-impact. Hardening at the pydantic boundary would close this; flagged as [LOW].

**"A legacy save with tz-naive `last_saved_at` crashes connect."** Real but per user policy these saves are throwaway. Defensive guard would be one line. Flagged as [LOW].

**"The narrator sees beats fired but no narrative trigger."** Correct, by design. AC2 specifies "do NOT call the narrator — the beat was earned passively, not from player action." The opening turn's prompt zone reads `active_tropes` (foreground/background) and surfaces what the player should perceive on return. The narrator's framing job is handled by the existing `_build_turn_context` reading the now-mutated state. Not 50-4's problem; trope_tick.py:render_foreground_block already does the work.

**"Player B's perfectly-correct advance gets discarded by Player A's possibly-buggy advance."** True. If A's clock is wildly skewed, A's mutations could be wrong, and B's correct ones get discarded. But the engine's guards (negative elapsed → skip) make this safe in the symmetric direction (A in the future → A skips, B skips — both correct), and in the asymmetric direction (A's `now` is the future relative to disk timestamp), A's advance applies a huge delta that gets clamped to 1.0. Aggressive but bounded.

**"Multiple connects in the same second by the same player."** SOLO is guarded by `SoloSlotConflict` (line 237) before reaching the advance. MP allows reconnect — but the `bind_world` idempotency kills the second-applied mutation.

**"The advance happens before `room.bind_world`, but bind happens FAR later (line 478 vs my call at line 356)."** True. Between line 356 and line 478, lots of code runs (chargen gate, character resume, etc). Could any of that code modify `snapshot.active_tropes` in ways that conflict with my advance? Scanning the intermediate code: no — it touches `snapshot.player_seats`, `snapshot.characters`, etc., but not `active_tropes`. Safe. (Architectural property worth keeping: between-session trope advance is the FIRST mutation post-load, before any session-bind code can confuse the state.)

**"Tests use `pytest.approx` but compare float equality elsewhere."** Reviewed — every progress comparison uses `pytest.approx`. Beat counts are integers, status is strings, both use `==`. Correct.

Devil's advocate produces 2 low-severity findings worth recording (NaN, tz-naive). Already captured above. No blocker uncovered.

**Handoff:** To SM (Hawkeye) for finish-story.

### Dev (implementation)

- **Content repo touched: no changes required**
  - Spec source: sprint/epic-50.yaml line 114
  - Spec text: `repos: server,content`
  - Implementation: server-only diff. Content packs already declare `rate_per_day` where applicable (4 of 5 live packs: caverns_and_claudes, mutant_wasteland, space_opera, tea_and_murder). `elemental_harmony` has no `passive_progression` blocks at all and the engine handles a missing block as a no-op (matches the existing `tick_tropes` precedent at `sidequest/game/trope_tick.py:183`).
  - Rationale: adding rate_per_day to elemental_harmony tropes would be a content-design decision (which rates, on which tropes) that exceeds the 50-4 scope. The engine already degrades gracefully.
  - Severity: minor
  - Forward impact: a separate playtest-driven story can tune elemental_harmony's rates if the playgroup notices its tropes feel static between sessions.

### TEA (test design)

- **Function signature deviates from story Architecture Context**
  - Spec source: session file `## Architecture Context` → `### Call Site`
  - Spec text: `def advance_tropes_between_sessions(session: GameSession, now_timestamp: float) -> dict[str, dict[str, Any]]`
  - Implementation: tests pin `def advance_tropes_between_sessions(*, snapshot: GameSnapshot, pack: Any, now: datetime) -> None`
  - Rationale: matches the existing engine in the same package (`trope_tick.tick_tropes`) so callers and reviewers can pattern-match across the two functions. Keyword-only args prevent the wire-site from swapping snapshot/pack. `datetime` matches `snapshot.last_saved_at`'s declared type (avoids float ↔ datetime conversion at every callsite). `None` return relies on OTEL spans for diagnostics, matching the project's "spans are the lie detector" principle (CLAUDE.md).
  - Severity: minor
  - Forward impact: Dev must call with keyword args at the connect.py wire site; the wiring test enforces this. If Reviewer prefers the original signature, the unit tests are isolated enough to retarget — the engine logic is the same.

- **Beat semantics: fire-all-crossed (not stagger)**
  - Spec source: session file `## Architecture Context` → `### Rust Reference`
  - Spec text: "for each trope, for each beat in its definition, check if `progress_before < beat.at <= progress_after`, and if so, record the beat and emit OTEL span"
  - Implementation: tests pin "every beat whose threshold falls in `(progress_before, progress_after]` fires this pass" (no per-pass cap; offline catch-up). The in-session engine staggers (one beat per tick); the between-session engine does not.
  - Rationale: matches the Rust port reference and the AC2 phrasing ("If advancement crosses a beat threshold, the beat fires immediately"). The narrator's opening turn handles the framing — multiple passive fires in one pass don't double-narrate.
  - Severity: minor
  - Forward impact: Dev implements a loop over thresholds, not single-pick stagger.

### Reviewer (audit)

- **TEA "Function signature deviates from story Architecture Context"** → ✓ ACCEPTED by Reviewer: keyword-only with `datetime` matches the existing engine in the same package; positional `float` would force callers to convert at every wire site. Architect's spec-check Mismatch 2 reached the same conclusion.
- **TEA "Beat semantics: fire-all-crossed (not stagger)"** → ✓ ACCEPTED by Reviewer: matches both the Rust reference quoted in the session file and the AC2 "fires immediately" wording. The narrator's opening turn frames the catch-up; multi-fire-in-one-pass does not double-narrate because there is no narrator call per beat in this path.
- **Dev "Content repo touched: no changes required"** → ✓ ACCEPTED by Reviewer: spot-checked all 5 live genre packs. 4 of 5 declare `rate_per_day` at varying density (`caverns_and_claudes` x4, `mutant_wasteland` x3, `space_opera` x5, `tea_and_murder` x6). `elemental_harmony` has zero `passive_progression` blocks anywhere — engine's `if tdef.passive_progression is None: continue` guard handles this cleanly. Content tuning is a separate design discussion.
- **Architect spec-check Mismatch 1 "AC3 RESOLVED stricter than literal"** → ✓ ACCEPTED by Reviewer: implementation matches `trope_tick.py:257-276`. For well-formed YAML (all `beat.at` ≤ 1.0), the literal spec and the strict gate are functionally identical. Spec-update preferred over code-change.
- **Architect spec-check Mismatch 2 "AC1/Architecture Context call-site type drift"** → ✓ ACCEPTED by Reviewer: covered by TEA's deviation above; no additional action.
- **No additional undocumented deviations.** I checked the diff against every section of the story context and the AC list. The engine matches what the tests pin and what the deviation log describes.

### Architect (reconcile)

- No additional deviations found.

**Verification of existing entries (re-audit against final diff):**
- TEA "Function signature deviates from story Architecture Context" — accurate. Code at `sidequest/game/trope_advance.py:57-62` matches the deviation entry's described shape (`*, snapshot: GameSnapshot, pack: Any, now: datetime) -> None`).
- TEA "Beat semantics: fire-all-crossed (not stagger)" — accurate. Code at `sidequest/game/trope_advance.py:107-114` loops over the escalation tail without per-pass cap; window is `progress_before < beat.at <= progress_after` exactly as quoted from the Rust reference.
- Dev "Content repo touched: no changes required" — accurate. `git log feat/50-4-trope-rate-per-day-advancement` on `sidequest-content` shows zero commits beyond `develop`. The engine handles missing `passive_progression` in `elemental_harmony` via the precedent at `trope_tick.py:183` (verified by `test_trope_with_no_passive_progression_def_is_skipped`).
- Reviewer audit stamps (all five) — accurate; the spec-check Mismatch 1 (AC3 strict-resolve) and Mismatch 2 (signature drift) are the only architectural divergences and both were ACCEPTED with rationale matching what the code does.

**AC deferral check:** No ACs deferred — all six ACs have explicit test coverage in `tests/game/test_trope_advance_between_sessions.py` and `tests/server/test_50_4_trope_advance_wire.py`. The ac-completion gate's accountability table is not required for this story.

**PRD reference:** Story context cites ADR-018 (Trope Engine) as the load-bearing design. ADR-018 status in the README is "partial" — this story takes a step toward closing that drift. No PRD lives outside the ADR for this subsystem.

## Sm Assessment

- 5pt TDD story, repos: server,content. Story is well-scoped: one entry point (`advance_tropes_between_sessions`), one call site (server session load handler after deserialization, before first turn), one new OTEL span (`SPAN_TROPE_BETWEEN_SESSION_ADVANCE`).
- Rust reference exists at `sidequest-api/src/trope.rs::advance_between_sessions` — per `feedback_ports_are_not_designs`, this is a port, translate verbatim; do not run an alternatives menu.
- Wiring test required (AC6): advancement must run from the production session-load path, not be mocked. Per CLAUDE.md "Verify Wiring, Not Just Existence" + "Every Test Suite Needs a Wiring Test".
- OTEL emission is non-negotiable per the GM-panel "lie detector" principle — span must include `trope_id`, `days_elapsed`, `progress_before/after`, `beats_fired_count`, `new_status`.
- Beat-firing semantics on load: record in `beats_fired`, emit OTEL, do NOT call the narrator (passive advancement, not player-driven).
- Clamp progress to 1.0 and mark RESOLVED on overflow.
- Banned patterns for TEA/Dev (pass forward into subagent prompts): no `git stash` of any kind; never run tests on a prior commit to "prove" a failure was pre-existing. Diagnose on HEAD.
- No Jira (project is personal). No PR-base assumption — both repos target `develop`.
- Routing: phased TDD → TEA owns RED next.

## TEA Assessment

**Tests Required:** Yes
**Reason:** New engine module + new OTEL span + new wire site at connect.py. Pure-data refactor with no behavior — never. This story creates load-bearing behavior, so tests precede code.

**Test Files:**
- `sidequest-server/tests/game/test_trope_advance_between_sessions.py` — 27 unit tests for the engine (signature, AC1–AC5, edge cases).
- `sidequest-server/tests/server/test_50_4_trope_advance_wire.py` — 6 wiring/hygiene tests (connect.py imports + AST call check + span re-export + module docstrings).

**Tests Written:** 33 tests covering 6 ACs.
**Status:** RED — 32 failing, 1 sanity-passing (connect.py file exists). Verified via `uv run pytest tests/game/test_trope_advance_between_sessions.py tests/server/test_50_4_trope_advance_wire.py`.

**Commit:** `55a7083` on `feat/50-4-trope-rate-per-day-advancement` (sidequest-server).

### Rule Coverage

Rules from `.pennyfarthing/gates/lang-review/python.md` applicable to this story:

| Rule | Test(s) | Status |
|------|---------|--------|
| #3 type annotations at boundaries | `TestModuleContract::test_all_parameters_have_type_annotations` | failing |
| #6 test quality — meaningful assertions | self-check pass — no `assert True`, no truthy-only checks, every test asserts on a specific value or membership | enforced in red |
| #10 import hygiene — no circular | wiring test imports `sidequest.game.trope_advance` and `sidequest.handlers.connect`; would surface a cycle | failing (module doesn't exist) |

**Not applicable:** rules #1 (no exception handling in the engine), #2 (no defaults), #4 (no logging in scope — OTEL only), #5 (no path handling), #7 (no resources), #8 (no deserialization), #9 (sync engine), #11 (not a boundary), #12, #13.

**Self-check:** zero vacuous tests; every assertion compares to a concrete value, a typed predicate, or a known-set membership.

### Test Strategy Notes

1. **Unit tests** isolate the engine via a `SimpleNamespace` pack stand-in (matches the `tick_tropes` test fixture pattern in `tests/game/test_trope_tick.py`). Time anchored at `2026-05-13 12:00 UTC` so elapsed-day arithmetic is exact.
2. **OTEL tests** use the same `init_tracer()` + `InMemorySpanExporter` pattern as the existing trope-tick tests; capture per-span attributes via `s.attributes.get(...)`.
3. **Wiring tests** parse `connect.py` with `ast` rather than executing it — the handler has many side-effecting imports (database, websocket, lore store) that would slow tests and pull in fixtures. AST inspection catches both "imported but unused" and "called with positional args" regressions statically.
4. **Hygiene tests** pin docstrings on the new module + public function (project convention; helps the Reviewer locate ADR-018 from grep).

**Handoff:** To Dev (Winchester) for GREEN. Implement `sidequest/game/trope_advance.py` and `SPAN_TROPE_BETWEEN_SESSION_ADVANCE` in `sidequest/telemetry/spans/trope.py`, then wire the call into `sidequest/handlers/connect.py` after `_backfill_magic_state_on_resume` (around line 342) — before the first turn dispatches. Banned patterns forwarded: **no `git stash` of any kind; never run tests on a prior commit to "prove" a failure was pre-existing — diagnose on HEAD.**

## Dev Assessment

**Implementation Complete:** Yes
**Files Changed:**
- `sidequest-server/sidequest/game/trope_advance.py` *(new)* — engine module with `advance_tropes_between_sessions(*, snapshot, pack, now) -> None`. ~80 LoC including docstrings.
- `sidequest-server/sidequest/telemetry/spans/trope.py` — added `SPAN_TROPE_BETWEEN_SESSION_ADVANCE` constant and its `state_transition`/`component="tropes"` route (six attributes per the AC5 contract).
- `sidequest-server/sidequest/handlers/connect.py` — added `datetime`/`UTC` import, `advance_tropes_between_sessions` import, and the call directly after `_backfill_magic_state_on_resume` (which runs once per save-resume in the SOLO/MP branches) — before any turn dispatches.
- `sidequest-server/tests/game/test_trope_advance_between_sessions.py` — TEA's 27 unit tests, reformatted by ruff format.
- `sidequest-server/tests/server/test_50_4_trope_advance_wire.py` — TEA's 6 wiring/hygiene tests, reformatted by ruff format.

**Content repo:** branch created (`feat/50-4-trope-rate-per-day-advancement`) but no commits — see deviation log above. Branch remains local; SM can prune at finish time.

**Tests:** 33/33 50-4 tests pass (GREEN). Full suite: 5196 passed, 64 skipped, 0 failed.
**Lint:** `uv run ruff check` clean on all changed files. `uv run ruff format` clean (test files reformatted as part of this commit).
**Branch:** `feat/50-4-trope-rate-per-day-advancement` (sidequest-server), pushed to origin. Commits: `55a7083` (test), `a8bbe66` (feat).

### Implementation Notes

1. **No-op gates land early.** `last_saved_at is None`, `delta_seconds <= 0`, `status != "progressing"`, missing tdef, `passive_progression is None`, and `rate <= 0` all return without emitting a span. The span only fires when the trope actually moved — keeps the GM panel quiet on uneventful loads.
2. **Beat-firing is `(progress_before, progress_after]` (exclusive lower, inclusive upper).** Matches the AC2 wording ("crosses the beat") and the Rust reference summary in the session file. The inclusive upper bound is required so a trope clamped to 1.0 fires an `at=1.0` beat (covered by `test_progress_at_one_without_all_beats_does_not_resolve`).
3. **Beats fire until one misses, then break.** Escalation thresholds are ordered ascending; the first miss means every later threshold is also above the window. Saves a few comparisons on long escalation lists without changing observable behavior.
4. **`new_status` defaults to empty string, not None.** OTEL span attributes can't be `None` (the SDK drops them); empty string matches the route extractor's default and lets the GM panel filter on `new_status == "resolved"` without nullability handling.
5. **No narrator-side wiring.** AC2 explicitly forbids invoking the narrator from this path; the opening turn handles framing. The engine touches `progress`, `beats_fired`, and `status` only — `narrative_log`, `quest_log`, etc. are untouched (covered by `test_passive_fire_does_not_record_narrative_entry`).

### Self-Review Checklist
- [x] All 6 ACs covered by tests, all green.
- [x] Wiring test (AC6) verifies `connect.py` imports + calls the engine with keyword args. The AST inspection catches both "missed import" and "imported-but-unused" regressions.
- [x] OTEL span registered in `SPAN_ROUTES` so the GM panel's typed feed surfaces it (CLAUDE.md "lie detector" principle).
- [x] No silent fallbacks: clock skew, missing-pack-def, and never-saved snapshots all return early with no mutation and no spans (rather than e.g. defaulting elapsed-days to 0 and emitting a noise span).
- [x] No stubs: the engine is fully functional; deferred-feature comments are absent.
- [x] No backward-compat shims: `TropeState` already round-trips through `extra="ignore"`, so older saves load cleanly without an explicit migration.
- [x] Project patterns: matches `tick_tropes` shape (keyword-only kwargs, duck-typed pack, `Span.open` context manager).

**Handoff:** To TEA (verify phase) for simplify-pass + quality gate.

## Architect Assessment (spec-check)

**Spec Alignment:** Aligned (with two minor drifts, both documented as deviations).
**Mismatches Found:** 2

### Mismatch 1 — AC3 RESOLVED condition stricter than literal spec

- **Category:** Different behavior — Type: Behavioral — Severity: Minor
- **Spec (AC3):** "If advancement would push progress > 1.0, clamp to 1.0 and mark the trope as RESOLVED."
- **Code (`trope_advance.py:118–125`):** Marks `resolved` only when `progress_after >= 1.0` AND `beats_fired >= len(escalation)`. A trope that clamps to 1.0 but still has un-fired beats stays `progressing`.
- **Recommendation:** **A — update spec.** The implementation's gate matches the in-session engine (`trope_tick.py:257–276` comment: "Either condition alone is not enough"). Marking a trope `resolved` while beats remain un-fired would silently truncate its arc — a trope with `escalation=[at=0.50, at=0.75, at=1.00]` and a passive-only path could otherwise reach 1.0 with `beats_fired=0` and resolve before any beat has fired. For well-formed YAML (all beats ≤ 1.0) the two conditions converge — code and spec only diverge on illegal data. Behavior is **better** than the literal spec; capture as a deviation rather than handing back.

### Mismatch 2 — AC1/Architecture Context call-site type drift

- **Category:** Ambiguous spec — Type: Architectural — Severity: Minor
- **Spec (Architecture Context):** `def advance_tropes_between_sessions(session: GameSession, now_timestamp: float) -> dict[str, dict[str, Any]]` — positional, `GameSession`, float timestamp, return-dict.
- **Code:** `def advance_tropes_between_sessions(*, snapshot: GameSnapshot, pack: Any, now: datetime) -> None` — keyword-only, `GameSnapshot`, datetime, mutation-only.
- **Recommendation:** **A — already updated via TEA deviation log** (`### TEA (test design)` → "Function signature deviates..."). The implementation matches the existing `tick_tropes` pattern, uses the type already on `snapshot.last_saved_at` (`datetime | None`), and relies on OTEL spans for diagnostics instead of a return value. TEA's deviation entry covers the change with full 6-field format. No additional action required.

### Verification of Existing Deviations

- TEA's "function signature" deviation — **accurate**, code matches the deviation as written.
- TEA's "fire-all-crossed (not stagger)" deviation — **accurate**, `escalation[trope.beats_fired:]` loop with no per-pass cap.
- Dev's "content repo no changes" deviation — **accurate**, no commits on the content branch.

### Substantive Code Review (architecture-level)

- **Reuse over reinvention.** Engine uses the existing `Span.open` context manager, the existing `SpanRoute` register pattern, and matches the `tick_tropes` duck-typed pack contract. No new infrastructure introduced.
- **No silent fallbacks.** All early-return paths (`last_saved_at is None`, negative elapsed, status≠progressing, missing tdef, missing passive_progression, rate ≤ 0, no progress delta) return without mutation AND without emitting a span. The GM panel sees only events that actually moved.
- **Wiring is real.** AST-validated call site at `connect.py:356`. Import at line 28. Keyword args enforced by signature.
- **OTEL routing is complete.** `SPAN_TROPE_BETWEEN_SESSION_ADVANCE` is registered in `SPAN_ROUTES` (not just `FLAT_ONLY_SPANS`), `component="tropes"`, six attributes match AC5. Routing-completeness test (`tests/telemetry/test_routing_completeness.py`) covers it implicitly via the existing pattern.
- **ADR-018 alignment.** Closes the documented gap ("Python port carried the data model but left the advancement logic unimplemented"); the implementation honors the cap, cooldown, and resolution semantics owned by the in-session engine by deliberately *not* duplicating activation logic (dormant tropes don't auto-promote on load).

### Acceptance Criteria Coverage Matrix

| AC | Spec | Code Location | Test Coverage |
|----|------|---------------|---------------|
| AC1 | Load-time advancement | `trope_advance.py:75–116` | `TestAC1LoadTimeAdvancement` (8 tests) |
| AC2 | Beat firing on load | `trope_advance.py:107–115` | `TestAC2BeatFiringOnLoad` (5 tests) |
| AC3 | Progress clamp + RESOLVED | `trope_advance.py:100, 118–125` | `TestAC3ProgressClamp` (3 tests) |
| AC4 | No advance on first load | `trope_advance.py:75–77` | `TestAC4NoAdvanceOnFirstLoad` (2 tests) |
| AC5 | OTEL emission | `trope.py: const + route`, `trope_advance.py:127–138` | `TestAC5OtelEmission` (5 tests) |
| AC6 | Integration / wiring test | `connect.py:28, 356–360` | `TestEngineWiredIntoConnectHandler` + `TestSpanRoutedThroughWatcher` + `TestEngineModuleHygiene` (6 tests) |

**Decision:** Proceed to TEA verify (simplify + quality-pass). No hand-back to Dev required.

## TEA Assessment (verify phase)

**Phase:** finish
**Status:** GREEN confirmed (33/33 50-4 tests pass; full server suite 5196 passed, 64 skipped)

### Simplify Report

**Teammates:** reuse, quality, efficiency
**Files Analyzed:** 5 (trope_advance.py, connect.py, telemetry/spans/trope.py, both new test files)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 5 findings (4 high, 1 medium) | duplicate `otel_capture` fixture; cross-file duplication of `_trope_def`/`_pack_with`/`_seed_snapshot` against `test_trope_tick.py`; `_spans_named` duplicated across ~9 test files |
| simplify-quality | clean | no findings |
| simplify-efficiency | clean | no findings |

**Applied:** 1 high-confidence fix
- **otel_capture duplicate** — deleted local fixture; `tests/game/conftest.py:182` auto-injects the same fixture (verified by direct file read, including the in-fixture comment about clearing accumulated processors).

**Flagged for Review:** 0

**Deferred (out of 50-4 scope):**
- `_trope_def`/`_pack_with` extraction to conftest — high confidence per the agent but would require also editing `test_trope_tick.py`'s helpers; the two `_seed_snapshot` variants have divergent signatures (mine takes `last_saved_at`; trope_tick's sets `turn_manager.interaction`). Harmonizing those is a legitimate refactor but exceeds 50-4 scope per CLAUDE.md "Don't add features, refactor, or introduce abstractions beyond what the task requires."
- `_spans_named` extraction — agent itself noted this is a 9-file cleanup. Genuinely cross-cutting; warrants its own story.

**Noted:** 0
**Reverted:** 0

**Overall:** simplify: applied 1 fix; 4 deferred to a follow-up cleanup story.

### Regression Check

After applying the simplify fix:
- `uv run pytest tests/game/test_trope_advance_between_sessions.py tests/server/test_50_4_trope_advance_wire.py` → 33/33 pass.
- `just server-check` → ruff clean, pyright clean, 5196 tests pass.
- `just check-all` → server clean; **pre-existing UI typecheck failures** at `sidequest-ui/src/App.tsx:722:11` and `sidequest-ui/src/__tests__/turn-status-wire-shape-wiring.test.tsx:35:9` (both `TS2352: Conversion of type 'GameMessage' to type 'Record<string, unknown>' may be a mistake`). My diff is server-only — verified via `git diff --name-only develop` showing zero UI files. These TS errors pre-date this branch.

### Quality Checks

- **Lint:** `uv run ruff check` clean on all changed files (after auto-fix of `I001` import-order on the test file post-edit).
- **Format:** `uv run ruff format --check` clean.
- **Tests:** server suite full green, 50-4 tests all pass.

### Delivery Findings Capture

(See `### TEA (verify)` under Delivery Findings below.)

**Handoff:** To Reviewer (Colonel Potter) for code review and PR creation.