# Story 126-29 Context

## Story Information
- **ID:** 126-29
- **Type:** bug
- **Points:** 3
- **Priority:** p2
- **Workflow:** tdd
- **Repositories:** server, ui

## Title
[BUG] Gate Fate proactive tiles on committed-this-exchange so a resumed mid-exchange conflict doesn't offer actions the server rejects (#403).

## Description
Gate Fate proactive tiles on committed-this-exchange so a resumed mid-exchange conflict doesn't offer actions the server rejects. Add a per-PC `committed` bool to the FATE_STATE.conflict participant, sourced from `encounter.fate_commits`; the UI disables/replaces the proactive Overcome/Create-Advantage/Attack/Concede tiles with the existing fate-sealed-hint when set.

Do NOT relax the server `dispatch_fate_throw` sealed-commit guard (ADR-129/151).

## Acceptance Criteria
1. Server change: add a `committed` bool field to FATE_STATE.conflict participant model, sourced from `encounter.fate_commits` — a participant is committed if their action has been recorded in the sealed-commit ledger for this exchange.
2. Broadcast the updated FATE_STATE to all seats so the UI can read the committed status per participant.
3. UI change: when a participant's `committed` bool is true, disable the proactive action tiles (Overcome, Create Advantage, Attack, Concede) and show the existing fate-sealed-hint instead (reuse the existing styling/UI pattern).
4. Add a test that demonstrates: (a) on a fresh Fate conflict, all PCs have `committed=false`; (b) after a PC submits an action and the server records it in fate_commits, that PC's FATE_STATE.participant.committed becomes true; (c) on UI, the proactive tiles disable and fate-sealed-hint shows; (d) on server resume mid-exchange, the same PC's FATE_STATE retains committed=true.
5. Verify the server dispatch_fate_throw sealed-commit guard (ADR-129/151) is NOT relaxed — if a committed participant attempts an action, the server still rejects it loudly.
6. OTEL span to confirm committed status is set/broadcast per participant.

## Related Items
- Issue #403
- ADR-129: N-Seat Table Engine — Generalized Sealed-Commit Loop
- ADR-151: The Fate DEFEND Follow-Up Barrier
- Story 126-8 (DEFEND barrier wiring)
- Story 126-14 (defend-concession protocol)
- Story 126-17 (defend-throw UI surface)

## Scope Notes
- This is a pure gating fix — it prevents the UI from offering actions the server will reject after a resume.
- The server sealed-commit guard is the authoritative enforcement and must stay fail-loud.
- Reuse existing UI patterns (fate-sealed-hint) for consistency.
- Both server and UI work is required; repos: server,ui.

## Deliverables
- Server: FATE_STATE.conflict participant.committed field + broadcast logic
- Server: OTEL span on committed status
- Server test: committed status lifecycle (fresh, after action, post-resume)
- Server test: sealed-commit guard still rejects committed participants
- UI: proactive tile disable/replacement when committed=true
- UI test: tile visibility + fate-sealed-hint show on committed=true
