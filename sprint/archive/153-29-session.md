---
story_id: "153-29"
jira_key: ""
epic: "153"
workflow: "tdd"
---
# Story 153-29: MP-PRONOUN-LOCALIZATION-INCOMPLETE

## Story Details
- **ID:** 153-29
- **Title:** [MP-PRONOUN-LOCALIZATION-INCOMPLETE] per-recipient localizer must convert possessive/subject pronouns (her->your, he->you), not only the subject noun + verb
- **Jira Key:** (not configured for this project)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-22T15:47:31Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-22T13:49:08Z | 2026-06-22T14:00:52Z | 11m 44s |
| red | 2026-06-22T14:00:52Z | 2026-06-22T14:29:27Z | 28m 35s |
| green | 2026-06-22T14:29:27Z | 2026-06-22T15:04:26Z | 34m 59s |
| review | 2026-06-22T15:04:26Z | 2026-06-22T15:18:12Z | 13m 46s |
| red | 2026-06-22T15:18:12Z | 2026-06-22T15:23:43Z | 5m 31s |
| green | 2026-06-22T15:23:43Z | 2026-06-22T15:39:54Z | 16m 11s |
| review | 2026-06-22T15:39:54Z | 2026-06-22T15:47:31Z | 7m 37s |
| finish | 2026-06-22T15:47:31Z | - | - |

## Story Context

Full story context and acceptance criteria are documented in:
**File:** `sprint/context/context-story-153-29.md`

Key points:
- **Type:** Bug (3 pts, P2)
- **Repository:** sidequest-server
- **Root Cause:** Server-side `pov_swap.py` possessive/subject/object pronoun passes (5/6/7) were retired on 2026-05-23 to prevent NPC-bleed regressions. The current finding shows that contract is insufficient — pronouns for the same character still appear third-person in the localized player's narration tab.
- **Direction:** Re-introduce antecedent-gated pronoun agreement (possessive/subject/object) into `pov_swap.py`, reusing the existing `had_subject_swap` / `subj_swapped_at_start` gating machinery to prevent NPC-bleed (2026-05-23 fix).

### Acceptance Criteria (8 total)
1. Possessive pronoun agreement for the localized character (her→your, his→your, their→your)
2. Follow-on subject pronoun agreement for the localized character (he/she/they→you with correct verb conjugation)
3. Object pronoun agreement for the localized character (him/her/them→you)
4. Antecedent gate preserves the 2026-05-23 fix (no NPC bleed)
5. Pronoun-agreement assertion in a localized MP narration (full person agreement test required)
6. Replay/canonical-text invariant unchanged (stored EventLog remains 3rd-person)
7. OTEL watcher visibility (narration.second_person_swap span count reflects new passes)
8. Wiring / integration test proves production reachability through emitters._apply_pov_swap

### Key Code Areas
- **The localizer (fix owner):** `sidequest/agents/pov_swap.py` — `swap_to_second_person(text, target_name, pronouns)`
  - `_PRONOUN_FORMS` (subject/object/possessive/reflexive per pronoun set) — data already present
  - Retired Passes 5/6/7 comment block at `pov_swap.py:454-470` — the spec for what to re-introduce
  - Existing `had_subject_swap` / `subj_swapped_at_start` gating (used by Pass 4 reflexive)
- **Per-recipient wiring:** `sidequest/server/emitters.py` — `_apply_pov_swap`, invoked from `emit_event`
  - Gate: `_visibility.anchor_pc` + `pov_strategy == "pc_anchored"`, recipient PC match
- **Existing test anchors:**
  - `tests/agents/test_pov_swap.py` — pure-function pass coverage
  - `tests/agents/test_pov_swap_otel.py` — swap_count / span assertions
  - `tests/server/test_narration_pov_emission.py` — per-recipient emit wiring
  - `tests/server/test_narration_pov_regression.py` — NPC-bleed regression home (AC 4)
  - `tests/server/test_opening_pov_swap_71_5.py` — opening-narration POV

### Branch Strategy
**Branch Strategy:** gitflow (feat/153-29-mp-pronoun-localization)

## Sm Assessment

**Story:** 153-29 — [MP-PRONOUN-LOCALIZATION-INCOMPLETE] the per-recipient POV localizer
swaps the local PC's name to "You" and conjugates the adjacent verb, but leaves
possessive/subject/object pronouns for that same character in 3rd person — producing
person-disagreement inside the localized player's own tab ("You press **her** palm…",
and worse mixed-person in combat).

**Type / size / workflow:** Bug, 3 points, `tdd` (phased: setup → red → green → review →
finish). **Repo:** `sidequest-server` only (base branch `develop`). Confirmed by the
Architect's owning-side discovery (see context doc §Owning-Side Verdict): the localizer is
server-side `sidequest/agents/pov_swap.py::swap_to_second_person`, run per-recipient at
broadcast time in `sidequest/server/emitters.py::_apply_pov_swap`. The reconnect/replay
clue (replay shows clean 3rd-person) is the tell — the stored EventLog prose is canonical
3rd-person; the 2nd-person rewrite is applied on the fly to one recipient's frame. The
client-side Fate exchange-ledger "You" rewrite (`FateConflictSurface.tsx`, ui PR #444) is
a DIFFERENT surface (structured data, no prose field) and is explicitly out of scope.

**Approach direction (reuse-first, no new rewrite layer):** re-introduce the retired
Passes 5/6/7 (subject/possessive/object pronoun agreement) inside `pov_swap.py`, but
**antecedent-gated** so a pronoun is only rewritten when the SAME sentence already had a
name-driven swap of the target PC — reusing the existing `had_subject_swap` /
`subj_swapped_at_start` flags that already gate Pass 4 (reflexive) and Passes 8/9
(coordinated verbs). Passes 5/6/7 were retired 2026-05-23 because they were
antecedent-blind and bled NPC pronouns into PC actions ("You doesn't hurry"); the gate is
exactly what makes the re-introduction safe. `_PRONOUN_FORMS` already carries the
subject/object/possessive data for he/him, she/her, they/them — only the consuming passes
were removed.

**Context:** Full spec at `sprint/context/context-story-153-29.md` (8 ACs, root-cause
direction, key code areas, ADR-036/104/105/108/116 notes). Context file naming verified
(`context-story-153-29.md`, correct prefix form).

**Regression guard TEA must hold (AC 4):** the pulp_noir/annees_folles shape — a same-pronoun
NPC sentence with NO PC name ("the man… folds his paper… He doesn't hurry", he/him PC) —
must stay fully 3rd-person; never "You doesn't hurry" / "your paper".

**Wiring (AC 8, server CLAUDE.md "No Source-Text Wiring Tests"):** the integration test
must drive the REAL emit path (`emitters._apply_pov_swap` → `swap_to_second_person`) with a
`_visibility` sidecar (`anchor_pc` + `pov_strategy == "pc_anchored"`), assert the anchor
recipient's frame has full pronoun agreement AND a non-anchor recipient's frame stays
canonical 3rd-person — never grep `pov_swap.py` source.

**OTEL (AC 7):** keep `narration.second_person_swap` swap_count accurate — count the new
pronoun substitutions consistent with existing per-edit accounting (GM-panel lie-detector).

**Setup note:** sm-setup stranded the session in `sidequest-server/.session/`; relocated to
the canonical `.session/` (→ `sprint/.session/`) where `pf handoff` reads. Branch verified
in the server subrepo (next check below). Jira cleanly skipped — not configured for this
personal project (per server CLAUDE.md).

**Handoff:** → TEA (Amos Burton) for the RED phase. Write failing tests for all 8 ACs,
anchored in the five existing test files named in the context doc; reproduce the finding's
two sentences (possessive "her palm"; combat mixed-person) plus the NPC-bleed guard first.

## TEA Assessment

**Tests Required:** Yes
**Reason:** n/a — 3-pt bug changing deterministic-rewriter behavior across 8 ACs.

**Test Files:**
- `tests/agents/test_pov_swap.py` — pure-function pronoun-agreement coverage (AC 1/2/3/4/5). 1 existing test rewritten to the new contract, 2 semicolon-NPC guards' docstrings updated, 13 new/updated tests.
- `tests/agents/test_pov_swap_otel.py` — `swap_count` includes the new pronoun edits (AC 7); 1 new test.
- `tests/server/test_narration_pov_emission.py` — real per-recipient emit-path wiring (AC 8) + canonical/replay invariant (AC 6); 2 new tests. **File RE-INCLUDED** from the conftest deprecated-skip set (see Delivery Findings).
- `tests/conftest.py` — removed `server/test_narration_pov_emission.py` from `_CAVERNS_SUNDEN_DEPRECATED_TESTS` so the AC-8 wiring test actually RUNS (a skipped wiring test proves nothing).

**Tests Written:** 16 new/updated tests across all 8 ACs (13 pure-fn + 1 OTEL + 2 emit-path).
**Status:** RED — 15 fail by design; 1 (the AC-6 canonical-text invariant) PASSES by design as a protective lock (the EventLog already stores canonical 3rd-person; Dev must keep it that way). Confirmed via testing-runner: test_pov_swap.py 13 fail / guards green; test_pov_swap_otel.py swap_count=2<5 fail; test_narration_pov_emission.py 6 pass (5 pre-existing wiring + AC-6) / 1 fail (AC-8 'You press her palm').

### Per-AC coverage
- **AC 1** (possessive her/his/their→your): `test_possessive_pronoun_{her,his,their}_after_name_swap_becomes_your`, `test_possessive_name_swap_arms_the_pronoun_gate` — RED
- **AC 2** (subject he/she/they→you + verb conjugation): `test_subject_pronoun_{he,she,they}_after_name_swap_*`, `test_subject_pronoun_after_name_swap_in_same_clause_becomes_you` — RED
- **AC 3** (object him/her/them→you): `test_object_pronoun_{him,her,them}_referring_to_pc_becomes_you` — RED
- **AC 4** (antecedent gate / no NPC bleed): `test_pronoun_in_separate_sentence_without_pc_name_survives` (green guard), `test_pronoun_converts_in_name_clause_but_not_across_semicolon_to_npc` (RED), the two semicolon-NPC guards + existing annees_folles guards (green)
- **AC 5** (full-agreement assertion): `test_localized_combat_sentence_has_no_residual_third_person_pronoun` — RED
- **AC 6** (replay/canonical invariant): `test_canonical_eventlog_text_stays_third_person_after_localized_emit` — PASS (protective lock)
- **AC 7** (OTEL swap_count): `test_swap_count_includes_pronoun_substitutions` — RED
- **AC 8** (wiring through real emit path): `test_anchor_recipient_sees_full_pronoun_agreement` — RED

### Rule Coverage (`.pennyfarthing/gates/lang-review/python.md`)
| Rule | Test(s) | Status |
|------|---------|--------|
| #6 test quality (meaningful assertions) | every new test uses exact `==` + negative substring/regex asserts; AC-5 asserts a specific residual-pronoun regex; OTEL asserts `>= 5`; no truthy-only / vacuous / skip | self-checked clean |
| #1 fail-loud (no silent fallback) | existing `test_empty_target_name_raises` / `test_unknown_pronoun_string_raises` retained | green |
| #11 ReDoS (regex backtracking) | new passes must be static, anchored regexes (no user-built patterns) — flagged for Dev (server CLAUDE.md warns on catastrophic backtracking) | noted for Dev |

**Rules checked:** 3 of 13 applicable (this is a test-authoring phase; #6 is load-bearing, #1 covered by retained guards, #11 handed to Dev). The other 10 target production code Dev will write in GREEN.
**Self-check:** 0 vacuous assertions found in new tests; the rewritten `test_subject_pronoun_after_name_swap_in_same_clause_becomes_you` replaced an assertion that pinned the now-reversed retired-pass contract.

**Handoff:** To Dev (Naomi Nagata) for GREEN — re-introduce antecedent-gated possessive/subject/object pronoun passes in `pov_swap.py`: (1) gate on the existing `had_subject_swap`/`subj_swapped_at_start`, AND arm it from Pass 1 possessive-name swaps too (AC 4); (2) make the gate CLAUSE-local — do not cross a `;` into a clause about another subject (see Design Deviation); (3) conjugate the verb after a swapped subject pronoun (`he rolls`→`you roll`); (4) count every pronoun edit in `swap_count` (AC 7). Reuse `_PRONOUN_FORMS` (data already present) and the she/her possessive-vs-object lookahead the code already notes. Do NOT add a new rewrite layer.

## Delivery Findings

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Conflict** (non-blocking): AC 4's literal "same-sentence" gate would re-open the 2026-05-23 NPC-bleed bug for an NPC pronoun in a separate `;`-clause of one engine-sentence. TEA pinned a stricter CLAUSE-local gate to honor AC 4's stated "no NPC bleed" intent. Affects `sidequest/agents/pov_swap.py` (Dev must track name-swap per `;`-clause, not a whole-sentence flag). *Found by TEA during test design.* See the matching Design Deviation.
- **Improvement** (non-blocking): the per-recipient POV-swap WIRING file (`tests/server/test_narration_pov_emission.py`) was entirely skipped via the conftest `_CAVERNS_SUNDEN_DEPRECATED_TESTS` blacklist — the whole `swap_to_second_person` per-recipient emit path had NO active wiring coverage. Re-included it (builds in-memory, no on-disk world load; sibling regression file already runs un-skipped). Affects `tests/conftest.py`. Sibling skipped files in that set may also be hiding live-subsystem coverage. *Found by TEA during test design.*
- **Question** (non-blocking): AC 1's "sentence-capitalized possessive at sentence start → 'Your'" is structurally ungateable for a possessive PRONOUN ("Her …" opening a sentence) under the antecedent gate — there is no prior in-clause name swap to gate on, and cross-sentence antecedent tracking is exactly what the 2026-05-23 retire forbids. (Sentence-initial possessive NAME is covered by Pass 1 already.) Not tested. Affects `sidequest/agents/pov_swap.py` — confirm out-of-scope or supply a separate antecedent signal. *Found by TEA during test design.*
- **Improvement** (non-blocking): she/her possessive ("her palm") vs object ("bites her") share the surface form "her"; agreement relies on the lookahead heuristic the code already notes in `_PRONOUN_FORMS`. Ambiguous lookahead positions (e.g. "her" before a gerund) may misclassify; Dev should reuse/extend that hook rather than guess. Affects `sidequest/agents/pov_swap.py`. *Found by TEA during test design.*
- **Gap** (non-blocking, rework r1): the original RED had NO coverage at the `;`-clause boundary for NAME swaps — every name-swap test put the name in the first clause / whole sentence, so the clause-split's effect on `_is_sentence_start_in` / `_is_proper_noun_fragment` (capitalization + 153-14 fragment) went untested and the Reviewer's two regressions slipped through GREEN. Rework adds 4 RED + 2 green-guard boundary tests. Lesson for future POV work: any test that exercises a NAME or possessive-NAME swap should include a variant where the name sits in a NON-first `;`-clause. Affects `tests/agents/test_pov_swap.py`. *Found by TEA during rework round-trip 1.*

### Dev (implementation)
- **Conflict** (non-blocking, resolved): three pre-existing tests asserted a PC-referent possessive SURVIVES third-person (`test_adverb_between_subject_and_verb_conjugates` "his hands", `test_interrupter_conjugation_they_them_parity` "their hands", `test_possessive_his_after_comma_not_de_pluralized` "his copper face") — the retired-pass contract that AC 1 explicitly reverses. They were not in TEA's changed set and were validated RED-green only against pre-implementation code (where they pass because the passes don't exist yet), so the conflict was latent. Resolved by updating the three to the new contract while preserving each test's load-bearing assertion (verb conjugation / #708 de-pluralization guard). Affects `tests/agents/test_pov_swap.py` (3 tests, see matching Design Deviation). *Found by Dev during implementation.*
- **Question** (non-blocking): answering TEA's she/her-lookahead Improvement — Dev implemented the disambiguation as: possessive `her` = `\bher\b(?=\s+\w)` (governs a following word), object `her` = `\bher\b(?!\s+\w)` (clause-final / before punctuation). All AC-1/3/5 her-cases pass. The known gap TEA flagged ("her" before a gerund, e.g. "watching her running") is unhandled — it would classify as possessive; no playtest case surfaced it and none is tested. Affects `sidequest/agents/pov_swap.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): AC 7 swap_count now counts each pronoun edit (possessive +1, subject-pronoun +1 and its verb-conjugation +1, object +1), consistent with the existing per-edit accounting. The GM-panel `narration.second_person_swap` span therefore reflects the pronoun work (verified: "Carl plants a boot and he hauls his polearm." → count 5). No new OTEL span was added — the existing span's attribute simply grew, which is the AC-7 contract. *Found by Dev during implementation.*
- **Improvement** (non-blocking, rework r2): the lesson generalizes — when a refactor changes input granularity (whole-sentence → per-clause), every helper that infers POSITION CONTEXT (`_is_sentence_start_in`, `_is_proper_noun_fragment`) must be told the new boundary or it will silently treat a sub-unit start as a string start. The remaining non-blocking findings from review (within-clause same-set NPC bleed; she/her object-before-particle; format-dirty test file; `import json` placement; doc nits) are NOT addressed in this round — they are accepted-approach limitations / TEA-file housekeeping and were out of the rejected-finding scope. Affects `sidequest/agents/pov_swap.py`, `tests/server/test_narration_pov_emission.py`. *Found by Dev during rework round-trip 2.*

### Reviewer (code review)
- **Gap** (blocking): the `;`-clause-split re-opens the shipped 153-14 NPC-name-fragment guard after a semicolon — `"…; Vah Kantos bows."` (PC "Kantos") → `"…; Vah you bow…"`. Affects `sidequest/agents/pov_swap.py` (`_is_proper_noun_fragment` must thread `is_first_clause` into its `_is_sentence_start_in` call). *Found by Reviewer during code review.*
- **Gap** (blocking): a PC name swapped at the start of a post-`;` clause capitalizes mid-sentence — `"The torch gutters; Carl steadies it."` → `"…; You steady it."`. Affects `sidequest/agents/pov_swap.py` (`_is_sentence_start_in`: the `if j < 0: return True` whitespace-walkback must return `clause_is_sentence_start`). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): within-clause same-pronoun-set NPC bleed — an armed clause converts a same-set NPC object/possessive (`"Carl shoves him."` → `"You shove you."`). Inherent to the regex gate; mitigate narrator-side. Affects `sidequest-content`/narrator `pov_rules.md` (instruct the narrator to name NPC objects, not pronoun them, in clauses that also name the PC) and/or a future antecedent pass — Architect call, out of this story's scope. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): she/her object pronoun before a non-noun is misclassified as possessive (`"knocks her back."` → `"your back"`). Confirms TEA's Question. Affects `sidequest/agents/pov_swap.py` (the `(?=\s+\w)` lookahead could exclude common particles/adverbs, or stay a documented limitation). *Found by Reviewer during code review.*
- **Improvement** (non-blocking, housekeeping for the rework): `ruff format tests/server/test_narration_pov_emission.py` (format-dirty from the RED commit); move `import json` to module scope (`:812`); refresh the stale module-docstring opening line and the `test_swap_count_matches_substitution_total` docstring; add a note (or renumber) for the Pass 6→5→7 ordering. Affects `tests/server/test_narration_pov_emission.py`, `sidequest/agents/pov_swap.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, re-review r1): two of the rework's GREEN tests/guards could be tightened — `test_first_clause_subject_swap_stays_capitalized_after_semicolon_fix` should use `out == "You steady the torch; the flame holds."` instead of `startswith(...)` (flagged by both test-analyzer and rule-checker); and three future-refactor sentinel tests are worth adding (3rd-clause name swap; a cross-`;` possessive non-bleed guard `"Carl plants a boot; his grip tightens."` → his stays; mid-clause suffix-NPC in a non-first clause) — I verified all three behave correctly today, so these are belt-and-suspenders, not bug coverage. Affects `tests/agents/test_pov_swap.py`. *Found by Reviewer during re-review round-trip 1.*
- **Resolved** (was blocking, now FIXED): both round-1 blocking Gaps above (153-14 fragment after `;`; capitalization after `;`) are fixed in rework r2 and verified GREEN (4 RED tests pass, 0 over-correction, rule-checker confirmed the `j<0` change behavior-preserving). The format-dirty `test_narration_pov_emission.py` + `import json` placement remain open for the finish/follow-up (LOW, non-blocking — `ruff format` before merge). *Re-review round-trip 1.*

## Design Deviations

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Clause-local antecedent gate instead of the context doc's "same-sentence" wording**
  - Spec source: context-story-153-29.md, AC 4 (+ Root Cause Direction: "sentence-local … gated on a name-driven swap in the SAME sentence")
  - Spec text: "A pronoun is only rewritten when the same sentence already had a name-driven subject/possessive swap of the target PC."
  - Implementation: Tests pin a stricter CLAUSE-local gate — pronoun agreement does NOT cross a `;` boundary into a clause about a different subject (`test_pronoun_converts_in_name_clause_but_not_across_semicolon_to_npc`; the two `;`-NPC guards kept green). Same-clause pronouns convert (AC 1/2/3).
  - Rationale: the engine "sentence" splits only on `.!?`, so one sentence can hold an NPC clause after `;` ("Carl plants a boot; the moth shudders against him"). The literal same-sentence gate would convert that NPC 'him'→'you' — re-opening the 2026-05-23 antecedent-blind bleed that AC 4's own TITLE ("no NPC bleed") exists to prevent. Honoring AC 4's stated intent outranks its suggested mechanism. Every finding example lives in the same clause as its name swap, so none is blocked.
  - Severity: minor
  - Forward impact: Dev must implement clause-aware gating (track the name-swap per `;`-clause), not a single whole-sentence flag. If the Architect prefers the coarse same-sentence gate, three tests are where that decision lands (the two `;`-NPC guards + the clause-boundary test).
- **Did not test AC 1's "sentence-capitalized possessive at sentence start → Your" for a possessive PRONOUN**
  - Spec source: context-story-153-29.md, AC 1
  - Spec text: "Sentence-capitalized possessive at sentence start → 'Your'."
  - Implementation: no test for a possessive PRONOUN ("Her …"/"His …") opening a sentence; only mid-clause possessives after an in-clause name swap are tested. (Sentence-initial possessive NAME → "Your" is already covered by Pass 1's existing tests.)
  - Rationale: under the antecedent gate a possessive pronoun at the absolute start of a sentence has NO prior in-clause name swap to gate on — structurally ungateable without cross-sentence antecedent tracking, which the 2026-05-23 retire forbids. Pinning it would demand behavior the gate cannot safely produce.
  - Severity: minor
  - Forward impact: if a playtest surfaces a sentence-initial possessive pronoun for the PC, it needs a separate antecedent signal (prior-sentence subject) — out of this story's gated-rewrite scope. Captured as a Question delivery finding.
- **Rework r1 — No new spec deviations.** The rework adds regression tests pinning the two Reviewer-found post-`;` clause-boundary bugs to their pre-branch-correct behavior (lowercase clause-initial swap; 153-14 fragment guard holds after `;`). These enforce existing correct contract, not a new interpretation; the clause-local design decision (logged above) stands. No deviation from spec.

### Dev (implementation)
- **Updated three existing tests whose assertions pinned the now-reversed "retired-pronoun-passes" contract**
  - Spec source: context-story-153-29.md, AC 1 ("possessive pronoun agreement her→your, his→your, their→your") — highest-authority story scope
  - Spec text: "Possessive pronoun agreement for the localized character (her→your, his→your, their→your)."
  - Implementation: AC 1 makes a PC-referent possessive in an armed clause agree to "your". Three pre-existing tests (NOT in TEA's changed set) asserted the *opposite* — that the possessive survives third-person — and their docstrings explicitly invoke "the retired-pronoun-passes contract" AC 1 reverses. They cannot coexist with AC 1 (both clauses are armed, single-clause, possessive co-refers with the swapped PC; there is no regex-distinguishable difference from the new AC-1 cases). Updated each to the new contract, **preserving each test's load-bearing assertion**: (1) `test_adverb_between_subject_and_verb_conjugates` — "…with his hands…"→"…with your hands…" (keeps the adverb-stranded verb conjugation `works`→`work`); (2) `test_interrupter_conjugation_they_them_parity` — "…with their hands…"→"…with your hands…" (keeps the interrupter verb conjugation); (3) `test_possessive_his_after_comma_not_de_pluralized` — asserts "your copper face" not "his copper face", and KEEPS the load-bearing #708 guard `"hi copper" not in out` (the possessive must never be de-pluralized to "hi" — now it agrees to "your", still not "hi").
  - Rationale: per the Spec Authority Hierarchy, story scope (AC 1) outranks the stale tests. The alternative — special-casing the implementation so "his hands"/"their hands"/"his copper face" survive while "his shield"/"her palm" convert — is impossible (identical grammar) and would be a worse violation. Editing tests is normally TEA's lane; flagged loudly here + as a Delivery Finding so Reviewer/TEA can scrutinize.
  - Severity: minor
  - Forward impact: none on production. If TEA/Architect intends these three cases to behave differently from the AC-1 cases, the contract itself needs revisiting — but no rule distinguishes them.
- **Realized the clause-local gate by splitting the engine-sentence on `;` and processing each clause through the full pass pipeline**
  - Spec source: TEA Design Deviation (clause-local gate) + AC 4 (no NPC bleed)
  - Spec text: "Dev must implement clause-aware gating (track the name-swap per `;`-clause), not a single whole-sentence flag."
  - Implementation: `_rewrite_sentence` now splits on `;` (separators preserved) and dispatches each clause to `_rewrite_clause`, which carries a per-clause `name_swap_occurred` flag gating the re-introduced pronoun passes. SIDE EFFECT: the pre-existing `had_subject_swap`-gated passes (Pass 4 reflexive, Pass 8 "and"-verb, Pass 9 comma-verb) are now ALSO clause-local — previously a subject swap in clause 1 could conjugate a coordinated verb in a post-`;` clause 2 about a different subject. No test exercised that cross-`;` behavior either way; the narrowing is strictly safer (matches AC 4's no-bleed intent).
  - Rationale: per-clause processing is the cleanest realization of TEA's directive and makes `name_swap_occurred` precise (armed only by a real swap in the clause) instead of a presence-heuristic. `_is_sentence_start_in` gained a `clause_is_sentence_start` param so a name swapped at the start of a non-first `;`-clause stays lowercase ("…; you step", not "…; You step").
  - Severity: minor
  - Forward impact: any future pass added to `_rewrite_clause` is automatically clause-scoped. If a genuine cross-`;` coordinated-verb case ever surfaces in a playtest, that is where it would need handling.
- **Rework r2 — resolved the Reviewer's FLAGGED clause-boundary bugs (no new deviation).** The deviation above understated a consequence: the clause-split fed single clauses to `_is_sentence_start_in` / `_is_proper_noun_fragment`, which were written for whole sentences and read a clause start as a sentence start (capital "You" after `;`; 153-14 fragment leak after `;`). The `clause_is_sentence_start` param I added was ineffective because the real path is the whitespace walk-back, not the `idx==0` branch. Fix (this round): `_is_sentence_start_in`'s `if j < 0: return True` → `return clause_is_sentence_start`, and `_is_proper_noun_fragment` now takes `is_first_clause` and threads `clause_is_sentence_start=is_first_clause`. Both behaviors are restored to their pre-branch-correct form; first-clause swaps still capitalize. This enforces the existing correct contract — not a new spec interpretation — so no new deviation. The Reviewer's FLAGGED deviation is considered resolved.

### Reviewer (audit)
- **TEA — "Clause-local antecedent gate instead of same-sentence wording"** → ✓ ACCEPTED by Reviewer: the clause-local reading is correct and honors AC-4's "no NPC bleed" intent; the cross-`;` guards verify cleanly. (The *implementation* of clause-locality is where the bugs are — see below — but the design decision is sound.)
- **TEA — "Did not test sentence-capitalized possessive PRONOUN at sentence start"** → ✓ ACCEPTED by Reviewer: structurally ungateable under the antecedent gate without cross-sentence tracking; out of scope is the right call.
- **Dev — "Updated three existing tests that pinned the retired contract"** → ✓ ACCEPTED by Reviewer: spec-authority (AC-1) outranks the stale assertions; each test's load-bearing guard (verb conjugation / #708 de-pluralization) is preserved. test-analyzer concurs. The only nit: `test_possessive_his_after_comma`'s positive assert is a substring rather than `==` — but that style predates the story, so it is not a Dev regression.
- **Dev — "Realized the clause-local gate by splitting on `;` and processing each clause"** → ✗ FLAGGED by Reviewer: the *decision* to clause-split is reasonable, but the deviation's stated guarantee is FALSE as implemented. It claims "`_is_sentence_start_in` gained a `clause_is_sentence_start` param so a name swapped at the start of a non-first `;`-clause stays lowercase (\"…; you step\", not \"…; You step\")." My probe shows the opposite: `"The door opens; Carl grabs his sword."` → `"…; You grab your sword."` (capital). The param only gates the `idx == 0` branch, but `re.split(r"(;)")` leaves a leading space so the name sits at idx 1 and the whitespace-walkback `if j < 0: return True` fires instead, ignoring the flag. The same clause-unaware inference also re-opens the shipped 153-14 fragment guard after a `;`. **This deviation introduced two regressions** — see the Reviewer Assessment severity table. Severity: HIGH (blocking).

### Reviewer (audit) — undocumented deviations
- **Within-clause same-pronoun-set NPC bleed:** Spec/AC-4 says "no NPC bleed"; the clause-local gate converts ALL of the PC's pronoun-set pronouns inside an armed clause, so a same-set NPC object/possessive in that clause bleeds (`"Carl shoves him."` → `"You shove you."`). Dev documented the *cross-`;`* clause-locality but did not log this *within-clause* residual as a known limitation. Inherent to a regex gate (no antecedent resolution) and accepted-by-approach, so non-blocking — but it should have been logged. Severity: M (documentation gap; the behavior itself is an accepted limitation). → Now logged by Dev as a Delivery Finding (Improvement, narrator pov_rules.md / Architect scope) in rework r2. Documentation gap CLOSED.

### Reviewer (audit) — re-review (round-trip 1)
- **Dev — "Realized the clause-local gate by splitting on `;`"** (FLAGGED in round 1) → ✓ RESOLVED. The two regressions that earned the FLAG (capital "You" after `;`; 153-14 fragment leak after `;`) are fixed in rework r2 by threading the clause boundary into `_is_sentence_start_in` (j<0 → `clause_is_sentence_start`) and `_is_proper_noun_fragment` (`is_first_clause`). Verified by me + the 4 RED tests now green + rule-checker's behavior-preservation proof. The clause-split design itself was always sound; only its boundary inference was incomplete, and that is now corrected.
- **Dev — "Rework r2 — resolved the FLAGGED clause-boundary bugs (no new deviation)"** → ✓ ACCEPTED. The fix enforces the existing correct contract (pre-branch behavior), not a new interpretation; no new deviation, correctly judged.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/agents/pov_swap.py` — Re-introduced the retired subject/possessive/object pronoun passes as antecedent-gated, clause-local agreement. `_rewrite_sentence` splits the engine-sentence on `;` and dispatches each clause to the renamed `_rewrite_clause`, which carries a per-clause `name_swap_occurred` flag (armed by Pass 1 possessive-name OR Pass 2/3 subject-name) that gates the new passes. Possessive→"your", subject→"you"+verb-conjugation, object→"you"; she/her "her" disambiguated by following-noun lookahead. `swap_count` (OTEL `narration.second_person_swap`) counts each pronoun edit (AC 7). `_is_sentence_start_in` gained `clause_is_sentence_start` so post-`;` clause-initial swaps stay lowercase. Module + inner comments updated to reflect the gated re-introduction.
- `tests/agents/test_pov_swap.py` — Updated 3 pre-existing tests whose assertions pinned the now-reversed retired-pass contract (his/their possessive surviving), preserving each test's load-bearing assertion. See Design Deviations.

**Tests:** GREEN.
- Target suite (pov_swap + otel + emission): 90/90 passing.
- Consumer/regression suite (dialogue_extract, opening_pov_swap_71_5, opening_emit_event_71_13, narration_pov_regression): 19/19 passing.
- Full server suite: 13965 passed, 340 skipped, **2 failed — both pre-existing and unrelated to pov_swap** (`test_59_30_witnesses` witness-count drift from story 153-5; `test_movement_dispatch::test_move_toward_uncommitted_edge_sync_materializes` `_FakeHandle` missing `.drain()` from the immediately-prior commit 43a899ea). Neither test imports pov_swap; my diff touches only `pov_swap.py` + `test_pov_swap.py`.

**Wiring (AC 8):** No new wiring needed — `emitters._apply_pov_swap` → `swap_to_second_person` already exists; the re-included `test_anchor_recipient_sees_full_pronoun_agreement` drives the real per-recipient emit path end-to-end and passes (anchor sees "You press your palm…", non-anchor sees canonical 3rd-person).

**Branch:** feat/153-29-mp-pronoun-localization (server) — pushed.

**Handoff:** To next phase (review). Reviewer/TEA: please scrutinize the 3 test updates (Design Deviation: "Updated three existing tests…") — they resolve a latent AC-1-vs-stale-test conflict TEA's RED couldn't surface.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 1 (format violation) + 90/90 green, no smells | confirmed 1, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A — Disabled via settings (covered manually: probed post-`;` clause boundaries, within-clause NPC bleed, she/her lookahead, modals — found 2 blocking regressions) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A — Disabled via settings (manual: pure fn, fail-loud ValueError on bad input, no swallowed errors) |
| 4 | reviewer-test-analyzer | Yes | findings | 8 (3 test-update verdicts + 5 quality/coverage) | confirmed 5, dismissed 0, deferred 3 |
| 5 | reviewer-comment-analyzer | Yes | findings | 4 (stale docstring, label order, Pass-4 note, _is_proper_noun_fragment) | confirmed 4, dismissed 0, deferred 0 |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — Disabled via settings (manual: `forms: dict` bare-type on private helper, pre-existing, exempt) |
| 7 | reviewer-security | No | Skipped | disabled | N/A — Disabled via settings (manual + rule-checker: ReDoS-clean; pronouns validated against closed set before regex build) |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — Disabled via settings (manual: clause-split is justified by clause-locality requirement; no over-engineering) |
| 9 | reviewer-rule-checker | Yes | findings | 2 (import json in fn body, rule 10/13) | confirmed 1 (1 line, 2 rules), dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 2 blocking (Reviewer-found regressions) + ~11 non-blocking confirmed, 0 dismissed, 3 deferred (test-coverage suggestions for the rework)

### Rule Compliance (`.pennyfarthing/gates/lang-review/python.md` + server CLAUDE.md)

Exhaustive per-rule enumeration over the diff (production = `pov_swap.py`; tests = 4 files):

- **#1 Silent exceptions:** COMPLIANT. `pov_swap.py` has no try/except; the only error path is the fail-loud `raise ValueError` for empty `target_name` / unknown `pronouns` (swap_to_second_person) — satisfies "No Silent Fallbacks".
- **#2 Mutable defaults:** COMPLIANT. Every new/changed signature (`_rewrite_clause`, `_rewrite_sentence`, `_is_sentence_start_in(..., clause_is_sentence_start=True)`) uses keyword-only or immutable-bool defaults. No `[]`/`{}`/`set()`.
- **#3 Type annotations:** COMPLIANT (with note). Public `swap_to_second_person` fully annotated `-> tuple[str, int]`. New `clause_is_sentence_start: bool = True` annotated. The `forms: dict` bare type on `_rewrite_clause`/`_rewrite_sentence` is a private-helper, pre-existing pattern — exempt per rule's "internal/private helpers exempt" carve-out; not worsened by this diff.
- **#4 Logging:** COMPLIANT. Module uses OTEL spans (project convention), not `logging`. The `narration.second_person_swap` span carries `swap_count`/`swap_target_name` — OTEL Observability Principle satisfied; swap_count now counts pronoun edits (AC-7).
- **#5 Path handling:** COMPLIANT. No file I/O in production; tests use `tmp_path` (pathlib).
- **#6 Test quality:** COMPLIANT overall — every new pure-fn test uses exact `==` + negative guards; wiring tests drive real dispatch (not source-grep). Minor non-blocking: `_re_word(...) is False` identity-comparison (TEA's test), substring (not `==`) positive assert on `test_possessive_his_after_comma`/AC-8, unbounded `>= 5` on a deterministic AC-7 input. Documented as LOW.
- **#7 Resource leaks:** COMPLIANT. No file/socket/lock acquisition.
- **#8 Unsafe deserialization:** COMPLIANT. No pickle/eval/exec/yaml.load. `json.loads` in AC-6 test reads engine-written payload (controlled).
- **#9 Async pitfalls:** COMPLIANT. Entirely synchronous.
- **#10 Import hygiene:** ONE violation — `import json` inside the AC-6 test function body (`test_narration_pov_emission.py:812`); stdlib, belongs at module scope. LOW.
- **#11 Security / ReDoS:** COMPLIANT. Enumerated every new regex (`re.split(r"(;)")`, `\b{poss}\b(?=\s+\w)`, `\b{subj}\b(?:\s+(\w+))?`, `\b{obj}\b(?!\s+\w)`). All operate on disjoint `\s`/`\w` classes (no catastrophic backtracking) and on short single clauses; pronoun forms are validated against the closed `_PRONOUN_FORMS` key set BEFORE any pattern is built, so no user string reaches the regex. Pre-existing `interrupter_pat` `(?:\s+\w+)+?` lazy-nested concern is unchanged by this diff.
- **#12 Dependency hygiene:** COMPLIANT. No dependency changes.
- **#13 Fix-introduced regressions (meta):** **TWO VIOLATIONS** — the clause-split fix re-introduces two previously-correct behaviors as bugs (capitalization after `;`, 153-14 fragment after `;`). See Reviewer Assessment. Plus the `import json` rule-10/13 instance.
- **No Source-Text Wiring Tests (CLAUDE.md):** COMPLIANT. AC-8 (`test_anchor_recipient_sees_full_pronoun_agreement`) drives `_emit_event` → real per-recipient path; AC-6 reads the EventLog. Neither greps source.

## Reviewer Assessment

**Verdict:** REJECTED

The feature is well-built and the 8 ACs are met for the *tested* inputs (90/90 green), but my own boundary probing found **two real regressions introduced by the `;`-clause-split implementation choice** — both were CORRECT before this branch and are now broken. They share one root cause (clause boundaries are not propagated into `_is_sentence_start_in` / `_is_proper_noun_fragment`) and one small fix. Semicolons are common in narrator prose (the clause-local design exists *because* narration chains clauses with `;`), so these are not exotic.

### Blocking findings

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | **153-14 NPC-name-fragment protection regresses after a `;`.** `"The door opens; Vah Kantos bows to the council."` (PC `Kantos`) → `"The door opens; Vah you bow to the council."` — the suffix-NPC-name "Vah Kantos" loses its fragment guard and "Kantos" swaps to "you", producing garbled prose. Single-clause baseline (`"The envoy Vah Kantos bows…"`) is still protected (count 0), proving the `;`-split caused it. Re-opens a SHIPPED playtest fix (sq-playtest 2026-06-20/21). | `pov_swap.py` `_is_proper_noun_fragment` (`~:254`) calls `_is_sentence_start_in(text, before.start(1))` without `clause_is_sentence_start=is_first_clause`; `is_first_clause` is not threaded into the function. | Thread `is_first_clause` into `_is_proper_noun_fragment` and pass it through to the `_is_sentence_start_in` call. |
| [MEDIUM] | **Capitalization regression: a PC name swapped at the start of a post-`;` clause yields capital "You"/"Your" mid-sentence.** `"The door opens; Carl grabs his sword."` → `"The door opens; You grab your sword."` (should be lowercase "you"). Pre-split this was correct (lowercase, because `_is_sentence_start_in` saw the `;`). The new `clause_is_sentence_start` param is INEFFECTIVE here: after `re.split(r"(;)")` the clause is `" Carl…"` (leading space), so the name sits at idx 1, not 0 — the param only gates the `idx == 0` branch, while the real path is the whitespace-walkback `if j < 0: return True`. | `pov_swap.py` `_is_sentence_start_in` (`~:805`): the `if j < 0: return True` ignores `clause_is_sentence_start`. | Change `if j < 0: return True` → `return clause_is_sentence_start`. (Combined with the fix above, this resolves BOTH regressions.) |

**Rework routing:** testable logic regressions → `red` (TEA adds failing tests: post-`;` lowercase swap; post-`;` suffix-NPC-name stays protected) → Dev fixes (the two one-/two-line changes above). Both fixes are tiny; the rework is a clean, fast loop.

### Observations (tagged)

- **[VERIFIED] The 3 stale-test updates are legitimate, not gutting** — `test_adverb_…` and `test_interrupter_…they_them` keep their load-bearing `assert "works" not in out` verb-conjugation guards; `test_possessive_his_after_comma` keeps the #708 `assert "hi copper" not in out` de-pluralization guard. Evidence: `test_pov_swap.py:245/273/743`. Spec-authority (AC-1) correctly outranks the retired-pass assertions. [TEST] confirmed — test-analyzer agrees (high).
- **[HIGH] 153-14 fragment regression after `;`** — `pov_swap.py:_is_proper_noun_fragment`. [DOC] comment-analyzer independently flagged this exact call (`:264`, low conf); my probe confirmed it as a real behavioral regression, upgrading it from a doc note to a blocking bug.
- **[MEDIUM] Capitalization regression after `;`** — `pov_swap.py:_is_sentence_start_in` `j<0` branch. Confirmed by probe. The `clause_is_sentence_start` plumbing is dead for its stated purpose (leading-space clauses).
- **[MEDIUM] Within-clause same-pronoun-set NPC bleed** — `"Carl shoves him."` (him = an NPC) → `"You shove you."`; `"Carl grabs the guard and runs him through."` → `"…run you through."`. The clause-local gate converts ALL of the PC's pronoun-set pronouns in an armed clause, including a same-set NPC object/possessive. Inherent to a regex gate with no antecedent resolution (acknowledged in the module docstring) and explicitly narrower than the 2026-05-23 cross-clause bug — but NOT documented by Dev as a residual limitation, and a plausible combat construction. Non-blocking (accepted-approach limitation) but needs a Delivery Finding for the narrator pov_rules.md side. [EDGE] (subagent disabled — found manually).
- **[LOW] she/her object pronoun before a non-noun misclassified as possessive** — `"Vesna knocks her back."` → `"You knock your back."` (should be "knock you back"); `"watches her running"` → `"your running"`. The `(?=\s+\w)` lookahead treats any following word as a governed noun. Exactly the gap TEA flagged as a Question delivery finding; Dev reused the flagged hook. Non-blocking, known limitation. [EDGE]/[TEST].
- **[LOW] Format violation in the branch** — `test_narration_pov_emission.py` is not `ruff format`-clean (from TEA's RED commit `5f61a631`, not Dev's). `uv run ruff format` fixes it. Should be clean before merge. [TYPE]/preflight.
- **[LOW] `import json` inside the AC-6 test function body** — `test_narration_pov_emission.py:812`; stdlib import belongs at module scope. [RULE] rule-checker (rule 10/13, high).
- **[LOW] Stale module docstring opening line** — `pov_swap.py:7` still summarizes the module as rewriting "NAME references … plus verb conjugation and reflexive" with no mention of the now-live pronoun passes. The later "RE-INTRODUCTION" paragraph is correct, but the one-line summary is incomplete. [DOC] comment-analyzer (high).
- **[LOW] Pass label ordering 6→5→7 is confusing** — `pov_swap.py:~684`: the gated block runs possessive (Pass 6) before subject (Pass 5) for the she/her disambiguation, but the numeric labels read out of order with no note at the call site. [DOC] comment-analyzer (high).
- **[LOW] Stale docstring on `test_swap_count_matches_substitution_total`** — `test_pov_swap.py:~553` still says sentence-3 pronouns survive "under the (pronoun-pass retired) contract"; under 153-29 they survive because the gate is *not armed* (no PC name in that sentence), not because the passes are retired. The assertion still holds; the explanation is stale. [TEST] test-analyzer (medium).
- **[SIMPLE] No unnecessary complexity** — the clause-split is the minimal realization of TEA's clause-local directive; not over-engineered (subagent disabled — assessed manually). The bug is in a *missed* boundary case, not excess machinery.
- **[SEC] No security exposure** — pure string transform, ReDoS-clean, inputs validated before regex build (subagent disabled — confirmed via rule-checker rule 11).

### Data flow traced

Narrator prose (LLM output, semi-trusted) → `swap_to_second_person(text, target_name, pronouns)` validates `pronouns` against the closed `_PRONOUN_FORMS` set (fail-loud) → `_split_by_dialogue` (dialogue preserved) → `_split_into_sentences` (`.!?`) → **`_rewrite_sentence` splits on `;`** → per-clause `_rewrite_clause` (name passes → gated pronoun passes) → rejoin → OTEL `narration.second_person_swap` span. Wiring: `emitters._apply_pov_swap` (already present) calls this per recipient when `_visibility.anchor_pc` matches the recipient PC; canonical 3rd-person stays in the EventLog (AC-6 verified). The data flow is sound; the defect is purely in the per-clause sentence-boundary inference, which the `;`-split silently changed.

### Devil's Advocate

Argue the code is broken: it *is*, and a stressed table will see it. The whole reason `pov_swap` exists is so a career GM (Keith, per CLAUDE.md) cannot tell a human DM from the engine — and a capital "You" sitting mid-sentence right after a semicolon ("The torch gutters; You steady it.") is precisely the kind of mechanical tell that shatters that illusion. Narration uses semicolons constantly; the Dev's own test fixtures chain clauses with them ("Carl plants a boot; the moth shudders"). So the capitalization regression is not a corner — it is on the main road, and it fires every time a PC acts in a post-`;` clause. Worse, the 153-14 collision (a PC whose name is a token of an NPC's name) was a *real observed playtest bug* fixed only days ago; my probe shows "The door opens; Vah Kantos bows." now renders "Vah you bow" — a fix we already paid for, silently un-paid by the `;`-split. A confused player reading "Vah you bow to the council" on their tab will rightly think the engine is broken. What would a malicious or adversarial input do? Feed a sentence with many semicolons and PC-name/NPC-name collisions and you compound both bugs across one beat. What would a stressed filesystem or odd config produce? Irrelevant here — this is deterministic string logic, which is exactly why the regression is reproducible 100% of the time, not flaky. The one mercy is that both bugs trace to a single root — `_is_sentence_start_in` and `_is_proper_noun_fragment` were written for whole-sentence input and never told that a clause is not a sentence — so the fix is two lines plus threading one bool, and the existing 90 tests prove the non-boundary behavior is solid. That is the case FOR rejecting now rather than shipping: the cost to fix is trivial, the cost of a playtester re-finding "Vah you bow" is the project's core promise. Reject, add the two failing boundary tests, fix, re-green.

**Handoff:** Back to TEA (Amos Burton) for RED — add failing tests for the two post-`;` boundary regressions, then Dev.
## TEA Assessment — Rework (round-trip 1)

**Tests Required:** Yes — Reviewer REJECT with two testable logic regressions from the `;`-clause split.

**Tests Added (6, in `tests/agents/test_pov_swap.py`):**
- RED (4 — pin the regressions to pre-branch-correct behavior):
  - `test_subject_swap_at_start_of_post_semicolon_clause_stays_lowercase` — `"The torch gutters; Carl steadies it."` → `"…; you steady it."` (currently capital "You").
  - `test_subject_and_possessive_swap_after_semicolon_stays_lowercase` — `"The shield drops; Carl raises his guard."` → `"…; you raise your guard."`.
  - `test_possessive_name_swap_at_start_of_post_semicolon_clause_stays_lowercase` — Pass-1 path: `"The torch gutters; Carl's grip tightens."` → `"…; your grip tightens."`.
  - `test_suffix_npc_name_after_semicolon_left_intact_153_14_regression` — `"The door opens; Vah Kantos bows to the council."` (PC "Kantos") stays intact, count 0 (currently "Vah you bow").
- GREEN guards (2 — must STAY green so Dev's fix does not over-correct):
  - `test_first_clause_subject_swap_stays_capitalized_after_semicolon_fix` — a genuine sentence-initial swap stays capital "You".
  - `test_prefix_npc_name_after_semicolon_left_intact_green_guard` — the prefix collision after `;` ("Kantos Vah") remains protected.

**Status:** RED verified via testing-runner — exactly 4 fail (the regressions), 80 pass (2 green guards + all pre-existing), zero collateral failures.

**Rule coverage:** rule #6 (test quality) — every new test uses exact `==` plus a negative guard (`"; You steady" not in out`, `count == 0`); no vacuous assertions. Did NOT add tests for the non-blocking limitations (within-clause same-set NPC bleed, she/her object-before-particle) — those are accepted-approach limitations / Architect-scope Delivery Findings, and pinning the buggy output as "expected" would codify a bug and force out-of-scope antecedent resolution.

**Fix direction for Dev (both regressions, one root):**
1. `_is_sentence_start_in`: change the whitespace-walkback `if j < 0: return True` → `return clause_is_sentence_start`. (This is the real path for leading-space clauses; the existing `idx == 0` guard alone never fires.)
2. `_is_proper_noun_fragment`: thread `is_first_clause` in from `_rewrite_clause` and pass `clause_is_sentence_start=is_first_clause` to its `_is_sentence_start_in` call, so a preceding capitalized token at a non-first clause start is recognized as a fragment, not a sentence opener.

**Handoff:** To Dev (Naomi Nagata) for GREEN — make the two boundary fixes above; keep the 2 green guards green and all 90 prior tests passing.
## Dev Assessment — Rework (round-trip 2)

**Implementation Complete:** Yes — both Reviewer-blocking regressions fixed.

**Files Changed (this round):**
- `sidequest/agents/pov_swap.py` — two clause-boundary fixes sharing one root (the `;`-split fed single clauses to helpers written for whole sentences):
  1. `_is_sentence_start_in`: the whitespace walk-back `if j < 0: return True` → `return clause_is_sentence_start`. This is the path that actually fires for `;`-clauses (the leading space puts the swapped name at idx 1, so the `idx == 0` guard never ran). Fixes the capital-"You"-after-`;` regression.
  2. `_is_proper_noun_fragment`: added a keyword-only `is_first_clause` param and threads `clause_is_sentence_start=is_first_clause` into its `_is_sentence_start_in` call; both call sites (`_name_subj_sub`, `_name_bare_sub`) pass `is_first_clause`. Fixes the 153-14 suffix-NPC-name leak after a `;`. Docstring updated to note the clause context.

**Tests:** GREEN.
- pov suite + all consumers (test_pov_swap / _otel / narration_pov_emission / dialogue_extract / opening_pov_swap_71_5 / opening_emit_event_71_13 / narration_pov_regression): **115/115 passing** — the 4 RED rework tests now pass, the 2 green guards stayed green, all prior tests green.
- Full server suite: 13970 passed, 340 skipped, **3 failed — 2 known-baseline (witness count, _FakeHandle.drain) + 1 unrelated xdist isolation flake** (`test_watcher_events::test_publish_event_shape`, confirmed: passes `-n0` in isolation, zero pov_swap references). No new failures attributable to this change.

**Self-review:** the fix restores pre-branch-correct behavior without over-correcting — first-clause/sentence-initial swaps still capitalize (`"Carl steadies the torch; the flame holds."` → `"You steady the torch; …"`); the prefix-NPC collision after `;` stays protected. ruff check + format clean.

**Branch:** feat/153-29-mp-pronoun-localization (server) — pushed (commit 5483be1f).

**Handoff:** To Reviewer (Chrisjen Avasarala) for re-review. The two blocking regressions are resolved with the exact fix TEA/Reviewer specified; non-blocking findings (within-clause same-set NPC bleed, she/her object-before-particle, format/import-json/doc nits) remain as recorded Delivery Findings — out of the rejected-finding scope, flagged for Architect / a future polish pass.
## Subagent Results (re-review — round-trip 1)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | findings | 96/96 green, surgical 5-line fix, no smells; format-dirty carryover | confirmed 1 (format, LOW carryover), dismissed 0 |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | N/A — disabled (covered manually: probed fix + 15 boundary cases incl. cross-`;` gate, 3rd-clause, paragraph-break, fresh-`.`-sentence — all correct) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | N/A — disabled (pure fn, fail-loud ValueError intact) |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (4 RED genuine; green-guard startswith; 3 coverage gaps) | confirmed 2 (startswith LOW, gaps LOW), dismissed 0, deferred 0 — all non-blocking |
| 5 | reviewer-comment-analyzer | Yes | clean | none | N/A — rework comments/docstrings all accurate, no contradiction |
| 6 | reviewer-type-design | No | Skipped | disabled | N/A — disabled (new `is_first_clause: bool = True` annotated, immutable default) |
| 7 | reviewer-security | No | Skipped | disabled | N/A — disabled (no new regex; rule-checker confirmed) |
| 8 | reviewer-simplifier | No | Skipped | disabled | N/A — disabled (minimal 5-line surgical fix, no complexity added) |
| 9 | reviewer-rule-checker | Yes | findings | 1 (green-guard startswith, rule 6) + rule-13 META: j<0 change behavior-preserving | confirmed 1 (LOW), dismissed 0 |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 0 blocking, ~4 non-blocking confirmed (all LOW), 0 dismissed

## Reviewer Assessment (re-review — round-trip 1)

**Verdict:** APPROVED

The two blocking regressions from round 1 are fixed with a surgical 5-line change, and I independently verified the fix across 15+ boundary cases — the regressions are gone AND nothing new broke. The rule-checker's rule-13 meta-analysis is the load-bearing safety proof: the foundational `if j < 0: return True` → `return clause_is_sentence_start` change is **behavior-preserving for every caller** (all thread `is_first_clause` explicitly; `is_first_clause=True` returns `True` exactly as before; only non-first clauses change, which is the intended fix).

**The fix, verified:**
- `"The torch gutters; Carl steadies it."` → `"…; you steady it."` (lowercase) ✓; `"The shield drops; Carl raises his guard."` → `"…; you raise your guard."` ✓; possessive-name path `"…; Carl's grip tightens."` → `"…; your grip"` ✓.
- 153-14 after `;`: `"The door opens; Vah Kantos bows."` (PC "Kantos") → unchanged, count 0 ✓.
- **No over-correction** (the critical risk): a fresh `.`-sentence still capitalizes — `"The door opens. Carl steadies it."` → `"… You steady it."` ✓ — proving the fix distinguishes a `;`-clause-start from a sentence-start. First-clause swaps capital ✓; paragraph-break (`—\n\nLaverne…` → `You`/`Your`) ✓; multi-`;` third-clause lowercase ✓.
- **Cross-`;` gate integrity intact** (verified per test-analyzer's gap #2): `"Carl plants a boot; his grip tightens."` → `"…; his grip tightens."` (his STAYS — no cross-`;` possessive bleed); same for `he`/`him` in an unarmed clause. The 2026-05-23 NPC-bleed class is NOT re-opened.

**Observations (tagged):**
- **[VERIFIED] Both round-1 blocking regressions fixed** — empirically across 15+ cases; matches the 4 RED rework tests (now green) + 2 green guards.
- **[RULE] j<0 change is behavior-preserving** — rule-checker enumerated all 7 call sites; every one threads `is_first_clause`; no default-reliant caller. No new regression class. CONFIRMED, non-blocking (it's a correctness-preserving verification).
- **[TEST] 4 RED rework tests are genuine** — confirmed fail@5c571742, pass@fix, exact `==` with repr. Strong pins.
- **[TEST]/[RULE] green-guard `test_first_clause_subject_swap_stays_capitalized_after_semicolon_fix` uses `startswith` not `==`** — flagged by BOTH test-analyzer and rule-checker (LOW). It does verify the capitalization (its purpose), but the trailing unarmed clause is unasserted. Non-blocking test-polish; recommend tightening to `out == "You steady the torch; the flame holds."`.
- **[TEST] three coverage gaps** (3rd-clause name swap; cross-`;` possessive non-bleed guard; mid-clause suffix-NPC in a non-first clause) — I verified ALL THREE behave correctly in the impl; they are untested-but-correct, valuable as future-refactor sentinels. Non-blocking.
- **[DOC] comment-analyzer clean** — the rework's new docstrings/comments are accurate; pre-existing notes not contradicted.
- **[SIMPLE] minimal, surgical fix** — 5 production lines, no added complexity (subagent disabled — assessed manually).
- **[SEC] no new regex / no security surface** — rule-checker confirmed no new patterns; ReDoS-clean (subagent disabled — confirmed via rule-checker rule 11).
- **[TYPE] new `is_first_clause: bool = True`** annotated, immutable default (subagent disabled — confirmed via rule-checker rules 2/3).
- **[EDGE] boundary battery clean** — cross-`;`, multi-`;`, fresh-sentence, paragraph-break, fragment-after-`;` all correct (subagent disabled — covered by my probes).
- **[SILENT] no silent fallback** — fail-loud ValueError intact; the `is_first_clause=True` default is the conservative pre-rework value, not a silent alternative path (subagent disabled — confirmed via rule-checker A1).
- **[LOW] carryover non-blocking items** — `test_narration_pov_emission.py` still format-dirty (from the RED commit; `ruff format` needed before merge); `import json` in function body; the round-1 doc nits and accepted-limitation Delivery Findings (within-clause same-set NPC bleed, she/her object-before-particle). None block; recorded for finish/follow-up.

**Data flow traced:** narrator prose → `swap_to_second_person` (validates pronouns, fail-loud) → dialogue split → sentence split (`.!?`) → `;`-clause split → per-clause `_rewrite_clause(is_first_clause)` → name/pronoun passes using `_is_sentence_start_in(clause_is_sentence_start=is_first_clause)` and `_is_proper_noun_fragment(is_first_clause=…)` → rejoin → OTEL span. The clause-boundary context now flows correctly to both position helpers; canonical 3rd-person stays in the EventLog (AC-6).

**Pattern observed:** clause-context threaded uniformly through every position-sensitive helper — `sidequest/agents/pov_swap.py` `_is_sentence_start_in:835` (`return clause_is_sentence_start`) + `_is_proper_noun_fragment:270-278`. Good pattern: the boundary is a first-class parameter, not inferred.

**Error handling:** unchanged and correct — `swap_to_second_person` raises `ValueError` on empty name / unsupported pronouns (`pov_swap.py:875-879`); pure deterministic transform with no I/O.

**Handoff:** To SM (Camina Drummer) for finish-story.