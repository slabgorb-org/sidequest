# WN Combat Player Action Surface + RP-Flavor Rider — Design

**Date:** 2026-06-14
**Status:** Approved (design settled with Keith, 2026-06-14, this session)
**Repos:** sidequest-ui (primary), sidequest-server (action-id contract + OTEL)
**Author:** Neo (Architect)
**Architecture-of-record:** ADR-143 (WN binding replaces the native combat engine). This spec
covers **only** the *player-facing action surface* — deliverable #2 of Keith's 2026-06-14 rework
brief. The engine cut (remove native `apply_beat` scaffolding from `run_wn_round`) is ADR-143 /
epic-108 story **108-1**; the room-sourced seater is **108-2**; content de-nativization is **108-3**.
This spec depends on 108-1 and does not re-litigate it.

## The one-sentence design

Under a Without Number binding, combat is declared through a **closed set of server-authored WN
action buttons** (not native "beats"), each button fires a **real WN roll** resolved by the
`WithoutNumberRulesetModule` and sequenced by `wn_round.py`, and the player may optionally attach
**freeform text that is pure RP flavor** — handed to the narrator as a hook, carrying **zero
mechanical effect**.

## Why buttons, and why combat is the one place we accept a closed verb set

SideQuest's whole reason to exist is removing the Zork Problem — the natural-language narrator lets
a player attempt anything they can articulate (SOUL.md → *The Zork Problem*). **Combat is the
deliberate exception, and the exception is load-bearing.** We have tried freeform combat and it
**fails the same way every time: the narrator just *narrates* a result instead of the engine
*resolving* one.** That is the El Dorado failure the entire mechanical-scaffold architecture exists
to escape (SOUL.md *purpose*: "escape El Dorado through structural support"). A button is not a UI
convenience here — it is the structural scaffold that **forces the engine to be the authority** and
denies the narrator the chance to invent an outcome. Keith, 2026-06-14, emphatic:

> "We have already proven we can't reliably do the mechanics [freeform]. This is El Dorado if we
> try. We have to have the buttons — you don't have to call them 'beats.' WE HAVE TRIED THE FREEFORM
> COMBAT AND IT JUST GETS NARRATED."

So the closed verb set is intentional **for combat resolution only**. It does not reintroduce the
Zork ceiling everywhere — it is scoped to the moment where an unresolved verb becomes a narrator lie.

## The RP-flavor rider (the chandelier swing) — already wired, now constrained

The escape hatch that keeps the closed set from feeling like a cage is the **flavor rider**, and it
**already exists in the wire contract** — this spec constrains it, it does not invent it.

- `DICE_THROW.player_action` (`sidequest/protocol/dice.py:177-185`) is documented as *"the freeform
  text the player typed into the InputBar at the moment they clicked a beat tile … 'I swing from the
  chandelier' + click Attack carries the chandelier swing as the player's stated action."* The
  dispatch already prepends it to the narrator's replay text as `PLAYER_ACTION: {text}`
  (`dispatch/dice.py:281-282`, `:308-309`).
- **The rider's contract under WN (the invariant this spec adds):** the flavor text is **RP intent
  only**. It rides *alongside* a button-press; it **never** becomes its own action, gets its own
  roll, grants advantage, sets a DC, or changes the resolved outcome in any way. The d20 and the
  damage dice are identical whether the player typed nothing or typed a flourish. The text exists
  **solely so the narrator colors the resolved button outcome** with what the player pictured. Keith,
  2026-06-14: *"You ACCOMPANY the attack with the chandelier swing, not replace it. It allows the
  narrator a hook into your RP intent, THAT IS ALL … this is just an RP affordance."*

**There is no freeform-adjudication path. The engine never tries to mechanize "chandelier swing."**
Resolution already happened on the button; the rider is downstream cosmetic context. This is what
keeps the chandelier *out* of the El Dorado trap — there is nothing for the narrator to "resolve,"
because the roll is already done.

### Bare freeform during combat (the lock reconciliation)

The brief notes "plain Enter is currently locked during confrontation." Mechanically, the server
does **not** hard-lock free text — the `DICE_THROW` path *requires* a `beat_id`/action-id for dice
resolution, while a bare `PLAYER_ACTION` message would still reach the narrator (UI-side lock only;
confirmed via dispatch trace). Under WN combat the design intent is explicit:

- **The only text path during combat is the rider on a button-press.** A bare combat free-text
  submission (text with no action button) must **not** be resolved to a combat outcome by the
  narrator. The UI keeps the InputBar bound to "type your flourish, then pick an action" — text alone
  does not submit.
- Out-of-band table-talk (ADR-107 aside channel) is unaffected — that is non-turn-consuming OOC, not
  a combat action, and never resolves mechanically.

This preserves the invariant that **every combat outcome traces to a button → roll**, never to a
narrated free-text.

## The WN action set (the buttons)

The button set is the **WWN SRD action economy** (per the standing WWN-SRD-authority ruling,
gm-decisions.md 2026-06-13 — source the set from the SRD, do not invent or port native beats). WWN's
turn is a **Move + a Main Action** (plus free "on-turn" actions). The combat buttons for the L1
`beneath_sunden` melee surface, derived from that economy:

| Button | WN resolution | Module seam |
|---|---|---|
| **Attack** (equipped weapon) | `d20 + hit bonus + attribute mod vs target AC`; weapon damage dice on hit; Shock where applicable | `ruleset.attack_params` / `resolve_damage`; opponent acts at its OWN initiative slot in `run_wn_round` |
| **Use Item** (consumable from carried inventory) | item effect applied (e.g. heal `1d6+2` to HpPool); item consumed; **no attack roll** (auto-resolve) | existing 106-4 Part-C item-use path (`dispatch/item_use.py`), already costs the Main Action and the opponent still acts |
| **Move / Disengage** | reposition; WWN Fighting Withdrawal where the SRD grants it | movement under the round walk |
| **Cast** (arcane classes only) | WN Effort spend + spell resolution | `spell_id` carrier (story 102-2), `wwn.spell.cast` |

**Explicitly NOT a button: Brace / total-defense.** WWN has **no total-defense action** — defense
is **passive AC** from armor, shield, cover, and Foci, not an action a player spends a turn on
(gm-decisions 2026-06-13; WWN SRD). The native `brace` `BeatKind` is removed by 108-1; it must not
reappear as a WN button.

> **Architectural reconciliation flag (for 108-1 / scenario-designer):** ADR-143's decision prose
> lists *"full defense"* among WN actions (`attack, full defense, move, item-use, cast`). That
> parenthetical conflicts with the WWN SRD and with the gm-decisions ruling ("Brace is not a WWN
> action; WWN has no total-defense action"). **Resolution: there is no total-defense button under
> WWN.** If a future WN sister-ruleset (CWN/SWN/AWN) authors a genuine defensive Main Action from
> *its* SRD, it is added per-module from that SRD — never as a revived native `brace`. Recommend
> ADR-143 be amended to strike "full defense" from the WWN action list to prevent the next
> contributor re-deriving a Brace button.

The final per-pack button set is **content/scenario-designer** territory (enumerated against the WWN
SRD action list), not engine. This spec fixes the *contract and shape*, not the per-class roster.

## Wire contract (reuse, no new protocol)

No new transport. The existing `DICE_THROW` path carries everything:

- **Action identity moves from `beat_id` (a native `BeatKind`) to a WN action id.** Today the WN
  sealed-round path *already* routes through `DICE_THROW` keyed by a `beat_id` (e.g. `strike`); 108-1
  removes the native `BeatKind` semantics behind it. The UI button emits the WN action id in the same
  field slot; the server resolves it via the ruleset module, not `beat_kinds.apply_beat`. (Whether
  the field is literally renamed `action_id` or the `beat_id` slot is repurposed is an
  implementation choice for 108-1's author — the *contract* is "a WN action id, not a native beat
  kind.")
- **`player_action`** stays exactly as-is: the optional flavor rider, prepended to the narrator
  replay text, mechanically inert.
- **`spell_id`** stays as-is for the Cast button (story 102-2).
- The 3D dice tray (ADR-074) renders the WN attack roll unchanged — a WWN attack *is* a d20 throw.

## OTEL (the lie detector must prove the rider is flavor-only)

Per the OTEL Observability Principle and ADR-143's "prove native is OFF" requirement:

1. **The button → WN roll** emits the existing WN round spans (`{slug}.round.committed`,
   `encounter.beat_applied{source="wn_round"}`, `encounter.opponent_attack_resolved`) — the GM panel
   confirms a real roll resolved the action.
2. **The flavor rider must be observably inert.** When `player_action` is present on a WN combat
   throw, emit (or enrich the action-resolution span with) a marker proving the text was attached as
   narrator context **and did not enter mechanical resolution** — e.g.
   `wn.action.flavor_rider{attached=true, affected_mechanics=false}`. This is the lie-detector for
   *this* feature: it proves the chandelier text colored the prose without touching the dice. Without
   it, we cannot tell a flavor rider from a covert freeform-adjudication regression.
3. Pairs with 108-1's `wn.native_scaffolding_suppressed` (no fleeting tag / dial / reprisal rider).

## Scope

**In scope:** the player-facing WN *combat* action surface (`hp_depletion` confrontations under a WN
binding) — the buttons, the flavor rider's flavor-only contract, the bare-free-text lock, the action-id
wire contract, the rider OTEL.

**Out of scope (owned elsewhere):**
- Engine cut — removing native `apply_beat` scaffolding from `run_wn_round` → **108-1**.
- Room-sourced seater (no "Unknown Adversary") → **108-2**.
- Content de-nativization of combat defs → **108-3**.
- WWN dying/down window + solo-actuator gap → **recommended new story (see below)**.
- Dial chase / negotiation confrontations — keep the native dial engine (ADR-143 scope), untouched.

## Recommended epic-108 story (for the SM to materialize via `pf sprint`)

> **108-5 — WN combat player action surface: WN action buttons replace the native beat menu; flavor
> rider constrained flavor-only.** (`repos: ui,server`, `workflow: tdd`, `type: feature`,
> `depends_on: 108-1`, `priority: p1`)
>
> Replace the native beat tiles (Strike/Brace/Break Contact/Committed Blow) in the confrontation
> overlay with the WWN SRD action button set (Attack / Use Item / Move-Disengage / Cast); **no
> Brace/total-defense button** (not a WWN action). Each button fires a real WN roll via the bound
> `WithoutNumberRulesetModule` (108-1 resolution path), rendered in the ADR-074 dice tray. Retain
> `DICE_THROW.player_action` as the optional **RP-flavor rider** — narrator hook only, zero
> mechanical effect — and enforce that a bare combat free-text (no action button) does not resolve to
> a combat outcome. Add `wn.action.flavor_rider{affected_mechanics=false}` OTEL proving the rider
> stayed flavor-only. Depends on 108-1 (the engine must resolve a WN action, not a native beat,
> behind the button).

## Open dependency note for the SM

The cancellation of story **106-5** (commit `e5ae1fc8`) states its "real-WWN-dying-window work folds
into the WWN-first rework," but **epic-108 has no dying-window story**. The unsolved part — the WWN
d6 stabilize clock is a dead letter in solo play ("don't ship a clock nothing can advance,"
gm-decisions 2026-06-13) — is currently **unowned**. Recommend a companion story:

> **108-6 — WWN dying/down window + solo-actuator gap.** (`repos: server`, `workflow: tdd`,
> `type: feature`, `priority: p1`, **brainstorm flag**) Emit a real WWN mortally-wounded → d6-round
> stabilize → dead window under the WN round (not terminal-dead-only). **The solo-actuator gap is an
> OPEN design problem** (in solo play nothing can advance/act-on the stabilize clock — input is
> disabled once the PC is "out of the action") and must be brainstormed before implementation: a
> clock nothing can advance is worse than no clock. Server #846 already removed the dual-status
> *contradiction* (terminal-dead shows one coherent status); this story is the *actionable window*,
> not the contradiction fix.
