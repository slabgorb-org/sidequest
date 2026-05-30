# Story 59-22 Context: Extract shared `_deliver_to_connected_recipients` helper

> Parent epic: 59 (Playtest bug fixes / mechanical-engagement cleanup) — see `sprint/epic-59.yaml`
> Workflow: tdd · Repos: server · Points: 3 · Priority: p3
> Follow-up to **59-16** (simplify-reuse medium-confidence finding, verify phase — NOT auto-applied).

## Objective

`sidequest/server/emitters.py` has **two** recipient-delivery loops that independently re-implement the
same socket → queue → drop-on-loss → `put_nowait` dispatch pattern. Extract a single shared helper so the
mid-broadcast drop handling lives in exactly one place.

This is a **refactor-only** story: behavior is unchanged, and the existing `emit_event` + confrontation
delivery tests must stay green. The whole point is dedup, not new functionality.

## The two duplicated loops (verified 2026-05-30)

**A. `_deliver_fanout(...)`** — `emitters.py:71–127`
Iterates `fanout: list[tuple[str, FilterDecision, dict]]`. Per recipient:
`if not decision.include: continue` → `room.socket_for_player(pid)` (None → `_emit_recipient_dropped(kind, pid, "socket_gone")`) → `room.queue_for_socket(socket_id)` (None → `_emit_recipient_dropped(..., "queue_detached")`) → **build payload inline** from the filtered dict (C3 `payload_cls.model_validate({**filtered_data, "seq": seq})`, `_visibility` strip, `try/except` logs `fanout_failed`) → `queue.put_nowait(msg)`.

**B. The `per_recipient_payload` supplier loop inside `emit_event`** — `emitters.py:403–417`
Iterates `room.connected_player_ids()`. Per recipient:
`msg = _frame_for(pid)` (the builder; `None` → skip) → tracks `emitter_msg` when `pid == emitter_player_id` → `if msg is None: continue` → `room.socket_for_player(pid)` (None → `"socket_gone"`) → `room.queue_for_socket(socket_id)` (None → `"queue_detached"`) → `queue.put_nowait(msg)`.

**Shared core** (the dedup target): the `socket_for_player → _emit_recipient_dropped("socket_gone") →
queue_for_socket → _emit_recipient_dropped("queue_detached") → put_nowait` sequence.

**What differs** (must be preserved via abstraction, not flattened):
- **Message construction.** Loop A rebuilds from the filtered dict under the C3 `model_validate` rule with
  its own `try/except`+`fanout_failed` log and `_visibility` strip. Loop B has the message already built by
  `_frame_for(pid)` and treats a `None` return as "send nothing to this socket." → the helper needs a
  **builder-callable abstraction**: `message_builder(pid) -> message | None`, where `None` means skip.
- **Include gate.** Loop A skips on `not decision.include`; Loop B skips on builder→`None`. Fold A's
  include-gate into its builder (builder returns `None` when `decision.include` is False) so the helper has
  one skip rule.
- **Emitter back-compat.** Loop B must still capture the emitter's own frame (`pid == emitter_player_id`)
  to return it to the caller. The helper must not swallow this — either return the per-pid frames/let the
  caller capture the emitter's, or expose the emitter frame. Do NOT regress the Story 59-20
  emitter-fallback logic at `emitters.py:421–434` (cleared-frame return when the supplier yields `None`
  for the emitter) — that stays in `emit_event`, outside the helper.

## Proposed shape (Dev/TEA may refine)

```python
def _deliver_to_connected_recipients(
    room, recipients, *, message_builder, kind,
) -> None:  # or return captured frames if the caller needs the emitter's
    for pid in recipients:
        msg = message_builder(pid)
        if msg is None:
            continue
        socket_id = room.socket_for_player(pid)
        if socket_id is None:
            _emit_recipient_dropped(kind, pid, "socket_gone"); continue
        queue = room.queue_for_socket(socket_id)
        if queue is None:
            _emit_recipient_dropped(kind, pid, "queue_detached"); continue
        queue.put_nowait(msg)
```
Loop A's caller passes `recipients = [pid for (pid, decision, data) in fanout]` and a builder that
encapsulates the include-gate + C3 model_validate + `_visibility` strip + `fanout_failed` try/except.
Loop B's caller passes `recipients = room.connected_player_ids()` and `_frame_for` as the builder, then
captures the emitter frame itself.

> Exact return contract (how the emitter frame gets back to `emit_event`) is a Dev decision — keep the
> two callers' observable behavior identical to today.

## Acceptance Criteria

- [ ] **AC1:** A single `_deliver_to_connected_recipients` helper exists; BOTH `_deliver_fanout` and the
  `emit_event` supplier loop delegate the socket/queue/drop/`put_nowait` dispatch to it. No third copy.
- [ ] **AC2:** Behavior unchanged — `socket_gone` / `queue_detached` drops still fire `_emit_recipient_dropped`
  with the same `kind`/reason; the C3 `model_validate` payload rebuild + `_visibility` strip + `fanout_failed`
  handling are preserved for the fanout path; the emitter-frame return value of `emit_event` is unchanged,
  including the 59-20 cleared-frame fallback.
- [ ] **AC3:** The full existing emitter/confrontation delivery test suite stays green (see Testing), and
  the helper has a direct unit test exercising both the happy path and BOTH drop reasons against a real
  `SessionRoom` with synthetic recipients (the `_deliver_fanout` docstring already establishes this
  no-DB/no-pack/no-projection testing style — extend it to the new helper).

## Files Affected

- `sidequest-server/sidequest/server/emitters.py` — extract the helper; rewire both call sites.
- `sidequest-server/tests/server/test_emit_fanout_recipient_drop.py` — existing drop-window coverage; the
  primary regression guard. Add/extend helper-level tests here or in a sibling.
- Adjacent guards that MUST stay green: `tests/server/test_emitters.py`,
  `tests/server/test_confrontation_single_delivery.py`, `tests/server/test_merged_mp_emitter_projection.py`,
  `tests/server/test_opening_emit_event_71_13.py`, `tests/server/test_emitters_broadcast_delta.py`.

## Testing Strategy

- **TDD note:** this is a pure refactor, so the "RED" test is a *characterization* test — write a helper-level
  test that pins the shared dispatch contract (happy path + `socket_gone` + `queue_detached` both surfacing
  `_emit_recipient_dropped`) such that it can only pass once both call sites route through the one helper. The
  existing behavior tests are the safety net proving no regression.
- **Wiring (required):** at least one assertion must prove BOTH production call sites go through the helper
  (e.g. patch/spy `_deliver_to_connected_recipients` and assert it's invoked by a fanout emit AND by a
  `per_recipient_payload` emit) — not just that the helper works in isolation.
- **Env:** server suite needs `SIDEQUEST_DATABASE_URL=postgresql://$USER@localhost:5432/sidequest_test`
  (else ~33 phantom `MissingDatabaseUrlError`) and `SIDEQUEST_GENRE_PACKS` for content-gated tests. Gate on
  the full suite with content, not a scoped subset — record the baseline failure list first; any failure not
  in it is a regression.
