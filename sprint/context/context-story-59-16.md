---
parent: context-epic-59.md
workflow: tdd
---

# Story 59-16: Confrontation beats — collapse to one filtered delivery path

## ⚠️ Staleness Check

**Work is NOT started. Spec premise verified live; line numbers in the spec/description have DRIFTED — re-locate by symbol, not by number.**

- Branch `feat/confrontation-single-filtered-delivery` (sidequest-server) **does not exist** locally or on `origin`/`oq1-local` (verified `git branch -a`). No commits. RED-first is clean.
- The dual-delivery bug is **still live**. Both racing mechanisms are present in production code today:
  - **Unfiltered full-union `CONFRONTATION` broadcast** + **per-PC class-filtered overlay queued behind it** in `websocket_session_handler.py` and `dispatch/dice.py`. The UI is last-message-wins.
  - `emitters.py` still gates `project_emitter = author_player_id is not None`; the CONFRONTATION emits pass **no** `author_player_id`, so the solo emitter raw-bypasses the firewall and `out_to_self` is the raw union.
- **Line numbers cited in the description/spec are stale** (the spec references a 4500+-line file; both handlers are now ~3368 / ~773 lines). Verified current sites:
  | Spec citation | Actual site (verified 2026-05-28) |
  |---|---|
  | `emitters.py:240` project_emitter / `:460-464` out_to_self | `sidequest/server/emitters.py:302` (`project_emitter`), `:534`/`:552` (`out_to_self`), `def emit_event` at `:235` |
  | `wssh:4525` start emit / `4614-4657` overlay | `websocket_session_handler.py:1607-1628` (canonical emit), `1630-1685` (overlay loop) |
  | `dice.py:647` broadcast / `667-704` overlay | `dispatch/dice.py:619-652` (`room_broadcast` canonical), `665-692` (per-PC overlay loop) |
  | `connect.py:1474` resume filter | `handlers/connect.py:1515-1568` (already a single clean filtered call) |
- `resolve_recipient_pc` and `build_confrontation_payload` live in `sidequest/server/dispatch/confrontation.py` (`:33`, `:99`); `GameStateView` at `projection/view.py` exposes no class/spell context (firewall genuinely cannot compute class-legal beats — the spec's reason to keep beat logic in the encounter layer holds).
- All three named test files exist and must be **rewritten, not reverted**: `tests/server/test_confrontation_per_pc_projection.py`, `..._call_site_audit.py`, `..._mp_broadcast.py`.

## Business Context

Solo Fighter is offered other classes' confrontation beats — Backstab, Cast Cantrip, Cast Spell, Turn Undead, Pray for Aid — that the Fighter can never use. This is the SOUL "Illusionism" failure made tactile: the UI presents mechanical choices the engine will reject, breaking the contract that the Confrontation tab shows *your* legal moves. It is correct on first load (the connect/resume path filters cleanly) but reverts to the full union after a flee or a client reconnect, exactly when a player is mid-fight and least able to absorb a regression.

The bug matters most to **Sebastien and Jade** (mechanics-first): the beat list *is* the mechanical surface they read to plan a turn. A wrong button is a lie about what the system will let them do. For **Keith-as-player**, a Fighter offered Turn Undead is precisely the "the DM doesn't know the rules" tell that breaks immersion. The root cause is architectural debt from Story 49-7, which bolted a per-PC filtered overlay *on top of* an unfiltered union broadcast and relied on last-message-wins ordering — a race that loses after flee/reconnect. The fix collapses two racing delivery paths into one filtered fan-out, making the displayed beats provably class-legal on every emit.

## Technical Guardrails

**Locked design (Keith, 2026-05-26): ONE CONFRONTATION delivery path.**

- **Beat/class logic stays in the encounter layer** (`dispatch/confrontation.py`), NOT the firewall. `GameStateView` has no class/spell context, so the ADR-105 projection firewall cannot compute class-legal beats — do not try to move filtering there.
- **Canonical full-union payload → EventLog ONLY** (replay/audit). It is **never** sent to a client socket. Today `build_confrontation_payload(recipient_pc=None)` builds the union and it goes both to EventLog *and* to client sockets — sever the client half.
- **Exactly one client fan-out** for CONFRONTATION: per-recipient class-filtered, delivered to **every connected socket including the emitter** (this kills the solo bypass where the player IS the emitter and always got the union).
- **Delete both overlay loops** — `websocket_session_handler.py:1630-1685` and `dispatch/dice.py:665-692` — plus the `room_broadcast(union)` / `_emit_event(union)` client delivery they were patching over.

**Implementation shape (per spec §Implementation):**

1. **Extend `emit_event`** (`emitters.py:235`) with an optional `per_recipient_payload: Callable[[str], BaseModel] | None = None`. When supplied:
   - Persist the canonical `payload_model` (union) to EventLog as today.
   - For **every** connected player *including the emitter*, deliver `per_recipient_payload(pid)` instead of the projected-canonical / raw-bypass frame. This **overrides Invariant 3 for this emit only** — when a supplier is given the emitter is no longer raw-bypassed. `out_to_self` (`:534`/`:552`) becomes the emitter's filtered frame.
2. **Start path** (`wssh:1607-1685`): call `_emit_event` / `emit_event` with a supplier that does `resolve_recipient_pc(...)` + `build_confrontation_payload(recipient_pc=...)`. Delete the overlay loop (1630-1685) and the `recipient_pc=None` canonical-to-client assumption.
3. **Dice mid-turn** (`dice.py:619-692`): same supplier; drop `room_broadcast(union)` + the overlay; deliver filtered per recipient.
4. **Connect/resume** (`connect.py:1515-1568`): already filtered via a single `resolve_recipient_pc` + `build_confrontation_payload(recipient_pc=...)` call — confirm it uses the same supplier shape and dedupe with the new helper.
5. **Fail LOUD on unresolvable seated PC:** if `resolve_recipient_pc` returns `None` for a seated, connected PC, fail loud (ERROR span), do NOT send the union. **NOTE:** `resolve_recipient_pc`'s current docstring (`confrontation.py:43-48`) explicitly licenses a "fall back to unfiltered payload + warn" contract for `None`. That contract must be **narrowed**: a lobby/unseated socket legitimately has no PC (`player_seats.get` miss → no beats, fine), but a *seated, connected* PC that won't resolve is a bug and must surface, never silently get the union. Update that docstring.

**OTEL (CLAUDE.md lie-detector principle):** `build_confrontation_payload(recipient_pc=...)` already fires `confrontation_beat_filter_span(source='ui_panel_projection')` per recipient (`confrontation.py:152-179`). Keep it firing on the single path. **Add a delivered-to vs connected recipient count** so the GM panel can catch a future skip.

**Anti-patterns to avoid (CLAUDE.md):**
- **No source-text wiring tests.** `test_confrontation_per_pc_call_site_audit.py` may currently grep handler source for the overlay literal — when rewriting, replace any `read_text()`/regex-on-source assertion with an OTEL-span or fixture-driven behavior test. Do not assert "the supplier literal appears N times."
- **No silent union fallback** anywhere — that is the exact debt being removed.

## Scope Boundaries

**In scope:**
- `emit_event` gains the `per_recipient_payload` supplier override (`emitters.py`).
- Single filtered fan-out wired at start (`wssh`), mid-turn/flee (`dice.py`), and confirmed at resume (`connect.py`).
- Both overlay loops + the union-to-client delivery deleted.
- Fail-LOUD ERROR span for an unresolvable seated+connected PC; `resolve_recipient_pc` docstring narrowed.
- Recipient delivered-vs-connected count added to the existing filter span.
- Rewrite `test_confrontation_per_pc_projection.py`, `..._call_site_audit.py`, `..._mp_broadcast.py` to the single-path shape; new red-first regression + wiring test.

**Out of scope:**
- Moving beat/class logic into the projection firewall or extending `GameStateView` with class context (explicitly rejected — beat logic stays in the encounter layer).
- ADR-105 Track B content redaction of the shared blob (separate concern).
- The merged-MP `author_player_id` Track-A path semantics for *non*-CONFRONTATION emits — leave the existing `project_emitter` behavior intact for other kinds.
- `beat_filter.py` filter semantics — the single source of truth for which beats are class-legal stays unchanged; this is a delivery-wiring change.
- The `Sebastien's lie-detector` mislabel on the backend span comment at `dice.py:622` (CLAUDE.md flags name-on-dev-observability, but it is not this story's surface — don't gold-plate).
- Adjacent firewall surface 59-9 (separate story).

## AC Context

**AC1 — Single filtered fan-out to ALL sockets incl. emitter.**
On a live CONFRONTATION emit (start path), every connected socket — *including the emitter's own* — receives a per-recipient class-filtered frame built via `build_confrontation_payload(recipient_pc=...)`. Verify the emitter is no longer raw-bypassed: with the supplier supplied, `out_to_self` (`emitters.py:534`) is the filtered frame, not the union. Drive through the real handler; assert one `confrontation_beat_filter_span(source='ui_panel_projection')` fires per connected recipient including the emitter.

**AC2 — Canonical union → EventLog only, never a client socket.**
After an emit, assert the EventLog still holds the canonical full-union CONFRONTATION row (replay/audit parity preserved), AND that no client socket — emitter or peer — ever received the union payload. Behavioral assertion on delivered frames, not source grep.

**AC3 — Both overlay loops deleted.**
The `websocket_session_handler.py:1630-1685` overlay loop and the `dispatch/dice.py:665-692` per-PC overlay loop (plus the union `room_broadcast`/`_emit_event`-to-client delivery they followed) are gone. Verify via behavior — a single delivery per recipient, no double-frame race — using OTEL recipient counts / delivered-frame assertions, NOT a source-text audit. The rewritten `..._call_site_audit.py` must assert behavior, not literals.

**AC4 — Fail LOUD on unresolvable seated+connected PC.**
A seated, connected PC for whom `resolve_recipient_pc` returns `None` triggers an ERROR span and no delivery to that socket — the union is NOT sent as a fallback. Distinguish from a lobby/unseated socket (no `player_seats` entry), which legitimately gets no beats and no error. Add a fixture with a seated PC whose class won't resolve; assert the ERROR span fires and no union frame goes out.

**AC5 — Solo Fighter sees only Fighter beats (the regression repro).**
Red-first, fixture-driven: synthetic caverns_and_claudes pack + solo Fighter snapshot + a real CONFRONTATION emit through the handler. Assert the **emitter's own delivered frame** contains no `backstab` / `cast_spell` / `cast_cantrip` / `turn_undead` / `pray_for_aid` beat ids. Then exercise the flee/mid-turn path (`dice.py`) and a reconnect (`connect.py`) and assert the same — the bug reproduces today only after flee/reconnect, so all three emits must be covered. Wiring test: assert the supplier is invoked for the emitter (the path that was bypassed).

## Assumptions

- The full server suite is gated with content + `SIDEQUEST_DATABASE_URL` set (per MEMORY: a "~33 MissingDatabaseUrlError" first pass is the env tell, not a regression; `tests/genre/` calibration SKIPs without `SIDEQUEST_GENRE_PACKS`). Record the baseline failure list before claiming green.
- `build_confrontation_payload(recipient_pc=...)` and `resolve_recipient_pc` are stable entrypoints reused as-is; this story only changes *who calls them and how the result is delivered*, not their filter semantics.
- The UI's last-message-wins rendering is the reason the race manifests; collapsing to one delivery removes the dependency on arrival order — no UI change is required for the fix, though the UI now receives exactly one CONFRONTATION per recipient per emit.
- caverns_and_claudes (multi-class, Fighter present) is the right fixture pack; it is a live, loadable pack.
