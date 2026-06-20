# Epic 152: WN combat owns the full WWN action set — cast + Total Defense + Fighting Withdrawal via WWN math, not native beats (complete 108-8)

## Overview

Completes the WWN combat de-nativization started in epic-108 (ADR-143, "Bind the
Ruleset, Don't Balance It"). 108-3 stripped **all** native combat beats off WWN
`hp_depletion` confrontation defs (`cdef.beats == []`); 108-8 synthesized **only**
the player `attack` action. Every other action a WWN combat round needs — `cast_spell`,
the defensive verbs, and the **opponent's own strike** — was stripped but never
synthesized, so each fell into the empty-cdef lookup and raised `unknown beat_id …
available: []` (or silently skipped, for the opponent) before a round could resolve.
This epic synthesizes the rest of the action set **as genuine WWN mechanics**, not as
ported native scaffolding.

**Priority:** P1
**Repo:** server
**Stories:** 5 (13 pts done · 3 pts remaining · 5 pts canceled)

**Story status (2026-06-20):**

| Story | Pts | Status | Summary |
|-------|-----|--------|---------|
| 152-1 | 5 | done | WWN defensive actions — remove native brace/break_contact reprisal-mitigation; add Total Defense (+2 AC / Shock immunity) + Fighting Withdrawal/Run. **Absorbed 152-4's opponent-strike synthesis** as a blocking precondition. (PR #995) |
| 152-2 | 5 | done | Synthesize the `cast_spell` action → route to the existing WWN cast spine on a zero-beat def. (PR #996) |
| 152-3 | 3 | done | Restore chargen class-surface tests; reconcile `class_moves` to the de-nativized WN action set. |
| 152-4 | 5 | **canceled** | Synthesize the WN **opponent** attack. **Stale — shipped inside 152-1.** Title's "prerequisite for 152-1" was the tell: a prerequisite worked after its dependent gets absorbed by it. Verified green on HEAD (`test_wwn_opponent_attacks_on_its_slot_with_a_synthesized_strike`). |
| 152-5 | 3 | backlog | MP WN-round wire: 2nd commit misresolves to the 1st PC's seat (round never fires) + non-hermetic narrator transport on the sealed-commit handler path. |

## Planning Documents

| Document | Relevant Sections |
|----------|-------------------|
| **WN-full-action-set design** (`docs/superpowers/specs/2026-06-20-wn-full-action-set-design.md`) | TL;DR + measurement (the 71/3 RED breakdown); "Doctrine ruling and a course correction" (cast vs brace/break_contact); decomposition boundary (epic-152 vs 125-8 test-debt vs separate roots) |
| **ADR-143** Bind the Ruleset, Don't Balance It (`docs/adr/143-*.md`) | The governing doctrine — the WN engine *replaces* the native combat engine; native mechanics are removed, never balanced against the binding |
| **ADR-142** Without Number core extraction (`docs/adr/142-*.md`) | `without_number.py` honest base + reparented swn/wwn/cwn/awn siblings — the module this epic's synthesis is gated on (`isinstance(WithoutNumberRulesetModule)`) |
| **ADR-114** Ablative HP substrate (`docs/adr/114-*.md`) | `creature_core.py` `HpPool`; the synthesized `attack` lands weapon dice on ablative HP via the strike channel |
| **ADR-117** Pluggable ruleset module system (`docs/adr/117-*.md`) | The `RulesetModule` seam / registry the WWN binding resolves through |
| **ADR-116** A confrontation requires an Other (`docs/adr/116-*.md`) | The opponent-seating invariant the synthesized opponent strike depends on (no Other → no reprisal) |
| **152-1 session archive** (`sprint/archive/152-1-session.md`) | Lines 191/219-222/246 — the record that opponent-strike synthesis was pulled into 152-1; the canonical authority that 152-4 is stale |

## Background

**Why this epic exists.** Epic-108 de-nativized WWN combat per ADR-143: a pack that
binds a Without Number ruleset must run on that ruleset's already-balanced math, with
the native beat/dial scaffolding *removed* from its combat path — not layered on top and
tuned. 108-3 did the removal (stripped every native combat beat off WWN defs). 108-8 did
only part of the rebuild (synthesized the player `attack`). The gap between those two left
a **live, player-facing outage**: in WWN combat across `caverns_and_claudes`,
`elemental_harmony`, `heavy_metal`, and `barsoom` (red since ~2026-06-15) you could attack
and use an item, but you could **not** cast a spell, brace, or disengage — and the **Other
dealt no damage** (its strike beat was stripped too, so its reprisal silently skipped with
`dice.opponent_reprisal_skipped reason=no_strike_beat`, PC_LOST=0).

**The course correction (Keith, 2026-06-20).** The first plan was to *synthesize the
native `brace`/`break_contact` beats* and restore the 106-2 reprisal-mitigation model
(tier-delta HP mitigation, whole-attack prevention, a per-beat opponent reprisal). That was
caught before any code shipped — *"why are we trying to shape native into SRD?"* It is the
exact ADR-143 trap: porting native mechanics into a bound ruleset. WWN has **none** of
those constructs. WWN defines defense as **Armor Class manipulation** (SRD §2.4.4) and
combat as **side-initiative** (§2.4.1) — the opponent attacks once on its own turn, with no
per-beat reprisal. So the resolution splits by whether each action is a *real* WWN verb:

- **`cast`** — a real WWN action (SRD §4.2). Route a synthesized `cast_spell` commit to the
  pre-existing WWN cast spine before the cdef lookup (152-2).
- **`brace` / `break_contact`** — native-only. **Remove** the scaffolding; replace with the
  genuine WWN defensive verbs: **Total Defense** (Instant Action → +2 Melee/Ranged AC +
  Shock immunity until next turn, resolved by raising the AC the opponent's d20 must clear —
  no damage-reduction number) and **Fighting Withdrawal / Run** (disengage so a following Run
  provokes no free attack; does *not* cancel the opponent's own-turn attack). All magnitudes
  SRD-verbatim — nothing invented (152-1).
- **opponent strike** — synthesized like the player's `attack`, so the Other attacks once on
  its slot vs the defender's (possibly Total-Defense-boosted) AC. This was 152-4's scope; it
  was a blocking precondition for testing Total Defense and was implemented inside 152-1.

**Scope boundaries vs adjacent work.** Pure stale-id test-debt (`committed_blow`/`strike`
→`attack` swaps, loader assertion flips) stays in **125-8** (epic-125) — its AC1 was
narrowed because the synthesis-gated tests moved here. Separate roots surfaced in the same
2026-06-20 sweep are *not* this epic: chargen `[None×6]` (→ 152-3), e2e chargen protocol
drift, Fate-SRD catalog load, and deprecated-world skips each got their own home.

## Technical Architecture

The mechanism is **transient action-beat synthesis at the dispatch call site**, gated on
the WWN binding. A WN combat def has `cdef.beats == []`; instead of looking the action up
in that empty pool, a WN-gated branch synthesizes a transient `BeatDef` for the action and
resolves it through the existing WWN math. Native packs route the *same* ids through the
normal cdef lookup, so nothing about native combat changes.

**Key files:**

| File | Role |
|------|------|
| `sidequest/game/beat_filter.py` | The closed action allowlist `_WN_ACTION_BEAT_IDS = {attack, total_defense, fighting_withdrawal, run}` + `wn_action_beat()` (synthesizes the transient `BeatDef`s) + `is_wn_action_beat` / `is_wn_flee_action` / `is_wn_nonoffensive_action`. `attack` carries a `strike` channel (weapon dice → ablative HP); the defensive/move verbs carry **no** strike channel (`BeatKind.push`). `cast_spell` is **deliberately NOT** in the allowlist — cast routing is WWN-ruleset-specific (the cast spine has no non-WWN arm), so each call site gates it on the `wwn` binding and a `cast_spell` on any other ruleset stays a loud unknown-beat raise. |
| `sidequest/server/dispatch/dice.py` | Player-commit synthesis (`isinstance(ruleset, WithoutNumberRulesetModule) and is_wn_action_beat(...)` ahead of the empty-cdef lookup); the WWN cast spine; the `is_item_use_beat` transient intercept it mirrors; `_resolve_opponent_reprisal` (≈1992) — synthesizes the **opponent's** strike on a zero-beat def (≈2052) and reads the defender's sealed posture via `_defensive_posture_for_reprisal` (Total Defense → +2 AC + Shock immunity; full damage on a connecting hit; no whole-attack prevent). |
| `sidequest/server/dispatch/wn_round.py` | The WN sealed-round walk: own-turn slot attack calls `_resolve_opponent_reprisal` (≈302); the flee path provokes the `source="opportunity_attack"` free attack (≈423, guarded by `encounter.resolved`/target-downed so a downed fleer isn't re-attacked); player-slot non-offensive intercept for `run`/`fighting_withdrawal`/`total_defense` (≈461) ahead of the strike resolver. |
| `sidequest/game/ruleset/without_number.py`, `wwn.py` | `resolve_opponent_attack` (d20 + to-hit vs target AC) and the AC math that Total Defense's +2 feeds into — the "balanced math" the binding inherits. |

**Action → resolution path:**

```
player commit (beat_id) on a WWN hp_depletion cdef (cdef.beats == [])
  ├─ is_item_use_beat            → item-use transient intercept
  ├─ is_wn_nonoffensive_action   → wn_round flee/posture intercept (no strike; AC posture / disengage)
  ├─ is_wn_action_beat(attack)   → wn_action_beat("attack") → strike → ablative HP
  ├─ cast_spell (+ wwn gate)     → WWN cast spine (spell_id validate, catalog resolve, cast)
  └─ else                        → empty-cdef lookup → loud DiceDispatchError (No Silent Fallbacks)

opponent turn (own slot OR opportunity-attack on flee)
  └─ _resolve_opponent_reprisal → synthesize opponent strike (wn_action_beat) →
       resolve_opponent_attack(d20 vs target_ac + Total-Defense delta) → ablative HP
```

**Invariants every story preserves (from 108-8):** the allowlist is **closed** (a bogus
id still raises); synthesis is gated on `isinstance(ruleset, WithoutNumberRulesetModule)`
so native packs resolve authored ids on the native engine; and every defensive/opponent
decision emits an OTEL span (the opponent-attack span carries `defender_beat`, `ac_delta`,
and `source` = `opponent_reprisal` | `opportunity_attack`) — the GM-panel lie detector.

## Cross-Epic Dependencies

**Depends on:**
- **Epic 108** (WWN combat de-nativization) — 108-3 stripped the native beats this epic
  re-synthesizes; 108-8 established the `attack`-synthesis pattern (allowlist + WWN gate +
  `wn_action_beat`) that every 152 story mirrors.
- **Epic 142** (Without Number core extraction) — provides `WithoutNumberRulesetModule`, the
  `isinstance` gate all synthesis hangs off.
- **Epic 114 / ADR-114** (ablative HP) — the `HpPool` the synthesized `attack` and opponent
  strike deal damage into.

**Depended on by:**
- **Epic 125** (125-8 test-debt) — its AC1 was narrowed because the synthesis-gated WWN tests
  are owned here; 125-8 covers only the pure stale-id / loader-assertion edits.
- **152-5** (MP WN-round wire) — sits on the now-complete single-player WN round; fixes the
  2nd-commit-misresolves-to-1st-seat bug and the non-hermetic narrator transport on the
  sealed-commit handler path.

---
_Authored by Architect (The Man in Black) 2026-06-20 via `/pf-context create epic 152`. Replaces the auto-generated stub; 152-4 canceled as stale (absorbed by 152-1) during the same triage._
