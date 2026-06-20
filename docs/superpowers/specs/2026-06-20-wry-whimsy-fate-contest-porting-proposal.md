# Proposal: Port wry_whimsy's Confrontation Catalog to Fate Schema (add `resolution_mode: contest`)

**Status:** PROPOSAL — awaiting Keith's crunch decision. No edits made.
**Author:** GM (playtest-derived, 150-8 oz)
**Date:** 2026-06-20
**Origin:** ping-pong finding `WRY-WHIMSY-NO-FATE-CONTEST-DEFS` (150-8 `wry_whimsy/oz` playtest)
**SOUL/ADR frame:** "Bind the Ruleset, Don't Balance It" (ADR-144 REPLACE); content-side de-nativization sibling of the 2026-06-17 §2/§3 migration already applied to tea_and_murder + spaghetti_western.

---

## 1. Problem (one paragraph)

`wry_whimsy` declares `ruleset: fate` (`rules.yaml:19`) but its entire `confrontations:` catalog is still authored in the **retired native-dial schema** — `audience`, `wit_duel`, `escape`, each with dual 0→10 dial metrics (`standing`/`verdict`/`upper_hand`), native beat `kind: strike/angle/brace/push`, and native stat checks `WIT/HEART/GUILE/NERVE`. **None declare `resolution_mode`.** Because `resolution_mode: contest` is a *per-genre authored* ConfrontationDef property (read at `genre/loader.py:730`, validated `genre/models/rules.py:547`) and **not** a Fate-ruleset built-in, the Fate engine has no contest def to seat and falls through to a generic Fate **Conflict** for every opposed action. Net effect: a Fate **Contest** (opposed 4dF, first-to-N, no stress) is **structurally unreachable on every wry_whimsy world** (gulliver, oz, wonderland). This is the root cause of the un-verifiable #936/#985/#990 across the 150-7/150-8 sweep, and it corrects the earlier "high-menace tone" hypothesis (oz is *low*-menace and still can't reach a Contest).

**Scope of the gap:** of the 4 Fate genres, only **spaghetti_western + tea_and_murder** were ported (declare `resolution_mode`). **wry_whimsy + pulp_noir were not.** This proposal covers wry_whimsy; pulp_noir is the same fix and should be tracked alongside.

## 2. The template (already shipped, mirror it)

tea_and_murder's `social_duel` (`rules.yaml:396`) is the canonical Fate Contest shape:

```yaml
  - type: social_duel
    label: Duel of Wits
    intent_verbs: [insult, riposte, parry, slight, retort, snub]
    on_intent_mismatch: warn
    category: social
    resolution_mode: contest               # <-- the missing key
    player_metric:    { name: barbs_landed, starting: 0, threshold: 3 }   # first-to-3
    opponent_metric:  { name: barbs_landed, starting: 0, threshold: 3 }
    beats:                                  # display-only stubs: id + label + narrator_hint ONLY
      - { id: riposte,          label: Verbal Riposte,      narrator_hint: "A cutting remark, perfectly timed." }
      - { id: appeal_propriety, label: Appeal to Propriety, narrator_hint: "Invoke social convention to embarrass the opponent." }
      - { id: composure,        label: Maintain Composure,  narrator_hint: "Recover poise — resist the next barb." }
      - { id: concede,          label: Concede Gracefully,  narrator_hint: "Duel ends — withdraw with dignity intact." }
    mood: mystery
```

Key invariants of a contest def (per `ConfrontationDef._validate`, spec 2026-06-17 §2):
- `resolution_mode: contest` ⟺ every beat is a **display-only stub** — `id` + `label` + `narrator_hint`, **no dial fields** (`kind`, `base`, `stat_check`, `risk`, `effect`, `consequence` are all stripped). A contest beat carrying a dial field fails validation.
- Resolution is by the 4dF exchange engine; the **player picks a Fate skill at throw time** (Rapport/Provoke/Will/Empathy…), so the per-beat `stat_check` dissolves — the native `WIT/HEART/GUILE/NERVE` bindings are *removed*, not converted.
- Asymmetric stakes (a head start) live on `opponent_metric.starting` (see tea_and_murder's `scandal`, which seeds `exposure` at 2/3).
- **Beat `id`s survive** for the world-class Abilities tab / progression references — preserve them.

wry_whimsy already uses the standard Fate skill ladder (`rules.yaml:29` — Rapport 4, Empathy 3, Will 3, … Provoke 1), so no skill-system work is needed; the contest just rolls those.

## 3. Proposed changes to `wry_whimsy/rules.yaml`

### 3a. `wit_duel` → Fate Contest (clear yes — it is literally a contest)

The current `wit_duel` is a battle of wits with `upper_hand` vs `upper_hand` dials and a concede beat that already says *"you bow out of the **contest** gracefully."* It is a Fate Contest mis-authored as a native dial duel. Port:

```yaml
  - type: wit_duel
    label: "Wit-Duel"
    intent_verbs: [riddle, retort, quip, outwit, banter, puzzle, counter, answer]
    on_intent_mismatch: reprompt
    category: social
    resolution_mode: contest
    player_metric:   { name: upper_hand, starting: 0, threshold: 3 }
    opponent_metric: { name: upper_hand, starting: 0, threshold: 3 }
    beats:                                  # IDs preserved; dial fields stripped
      - { id: sharp_retort,       label: "Sharp Retort",        narrator_hint: "A clean, fast reversal. The interlocutor did not expect to be answered so well." }
      - { id: pose_a_riddle,      label: "Pose a Riddle",       narrator_hint: "High-variance. A good riddle traps them; a bad one is a gift." }
      - { id: feign_confusion,    label: "Feign Confusion",     narrator_hint: "The traveler plays dumb on purpose. Banked leverage, not an immediate hit." }
      - { id: keep_a_straight_face, label: "Keep a Straight Face", narrator_hint: "Unflappable. The absurdity rolls off and leaves the opponent looking foolish." }
      - { id: concede_the_game,   label: "Concede the Game",    narrator_hint: "The traveler declines to win, and the contest simply ends. Dignity intact." }
    mood: nonsense
```

### 3b. `audience` (Trial) → Fate Contest (recommended yes)

A trial before a humbug authority where you race to win standing before the verdict tightens is a textbook Fate Contest (you vs the court, first to 3). Port the dual `standing`/`verdict` dials to first-to-3 metrics; preserve `escalates_to: chase`, `mood: courtroom`, and all beat IDs (`state_your_case`, `appeal_to_fairness`, `spot_the_contradiction`, `hold_your_nerve`, `refuse_the_premise`) as display stubs.

> **Note for Keith:** `audience` has higher design surface than `wit_duel` — `spot_the_contradiction` banks a "Court's Own Rule Turned" tag and `refuse_the_premise` is a `resolution: true` walk-out. In a Fate Contest those become *narrative* outcomes of exchanges / a Concede, not dial mechanics. If you want the "bank a contradiction for later" lever to stay mechanical, that's a CreateAdvantage aspect in Fate, not a beat — worth a decision.

### 3c. `escape` (chase) → Contest? (open question — your call)

A flight through dream-logic terrain is a chase, which Fate also models as a Contest (race to get away vs the pursuer closing). Plausible to port the same way, but chase semantics (zones, distance) may warrant `resolution_mode: contest` with different metric naming, or staying conflict-adjacent. **Flagging, not recommending — your decision on whether escape becomes a contest now or later.**

## 4. What this does NOT change

- **Fate Conflicts still work as-is.** wry_whimsy already seats a generic Fate Conflict for coercive/menacing opposition (verified on oz: attack→stress→consequence ablation, DEFEND barrier). Oz menace that "enchants/enslaves" legitimately routes to a Conflict. This proposal only *adds* the missing Contest path; it removes nothing.
- **No skill-system or character-sheet work** — wry_whimsy's Fate ladder is already in place.
- **No engine code** — the Fate Contest engine (`dispatch/fate_contest.py`), narrator contest zone (`narrator.py:394`), and seating already exist and are exercised on tea_and_murder/glenross. This is content-only.

## 5. Risks / things to check before authoring

1. **Beat-ID references.** Confirm wry_whimsy `progression.yaml` / abilities don't bind to the native beat *mechanics* (base/kind). The IDs survive as stubs; only the dial fields are stripped. (tea_and_murder explicitly preserves IDs for the Abilities tab for this reason.)
2. **Intent-router selection.** With contest defs present, confirm the router escalates a wits/argument intent to `wit_duel`/`audience` (contest) rather than the generic conflict. This is the behavior that was missing in the 150-8 playtest; the porting is the precondition, but a quick re-verify on oz after authoring is warranted.
3. **`on_intent_mismatch`.** wry_whimsy currently uses `reprompt`; tea_and_murder's contests use `warn` (cosy-genre, per the 2026-05-20 intent-validator spec). Decide whether wry_whimsy contests should `warn` (looser, lets whimsical free-text through) or keep `reprompt`.
4. **Optional loader guard (FIXER, separate):** a Fate genre shipping native-schema confrontation defs with no `resolution_mode` currently fails silently into a generic conflict. A loader validation warning ("Fate genre X has native-schema confrontation def Y with no resolution_mode") would catch the pulp_noir/wry_whimsy class of gap loudly (per "No Silent Fallbacks"). Tracked in the ping-pong finding as a secondary item.

## 6. Verification plan (after authoring)

Re-run the 150-8 oz playtest path: a wits/argument action vs an authority should seat a `wit_duel`/`audience` **Contest** (`cdef.resolution_mode: contest`, `encounter.contest` present), and driving Overcomes to first-to-3 should advance `encounter.contest.player_victories` (#936), narrate each exchange without the `build_encounter_context` crash (#985/#990), and offer Overcome/CA-only (not Attack/Concede) action gating (#987). At that point the wry_whimsy 150-x Contest ACs become verifiable on-genre instead of needing tea_and_murder/glenross.
