# Story Context: 153-29 — MP Per-Player Pronoun Localization Incomplete

## Story Metadata
- **Story ID:** 153-29
- **Epic:** 153 (Playtest follow-ups — open findings from the 2026-06-20/21 full-stack /sq-playtest sweep)
- **Type:** Bug
- **Points:** 3
- **Workflow:** TDD
- **Repositories:** sidequest-server *(confirmed — see Owning-Side Verdict below)*
- **Priority:** P2

## Problem Statement

In multiplayer, the per-recipient POV localizer rewrites the local player's character
name to "You" and conjugates the immediately-following verb, but it does **not** carry
**pronoun agreement** for the same character. The result is person-disagreement inside
the localized player's own narration tab.

Verbatim finding from the playtest:

> Raw server narration "Vesna presses her palm flat to the gouged wall" → Vesna's tab
> renders "You press her palm…". The per-recipient localizer correctly swaps the subject
> noun (Vesna→You) and conjugates the verb (presses→press), but does NOT swap the
> possessive pronoun her→your, producing person-disagreement. Worse in combat, a single
> sentence mixes 2nd+3rd person for the same character — "the weight of it lands on your
> back and something rakes across his shoulders"; "rake you across the shoulder before he
> can raise the blade." IMPORTANT: on reconnect/replay the narration shows clean
> 3rd-person ("Vesna presses her palm") — so the localization is applied at LIVE render
> time per-recipient; the stored/replayed text is the un-localized base.

So the symptom is: **possessive ("her"/"his"/"their" → "your") and follow-on subject
pronouns ("he"/"she"/"they" → "you") for the SAME character whose name was swapped are
left in third person**, while the name + adjacent verb are correctly second-person.

## Owning-Side Verdict (CRITICAL DISCOVERY TASK — RESOLVED)

The discovery task was to determine whether this localizer lives **client-side**
(`sidequest-ui`) or **server-side per-recipient broadcast** (`sidequest-server`). The
reconnect/replay clue (replay shows clean 3rd-person) was the tell, and it points
**server-side**, not client-side:

- The localizer is **`sidequest-server`** code:
  `sidequest/agents/pov_swap.py` → `swap_to_second_person(text, target_name, pronouns)`.
- It runs **per-recipient at broadcast time** inside `sidequest/server/emitters.py`
  (`_apply_pov_swap`, called from `emit_event`), only when the recipient's PC name matches
  the payload's `_visibility.anchor_pc` and `pov_strategy == "pc_anchored"`.
- The **stored prose in the EventLog is canonical 3rd-person**; the 2nd-person rewrite is
  applied on the fly to that one recipient's frame, which is exactly why reconnect/replay
  (re-reading the EventLog) shows clean 3rd-person. This matches the finding precisely.

There is a separate, unrelated client-side "You/you" localizer for the **Fate exchange
ledger** (`sidequest-ui/src/components/FateConflictSurface.tsx::exchangeClause`, the
ui PR #444 work). That one operates on **structured data** (`line.actor`/`line.target`
names + an action verb), not on prose — it has no prose field where a possessive pronoun
could appear, so it is **NOT** the surface in this finding and is out of scope. (It is
worth one paragraph in the story so a reader doesn't conflate the two "You" rewrites.)

**Repo field is correct as `server`.** No repo-field change is needed. The story's title
("per-recipient localizer must convert possessive/subject pronouns") refers to the
server-side `pov_swap.py`.

## Root Cause Direction

`swap_to_second_person` (`pov_swap.py`) is a pure regex string transform with numbered
passes. The **name-driven** passes work:

- Pass 1: possessive **name** `Carl's` → `Your`/`your`
- Pass 2: subject **name** + adjacent verb `Carl plants` → `You plant`
- Pass 2b: subject-verb interrupter conjugation
- Pass 3: bare **name** → `you`/`You`
- Pass 4: reflexive (`himself`/`herself`/`themself`) → `yourself`, gated on a prior
  name-driven subject swap
- Passes 8/9: coordinated-verb conjugation after `and` / comma

The **pronoun** passes are the exact gap in the finding. Passes 5/6/7 were **RETIRED**
on 2026-05-23 (pulp_noir/annees_folles repro) — see the comment block at
`pov_swap.py:454-470`:

- Pass 5: subject pronoun `He`/`She`/`They` → `You`
- Pass 6: possessive pronoun `his`/`her`/`their` → `your`  ← the `her→your` miss in the finding
- Pass 7: object pronoun `him`/`her`/`them` → `you`        ← the `rake you`/mixed-person miss

They were retired because they were **antecedent-blind**: regex fired on *every* matching
pronoun in the anchored prose, so in a scene with an NPC who shares the PC's pronouns
("the man… folds **his** paper… **He** doesn't hurry") the passes turned the NPC's
actions into PC actions ("You doesn't hurry"). The doctrinal fix at the time pushed the
contract to the narrator side (`narrator_prompts/pov_rules.md`: write the PC's actions
using the PC's NAME, never a pronoun). The current finding shows that contract is
insufficient — possessives and follow-on subject pronouns for the same character still
appear, and the localizer leaves them third-person.

**Direction (reuse-first — extend `pov_swap.py`, do NOT add a new rewrite layer):**
re-introduce possessive/subject pronoun agreement, but **antecedent-gated** so it only
fires for the **same character whose name was just swapped**, never for a same-pronoun
NPC. The existing machinery already carries the gating state needed:

- `had_subject_swap` / `subj_swapped_at_start` flags (set by Passes 2/3, already used to
  gate Pass 4 reflexive and Passes 8/9 coordinated verbs)
- `forms["possessive"]` / `forms["subject"]` / `forms["object"]` are already populated in
  `_PRONOUN_FORMS` for he/him, she/her, they/them (the data is present; only the passes
  that consume it were removed).

The safe rewrite is **sentence-local and gated on a name-driven swap in the SAME
sentence** — mirror the Pass-4 reflexive gate. A possessive/subject pronoun is swapped to
2nd person only when this sentence already had the PC's NAME swapped to "You" (so the
antecedent is unambiguously the local PC). A bare same-pronoun NPC sentence with no PC
name never trips the gate, preserving the 2026-05-23 fix's intent. Disambiguation
already-handled hooks exist: she/her possessive vs object share a surface form and the
code notes lookahead disambiguation (`_PRONOUN_FORMS` "she/her" comment).

## Acceptance Criteria

1. **Possessive pronoun agreement for the localized character:**
   When `swap_to_second_person` swaps the PC's name to "You"/"you" in a sentence, a
   possessive pronoun referring to that same PC in the same sentence is converted:
   `her`→`your`, `his`→`your`, `their`→`your`. Example: "Vesna presses her palm" with
   target=Vesna, pronouns="she/her" → "You press your palm". Sentence-capitalized
   possessive at sentence start → "Your".

2. **Follow-on subject pronoun agreement for the localized character:**
   A subject pronoun referring to the same just-swapped PC is converted to "you"/"You"
   with correct verb conjugation: `he/she/they … raises` → `you … raise`. Example from
   the finding: "…before he can raise the blade" (target's antecedent) → "…before you
   can raise the blade".

3. **Object pronoun agreement for the localized character:**
   An object pronoun referring to the same just-swapped PC is converted: `him/her/them`
   → `you`. Example: "something rakes across his shoulders" / "rake you across the
   shoulder" no longer mixes person for the localized PC — both render in 2nd person
   ("…rakes across your shoulders", "rake you across the shoulder").

4. **Antecedent gate preserves the 2026-05-23 fix (no NPC bleed):**
   A pronoun is only rewritten when the same sentence already had a **name-driven**
   subject/possessive swap of the target PC (reusing the existing `had_subject_swap` /
   `subj_swapped_at_start` gate that already governs Pass 4). A sentence describing a
   same-pronoun NPC with **no** PC name in it is left fully third-person. Regression test:
   the pulp_noir/annees_folles shape — "the man with Le Figaro folds his paper… He
   doesn't hurry." with a he/him PC — must NOT produce "You doesn't hurry" or "your
   paper".

5. **Pronoun-agreement assertion in a localized MP narration (required):**
   At least one test asserts **full person agreement** on a representative localized
   multi-pronoun sentence — i.e. no sentence localized for the anchor PC may contain a
   third-person pronoun (he/she/they/him/her/them/his/their) that co-refers with the
   swapped "You". Concretely: feed the combat example through the localizer for the
   anchored PC and assert the output contains **no** residual third-person pronoun for
   that character (subject/object/possessive all agree with "You").

6. **Replay/canonical-text invariant unchanged:**
   The stored EventLog prose remains canonical 3rd-person; only the per-recipient
   broadcast frame is localized. A test confirms the un-localized base text (replay path)
   is untouched and that localization is applied solely at the per-recipient emit step.

7. **OTEL watcher visibility:**
   The existing `narration.second_person_swap` span (the swap_count return value, GM-panel
   lie-detector) reflects the additional pronoun substitutions in its count, so the GM
   panel can verify pronoun agreement fired (not just name+verb). New pass categories
   should be counted in `swap_count` consistent with the existing per-edit accounting.

8. **Wiring / integration test proves production reachability:**
   An integration test drives the **real per-recipient emit path**
   (`emitters._apply_pov_swap` → `swap_to_second_person`), not the pure function in
   isolation: construct a payload with a `_visibility` sidecar (`anchor_pc` +
   `pov_strategy == "pc_anchored"`) and a recipient whose PC matches the anchor, fire the
   emit, and assert the delivered frame's `text` has full pronoun agreement while a
   non-anchor recipient's frame is untouched (canonical 3rd-person). This proves the
   extended passes are reached through production code, not just unit-tested.

## Key Code Areas to Investigate

**The localizer (owns the fix):**
- `sidequest-server/sidequest/agents/pov_swap.py` — `swap_to_second_person(text, target_name, pronouns)`.
  - `_PRONOUN_FORMS` (subject/object/possessive/reflexive per pronoun set) — data already present.
  - Passes 1–4 (name-driven + reflexive) — working; reuse the `had_subject_swap` /
    `subj_swapped_at_start` gating they already establish.
  - **Retired Passes 5/6/7 comment block at `pov_swap.py:454-470`** — the precise spec of
    what to re-introduce (subject/possessive/object), now antecedent-gated.
  - `_is_sentence_start_in`, `_looks_like_verb`, `_conjugate` — existing helpers to reuse.

**The per-recipient wiring (where it runs):**
- `sidequest-server/sidequest/server/emitters.py` — `_apply_pov_swap` (defined ~line 258),
  invoked from `emit_event` (call sites ~lines 596/632/682/700). Gate: `_visibility.anchor_pc`
  + `pov_strategy == "pc_anchored"`, recipient PC match via `view.character_of(...)`,
  pronouns via `_pronouns_for_pc(snapshot, ...)`. Import at `emitters.py:19`.

**Existing tests to extend (anchors for new cases):**
- `sidequest-server/tests/agents/test_pov_swap.py` — pure-function pass coverage.
- `sidequest-server/tests/agents/test_pov_swap_otel.py` — swap_count / span assertions.
- `sidequest-server/tests/server/test_narration_pov_emission.py` — per-recipient emit wiring.
- `sidequest-server/tests/server/test_narration_pov_regression.py` — the NPC-bleed
  regression home; the antecedent-gate (AC 4) regression belongs here.
- `sidequest-server/tests/server/test_opening_pov_swap_71_5.py` — opening-narration POV.

**Out of scope (do not touch — different surface):**
- `sidequest-ui/src/components/FateConflictSurface.tsx` — `exchangeClause(line, me)`
  (client-side Fate exchange-ledger "You" rewrite, ui PR #444). Structured data, no prose
  field; not the finding's surface.

## Technical Notes

- **ADR-036 (multiplayer turn coordination):** narration is fanned out per recipient
  during the wait/resolution phase; the POV swap is one of the per-recipient transforms
  applied as each player's frame is built. The fix lives entirely inside that per-recipient
  step — it does not change the turn barrier or visibility of peer action text (ADR-036's
  2026-05-03 amendment keeps peer action text visible).
- **ADR-104 / ADR-105 (perception firewall):** the POV swap is downstream of perception
  filtering — it rewrites only the prose that survives the firewall and is destined for
  the anchor PC's tab. Pronoun agreement must not "see" or leak any content the firewall
  removed; it operates purely on the already-filtered text for the one recipient. The
  antecedent gate (same-sentence name swap) is what keeps it from mis-attributing prose
  about another character to the local PC — conceptually the grammatical analogue of the
  perception firewall's per-recipient discipline.
- **ADR-108 (per-recipient item attribution / tagging):** the same per-recipient emit
  path already carries recipient-tagged content; pronoun localization is the prose-grammar
  sibling of that per-recipient tailoring. Reuse the existing recipient-keyed emit point,
  do not introduce a parallel rewrite stage.
- **ADR-116 (a confrontation requires an Other):** the worst-case examples in the finding
  are combat sentences; the localizer runs on confrontation narration the same as any
  other narration. No confrontation-membership change is implied — this is purely a
  grammar-agreement fix on the recipient's own prose.
- **Reuse-first / No new rewrite layer:** the architect direction is explicit — extend the
  EXISTING `pov_swap.py` passes (re-introduce 5/6/7 antecedent-gated), do not invent a new
  localization module or a second rewrite stage. The pronoun-form data and gating flags
  already exist; the work is re-enabling consumption of them safely.
- **No source-text wiring tests** (server CLAUDE.md): the wiring test must drive the real
  emit path and assert on emitted prose / OTEL spans, never grep `pov_swap.py` source.
- **OTEL principle:** the `narration.second_person_swap` span's count is the GM-panel
  lie-detector for this subsystem; keep it accurate as passes are added.

## Story Scope

In scope:
- Extending `pov_swap.py` with antecedent-gated possessive, subject, and object pronoun
  agreement for the **single localized target character** (the swapped PC), reusing the
  existing same-sentence name-swap gate.
- Keeping the 2026-05-23 NPC-bleed fix intact via that gate.
- A wiring/integration test through `emitters._apply_pov_swap` and a pronoun-agreement
  assertion on a localized MP combat sentence.
- Keeping `swap_count` / `narration.second_person_swap` OTEL accurate.

Out of scope:
- The client-side Fate exchange-ledger localizer (`FateConflictSurface.tsx`) — different
  surface, no prose field, separate ui PR #444 lineage.
- Adding pronoun sets beyond the three already in `_PRONOUN_FORMS` (he/him, she/her,
  they/them) unless a playtest world requires it.
- Any change to perception filtering (ADR-104/105), the turn barrier (ADR-036), or
  confrontation membership (ADR-116).
- Narrator-prompt rewording (`narrator_prompts/pov_rules.md`) — the fix is in the
  deterministic rewriter, not the prompt contract.

---

## Development Notes

1. Re-read the retired-passes comment block (`pov_swap.py:454-470`) — it is the spec for
   exactly what to re-introduce and why it was removed; the new version must be
   antecedent-gated on `had_subject_swap` / `subj_swapped_at_start`.
2. Reproduce the finding's two sentences as RED tests first (possessive "her palm";
   combat mixed-person), plus the pulp_noir/annees_folles NPC-bleed sentence as the guard.
3. Drive at least one case through `emitters._apply_pov_swap` so the wiring test exercises
   the real per-recipient broadcast gate, not just the pure function.
