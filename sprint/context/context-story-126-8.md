# Story 126-8 Context

## Title
[FATE] Player defense 4dF is determinative (physics-is-the-roll) — the DEFEND barrier (ADR-148/149)

## Metadata
- **Story ID:** 126-8
- **Type:** story
- **Points:** 5
- **Priority:** p3
- **Workflow:** tdd
- **Repos:** server, ui
- **Epic:** Fate Core playtest follow-ups — annees_folles eval (2026-06-16/17)

## Problem

The DEFEND half of ADR-148, deliberately deferred from 126-7. Story 126-7 made the player's PROACTIVE Fate 4dF determinative (FATE_THROW: settled tray faces ARE the roll, server resolves from reported faces). **126-8 brings the player's DEFENSE roll into the same physics-is-the-roll model.**

Today `_roll_defense` / `_seat_opponent_commits` in `sidequest/server/dispatch/fate_conflict.py` still roll the defending player's 4dF SERVER-SIDE with the tray as decoration. When a SEATED Fate PC defends against an attack, the player should physically throw the 4dF and the settled faces resolve the defense (no `roll_4df` on the player defense path). 

**Key constraint:** the sealed-commit turn model (ADR-036 / ADR-129). Every player's proactive action and defense happens concurrently + privately on their client, then the table's collective intents commit simultaneously behind a barrier. This story **does NOT abandon the sealed barrier** — instead, it makes the defender's throw an *interactive but asynchronous* moment within the barrier: the attack targets them, they see the committed attack total, they throw and submit, and the server continues only when all defenses are in. The server walks the entire woven exchange once and narrates it once — one round, one cinematic beat.

Per ADR-148 line 146 this is **"Story 126-8 / ADR-149"** — the no-`roll_4df`-on-the-player-path invariant extends from proactive to defense. SOUL: bind the ruleset (Fate ladder math unchanged).

## Technical Approach — Approved Architecture

The design is COMPLETE and APPROVED (Architect review, 2026-06-18):
- **Complete sealed-commit interaction model:** `docs/superpowers/specs/2026-06-18-fate-sealed-commit-interaction-model-design.md`
- **Server implementation plan:** `docs/superpowers/plans/2026-06-18-fate-sealed-commit-defend-server.md`

### Round structure (the sealed-commit envelope)

```
 1. COMMIT     Sealed barrier (unchanged from today).
   (barrier)   Each seated PC, CONCURRENTLY + PRIVATELY:
                 • throws the proactive die (attack/overcome/etc.)
                 • LOCAL ADJUST LOOP — invoke (+2) / reroll, spending own FP/aspects
                 • submits the FINAL result
               Closes when all PCs submit.

 2. REVEAL     Server, instant.
   (server)    Seat + lock NPC attacks NOW (their 4dF rolled here, never re-rolled across suspend).
               Build the attack graph.

 3. DEFEND     Second barrier — CONDITIONAL (only if a PC is targeted).
   (barrier)   Per incoming attack, the PC:
                 • sees the committed ATTACK TOTAL (fully informed)
                 • free-picks a defense skill (justified in fiction — the Zork Problem)
                 • LOCAL ADJUST LOOP — now fully informed, invoke/reroll their FP/aspects
                 • submits the FINAL defense — OR CONCEDE here
               Closes when all PC defenses/concessions are in.

 4. RESOLVE    Server, instant.
   (server)    Every roll in hand. Walk once: compare proactive vs defense, shifts, 
               absorb stress/consequences, place created aspects. Emits OTEL (lie detector).

 5. NARRATE    ONE narrator call (floor).
   (narrator)  Renders the ENTIRE woven exchange as ONE cinematic beat. Sets up next round.
```

### The keystone insight — latency lives in the narrator, not the wire

WebSocket round-trip: milliseconds. LLM narrator call: seconds. Therefore: **spend client↔server chatter like water; hoard narrator calls like gold.**

The sealed barrier is a **batching engine**: collect the whole table's intents and final rolls, resolve every mechanic server-side, and **only then** invoke the narrator once to render the entire woven exchange as a single cinematic beat. **The narrator is NEVER in the mechanical loop.**

### Key decisions

1. **Contested asymmetry — informed defender, committed attacker:** The attacker commits first (blind to the defense). The defender reacts second and sees the incoming attack total. This is faithful to the feel (you strike; they see the blow and react) and gives it for free from the medium.
2. **Narrator cadence — one call at RESOLVE, drama-scaled:** Exactly one narrator call per round, rendering the whole woven exchange. A genuine spike may earn one extra beat (deferred).
3. **The local adjust loop is client-owned:** A reroll means the client throws again and submits the new faces; the server resolves once and validates the spend on submit (reject loud if unaffordable). The narrator sees no intermediate dice.
4. **Bind the ruleset, don't balance it:** No changes to `classify_outcome`, shifts, tiers, or ladder math. This changes the dice *source* and *interaction choreography* only.

### Implementation strategy

**Server-side only in this slice.** The UI surfaces (COMMIT tray, DEFEND prompt, informed banner, free-pick skill selector, aspect shelf, concede control, peer visibility) are a separate follow-up story.

**State machine at DEFEND:** The exchange suspends at a persisted `pending_defenses` ledger checkpoint (resume-safe, ADR-128):
- After REVEAL: if a PC is targeted, write the ledger, emit `FATE_DEFEND_REQUEST`, persist, and **park** (no walk yet).
- Each `FATE_THROW(action="defend")` records the defender's result by `request_id`.
- When ledger full: resume, walk the exchange with recorded PC defenses, narrate once.

**NPC rolls stay server-side:** `_roll_defense` and `_seat_opponent_commits` for opponent actors stay unchanged.

## Scope

- **In scope (server-side):** COMMIT→REVEAL→DEFEND→RESOLVE→NARRATE restructure; `pending_defenses` ledger + suspend/resume checkpoint; `FATE_DEFEND_REQUEST` message + `action="defend"` on `FATE_THROW`; player defense via `resolve_action_from_faces` (NEVER `roll_4df` on player path); concede-at-defend; informed defender sees attack total; free-pick defense skill; `role="defense"` OTEL span + new `fate.defend_phase` span; block-and-wait AFK.

- **Out of scope (deferred to follow-up):** DEFEND prompt UI, informed banner, free-pick skill selector, aspect shelf (tap-to-spend chips), concede control, peer visibility board (Guitar Solo non-targeted-player view); active-help cross-player aid-invokes; DEFEND timeout / auto-resolve.

## Acceptance Criteria

_TEA finalizes/expands during RED. Complete set from the approved spec + server plan:_

✅ **Design approved** — two documents are written and approved by the Architect:
- [ ] Spec: `docs/superpowers/specs/2026-06-18-fate-sealed-commit-interaction-model-design.md` (complete sealed-commit model, §1–13)
- [ ] Server plan: `docs/superpowers/plans/2026-06-18-fate-sealed-commit-defend-server.md` (8 tasks: protocol, ledger, OTEL, reveal+park, emit requests, defense recording, resume+walk, end-to-end wiring)

✅ **Protocol layer:**
- [ ] New `FATE_DEFEND_REQUEST` message type (server→client) in the `GameMessage` union, carrying `request_id`, `defender`, `attacker`, `attack_skill`, `attack_total`, `mental`.
- [ ] Extended `FATE_THROW` with `action="defend"` (widened from `["overcome", "create_advantage", "attack"]`); defend throws echo the `request_id` of the request they answer.
- [ ] Wire validation: `FateThrowPayload` accepts `action="defend"` + echoes `request_id`; rejects ≠4 faces, faces ∉ {−1,0,1}, extra fields. `FateDefendRequestPayload` validates.

✅ **Resume-safe state machine:**
- [ ] `FatePendingDefense` model (request_id, attacker, defender, attack_skill, attack_total, defense_total | None, conceded).
- [ ] `pending_defenses: list[FatePendingDefense]` field on `StructuredEncounter`, sibling to `fate_commits`.
- [ ] Ledger survives a snapshot round-trip (JSON serialization).
- [ ] Legacy encounters without the field load as empty (upgrade-safe).

✅ **Deterministic player defense:**
- [ ] Player defense resolves from REPORTED FACES via `resolve_action_from_faces` — **no `roll_4df` on the player path** (spy assertion in test).
- [ ] NPC defense stays server-rolled (`roll_4df`).
- [ ] Faces → expected ladder_total/shifts (determinism test with known faces).

✅ **Informed defender:**
- [ ] Server hands the defender the committed `attack_total` in `FATE_DEFEND_REQUEST` before they throw.
- [ ] Defender free-picks a defense skill (any skill on the sheet, justified in fiction — the Zork Problem).

✅ **REVEAL + park decision:**
- [ ] When the COMMIT barrier closes: run REVEAL (seat + lock NPC attacks, their 4dF rolled NOW).
- [ ] If any PC is targeted by an attack: write `pending_defenses` (one entry per incoming attack), emit one `FATE_DEFEND_REQUEST` per entry, **persist the checkpoint, and park** (return `FateDispatchResult(awaiting_defense=True, defend_requests=...)` WITHOUT walking the exchange).
- [ ] If no PC targeted: resolve immediately (today's single-call path, unchanged).

✅ **Broadcast defend requests:**
- [ ] When the round parks, emit one `FATE_DEFEND_REQUEST` message per entry (routed to the defender's seat or broadcast to the room).
- [ ] Persist the parked checkpoint (snapshot with pending_defenses filled).
- [ ] No narration is triggered by the park.

✅ **Defense recording:**
- [ ] Each `FATE_THROW(action="defend")` is routed to a defense handler.
- [ ] Looks up the unfilled `pending_defenses` entry by `request_id` (fail loud with `FateConflictError` if missing or already-filled).
- [ ] Resolves the defender's ladder total from the reported `thrown_faces` with their chosen `skill` at `Opposition(value=0, kind="active")` using `resolve_action_from_faces` (NEVER `roll_4df`).
- [ ] Records `defense_total` on the matched entry (or `conceded=True` for a fold).
- [ ] Emits `fate.action_resolved(role="defense", source="player_thrown")` OTEL span + `fate.defend_phase(responded=True)` span.
- [ ] Reports `ledger_full: bool` — True when every pending_defenses entry is now filled.

✅ **Concede at defend:**
- [ ] A concession in the DEFEND barrier marks the entry `conceded=True` and counts as filling it (ledger_full logic).
- [ ] No throw is needed (the faces are omitted from the concession message).

✅ **Resume and walk:**
- [ ] When the ledger fills: resume the parked exchange.
- [ ] Run the existing exchange walker (`run_fate_exchange` / `_resolve_attack`), but the `_resolve_attack` step reads the *recorded* PC defense_total from the ledger instead of calling `_roll_defense`.
- [ ] NPC defenses still call `roll_4df` inline.
- [ ] Emit `fate.defend_phase` OTEL spans for the ledger state (who responded, concede flags).
- [ ] After resolution, invoke the narrator **once** to render the entire woven exchange.

✅ **OTEL (lie detector):**
- [ ] `fate.action_resolved` gains `role ∈ {action, defense}` (keeping `source ∈ {player_thrown, server_rolled}`).
- [ ] New `fate.defend_phase` span: `defender`, `attacker`, `request_id`, `responded` (False at request time, True when defense lands), `conceded` flag.
- [ ] GM panel can confirm a player defense came from the client and an NPC defense came from the server RNG.

✅ **Block-and-wait AFK:**
- [ ] The DEFEND barrier waits indefinitely on an absent defender; no timeout, no server-side auto-roll.
- [ ] (Timeout/auto-resolve is a future deliberate feature, not baked in now.)

✅ **Wiring (mandatory, end-to-end):**
- [ ] NPC-attacks-PC → REVEAL → park → `FATE_DEFEND_REQUEST` broadcast → player `FATE_THROW(defend)` → record → ledger full → RESUME → walk exchange → narrate, all through the real handler/registry/exchange on a fixture snapshot (not a unit stub).
- [ ] Confirm the NPC path still server-rolls (spy on `roll_4df` for NPC defenses).
- [ ] No source-text wiring tests (never grep production code); use span capture (injected `_tracer`) and behavioral fixtures driving real handlers.

## Implementation Plan (from approved server plan)

**8 tasks** (570 LOC production, ~500 LOC test):

1. **Protocol** — `FATE_DEFEND_REQUEST` message + `action="defend"` on `FATE_THROW` (~50 LOC, 1 test file)
2. **Ledger model** — `FatePendingDefense` + `pending_defenses` field on `StructuredEncounter` (~40 LOC, 1 test)
3. **OTEL** — `role` on `fate_action_resolved_span` + new `fate_defend_phase_span` (~70 LOC, 1 test file)
4. **REVEAL + park** — `_build_pending_defenses`, restructure barrier-close branch (~120 LOC, 1 test file)
5. **Emit requests** — broadcast `FATE_DEFEND_REQUEST` from handler, persist checkpoint (~50 LOC, 1 test)
6. **Defense recording** — `dispatch_fate_defense`, route defend action in handler (~100 LOC, 1 test file)
7. **Resume + walk** — when ledger full, run existing walker but read recorded defenses (~80 LOC, 1 test file)
8. **End-to-end wiring** — NPC-attacks-PC → park → defend → resume → narrate through real handler/registry (~60 LOC, 1 comprehensive test)

## Dependencies

- **126-7 (done):** Player proactive 4dF determinism. Infrastructure (`resolve_action_from_faces`, `throw_params`, dF `DieKind`, `FateThrowPayload`) is live; reuse and extend.
- **ADR-148 (live):** Player Fate rolls are physics-is-the-roll. This extends it to defense.
- **ADR-036 / ADR-129 (live):** Sealed-commit turn model (the barrier is non-negotiable).
- **ADR-128 (live):** Resume-safe randomness (resume-safety precedent for state machines like this).
- **ADR-144 (live):** Fate Core binding (the ruleset math this never touches).

## Non-Goals

- Abandoning the sealed-commit barrier (it is the special sauce, the advantage over tabletop).
- Post-defense push window for attacker (contested asymmetry accepted as-is).
- Cross-player aid-invokes during DEFEND in this slice (deferred).
- DEFEND timeout / auto-resolve (deferred).
- Any changes to Fate resolution math (bind, don't balance).

---

_Enriched from `pf context create story 126-8` with details from the approved spec and server plan (2026-06-18)._
