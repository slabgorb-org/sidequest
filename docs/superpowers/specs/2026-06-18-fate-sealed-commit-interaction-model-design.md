# Fate Core in the Sealed-Commit Turn Model — The Complete Interaction Model

**Date:** 2026-06-18
**Author:** The Architect (TEA) + Keith Avery
**Status:** Approved (design) — pending written-spec review
**Epic:** 126 (Fate Core playtest follow-ups)
**Implements first slice:** Story 126-8 (Fate defend follow-up barrier, ADR-149)
**Builds on:** `docs/superpowers/specs/2026-06-17-fate-determinative-rolls-design.md` (proactive determinism + the defend-barrier model)
**Companion ADRs:** ADR-148 (proactive determinism, live) · ADR-149 (defend follow-up barrier — to be authored in 126-8)
**Reconciles:** ADR-036 / ADR-129 (sealed-commit turn model) · ADR-074 (dice physics-is-the-roll) · ADR-144 (Fate Core binding) · ADR-107 (out-of-band aside channel) · ADR-128 (resume-safe randomness)

---

## 1. Problem

Fate Core is a **conversation**. At the tabletop the loop is: declare → roll → *see the result* → decide whether to spend a fate point to invoke (+2 or reroll) → narrate. Defense is an **active, chosen** roll the target makes *in reaction* to an attack. Aspects created by one player become resources another invokes later. Compels and concessions are negotiated mid-scene. Fate points flow constantly between players and GM.

Our turn engine is the opposite shape: a **sealed-commit barrier** (ADR-036 / ADR-129). Everyone commits **blind and simultaneously**, the barrier closes, then resolution unfolds with no agency in between. That barrier is **non-negotiable** — it is what protects Alex from ever being rushed and what kills fast-typist monopolies. It is also one of SideQuest's genuine advantages over tabletop, and we intend to *exploit* it, not merely survive it.

The design problem: **make Fate's reactive, post-information, negotiated beats live inside a blind-simultaneous-commit model — and feel alive, not like submitting a form and watching a replay.** Story 126-8 (interactive player defense) is the first hard collision; this document is the complete model it implements.

### 1.1 The keystone insight — latency lives in the narrator, not the wire

A WebSocket/server round-trip costs **milliseconds**. A narrator (LLM) call costs **seconds** — the entire 126-9 / 126-10 latency investigation was narrator + router LLM time, never wire time. Therefore:

> **Spend client↔server chatter like water; hoard narrator calls like gold.**

Two consequences fall straight out, and they dissolve the smoothness-vs-fidelity tension rather than splitting it:

- **The client owns the roll-adjust loop; the narrator sees no intermediate dice.** The reason *solo* Fate can ping-pong "roll → see → invoke → reroll" forever is that there is no table waiting — and that ping-pong was never the table's business in the first place. It is private to one player and their **own** dice and **own** resources (fate points, aspects), all of which the client already knows. So in multiplayer, every player runs that solo loop **concurrently and locally**, and the sealed barrier waits only for each to hit *Submit* — the one wait the table already accepts.
- **One round, one narration.** The sealed barrier is a **batching engine**: collect the whole table's intents and final rolls, resolve **every** mechanic server-side, and only *then* invoke the narrator **once** to render the entire woven exchange as a single cinematic beat. The narrator is **never** in the mechanical loop.

### 1.2 Sealed turns are the special sauce, not the constraint

Tabletop is **serial**: initiative means three players watch one act, the GM narrates, the next acts. We are **simultaneous**: N players commit at once, the engine resolves the whole measure in parallel, and the narrator writes the entire band's bar in one pass. This **structurally dissolves the Guitar Solo problem** (SOUL): nobody is a silent audience, because everyone's verb resolves into the *same* beat. The barrier "wait" is not dead time — it overlaps every player's local deliberation instead of serializing it.

---

## 2. Principles (the design test)

1. **Latency lives in the narrator, not the wire.** Wire round-trips are free; narrator calls are the cost.
2. **The client owns the roll-adjust loop.** Throw (physics-is-the-roll) → adjust locally (invoke / reroll, spending own FP/aspects) → submit only the final result. The server validates the spend on submit and rejects loud if unaffordable (No Silent Fallbacks). The narrator sees no intermediate dice.
3. **One round, one narration.** Resolve all mechanics cheaply, narrate once. NPC action-*selection*, if it needs intelligence, uses the **cheap tier** (Haiku / heuristic / intent-router) — never the expensive cinematic narration.
4. **Sealed turns are a feature.** Simultaneous where tabletop is serial; everyone's verb lands in one beat.
5. **Bind the ruleset, don't balance it** (SOUL / ADR-144). This document changes the dice *source* and the *interaction choreography*, never the Fate ladder math (`classify_outcome`, shifts, tiers).

**Design test for any future Fate feature:** if it would put the cinematic narrator (Sonnet) *inside* the commit→resolve loop, or round-trip it per-player-per-action, it is mis-designed.

---

## 3. The complete round structure

Every Fate interactive beat, placed inside the sealed barrier. **Two barriers maximum; one (occasionally two) narrator calls per round.**

```
 INTER-ROUND   The previous round's single narration set the fiction and projected
               FATE_STATE (sheets / aspects / fate points). A narrator-offered COMPEL
               rides that narration; players accept/refuse out-of-band (ADR-107),
               non-committing, before committing.                  [no narrator call]

 1. COMMIT     Sealed barrier (the one the table already accepts).
   (barrier)   Each seated PC, CONCURRENTLY + PRIVATELY on their own client:
                 • throws the proactive die (overcome / create_advantage / attack)
                   — physics-is-the-roll (ADR-074/148)
                 • LOCAL ADJUST LOOP — invoke (+2) / reroll, spending own FP/aspects;
                   informed by own dice (+ the known target for a fixed-difficulty obstacle)
                 • submits the FINAL result
                 • (pre-roll, non-committing alternatives: concede / accept/refuse a compel)
               Closes when all live seated PCs submit.            [wire only · no narrator]

 2. REVEAL     Server, instant. Seat NPC/opponent actions (CHEAP tier picks target+skill;
   (server)    NPC 4dF rolled SERVER-SIDE NOW, so it is locked and never re-rolled across
               the suspend). Build the attack graph. No PC targeted → skip DEFEND entirely.

 3. DEFEND     Second barrier — CONDITIONAL (only if a PC is targeted).
   (barrier)   Per incoming attack, the server hands the PC the COMMITTED ATTACK TOTAL:
                 • free-pick a defense skill (justified in the fiction — the Zork Problem:
                   never close the verb set)
                 • LOCAL ADJUST LOOP — now FULLY INFORMED (sees the incoming number)
                 • submit the FINAL defense — OR CONCEDE here ("seeing it go bad")
               NPC defenses roll server-side inline. Multiple attacks on one PC stack as
               sequential cards within this single barrier. Closes when all PC
               defenses/concessions are in.                       [wire only · no narrator]

 4. RESOLVE    Server, instant. Every roll in hand → walk once: compare attacker vs
   (server)    defender finals, shifts, absorb stress/consequences, place created aspects,
               mark taken-out, end-on-no-other. Emits the fate.* OTEL spans (lie detector).

 5. NARRATE    ONE narrator call (the floor): renders the ENTIRE woven exchange as a single
   (narrator)  cinematic beat. Drama-scale (SOUL): a genuine spike (a PC taken out, a
               reversal) may earn ONE extra beat. Sets up the next round; may attach the
               next compel offers.
```

### 3.1 How each Fate beat maps

| Fate beat | Where it lives | Notes |
|---|---|---|
| Proactive action + post-roll invoke | COMMIT local loop | Already live for the throw (126-7); generalized here |
| **Reactive defense (+ defense invoke)** | **DEFEND local loop** | **126-8 — the new beat. Informed defender.** |
| Invoke an aspect (yours or another's) | Any local loop (self-invoke) | Free invokes placed by create-advantage are consumed by *any* player inside their own COMMIT/DEFEND loop |
| Create-an-advantage | COMMIT (proactive) | No new beat; payoff is cross-turn but the spend is always local |
| Compel | INTER-ROUND, out-of-band (ADR-107) | Rides the once-per-round narration; resolved before next commit; non-committing |
| Concession | DEFEND beat (and pre-commit) | The informed-defender display makes "I see the Great attack → I fold" the natural dramatic moment |

---

## 4. Key decisions

### 4.1 Contested asymmetry — informed defender, committed attacker

The attacker commits **first** (COMMIT), blind to the defense. The defender reacts **second** (DEFEND) — and by then the attacker's final number is already locked on the server. So we **hand the defender the incoming attack total** and let them adjust *fully informed* ("they rolled Great — I'd better invoke"), for free, while the attacker — who struck first — does **not** get to re-push after seeing the defense.

This is faithful to the feel (you strike; they see the blow and react) and the medium gives it for nothing. The only fidelity loss is the attacker cannot push *after* the defense reveals — minor, and accepted. We do **not** add a post-defense window for the attacker.

### 4.2 Narrator cadence — one call at RESOLVE, drama-scaled

Floor: exactly **one** narrator call per round, at RESOLVE, rendering the whole woven exchange. Refinement (SOUL "Cost Scales with Drama"): a genuine spike — a PC taken out, a dramatic reversal — may earn **one** extra beat. The quiet round gets exactly one. The narrator is never invoked mid-round.

### 4.3 The local adjust loop is client-owned

A reroll under determinism means the **client throws again** and submits the new faces; the server resolves once and does only the fate-point/aspect accounting (established by ADR-148 for the proactive throw, generalized here to every player roll — proactive and defense). The server is the authority only at **submit**: it validates that the player actually held the fate point / free invoke spent, and rejects loud otherwise.

---

## 5. Control-flow / state — the suspend/resume seam

COMMIT→RESOLVE can no longer be one synchronous call: it must **suspend at DEFEND and survive a server restart** while it waits on a possibly-slow human. A pause-resume coroutine is rejected — a half-resolved walk cannot be persisted, so a restart mid-`await` would lose the exchange. The resume-safe shape is **a phase state machine on the encounter where every transition is a checkpoint** (ADR-128 resume-safety).

- **New state — a `pending_defenses` ledger** (sibling to `fate_commits` on the encounter): one entry per incoming attack on a PC —
  `{request_id, attacker, defender, attack_skill, attack_total, defense_result | None}`.
  An unfilled entry *is* the "we are in DEFEND" signal (an explicit phase enum may be added for legibility/OTEL, but is not required for correctness).
- **COMMIT closes → server runs REVEAL synchronously and persists it:** seat NPC commits (cheap-tier target+skill; NPC 4dF rolled server-side **now** and locked), build the attack graph.
  - *No PC targeted* → resolve immediately (today's single-call path, unchanged).
  - *PC(s) targeted* → write `pending_defenses`, emit one `FATE_DEFEND_REQUEST` per entry (carrying the committed `attack_total`), **persist, and return.** The exchange is parked at a clean checkpoint.
- **Each `FATE_THROW(action=defend)` arrives** → the existing `FateThrowHandler` branches on `action=defend` to a defense path: validate faces + fate-point spend, resolve from the reported faces (`resolve_action_from_faces` — **no `roll_4df` on the player path**), record `defense_result` on the matching entry by `request_id`. A concession marks the entry conceded.
- **Ledger full → RESUME:** run RESOLVE — the existing exchange walk, but `_resolve_attack` reads the *recorded* PC defense instead of calling `_roll_defense` (NPC defenses still `roll_4df` inline). Clear the ledger, emit `fate.defend_phase` + the resolution spans, NARRATE once.
- **AFK = block-and-wait** (2026-06-17 design §8): the DEFEND barrier waits indefinitely, exactly like the commit barrier — no timeout, no quiet server-roll for an absent player. Never rush Alex; No Silent Fallbacks. (A timeout/auto-resolve is a deliberate future feature, not baked in now.)

*Rejected alternatives:* the mid-walk coroutine (not restart-safe); stateless re-derivation (it would re-seat NPCs and thus **re-roll their locked dice** — non-starter).

---

## 6. Protocol

| Message | Dir | Role |
|---|---|---|
| **`FATE_THROW`** (existing, extended) | client→server | **All** player physics rolls — proactive *and* defend. `action` ∈ {overcome, create_advantage, attack, **defend**}; for a defend it echoes the `request_id` of the `FATE_DEFEND_REQUEST` it answers. Faces authoritative at the wire (`extra="forbid"`, exactly 4, each ∈ {−1,0,1}). |
| **`FATE_DEFEND_REQUEST`** (new, `FateDefendRequestPayload`) | server→client | "You are attacked by X with skill Y at total T — defend." Carries attacker, attack skill, the committed `attack_total`, and a `request_id` the client echoes. One per incoming attack on a PC. |
| **`FATE_ROLL`** (existing) | server→all | Broadcast per resolved roll (action **and** defense): authoritative `dice` + echoed `throw_params` + server `seed`; spectators replay and snap to the authoritative dice. |
| **`FATE_ACTION`** (existing) | client→server | Retained for the **non-roll** verbs only: concede, compel_accept, compel_refuse. Never mounts a tray. |

**Naming reconciliation (deliberate deviation):** Story 126-8's card paraphrases this as a "new `FATE_DEFEND_THROW` message." The authoritative model uses **`FATE_THROW(action=defend)` + `FATE_DEFEND_REQUEST`** instead — a defend is the same physics throw as a proactive action, so it reuses `FATE_THROW` rather than forking a parallel message; the genuinely new artifact is the server→client *request*. An optional `face` on `FATE_ACTION` is rejected (a silent fallback would re-open the server-rolls-for-players backdoor). The card's name is shorthand; this document is the contract.

---

## 7. Server resolution

`game/ruleset/fate_resolution.py` already factors classify/build into one private `_build_outcome`, consumed by two siblings (live since 126-7):

- `resolve_action(*, skill_rating, opposition, rng, invoke_bonus)` — **NPC path**, rolls `roll_4df(rng)`.
- `resolve_action_from_faces(*, skill_rating, opposition, faces, invoke_bonus)` — **player path** (proactive *and* defense), never touches an `rng`.

126-8 routes the player's **defense** through `resolve_action_from_faces` (from the recorded DEFEND-phase faces) and leaves NPC defense on `roll_4df`. The Fate ladder math is untouched — bind the ruleset, don't balance it.

---

## 8. UI surfaces (sidequest-ui + ../dice-lib — reuse, don't reinvent)

The dF `DieKind`, `DiceScene`, and `replayThrowParams` already exist (125-4 / 126-7). The new work is interaction, not rendering.

- **COMMIT tray — the aspect shelf (chosen).** After the 4dF settle: a live ladder readout (`dice + skill = total` vs the target for a fixed-difficulty obstacle, or "contested — opposition at resolve" for an active attack), and an **aspect shelf** of tap-to-spend chips beneath the tray — each invokable aspect is a chip showing its FP cost; tap to spend (+2 animates onto the total), tap again to take it back before commit; a Reroll chip re-throws; a Commit button locks. (Action-row presentation is the fallback; the shelf is the tactile, whole-hand-visible direction.)
- **DEFEND prompt — informed, free-pick, concede-at-defend.** A prominent banner shows the incoming attack total *before* the throw. A **free-pick** defense-skill selector (any skill on the sheet, justified in the fiction — the Zork Problem). The same throw + aspect-shelf loop, now fully informed. A **Concede** control, present but visually secondary to Defend (fold on your terms for fate points). Multiple incoming attacks present as sequential cards within the one DEFEND barrier.
- **Guitar Solo / non-targeted players — the live board (floor).** While one player defends, the others see every committed intent as a card (peer visibility, ADR-036 amendment) plus the defender's dice landing (spectator replay snapped to authoritative faces). They already have a verb this round (their committed action), so the board needs no extra interaction. **Future enrichment (deferred):** "active help" — a teammate spends a fate point to invoke an aspect aiding the defender; truest to the Guitar Solo ideal but reopens cross-player invokes mid-defense, so it is **not** in the first slice.

---

## 9. OTEL (the lie detector)

- `fate.action_resolved` gains `role ∈ {action, defense}` **and** keeps `source ∈ {player_thrown, server_rolled}` (the `source` attr already exists from 126-7). The GM panel can confirm a player defense really came from the client and an NPC defense really came from the server RNG.
- New **`fate.defend_phase`** span: who was requested to defend, who responded — so the GM panel can confirm the DEFEND barrier actually fired and was not improvised.
- Span assertions, not source-text greps (server CLAUDE.md "No Source-Text Wiring Tests").

---

## 10. Implementation slicing

- **Story 126-8 (ADR-149) — this design's first vertical slice:** the COMMIT→REVEAL→DEFEND→RESOLVE restructure; `pending_defenses` ledger + suspend/resume state machine (resume-safe); `FATE_DEFEND_REQUEST` + `FATE_THROW(action=defend)`; player defense via `resolve_action_from_faces`; NPC defense stays `roll_4df`; concede-at-defend; the defend-mode UI (informed banner, free-pick skill, aspect shelf, concede); the live-board Guitar Solo view; `role`/`fate.defend_phase` OTEL; block-and-wait AFK.
- **Deferred (future stories):** Guitar Solo "active help" cross-player aid-invokes (§8); DEFEND-barrier timeout/auto-resolve (§5).

---

## 11. Testing

Mirrors the 2026-06-17 design §10, extended for the complete model. Span assertions over source greps throughout.

- **Determinism:** player defense resolves from reported faces; assert `roll_4df` is **not** called on the player defense path (spy). Faces → expected defense ladder_total/shifts.
- **NPC server-side:** NPC defense still calls `roll_4df`; NPC proactive rolls server-side.
- **Wire validation:** `FateThrowPayload` accepts `action="defend"` + echoes a `request_id`; rejects ≠4 faces, faces ∉ {−1,0,1}, extra fields. `FateDefendRequestPayload` validates and is in the `GameMessage` union.
- **Conditional DEFEND:** a round with no PC targeted emits no `FATE_DEFEND_REQUEST` and skips the barrier; a round with a PC targeted emits one request per incoming attack and parks the exchange.
- **Resume-safety:** the exchange suspended at DEFEND survives a reload from persisted state; NPC rolls are not re-rolled on resume.
- **OTEL:** `fate.action_resolved` fires with the right `source`/`role`; `fate.defend_phase` fires recording requested/responded.
- **WIRING (mandatory, end-to-end):** NPC-attacks-PC → `FATE_DEFEND_REQUEST` → player defend `FATE_THROW` → resolve, all through the real handler/registry/exchange on a fixture snapshot (not a unit stub); confirm the NPC path still server-rolls.
- **Block-and-wait:** an absent defender holds the barrier; no server-side auto-roll fires for them.

---

## 12. Non-goals

- Abandoning the sealed-commit barrier for sequential initiative (explicitly rejected — it is the special sauce).
- Post-defense push window for the attacker (§4.1).
- Cross-player aid-invokes during DEFEND in the first slice (deferred, §8/§10).
- DEFEND timeout / auto-resolve (deferred, §5).
- Changing any Fate resolution math (bind, don't balance).

---

## 13. References

- `docs/superpowers/specs/2026-06-17-fate-determinative-rolls-design.md` — proactive determinism + the defend-barrier model this completes
- ADR-148 — Player Fate Rolls Are Physics-Is-The-Roll (proactive; live)
- ADR-149 — Fate Defend Follow-up Barrier (to be authored in 126-8)
- ADR-036 / ADR-129 — sealed-commit turn model
- ADR-074 — Dice Resolution Protocol (physics-is-the-roll)
- ADR-144 — Fate Core Binding Replaces the Native Ruleset
- ADR-107 — Out-of-band aside channel (compels)
- ADR-128 — resume-safe randomness (resume-safety precedent)
- SOUL.md — "The Guitar Solo," "Cost Scales with Drama," "The Zork Problem," "Bind the Ruleset, Don't Balance It"
