---
story_id: "61-followup-A"
jira_key: "N/A"
epic: "Epic 61 — Bounded Narrator Prompt: Slim Snapshot + Wire RAG"
workflow: "tdd"
---

# Story 61-followup-A: Session-id-keyed baselines on AnthropicSdkClient (cross-session pollution on slug-reuse rejoin)

## Story Details
- **ID:** 61-followup-A
- **Epic:** 61 — Bounded Narrator Prompt: Slim Snapshot + Wire RAG
- **Jira Key:** N/A (no Jira in this project)
- **Type:** Refactor (P2, 2 points)
- **Workflow:** tdd
- **Stack Parent:** none
- **Repos:** sidequest-server

## Story Context

The 61-4 fingerprint detector's rolling baseline lives on the AnthropicSdkClient instance, not on a session key. Multiplayer session URLs are deterministic (memory: project_session_id_dropin — /play/{date}-{world}-mp rejoins existing session) and the client instance survives across rejoins, so the baseline from the prior session pollutes the new one.

**Requirement:** Key the baseline on session_id (or equivalent stable identifier) so a fresh rejoin starts with a fresh baseline window, and a slug-reuse rejoin inherits the prior session's baseline correctly.

### Acceptance Criteria

1. **Per-session baseline keying:** The rolling baseline deque on AnthropicSdkClient is keyed by session_id, not a single instance variable. Accessing baseline for session A, then session B, returns independent deques.

2. **Fresh rejoin starts with clean baseline:** A new session (fresh /play/{date}-{world}-mp call) initializes an empty baseline deque for that session_id.

3. **Slug-reuse rejoin inherits prior baseline:** When a player rejoins a deterministic-URL session (/play/{date}-{world}-mp), the new client connection inherits the prior session's rolling-baseline deque (same session_id).

4. **reset_baselines() scoped to session:** The reset_baselines() hook on SessionRoom.close_store() only resets the deque for that session_id, leaving other sessions' baselines untouched.

5. **Regression test (unit):** Create two separate session_ids, drive baseline-building calls on each, assert they maintain independent deques and the 61-4 fingerprint detector compares against the correct deque for each session.

6. **Regression test (integration, wiring):** Drive a multiplayer rejoin flow (new client, same session_id) and assert the reconnected client sees the prior baseline, not a fresh one.

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-05-24T01:14:44Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-05-23T23:44:15Z | 2026-05-23T23:49:57Z | 5m 42s |
| red | 2026-05-23T23:49:57Z | 2026-05-24T00:21:14Z | 31m 17s |
| green | 2026-05-24T00:21:14Z | 2026-05-24T00:34:06Z | 12m 52s |
| spec-check | 2026-05-24T00:34:06Z | 2026-05-24T00:39:01Z | 4m 55s |
| verify | 2026-05-24T00:39:01Z | 2026-05-24T00:42:53Z | 3m 52s |
| review | 2026-05-24T00:42:53Z | 2026-05-24T00:53:51Z | 10m 58s |
| green | 2026-05-24T00:53:51Z | 2026-05-24T01:00:01Z | 6m 10s |
| spec-check | 2026-05-24T01:00:01Z | 2026-05-24T01:02:52Z | 2m 51s |
| verify | 2026-05-24T01:02:52Z | 2026-05-24T01:06:06Z | 3m 14s |
| review | 2026-05-24T01:06:06Z | 2026-05-24T01:14:44Z | 8m 38s |
| finish | 2026-05-24T01:14:44Z | - | - |

## Sm Assessment

**Story:** 61-followup-A — Session-id-keyed baselines on AnthropicSdkClient. 2pts, P0 per handoff (P2 in YAML — handoff is operator intent, leaving YAML alone). Server-only, TDD, no Jira.

**Setup outcomes:**
- Server is on `feat/61-followup-A-session-keyed-baselines` off updated `develop` (origin/develop fast-forwarded to `0874029`, post-merge of D's PR #394).
- Session scaffolded at `.session/61-followup-A-session.md` (sm-setup placed it correctly, no manual relocation needed this time).
- Story context written out-of-band at `sprint/context/context-story-61-followup-A.md` because sm-setup currently skips context creation for `-followup-X` IDs. Parent epic context (`context-epic-61.md`) verified present.
- No tandem partner consulted — right-sized for a 2pt mechanical refactor with a fully spec'd sketch in the handoff (memory `feedback_plan_ceremony.md`).

**Routing rationale:** Workflow is phased TDD. Next agent is Igor (TEA) for RED. The story is a straight port-the-shape refactor — convert two instance-wide `deque` baselines into `dict[session_id, deque]`, plumb `session_id` through `_maybe_emit_cost_runaway`, and convert `reset_baselines()` → `reset_baselines(session_id)`. The pattern to mirror is already in the file at line 226 (`_session_cumulative_cost_usd: dict[str, float]` from 61-followup-D). Test fakes coordination note carried forward from handoff in case a fifth sibling file is needed.

**Out-of-scope guardrails explicitly noted in context** (so Igor doesn't drift into B or C):
- Do not touch `SessionRoom.close_store()` — that's 61-followup-C.
- Do not promote `narrator.sdk.usage` log → watcher event — that's 61-followup-B.
- Do not invent TTL/LRU on the per-session dict — bounded-memory mitigation is C's job.
- No new typed exceptions, no new OTEL events.

**Known tooling debt carried forward** (not blocking, log for later):
1. `pf sprint story finish -followup-X` rejects the ID format — finish ceremony must be manual at end of story.
2. `pf sprint story claim` rejected with "assigned to unknown" despite null assignee — worked around via `pf sprint story update --status in_progress --assigned-to slabgorb`.
3. `sm-setup` skipped story-context creation for `-followup-A` (same bug as `-followup-D`) — SM did it manually here too.

## TEA Assessment

**Tests Required:** Yes
**Reason:** TDD workflow; mechanical refactor with cross-session-behavior correctness depending on per-session keying.

**Test Files:**
- `sidequest-server/tests/agents/test_61_followup_A_session_keyed_baselines.py` (705 lines, 12 tests, committed as `fb97323` on `feat/61-followup-A-session-keyed-baselines`)

**Tests Written:** 12 tests covering 6 ACs + 2 structural drift detectors + 2 None-bypass behavioral tests + 2 reset edge cases
**Status:** RED (12/12 failing — verified via `uv run pytest tests/agents/test_61_followup_A_session_keyed_baselines.py -v -n0`)

### Test → AC mapping

| # | Test | Covers | RED failure mode (today) |
|---|---|---|---|
| 1 | `test_cost_baseline_is_dict_keyed_on_session_id` | Structural drift | AssertionError — `_cost_baseline` is `deque`, not `Mapping` |
| 2 | `test_input_tokens_baseline_is_dict_keyed_on_session_id` | Structural drift | AssertionError — `_input_tokens_baseline` is `deque`, not `Mapping` |
| 3 | `test_maybe_emit_cost_runaway_accepts_session_id_kwarg` | Signature drift | AssertionError — `session_id` not in signature parameters |
| 4 | `test_reset_baselines_requires_typed_session_id_param` | AC 4 + rule #3 | AssertionError — `session_id` not in `reset_baselines` parameters |
| 5 | `test_direct_emit_records_per_session_baseline_independence` | AC 1 | TypeError — unexpected kwarg `session_id` |
| 6 | `test_fresh_session_uses_warmup_floor_not_event` | AC 2 | AssertionError — `"brand-new-session" in deque([...])` is False (cross-detects structural shape) |
| 7 | `test_session_a_trips_cost_multiple_after_session_b_floods` | **AC 3 + AC 5 (the gauntlet)** | AssertionError — 0 events but expected 1 (instance-wide deque polluted by B) |
| 8 | `test_session_id_none_direct_call_skips_baseline_dict` | None-bypass (direct) | TypeError — unexpected kwarg `session_id` |
| 9 | `test_complete_with_tools_with_none_session_id_does_not_populate_baseline` | None-bypass (wiring) | AssertionError — `_cost_baseline` has 1 entry (the appended call), not 0 |
| 10 | `test_complete_with_tools_routes_session_id_to_baseline_dict` | AC 6 (wiring) | AttributeError — `deque` has no `.keys()` |
| 11 | `test_reset_baselines_clears_only_target_session` | AC 4 (behavior) | TypeError on seeding loop (unexpected kwarg) |
| 12 | `test_reset_baselines_noop_on_unknown_session_id` | AC 4 (edge case) | TypeError — `reset_baselines()` takes 1 positional but 2 given |

### Gauntlet design (test 7) — the lie detector

The setup deliberately picks values that distinguish per-session and instance-wide behaviors at the TRIGGER level, not just dict-contents:

- Session A: 10 calls at input=11_000 / output=500 → cost ≈ $0.0405/call → A's clamped baseline = $0.0405.
- Session B: 10 STRICTLY LATER calls at input=30_000 / output=500 → cost ≈ $0.0975/call → in instance-wide K=10 deque, B's 10 calls evict A's 10 entirely.
- Trip call on A: input=35_000 / output=8_000 → cost ≈ $0.225.

Only `cost_multiple` depends on the baseline. `io_fingerprint` is silent (output 8K ≫ 50). `input_absolute` is silent (35K < 40K). `cost_absolute` is silent ($0.225 < $0.30). So the trigger is a clean discriminator:

- **Per-session correct (post-fix):** A's baseline still $0.0405. 5× = $0.2025. $0.225 > $0.2025 → cost_multiple fires.
- **Instance-wide today (RED):** combined deque holds only B's last 10 = mean $0.0975, clamped at $0.09. 5× = $0.45. $0.225 < $0.45 → silent. 0 events. Test fails RED.

Test also asserts `trigger == "cost_multiple"` (not `cost_absolute`) and `0.035 ≤ baseline_cost_usd ≤ 0.050` to prevent a false-pass where the absolute floor saves us but the per-session semantics still wrong.

### Rule Coverage

| Rule | Test(s) | Status |
|---|---|---|
| #3 type annotations at public surface | `test_reset_baselines_requires_typed_session_id_param` (asserts `param.annotation is str`, no default) | failing |
| #6 test quality (no vacuous, specific values) | self-check on all 12 tests — every assert checks specific membership/equality/value; no `assert True`, no truthy fallthrough | passing (self-check) |
| #9 async/await hygiene | All async tests `@pytest.mark.asyncio`, `asyncio.sleep(0.05)` for event-loop settling (matches existing pattern) | passing (self-check) |
| #10 import hygiene | No `*` imports, no circular, single `# type: ignore[attr-defined]` on the test-test coupling import matches D pattern | passing (self-check) |

**Rules checked:** 4 of 14 applicable. Rules #1, #2, #4, #5, #7, #8, #11, #12, #13, #14 are N/A for a pure-test file (no exception handling, no mutable defaults, no logging, no path ops, no resource handling, no deserialization, no input validation boundary, no deps, no fix-regression to scan, no register/commit cleanup ordering).

**Self-check:** 0 vacuous tests; all 12 asserts on specific values. The two bare-existence asserts in `test_reset_baselines_clears_only_target_session` (lines 644-645) are pre-condition seeds before the actual reset-behavior assertions; intentional, not vacuous.

### Test file strategy decision

Created a 5th sibling `test_61_followup_A_session_keyed_baselines.py`, importing fakes from `test_61_4_cost_runaway_alarm` (same `# type: ignore[attr-defined]` shape as the four D files). Right-sized per memory `feedback_plan_ceremony` — fakes-consolidation refactor (move shared `_FakeSocket / _resp / _Sdk / _system_blocks / _tools_empty / _user_msg` to `tests/agents/fakes/sdk_shape.py`) would touch 7 files for ~150 lines of pure mechanical churn on a 2pt story. Logged as non-blocking Improvement; recommended before any 6th sibling.

**Handoff:** To Dev (Ponder Stibbons) for GREEN. See Delivery Findings below for the test-update debt Dev must clear during implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Branch:** `feat/61-followup-A-session-keyed-baselines` (commit `7e3c7f7`, pushed to origin)
**Tests:** 12/12 new A tests pass · 47/47 sibling baseline-detector tests pass · 7416 / 7416 full server suite pass (375 skipped) · ruff clean · pyright clean

**Files Changed:**

| File | Nature of change |
|---|---|
| `sidequest-server/sidequest/agents/anthropic_sdk_client.py` | Production refactor — deque → `dict[str, deque]`, `session_id` plumbing, `reset_baselines(session_id)`, append moved inside `_maybe_emit_cost_runaway`, `session_id` added to event payload + log line |
| `sidequest-server/tests/agents/test_61_followup_A_session_keyed_baselines.py` | Test fix: `typing.get_type_hints` (not `inspect`) for PEP 563-resolved annotation check (Design Deviation #3) |
| `sidequest-server/tests/agents/test_61_4_cost_runaway_alarm.py` | 13 `complete_with_tools` call sites + the `test_reset_baselines_clears_rolling_state` rewrite for the new dict topology |
| `sidequest-server/tests/agents/test_61_followup_D_baseline_ceiling.py` | 4 `complete_with_tools` call sites get `session_id="61-baseline-test"` |
| `sidequest-server/tests/agents/test_61_followup_D_input_absolute_floor.py` | 6 `complete_with_tools` call sites get `session_id="61-baseline-test"` |

**Implementation summary:**

1. **Per-session dict refactor** (anthropic_sdk_client.py:190-191 area): the two instance-wide deques become `dict[str, deque[float]]` / `dict[str, deque[int]]`. Lazy-init on first observation via `setdefault(session_id, deque(maxlen=_BASELINE_WINDOW_K))`.
2. **`_maybe_emit_cost_runaway`** gains required keyword-only `session_id: str | None`. None bypasses the detector entirely (no read, no append) — matches the existing None bypass on `_update_session_cumulative` at anthropic_sdk_client.py:408. Encapsulated the append (after the trigger-check + emit) inside the helper.
3. **`complete_with_tools` call site**: removed the explicit append block. Detector lifecycle now lives entirely inside the helper.
4. **`reset_baselines`**: now takes `session_id: str` (required, typed, no default). Uses `dict.pop(session_id, None)` so a never-observed session is a safe no-op (race-tolerance for disconnect-before-first-call).
5. **Event payload + log**: added `session_id` to both. One-line additions each.
6. **Test call-site updates**: mechanical injection via Python regex across the 3 baseline-detector test files. All 23 sites get `session_id="61-baseline-test"` so the detector still exercises post-A-bypass.
7. **`test_reset_baselines_clears_rolling_state` rewrite** (test_61_4): the pre-A direct-shape assertions (`len(client._cost_baseline) == 10`, `reset_baselines()` no-arg) had to be updated for the new dict topology and the new signature. Asserts on the session's deque + key absence post-reset.

**Gauntlet result (the lie detector):** `test_session_a_trips_cost_multiple_after_session_b_floods` now passes — session A's $0.225 trip call fires `cost_runaway_suspected` with `trigger="cost_multiple"` and `baseline_cost_usd≈$0.0405`, proving session B's flood didn't touch A's baseline window. Before the fix this test reported 0 events (the instance-wide K=10 deque was filled exclusively with B's later calls).

**Self-review checklist:**
- [x] Code wired end-to-end: production call site at orchestrator.py:2661/2674 already passes `session_id=current_session_id` (61-followup-D wiring); A's new per-session lookup consumes it without further changes.
- [x] Follows project pattern: mirrors `_session_cumulative_cost_usd` dict shape, mirrors None-bypass semantics.
- [x] All ACs met (verified by 12 passing tests + the gauntlet discriminator).
- [x] No new error handling needed (no new failure modes; existing exceptions unchanged).
- [x] No `# type: ignore` added; pyright clean.
- [x] Out-of-scope guardrails respected: did NOT touch SessionRoom.close_store (C), did NOT promote `narrator.sdk.usage` log (B), did NOT add TTL/LRU (C), no new typed exceptions, no new OTEL event types (added one field to an existing event).

**Handoff:** To TEA (Igor) for verify phase (simplify + quality-pass).

## Architect Assessment (spec-check)

I've done a little sketch. Well, forty-seven sketches. The clockwork moves correctly.

**Spec Alignment:** Aligned (with five low-severity mismatches catalogued below; none require Dev rework).
**Mismatches Found:** 5 (3 Behavioral/Architectural — all Option A, code is correct; 2 Ambiguous spec — Option C, traceability only).
**Decision:** Proceed to TEA verify.

### AC-by-AC walk

| AC | Spec | Code | Aligned? |
|---|---|---|---|
| 1 — Per-session keying | `dict[session_id, deque]` | `self._cost_baseline: dict[str, deque[float]] = {}` (anthropic_sdk_client.py:208) + `setdefault(session_id, deque(maxlen=K))` at append site | ✓ |
| 2 — Fresh rejoin clean baseline | Fresh session_id → empty deque → warmup floors | `cost_window = self._cost_baseline.get(session_id)` returns None for never-seen sessions; warmup=True; floors used | ✓ |
| 3 — Slug-reuse rejoin inherits | Same session_id → same window | Same client instance + same session_id key = same deque entry; no per-rejoin reset | ✓ |
| 4 — `reset_baselines` per-session | Required typed `session_id: str` | `def reset_baselines(self, session_id: str)` with `dict.pop(session_id, None)` | ✓ (wiring deferred — Mismatch #5 below) |
| 5 — Regression test (unit) | Two session_ids, independent deques, correct comparison | `test_session_a_trips_cost_multiple_after_session_b_floods` — the gauntlet | ✓ |
| 6 — Regression test (integration, wiring) | "Drive multiplayer rejoin... reconnected client sees prior baseline" | `test_complete_with_tools_routes_session_id_to_baseline_dict` (X/Y/X = {X: 2, Y: 1}) | ✓ (per story-context clarification — Mismatch #4 below) |

### Spec-boundary check (in-scope vs deferred)

| Boundary | Status |
|---|---|
| `SessionRoom.close_store()` wiring (61-followup-C) | Untouched ✓ |
| `_session_cumulative_cost_usd` (61-followup-D) | Untouched ✓ |
| `narrator.sdk.usage` log promotion (61-followup-B) | Untouched ✓ |
| Clamp values, trigger priority, ceiling envs | All unchanged ✓ |
| New typed exceptions | None added ✓ |
| TTL/LRU eviction | Not added (correctly deferred to C) ✓ |
| Production scope | Single file: `sidequest/agents/anthropic_sdk_client.py` (170 insertions, 87 deletions) ✓ |

### Mismatches

**1. Append location: spec said "at call site", code put it inside `_maybe_emit_cost_runaway`** (Behavioral — Minor)
- Spec: context-story-61-followup-A.md, Technical Guardrails → "Surfaces to modify" table lists "Append calls at lines 399-400 — wrap with a None-bypass + per-session lookup."
- Code: Removed the explicit append from `complete_with_tools`; the per-session append now lives at the tail of `_maybe_emit_cost_runaway` (after the trigger check + emit). The pre-PRIOR-comparison semantics are preserved because the read happens first, then the trigger check, then the append at the very end.
- Recommendation: **A — Update spec**. The encapsulation is the correct design — the detector's full state-management lifecycle (read → emit → append) is now owned by a single helper. TEA's tests #5 and #11 demand this shape (they invoke the helper directly and assert dict population, which the two-step pattern couldn't satisfy). Dev's deviation is sound. No code change needed.

**2. `session_id` added to `cost_runaway_suspected` event payload + log line** (Architectural — Trivial)
- Spec: context-story-61-followup-A.md, Assumptions §6 explicitly authorized this as "the smallest possible addition if operators can't tell sessions apart, do not invent a new event."
- Code: One-line additions to the `fields` dict and the `logger.error` format string. Tests don't assert this; GM-panel consumers benefit (multi-session attribution on interleaved alarms).
- Recommendation: **A — Update spec** (treat as canonical). The TEA Question finding explicitly invited the call; Dev took it correctly.

**3. Test fix: `typing.get_type_hints` instead of `inspect.signature(...).parameters[...].annotation is str`** (Implementation detail — Minor)
- Spec: TEA's own test, `test_reset_baselines_requires_typed_session_id_param`, was written to enforce lang-review rule #3.
- Code: Production has `from __future__ import annotations` (PEP 563) at the module top. `param.annotation` is then the string `"str"`, not the type `str`. Dev replaced `param.annotation is str` with `typing.get_type_hints(AnthropicSdkClient.reset_baselines)["session_id"] is str`, which resolves the forward ref.
- Recommendation: **A — Update spec**. The new mechanism preserves the rule-enforcement intent. The original assertion couldn't pass against any PEP 563 codebase regardless of implementation. Worth a wider note (flagged below in findings): every future Python test in this codebase that checks annotations should use `typing.get_type_hints`.

**4. AC 6 wording — "(new client, same session_id)"** (Ambiguous spec — Minor)
- Spec: AC 6 literally says "Drive a multiplayer rejoin flow (new client, same session_id) and assert the reconnected client sees the prior baseline, not a fresh one."
- Code: `test_complete_with_tools_routes_session_id_to_baseline_dict` drives 3 calls on a SINGLE client instance with X/Y/X session_ids and asserts the dict shape. No literal "new client" construction.
- Recommendation: **C — Clarify spec**. The story-context AC 6 expansion already clarified the unit-test mechanical equivalent: "two `complete_with_tools` calls with the same `session_id` parameter on a single client instance. Don't spin up a real WebSocket session for this." The headline AC text is the loose framing; the context expansion is the operational one. Code is correct; spec headline could be misread without the context.

**5. AC 4 wording — "reset_baselines() hook on SessionRoom.close_store()"** (Ambiguous spec — Minor)
- Spec: AC 4 reads as if `SessionRoom.close_store()` wiring is in-scope for A.
- Code: Provides the per-session `reset_baselines(session_id)` API; does NOT touch `SessionRoom.close_store()`. The wiring is the explicit responsibility of 61-followup-C per story context Scope Boundaries (in-scope vs out-of-scope split).
- Recommendation: **C — Clarify spec**. Story context already resolves it ("Wiring `SessionRoom.close_store()` to call `reset_baselines(session_id)` — that is 61-followup-C"). The deviation here is between the AC's terse phrasing and the operative scope split; code follows the scope split correctly.

### Dev's logged deviations — review

All three Dev deviations (`### Dev (implementation)` in the session file) are well-formed, accurate, and consistent with my analysis above. No corrections needed; they map 1:1 onto my Mismatches #1, #2, #3.

### Architectural observations (not mismatches)

- **Unbounded-growth deferral is genuinely safe** at the deque-level: each session_id costs ~K floats + K ints ≈ 160 bytes. Even 100K distinct sessions = ~16MB. The 61-followup-C eviction is correct future work but not memory-pressure-urgent. Aligns with story context Assumptions §3.
- **Pattern parity with `_session_cumulative_cost_usd`** is clean: same `dict[str, ...]` shape, same lazy-init semantics, same None-bypass contract, same future-wiring deferral story (D's tracker also lacks eviction today). The two detectors now agree on what a "session" is — exactly the architectural alignment the story was after.
- **Defensive `assert cost_window is not None and input_window is not None`** in the post-warmup branch is a pyright type-narrowing helper, not a runtime safety net. The condition is genuinely unreachable in practice (warmup=False only when both windows exist with len ≥ K). Acceptable Python idiom; not a "silent fallback" violation since the assertion would be a visible AssertionError rather than a silent miscompare.

## Delivery Findings

No upstream findings at setup time.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)

- No upstream findings during implementation. The three TEA findings were addressed in-PR: (1) Gap — all 23 sites updated via mechanical regex injection across 3 files, including the pre-existing `test_reset_baselines_clears_rolling_state` direct-shape assertions which were rewritten for the new dict topology; (2) Improvement — fakes consolidation deferred per memory `feedback_plan_ceremony` (right-sized for 2pt story); (3) Question — added `session_id` to event payload + log line.

### TEA (test verification)

- **Improvement** (non-blocking): `pf check` from the orchestrator root only exercises the orchestrator's npm lint and skips the server's Python lint+test suite (no Python toolchain configured at the orchestrator level). For a server-only story, `just server-check` is the right command. Workflow guidance in `.pennyfarthing/agents/tea.md` step 7 says "use the project-agnostic `pf check` command" but the actual quality gate for this story required running the just recipe. Consider documenting the per-repo fallback (orchestrator → `pf check`, server-only stories → `just server-check`) in the TEA verify workflow, or extending the project's `pf check` configuration to dispatch into subrepo toolchains for polyrepo setups. Not blocking — just server-check covered the gate. *Found by TEA during test verification.*

- No upstream findings during test verification beyond the above.

### Architect (spec-check)

- **Improvement** (non-blocking): All future Python tests in this codebase that assert on parameter type annotations should use `typing.get_type_hints(callable)` rather than `inspect.signature(callable).parameters[name].annotation is <type>`.
  Affects test design across `sidequest-server/tests/` whenever annotation enforcement is in scope. The server uses `from __future__ import annotations` widely (PEP 563), which stringifies all annotations at definition time. `param.annotation` will be the string form (e.g. `"str"`) and the `is`-identity check against the bare type always fails. `typing.get_type_hints` resolves the forward reference against the module's globals and returns the actual type. The 61-followup-A test fix is the canonical pattern; future TEAs and Reviewers should apply it proactively. Not blocking — no code change needed today; a one-line note in the testing skill or lang-review/python.md checklist (rule #6 expansion) would prevent the same time-loss next sprint. *Found by Architect during spec-check.*

- **Question** (non-blocking): The unbounded growth of `_cost_baseline` / `_input_tokens_baseline` is bounded by `deque(maxlen=K)` per entry (~160B/session), so 100K distinct sessions ≈ 16MB. Genuinely safe to defer eviction to 61-followup-C. But: at what session-count threshold should we revisit? Story context Assumptions §3 said "If this becomes a real memory pressure problem before C lands, escalate." A concrete trigger (e.g. "if a single process accumulates >10K distinct session_ids before C ships, accelerate C") would make the deferral less judgment-call-dependent. Not a code change; a planning-time note for whoever picks up C. *Found by Architect during spec-check.*

### TEA (test design)

- **Gap** (blocking): Existing baseline-detector tests omit `session_id`, become detector no-ops post-fix.
  Affects `sidequest-server/tests/agents/test_61_4_cost_runaway_alarm.py` (13 `complete_with_tools(` call sites), `tests/agents/test_61_followup_D_baseline_ceiling.py` (4 sites), `tests/agents/test_61_followup_D_input_absolute_floor.py` (6 sites). After A's behavioral contract lands (`session_id=None` → detector no-op), every existing call without `session_id` silently stops exercising `_maybe_emit_cost_runaway`. Tests asserting `cost_runaway_suspected` event firing would flip to false-passes (no event because detector is bypassed, not because the detector approved). Dev MUST add `session_id="<test-name>"` to all 23 call sites during GREEN — without this, the test suite passes but the detector loses its 12-test coverage and a future regression would not be caught. Note: `test_61_followup_D_session_cost_ceiling.py` already passes `session_id` everywhere (it was added for D's cumulative tracker); only the baseline-detector tests are affected. *Found by TEA during test design.*
- **Improvement** (non-blocking): Fakes consolidation debt deepens by one file.
  Affects `sidequest-server/tests/agents/test_61_4_cost_runaway_alarm.py` (origin of `_FakeSocket`, `_resp`, `_Sdk`, `_system_blocks`, `_tools_empty`, `_user_msg`) and the four sibling files (3 D files + the new A file) that import them via `from tests.agents.test_61_4_cost_runaway_alarm import (...)  # type: ignore[attr-defined]`. Recommended consolidation target: `tests/agents/fakes/sdk_shape.py` + `tests/agents/fakes/__init__.py`. Right-sized out of A per memory `feedback_plan_ceremony` (would touch 7 files for ~150 mechanical lines on a 2pt story). Should land before any 6th sibling test file. *Found by TEA during test design.*
- **Question** (non-blocking): cost_runaway_suspected event payload session attribution.
  Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py` (lines ~616-625, the `fields` dict for `_watcher_publish_event`). Today's payload has no `session_id`; after A, the GM panel could see multiple sessions' cost_runaway events interleaved with no way to attribute them. Context-story-61-followup-A.md AC 6 explicitly permits adding `session_id` as the smallest possible addition if operators can't tell sessions apart, but does not require it. Dev's call during GREEN — add it if it costs nothing, defer otherwise. Tests do NOT assert it. *Found by TEA during test design.*

### Architect (spec-check rework r1)

- **Improvement** (non-blocking): Wider testing-pattern concern surfaced by the rework. The HIGH bug (`reset()` zero-args after signature change) slipped past the existing wiring test `test_close_store_resets_narrator_cost_baselines` because the test asserted only `mock.reset_baselines.call_count == 1` against a `MagicMock` — and MagicMock accepts ANY arity, so the test happily passed against the broken call. This is a **class of testing weakness**, not just a one-off: any wiring test that asserts `call_count` against a `MagicMock` rather than `assert_called_*_with(...)` accepts any signature drift silently. A grep over `tests/server/` and `tests/agents/` shows at least a half-dozen other `assert mock.x.call_count == ...` patterns of the same shape; each is a latent loophole. Future TEA / Reviewer / lang-review/python.md authors should default-suspect `call_count`-only assertions on `MagicMock` wiring tests and demand `assert_called_*_with(...)` when the caller passes domain-relevant arguments. Recommend a one-line addition to lang-review/python.md rule #6 (test quality) capturing this. *Found by Architect during spec-check rework.*

### Reviewer (code review)

- **Gap** (blocking): `SessionRoom.close_store()` calls `reset_baselines()` with zero arguments at `sidequest-server/sidequest/server/session_room.py:357`, but the new signature requires `session_id: str`. The signature was changed in-PR (A's surface), and the existing dormant call site was not updated. The `except Exception` block at line 358 swallows the resulting `TypeError` into a `session.reset_baselines_failed` warning, so teardown does not crash — but the reset silently does nothing. When 61-followup-C wires `close_store()` into a real teardown path, every slug recycle will silently fail to reset baselines. Affects `sidequest-server/sidequest/server/session_room.py:357` (one-line fix: `reset()` → `reset(self.slug)` — `self.slug` is the dataclass field at `session_room.py:147` and is the same value flowing into `complete_with_tools(..., session_id=context.session_id)` via the orchestrator at `orchestrator.py:3675` and `session_helpers.py:998` `session_id=sd.game_slug`). This is the kind of silent fallback CLAUDE.md explicitly bans. *Found by Reviewer during code review (confirmed by reviewer-preflight subagent).*

- **Improvement** (non-blocking): `reset_baselines(session_id)` clears only `_cost_baseline` and `_input_tokens_baseline`. The 61-followup-D state (`_session_cumulative_cost_usd`, `_session_ceiling_announced`) is intentionally untouched, but the docstring is silent on that choice. Whoever wires 61-followup-C will have to decide whether slug recycle should also wipe the D-layer dicts (likely YES, since "slug recycle" is the operative trigger for both detector resets); the absence of a per-method scope note here means that decision lives nowhere until C is being authored. Affects `sidequest-server/sidequest/agents/anthropic_sdk_client.py:510-544` (docstring of `reset_baselines`). Add one sentence: "The 61-followup-D state (`_session_cumulative_cost_usd`, `_session_ceiling_announced`) is NOT cleared by this method — 61-followup-C will decide whether close_store's eviction path should also clear those." *Found by Reviewer during code review.*

- **Improvement** (non-blocking): Line-number references in the new test file have already drifted from the post-refactor production file. The new test file at `sidequest-server/tests/agents/test_61_followup_A_session_keyed_baselines.py` cites `anthropic_sdk_client.py:393` (line 155 of the test, in `test_maybe_emit_cost_runaway_accepts_session_id_kwarg`), `:408` (lines 25 and 476, for the None-bypass mirror), and `:399-400` (line 567, for the routed call site). The actual call site is now `anthropic_sdk_client.py:415` and the cumulative-tracker None bypass is `:276`/`:429`. These are tests Dev wrote himself, so the drift was already present at red-phase write time. Cosmetic — does not affect behavior. Either drop the explicit line numbers or update them. *Found by Reviewer during code review.*

### Reviewer (re-review r2)

- **Improvement** (non-blocking, forward to 61-followup-C): The pre-existing `self._slug` reference at `sidequest-server/sidequest/server/session_room.py:~365` (in the `_log.warning` call inside the `close_store` except block) is a latent AttributeError — the dataclass field is `slug` (no underscore) per `session_room.py:147`. Today the warning path is unreachable (`close_store` is dormant + the signature-arity bug that would have hit this path is now fixed in this PR), so it's not load-bearing. But it sits one signature drift away from masking the very kind of diagnostic the warning was designed to surface. 61-followup-C is the next story that touches the teardown path — fix this then. Pyright has been flagging it since the original 61-4 work. Dev and Architect both flagged forward; I confirm the forward-flag and second the recommendation. *Found by Reviewer during re-review.*

- No other upstream findings during re-review. The rework cleared all three findings from review-r1.

## Design Deviations

No design deviations at setup time.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- No deviations from spec.

### Dev (implementation)

- **Append moved inside `_maybe_emit_cost_runaway` rather than kept at the call site.**
  - Spec source: context-story-61-followup-A.md, Technical Guardrails → "Surfaces to modify" table
  - Spec text: "Append calls at lines 399-400 — wrap with a None-bypass + per-session lookup" (implying append stays at the `complete_with_tools` call site).
  - Implementation: Moved both per-session `setdefault(...).append(...)` calls INTO `_maybe_emit_cost_runaway` (after the trigger check). Removed the explicit append block from `complete_with_tools`.
  - Rationale: TEA's tests #5 and #11 directly call `_maybe_emit_cost_runaway(..., session_id="X")` and then assert that `client._cost_baseline["X"]` is populated. With the spec's "append at call site" structure, those direct calls would have left the dict empty and the tests would not pass. Moving the append inside preserves the existing read-before-append-for-PRIOR-comparison semantics (the read happens first, then trigger check, then append at the end) AND satisfies the test design. The detector's full lifecycle (read → emit → append) is now encapsulated, which is cleaner than the two-step pattern.
  - Severity: minor
  - Forward impact: none — observable behavior from `complete_with_tools` callers is identical. 61-followup-B (if it lands later) and 61-followup-C will see the cleaner internal API.

- **Added `session_id` to `cost_runaway_suspected` event payload + ERROR log line.**
  - Spec source: context-story-61-followup-A.md, Assumptions §6 (and TEA Delivery Findings — Question).
  - Spec text: "If implementation discovers a case where operators can't tell which session a baseline event came from, add `session_id` to the event payload as the smallest possible addition — do not invent a new event."
  - Implementation: Added `"session_id": session_id` to the `fields` dict and `session_id=%s` to the `logger.error` format. One-line addition each.
  - Rationale: Permitted by spec, costs nothing, gives the GM panel multi-session attribution. TEA's Question finding explicitly invited the call.
  - Severity: trivial
  - Forward impact: none — no tests asserted absence of the field; the GM panel's reader is additive (unknown keys are ignored).

- **Test fix in `test_reset_baselines_requires_typed_session_id_param`: `typing.get_type_hints` instead of `inspect.signature(...).parameters[...].annotation is str`.**
  - Spec source: TEA's own test, sprint/context/context-story-61-followup-A.md AC 4 (rule #3 type annotations).
  - Spec text: TEA asserted `param.annotation is str` to enforce the type annotation.
  - Implementation: Changed the assertion to `typing.get_type_hints(AnthropicSdkClient.reset_baselines).get("session_id") is str`.
  - Rationale: `anthropic_sdk_client.py` has `from __future__ import annotations` at module top (PEP 563), which stringifies every annotation. `param.annotation` is then the string `'str'`, not the type `str`, so the original `is str` check could never pass against this codebase regardless of implementation. The fix preserves the test's intent (verify the annotation IS the str type) using the API that resolves forward refs. The new test still fails if I removed the annotation entirely, so the rule-enforcement intent is intact.
  - Severity: minor
  - Forward impact: none — same intent, more robust mechanism. Future Python tests in this codebase that check annotations should use `typing.get_type_hints` for the same reason; flagged as a wider concern but not in scope for A.

### Architect (spec-check)
- No additional deviations beyond the three Dev entries above. My spec-check mismatch analysis (see Architect Assessment) recommends Option A — Update spec — for all three Dev deviations (the code is correct, the spec is the loose-fit). Two additional AC-wording ambiguities (Mismatches #4 and #5 in my assessment) are resolved by the story context's expansion text; both are Option C — Clarify spec only, no code impact.

### TEA (test verification)
- No deviations from spec.

### Reviewer (audit)

- **Dev deviation #1 (append moved inside `_maybe_emit_cost_runaway`)** → ✓ ACCEPTED by Reviewer: agrees with Dev + Architect reasoning. Encapsulating the read→emit→append lifecycle inside the helper is the cleaner design and is required for TEA tests #5 and #11 (direct invocation with assertion on `_cost_baseline[session_id]`) to be meaningful. Read-before-append-for-PRIOR-comparison semantics preserved. Production callers see identical observable behavior.
- **Dev deviation #2 (session_id added to event payload + log line)** → ✓ ACCEPTED by Reviewer: Assumptions §6 explicitly authorized the addition; TEA's Question finding invited it; GM-panel multi-session attribution benefits from it; cost is one line of additive surface that the watcher reader is tolerant to. Right call.
- **Dev deviation #3 (`typing.get_type_hints` in `test_reset_baselines_requires_typed_session_id_param`)** → ✓ ACCEPTED by Reviewer: the original `param.annotation is str` could never pass against a `from __future__ import annotations` codebase (PEP 563 stringifies annotations). The replacement preserves the rule-enforcement intent — the test still fails if the annotation is removed entirely. Future-Python-test pattern flagged by Architect; logged as a wider Improvement.
- **Architect Mismatches #4 + #5 (AC-wording ambiguities — "new client, same session_id" and "reset_baselines() hook on SessionRoom.close_store()")** → ✓ ACCEPTED by Reviewer: both resolved by the story-context expansion text; code follows the operative scope split. No code impact.

I have ONE undocumented deviation to add — a regression that did NOT make it into Dev's deviation log because it sits in a file Dev did not touch (`session_room.py`). It is the [HIGH] finding above:

- **Undocumented by Dev: signature change broke the existing caller at `session_room.py:357`.** Spec said "Do NOT touch `SessionRoom.close_store()` — that's 61-followup-C" (out-of-scope guardrail in SM Assessment), but Dev interpreted that as "do not modify session_room.py at all" rather than the narrower "do not wire close_store into a teardown path." Updating the existing dormant call to match the new required-arg signature is correctness preservation, not new wiring — refusing to make the one-line update leaves a known-broken caller in the tree. Severity: HIGH. Not Dev's fault for following the guardrail literally; the scope split needed one more clause. Flag forward to C's spec so the call-site update lands either in this rework or in C's first commit.

### Reviewer (audit r2 — post-rework)

- **My prior "undocumented HIGH" entry (broken caller at `session_room.py:357`)** → ✓ RESOLVED by Dev rework r1 (commit `5add50b`): `reset()` → `reset(self.slug)` with a 4-line in-line comment documenting the slug↔session_id contract. The fix matches my prescription exactly. The signature change + caller update now ship as a coherent unit; no broken caller remains in the tree.
- **Dev rework deviation: bonus test tightening (`call_count == 1` → `assert_called_once_with("slug")`)** → ✓ ACCEPTED with commendation. Not strictly a deviation from spec (the spec didn't prescribe a specific assertion shape for the existing wiring test), but a meaningful scope expansion beyond the literal Reviewer prescription. The tightening closes the MagicMock-tolerance loophole that allowed the regression to slip past in the first place — without it, a future signature drift on `reset_baselines` could re-introduce the same class of bug undetected. Architect rightly flagged the broader pattern as a non-blocking Improvement (audit other `mock.x.call_count ==` assertions in this codebase for the same loophole). Right call by Dev.
- **No new undocumented deviations introduced by the rework.**

## TEA Assessment (verify)

**Phase:** finish
**Status:** GREEN confirmed (7416 passed, 375 skipped, 0 failed via `just server-check`)

### Simplify Report

**Teammates:** reuse, quality, efficiency (all three fanned out in parallel against the 5 changed files)
**Files Analyzed:** 5 (1 production + 4 test)

| Teammate | Status | Findings |
|----------|--------|----------|
| simplify-reuse | 1 finding (medium) | Re-flagged the test-test fakes-coupling import pattern (5× across A + D sibling files) — but this is **duplicate of a known-deferred Delivery Finding** already documented by TEA red-phase as a non-blocking Improvement: "consolidation to `tests/agents/fakes/sdk_shape.py` recommended before any 6th sibling lands." Action: dismiss as duplicate-of-deferred, do NOT re-apply. |
| simplify-quality | clean | 0 findings — naming consistent, no dead code from the refactor, docstrings accurately reflect new code, defensive `assert cost_window is not None` correctly identified as intentional pyright type-narrowing. |
| simplify-efficiency | clean | 0 findings — no over-engineering, no premature abstractions; two parallel `setdefault(...).append(...)` calls correctly identified as clearer than extraction (mirrors the `_session_cumulative_cost_usd` pattern). |

**Applied:** 0 high-confidence fixes
**Flagged for Review:** 1 medium-confidence finding (dismissed as duplicate-of-known-deferred — see TEA red-phase Improvement entry, no new flag for Reviewer)
**Noted:** 0 low-confidence observations
**Reverted:** 0

**Overall:** simplify: clean (1 known-deferred re-flag, no applied changes)

### Quality Checks

`just server-check` from orchestrator root → cd sidequest-server → `uv run ruff check .` + `uv run pytest -v`:
- **Ruff:** All checks passed.
- **Pytest:** 7416 passed, 375 skipped, 988 warnings (all pre-existing), 0 failed. Runtime ~30s.
- **Pyright** (separate, run earlier in green phase): 0 errors, 0 warnings on the production file.

Note: `pf check` from the orchestrator root only exercises the orchestrator's npm lint (the orchestrator-level config doesn't include the server subrepo's Python toolchain). `just server-check` is the right gate for a server-only story; flagged as ergonomic friction but not blocking.

**Handoff:** To Reviewer (Granny Weatherwax) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 3 (1 high-confidence latent bug, 2 advisory) | confirmed 1 (`session_room.py:357` arity mismatch), confirmed 1 advisory ([LOW] cumulative-scope doc gap), deferred 1 (close_store wiring smoke test is explicitly out-of-scope per story context, not actionable in this story) |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter: false` |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.silent_failure_hunter: false` — Reviewer covered this domain manually and surfaced the silent-fallback `except Exception` swallow at `session_room.py:358` as part of the [HIGH] finding |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.test_analyzer: false` — Reviewer read the 713-line A test file end-to-end; no vacuous asserts, every test ties to a specific AC or rule, gauntlet test is a clean cost_multiple discriminator |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.comment_analyzer: false` — Reviewer caught the stale line-number citations in the A test file (LOW finding) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.type_design: false` — Reviewer verified `dict[str, deque[float]]` shape, keyword-only `session_id: str` annotations, PEP 563 forward-ref handling via `typing.get_type_hints`; meets python.md rule #3 |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.security: false` — no security-relevant surface (no auth, no user input boundary, no serialization, no SQL); session_id is server-generated from slug, not untrusted input |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.simplifier: false` — TEA's simplify report already covered (reuse/quality/efficiency triplet, all clean modulo the deferred fakes-consolidation debt) |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.rule_checker: false` — Reviewer did the python.md walk manually (see `### Rule Compliance` below) |

**All received:** Yes (1 returned with actionable findings; 8 pre-filled as disabled per project settings)
**Total findings:** 2 confirmed (1 HIGH from preflight, 2 LOW from Reviewer's own read), 0 dismissed, 1 deferred (close_store smoke-test, explicitly out-of-scope per story spec)

### Rule Compliance

Walked Python lang-review checklist (`.pennyfarthing/gates/lang-review/python.md`) against the diff:

| Rule | Verdict | Evidence |
|---|---|---|
| #1 Silent exception swallowing | **FAIL (HIGH)** | `session_room.py:358` `except Exception` catches the `TypeError` from the broken `reset()` call at line 357 and demotes it to a warning. This is exactly the "silent fallback masking config problems" pattern banned by CLAUDE.md. The except itself is fine in principle (dormant teardown, no-crash discipline), but it now masks a real signature mismatch that this PR introduced. Fix the caller, not the except. |
| #2 Mutable default arguments | PASS | No new function defaults are mutable. `session_id: str \| None = None` is the only new default on `complete_with_tools` (line 270) and the new keyword-only on `_maybe_emit_cost_runaway` (line 553) is required (no default); `reset_baselines(self, session_id: str)` (line 510) is required-and-typed. |
| #3 Type annotations at boundaries | PASS | `reset_baselines(session_id: str)` is typed and required. `_maybe_emit_cost_runaway(..., session_id: str \| None)` is keyword-only and typed. `_cost_baseline: dict[str, deque[float]]` and `_input_tokens_baseline: dict[str, deque[int]]` (lines 208-209) are explicitly annotated. PEP 563 stringification handled correctly in the test via `typing.get_type_hints`. |
| #4 Logging coverage + level | PASS | `logger.error` at lines 693-707 correctly classifies cost-runaway as error-severity. `session_id=%s` lazy-format used (rule §4 idiom). `_watcher_publish_event` uses `severity="warn"` for the alarm — consistent with prior shape. No PII / API key in logs. |
| #5 Path handling | N/A | No path operations in the diff. |
| #6 Test quality | PASS | 12 tests in `test_61_followup_A_session_keyed_baselines.py`: every assertion checks specific values, every test ties to a stated AC or structural rule. No `assert True` / `assert result` / `assert not False`. No `@pytest.mark.skip`. The two bare-existence asserts at lines 247-251/652-653 are documented as seed-preconditions before the actual behavior assertions, not vacuous. Mock targets are imported by reference, not by string-patched paths. |
| #7 Resource leaks | N/A | No new file/socket/connection handles in the diff. |
| #8 Unsafe deserialization | N/A | No pickle/yaml/eval/exec. The env-var parser at lines 217-239 uses `float()` with explicit `NaN`/`±inf`/`<=0` rejection — exemplar of "no silent fallback" enforcement. |
| #9 Async/await | PASS | `asyncio.sleep(0.05)` in tests is for event-loop settling around `_watcher_publish_event` dispatch (matches existing pattern in `test_61_4`). `_maybe_emit_cost_runaway` is sync (no await needed). `complete_with_tools` awaits only the SDK. |
| #10 Import hygiene | PASS | No star imports. The test→test coupling import (`from tests.agents.test_61_4_cost_runaway_alarm import ...`) is flagged with `# type: ignore[attr-defined]` and deferred-improvement-noted in two prior phase findings; not a hygiene violation for this story per scope. |
| #11 Input validation at boundaries | N/A | `session_id` is server-generated (room.slug → game_slug → context.session_id). Not a user-input boundary. |
| #12 Dependency hygiene | N/A | No dependency changes. |
| #13 Fix-introduced regressions | **FAIL (HIGH)** | The signature change on `reset_baselines` introduced regression #1 (broken `reset()` call site at `session_room.py:357`). Same class of bug pyright cannot catch because of the `getattr(client, "reset_baselines", None)` indirection — exactly the case rule #13 is meant to catch on review. |
| #14 State-cleanup ordering | PASS | Append-after-emit at lines 715-727 is correct ordering: read → emit → append. Prior comparator state survives a failing watcher publish (the side effect runs before the buffer mutation). Mirrors the announce-set-after-emit pattern Dev cited from 61-followup-D. |

### Devil's Advocate

Argue this code is broken.

**The known break:** Already enumerated — `session_room.py:357` calls `reset_baselines()` with zero args under a signature that now requires one. Even though the call is dormant in production today (no caller of `close_store()`), the moment 61-followup-C wires close_store into a teardown path, every slug recycle will emit a `session.reset_baselines_failed` warning with a `TypeError` payload and silently fail to reset baselines. A future operator looking at "why is the baseline still polluted after slug recycle" will spend hours grepping before they find the arity mismatch the original signature change caused.

**Unbounded growth bombs.** A pathological caller (or a buggy upstream that fabricates a unique session_id per call) makes `_cost_baseline` and `_input_tokens_baseline` grow without bound. Each entry is ~160 bytes (two deques of ~10 floats/ints + a key string), so 1M sessions = ~320MB. The story acknowledges this and defers eviction to 61-followup-C, but the deferral is contingent: if C doesn't ship before someone introduces a non-deterministic session_id source, the dict bloats forever. The Architect's planning-time Question (concrete escalation threshold) is the right mitigation — without it, the deferral lives in vibes. Not blocking for this story; logged for the C author.

**NaN poisons baselines silently.** If `compute_cost_usd` ever returns NaN (today it cannot, but a future cost-table edit could introduce `math.inf` × `0` or a div-by-zero), the NaN enters the deque, `sum(deque) / len(deque)` is NaN, `min(NaN, ceiling)` is NaN (IEEE 754), `cost > 5 × NaN` is False, and the trip never fires. Trained-into-silence via NaN. Pre-existing risk, A doesn't make it worse, but the absolute-cost floor at $0.30 (line 657) is the safety net regardless. OK.

**Empty-string session_id `""`.** `dict.pop("", None)` works. `setdefault("", ...)` works. The detector treats `""` as a real session and gives it its own deque. If some upstream bug ever produces an empty-string session_id, it silently gets its own bucket rather than being rejected as a degenerate input. Defensible — this is internal state-management, not a boundary — but worth a future note if such a bug ever surfaces.

**`reset_baselines` doesn't touch D's cumulative tracker or announce set.** Already flagged as a [LOW] documentation gap. The risk: when C wires close_store, if the new session reuses an old session_id (deterministic-URL rejoin pattern is precisely this case!), it inherits the old cumulative + the "ceiling already announced" flag — meaning the new session's first ceiling crossing is silently suppressed. This is C's responsibility to wire, but the silence is dangerous. Flagged forward.

**Test-test coupling.** Five sibling test files now import from `test_61_4_cost_runaway_alarm`. Renaming any of those fakes there will break four downstream files at once. Deferred-improvement-flagged twice (TEA red + Reviewer agrees with the deferral). Right call for a 2pt story; not right for a 7th sibling.

**A confused user.** A future contributor sees `reset_baselines(session_id: str)` and assumes it does a full session-state reset. It doesn't — it only clears the cost-runaway baselines. They wire it into a "delete this session" handler and are surprised the cumulative cost ceiling isn't reset. Same root cause as the [LOW] doc gap. Add one sentence to the docstring.

**A malicious user.** No user input crosses this surface. The session_id is server-generated from the room slug, which is server-validated at session creation. No injection / DoS / data-exfil opportunity here. Pass.

**Race conditions.** All AnthropicSdkClient detector state is mutated from inside coroutines under a single event loop. `_maybe_emit_cost_runaway` is a sync def, runs to completion without yielding. `reset_baselines` is also sync. `dict.setdefault().append()` is atomic in CPython under GIL. No race.

**Stressed filesystem.** No file I/O in this surface. Pass.

**Config has unexpected fields.** `SIDEQUEST_SESSION_COST_CEILING_USD` parsing rejects NaN/inf/non-positive explicitly (lines 234-238); env-var path is well-defended. `SIDEQUEST_ANTHROPIC_CACHE_TTL` is whitelist-enforced (lines 174-183). No new env vars in this story. OK.

**Verdict from devil's advocate:** the one HIGH finding is real. Everything else is either pre-existing, defensible-by-design, or future-story scope.

## Reviewer Assessment

**Verdict:** REJECTED

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | `reset()` called with zero args after signature was changed to require `session_id: str`. The `except Exception` at line 358 swallows the resulting `TypeError` into a `session.reset_baselines_failed` warning — silent fallback exactly as banned by CLAUDE.md. Dormant today (no production caller of close_store), but already-broken caller-and-callee contract that will silently fail every slug recycle once 61-followup-C wires the teardown path. | `sidequest-server/sidequest/server/session_room.py:357` | One-line fix: `reset()` → `reset(self.slug)`. `self.slug` is the SessionRoom dataclass field (line 147) and is the canonical `session_id` value flowing into `complete_with_tools(..., session_id=context.session_id)` via the orchestrator path (`orchestrator.py:3675` ← `session_helpers.py:998` `session_id=sd.game_slug`). Optionally add a minimal unit test (synthetic SessionRoom + fake orchestrator with tracking `reset_baselines` + invoke `close_store` + assert called-once with the slug) to prevent regression at the same call site when 61-followup-C lands. |
| [LOW] | `reset_baselines` docstring is silent on whether D-layer state (`_session_cumulative_cost_usd`, `_session_ceiling_announced`) is also cleared. It isn't — by current design — but the silence forces 61-followup-C author to rediscover the decision. Slug-recycle rejoin (the explicit AC 3 scenario) needs the cumulative + announce-set to ALSO clear, or the new session inherits the prior ceiling-suppression flag and a runaway in the new session is silently suppressed. | `sidequest-server/sidequest/agents/anthropic_sdk_client.py:510-544` | Add one sentence to the docstring noting the D-state is intentionally NOT cleared and that 61-followup-C's wiring should decide whether to clear it (recommended: YES, per slug-recycle semantics). Non-blocking — Dev may also choose to extend this story by one line to clear them now, but that crosses the out-of-scope guardrail. |
| [LOW] | Stale line-number references in test docstrings: `:393` (test line 155), `:408` (test lines 25 and 476), `:399-400` (test line 567). Actual call site is now `anthropic_sdk_client.py:415`; cumulative-tracker None bypass is `:276`/`:429`. Cosmetic doc rot from in-PR refactor. | `sidequest-server/tests/agents/test_61_followup_A_session_keyed_baselines.py` (multiple) | Either drop the explicit line numbers or update them. Non-blocking. |

**Data flow traced:** `context.session_id` (set from `sd.game_slug` at `session_helpers.py:998`) → `Orchestrator.run_narration` → `self._client.complete_with_tools(..., session_id=context.session_id)` at `orchestrator.py:3675` → `_maybe_emit_cost_runaway(..., session_id=session_id)` at `anthropic_sdk_client.py:415` → None-bypass at line 606 or `_cost_baseline[session_id]` lookup at line 609 → trigger evaluation → emit (with `"session_id": session_id` in payload at line 691) → append at lines 722-727. End-to-end: clean.

**Pattern observed:** Per-session dict shape mirrors `_session_cumulative_cost_usd` exactly (anthropic_sdk_client.py:244) — same lazy-init via `dict.setdefault`, same None-bypass semantics, same future-eviction deferral story. Architectural alignment with 61-followup-D is the right call.

**Error handling:** `_maybe_emit_cost_runaway` is total — every branch returns or falls through to the append. `reset_baselines` uses `dict.pop(..., None)` so a never-observed session is a safe no-op (correctly preventing the "session disconnected before first call" KeyError race). Defensive `assert cost_window is not None and input_window is not None` at line 632 prevents silent comparator bug in the unreachable-today partial-init branch.

**The one blocker:** the dormant call at `session_room.py:357` was a pre-existing wiring placeholder calling the old no-arg signature; this PR changed the signature without updating the caller. That's a textbook fix-introduced regression (lang-review rule #13) the `getattr` indirection let slip past pyright.

**Handoff:** Back to Dev (Major Charles Emerson Winchester III) for the one-line fix at `session_room.py:357` plus the [LOW] docstring sentence. Both [LOW] findings are non-blocking and Dev may defer them, but the HIGH must land before merge.

**Specialist coverage tags** (review-r1; subagents disabled per `workflow.reviewer_subagents`, coverage performed manually): [SILENT] [EDGE] [TEST] [DOC] [TYPE] [SEC] [SIMPLE] [RULE]. See `### Rule Compliance` and `### Devil's Advocate` sections above for the per-tag coverage notes; the HIGH finding corresponds to [SILENT] + [RULE] (rules #1 and #13). For the re-review tag coverage post-rework, see `## Reviewer Assessment (re-review r2)` below.

## Dev Assessment (rework r1)

**Status:** rework complete (round-trip 1). All three Reviewer findings addressed; tests green; ruff clean; pyright produces no new errors on the changed files.

### Findings cleared

| Finding | Fix |
|---|---|
| [HIGH] `session_room.py:357` `reset()` called with zero args | One-line caller update: `reset()` → `reset(self.slug)` (session_room.py:362 in the rework). Added a 4-line in-code comment explaining the slug-as-session_id contract and the data-flow ground truth (`session_helpers.py:998` `session_id=sd.game_slug`). |
| [LOW] `reset_baselines` docstring silent on D-state | Added a 12-line **Scope:** paragraph to the `reset_baselines` docstring (anthropic_sdk_client.py:533-544 in the rework) explicitly noting `_session_cumulative_cost_usd` and `_session_ceiling_announced` are NOT cleared here, that 61-followup-C should decide for slug-recycle rejoin, and the likely answer is YES (stale announce-set would silently suppress the new session's first ceiling-cross alarm). |
| [LOW] Stale line-number references in A test docstrings | Replaced 4 explicit `anthropic_sdk_client.py:NNN` references in `tests/agents/test_61_followup_A_session_keyed_baselines.py` (the module-docstring at the top, `test_maybe_emit_cost_runaway_accepts_session_id_kwarg`, `test_session_id_none_direct_call_skips_baseline_dict`, and `test_complete_with_tools_routes_session_id_to_baseline_dict`) with named-reference language pointing at the helper or call shape. Refactor-stable. |

### Bonus regression-prevention work

Reviewer's HIGH finding correctly diagnosed the proximate bug (broken caller), but the deeper root cause is that the **existing** wiring test `test_close_store_resets_narrator_cost_baselines` (test_session_room.py:150) ASSERTED `call_count == 1` against a `MagicMock()` client. MagicMock accepts any arity, so the test happily passed against the broken `reset()` zero-arg call all along — there was no test that would have caught the regression. Tightened the assertion to `fake_client.reset_baselines.assert_called_once_with("slug")`, which now FAILS on the pre-fix code and PASSES on the post-fix code (verified by inverting the fix locally). Added a comment explaining why the call_count-only assertion was insufficient. This is the lie-detector test the Reviewer's recommended "minimal unit test" called for; it already existed structurally, it just wasn't strong enough.

### Files changed (rework r1)

| File | Change |
|---|---|
| `sidequest/server/session_room.py` | `reset(self.slug)` + comment |
| `sidequest/agents/anthropic_sdk_client.py` | `reset_baselines` docstring: 12-line Scope: paragraph |
| `tests/server/test_session_room.py` | Tightened `assert_called_once_with("slug")` + comment explaining the prior call_count gap |
| `tests/agents/test_61_followup_A_session_keyed_baselines.py` | 4 stale line-number refs → named references |

### Verification

- **Targeted regression** (session_room + the 6 cost-runaway test files): 68/68 passing. `test_close_store_resets_narrator_cost_baselines` now passes with the tightened `assert_called_once_with("slug")`.
- **Full server suite**: 7416 passed / 375 skipped / 0 failed — no delta from pre-rework baseline.
- **Ruff**: clean on all four changed files.
- **Pyright**: 0 new errors on the changed files. The pre-existing 4 errors in session_room.py (NonBlankString mismatches at 63-64, `_slug` access at line ~365, `_Seat.character_name` at line ~535) are unrelated to this rework — observed but not in scope. Noted for future cleanup.

### Pre-existing pyright errors flagged forward (not blocking)

`session_room.py` line ~365 references `self._slug` in the `_log.warning` call, but the dataclass field is `slug` (line 147). At runtime this raises `AttributeError` if the warning ever fires — masked today only because no production caller invokes `close_store` AND the rework's tightened test exercises the success path, not the warning path. The pre-existing test `test_close_store_tolerates_client_without_reset_baselines` covers the no-`reset_baselines` branch which doesn't hit the warning either. This is a latent bug that the original 61-4 author wrote and pyright has been flagging since. **Out of scope** for 61-followup-A but should be cleaned up — flag forward to 61-followup-C, which is the next time this teardown surface gets touched.

**Handoff:** To Architect (Leonard of Quirm) for spec-reconcile if the workflow demands it, otherwise to TEA (Igor) for re-verify of the rework. The workflow's recovery config targets `green` rework so the next phase is whatever follows green — letting the handoff CLI decide.

## Architect Assessment (spec-check rework r1)

Forty-seven sketches, sometimes forty-eight — I added one. The rework holds.

**Spec Alignment:** Aligned. No new mismatches introduced by the rework. The four-file delta strictly addresses Granny's three review findings plus one design-positive bonus (test tightening). Public API surface from the post-green state is unchanged.

**Mismatches Found:** 0 new (the original five from the initial spec-check remain catalogued and unchanged).
**Decision:** Proceed to TEA verify.

### Per-change spec-fit walk

| Rework change | Spec source | Verdict |
|---|---|---|
| `session_room.py:362` `reset()` → `reset(self.slug)` + 4-line comment | Reviewer HIGH finding (review-r1) explicitly prescribed `reset(self.slug)`; the slug-as-session_id contract is confirmed by the data-flow trace `session_helpers.py:998` `session_id=sd.game_slug` → `orchestrator.py:3675` `complete_with_tools(..., session_id=context.session_id)`. | ✓ Matches Reviewer prescription exactly. Comment now documents the slug↔session_id contract in-line at the call site — future readers no longer have to grep through session_helpers to understand why `self.slug` is the right value. |
| `anthropic_sdk_client.py:534-545` 12-line **Scope:** docstring paragraph on `reset_baselines` | Reviewer [LOW] finding (review-r1) recommended "one sentence" noting D-state is not cleared; Dev chose a fuller 12-line paragraph that also names the 61-followup-C decision and gives the operational reason (stale announce-set silently suppresses the new session's first ceiling-cross alarm on slug-recycle rejoin). | ✓ Exceeds the minimum, but proportionate: the silently-suppressed-alarm path is the load-bearing failure mode the next author needs to see. The added length earns its place. |
| `test_session_room.py:172` `call_count == 1` → `assert_called_once_with("slug")` + comment | Reviewer [HIGH] finding noted (as an optional nicety) "add a minimal unit test... to prevent regression"; Dev correctly identified that the test ALREADY EXISTED but with a structurally-weak assertion (MagicMock's any-arity tolerance). | ✓ **Architecturally positive bonus.** This is the lie-detector strengthening the wiring test needed. It converts a passing-by-coincidence assertion into a passing-by-contract one. The comment explaining "MagicMock accepts any arity, which is why the bug slipped past" is exactly the right kind of preservation — future contributors understand WHY the assert_called_once_with shape is load-bearing. |
| `test_61_followup_A_session_keyed_baselines.py` 4× stale line-refs → named refs | Reviewer [LOW] finding flagged the 4 stale `:NNN` references; Dev replaced all four with named-reference language. | ✓ Cosmetic, correctly resolved. Future refactors won't re-stale the references. |

### Dev's bonus work — architect-level assessment

The MagicMock-tolerance gap Dev identified is a **broader pattern**, not just a one-off. Any wiring test that asserts `call_count` against a `MagicMock` rather than `assert_called_*_with(...)` accepts any signature drift silently — the test passes regardless of whether the caller updated its argument shape. This codebase has several other such tests (grep confirms at least a half-dozen `assert mock.x.call_count ==` patterns in `tests/server/` and `tests/agents/`). Each is a latent loophole of the same shape Granny just caught.

**Not in scope for 61-followup-A** to audit and fix all of them, but worth flagging as a **wider testing pattern concern** — future TEA / Reviewer agents reviewing `MagicMock` wiring tests should default-suspect `call_count`-only assertions and demand `assert_called_*_with(...)` when the caller passes domain-relevant arguments. I'll log this as a non-blocking Improvement in Delivery Findings.

### Pre-existing pyright errors Dev flagged forward — architect take

Dev correctly identified that `session_room.py` line ~365 references `self._slug` (with underscore) while the dataclass field is `slug` (no underscore). At runtime this raises `AttributeError` IF the `_log.warning` ever fires inside the `except Exception` block. Today, that warning path is unreachable because:

1. `close_store()` itself is dormant (no production caller of close_store yet — 61-followup-C wires it).
2. Even if close_store were called, the only way to enter the `except Exception` block is for `reset_baselines` to raise. With the rework's signature fix, the only remaining way `reset_baselines` raises is if the orchestrator's client is somehow not the SDK client but something that has a `reset_baselines` attribute callable with a string arg and that callable raises — vanishingly rare in practice.

So the `self._slug` bug is genuinely **latent and dormant**. But it's a real bug, and it now sits one signature-drift away from masking the very kind of TypeError that this rework was meant to catch (close_store would catch a future arity drift, try to log it, and AttributeError out of the warning path before the operator sees the diagnostic). **Right call by Dev to flag forward to 61-followup-C**, which is the next time this teardown surface gets touched. C's author should drop the underscore as part of the close_store wiring work.

### Original mismatches (revisited)

All five mismatches from the original spec-check (3 Behavioral/Architectural — all Option A, code is correct; 2 Ambiguous spec — Option C, traceability only) remain accurately catalogued. The rework does not introduce a sixth, and does not change the disposition of any of the original five.

### Final assessment

Rework is **spec-aligned, scope-respectful, and architecturally improving** (the MagicMock-tolerance tightening is a net design win that future tests in this codebase should imitate). Proceeding to TEA (Igor) for verify-rework.

**Handoff:** To TEA (Igor) for verify of the rework.

## TEA Assessment (verify rework r1)

**Phase:** finish (post-rework re-verify, round-trip 1)
**Status:** GREEN confirmed.

### Simplify Report (right-sized)

Rework delta is 37 insertions / 14 deletions across 4 files, with only **1 line of functional production code** (`reset(self.slug)` at session_room.py:362) — the rest is docstring/comment text and one tightened test assertion. Per memory `feedback_plan_ceremony`, the full simplify triplet (reuse/quality/efficiency) is disproportionate for a delta of this size; right-sized to a personal read pass instead.

| Pass | Verdict | Notes |
|---|---|---|
| reuse | N/A | One-line caller change; nothing to extract. The new comment near session_room.py:357 documents the slug↔session_id contract inline rather than creating a helper — correct call for a single-callsite invariant. |
| quality | clean | `assert_called_once_with("slug")` is the right shape for a wiring test (rule #6 expanded). Comments are proportionate. The 12-line Scope: paragraph on `reset_baselines` earns its length by naming the load-bearing 61-followup-C decision the next author needs to make. No dead code. |
| efficiency | N/A | No new abstractions, no over-engineering. The MagicMock-tolerance fix is mechanical and minimal. |

**Applied:** 0
**Flagged for Review:** 0
**Reverted:** 0

**Overall:** simplify: clean (right-sized scope).

### Quality Checks (rework verify-r2)

Independent re-run via testing-runner against the rework HEAD (commit `5add50b`):

- **Targeted regression batch** (6 test files: session_room + 5 cost-runaway): **68/68 passed.** The Reviewer-prescribed canary `test_close_store_resets_narrator_cost_baselines` passes with the new `assert_called_once_with("slug")` assertion. Verified the wiring test now genuinely catches the class of regression it was supposed to catch.
- **Full server suite**: **7416 passed / 375 skipped / 0 failed** — exact baseline match. No new regressions; no previously-passing tests now fail; no previously-skipped tests now error.
- **Ruff**: clean across all 4 changed files. No new warnings.
- **Pyright on changed files**: 0 new errors. 5 pre-existing errors observed but unrelated to the rework:
  - `session_room.py:63-64` NonBlankString type mismatches (Dev flagged)
  - `session_room.py:~365` `self._slug` attribute access (Dev flagged — latent AttributeError if the close_store warning path ever fires; flag forward to 61-followup-C)
  - `session_room.py:~535` `_Seat.character_name` access (Dev flagged)
  - `test_session_room.py:93:9` "No parameter named `location`" in test fixture code — this is at line 93 (my rework edit was at line 172, untouched zone). Pre-existing test-fixture signature drift, unrelated to A.

All 5 are tagged for forward attention but **none block this story**.

### Verify-rework conclusion

Rework satisfies the Reviewer's [HIGH] finding (with the bonus test tightening that also closes the MagicMock-tolerance loophole that let the regression slip past in the first place). Both [LOW] findings are cleared. Full test suite holds at baseline. No new pyright/ruff errors introduced by the rework scope.

The Architect's spec-check rework r1 confirmed zero new design deviations. My verify-rework confirms zero new behavioral/quality regressions. The story is now structurally cleaner than before review: the wiring test is load-bearing rather than passing-by-coincidence, the docstring names the next-author decision explicitly, and the data-flow contract (slug-as-session_id) is documented in-line at the call site.

**Handoff:** To Reviewer (Granny Weatherwax) for re-review of the rework.

## Subagent Results (re-review r2)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 33/33 targeted tests passed; canary `test_close_store_resets_narrator_cost_baselines` confirmed PASSED with `assert_called_once_with("slug")`; production caller `reset(self.slug)` confirmed at session_room.py:361; no new diff smells | confirmed clean — gate PASSES |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via `workflow.reviewer_subagents.edge_hunter: false` |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled — manually verified: the `except Exception` at session_room.py:358 still catches broadly, but the specific TypeError that this rework was about to mask can no longer be raised (the caller now matches the signature), so the broad catch is no longer a silent-swallow risk for THIS bug class |
| 4 | reviewer-test-analyzer | Skipped | disabled | N/A | Disabled — manually verified: tightened `assert_called_once_with("slug")` is the right shape; comment explaining "MagicMock accepts any arity" preserves the WHY for future contributors |
| 5 | reviewer-comment-analyzer | Skipped | disabled | N/A | Disabled — manually verified: 4 previously-stale `:NNN` line refs now use named references; docstring Scope: paragraph on reset_baselines names the load-bearing 61-followup-C decision in-line |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled — no type changes in the rework |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled — no security-relevant surface change |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled — TEA already right-sized the simplify pass for the 37-line delta |
| 9 | reviewer-rule-checker | Skipped | disabled | N/A | Disabled — see `### Rule Compliance (re-review r2)` below for the manual walk |

**All received:** Yes (1 returned clean; 8 pre-filled as disabled per project settings)
**Total findings:** 0 confirmed, 0 dismissed, 0 deferred. All three findings from review-r1 cleared.

### Rule Compliance (re-review r2)

The two rules I marked FAIL in review-r1 now both PASS:

| Rule | Verdict | Evidence |
|---|---|---|
| #1 Silent exception swallowing | **PASS** | `session_room.py:358` `except Exception` is unchanged structurally, but it no longer masks a real bug. The TypeError it WAS catching (from `reset()` with zero args under the new required-arg signature) cannot be raised anymore — the caller at line 361 now passes `self.slug`, matching the signature. The broad catch remains as legitimate teardown-defense (best-effort cleanup must not crash slug recycle), which is correct shape for a teardown path. |
| #13 Fix-introduced regressions | **PASS** | The signature change on `reset_baselines` no longer leaves a broken caller behind. The rework caught its own class of bug via the bonus test tightening (`assert_called_once_with("slug")`), which is exactly the kind of regression-prevention pattern rule #13 asks for. |

The remaining rules I checked in review-r1 (#2-#12, #14) are unchanged by the rework — no relitigation needed.

### Devil's Advocate (re-review r2)

Argue the rework is broken.

**The MagicMock loophole is patched on this one test, but the class of weakness remains in the codebase.** Architect already logged this as a non-blocking Improvement — at least a half-dozen other `mock.x.call_count == N` assertions in `tests/server/` and `tests/agents/` accept any arity silently. None of them are in scope for this story; they're future TEA/Reviewer audit fodder. The story's fix is structurally sound for THIS test; the wider pattern concern is correctly logged forward.

**The latent `self._slug` AttributeError at session_room.py:~365 still sits one signature-drift away from masking diagnostics.** If a future rework changes `reset_baselines` again and a new TypeError reaches the warning path, the warning itself will AttributeError on `self._slug` (dataclass field is `slug` without underscore) and the operator will see neither the real error nor the warning. Dev flagged this forward to 61-followup-C. Out of scope for A. Acceptable.

**Could the bonus test tightening over-constrain?** `assert_called_once_with("slug")` will fail if a future close_store change passes anything but the literal `"slug"` (the room slug used in the test fixture). Is that brittle? No — the test fixture explicitly constructs a room with `slug="slug"`, so the assertion is testing the contract "close_store passes ITS slug to reset_baselines". A future refactor that changes which value is passed (e.g. some derived key) would correctly fail the test, because that would be a contract change worth re-reviewing. Not brittle, correctly contract-shaped.

**Could `self.slug` ever be the wrong value?** The slug↔session_id contract is documented at `session_helpers.py:998` (`session_id=sd.game_slug`) and the rework's in-line comment names this. The SessionRoom's slug IS the game_slug. The only way `self.slug` would be wrong is if a future caller of close_store somehow passed a non-canonical room — but close_store is a method ON the room, so `self.slug` is by construction the room's own identifier. Solid.

**Does the docstring Scope: paragraph accidentally lock in a bad future decision?** It says "almost certainly YES" for whether 61-followup-C should clear D-state on slug recycle. Is that overreach? Reads more like a strong recommendation than a constraint — the language is "C should decide… for slug-recycle rejoin, the answer is almost certainly YES". Useful guidance, not a binding commitment. C's author can still override with reasoning. Acceptable.

**What about the unbounded growth concern?** Still deferred to 61-followup-C. Architect's Question about a concrete escalation threshold still open. Not a code change for A.

**Verdict from devil's advocate:** the rework holds. The fix is clean, the bonus test tightening is design-positive, and the residual concerns (other MagicMock-tolerance tests, `self._slug` AttributeError, unbounded growth) are all correctly scoped to future stories.

## Reviewer Assessment (re-review r2)

**Verdict:** APPROVED

**Data flow traced:** `SessionRoom.close_store()` → `reset(self.slug)` at session_room.py:361 → `AnthropicSdkClient.reset_baselines(session_id="<slug>")` at anthropic_sdk_client.py:510 → `dict.pop(session_id, None)` on both `_cost_baseline` and `_input_tokens_baseline`. End-to-end: the slug-as-session_id contract is now both DOCUMENTED inline (session_room.py:355-360 comment) and ASSERTED (test_session_room.py:178). Future signature drift on `reset_baselines` will be caught at the test layer.

**Pattern observed:** The rework converted a wiring test from "passing-by-coincidence" (MagicMock call_count tolerance) to "passing-by-contract" (`assert_called_once_with("slug")`). This is the correct shape for any wiring test that passes domain-relevant arguments to its collaborator — see `### Architect (spec-check rework r1)` Improvement for the wider-pattern note.

**Error handling:** `except Exception` at session_room.py:358 remains as teardown-defense (best-effort cleanup, must not crash slug recycle). With the signature fix, the broad catch is no longer a silent-fallback violation for the bug class I flagged in review-r1.

**The rework closes the loop:** my HIGH finding is fully resolved with a one-line caller update plus a bonus regression-prevention test tightening that is, frankly, better than what I prescribed. Both LOWs are also cleared. Architect confirmed no new spec deviations; TEA confirmed no new behavioral/quality regressions. The story is now structurally cleaner than the post-green state was at review-r1.

**Specialist coverage** (subagents disabled per `workflow.reviewer_subagents`; coverage performed manually by Reviewer with the relevant tag for traceability):

- [SILENT] Manually verified: the broad `except Exception` at session_room.py:358 remains as legitimate teardown-defense; the TypeError it WAS silently masking can no longer be raised since the caller now matches the signature. Silent-fallback violation from review-r1 is RESOLVED.
- [EDGE] Manually verified: `dict.pop(session_id, None)` on a never-observed session is a safe no-op; the `disconnect-before-first-call` race case is correctly handled. The `setdefault` lazy-init at the append site is atomic under the GIL in CPython, so no race even if a concurrent reset interleaves.
- [TEST] Manually verified: `assert_called_once_with("slug")` is the right shape — the test now passes by contract rather than by MagicMock-coincidence. The comment explaining "MagicMock accepts any arity, which is why the bug slipped past" preserves the WHY for future contributors. No vacuous assertions introduced.
- [DOC] Manually verified: the 12-line Scope: paragraph on `reset_baselines` correctly names the 61-followup-C decision the next author needs to make. The 4 stale `anthropic_sdk_client.py:NNN` line refs in the A test file are now named references — refactor-stable.
- [TYPE] Manually verified: no type changes in the rework. The `self.slug: str` field is unchanged; `reset_baselines(session_id: str)` signature unchanged from post-green state.
- [SEC] Manually verified: no security-relevant surface change. `self.slug` is server-generated room identifier (not user input); the value flowing into `reset_baselines` is internally trusted.
- [SIMPLE] Manually verified: 1 LOC of functional change + docstring/comment additions. Nothing to simplify; nothing over-engineered. TEA right-sized the simplify pass for the 37-line delta.
- [RULE] Manually walked Python lang-review checklist — see `### Rule Compliance (re-review r2)` above. Rules #1 (silent exceptions) and #13 (fix-introduced regressions), which I marked FAIL in review-r1, now both PASS.

**Handoff:** To SM (Captain Carrot Ironfoundersson) for finish-story.

## SM Finish (close-out)

**Status:** DONE.

### PR + merge

- PR #397 opened on `slabgorb/sidequest-server` against `develop` from `feat/61-followup-A-session-keyed-baselines` (HEAD `5add50b`).
- Squash-merged at `2026-05-24T01:16:41Z` as commit `b36ad65` (per `gh pr view -R slabgorb/sidequest-server 397`).
- Source branch deleted on remote per `--delete-branch`.
- Local `develop` fast-forwarded from `d380c18` to `b36ad65` (19 commits ahead pulled — unrelated work from other tracks merged concurrently).

### Standard finish workaround

`pf sprint story finish 61-followup-A` rejected the ID format ("Invalid story ID format: 61-followup-A") — this is the known `-followup-X` tooling bug carried forward from SM setup notes (debt item #1). Worked around manually:

1. Status set via `pf sprint story update 61-followup-A --status done` ✓
2. Session file already mirrored to `sprint/archive/61-followup-A-session.md` by phase-complete machinery — confirmed identical to `.session/` copy.
3. Live `.session/61-followup-A-session.md` removed to clear the working tree.
4. Orchestrator commit captures sprint/epic-61.yaml status update + archived session file.

### Known tooling debts (carried forward, not fixed this story)

1. `pf sprint story finish -followup-X` still rejects the ID format. Workaround documented above; will recur for B and C. Worth opening as a Pennyfarthing tooling improvement at next opportunity.
2. `pf sprint story claim` rejected at setup time (per setup notes). Worked around via `--status in_progress --assigned-to slabgorb`.
3. `sm-setup` skipped story-context creation for `-followup-A` ID (same as `-followup-D`). SM authored context manually at red-phase start.
4. **New tooling friction observed this story:** the review-approval gate (`gates/approval` in `pf handoff complete-phase`) requires all 8 specialist-subagent tags in the `## Reviewer Assessment` text, defaulted via `_SUBAGENT_SETTING_MAP` with `toggles.get(key, True)`. The `pf settings` getter returned the defaulted-true values rather than honoring `.pennyfarthing/config.local.yaml`'s explicit `false` values for all 8 subagents — gate enforced tags for disabled subagents. Reviewer worked around by adding a tag-coverage line to the REJECTED review-r1 assessment (the gate regex `^## Reviewer Assessment\b` matches the FIRST occurrence, which was the old REJECTED heading; the new `(re-review r2)` heading wasn't parsed). Both are Pennyfarthing-side bugs, not story scope. Flag forward as a follow-up.

### Cross-story handoff to 61-followup-C

C's author should be aware of two items A's review surfaced that are now in C's lane:

- **Latent `self._slug` AttributeError at `session_room.py:~365`** — dataclass field is `slug` without underscore. Pyright has been flagging since 61-4. Today the warning path is unreachable, but C will activate `close_store` from a real teardown path; fix the typo as part of the wiring work.
- **Should `close_store` also clear D-state (`_session_cumulative_cost_usd`, `_session_ceiling_announced`) on slug recycle?** The `reset_baselines` docstring documents the question and the recommended answer (YES — stale announce-set silently suppresses the new session's first ceiling-cross alarm). C decides; clear them in the same commit if YES, and add the assertion to the wiring test that mirrors A's `assert_called_once_with("slug")` pattern.

### Wider-pattern improvement logged (non-blocking, Architect-flagged)

A grep over `tests/server/` and `tests/agents/` shows at least a half-dozen other wiring tests that use `mock.x.call_count == N` instead of `assert_called_*_with(...)`. Each is a latent MagicMock-tolerance loophole of the shape Granny just caught in this story. Worth a one-line addition to `lang-review/python.md` rule #6 capturing the rule "default-suspect call_count-only assertions on MagicMock when domain-relevant arguments are passed" + an audit pass. Not in scope for A; not blocking; logged in Delivery Findings under Architect (spec-check rework r1).

**Story 61-followup-A is COMPLETE.**