---
parent: context-epic-61.md
workflow: tdd
---

# Story 61-followup-A: Session-id-keyed baselines on AnthropicSdkClient (cross-session pollution on slug-reuse rejoin)

## Business Context

The 61-4 cost-runaway fingerprint detector compares each call against a rolling baseline of the prior K=10 calls. Story 61-followup-D landed two complementary defenses — a baseline ceiling clamp and a per-session cumulative HARD KILL — that together close the worst leak from the 2026-05-23 $313 incident. But one structural mismatch remains: **the baseline deques live on the `AnthropicSdkClient` instance, not on the session.**

This matters because:

1. **Multiplayer session URLs are deterministic** (memory `project_session_id_dropin`): `/play/{date}-{world}-mp` rejoins the existing session. Different humans, different connections, *same session_id*. Today, the `AnthropicSdkClient` instance behind a slug's orchestrator may be re-used across what should be conceptually separate sessions, or recycled when a fresh process gets a new instance for an old session. Either way the *session* and the *instance* are not the same conceptual unit.
2. **The 61-followup-D cumulative tracker is already session-keyed** (`_session_cumulative_cost_usd: dict[str, float]`, anthropic_sdk_client.py:226). The baselines should mirror that pattern so the cost-runaway picture is consistent: a session has its own cumulative spend AND its own baseline window. Otherwise the comparator and the kill switch disagree on what a "session" is.
3. **`reset_baselines()` is already documented as scope-confused** (anthropic_sdk_client.py:489-511). The docstring openly notes it's instance-wide today and that 61-followup-C will eventually wire `SessionRoom.close_store()` as the call site — but `close_store()` is per-session. The current instance-wide reset would clobber other sessions' baselines if it actually fired. This story makes `reset_baselines` per-session so C can wire it without a footgun.

Outcome: a session's rolling baseline is owned by *that session*. A fresh session starts cold. A deterministic-URL rejoin to the same session_id inherits the prior baseline (drift continuity preserved). The 61-followup-C wiring can land on a sound foundation.

## Technical Guardrails

### Single file in scope

- **`sidequest-server/sidequest/agents/anthropic_sdk_client.py`** — only file that should change in the production tree.

### Surfaces to modify

| Surface | Today | After A |
|---|---|---|
| `self._cost_baseline` (line 190) | `deque[float]`, instance-wide | `dict[str, deque[float]]`, keyed on session_id |
| `self._input_tokens_baseline` (line 191) | `deque[int]`, instance-wide | `dict[str, deque[int]]`, keyed on session_id |
| `_maybe_emit_cost_runaway(...)` (line 513) | reads/writes instance deques | takes `session_id`, reads/writes the session's deques |
| Call site at line 393 in `complete_with_tools` | `self._maybe_emit_cost_runaway(...)` | pass `session_id` through (already in scope at line 252) |
| Append calls at lines 399-400 | append to instance deques | append to the session's deques |
| `reset_baselines()` (line 489) | clears instance deques | `reset_baselines(session_id: str)` — clears only that session's deques |

### Pattern to mirror

The 61-followup-D cumulative tracker is the explicit model:

```python
# anthropic_sdk_client.py:226 (existing — DO NOT MODIFY in this story)
self._session_cumulative_cost_usd: dict[str, float] = {}
self._session_ceiling_announced: set[str] = set()
```

A is the symmetric move for the baseline windows. Use the same `dict[str, ...]` shape, lazy initialization on first access, and the same `session_id=None` bypass semantics described below.

### `session_id=None` bypass — preserve verbatim

61-followup-D's contract: `session_id=None` bypasses the cumulative tracker because non-narrator codepaths (dungeon `materializer.py` one-shot curate, future ad-hoc one-shots) don't have a session identity. The baseline detector must follow the same rule:

- If `session_id is None`, **skip the baseline read AND skip the baseline append.** The detector is a no-op for that call. (This is a behavioral change from today, where `None`-session calls also feed the instance-wide window. Today's behavior is incidental — non-narrator calls were polluting the narrator's baseline. The new behavior is the principled one and aligns with how 61-followup-D treats `None`.)
- The two production narrator call sites already pass `session_id`: `orchestrator.py:2661` and `orchestrator.py:2674`. So narrator coverage is unchanged.

### What NOT to touch

- **`SessionRoom.close_store()`** (`sidequest-server/sidequest/server/session_room.py:322`) — that is 61-followup-C's wiring story. C is the natural call site for `reset_baselines(session_id)`. A only makes the API session-shaped; A does not invoke it from `close_store`.
- **`_session_cumulative_cost_usd`** and **`_session_ceiling_announced`** — already correct, do not touch.
- **`narrator.sdk.usage` log line** (~line 370) — promoting that to a watcher event is 61-followup-B's story. A leaves it alone.
- **Baseline-ceiling clamp logic** (61-followup-D §A, lines 558-573) — the clamp computation is unchanged; only the deques being averaged are swapped from instance-wide to session-scoped.
- **Trigger priority / fingerprint logic** — io_fingerprint > input_absolute > cost_multiple > cost_absolute stays exactly as is. Only the *what baseline am I comparing against* changes.
- **`AnthropicSdkConfigError`, `AnthropicSdkCostCeilingExceeded`** — no new typed exceptions for A.

### Test fakes — coordination with sibling stories

All four `tests/agents/test_61_followup_D_*.py` files import private fakes (`_FakeSocket`, `_Sdk`, `_resp`, ...) from `tests/agents/test_61_4_cost_runaway_alarm.py`. Per the handoff debt note: **if A's tests need to be a fifth sibling that reaches for those fakes, consolidate the shared shapes into `tests/agents/fakes/sdk_shape.py` first**, then have A and the four D files import from there. Don't deepen the test-test coupling.

If A's tests can be written by extending an existing `test_61_followup_D_*` file (the orchestrator-wiring file is the closest spiritual sibling), do that instead — but only if it doesn't make the file unwieldy.

## Scope Boundaries

**In scope:**

- Convert `_cost_baseline` and `_input_tokens_baseline` from instance-wide deques to `dict[session_id, deque]`.
- Plumb `session_id` through `_maybe_emit_cost_runaway` from its single caller (`complete_with_tools`).
- Convert `reset_baselines()` → `reset_baselines(session_id: str)`. Update its docstring (currently flags itself as dormant) to reflect the per-session signature and the C-wiring handoff.
- `session_id is None` bypasses baseline read AND baseline append (behavioral change, explicit in AC Context).
- Unit tests: cross-session independence, fresh-session cold start, slug-reuse rejoin continuity, `reset_baselines(session_id)` scoped to that session only.
- One **wiring/integration test** that drives `complete_with_tools` twice with the same `session_id` (real method, fake SDK) and asserts the baseline persists across calls — and once more with a different `session_id` and asserts independence.

**Out of scope:**

- Wiring `SessionRoom.close_store()` to call `reset_baselines(session_id)`. **That is 61-followup-C.**
- Promoting `narrator.sdk.usage` log → watcher event. **That is 61-followup-B.**
- Unbounded growth of the per-session deque dict. The dict grows one entry per distinct session_id seen, same as the 61-followup-D cumulative dict. C lights up `close_store` as the eviction hook. A document the explicit deferral in the Assumptions section. Do not invent a TTL or LRU here.
- Any change to triggers, priority, clamp values, or ceiling envs.
- Any change to the materializer one-shot curate path (it passes `session_id=None`, which the new bypass handles).

## AC Context

### AC 1 — Per-session baseline keying (independence)

**Pass condition:** Constructing one client, then calling its `_maybe_emit_cost_runaway` (or driving it via `complete_with_tools`) with `session_id="A"` followed by `session_id="B"` results in two independent deques. Inspecting `self._cost_baseline["A"]` and `self._cost_baseline["B"]` shows different content for each.

**Edge case:** First call for a session — the deque doesn't exist yet. The implementation must lazily create the deque (`maxlen=_BASELINE_WINDOW_K`) on first append, the same way the 61-followup-D cumulative dict lazy-inits.

**Test shape:** Direct unit test on a constructed client; call `_maybe_emit_cost_runaway(session_id="A", ...)` 3 times with distinct cost/input values, then `session_id="B"` once, assert dict has exactly two keys, each with the expected content.

### AC 2 — Fresh rejoin starts with clean baseline

**Pass condition:** Calling `_maybe_emit_cost_runaway(session_id="brand_new", ...)` when "brand_new" has no entry in the dict treats the call as warmup (uses `_WARMUP_COST_USD_FLOOR` / `_WARMUP_INPUT_TOKENS_FLOOR`). No event fires unless absolute floors are crossed.

**Edge case:** This is structurally the same as today's "first call after construction" — confirm warmup path still works through the dict indirection.

**Test shape:** Build a fresh client, fire one call below warmup floor with a never-seen session_id, assert no `cost_runaway_suspected` event.

### AC 3 — Slug-reuse rejoin inherits prior baseline

**Pass condition:** Two `complete_with_tools` invocations on the same client instance with the same `session_id` — separated by an arbitrary number of *other* sessions' calls in between — see a baseline window that reflects the prior calls for that session_id only. The "other sessions" must NOT contribute to this session's baseline.

**Edge case:** This is the inverse of AC 1. AC 1 proves independence; AC 3 proves continuity.

**Test shape:** Drive session "A" through `_BASELINE_WINDOW_K` calls at $0.05 each; drive session "B" through `_BASELINE_WINDOW_K` calls at $0.50 each; then fire one more call on session "A" at $0.50; assert it trips `cost_multiple` (baseline ~$0.05 × 5 = $0.25 < $0.50), **not** swallowed by session B's contamination.

### AC 4 — `reset_baselines(session_id)` scoped to session

**Pass condition:** `reset_baselines("A")` clears the deques for "A" only. Other sessions' deques are untouched. Calling `reset_baselines` on a never-seen session_id is a no-op (no KeyError).

**Edge case:** The dormant-infrastructure docstring (anthropic_sdk_client.py:489-511) needs updating. The new docstring should: (a) describe the new per-session signature, (b) note that 61-followup-C is the planned call site (still not wired here), (c) keep the explanation of *why* the reset matters once teardown wires in.

**Test shape:** Populate baselines for two session_ids, call `reset_baselines("A")`, assert "A" cleared and "B" intact. Then call `reset_baselines("never_seen")` and assert no exception.

### AC 5 — Regression unit test (cross-session independence + fingerprint)

This is the comprehensive unit test that combines ACs 1+3: two session_ids with parallel call sequences, asserting both that they maintain independent deques AND that the fingerprint detector compares against the correct session's deque. See AC 3 test shape — that single test covers both.

### AC 6 — Wiring/integration test

**Pass condition:** Drive the real `complete_with_tools` method (not just the private `_maybe_emit_cost_runaway`) with a fake SDK twice using the same `session_id`, then once with a different `session_id`. Assert via `_cost_baseline` inspection that the same-session calls share a deque and the different-session call sits in a separate deque.

**Rationale per server CLAUDE.md** ("Every Test Suite Needs a Wiring Test"): unit tests on `_maybe_emit_cost_runaway` prove the comparator works in isolation; this integration test proves `complete_with_tools` is actually plumbing `session_id` through. Without it, a future refactor that drops the `session_id` argument from the internal call site would pass all unit tests and silently regress to instance-wide pollution.

**Note on the handoff phrasing:** the story body originally mentioned "multiplayer rejoin flow." That's the conceptual scenario; the unit-test mechanical equivalent is "two `complete_with_tools` calls with the same `session_id` parameter on a single client instance." Don't spin up a real WebSocket session for this — the fake-SDK harness used by the 61-4 / 61-followup-D test files is the right level.

## Assumptions

1. **The 61-followup-D pattern is the model.** `_session_cumulative_cost_usd: dict[str, float]` (line 226) and `_session_ceiling_announced: set[str]` (line 230) demonstrate the chosen pattern for per-session client state. A mirrors that shape exactly. *If implementation finds the cumulative tracker has been restructured before A lands, log a Design Deviation and align.*

2. **`session_id=None` bypass is the principled behavior.** Non-narrator codepaths (dungeon materializer one-shot curate) pass `session_id=None` and should not contribute to baseline windows. This is consistent with how 61-followup-D treats them. *If Dev discovers a production call site that passes `session_id=None` to the narrator path, that's a 61-followup-D-era bug — flag it as a Design Deviation, do not paper over it.*

3. **Unbounded growth of the per-session dict is deferred to 61-followup-C.** A introduces a `dict[session_id, deque]` that grows one entry per distinct session_id seen, same as the existing cumulative dict. Memory bound = O(distinct session_ids since process start). Mitigation arrives in C via `close_store` eviction. *If this becomes a real memory pressure problem before C lands, escalate; do not add a TTL/LRU in A.*

4. **The 61-followup-C wiring (close_store → reset_baselines) lands after A.** A's docstring update for `reset_baselines` references C as the planned wiring story. *If the queue order changes and C ships first, that's fine — A's per-session signature is forward-compatible with whatever call site C builds.*

5. **Test fakes consolidation is a judgment call.** The handoff flags test-test coupling debt: four sibling files share private fakes from `test_61_4_cost_runaway_alarm.py`. A's test author should: (a) try to extend `test_61_followup_D_orchestrator_wiring.py` if possible (no new fakes needed); (b) if A genuinely needs a fifth file, consolidate first into `tests/agents/fakes/sdk_shape.py`. *Either decision is acceptable; document the choice in Delivery Findings so the next story has a clear precedent.*

6. **No new OTEL event in A.** The per-session baseline switch doesn't add a new mechanical decision point — it changes *which* deque a comparison reads from. The existing `cost_runaway_suspected` event already carries the baseline values that fired the trigger, and that signal is unchanged in shape. *If implementation discovers a case where operators can't tell which session a baseline event came from, add `session_id` to the event payload as the smallest possible addition — do not invent a new event.*
