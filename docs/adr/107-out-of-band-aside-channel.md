---
id: 107
title: "Out-of-Band Aside Channel — Non-Turn-Consuming Player→GM Table-Talk"
status: accepted
date: 2026-05-18
deciders: ["Keith Avery", "GM agent (brainstorm)", "Architect (planning mode)"]
supersedes: []
superseded-by: null
related: [36, 63, 82, 101, 104, 105]
tags: [frontend-protocol, multiplayer, agent-system]
implementation-status: live
implementation-pointer: docs/superpowers/specs/2026-05-17-aside-channel-design.md
---

# ADR-107: Out-of-Band Aside Channel — Non-Turn-Consuming Player→GM Table-Talk

## Status

Accepted. Design detail lives in
`docs/superpowers/specs/2026-05-17-aside-channel-design.md`; the per-task
decomposition is `docs/superpowers/plans/2026-05-17-aside-channel.md`. This ADR
is the durable decision record and scope boundary — it locks the contested
calls and the seams, it does not restate the spec.

## Context

The `aside` feature was half-wired. The inbound leg existed end-to-end — the
`InputBar` "(…)" toggle, `aside: bool` on `PLAYER_ACTION`
(`protocol/messages.py`), the peer mirror via `ActionRevealPayload.aside`, the
distinct `player-aside` segment in `narrativeSegments.ts`, and combat-bracket
stripping in `handlers/player_action.py` — but **no server branch on `aside`
existed**. Asides therefore flowed through the ADR-036 submit-and-wait barrier
and the full narrator path identically to in-fiction actions, consuming a turn
and advancing world state.

Four pressures forced this decision:

1. **Playtest finding F6.** During the 2026-05-17 Beneath Sünden 5-player MP
   session, players repeatedly used the in-fiction action box to ask the GM
   clarifying questions — Hiken (R7): *"I am very short and don't know how to
   swim. Will I be able to wade in the water or will I need to be carried?"* —
   and every such question burned a turn and was fully narrated. This is an
   inclusion failure: it directly penalizes Alex (slower typist, freezes under
   time pressure), for whom a clarifying question must not carry turn or clock
   cost.
2. **Port drift (ADR-082 / ADR-063).** ADR-063 references a Rust
   `handle_aside()` / `aside.rs` first-class aside narration path; the ADR-082
   Rust→Python port collapsed it to a 10-line bracket strip. The behavior was
   lost in the port, not by an explicit decision — this ADR records the
   decision the port elided.
3. **The `api-contract.md` lie.** The contract simultaneously claimed
   `aside: true` = "(not narrated)" *and* "broadcast identically to
   in-character text" — two contradictory statements, both false against the
   shipped behavior. A doc that lies is worse than a doc that is silent.
4. **The lie-detector mandate (CLAUDE.md OTEL Observability Principle).** An
   OOC GM ruling with zero mechanical backing is exactly the "Claude winging
   it" failure mode the GM panel exists to catch. An aside channel with no
   span is a new blind spot, and Sebastien's mechanics-first lane treats GM-
   panel visibility as a feature, not debug scaffolding.

This is a **"wire up what exists, don't reinvent" repair plus a doc-lie
correction — not a new feature.** The inbound leg is reused unchanged; only the
outbound leg and the handler branch are new.

## Decision

Adopt **Approach A**: finish the existing `aside: bool` flag rather than
introduce a parallel input path.

1. **Branch before the barrier.** `handlers/player_action.py` branches on
   `payload.aside` at the earliest server seam — *before* the ADR-036
   submit-and-wait barrier and *before* any narration dispatch. An aside is
   never written into `SessionRoom.pending_actions`, never increments the
   "everyone submitted" count, never takes `dispatch_lock`. It is
   concurrency-safe **by exclusion, not by locking**: an aside shares no
   mutable turn state, so an aside arriving mid-round — even while another
   player's turn is dispatching — cannot collide.

2. **The asker still owes a turn.** Sending an aside does nothing to the
   asker's pending-action slot. The barrier still waits for their real action
   if unsubmitted; it still stands if submitted. The aside is genuinely
   orthogonal — this orthogonality is what makes it free for Alex.

3. **Read-only resolver.** A new `AsideResolver` receives a *read* view
   (asker's character, current region/perception projection, inventory, genre
   rulebook surface, recent narration window) and returns text. It holds **no
   write path** — it structurally cannot advance the world, mutate inventory,
   tick tropes, or touch the dungeon. "No turn consumed" is enforced by the
   resolver having no hands, not by remembering not to use them.

4. **GM-craft answer policy.** The resolver answers capability/perception,
   rules/genre, and recap questions in 1–3 plain second-person GM sentences,
   out-of-character. It **refuses** hidden world state ("is the door
   trapped?") with *"You'd have to check — that's an action, not a
   question."* and refuses anything that would move the fiction, pointing back
   to the action box. Diamonds-and-Coal spoiler protection holds inside the
   aside channel exactly as in narration. The answer must be grounded in the
   state the resolver was given; if the inputs do not contain the answer it
   declines honestly rather than improvising (No Silent Fallbacks).

5. **New typed outbound message.** A dedicated `MessageType.ASIDE_ANSWER`
   (sibling of `NARRATION`, not a reuse of it) is broadcast to the whole room
   — `{ asker_id, question, answer, grounded_on[], round }`. Reusing
   `NARRATION` would make an OOC ruling indistinguishable from in-fiction
   prose in scrollback, scrapbook, and the GM panel — the exact conflation
   this ADR kills. `round` is carried for client ordering only; it is **never
   a turn record**. No `narrative_log` row, no `scrapbook_entries` row, no
   `session_meta` turn/round advance.

6. **Table-visible.** Both question and answer are broadcast to every seat,
   styled as OOC table-talk, consistent with ADR-036's 2026-05-03
   collaborative-visibility amendment (no slipped notes; sealed visibility is
   PvP-only and unimplemented). Table-visibility rides the existing room
   broadcast — it is not a per-recipient perception decision, so ADR-104 /
   ADR-105 are untouched.

7. **Routed `aside.resolve` OTEL span.** Every aside emits a routed (not
   flat-only) `aside.resolve` span carrying `asker_id`, `outcome`,
   `grounded_on`, `model`, `latency_ms`. Routed because an ungrounded aside is
   exactly the narrator-lie the GM panel must catch — a present span with
   empty `grounded_on` on a factual answer is a visible, auditable
   ungrounded-aside finding.

8. **Cost scales with drama (ADR-101 routing).** An aside is the lowest-drama
   input in the system; it routes to the cheap/fast model tier (Haiku) via
   ADR-101 per-call routing, which also keeps the answer near-instant — the
   point of an out-of-band channel. Asides are not routed through the full
   narrator/orchestrator.

## Consequences

- **A new out-of-band input class amends the ADR-036 barrier contract.** The
  barrier's invariant "every connected player must submit before narration"
  now explicitly excludes `aside: true` inputs. This is an amendment by
  cross-reference, **not a supersession** — ADR-036's turn model is otherwise
  unchanged, so ADR-107 does not carry `supersedes: [36]`.
- **The `api-contract.md` lie is corrected** to the true contract (`aside` →
  OOC GM answer, no turn, no world advance, `ASIDE_ANSWER` outbound,
  table-visible). A doc-contract guard test
  (`tests/protocol/test_api_contract_aside.py`) keeps the old contradictory
  claims from regressing.
- **GM-panel-auditable by construction.** The routed `aside.resolve` span
  closes the lie-detector gap: the channel cannot engage silently, and an
  ungrounded answer is visible to Sebastien's panel exactly like an ungrounded
  narration.
- **The `aside` flag's historical "styled but narrated" meaning is retired.**
  Any reader or tool that assumed an aside is a narrated turn must update;
  forensic timelines (e.g. the R3-stall analysis) stay clean because asides
  never pollute the narration log.
- **Tabletop First (SOUL).** This restores DM-table behavior the digital
  medium had regressed: at a real table a player can ask "wait, can I even
  wade here?" without it being their turn. The software now matches the
  baseline instead of penalizing the question.
- **The Zork Problem (SOUL).** Keeping clarifying questions in natural
  language — rather than forcing them through the action box or a menu —
  preserves the open-input ceiling. The aside channel is itself an
  application of "never let the interface imply a closed set of options."
- **Surface area is small and bounded.** Inbound leg unchanged; one new
  message type, one read-only resolver, one handler branch, one span. No new
  panel/modal, no persistence schema change.

## Alternatives

- **B — New dedicated inbound message type (`PLAYER_ASIDE`).** Rejected: the
  inbound `aside: bool` leg is already fully wired through the UI toggle,
  payload, and peer mirror. A second inbound type would duplicate that
  plumbing and create a second code path for "player typed something,"
  contradicting "wire up what exists, don't reinvent." The conflation problem
  is on the *outbound* leg, which is where the new typed message (`Decision`
  §5) is introduced.
- **C — Client-side REST side-channel for GM questions.** Rejected: it
  fragments the transport (ADR-038 establishes WebSocket as the real-time game
  channel), it cannot ride the existing room broadcast for table-visibility,
  and it would bypass the OTEL span path, reintroducing the blind spot the
  lie-detector mandate forbids.
- **Reuse `NARRATION` for the answer.** Rejected: an OOC ruling rendered
  through the narration path is indistinguishable from in-fiction prose in
  scrollback, scrapbook, and the GM panel — the precise conflation F6 exposed.
  A distinct `ASIDE_ANSWER` type is the minimum that keeps the turn record and
  the forensic timeline honest.
- **Private / sealed-visibility asides.** Out of scope: ADR-036 reserves
  sealed visibility for an unimplemented PvP paradigm; the co-op playgroup
  doesn't slip notes to the DM (ADR-036 2026-05-09 doctrine clarification).
