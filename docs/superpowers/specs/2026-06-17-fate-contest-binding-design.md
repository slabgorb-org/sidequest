# Fate Owns Its Confrontations — Add the Contest Mode, Re-author Off `opposed_check`, Rename the Dial Engine

- **Date:** 2026-06-17
- **Status:** Design — approved (Keith, 2026-06-17)
- **Story:** gates the Sprint 2624 implementation stories ("Ruleset-world combat & magic"), created from the plan that follows this spec
- **Implements / amends:** ADR-144 (Fate Core binding — now includes Contests), ADR-143 + SOUL "Bind the Ruleset, Don't Balance It", ADR-093 (opposed_check calibration — **scoped to the dial/WN family**), ADR-117 (the `RulesetModule` seam), ADR-033 (the dial/confrontation engine, here renamed)
- **Builds on:** F1c Fate conflict engine (`fate_conflict.py`), F4a Fate chargen, the WN extraction (ADR-142, `without_number.py`)
- **Repos:** `sidequest-server` (rename + Contest engine + dispatch + validator + OTEL), `sidequest-content` (re-author Fate-pack confrontations), no UI change required at design time (Contest reuses the FATE_ACTION surface)
- **Author:** Naomi Nagata (design mode) (Architect)

---

## Summary (the decision)

A Fate-bound pack is currently only *half* Fate. Chargen, sheets, and personal actions run on
Fate (4dF + ladder, `fate_conflict.py`), but its **structured confrontations** —
tea_and_murder's Polite Negotiation, tribunal, scandal, social_duel, gossip (~19 defs), and
spaghetti_western's one — are authored as **dial-engine `opposed_check` confrontations** whose
difficulty comes from `dial.compute_dc` (today the module is misnamed `native`). The opponent
rolls **d20** each beat; the contest is a **0→7 dial** hand-tuned under **ADR-093 opposed_check
calibration**. A 4dF system borrowing a d20 dial that *we* calibrate is precisely the
balance-the-native-mechanic trap **SOUL forbids** — and it is the mechanism behind the playtest's
open `[FATE/NOTE]` cross-ruleset-bleed finding.

This design makes a Fate pack's confrontations resolve through **Fate's own mechanics**, by
completing the binding rather than bending it. Four coordinated workstreams:

| # | Workstream | Essence |
|---|-----------|---------|
| **1** | **Rename the dial engine** | `NativeRulesetModule` → `DialRulesetModule`, slug `native` → `dial`; fail-loud the silent `"native"` defaults. Pure rename — **zero resolution change.** |
| **2** | **Add the Fate Contest mode** | New `fate_contest.py` implementing the standard SRD **Contest** (opposed 4dF, first to 3 victories, tie → boost). SRD implementation, not homebrew. |
| **3** | **Re-author Fate-pack confrontations** | The ~20 `opposed_check` social defs → Fate Contests. The 0→7 dial becomes the 0→3 victory tally. ADR-093 scoped to non-Fate. |
| **4** | **Guardrails** | A validator forbidding `opposed_check` in a Fate pack + fail-loud missing-ruleset defaults — so the bleed cannot return. |

The settled forks (Keith, 2026-06-17):

| Fork | Decision | Why |
|------|----------|-----|
| Scope | **C — close the bleed** (not tidy-only, not ratify) | The dial DC running inside Fate sessions is a real correctness/doctrine defect. |
| Confrontation model | **C1-b — add the Fate Contest mode** | These are RAW *Contests*, not Conflicts. Forcing them into stress/consequences (C1-a) is its own "make it fit." |
| Dial-engine identity | **`dial`** (renamed, kept) | It is not retirement-track — the WN family *structurally depends* on it. Honest name, not deletion. |

---

## §0 — Goal & the load-bearing invariant

**Goal.** A Fate-bound pack's confrontations resolve through Fate's own mechanics; the dial
engine is never reached on a Fate path; nothing in the tree reads as "the native ruleset is
still running."

**Invariant — WN is held byte-identical.** The dial engine, the `opposed_check` resolution mode,
and ADR-093 calibration stay **fully intact for the Without Number family.** This is not
optional politeness — it is structural:

- `WithoutNumberRulesetModule.compute_dc` **raises** (`without_number.py:150` — *"compute_dc is
  native-only"*). WN combat resolves vs **AC** (`attack_params`/`offer_difficulty`).
- `opposed_check` is a d20-**vs-DC** contest, and the only module implementing `compute_dc` is the
  dial engine. So road_warrior (cwn) and mutant_wasteland (awn), which author `opposed_check`
  defs, depend on `dial.compute_dc` **harder than Fate does** — their own module cannot produce
  that number.
- For WN, `opposed_check`-via-dial is **paradigm-consistent** (WN is itself a d20 system). It is
  not a bleed for WN; it is a legitimate shared contest mode and must stay.

**Therefore every change in this spec is gated on `ruleset == "fate"`.** Any removal of the
`opposed_check`→dial path that is *not* so gated regresses road_warrior + mutant_wasteland. That
is the single trap this design is built to avoid.

---

## §1 — Rename: `native` → `dial`

`NativeRulesetModule` → `DialRulesetModule`; slug `"native"` → `"dial"`. Update the registry
(`registry.py:13`), the docstring (which today falsely claims it backs "the Fate family" and is
"NOT a fallback for other modules"), and every `"native"`-as-slug string and comment. Reframe it
in docs as **the shared dial/beat/contest engine the WN family delegates `compute_dc` to** — not
a pack-bindable "default."

Make the three silent fallbacks **fail loud** (No Silent Fallbacks):
`pregen.py:434` (`getattr(…, "ruleset", "native") … else "native"`), `encounter_lifecycle.py:967`
(default param `ruleset_slug="native"`), `:1182` (`… else "native"`). A missing pack/ruleset is a
configuration error and must raise, not silently become the dial engine. After this, the dial
engine is reached by exactly **one** legitimate path: `confrontation.py:368`'s opposed-check DC.

Pure rename + fail-loud. **No resolution behavior changes for any ruleset.**

---

## §2 — The Fate Contest engine (the substantive work)

A new `fate_contest.py`, sibling to `fate_conflict.py` (the codebase already pairs these "one
tier over" modules; `fate_conflict.py` itself "mirrors wn_round.py one tier over"). Implements the
standard Fate Core **Contest**:

- **Structure:** participants compete for a *goal*; **no stress, no consequences** (a Contest is
  not harm — that is what distinguishes it from a Conflict).
- **Exchange:** each participant takes one action — 4dF + skill, aspects invocable — against the
  opposition (the F1a resolution primitive, reused).
- **Scoring (SRD — verify exact wording against the Fate SRD at implementation):** highest result
  scores **1 victory**; **succeed with style** while others don't → **2 victories**; a **tie** →
  no victory, but each tied participant gets a **boost**.
- **Win condition:** **first to 3 victories.** The `victories` tally is the Contest's analogue of
  the Conflict's stress track.
- **Integration:** reuse the existing `StructuredEncounter` / seat / participant scaffolding;
  routed exactly like Conflicts — the intent router seats it, `FATE_ACTION` dispatch handles it
  (extend `FateAction` / dispatch in `fate_action.py` + `encounter.py:152`). The confrontation
  def's `resolution_mode` selects contest vs conflict.
- **OTEL (lie-detector, mandatory per the OTEL Observability Principle):** `fate.contest.seeded`,
  `fate.contest.exchange` (per-exchange roll + victory delta), `fate.contest.resolved` (winner +
  final tally). The GM panel must be able to confirm the contest engine resolved, not the
  narrator.

This **completes** the Fate binding (Fate has Conflicts *and* Contests, as written) — it is SRD
implementation, the kind of work "Bind the Ruleset" endorses, not a homebrew system we must
balance.

---

## §3 — Content re-authoring: `opposed_check` → Fate Contest

The ~20 Fate-pack social confrontations (tea_and_murder Polite Negotiation / tribunal / scandal /
social_duel / gossip ≈19; spaghetti_western ×1) convert from the dial schema
(`resolution_mode: opposed_check`, `opponent_default_stats ≤ 10`, dial thresholds `7/7`,
beat-per-tactic) to the **Fate Contest schema** (opposing skill, victory target `3`, stakes /
goal). The 0→7 leverage/conviction **dial becomes the 0→3 victory tally**; each authored beat /
tactic becomes a per-exchange action; create-advantage and aspect invokes carry over natively.

**ADR-093 opposed_check calibration is explicitly scoped to non-Fate packs.** The calibration and
`tests/genre/test_confrontation_calibration.py` keep governing the **WN** `opposed_check` defs
(road_warrior, mutant_wasteland); they no longer apply to Fate, which after this has **no**
`opposed_check` defs to calibrate. (Contests need no such calibration — the 4dF-vs-4dF math is
the SRD's, not ours. That is the point.)

---

## §4 — Guardrails

A **content validator** that rejects a Fate-bound pack authoring an `opposed_check` (beat-surface)
confrontation def, with a loud, specific error pointing the author at the Contest schema. This is
the tripwire that keeps §0's invariant true going forward — the bleed cannot silently reappear
the next time someone authors a Fate confrontation. Plus the fail-loud conversions from §1.

---

## §5 — Testing & OTEL

- **WN regression guard (proves §0):** road_warrior + mutant_wasteland `opposed_check` resolution
  is unchanged — same DC via `dial.compute_dc`, ADR-093 calibration test still green.
- **Fate Contest behavior:** seat a contest, drive exchanges; assert the victory tally advances,
  first-to-3 terminates, tie → boost, succeed-with-style → 2 victories; assert the
  `fate.contest.*` spans fire (per the No-Source-Text-Wiring rule, drive the flow and assert
  spans, not source greps).
- **Validator:** a Fate pack carrying an `opposed_check` def fails to load loudly.
- **No-bleed integration:** a full tea_and_murder confrontation turn fires `fate.contest.*` spans
  and **zero** `dial`/`compute_dc` spans.

---

## §6 — Docs / ADR

- **ADR-144 amendment:** the Fate binding now includes the Contest mode; Fate-pack confrontations
  use Contests (or Conflicts), never `opposed_check`.
- **ADR-093 note:** opposed_check calibration is scoped to the dial/WN family; Fate is out.
- **ADR-033 / the dial engine:** record the `native` → `dial` rename and its honest role (the
  shared d20 contest/beat engine WN delegates `compute_dc` to).

---

## §7 — Out of scope / non-goals

- **No change to WN/cwn/awn/swn resolution.** The dial engine, `opposed_check`, and ADR-093 stay.
- **Not deleting the dial engine.** It is load-bearing for WN; this is a rename, not a retirement.
- **No Fate *Conflict* changes** beyond what hosting Contests requires — `fate_conflict.py` stress/
  consequence behavior is untouched.
- **No new UI screen.** Contests reuse the FATE_ACTION surface; client work, if any, is a
  follow-up.

---

## Open questions / risks

1. **SRD fidelity of the Contest scoring** — confirm the exact victory/tie/succeed-with-style
   wording against the Fate SRD during implementation (this spec states the working model; the SRD
   is the authority).
2. **Multi-beat → multi-exchange mapping** — some authored confrontations have rich per-beat
   tactics; converting each cleanly to a Contest exchange (and preserving the GM-panel legibility
   Sebastien/Jade value) is the content work's main subtlety.
3. **Dormant-vs-live confirmation** — bench-confirm in a live tea_and_murder session that today's
   `opposed_check` defs actually instantiate (vs. routing through FATE_ACTION), so the re-author is
   replacing a live path, not authoring around a dead one. (Audit strongly indicates live.)
