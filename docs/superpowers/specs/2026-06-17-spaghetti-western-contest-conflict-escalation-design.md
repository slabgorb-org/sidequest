---
title: "Spaghetti-Western Confrontation Taxonomy & the Contest→Conflict Escalation"
date: 2026-06-17
status: draft
deciders: ["Keith Avery", "Naomi (Dev, design mode)"]
related-adrs: [129, 143, 144, 116]
builds-on: "docs/superpowers/specs/2026-06-17-fate-contest-binding-design.md"
implementation-status: design-only
---

# Spaghetti-Western Confrontation Taxonomy & the Contest→Conflict Escalation

## Context

The Fate Contest binding (`2026-06-17-fate-contest-binding-design.md`, now in PRs) gave
spaghetti_western a Fate **Contest** engine and converted its sole `opposed_check` def
(`combat`/"Gunfight") to a Contest. Review flagged that this **mis-modeled the Gunfight**:
a Fate **Contest** has no stress and no consequences — a bloodless first-to-N race — but a
gunfight plainly inflicts harm. A gunfight is a Fate **Conflict** (stress tracks,
consequences, taken-out), not a Contest.

Settling that exposed the genre's real confrontation taxonomy and a mechanic SideQuest
does not yet have: a no-harm confrontation that **escalates into a fight mid-scene** ("the
card game ends in a cheater getting drawn on"). This spec defines the spaghetti_western
taxonomy and the one new engine mechanic it needs — an in-place **Contest→Conflict
escalation** — and explicitly scopes Poker **out**.

### Governing doctrine (Keith, 2026-06-17)

When binding an SRD, decide each "honor the native behavior?" call by layer:
**multiplayer/remote-substrate** mechanics (sealed all-at-once commits, presence, the
universal resolved signal, ADR-116 seating) are **preserved and the SRD bends to allow
them**; **genre resolution** mechanics become the SRD's. This spec applies that: a
gunfight's *resolution* is Fate's (Conflict), while the standoff/table *substrate* is kept.

## Decision — the taxonomy

| Confrontation | Resolution mode | Escalation to Gunfight |
|---|---|---|
| **Standoff** (`pre_combat`) | Fate **Contest** | **in-place flip** on the `draw` beat; **the drop + the flinch + situation aspects carry over** |
| **Gunfight** (`combat`) | Fate **Conflict** (stress/consequences) | — (this is the destination) |
| **Poker** (`social`) | **Unchanged** — ADR-129 real-card table engine | **scene reset** — table encounter ends, a fresh Gunfight Conflict seats, **nothing carries** |
| Tense Negotiation, Horseback Pursuit | unchanged (beat_selection) | out of scope |

### Why Poker is out of scope (deliberately)

Poker is **not** stray homebrew to retire — it is a deliberate "honest crunch" feature.
`sidequest/game/table/poker.py` deals a real shuffled 52-card deck without replacement,
ranks genuine 5-card hands, and `cheat`/`read` act on the real cards; its docstring states
the intent: *"Honest crunch where it's dramatic (Sebastien/Jade can see real card math)."*
It is wired end-to-end — `table_state` is projected per-seat through the perception
firewall (`confrontation.py::project_table_frame_for_seat`). Abstracting it into a 4dF
Fate Contest would delete that crunch. **We leave it exactly as is.**

Poker's def is `resolution_mode: table_resolution` (not `opposed_check`), so the Fate
guardrail validator does not flag it. The table engine's internal `accuse` opposed roll is
the table engine's own mechanic, not a confrontation-level `opposed_check` resolution mode;
it is **out of scope** and untouched.

**Reset, not flip.** When a poker scene turns violent ("a cheater gets drawn on"), the
poker table encounter **ends** and a **fresh Gunfight Conflict seats** — an ordinary scene
change via the existing seating path. **Nothing carries:** a stacked deck and a good read
are bound to the card-game fiction and do not steady a hand in a shootout. This needs **no
new engine work** — it is end-encounter-A / seat-encounter-B, which the system already does
for any scene change.

## The new mechanic — in-place Contest→Conflict escalation (Standoff only)

The single new build. A Standoff is a Fate Contest; its `draw` beat is the escalation
trigger. On `draw`, the **same encounter** transitions from Contest to Conflict in place
(encounter identity preserved — the panel does not tear down and re-seat).

### What the escalation does

1. **Clear `ContestState`.** `encounter.contest` is set to `None`; the Contest is over —
   not resolved with a victor, just superseded. The `draw` beat does **not** have to win
   the Contest first; it interrupts it.
2. **Bring the Conflict online on the same encounter.** Conflict stress/consequences come
   into play (read from each actor's `FateSheet`, per the existing Fate Conflict engine,
   `run_fate_exchange`). Stress starts **fresh** — nobody has been shot yet.
3. **Preserve participants.** The standoff's seated actors (player + Other) remain the
   Conflict's combatants; ADR-116's "a confrontation requires an Other" continues to hold.
4. **Carry the tactical edge as opening Conflict position** — the load-bearing rule. The
   standoff's *mechanical outcomes* become the Conflict's opening advantages:
   - **Got the drop** (the actor who initiated/led the `draw`) → acts **first** in the
     Conflict's initiative + a `Got the Drop` **boost** (single free invoke).
   - **Made him flinch** (the `flinch` beat landed — a `create_advantage` in Contest terms
     placing a `Rattled`/`Flinched First` aspect on the Other) → that aspect rides into the
     Conflict **on the Other**, with its free invoke intact.
   - **Generic situation aspects + boosts** created during the standoff (`size_up`,
     `bluff`) carry into the Conflict as opening situation aspects.
   - **Fate points are untouched** (the standoff did not spend the Conflict's economy).
5. **Emit `fate.contest.escalated`** (OTEL): `{from: "contest", to: "conflict",
   encounter_type, initiator, carried_aspects: [...], got_drop: <actor>}` — the GM-panel
   lie-detector proof that the escalation fired and *what* carried, so a narrator can't
   claim "he got the drop" with no mechanical backing.

### Standoff beats → Fate Contest actions (content authoring)

| Beat | Fate action | Effect |
|---|---|---|
| `size_up` | overcome / create_advantage | build a situation aspect (e.g. `Sun at His Back`) |
| `bluff` | create_advantage (Deceive) | aspect on the Other or self |
| `flinch` | create_advantage | place `Rattled`/`Flinched First` on the Other (free invoke) |
| `draw` | **escalation trigger** | flips Contest→Conflict; carries per the rule above |

## Components & data flow

```
Standoff seated  → encounter.contest = ContestState (existing seating, resolution_mode: contest)
   player turns  → run_fate_contest_exchange (existing Contest engine; aspects/boosts accrue on the encounter)
   `draw` beat   → escalate_contest_to_conflict(encounter, snapshot, ...)   ← NEW
                     • clear encounter.contest
                     • carry situation aspects + boosts; mint Got-the-Drop boost + initiative
                     • emit fate.contest.escalated span
   subsequent    → run_fate_exchange (existing Fate Conflict engine; stress/consequences)
```

- **New function:** `escalate_contest_to_conflict(...)` in `sidequest/server/dispatch/fate_contest.py`
  (it already owns the Contest lifecycle and imports the Conflict seam lazily). Single,
  well-bounded responsibility: transition one encounter's mode, carry the edge, emit the span.
- **Trigger wiring:** the `draw` beat commit, when the encounter is contest-mode for a
  Fate pack, calls the escalation instead of a normal Contest exchange. Author-declared on
  the beat (e.g. `escalates: true`) so it is content-driven, not a hard-coded beat id.
- **Reuses, does not reinvent:** seating + Other invariant (ADR-116, `_requires_opponent`),
  the Conflict engine (`run_fate_exchange`), situation-aspect storage on the encounter,
  the boost/free-invoke primitive, and the contest-span family.

## Error handling / invariants

- **Escalation only from a contest-mode encounter** under a Fate ruleset; otherwise raise
  loud (No Silent Fallbacks) — a `draw`-escalation on a non-contest/non-Fate encounter is a
  config/author bug.
- **Other must survive the transition** — the Conflict requires the same seated Other
  (ADR-116). If the standoff somehow has no Other at `draw`, fail loud (the contest could
  not have existed without one).
- **Carry is deterministic** — given the same standoff aspect/boost state, the same opening
  Conflict position results (seeded RNG only for any rolled component); pinned by tests.
- **Poker reset carries nothing** — asserted negatively (no poker aspect/strength leaks
  into the seated Gunfight).

## Testing

- **Contest→Conflict flip:** drive a Standoff Contest, land `flinch` (aspect on Other) and
  build a situation aspect, fire `draw`; assert `encounter.contest is None`, the Conflict
  engine now resolves, the `Flinched First` aspect + situation aspects are present on the
  Conflict with free invokes intact, the drop-getter has initiative + a `Got the Drop`
  boost, stress is fresh, and `fate.contest.escalated` fired with the carried set.
- **Poker reset:** with an active poker `table_state`, trigger violence; assert the table
  encounter ends and a fresh Gunfight Conflict seats with **no** carried poker state (no
  hand-strength, no table aspects), and **no** `fate.contest.escalated` span (it's a reset,
  not a flip).
- **Gunfight is a Conflict:** the converted `combat` def resolves through `run_fate_exchange`
  (stress/consequences), not the Contest engine; `attack` is a legal Conflict action.
- **Content validation:** spaghetti_western loads; Standoff is contest-mode with a
  `draw` escalation beat; Gunfight carries no `resolution_mode: contest`; Poker unchanged.
- **Wiring test:** the `draw` escalation is reachable from the real beat-commit dispatch
  path (drive a beat commit, assert the escalation fired) — not a source-text grep.

## Content changes (spaghetti_western `rules.yaml`)

- **Standoff:** add `resolution_mode: contest`; mark the `draw` beat as the escalation
  trigger (`escalates: true` or equivalent); ensure `player_metric`/`opponent_metric`
  thresholds suit a short nerves contest.
- **Gunfight:** remove `resolution_mode: contest` → routes to the Fate Conflict engine.
- **Poker:** unchanged.

## Out of scope / non-goals

- **Poker is untouched** (cards, cheat/read, accuse, the table engine) — by decision.
- **No N-party Fate Contest.** The Contest engine stays 2-party; this spec does not
  generalize it (Poker, the multi-seat case, stays on the table engine).
- **Generic cross-genre escalation.** The Contest→Conflict flip is genre-general in
  principle (a tense negotiation could turn into a fight anywhere), but we build and prove
  it for spaghetti_western's Standoff→Gunfight first. Generalization is a fast-follow.
- **Depends on** the Fate Contest binding (`2026-06-17-fate-contest-binding-design.md`)
  being merged before implementation — it provides `ContestState`, the Contest engine, and
  the Fate Conflict seam this escalation bridges.

## Open questions

None — the design is settled. Implementation sequencing waits on the contest-binding PRs
merging to `develop`.
