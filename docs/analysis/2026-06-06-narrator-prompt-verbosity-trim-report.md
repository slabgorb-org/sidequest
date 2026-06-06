# Narrator Static-Prose Verbosity Trim — Before/After Report

**Date:** 2026-06-06
**Author:** Dev (Bicycle Repair Man)
**Scope:** Option **A** — concision pass on the **stable** narrator prose `.md` files (the 1h cache prefix).
**Outcome:** **Net zero changes applied — by design.** See below.
**Companion doc:** [`2026-06-06-narrator-per-turn-cache-write-anatomy.md`](./2026-06-06-narrator-per-turn-cache-write-anatomy.md) — the cost/cache forensics that motivated this.

---

## TL;DR (read this first)

I did the pass. **The verbose "redundancy" in these prompts is mostly *deliberate, test-protected regression-fingerprinting*, not bloat — and there is essentially nothing safe to trim here for meaningful gain.**

The proof landed when my one trial cut — consolidating four restating "Patients on a sickbed count…" sentences in `output_only.md` into a single parenthetical — **tripped two tests** that guard that exact text as a load-bearing fingerprint. Their comment is explicit:

> *"ADR-111 §Alternatives B rejected compression because these specifics ARE the regression fingerprints — so they must survive verbatim into the constants. If the implementer compressed the prose into a one-line rule (rejected), this assertion fails — the bug-report specificity is the regression detector, not stylistic flavor."*
> — `tests/agents/test_57_4_recency_guardrails_migration.py:185-198`

I had done **precisely** the thing ADR-111 §Alternatives B rejected. **I reverted it.** The four sentences each encode a past NPC-tracking regression; the verbosity is the safety net.

**Two reasons this was never going to pay off anyway:**
1. **Wrong cost tier.** These files are in the **read** tier ($0.30/M). A hypothetical 20% cut ≈ 1.1k tok × $0.30/M ≈ **$0.0003/turn** (~$0.03 / 85-turn session). The per-turn cost lever is the **volatile `game_state` snapshot** (write tier, ~$0.04/turn) — the RAG story, not these files.
2. **The content is the moat.** This is the surface that has to "fool a career GM." Its specificity was bought with playtest regressions and is pinned by content-guarding tests across `test_57_4`, `test_61_12`, and `test_narrator`.

**Recommendation: do not trim the stable narrator prose. The lever is RAG-rebalancing the volatile `game_state` snapshot** (companion doc, §RAG rebalance) — a server change, not a prose edit.

---

## Methodology

1. Identified the stable set from `prompt_framework/bucket.py:28` (`STABLE_SECTION_NAMES`) ↔ `narrator_prompts/__init__.py` filenames.
2. Snapshotted pristine copies to `/tmp/prompt-trim-before/`.
3. Scanned for intra-file restatement and same-prefix cross-file duplication.
4. Trialed the single clearest "pure restatement" cut → it broke protected tests → reverted.
5. Cross-checked every remaining candidate against the test suite's content guards.

### Stable set baseline

| File | chars | words | ~tok | section |
|---|---|---|---|---|
| identity.md | 210 | 37 | 52 | `narrator_identity` |
| constraints.md | 792 | 110 | 198 | `narrator_constraints` |
| agency.md | 1,269 | 199 | 317 | `narrator_agency` |
| consequences.md | 398 | 69 | 99 | `narrator_consequences` |
| **output_only.md** | **15,080** | **2,066** | **3,770** | `output_format` |
| output_style.md | 667 | 113 | 166 | `narrator_output_style` |
| referral_rule.md | 324 | 63 | 81 | `narrator_referral_rule` |
| pov_rules.md | 2,788 | 464 | 697 | `narrator_pov_rules` |
| dialogue_rules.md | 756 | 129 | 189 | `narrator_dialogue` |
| **TOTAL** | **22,284** | **3,244** | **~5,570** | |

`output_only.md` is 75% of the set — a structured-output *contract* covering ~22 mechanics at ~90 words each. Detailed by necessity.

> **Not in scope A (volatile / User bucket):** `combat_rules.md`, `chase_rules.md`, `magic_output_rules.md`, `AUDIT.md`. Trimming these is Option **B** (the in-tail write lever) — a separate decision, and subject to the same fingerprint-protection caution.

---

## ATTEMPTED → REVERTED — `output_only.md` RECURRING-PRESENCE consolidation

**Trialed, then reverted. File is pristine. Net change: none.**

**Trial edit (what I tried):** four restating sentences → one parenthetical, keeping the concrete examples.

> *Before:* …every turn they remain onstage. **Patients on a sickbed count. Parents at a hearth count. Children at a doorway count. Siblings in the next room count.** A name in prose but absent…
>
> *Tried:* …every turn they remain onstage **(a patient on a sickbed, a parent at a hearth, a sibling in the next room all count)**. A name in prose but absent…

**Why reverted:** the literal `"Patients on a sickbed count"` is a protected ADR-111 regression fingerprint asserted by:
- `tests/agents/test_57_4_recency_guardrails_migration.py:191,300`
- `tests/agents/test_61_12_output_format_compaction.py:544`

The trial would have saved 3 words and failed 2 tests. Correctly so — the specificity *is* the regression detector.

---

## Candidate menu (cross-checked against the test guards)

For completeness — and so you can overrule me if you want. Each is small, and I recommend **against** most.

| # | Change | Δ words | Test-safe? | Risk | Rec |
|---|---|---|---|---|---|
| C2 | `output_only.md` drop the closing 3rd "ALWAYS emit the game_patch block. It is mandatory." (open already states it) | −8 | ✅ no test on this literal | MED — recency reinforcement of a high-violation rule | **Keep** |
| C3 | `output_style.md:6` drop "Dialogue: snappy. One exchange." (dup of `dialogue_rules.md:2,4`) | −6 | ✅ | LOW–MED — breaks the length cheat-sheet symmetry | **Keep** |
| C4 | `dialogue_rules.md:10` drop "Short exchanges. Real people don't monologue." (3rd brevity cue) | −6 | ✅ | LOW | **Optional** |
| C5 | `dialogue_rules.md:12` drop "Present what the NPC says… Let the player decide their reply." (restates agency) | −12 | ✅ (the guarded line `:11` "NEVER speak for the player character" stays — `test_narrator.py:321`) | MED — localized reinforcement of **The Test** | **Keep** |

**If you approved every one: ~−32 words (~0.6%), ~$0.00001/turn.** Not worth the regression surface.

---

## The real finding (this is the value of the exercise)

The static narrator prose is **already at its floor**. What reads as "verbose redundancy" is, on inspection, three deliberate things — all of which *should* stay:

1. **Regression fingerprints** — verbatim phrases pinned by tests so a future refactor can't quietly delete a hard-won NPC-tracking / fabrication / perception rule (ADR-111 §Alternatives B explicitly **rejected** compressing these).
2. **Primacy/recency bookends** — high-violation rules (emit the block; anti-fabrication; agency) stated at top *and* bottom, a standard compliance pattern.
3. **Concrete examples** — "the merchant takes your sword", "Laverne says…", the "behind him" POV case (the live #718 fix) — concreteness drives LLM compliance better than abstract rules.

Cutting any of these trades narrator quality — the one thing the project can't afford to lose — for fractions of a cent. **Wrong trade.**

## Bottom line

- **Applied: nothing.** The files are pristine (`git status` clean under `narrator_prompts/`).
- **Recommendation:** leave the stable prose alone. If per-turn cost is the goal, pursue the **RAG-rebalance of the `game_state` snapshot** (companion doc) — that's the write-tier lever with real dollars behind it.
- **If you still want a token trim:** Option **B** (the volatile `combat`/`chase`/`magic_output` rule files) is where a cut would actually touch the per-turn *write* — but apply the same fingerprint-check first.

**Snapshots:** pristine originals at `/tmp/prompt-trim-before/`. Working tree is unmodified.
