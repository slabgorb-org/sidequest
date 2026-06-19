---
id: 151
title: "The Fate DEFEND Follow-Up Barrier — A Conditional Second Sealed-Commit Phase for Physics-Is-The-Roll Player Defense, the pending_defenses Ledger, and Defender Authorization"
status: accepted
date: 2026-06-19
deciders: ["Keith Avery", "The Man in Black (Architect)"]
supersedes: []
superseded-by: null
related: [36, 74, 119, 128, 129, 144, 148]
tags: [game-systems, frontend-protocol, multiplayer, observability]
implementation-status: live
implementation-pointer: "sidequest-server sidequest/server/dispatch/fate_conflict.py (REVEAL/park/resume, dispatch_fate_defense) + sidequest/handlers/fate_throw.py (FATE_DEFEND_REQUEST broadcast, defend routing) + sidequest/game/encounter.py (FatePendingDefense ledger)"
---

# ADR-151: The Fate DEFEND Follow-Up Barrier — A Conditional Second Sealed-Commit Phase for Physics-Is-The-Roll Player Defense, the pending_defenses Ledger, and Defender Authorization

> Completes **ADR-148**. ADR-148 made a player's *proactive* Fate (4dF) roll
> physics-is-the-roll and explicitly deferred the *reactive* defense roll as "a
> separate, harder problem" (ADR-148 §6). This ADR documents the mechanism that
> closes that gap: a conditional second sealed-commit barrier (DEFEND) layered
> onto the Fate exchange so a targeted player can physically throw their own
> defense without breaking the sealed-commit turn model (ADR-036 / ADR-129).
> Per SOUL "Bind the Ruleset, Don't Balance It," nothing here touches the Fate
> ladder math — it changes *where the defender's dice come from*, never how the
> attack resolves.

## Numbering note — this is the ADR that ADR-148 reserved as "ADR-149"

ADR-148 §6 and the 2026-06-17 determinative-Fate design spec both scheduled this
defend barrier as "Story 126-8 / **ADR-149**." That number was a forward
reservation made before the ADR was written. ADR-149 was subsequently allocated
to an unrelated decision — *Ruleset-Tier SRD Reference Content and the
rules_document Reference Section* — so the reservation went stale. The DEFEND
barrier never got its own ADR; the code shipped (Stories 126-8 / 126-13 / 126-14)
carrying `ADR-148/149` citations that point, incorrectly, at the SRD content ADR.

**This ADR (151) is the real home for the DEFEND barrier.** Story 126-15 authors
this document and corrects the stale `ADR-148/149` citations to `ADR-148/151`
across the nine server files that describe DEFEND-barrier behavior (ADR-148 stays:
it owns the *roll source*; 151 owns the *barrier*). ADR-148 §6's own
forward-reference is corrected to point here.

## Context

The Fate round resolves as a **sealed-commit exchange** (ADR-036 / ADR-129):
every seat commits blind and simultaneously, the barrier closes, NPC actions are
seated, then a single exchange walk resolves everything. ADR-148 made the player's
proactive throw determinative — the settled tray faces *are* the roll, the server
resolves from the reported faces and never calls `roll_4df` on the player path.

Defense is the hard case. In Fate an attack is rolled against the defender's
*defend* roll, not a static DC, and the defender often doesn't know they are a
target until the attacker acts. By the time an NPC's attack on a player is
resolved, that player **already committed and the barrier is closed** — there is
no interactive window in the single-pass walk for them to physically throw a
defense die. The d20 path never hits this (every d20 roll is single-actor against
a static DC, with the roller present at resolution); Fate's reactive second-party
rolls collide with the sealed-commit barrier.

Abandoning the sealed-commit barrier for sequential initiative was explicitly
rejected: the barrier protects table pacing (ADR-036; never rush a slow typist).
So the player's defense was left server-rolled in ADR-148 — a documented boundary,
not a regression (defense rolls were never visualized) — and deferred to this
follow-up.

## Decision

**Keep the sealed-commit barrier; make the reactive defense a follow-up roll inside
a new, conditional DEFEND phase.** `run_fate_exchange` stops being a single batch
walk and becomes a four-checkpoint round.

### 1. The four-phase round: COMMIT → REVEAL → DEFEND → RESOLVE

| Phase | What happens |
|---|---|
| **COMMIT** | The existing sealed barrier (unchanged). Players submit proactive `FATE_THROW`s blind; the barrier closes when all seated PCs have committed. |
| **REVEAL** | The server seats and **locks** the NPC actions. Each NPC attack's 4dF is rolled **now**, at REVEAL (`roll_4df`), and never re-rolled across a suspend. The attack graph (who attacks / create-advantage-targets whom) is built. |
| **DEFEND** | **Conditional second barrier.** Only entered if at least one *seated PC* is targeted. The server writes the `pending_defenses` ledger, emits one `FATE_DEFEND_REQUEST` per incoming attack, persists the checkpoint, and **parks** (no narration). |
| **RESOLVE** | Once every pending defense is filled, the exchange walk runs with every roll already in hand — **no `roll_4df` on the player path** — and broadcasts `FATE_ROLL × N` (authoritative dice + throw_params + seed) for replay-and-snap. |

DEFEND is **skipped entirely** in rounds where no player is targeted; those resolve
immediately on the original single-pass path. Each phase is a clean **resume
checkpoint** — there is never a half-resolved walk to persist (a pause-resume
coroutine was rejected for exactly this reason).

### 2. Protocol: `FATE_DEFEND_REQUEST` (server→client) and `FATE_THROW(action="defend")`

- **`FATE_DEFEND_REQUEST`** (`FateDefendRequestPayload`, server→client) — "you are
  attacked by X with skill Y; defend." Carries `request_id`, `defender`,
  `attacker`, `attack_skill`, `attack_total`, and `mental`. One message per
  incoming attack on a seated PC. This is ADR-074's dormant *server-requests-a-throw*
  path, now used for real.
- **`FATE_THROW(action="defend")`** — the player's defense reuses the same
  faces-authoritative `FateThrowPayload` from ADR-148 (`throw_params` + four dF
  faces, `extra="forbid"`, each face ∈ {−1, 0, 1}), with `action="defend"` and the
  echoed `request_id` tying it to its pending entry.
- **`FATE_ACTION`** still carries only the non-roll verbs (`concede`,
  `compel_accept`, `compel_refuse`); it never mounts a tray.

A distinct faces-required message (not optional dice on `FATE_ACTION`) keeps the
player-thrown contract unforgeable — an empty `face` would reopen the
server-rolls-for-players backdoor ADR-148 deleted (No Silent Fallbacks).

### 3. The `pending_defenses` ledger — resume-safe (ADR-128)

When the round parks at the DEFEND barrier, the server writes a `pending_defenses`
ledger onto the encounter (`FatePendingDefense` model, `StructuredEncounter.pending_defenses`),
one entry per incoming attack on a PC. Each entry records the attacker, defender,
attack skill, locked `attack_total`, and `request_id`, and is filled with the
defender's `defense_total` (or a `conceded` flag) as defenses arrive.

The ledger rides `snapshot.encounter` and survives a server restart. NPC dice
rolled at REVEAL are **locked** and never re-rolled on resume. A legacy encounter
loaded without the ledger field deserializes to an empty ledger (no parked round in
flight ⇒ nothing to resume) — this is the one explicitly-blessed default, not a
silent fallback. The exchange RESUMES (`resume_fate_exchange`) once every entry is
filled.

### 4. Player defense is physics-is-the-roll; NPC defense stays server-side

Each `FATE_THROW(action="defend")` resolves the defender's 4dF from the **reported
faces** via `resolve_action_from_faces` — **no `roll_4df` on the player defense
path**, exactly mirroring the proactive contract from ADR-148. NPC/opponent
defenses stay server-rolled (`roll_4df`) — an NPC has no client to throw.

`_resolve_attack` compares attacker shifts vs. defender shifts exactly as before;
the only change is where the defender's faces originate. **The Fate ladder math
(`classify_outcome`, shifts, tiers) is untouched** (SOUL: bind, don't balance).

### 5. Per-attack defense, player picks the skill; invokes in scope

One defense throw per incoming attack; the player chooses the defense skill each
time (Athletics vs. a blade, Will vs. a hex) — faithful to Fate and aligned with
the engine, which already defends per-attack. Per-attack throws nest inside the
single DEFEND barrier, so a heavily-targeted player throws a couple of times within
it. Invokes on defense work as on the proactive side: a bonus invoke (+2) applies
to the reported faces; a reroll invoke means the client throws again and submits
new faces (the server never rerolls on a player path — it does the
fate-point/aspect accounting only).

### 6. AFK in DEFEND: block-and-wait (No Silent Fallbacks)

An absent defender blocks the barrier, identical to the COMMIT barrier
(submit-and-wait; never rush Alex). There is **no quiet server-side roll** for an
absent player and no timeout/auto-resolve — that would be a deliberate future
feature, not baked in. The round simply waits, persisted, until the defense
arrives.

### 7. Defender authorization (the multiplayer integrity gate)

`dispatch_fate_defense` must verify the authenticated actor **is** the entry's
`defender` before recording a defense. Matching a pending entry by client-supplied
`request_id` alone is insufficient: the id is derivable (`def:{round}:{attacker}->{target}`),
so in a multiplayer table player A could otherwise answer player B's
`FATE_DEFEND_REQUEST` with A's skill and faces, filling — and griefing — B's entry
and locking B out. The server rejects loudly on `entry.defender != actor` (mirroring
the ADR-119 `player_id` spoof-rejection in the same handler). The auth rejection
emits an OTEL watcher event (Story 126-13) so the GM panel sees the refusal.

### 8. Concession at the DEFEND barrier (Story 126-14)

A defender may **concede** instead of throwing. A defend concession does **not**
roll (`resolve_action_from_faces` is not called): it marks the matching entry
`conceded`, fills the ledger slot, and lets the barrier close. Concession is a
non-roll verb, so it never mounts a tray and never produces a `FATE_ROLL`.

### 9. OTEL — the DEFEND-barrier lie detector

- `fate.action_resolved` carries `source ∈ {player_thrown, server_rolled}` **and**
  `role ∈ {action, defense}`, so the GM panel distinguishes a defense roll from a
  proactive action and a player throw from a server roll — including NPC defenses,
  which are tagged `role="defense", source="server_rolled"` (Story 126-8 AC-8).
- A new `fate.defend_phase` span records who was requested to defend, who
  responded, and the `conceded` flag — confirming the DEFEND barrier actually fired
  and was not improvised by the narrator.

These are span assertions, not source-text greps (no source-text wiring tests).

## Consequences

**Positive**
- A targeted player throws their own defense — physics-is-the-roll end-to-end,
  closing the ADR-148 boundary without weakening the sealed-commit barrier.
- The conditional barrier costs nothing in rounds where no PC is targeted: they
  resolve on the original single-pass path.
- Resume-safety is structural: each phase is a persisted checkpoint, the ledger
  rides the snapshot, NPC dice are locked at REVEAL — a restart mid-defend resumes
  without re-rolling anything.
- The defender-authorization gate makes the multiplayer defense path spoof-proof,
  observable in OTEL when it rejects.
- The Fate ladder math is wholly untouched — we changed a dice *source*, not a
  resolution rule.

**Negative / accepted**
- The Fate exchange is now a four-checkpoint state machine with a park/resume path,
  not a single batch walk — more moving parts, justified by the sealed-commit
  constraint.
- An absent defender blocks the round (block-and-wait). Accepted per SOUL pacing
  doctrine; a timeout is a deliberate future feature, not a default.
- The player defense tray UI is the client surface for this barrier (Story 126-17);
  the server-side barrier shipped first and is independently testable via the
  protocol.

## Cross-references

- **ADR-148** (Player Fate Rolls Are Physics-Is-The-Roll): the proactive half. 148
  owns the *roll source*; this ADR owns the *DEFEND barrier*. 148 §6 deferred the
  reactive case and reserved this ADR (as the stale "ADR-149"); §6's reference is
  corrected to point here.
- **ADR-074** (Dice Resolution Protocol): physics-is-the-roll, and the dormant
  server-requests-a-throw path that `FATE_DEFEND_REQUEST` revives.
- **ADR-036 / ADR-129** (sealed-commit turn model): the barrier this phase extends
  without breaking; the reason the defense had to become a second barrier rather
  than an inline interactive roll.
- **ADR-128** (resume-safe randomness): precedent for the persisted-checkpoint /
  locked-dice resume model the `pending_defenses` ledger follows.
- **ADR-119** (Authenticated Player Identity): the `player_id` spoof-rejection the
  defender-authorization gate (§7) mirrors.
- **ADR-144** (Fate Core Binding): the bound ruleset whose ladder math stays
  untouched.
- Design sources: `docs/superpowers/specs/2026-06-17-fate-determinative-rolls-design.md`
  (the four-phase model) and the 2026-06-18 sealed-commit defend spec + server plan
  (Story 126-8 ACs). Implemented across Stories 126-8 (barrier), 126-13
  (auth-rejection OTEL), and 126-14 (concession wire).
