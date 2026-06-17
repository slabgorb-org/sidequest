---
id: 148
title: "Player Fate (4dF) Rolls Are Physics-Is-The-Roll; NPC Rolls Stay Server-Side — Reconciling ADR-074 and ADR-144"
status: proposed
date: 2026-06-17
deciders: ["Keith Avery", "The Man in Black (Architect)"]
supersedes: []
superseded-by: null
related: [36, 74, 117, 129, 144]
tags: [frontend-protocol, game-systems]
implementation-status: deferred
implementation-pointer: null
---

# ADR-148: Player Fate (4dF) Rolls Are Physics-Is-The-Roll; NPC Rolls Stay Server-Side — Reconciling ADR-074 and ADR-144

> Reconciliation note for **ADR-074** (Dice Resolution Protocol — player-facing rolls
> are physics-is-the-roll) and **ADR-144** (Fate Core Binding). It governs *where a
> Fate die value comes from*, not *how a Fate action resolves*. The Fate ladder math
> from the bound ruleset (`classify_outcome`, shifts, tiers) is untouched — per SOUL
> "Bind the Ruleset, Don't Balance It," we change the dice **source**, never the
> resolution.

## Context

The Fate 4dF resolution path is backwards relative to the d20 path. The d20 path is
**physics-is-the-roll** (ADR-074, as amended 2026-05-02): the rolling player's client
runs Rapier locally, reads the settled faces, and sends them to the server as the
authoritative result (`DiceThrowPayload.face`); the server resolves from those faces
(`resolve_dice_with_faces`) and never rolls its own RNG for a player. The server-side
`seed` exists only to make the spectator **replay** land on the same faces.

The Fate path inverts this. The player submits intent only (`FateActionPayload` — verb,
skill, target, invokes; **no dice**). The server rolls the dice itself
(`FateActionHandler` → `dispatch_fate_action` → `FateRulesetModule.resolve_action` →
`roll_4df(random.Random())`), decides the outcome, and broadcasts `FATE_ROLL`. The 3D
`FateDiceTray` is a **post-hoc decoration**: it receives the already-decided
`FateRollPayload` and calls `replayThrowParams(...)` with an `onAllSettle` no-op — the
settled face is discarded.

Story 125-4 tried to make that decoration *look* like the roll by animating the tumble.
It could not: the synthesized throw lands on physics-determined faces unrelated to the
server's already-decided result, so the 3D dice can contradict the text readout. That
defeats the legibility mandate (Sebastien/Jade: "the dice should show what was actually
rolled"). The agent attempting this story misjudged the fix twice — hence design-first.

The root cause is not the animation; it is the **direction of authority**. Determinism
fixes 125-4 *by construction*: when the faces come **from** the physics throw, replaying
`throw_params + seed` reproduces them for every seat — exactly what "mirror DICE_RESULT"
in the 125-4 / 118-x ACs actually required.

## Decision

**A player's Fate (4dF) roll is physics-is-the-roll.** The rolling player throws four
dF dice in an interactive tray; the faces they settle on **are** the roll. The server
resolves the Fate action from those reported faces and never calls `roll_4df` on the
player path. **NPC/opponent rolls stay server-side** (`roll_4df`) — an NPC has no client
to throw — and are projected to seats via `FATE_ROLL` with a server-synthesized
`throw_params + seed` (the 125-4 groundwork), so spectators replay and the NPC's dice are
visible too.

This is the **same model the d20 path already uses**, and we mirror the path that is
actually live — the **client-driven** one. We do not resurrect ADR-074's original
server-requests-a-throw round-trip (superseded 2026-05-02). Concretely:

### 1. Reconciling 074 and 144 — source vs. resolution

| Concern | Owner | Behavior |
|---|---|---|
| **Source** of a player's dF faces | ADR-074 (physics-is-the-roll) | client Rapier settle → authoritative `face[4]` |
| **Source** of an NPC's dF faces | server | `roll_4df(rng)` (no client exists) |
| **Resolution** (ladder, shifts, tier) | ADR-144 (bound Fate Core) | `classify_outcome` — **unchanged for both** |

We are **not** balancing or tuning anything (SOUL: Bind the Ruleset). `sum(faces) +
skill_rating + invoke_bonus`, then `classify_outcome`, is identical whether the four
faces came from the client or the server RNG. Only the dice *source* differs.

### 2. The client→server message: a new `FATE_THROW`, and `FATE_ACTION` keeps the non-roll verbs

Mirror `DICE_THROW`: a single client-driven message carries **both** the action context
and the authoritative faces. We add `FATE_THROW` / `FateThrowPayload` (the Fate analog of
`DiceThrowPayload`):

- Roll verbs (`overcome`, `create_advantage`, `attack`) for a **player** go out on
  `FATE_THROW` — they now require a throw.
- Non-roll verbs (`concede`, `compel_accept`, `compel_refuse`) stay on the existing
  `FATE_ACTION` — they never rolled and never should mount a tray.

`FateThrowPayload` carries the action intent fields plus `throw_params: ThrowParams` and
`face: tuple[int, int, int, int]`. Faces are **authoritative at the wire**: `extra="forbid"`,
exactly four, each in `{-1, 0, 1}` (validated in the model — defense in depth even though
the engine re-validates). The message is registered in the `GameMessage` union and
dispatched to a `FateThrowHandler`.

**`FATE_ACTION` is not extended with optional dice.** An optional `face` field would be a
silent fallback (No Silent Fallbacks): if it arrived empty on a player roll, the server
would have a backdoor to roll for the player — the exact bug we are deleting. A distinct,
faces-required message makes the player-thrown contract unforgeable.

### 3. The `seed` is server-generated, matching `DiceThrowPayload`

The story AC phrases the client message as "faces + throw_params + **seed**," but the
thing we are told to mirror — `DiceThrowPayload` — has **no seed**. The client sends
`throw_params` (the gesture) and `face`; the **server** generates the replay `seed`
(`generate_dice_seed`) and echoes both on the broadcast. This is faithful to the d20
contract and keeps the per-(session, round) seed authority server-side so every seat
replays identically. (Recorded as a deliberate refinement of the AC wording.)

### 4. Server resolution split

`game/ruleset/fate_resolution.py` factors the classify/build step out of `resolve_action`:

- `resolve_action(*, skill_rating, opposition, rng, invoke_bonus)` — **NPC path**, rolls
  `roll_4df(rng)` (unchanged signature).
- `resolve_action_from_faces(*, skill_rating, opposition, faces, invoke_bonus)` — **player
  path**, takes the four reported faces; never touches an `rng`.
- Both feed one private `_build_outcome(dice, …)` so the ladder math lives in one place.

`FateRulesetModule` gains a `resolve_action_from_faces` wrapper emitting the same
`fate.action_resolved` span. `dispatch_fate_action` takes the player's faces from
`FATE_THROW` and calls the faces variant; `_seat_opponent_commits` and `_roll_defense`
keep the `rng` variant.

### 5. Invokes under determinism

Fate invokes are post-roll. The thrower throws, sees the faces, then may invoke:

- **Bonus invoke (+2):** applied server-side from the reported faces
  (`ladder_total = sum(faces) + skill + invoke_bonus`). No roll. Identical to today.
- **Reroll invoke:** in the determinative model a reroll means the **client throws
  again** and submits the new faces. The server does **not** reroll — it resolves the
  submitted faces once and performs only the fate-point / aspect-invoke accounting. The
  current "call `resolve_action` a second time" branch is removed from the player path.

### 6. Defense rolls are out of scope (boundary, not regression)

A player's **reactive defense** against an incoming NPC attack resolves *inside* the
sealed-commit exchange walk (`run_fate_exchange` → `_resolve_attack` → `_roll_defense`),
after the per-round barrier closes (ADR-036 / ADR-129). There is no interactive moment to
throw there without breaking the barrier. Defense rolls — player and NPC alike — **stay
server-side** in this ADR. This is **not a regression**: defense rolls are not visualized
today (only the acting PC's roll is broadcast as `FATE_ROLL`). Interactive player defense
is a separate, harder problem — it is **designed** (a conditional DEFEND follow-up barrier
that keeps the sealed-commit barrier intact) in
`docs/superpowers/specs/2026-06-17-fate-determinative-rolls-design.md` and scheduled as
**Story 126-8 / ADR-149**, not left as an open punt. The "no `roll_4df` on the player
path" invariant therefore scopes to the player's **proactive action** dispatch
(`dispatch_fate_action`), which this ADR makes determinative.

### 7. Spectator consistency

`FATE_ROLL` carries the authoritative `dice` (the thrower's reported faces, or the NPC's
server roll), the echoed `throw_params`, and the server `seed`. Every other seat replays
`throw_params + seed` for the tumble **and the tray snaps the settled die to the
authoritative `dice` face** — so the 3D dice can never contradict the text readout,
consistent by construction with `DICE_RESULT`.

### 8. OTEL

`fate.action_resolved` already records the dice and ladder. It gains a `source`
attribute ∈ `{"player_thrown", "server_rolled"}` so the GM panel (the lie detector) can
confirm a player roll really came from the client and an NPC roll really came from the
server.

## Consequences

**Positive**
- 125-4's contradiction is fixed by construction: the dice *are* the roll.
- Reuses the proven, live d20 determinative pattern end-to-end (`DiceScene`, the dF
  `DieKind`, `replayThrowParams`); the only genuinely new artifact is the `FATE_THROW`
  message — the rest is plumbing.
- The player-thrown vs. server-rolled split is unforgeable at the wire and observable in
  OTEL.
- 125-4's wire groundwork (`throw_params`/`seed` on `FateRollPayload`, the dF `0` label)
  is preserved, not reverted.

**Negative / accepted**
- A player roll verb now costs an interactive throw (a beat of latency) instead of a
  synchronous send. This is the point — it is the same cost the d20 path already pays.
- Player defense remains server-rolled (boundary above). Deferred, documented.
- `reroll` invoke semantics change (client re-throws; server accounts only). Documented;
  the player-visible behavior — spend a fate point, get new dice — is unchanged.

**Flip to `accepted` / `implementation-status: live`** when Story 126-7 lands green.
