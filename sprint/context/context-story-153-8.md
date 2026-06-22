# Story 153-8 Context

## Title
[DAEMON-NO-RECONNECT] server daemon-client reconnect/back-off loop (ADR-131)

## Metadata
- **Story ID:** 153-8
- **Type:** bug
- **Points:** 3
- **Priority:** p3
- **Workflow:** tdd
- **Repo:** server
- **Epic:** 153 — Playtest follow-ups (open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)

## Problem Statement

When the daemon starts **after** the server, the server's daemon client establishes an
`unavailable` state at startup and never recovers — it does not probe, retry, or reconnect
once the daemon is healthy. As a result:

- `_maybe_dispatch_render` cannot dispatch image renders.
- RAG embed/retrieve (`lore_embedding`, `entity_embedding`) queues silently accumulate and
  never drain (counts climb past 20–46 pending items).
- The degradation persists **until the server is manually restarted with the daemon already up**.

This is a No-Silent-Fallbacks violation: the client no-ops renders + RAG on every turn
without surfacing a "daemon down — renders disabled" signal, and never self-heals.

The ADR-131 liveness heartbeat channel **does** reconnect (the daemon log shows
`Client connected: unix-client` every 15 s), confirming the Unix socket is reachable after
the daemon starts — but the embed/render worker client stays in the initial failed state,
never consulting the heartbeat to flip its availability flag.

## Repro / Evidence

**Session:** `2026-06-20-gulliver-e3c4e658` (150-7 playtest; DRIVER Hephaestus).

**Steps:**
1. Start the server while the daemon is **down**.
2. Start the daemon later (`just daemon`) — it warms successfully:
   `Daemon listening on /tmp/sidequest-renderer.sock pid 14514`, image/embed workers warm,
   `just daemon-status` returns `heartbeat state=ready`.
3. Observe server logs — **15+ lines after daemon came up:**
   ```
   WARNING lore_embedding.worker skipped reason=daemon_unavailable pending=20 socket=/tmp/sidequest-renderer.sock
   WARNING entity_embedding.worker skipped reason=daemon_unavailable pending=46
   WARNING lore_embedding.retrieve skipped reason=daemon_unavailable
   ```
4. Queues never drain; no image renders fire; RAG retrieval is degraded for the remainder of
   the session.

**Workaround used:** restart the server with the daemon already running.

**Impact on 150-7:** blocked RENDER-NO-SUBJECT end-to-end verification (narrator emits
`visual_scene` ✅ but no image can compose) and degraded narration RAG for the full session.

## Fix Direction

Add a **reconnect/back-off loop** to the server's daemon client so it re-establishes the
Unix-socket connection when the daemon comes up, without a server restart.

Natural trigger: the ADR-131 liveness heartbeat already connects successfully after the
daemon starts. The embed/render worker client should consult that heartbeat (or perform its
own probing on back-off) to flip its internal availability flag from `unavailable` →
`available` once the socket is reachable.

The liveness heartbeat channel (ADR-131) is the designed out-of-band contract between daemon
and server — the reconnect logic belongs on the server-side daemon client, not in the daemon.

References: **ADR-131** (daemon↔server out-of-band contracts — liveness heartbeat, OTEL HTTP
bridge, output-dir handshake); **ADR-035** (Unix socket IPC for Python sidecar).

## Acceptance Criteria

1. **Renders recover without server restart.** When the daemon starts after the server (in
   any order), `_maybe_dispatch_render` resumes dispatching renders automatically once the
   daemon is healthy — no manual server restart required.

2. **RAG embed/retrieve recover without server restart.** `lore_embedding` and
   `entity_embedding` queues drain and retrieve calls succeed once the daemon is reachable;
   the `daemon_unavailable` skip log ceases within one back-off cycle of the daemon coming up.

3. **Back-off loop is bounded.** The reconnect loop uses a capped exponential (or similar)
   back-off — it does not spin tightly nor block the server's hot path.

4. **Observability: reconnect is logged.** When the daemon-client transitions from
   `unavailable` → `available` (reconnect succeeds), a log line and/or watcher event is
   emitted so the GM panel / server log confirms the recovery (not a silent flip).

5. **Wiring / integration AC.** A test exercises the reconnect path end-to-end: simulate the
   daemon socket being absent at client init, then become available; assert the client
   transitions to `available` and that `_maybe_dispatch_render` / embed-worker calls succeed
   after reconnect — without restarting the client object. This must drive the production
   reconnect code path, not mock the availability flag directly.

## Source

- Board capture lines 562–575 (`DAEMON-NO-RECONNECT` finding, session
  `2026-06-20-gulliver-e3c4e658`).
- ADR-131 (daemon↔server out-of-band contracts — liveness heartbeat is the natural reconnect
  trigger).
- ADR-035 (Unix socket IPC for Python sidecar).

## Scope Notes

In scope:
- Reconnect/back-off loop on the server's daemon client (embed/render worker client).
- Flipping the `daemon_unavailable` flag back to available when the heartbeat / probe
  confirms the socket is reachable.
- Log/watcher event on successful reconnect (observability AC).
- Integration test driving the reconnect path through the production client code.

Out of scope:
- Changes to the daemon itself — the daemon already behaves correctly.
- The ADR-131 liveness heartbeat channel (it already reconnects; this story is about the
  embed/render client catching up to that).
- Any UI/GM-panel banner for "daemon down" state (a possible future hardening; not required
  for this AC set).
