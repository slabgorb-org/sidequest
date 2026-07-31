---
story_id: "158-61"
jira_key: ""
epic: "158"
workflow: "tdd"
---
# Story 158-61: beneath_sunden 107-2 gate hardening: extend template-compliance checks to all low-band creature specs + add converse spec->bestiary integrity test

## Story Details
- **ID:** 158-61
- **Jira Key:** (no jira)
- **Workflow:** tdd
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-31T14:07:46Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-31T12:57:44Z | 2026-07-31T12:59:22Z | 1m 38s |
| red | 2026-07-31T12:59:22Z | 2026-07-31T13:11:36Z | 12m 14s |
| green | 2026-07-31T13:11:36Z | 2026-07-31T13:53:20Z | 41m 44s |
| review | 2026-07-31T13:53:20Z | 2026-07-31T14:07:46Z | 14m 26s |
| finish | 2026-07-31T14:07:46Z | - | - |

## Technical Approach

Two non-blocking test-coverage gaps in the 107-2 creature-image gate (surfaced by the 158-60 review — content shipped correct, regressions only). Both live in the SERVER repo: `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`.

### Gap 1: Extend Template-Compliance Checks to All Low-Band Creature Specs

The four template-compliance tests (required-fields, style-free, no-text clause, non-proper-noun name) iterate a hardcoded `LOW_BAND_IDS` 6-tuple. The five specs added in 158-60 (darkmantle/piercer/shadow/stirge/grimlock) receive zero quality-gating — a style-leak and a proper-noun spec name were both empirically shown to pass.

**Fix:** Derive the id list from the bestiary 'low' tags (as the dynamic presence-test already does) so all four shape checks extend to every low-band spec. This closes the gap between hardcoded iteration and dynamic tag-based gating.

### Gap 2: Add Converse Spec→Bestiary Integrity Test

No converse referential-integrity test exists: nothing asserts every `creatures.yaml` spec id resolves to a real bestiary entry. A phantom orphan spec passed all 14 tests.

**Fix:** Add a converse test mirroring `test_all_room_bindings_reference_real_bestiary_ids` to verify bidirectional consistency: every spec in the creatures config must exist as a creature in the bestiary.

## Acceptance Criteria

- All four template-compliance tests (required-fields, style-free, no-text clause, non-proper-noun name) extend to every low-band spec by deriving the id list from bestiary 'low' tags, not hardcoded `LOW_BAND_IDS`.
- A new converse test asserts every creature spec id in the world's creatures configuration resolves to a bestiary entry (no phantom orphan specs).
- Both tests remain in `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`.
- No regression to the working 158-60 creature-image gate.

## Sm Assessment

Branch `feat/158-61-beneath-sunden-107-2-gate-hardening` off fresh `develop` (tip `51e031c5`,
which includes 158-57). No Jira — epic-158 stories are sprint-YAML-only, claim explicitly SKIPPED.

**Read this before writing a line of test code — this story inverts the usual TDD shape.**

Here the *deliverable itself is test code*. That makes it dangerously easy to skip straight to
writing the corrected gate and declare RED complete because "the new tests pass." That would
prove nothing. A gate that is too narrow does not fail — it **passes on input it should have
rejected**, which is exactly why these two gaps survived 158-60 review in the first place.

**So RED must demonstrate the hole, not the fix.** The 158-60 review already tells you precisely
how, because it did this empirically:

- **Gap 1** — a style-leak spec and a proper-noun spec name were both *shown to pass* the current
  gate. Reproduce that: introduce those non-compliant specs among the five ids 158-60 added
  (`darkmantle`, `piercer`, `shadow`, `stirge`, `grimlock`) and demonstrate the four
  template-compliance tests do not catch them, because they iterate the hardcoded `LOW_BAND_IDS`
  6-tuple which does not contain those ids.
- **Gap 2** — a phantom orphan spec *passed all 14 tests*. Reproduce that: a spec id resolving to
  no bestiary entry, currently undetected.

A RED that shows compliant input passing is worthless. RED here means: **bad input gets through
today.** GREEN means the derived-from-`low`-tags iteration and the converse integrity test catch
it. If you cannot make the current gate accept something it should reject, then the gap does not
exist and you should tell me that instead of manufacturing a test.

**Do not weaken the fixture to make a point.** The non-compliant specs are proof material, not
shipped content — they must not end up in real `creatures.yaml` content. `sidequest-content` is
NOT in this story's repo scope; this is server-test-only. If you conclude content must change,
stop and tell me rather than reaching into another repo.

**Doctrine that bears on Gap 2.** ADR-155 makes `bestiary.yaml` the single source of truth for
creature-image production, with `creatures.yaml` demoted to an optional per-world override. The
converse test is that ADR expressed as an executable check: an override that points at nothing in
the source of truth is a silent orphan, and per No Silent Fallbacks it should fail loudly. Mirror
`test_all_room_bindings_reference_real_bestiary_ids` — the existing idiom is right, it simply
only runs in one direction today.

**Sequencing note.** I deliberately scheduled this before 158-63 (per-room creature bindings,
which adds bindings across 33 rooms). Hardening the gate first means 158-63's content work is
gated by the stronger checks as it lands, rather than being retrofitted afterwards.

Peloton subagent mode: I drive each phase as a foreground subagent and verify every phase claim
myself. This is story 2 of 6 in epic 158.

## Tea Assessment

**Tests Required:** Yes
**Phase:** finish complete. Commit `44b573ef` (test-only, strictly additive), pushed to
`origin/feat/158-61-beneath-sunden-107-2-gate-hardening`. Working tree clean.

**Reproduce command (from `sidequest-server/`):**

```
uv run pytest -n0 -v tests/genre/test_beneath_sunden_creature_images_107_2.py
```

Expected today: **5 failed, 5 passed**.

### The shape I chose, and why

You were right that writing the corrected gate and watching it pass would prove
nothing. But there is a second trap right behind it: a poison test that "fails" for
a reason unrelated to the poison. So RED here is a set of **gate meta-tests**. Each
one copies the shipped `beneath_sunden` world into a tmp dir, changes exactly one
thing, points the module's `_world_dir` at the copy, runs *every* gate function in
the module, and asserts at least one rejects it.

A control test — `test_gate_accepts_the_shipped_world_unchanged` — pins the
unmodified copy as clean and **passes today**. It is load-bearing: without it, a
rejection could be coming from the copy rather than the poison. It also fails loudly
if the fixture path is wrong, instead of silently measuring nothing.

The gate set is enumerated from the module namespace, and meta-tests exclude
themselves via an attribute marker (`@_meta`), not a name prefix — so renaming a
test cannot silently fold a meta-test into the set of gates it is measuring, and a
gate added later is measured automatically.

No source-text grepping (`CLAUDE.md` §"No Source-Text Wiring Tests") — the real gate
functions execute against a real-shaped world on disk. No shipped content touched;
every poison lives in a pytest `tmp_path`. `sidequest-content` is untouched (`git
status` there is unchanged — the pre-existing `feat/flickering-reach-generics`
branch state I found it in).

### Holes demonstrated — 5 RED

**Gap 1** (name guard reaches only the hardcoded `LOW_BAND_IDS` six, not the eleven
entries the bestiary tags `low`):

| Test | Poison | Today |
|---|---|---|
| `test_gate_rejects_digits_in_a_low_band_spec_name` | `stirge.name` → `"The Small Thirst On 2 Fast Wings"` | passes every gate |
| `test_gate_rejects_quotes_in_a_low_band_spec_name` | `grimlock.name` → `'…Hunts By "Sound"'` | passes every gate |
| `test_gate_rejects_a_bad_spec_for_a_newly_low_tagged_entry` | 12th low-tagged bestiary entry + override name with a digit | passes every gate |

The third one is deliberate insurance on the AC's *mechanism*. AC1 says "derive the
id list from the bestiary `low` tags" — a Dev who instead widens the tuple from six
to eleven makes the first two tests green while leaving the gate exactly as brittle.
That third test fails against a hand-kept list of any length and only passes when the
iteration is genuinely tag-derived.

**Gap 2** (referential integrity runs one direction only — room→bestiary and
bestiary→spec exist; spec→bestiary does not):

| Test | Poison | Today |
|---|---|---|
| `test_gate_rejects_a_spec_with_no_bestiary_entry` | phantom `the_spec_that_binds_to_nothing` | passes every gate |
| `test_gate_rejects_a_typod_spec_id` | `grimlock` → `grimlok` | passes every gate |

The typo case is the one that will actually reach the repo. Nobody authors a phantom
on purpose. One dropped letter costs twice: the bespoke plate is silently detached
from the creature it was written for (which falls back to derived prose under
`name_is_secret: true`, so it still renders *something*), and an orphan override is
left behind. World parses, all gates pass, and the only symptom is a portrait that
quietly stopped being the one someone wrote. That is the No Silent Fallbacks / ADR-155
case in its purest form.

### What I deliberately did NOT test — and why the premise is partly stale

I probed every claim in the story before writing anything, against develop tip
`51e031c5`. **Two of the four named template-compliance limbs no longer have holes.**
The 158-60 review's empirical evidence was gathered against the *pre-*158-52 version
of this file; commit `5348a18e` ("retune to derived-source model", 2026-07-03)
reshaped six tests into four and closed those two limbs in passing. The finding was
filed accurately and then partially overtaken by a same-day commit.

| Story claim | Probe result | Action |
|---|---|---|
| style-leak passes | **Rejected** by `test_override_specs_are_well_formed_and_style_free` — it iterates *all* specs, not `LOW_BAND_IDS` | no test written |
| proper-noun spec name passes | **Rejected** by `test_every_low_tagged_bestiary_entry_is_renderable` via `_naming_handled`, which covers every low-tagged entry | no test written |
| no-text clause missing from a description passes | Passes — but **by design**: the 158-52 retune moved that clause to `visual_style.yaml positive_suffix`, and the module docstring says so explicitly | no test written |

So the residual Gap 1 hole is narrower than written: it is the **digits and quotes**
half of the name guard, which lives only in the hardcoded-tuple test and has no
dynamic counterpart. That is real, and the third test above shows it is not closed
under low-band growth either. I did not manufacture tests for the three rows above —
per your instruction, I am telling you instead.

AC1's wording ("all four template-compliance tests … extend to every low-band spec")
therefore over-describes the remaining work. The honest restatement, which is what
the RED tests encode: **the name guard (proper-noun, digits, quotes) must iterate the
bestiary-derived low set rather than `LOW_BAND_IDS`.** Your call whether to amend the
AC; I did not edit it.

### Scope I declined

One further hole I confirmed but did not test, per your "do not sprawl" instruction —
recorded as a Delivery Finding below rather than as a sixth RED test. It is fixed by
neither stated gap's fix direction, so it would have expanded Dev's GREEN beyond the ACs.

### Notes for Dev (GREEN)

- Do **not** satisfy these by widening `LOW_BAND_IDS`. `test_gate_rejects_a_bad_spec_for_a_newly_low_tagged_entry` exists specifically to fail that.
- The five RED tests assert only "*some* gate rejects this." They do not dictate which gate or how — restructure the four gates freely.
- The control test must stay green. If it goes red, the stronger gate has found something in shipped content, and that is a content question for Keith, not a test to loosen.
- The room-binding file (`test_beneath_sunden_room_binding_107_2.py`, 5 tests) is green and untouched; keep it that way.

**Test Files:**
- `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py` — +269 lines, strictly additive (0 deleted lines; I reverted incidental `ruff format` churn on pre-existing code to keep your diff review clean — see Delivery Findings)

**Tests Written:** 6 (5 RED + 1 control) covering 2 ACs
**Status:** RED — 5 failing for the intended reason (bad input passes today)
**Regression check:** full `tests/genre/` → 1241 passed, 49 skipped, 5 failed (exactly the 5 intended). `ruff check` clean, `pyright` clean on the file.

**Handoff:** To Dev for GREEN.

## Sm Assessment — RED review + AC correction (2026-07-31)

Verified independently: commit `44b573ef` is test-only and **strictly additive (+269/-0)**,
`sidequest-content` working tree clean (TEA stayed inside repo scope as instructed), and
`uv run pytest tests/genre/test_beneath_sunden_creature_images_107_2.py -n0` reproduces exactly
**5 failed / 5 passed**. The five failures assert on `_gates_rejecting(...) == []` — an empty
list of gates that rejected the poison, i.e. bad input passing today. That is a genuine RED for
this story's inverted shape, not a fix wearing a RED costume.

**AC1 IS FACTUALLY WRONG AND I AM CORRECTING IT.** TEA probed the premise before writing tests
and found it stale; I verified that myself rather than take it on report. AC1 says "all four
template-compliance tests ... iterate a hardcoded `LOW_BAND_IDS`." Grepping the file at develop
tip `51e031c5`, **exactly one** test touches `LOW_BAND_IDS` —
`test_low_band_shaft_ids_keep_non_proper_noun_guard` at line 156. The other three do not:
`test_override_specs_are_well_formed_and_style_free` (line 179) iterates **all** specs, and
`test_every_low_tagged_bestiary_entry_is_renderable` (line 111) covers **every** low-tagged entry
via `_naming_handled`.

The story description was written from the 158-60 review, which predates commit `5348a18e`
(158-52 retune, 2026-07-03). That retune reshaped this file from six tests to four and closed two
of the four claimed limbs in passing. The third claimed limb — the no-text clause — passes **by
design**, because 158-52 moved that clause to `visual_style.yaml positive_suffix`, as the module
docstring states.

**Corrected AC1:** *the name guard (proper-noun / digits / quotes) must iterate the
bestiary-derived low set rather than the hardcoded `LOW_BAND_IDS` tuple.* The residual hole is the
digits/quotes half, which exists only in the hardcoded-tuple test with no dynamic counterpart.
**AC2 (converse spec→bestiary integrity) is fully real and unchanged.** AC3 and AC4 unchanged.

TEA was right to refuse to manufacture tests for the three stale rows. A test written to satisfy
a stale AC would have asserted behaviour that already works, passed forever, and quietly
misrepresented this gate's coverage — which is the exact failure mode this story exists to fix.
Writing a green test against a phantom gap is worse than leaving the gap, because it manufactures
false confidence. Correct call.

**Dev: do NOT widen the tuple.** TEA planted `test_gate_rejects_a_bad_spec_for_a_newly_low_tagged_entry`,
which adds a *twelfth* low-tagged bestiary entry with a bad override. Hand-widening `LOW_BAND_IDS`
from six to eleven turns two of the five green and leaves that one red on purpose. It pins AC1's
**mechanism** (derive from the `low` tags) rather than its symptom. That is the test to design
against.

The sharpest of the five is `test_gate_rejects_a_typod_spec_id` — `grimlock` → `grimlok`. One
dropped letter silently detaches a bespoke plate from its creature, which still renders by falling
back to derived prose under `name_is_secret: true`, *and* leaves an orphan. The world parses,
every gate passes, and the only symptom is a portrait that quietly stopped being the one someone
wrote. That is precisely the class of silent failure ADR-155 and No Silent Fallbacks exist to
prevent, and it is a real risk for Jade as a content author working by paste-and-PR.

**Two of TEA's Delivery Findings are real gaps I am filing as follow-ups, not folding in** (2-point
story, and neither is in either gap's fix direction): wrong-*type* override fields pass every gate
(`threat_level: "very high"` with `tags: []` verified passing — 158-52 dropped the old int/tags
check and did not replace it, and `threat_level` selects render tier under ADR-155); and the name
guard covers only low-tagged entries, leaving the 7 mid/deep capstones with no name gating at all
even after this story lands.

**Formatting note:** this file already fails `ruff format --check` on `develop` (TEA verified by
stashing). Pre-existing drift, not this story's debt. TEA correctly reverted formatter churn on
pre-existing lines to keep the diff reviewable.

## Sm Assessment — GREEN review (2026-07-31)

Verified independently.

- **TEA's meta-tests untouched.** Diffing `44b573ef..876fd9d0` for any `def test_gate_(rejects|accepts)` line returns nothing — Dev changed the gates, not the specification that measures them. That was the one thing most worth faking on this story, since the "production code" here is itself test code sitting in the same file.
- **The trap held.** `LOW_BAND_IDS` is gone as a symbol; the only surviving mentions are prose inside TEA's meta-test docstrings. The guard now iterates `_low_tagged_ids(bestiary)` (line 85, used at 159). Dev derived the set from the bestiary `low` tags rather than hand-widening six to eleven, so `test_gate_rejects_a_bad_spec_for_a_newly_low_tagged_entry` — which plants a *twelfth* low-tagged entry — passes for the right reason. Widening would have left it red.
- Target file **11/11**. Full suite `-n0`: **15023 passed / 341 skipped / exit 0**, matching Dev's report exactly. The arithmetic reconciles: 15016 baseline + TEA's 6 (5 meta + 1 control) + Dev's 1 converse gate = 15023. No orphan count.
- `ruff check` clean on the touched file. `ruff format --check` still fails on it — pre-existing drift confirmed by Dev via `git stash`, byte-identical to `develop`, none of it on added lines. Correctly left alone rather than buried in this diff.
- `sidequest-content` working tree clean. Scope held.

**Dev's honest count correction, noted and credited.** My mandate said "→ 10 passed". Dev reported 11 and flagged the discrepancy rather than quietly matching my number: AC2 requires a genuinely new converse test, so the file grows from 10 to 11. Dev was right and I was wrong. Flagging a superior's stated figure instead of silently conforming to it is exactly the behaviour that makes this pipeline worth running.

**One item for the Reviewer's [DOC] lens.** TEA's meta-test docstrings (lines ~356, 368, 382, 444) still describe the hole in terms of "the hardcoded `LOW_BAND_IDS` six" — a symbol this commit deletes. The prose is now historical rather than descriptive. It is harmless to execution and arguably useful as provenance, but it names a symbol that no longer exists, which is the kind of thing that misleads the next reader. Reviewer's call whether to correct or keep as history; I am not blocking on it.

## Sm Assessment — review APPROVED, story accepted (2026-07-31)

Verdict accepted. Story is cleared to merge.

**The review method is worth recording, because it is the right one for this story's shape.**
Avasarala did not accept "the tests pass" — on a story whose deliverable *is* test code, that is
the cheapest available lie. She rebuilt the gate set from the module namespace and ran every
poison against **three** worlds: `develop`, a hypothetical hand-widened tuple (6→11), and `HEAD`.
The middle column is the whole argument. A Dev who hand-widened would have turned two meta-tests
green and looked finished, while the twelfth-entry test stayed red exactly as TEA designed. That
is a mechanism fix, proven, not asserted. She also confirmed each poison is caught by **exactly
one gate, and the right one** — not "some gate somewhere," which is how a too-broad gate
masquerades as coverage.

Two checks nobody asked her for, both load-bearing: all six original tuple ids are **still**
`low`-tagged, so the derived set is a strict superset rather than a coverage cut wearing a
widening's clothes; and Dev added `assert low_ids, "precondition: bestiary tags its low band"`
unprompted, which she verified by stripping every `low` tag and watching it fail loudly. That
assertion closes the empty-derivation vacuity trap — a derived set that silently derives *nothing*
gates nothing — and no AC or RED test demanded it. Credit to Dev for it.

**[DOC] ruling — KEEP, and I agree.** I flagged TEA's docstrings naming the now-deleted
`LOW_BAND_IDS`. Avasarala ruled them provenance rather than staleness: strip them and the
meta-test reads as arbitrary to the next person, whereas the assertion text only fires when
someone *regresses* the derivation, at which point "derive from the tags, don't widen by hand" is
exactly the instruction they need. One genuinely false present-tense fragment at `:368` ("the name
guard **reaches** only…") is a two-word fix for whoever next touches the file, not worth a round
trip. Correct call — I was reading it as drift; it is closer to a comment explaining why the test
exists.

**Subagents failed again — 0 of 4 returned, second story running.** Same as 158-57. She again
refused to stall the gate, recorded all four `Status: error`, declined to write "clean" rows for
agents that produced nothing, and ran all four domains herself with the method documented per row.
This is now a confirmed pattern, not a one-off, and it is surfaced to Keith as infrastructure.

**Findings NOT promoted into this story — deliberate, and the reasoning differs from 158-57.**
The [MEDIUM] (an override spec with a missing or empty `id` passes every gate, because
`_creatures_manifest:73` drops id-less entries before the converse gate ever sees them) is the
same silent-orphan class this story exists to close, and I considered pulling it in as I did with
the UI consumer on 158-57. I am not, for two reasons that did not apply there. First, AC2 is met
**as written** — "every spec *id* … resolves" cannot reach a spec that has no id, so this is a
genuine scope boundary rather than a half-delivered AC. On 158-57 the story's own AC was unmet
without the promotion; here it is met. Second, the fix lives in the manifest loader's filter, a
different component with blast radius beyond this gate, not in the seam we just hardened. Pulling
it in would mean redesigning a shared loader inside a 2-point test story. Filed instead at p2 so
it is not lost, and flagged as the same class so whoever takes it sees the connection.

Filed as follow-ups: wrong-*type* override fields passing every gate (TEA), the name guard
covering only low-tagged entries and leaving the 7 mid/deep capstones ungated (TEA), and the
id-less override spec (Reviewer [MEDIUM]). The three [LOW]s are recorded in the archived session
rather than filed — they are notes for the next person in this file, not work items.

## Delivery Findings

**Source:** 158-60 review delivery findings (archived session: `sprint/archive/158-60-session.md`)

- **Type:** Gap
- **Urgency:** non-blocking
- The hardcoded LOW_BAND_IDS list does not cover all low-band specs added in 158-60; test coverage is incomplete and a style-leak/proper-noun violation could pass.
- **Type:** Gap
- **Urgency:** non-blocking
- No converse integrity test exists to catch phantom spec entries with no corresponding bestiary creature; a config orphan passed all 14 tests.

### TEA (test design)

- **Gap** (non-blocking): A declared override field of the wrong TYPE passes every gate.
  `test_override_specs_are_well_formed_and_style_free` enforces "any field it does declare
  is non-empty" — but only for `name` and `description`. Empirically verified: setting
  `piercer.threat_level: "very high"` and `tags: []` passes all four gates. The 158-52
  retune dropped the old `test_low_band_specs_have_required_fields` check on
  `threat_level: int` / non-empty `tags` and did not replace it. `threat_level` selects the
  render tier under ADR-155, so a string there is a real render-pipeline break, not a
  cosmetic one. Affects `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py`
  (extend the declared-field loop to validate `threat_level` is `int` and `tags` is a
  non-empty list). NOT covered by either 158-61 gap's fix direction — deliberately left out
  of RED to hold the 2-point scope. *Found by TEA during RED probing.*
- **Gap** (non-blocking): The name guard (proper-noun / digits / quotes) covers **only**
  low-tagged entries. The 7 mid/deep capstone specs (`aboleth`, `lich`, `mummy_lord`,
  `vampire`, `otyugh`, `black_pudding`, `wight`) are outside `LOW_BAND_IDS` and outside the
  low-tag derivation, so they get no name gating at all — even after 158-61's fix lands.
  This world's "nothing is named" conceit applies to the whole roster, not the low band, and
  the marquee plates are the ones most likely to be re-authored. Affects the same file
  (consider deriving over *all* override specs rather than the low band specifically).
  *Found by TEA during RED probing.*
- **Improvement** (non-blocking): The story premise is partly stale — two of the four named
  template-compliance limbs (style-leak, proper-noun name) no longer have holes. The 158-60
  review's evidence predates commit `5348a18e` (158-52 retune, 2026-07-03), which reshaped
  this file from six tests to four and closed both in passing. Detail and probe evidence in
  the TEA Assessment above. Suggest amending AC1 to the residual truth: the **name guard**
  (proper-noun/digits/quotes) must iterate the bestiary-derived low set rather than
  `LOW_BAND_IDS`. *Found by TEA during RED probing.*
- **Improvement** (non-blocking): `tests/genre/test_beneath_sunden_creature_images_107_2.py`
  on `develop` already fails `uv run ruff format --check` (verified by stashing my changes
  and re-running). Pre-existing drift, not introduced here. I reverted the formatter's churn
  on pre-existing lines so 158-61's diff stays strictly additive (0 deleted lines); the file
  will still churn the next time anyone runs `just server-fmt`. Affects
  `sidequest-server` (a formatter sweep, separately). *Found by TEA during RED.*

### Reviewer (code review)

- **Gap** (non-blocking): An override spec with a **missing or empty `id`** passes every gate,
  including the new converse one. `_creatures_manifest` (line 73) filters
  `if isinstance(c, dict) and c.get("id")`, so an id-less entry is dropped from the specs dict
  *before* `test_creature_specs_reference_real_bestiary_ids` can ever see it. Verified empirically
  against a tmp-copy of the shipped world: an appended entry with no `id:` key, an entry with
  `id: ""`, and the `grimlock` spec with its `id:` line deleted **all pass all five gates**. This
  is the same silent-orphan class as the `grimlock`→`grimlok` typo this story exists to close —
  an author deleting or fat-fingering the `id:` line detaches the bespoke plate exactly as a
  mistyped id does, and the world still parses. The filter is pre-existing and untouched here, and
  AC2's literal wording ("every creature spec **id** … resolves to a bestiary entry") does not
  reach a spec that has no id, so this is out of scope for 158-61 — but it is the nearest
  remaining hole in the same wall, and it is squarely a No Silent Fallbacks case. Affects
  `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py` (assert every entry
  in the `creatures:` list is a mapping carrying a non-empty `id`, rather than silently skipping
  those that aren't). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The meta-tests assert only `_gates_rejecting(...)` is non-empty —
  they do not name the gate expected to do the rejecting. Today this is precise: I verified each of
  the five poisons is caught by exactly one gate, and the correct one (Gap 1 poisons → the retuned
  name guard; Gap 2 poisons → the new converse gate). But the contract is loose enough that any
  future gate strict enough to reject the poisoned fixtures *incidentally* would turn all five
  meta-tests green for the wrong reason, silently retiring the very specification they exist to
  hold. TEA chose the looseness deliberately so Dev could restructure gates freely during GREEN;
  now that the structure has settled, asserting the expected gate name would make the meta-tests
  vacuity-proof. Affects the same file. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The control test's baseline is one transformation short of the
  poison tests' baseline. `test_gate_accepts_the_shipped_world_unchanged` measures a **byte copy**
  (`_world_copy` → `shutil.copyfile`), while every poison test additionally round-trips the whole
  file through `yaml.safe_load`/`safe_dump` via `_rewrite`. I verified the round-trip does change
  the bytes but perturbs no gate — harmless today, because every gate reads through `safe_load`, so
  the round-trip is a no-op in the only domain the gates can observe. It stops being harmless the
  moment any gate inspects raw file *text* (encoding, key order, comments), at which point the
  control would still be green while the poison baseline had drifted. A one-line control variant
  that round-trips before asserting clean would close it. Affects the same file.
  *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The low-tag predicate now has **two** expressions rather than one.
  `_low_tagged_ids` (line 91) and the inline `low_tagged` comprehension in
  `test_every_low_tagged_bestiary_entry_is_renderable` (line 117) are the same
  `"low" in (e.get("tags") or [])` test written twice. Dev's assessment describes the helper as
  "factored out and reused," which is accurate for the name guard but not for the original inline
  site, which was left as-is. Harmless today; it is exactly the shape that drifts the next time
  low-band membership semantics change. Affects the same file (have the renderable gate call
  `_low_tagged_ids` too). *Found by Reviewer during code review.*

## Design Deviations

### TEA (test design)

- **RED asserts "the gate rejects X", not "the content satisfies X":** Spec (AC list) is
  written as content-shaped assertions; the RED tests are gate meta-tests that run the real
  gate functions against poisoned tmp-dir copies of the shipped world. Reason: a too-narrow
  gate cannot be shown broken by feeding it good content — it only reveals itself by
  accepting bad input, per the SM Assessment. No AC behavior was changed; the meta-tests are
  strictly a stronger way to pin the same ACs. Severity: minor.
- **Three of the four named template-compliance limbs are not tested:** Spec (AC1) says all
  four checks extend to every low-band spec. Probing showed style-leak and proper-noun are
  already covered post-158-52, and the per-description no-text clause is intentionally
  retired (moved to `visual_style.yaml positive_suffix`). Tests were written only for the
  limbs that reproduce as holes (digits, quotes) plus the derivation mechanism itself.
  Reason: SM instruction — do not manufacture a test to fit the story. Severity: minor.

### Dev (implementation)
- No deviations from spec. AC2 required "a new converse test," so the file's test count
  goes from 10 to 11 (not the "10 passed" figure named in the mandate's verification
  checklist) — flagged here for SM's independent verification, not logged as a deviation
  since adding the test is exactly what AC2 asked for.

### Reviewer (audit)

Every logged deviation stamped. No undocumented deviations found.

- **TEA — "RED asserts 'the gate rejects X', not 'the content satisfies X'"** → **✓ ACCEPTED by
  Reviewer.** Not merely defensible, it is the only shape that could have worked, and I verified it
  empirically rather than taking it on report. Reconstructing the `develop` gate set against
  poisoned tmp-copies, **all five poisons slip through with zero rejections** — the hole is real and
  the meta-tests are the thing that shows it. Against HEAD, all five are caught. A content-shaped
  assertion could not have expressed this, because a too-narrow gate does not fail on good input.
- **TEA — "Three of the four named template-compliance limbs are not tested"** → **✓ ACCEPTED by
  Reviewer.** Verified in code at HEAD, not from the narrative: the style-leak limb is covered by
  `test_override_specs_are_well_formed_and_style_free`, which iterates **all** specs
  (`for cid, spec in specs.items()`, line 194), not a subset; the proper-noun limb is covered for
  **every** low-tagged entry by `test_every_low_tagged_bestiary_entry_is_renderable` via
  `_naming_handled` (lines 131-142); and the no-text clause is pinned where 158-52 moved it, in
  `test_world_suffix_carries_no_text_clause` (line 209). Manufacturing tests for those three would
  have produced permanently-green assertions misrepresenting this gate's reach — the exact failure
  mode the story exists to correct. Refusing was the right call, and SM's AC1 correction ratifies it.
- **Dev — "no deviations; file grows 10 → 11 because AC2 requires a new test"** → **✓ ACCEPTED by
  Reviewer.** Independently confirmed by census: 11 test functions in the module, 5 gates + 6
  `@_meta` meta-tests, every meta-test correctly marked and none leaking into the measured set.
  Dev is right and the mandate's "10 passed" figure was wrong. Correcting a stated figure upward
  rather than quietly conforming to it is the behaviour I want to see reinforced.

## Dev Assessment

**Implementation Complete:** Yes

**How the low set is derived (Gap 1 / AC1):** Added `_low_tagged_ids(bestiary)` —
`{eid for eid, e in bestiary.items() if "low" in (e.get("tags") or [])}` — the same
predicate `test_every_low_tagged_bestiary_entry_is_renderable` already used inline for its
own `low_tagged` dict, now factored out and reused. Removed the hardcoded `LOW_BAND_IDS`
6-tuple entirely (no other reference to it existed anywhere in the repo — verified by
grep). `test_low_band_shaft_ids_keep_non_proper_noun_guard` now does
`for cid in sorted(_low_tagged_ids(bestiary)):` instead of `for cid in LOW_BAND_IDS:` —
reaching all 11 bestiary-tagged low entries (the original 6 shaft creatures + the 5
158-60 additions: darkmantle/piercer/shadow/stirge/grimlock), and closed under future
growth per `test_gate_rejects_a_bad_spec_for_a_newly_low_tagged_entry` (did NOT hand-widen
the tuple — that test stays green because there is no tuple left to widen). Dropped the
now-redundant `assert cid in bestiary` precondition line since ids are derived from the
bestiary itself and can't fail to be present in it.

**How the converse test resolves specs to bestiary entries (Gap 2 / AC2):** Added
`test_creature_specs_reference_real_bestiary_ids`, mirroring
`test_all_room_bindings_reference_real_bestiary_ids` in the sibling room-binding file:
loads `_creatures_manifest()` specs and `_bestiary_entries_by_id()`, asserts every spec id
in `creatures.yaml` is a key in the bestiary dict, listing any dangling ids. Placed as a
new top-level `test_` gate function (not `@_meta`), so it is picked up automatically by
`_gate_functions()`'s namespace enumeration and participates in every meta-test's
`_gates_rejecting` run — including the two Gap-2 poison tests
(`test_gate_rejects_a_spec_with_no_bestiary_entry`, `test_gate_rejects_a_typod_spec_id`),
both of which it now catches.

**Files Changed:**
- `sidequest-server/tests/genre/test_beneath_sunden_creature_images_107_2.py` — removed
  `LOW_BAND_IDS` tuple; added `_low_tagged_ids()` helper; retuned
  `test_low_band_shaft_ids_keep_non_proper_noun_guard` to iterate the derived low set; added
  `test_creature_specs_reference_real_bestiary_ids` (AC2). Did not touch any `@_meta`
  function or the shipped `sidequest-content` world. +44/-19 lines, one commit.

**Tests:** 11/11 passing in the target file (GREEN) — the 5 previously-RED meta-tests, the
control test, the 4 original gates (one retuned), and the 1 new AC2 gate. Full suite:
15023 passed / 341 skipped / 0 failed (baseline was 15016 passed / 341 skipped — the +7
delta is the 11-test file itself flipping from "5 pass/5 fail" to "11 pass," plus whatever
baseline drift already existed; zero new failures either way). `ruff check` clean on the
file. `pyright` clean on the file (0 errors/warnings/informations). `ruff format --check`
still fails on the file — verified byte-identical pre-existing drift via `git stash` (same
diff lines, same line numbers class, before and after my change); none of it is on lines I
added or touched with different formatting than the original.

**Branch:** `feat/158-61-beneath-sunden-107-2-gate-hardening` (pushed, commit `876fd9d0`)

**Handoff:** To next phase (verify or review)

### Delivery Findings

- No upstream findings during implementation. The two non-blocking gaps TEA filed
  (wrong-type override fields passing every gate; name guard not covering the 7 mid/deep
  capstones) are unchanged by this story's fix direction, as SM already noted — nothing new
  surfaced while implementing.
## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | No | error | none produced | N/A — domain re-run by Reviewer directly |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | No | error | none produced | N/A — domain re-run by Reviewer directly |
| 5 | reviewer-comment-analyzer | No | error | none produced | N/A — domain re-run by Reviewer directly |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | No | error | none produced | N/A — domain re-run by Reviewer directly |

**All received:** Yes (0 of 4 enabled specialists actually returned; 5 disabled via
`workflow.reviewer_subagents`. All four enabled specialists were spawned and never reported —
the same failure seen on the previous story. I am NOT claiming coverage from them. Every row above
marked `error` had its domain executed by me directly, with the evidence recorded in the assessment
below; the gate is unblocked on my own verification, not on theirs.)

**Total findings:** 6 confirmed (0 blocking), 0 dismissed, 0 deferred — all originated by Reviewer.

**Domains re-run by hand, and how:**
- *preflight* — `uv run pytest -n0` and default xdist on the target file (11 passed both ways),
  `ruff check` (clean), `ruff format --check` (fails; proven pre-existing by formatting the
  `origin/develop` blob, which fails identically, and by confirming no formatter-target line
  intersects any added hunk), both `sidequest-server` and `sidequest-content` trees clean.
- *test-analyzer* — purpose-built probes under scratchpad: gate enumeration, per-poison attribution,
  a `develop` counterfactual, a hand-widened-tuple counterfactual, an empty-derivation vacuity
  probe, and a YAML round-trip baseline probe.
- *comment-analyzer* — exhaustive `grep -n` of the deleted symbol across the file and repo, with
  each surviving mention classified docstring-vs-assertion-message.
- *rule-checker* — each added/changed function judged against No Silent Fallbacks, No Stubbing,
  No Source-Text Wiring Tests, Verify Wiring Not Just Existence, and ADR-155.

## Reviewer Assessment

**Verdict:** APPROVED

Nothing here is blocking. No Critical, no High. That is not a rubber stamp — I tried hard to break
this story and it held, and I want to be specific about what I actually executed, because on a
story whose deliverable *is* test code the cheapest possible lie is "the tests pass."

I did not take the pipeline's word for the three claims that carry this story. I rebuilt them.

### The load-bearing question: are TEA's meta-tests real, or do they pass vacuously?

They are real. I reconstructed the gate set from the module namespace and ran every poison against
three worlds — `develop`, a hand-widened counterfactual, and HEAD:

| Poison | on `develop` | hand-widened tuple (6→11) | HEAD |
|---|---|---|---|
| digits in `stirge` name | slips through | caught | caught — name guard |
| quotes in `grimlock` name | slips through | caught | caught — name guard |
| 12th low-tagged entry + digit name | slips through | **slips through** | caught — name guard |
| phantom orphan spec | slips through | slips through | caught — converse gate |
| typo `grimlock`→`grimlok` | slips through | slips through | caught — converse gate |

Four things fall out of that table, and all four matter.

**The control is doing real work.** The unmodified copy is rejected by *nothing*, so a rejection can
only have come from the poison and not from the tmp-dir copy. That is the whole structural claim of
the story and it holds.

**Each poison is caught by exactly one gate, and it is the right one.** Not "some gate somewhere" —
Gap 1 poisons land on the retuned name guard, Gap 2 poisons land on the new converse gate, one
rejection each, no incidental overlap. The meta-tests are not passing for a coincidental reason.

**Every poison genuinely slips through on `develop`.** The RED was RED for the stated reason.

**The trap held, which is the finding I care most about.** Column three is the whole point. A Dev
who hand-widened `LOW_BAND_IDS` from six to eleven would have turned two meta-tests green and
looked finished — and `test_gate_rejects_a_bad_spec_for_a_newly_low_tagged_entry` would have stayed
red, exactly as TEA designed. Dev did not do that. `_low_tagged_ids` (line 91) derives the set from
the bestiary `low` tags at runtime, the guard consumes it at line 159, and the twelfth-entry poison
is caught. Dev fixed the mechanism, not the symptom.

**[VERIFIED]** No non-`AssertionError` escaped any gate in any scenario — `_gates_rejecting`
(line 316) catches `AssertionError` only, so any other exception propagates and *fails the
meta-test loudly* rather than being silently recorded as "no rejection." That is the correct
polarity for No Silent Fallbacks, and I confirmed empirically it never fires today.

### Did the widening quietly cost coverage?

This was my sharpest suspicion: replacing a hand-kept list with a derivation can silently *shrink*
the covered set, and it would look like a widening. It did not. **[VERIFIED]** all six original
`LOW_BAND_IDS` ids (`gnaw_swarm`, `rope_spider`, `hold_skeleton`, `shaft_goblin`, `grave_ghoul`,
`harrier_pack_leader`) are still `low`-tagged in the shipped bestiary, so the derived set is a
strict superset: 11 = the original 6 + the 5 that 158-60 added. Nothing fell out.

**[VERIFIED] [EDGE] Dev closed the classic derived-set trap, and this is the best line in the
diff.** When a hardcoded list becomes a derivation, the degenerate case is an *empty* derivation —
the loop then iterates nothing and the guard passes vacuously forever. Dev added
`assert low_ids, "precondition: bestiary tags its low band"` (line 160). I stripped every `low` tag
from a copy of the bestiary and confirmed the guard fails loudly instead of passing on an empty
set. Unprompted by any AC or any RED test. That is the difference between a derivation and a
derivation you can trust.

### Does the new converse gate actually catch an orphan?

**[VERIFIED]** Yes, and specifically the case that will really reach the repo. The
`grimlock`→`grimlok` typo is caught by `test_creature_specs_reference_real_bestiary_ids` (line 226)
**and by nothing else** — I confirmed the name guard cannot catch it, because with the spec id
changed the guard takes its `spec is None` branch and the world's top-level `name_is_secret: true`
satisfies it. So the new gate is not redundant with anything; it is the only thing standing between
a one-letter slip and a portrait that quietly stops being the one someone authored. That is the
ADR-155 / No Silent Fallbacks case in its purest form, and it is exactly the trap that would bite
Jade authoring by paste-and-PR.

### Findings

No blocking issues. All six are recorded in `## Delivery Findings` under `### Reviewer (code
review)`; none duplicates the two SM has already filed.

| Severity | Tag | Issue | Location |
|----------|-----|-------|----------|
| [MEDIUM] | [TEST] [RULE] [SILENT] | An override spec with a **missing or empty `id`** passes every gate. `_creatures_manifest` drops id-less entries before the converse gate can see them. Verified: no `id:` key, `id: ""`, and `grimlock` with its `id:` line deleted all pass all five gates. Same silent-orphan class as the typo — pre-existing filter, outside AC2's literal wording, so non-blocking | `test_beneath_sunden_creature_images_107_2.py:73` |
| [LOW] | [TEST] [EDGE] | Meta-tests assert only that *some* gate rejects, never which. Precise today (one correct gate each, verified), but a future over-strict gate would turn all five green for the wrong reason | `:366, :390, :441, :482, :504` |
| [LOW] | [TEST] | Control measures a **byte copy**; poisons additionally round-trip through `safe_load`/`safe_dump`. Harmless today (verified: bytes differ, gates unperturbed — every gate reads through `safe_load`), but the baselines are not the same object | `:291, :301` |
| [LOW] | [SIMPLE] | The low-tag predicate now has two expressions: `_low_tagged_ids` and the inline comprehension left behind in the renderable gate. Dev's "factored out and reused" is true of the name guard only | `:91` and `:117` |
| [LOW] | [DOC] | Four surviving `LOW_BAND_IDS` mentions name a symbol this commit deletes — docstrings `:356`, `:382`; assertion failure messages `:368`, `:444` | as listed |
| [LOW] | [DOC] | `test_low_band_shaft_ids_keep_non_proper_noun_guard` is now misnamed — it no longer walks the six shaft ids | `:145` |

### [DOC] ruling on the surviving `LOW_BAND_IDS` prose — you asked me to call it

**KEEP.** Not blocking, and not worth a commit on its own.

The symbol is gone as code — I confirmed zero references anywhere in the repo outside this file's
prose. What survives is four mentions, and they are two different kinds of text that deserve
different treatment. The two in **docstrings** (`:356`, `:382`) are provenance, and provenance is
load-bearing here: without it, the next reader finds a meta-test that pokes `stirge` and `grimlock`
for no visible reason. "These ids were outside the old hardcoded six" *is* the reason. Delete it and
the test looks arbitrary — that is a worse failure than naming a dead symbol.

The two in **assertion failure messages** (`:368`, `:444`) I looked at harder, because those are
read at failure time by someone under pressure, and telling them to perform a fix that is already
in the tree would be a genuine trap. It survives that test: those messages only ever fire if
someone *regresses* the derivation, and at that moment "derive the id list from the bestiary tags"
and "widening `LOW_BAND_IDS` by hand does not fix this" are precisely the right instructions. They
read as stale but function as restoration guidance.

The one honestly misleading fragment is the present tense in `:368` — "the name guard **reaches**
only the hardcoded `LOW_BAND_IDS` six." That states as current fact something this commit made
false. If anyone touches this file again, changing that to past tense is a two-word fix worth making
in passing. I am not spending a round trip on it now.

### Rule compliance — every added or changed function, against every applicable rule

**[RULE] [VERIFIED] No Source-Text Wiring Tests — compliant, and this was the rule most at risk.**
`_gate_functions` (line 276) enumerates `globals()` for callables named `test_*` lacking
`_is_gate_meta`. I checked it against the prohibition and against the stated exception. It never
reads source text — no `read_text()` on a source file, no regex over a module. It interrogates
*runtime objects and their attributes*, which is the sanctioned "reflection-based" exception the
rule carves out. And the gates themselves are executed for real against a real-shaped world on
disk, which is the rule's own recommendation #2 (fixture-driven behavior test). Compliant on both
the letter and the intent.

**[RULE] [VERIFIED] The `@_meta` marker is attribute-based, not name-based** (line 266) — so
renaming a meta-test cannot silently fold it into the set of gates it measures. I verified the
census: 11 functions, 5 gates, 6 meta, every meta correctly marked, zero leakage. This is the
detail that keeps the whole construction honest, and it is the right call.

**[RULE] No Silent Fallbacks** — the one genuine hit is the id-less override drop at line 73,
filed above as [MEDIUM]. I am not dismissing it, and I want to be explicit about why it is not
blocking rather than hand-waving it: the filter is pre-existing, untouched by this diff, and AC2 is
worded as "every creature spec **id** … resolves," which cannot reach a spec that has no id. It is
the next story's work, not this one's failure. Everywhere else the rule is honoured — the empty-low
precondition (`:160`), the empty-specs assertion (`:190`), and `_gates_rejecting` re-raising
non-assertion exceptions all fail loudly.

**[RULE] No Stubbing** — no placeholders, no skeletons, no dead code. `LOW_BAND_IDS` was *removed*
rather than left orphaned, which is the rule applied correctly.

**[RULE] Verify Wiring Not Just Existence / Every Test Suite Needs a Wiring Test** — the new gate is
not merely defined, it is *reached*: my census confirms `test_creature_specs_reference_real_bestiary_ids`
is picked up by `_gate_functions`' namespace enumeration and participates in all six meta-tests. Its
existence and its wiring are separately verified.

**[RULE] OTEL Observability Principle — not applicable, and I checked rather than assumed.** The
diff is test-only and touches no subsystem, emits no narration, and makes no engine decision. There
is nothing for the GM panel to detect. Requiring spans here would be cargo cult.

**[RULE] [VERIFIED] ADR-155 — this diff is the ADR expressed as an executable check.**
`bestiary.yaml` is the single source of truth: the low set is derived from *bestiary* tags, and the
converse gate enforces that `creatures.yaml` — the optional override — cannot point at anything the
source of truth has never heard of.

**[TYPE]** Nothing structural. `_low_tagged_ids` returns `set[str]`, consumed through `sorted()` at
line 161 so iteration is deterministic. One cosmetic mismatch: `_meta` is annotated
`Callable[..., None]` while `_gate_functions` returns `list[Callable[[], object]]`. `pyright` is
clean and the runtime behaviour is correct. Not worth a finding.

**[SEC]** Nothing. `yaml.safe_load` throughout, no `yaml.load`, no deserialization of untrusted
input, no secrets, no network, no auth surface. The one real risk on a story that mutates world
files is writing to shipped content — **[VERIFIED]** every write is confined to `tmp_path`:
`_world_copy` reads the real world and writes only into the pytest tmp dir, and every `_rewrite`
call site passes the local `world` handle. `sidequest-content` is byte-clean after a full run.

### Data flow traced

The user here is a **content author** — Jade, pasting a world override in a PR — and the input is a
single line of YAML. Traced end to end: `creatures.yaml` `id:` field → `_creatures_manifest`
(`:61`) parses via `safe_load` and builds `specs` keyed by id, **silently dropping any entry
lacking one** → `test_creature_specs_reference_real_bestiary_ids` (`:226`) diffs those keys against
`_bestiary_entries_by_id` → any id absent from the bestiary is collected into `dangling` and the
gate fails loudly, naming the offending ids.

Safe because a *wrong* id now fails at author time instead of at render time. Not yet safe because
a *missing* id never reaches the gate at all — the drop at `:73` is the one place this flow still
swallows the author's mistake, which is precisely why I filed it rather than waving it through.

### Pattern observed

Good pattern, worth naming so it propagates: **the meta-test with a live control**
(`:331`, `:316`). Gate coverage is normally unfalsifiable — a too-narrow gate is silent by
construction, which is exactly how the two 158-60 findings survived review. Running the real gate
functions against a poisoned copy, with a control pinning the copy itself as clean, converts
"is this gate wide enough?" from a code-reading exercise into a test that fails. That is a reusable
answer to a recurring problem in this repo and I would like to see it again.

### Devil's Advocate

Let me argue this is broken, because approving is the easy path and I do not take it for free.

*The strongest case against:* this story hardens a gate on exactly one world out of twenty-two.
Every other world with a `creatures.yaml` override carries the identical orphan risk today, and I
confirmed no generic cross-world validator exists anywhere in the suite. So a reader could
reasonably say the win is a rounding error — one world gated, twenty-one still exposed, and the
next author who trips this will not be in `beneath_sunden`. Against that: the file follows the
established world-specific idiom (`test_beneath_sunden_room_binding_107_2.py:103` is world-scoped
too), the AC scoped it to this world deliberately, and generalizing is a real story, not a
rider on a 2-pointer. I record the generalization as worth filing and decline to block on it.

*The confused-author case*, which worries me more, is the one I filed as [MEDIUM]. Jade does not
mistype ids on purpose — she pastes a block and drops or renames a key. I probed five variants of
that. Two are caught (wrong id, wrong-case id). Three are not: no `id:` key, empty `id:`, and a
deleted `id:` line. The story closes the variant it was scoped to and leaves the adjacent ones open,
which is honest scoping rather than a defect — but it does mean the headline "orphan overrides now
fail loudly" is narrower than it sounds, and I would rather say so plainly than let it stand.

*The stressed-filesystem case:* `_world_copy` does `dest.mkdir()` with no `exist_ok`, so a collision
raises rather than silently reusing a directory — correct polarity. A missing world file raises
`FileNotFoundError` out of `shutil.copyfile`, uncaught, failing loudly. Both good.

*The vacuity case*, which is where I expected to find blood: the meta-tests assert only that the
rejection list is non-empty. That is a genuinely weak contract, and if the gates ever grow one
over-strict member, all five go green for the wrong reason and nobody learns. I filed it. It is not
blocking today because I *measured* today's attribution rather than assuming it — one gate per
poison, the correct one, every time.

*The one that would have sunk it* — a derivation that silently covers less than the tuple it
replaced — I checked directly and it does not happen, and Dev's empty-set precondition means it
cannot happen quietly later either.

Verdict stands.

### Deviations

All three logged deviations audited and stamped ACCEPTED under `### Reviewer (audit)`. No
undocumented deviations found — I diffed for any change to a `@_meta` function and confirmed Dev
changed the gates without touching the specification measuring them.

**Handoff:** To SM (Camina Drummer) for finish-story. I have not merged, opened a PR, or run a
handoff marker — those are yours.