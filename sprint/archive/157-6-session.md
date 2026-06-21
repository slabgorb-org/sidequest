---
story_id: "157-6"
jira_key: ""
epic: "157"
workflow: "trivial"
---
# Story 157-6: [CONTENT] Faction-tag fan-out: oz, wonderland, the_circuit

## Story Details
- **ID:** 157-6
- **Jira Key:** (none — Jira integration not configured for this project)
- **Workflow:** trivial
- **Stack Parent:** 157-5 (proof world: gulliver faction-tagging complete)
- **Branch Strategy:** gitflow (feat/157-6-faction-tag-fanout)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-21T09:05:29Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T08:16:54.342598+00:00 | 2026-06-21T08:22:20Z | 5m 25s |
| implement | 2026-06-21T08:22:20Z | 2026-06-21T08:55:27Z | 33m 7s |
| review | 2026-06-21T08:55:27Z | 2026-06-21T09:05:29Z | 10m 2s |
| finish | 2026-06-21T09:05:29Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Gap** (non-blocking): This story's `repos` is `content`, but the wiring proof (no-bleed
  tests) lives in `sidequest-server`. TWO feature branches are pushed: `feat/157-6-faction-tag-fanout`
  on both `sidequest-content` (the YAML) and `sidequest-server` (the 3 test files). SM-finish must
  create/merge BOTH PRs — **content FIRST, then server** (the server tests load live content from
  `../sidequest-content`, so the tagged content must be on content/develop before the server test
  branch merges). Same cross-repo coupling as story 71-24 / the fate-contest binding.
- **Improvement** (non-blocking): `genre_packs/wry_whimsy/worlds/wonderland/tropes.yaml`'s file
  header claims three `extends:` tropes (nonsense_as_authority, the_truth_telling_cat,
  the_pack_of_cards), but only `nonsense_as_authority` actually carries an `extends:` line in its
  body. Pre-existing inaccuracy (NOT introduced by 157-6); I tagged per the real bodies. Worth a
  content-doc cleanup pass.

### Reviewer (code review)
- **Improvement** (non-blocking, PRE-EXISTING): `genre_packs/wry_whimsy/worlds/oz/tropes.yaml`
  `green_spectacles` is section-commented "(specializes The Seam Reveal)" and listed in the file
  header as an `extends:` trope, but its body has **no `extends:` line** — so it does NOT inherit
  from The Seam Reveal at runtime. Either the comment/header is wrong or the `extends:` field was
  dropped. Same inaccuracy class as the wonderland header above; predates 157-6 (a behavior change
  to add `extends:` is out of this story's scope). Flag for a content owner to decide intent.
  Affects `genre_packs/wry_whimsy/worlds/oz/tropes.yaml`. *Found by Reviewer during code review.*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No deviations from spec. Replicated the 157-5 gulliver pattern exactly (factions =
  region `controlled_by`, `"*"` for genuine world-spines) across oz/wonderland/the_circuit,
  with the no-bleed test mirroring `test_157_5_gulliver_no_bleed.py`. Per-item faction
  assignments are content judgment within the spec (I used read-only analysis agents as
  advisory input, then verified each against the actual content/cartography text and
  corrected several — fighting_tree/kalidah to their Baum-canon zones, blood_feud_spark
  scoped to `[mods, rockers]`); none of this departs from the AC.
  → ✓ ACCEPTED by Reviewer: the implementation follows the spec — factions = cartography
  `controlled_by`, additive-only diff, real no-bleed wiring proof. The faction-assignment
  corrections are sound content judgment, not spec deviations. (The defects I found are
  documentation/test-label accuracy, not spec deviations — see the severity table.)

### Reviewer (audit)
- No UNDOCUMENTED spec deviations. The implementation matches AC1-4. However, the diff
  ships **documentation/test-labeling that misdescribes the code** (the `green_spectacles`
  "extends" mislabel and the oz-seed "trio" comment) — these are accuracy defects, captured
  as findings in the Reviewer Assessment severity table, not spec deviations.

## Sm Assessment

**Routing:** trivial workflow (phased: setup → **implement[Dev]** → review → finish).
Next phase owner is **Dev (Naomi Nagata)**. No TEA RED phase in trivial.

**Setup verification (all corrected/confirmed):**
- Story unblocked: depends_on 157-5 is DONE and merged to content `develop` (PR #483 / commit `db55af9`).
- Branches: content on `feat/157-6-faction-tag-fanout` (off `develop`) ✓; orchestrator on `main` ✓.
- Session moved from the content subrepo's `.session/` to the canonical `sprint/.session/`
  (root `.session` symlink → `sprint/.session`) so `pf handoff` can resolve it.
- Status set to `in_progress` manually (this project has **no Jira** — YAML is the only tracker).
- Phase Started timestamp is valid ISO-8601 (`+00:00`), not the " UTC" form that crashes complete-phase.
- Context file (`sprint/context/context-story-157-6.md`) was a thin auto-stub; **enriched by SM**
  with Problem, where-to-look Technical Approach (faction tables from each world's cartography.yaml,
  gulliver parity template, reference reads), Scope, and AC — because trivial has no TEA phase to
  flesh out intent.

**Scope for Dev:** Replicate the proven 157-5 gulliver pattern — add `factions:` lists to pooled/
home-less items in `bestiary.yaml`, `tropes.yaml`, `seed_tropes.yaml` for **oz, wonderland,
the_circuit**. Faction value = the region's `controlled_by` (from each world's `cartography.yaml`),
`"*"` for world-global. No invented factions, no engine changes (seams done in 157-2/3/4), no
validator (that's 157-7). Wiring proof = a no-bleed verification mirroring
`test_157_5_gulliver_no_bleed.py` covering the three new worlds — YAML edits alone are not "done."
Read `git -C sidequest-content show db55af9` for the exact YAML shape and the full context doc first.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest-content` (branch `feat/157-6-faction-tag-fanout`, off develop) — 9 files, +194:
  - `genre_packs/wry_whimsy/worlds/oz/{bestiary,tropes,seed_tropes}.yaml` — 13 + 7 + 11 items tagged
  - `genre_packs/wry_whimsy/worlds/wonderland/{bestiary,tropes,seed_tropes}.yaml` — 12 + 9 + 11
  - `genre_packs/road_warrior/worlds/the_circuit/{bestiary,tropes,seed_tropes}.yaml` — 9 + 6 + 12
  - Each pooled item got a `factions:` list (region `controlled_by`, or `"*"` for a world-spine) + inline rationale; each file got a header block explaining the scheme.
- `sidequest-server` (branch `feat/157-6-faction-tag-fanout`, off develop) — 3 files, +532:
  - `tests/genre/test_157_6_{oz,wonderland,the_circuit}_no_bleed.py` — wiring proofs mirroring 157-5.

**Tests:** 34/34 passing (GREEN) for the three new no-bleed files. 157-5 gulliver regression green (12/12). Pack-validator suite green (41 passed, 2 skipped). Both packs `validate pack` → PASS, 0 errors. All three worlds `load_genre_pack` clean, `world_is_zoned=True`, every pooled item tagged + referentially valid.

**AC status:**
1. ✅ Every pooled item in oz/wonderland/the_circuit (bestiary/tropes/seed_tropes) carries a `factions:` list.
2. ✅ Every faction value is a real cartography `controlled_by` or `"*"` — verified by the loader sweep + completeness tests. No invented factions.
3. ✅ No content bleed — behavioral `is_eligible` no-bleed tests per world (region item not eligible in wrong zone, eligible in its own; `"*"` spines eligible everywhere; `extends` tropes keep their factions through `_merge_trope`).
4. ✅ YAML valid; loader loads all three worlds clean; validator 0 errors.

**Branches:** both pushed (`feat/157-6-faction-tag-fanout` on sidequest-content + sidequest-server). No PRs created (SM creates/merges at finish).

**Handoff:** To review. NOTE the two-repo merge order in Delivery Findings — content PR must merge before the server test PR.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (34 pass, 157-5 regression green, 2 packs validate 0 errors, ruff clean) | confirmed 0, dismissed 0, deferred 0 |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | findings | 5 (1 medium, 4 low) | confirmed 1 (seam-zone), dismissed 0, deferred 4 (low "no action") |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (both high-confidence) | confirmed 2 (oz-seed "trio" + wonderland stale header), dismissed 0, deferred 0 |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations (87 instances across 13 + 4 rules) | confirmed 0, dismissed 0, deferred 0 |

**All received:** Yes (4 enabled returned; 5 disabled pre-filled per settings)
**Total findings:** 4 confirmed (1 reviewer-independent + 1 [TEST] + 2 [DOC]), 0 dismissed, 4 deferred (low, no-action)

## Reviewer Assessment

**Verdict:** REJECTED

The implementation is **correct** — faction assignments are sound, the diff is purely
additive (0 deletions; every added line is a `factions:` field or a comment), both packs
validate with 0 errors, and 34 no-bleed tests pass with genuine anti-vacuity guards. But
the diff ships **test/comment documentation that misdescribes the code**, including a test
that overstates its own coverage. These are MEDIUM accuracy defects in freshly-introduced
code, cheaply fixed; per "fix what you see, don't defer" they go back for a green rework
rather than shipping self-misdescribing tests to develop.

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [MEDIUM] | `green_spectacles` is described as an `extends:` trope and the `_merge_trope` regression guard, but it has **no `extends:` line** in its body (only `incomplete_companion` + `lost_princess` extend in oz). The test still validly asserts the faction scope, but it does NOT exercise the inheritance path it claims to — overstating coverage. | `sidequest-server/tests/genre/test_157_6_oz_no_bleed.py` docstring L15-18, `_assert_all_tagged` comment L105-106, `test_extends_trope_keeps_specific_faction_after_merge` L172-183; `sidequest-content/.../oz/tropes.yaml` faction-header ("three extends tropes …") | **Preferred:** repoint `test_extends_trope_keeps_specific_faction_after_merge` to `incomplete_companion` (which genuinely extends Helpful Companion, `[open_country]`) so oz has a real specific-faction-through-`_merge_trope` guard (parallel to gulliver's `the_petty_holy_war`); keep a renamed plain no-bleed test for green_spectacles. Fix the docstring + oz tropes header to say two extends tropes (incomplete_companion, lost_princess). |
| [MEDIUM] | oz seed header claims "the southern Glinda-journey trio (Fighting Trees, China Country, Hammer-Heads) all sit in glinda's Quadling country" — but Fighting Trees + Hammer-Heads are **bestiary** entries; only **one** seed (`oz_the_breakable_country`) is glinda-tagged. Misleading in a seed-file header. | `sidequest-content/.../oz/seed_tropes.yaml` faction-header | Reword: the one glinda-tagged seed is `oz_the_breakable_country` (China Country); the Fighting Trees / Hammer-Heads are bestiary entries, not seeds. |
| [LOW] | Pre-existing **file** headers overstate the `extends:` trope count and now contradict the accurate new comments in the same file: wonderland header L11 claims 3 extends (only `nonsense_as_authority` has it); oz file header similarly lists `green_spectacles`. | `wonderland/tropes.yaml` L11-13; `oz/tropes.yaml` file header | In-scope cleanup (these files are already modified): correct both pre-existing headers to match reality, resolving the in-file contradiction. |
| [MEDIUM] | Wonderland's seam zone (`no_one`) eligibility is never asserted — a `[the_queens_terror]` item against `{no_one}` is untested, so the "no pooled content at the threshold" invariant is documented but not mechanically guarded. | `test_157_6_wonderland_no_bleed.py` | Add `assert is_eligible(<card item>.factions, {SEAM}, zoned=True) is False` to confirm both halves are blocked at the seam. |

**Subagent dispatch tags:**
- `[TEST]` — test-analyzer: wonderland seam-zone eligibility untested (MEDIUM, confirmed); enchantment_not_kill not behaviorally tested but covered by completeness loop (LOW, deferred — no action); the_circuit has no extends-test because it has no extends tropes (LOW, correct).
- `[DOC]` — comment-analyzer: oz-seed "trio" comment misleading (confirmed); wonderland pre-existing header stale (confirmed).
- `[RULE]` — rule-checker: CLEAN, 0 violations across 87 instances (13 python checks + 4 project rules incl. No-Silent-Fallbacks, No-Stubbing, wiring-test, no-invented-factions). Note: rule-checker rated the green_spectacles test "compliant" on test-QUALITY (real assertions) — orthogonal to the [MEDIUM] mislabel finding, which is doc accuracy, not a rule violation.
- `[EDGE]` `[SILENT]` `[TYPE]` `[SEC]` `[SIMPLE]` — disabled via `workflow.reviewer_subagents`; not run. I assessed their domains myself (see Devil's Advocate + Rule Compliance): no boundary/silent-failure/type/security/complexity issues in additive content data + read-only test files.

### Rule Compliance (enumerated)
- **No Silent Fallbacks (SOUL):** ✓ Each test fixture fails loud (`assert "oz" in pack.worlds, f"..."`); `is_eligible`'s permissive-on-empty is documented engine behavior, not a content fallback. The strict load validator is 157-7 (correctly out of scope).
- **Crunch in genre / no invented factions:** ✓ All 90 tagged items use exact cartography `controlled_by` slugs or `"*"` — verified by loader sweep (problems=NONE), the 3 `test_zones_are_*` assertions, and rule-checker A4 (87 instances, 0 invented).
- **Additive-only content edits:** ✓ `--numstat` shows 0 deletions across all 9 files; every `+` line is a `factions:` field or comment.
- **Every test suite needs a wiring test:** ✓ The `test_*_is_a_zoned_world` per file IS the wiring proof — drives the real `world_is_zoned`/`is_eligible` predicates; without it the proof is vacuous (documented in-test).
- **`_merge_trope` factions propagation (157-5 fix):** ✓ Genuinely exercised by oz `lost_princess` (`"*"` through merge) and wonderland `nonsense_as_authority` (`"*"` through merge), plus `incomplete_companion` (specific faction) via the completeness loop. The ONLY defect is the green_spectacles MISLABEL (it isn't an extends trope) — coverage exists, the label lies.
- **Python checklist (13):** ✓ rule-checker clean — no bare excepts, mutable defaults, unsafe yaml (loader uses `safe_load`), resource leaks, async pitfalls, or import-hygiene issues; pathlib used; test deps already in dev extras.

### Observations (≥5)
1. `[VERIFIED]` Diff purely additive — `git diff --numstat develop...HEAD` = 0 deletions on all 9 content files; no existing creature/trope/seed content mutated.
2. `[VERIFIED]` Faction values referentially valid — loader sweep returns `problems=NONE`; `world_is_zoned=True` for all three (so eligibility is non-vacuous).
3. `[MEDIUM]` green_spectacles extends-mislabel (see table) — my independent finding; both rule-checker and test-analyzer assumed it extends and validated on that false premise.
4. `[DOC][MEDIUM]` oz-seed "trio" comment conflates bestiary + seeds (see table).
5. `[TEST][MEDIUM]` wonderland seam-zone eligibility untested (see table).
6. `[VERIFIED]` the_circuit's heavy `"*"` usage is justified by the file's own design note (port-city ecology + Thread entities transcend turf; only the Rocker guard dog is faction-owned) — not a lazy default.
7. `[VERIFIED]` extends regression IS genuinely guarded for oz (lost_princess) and wonderland (nonsense_as_authority) against the RESOLVED `world.tropes`.

### Devil's Advocate
Argue this is broken. First attack: the no-bleed tests are theater — `is_eligible` returns
permissive (`True`) on an empty active set, so if `valid_factions` ever resolved empty the
`"*"`-spine loops would vacuously pass. Rebuttal: each file's `test_zones_are_*` asserts the
exact non-empty cartography set first, and `test_*_is_a_zoned_world` asserts `world_is_zoned`
— together these make an empty/permissive short-circuit impossible without a louder failure
elsewhere. Second attack: the completeness tests hardcode counts (`== 13`, `== 9`, `== 12`)
— brittle, and a maintainer adding one creature breaks them. Rebuttal: the counts are
load-bearing (they guard the `_assert_all_tagged` loop from vacuously iterating an empty
list), match 157-5 precedent, and a deliberate breakage on content change is acceptable for
a wiring proof. Third attack — the real one: `test_extends_trope_keeps_specific_faction_after_merge`
claims to be the `_merge_trope` regression guard, but green_spectacles isn't an extends
trope, so a future dev who breaks `_merge_trope`'s specific-faction propagation would see
this test still pass and feel safe — the break would only surface via `incomplete_companion`
in the completeness loop, a weaker and non-obvious signal. That false confidence is the
actual harm, and it's why this is a REJECT not an approve-with-note: a test that lies about
what it guards is worse than no test there. Fourth attack: wrong faction assignments could
let content bleed anyway. Rebuttal: I independently re-derived the riskiest calls
(fighting_tree/kalidah/blood_feud) against cartography + Baum canon; they're defensible, and
any genuinely wrong slug would have failed the referential-validity sweep. Fifth: could the
additive YAML break the loader for a non-zoned world? No — `factions` defaults to `[]` and
`is_eligible` is permissive when unzoned; the field already shipped in gulliver. Net: the
content is sound; the documentation/test-labeling is not, and that's fixable in one green pass.

**Handoff:** Back to Dev (Naomi Nagata) for green rework — doc/comment/test-label fixes only, no logic changes. Re-review the delta after.

## Reviewer Re-Review (post-rework)

**Note on workflow mechanics:** the `trivial` workflow is linear (setup→implement→review→finish)
with no rework loop, and `complete-phase review green rework` advanced the phase to `finish`
(no `green` phase exists; `fix-phase` only moves forward). Per "fix what you see, don't defer,"
the REJECT findings were therefore reworked **inline in this session** and re-verified, rather
than deferred to a follow-up. Transparent reject→fix→re-verify→approve record below.

**Rework applied (all confirmed findings resolved):**
- [MEDIUM] green_spectacles extends-mislabel → FIXED. Repointed
  `test_extends_trope_keeps_specific_faction_after_merge` to `incomplete_companion` (which
  genuinely `extends: Helpful Companion`, `[open_country]`) — now a real `_merge_trope`
  specific-faction guard (verified: a dropped-factions regression would flip its eligibility
  and fail the test). Added `test_green_spectacles_scoped_to_the_emerald_city` so green_spectacles
  keeps its no-bleed coverage. Fixed the module docstring + completeness comment + oz tropes
  faction-header to "two extends tropes". (server commit `5a359b29`, content commit `379bd1a`)
- [MEDIUM] oz-seed "trio" comment → FIXED. Reworded to name the one glinda seed
  (`oz_the_breakable_country`) and note Fighting Trees / Hammer-Heads are bestiary entries.
- [LOW] pre-existing wonderland + oz file headers' stale extends counts → FIXED (corrected to
  match reality; resolves the in-file contradiction).
- [MEDIUM] wonderland seam-zone eligibility → FIXED. Added `test_no_half_content_eligible_at_the_seam`
  (neither half's content eligible at `no_one`; the `"*"` way-home spine still reaches it).

**Re-verification (evidence):** 36/36 of the 157-6 no-bleed tests pass (was 34; +2 from the
fixes); 157-5 gulliver regression green (12/12); ruff clean on all 3 test files; wry_whimsy +
road_warrior packs `validate pack` → 0 errors. Faction tags unchanged — the rework was
doc/test-label only. Two pre-existing items remain as delivery findings for a content owner
(green_spectacles / the_truth_telling_cat / the_pack_of_cards: section comments say "specializes"
but bodies lack `extends:` — out of 157-6 scope to change behavior).

**Updated Verdict:** APPROVED (all review findings resolved in-session; no Critical/High; the two
remaining items are pre-existing, documented delivery findings, not 157-6 regressions).

**Handoff:** To SM (Camina Drummer) for finish — create + merge BOTH PRs, **content first then
server** (per Dev's cross-repo Delivery Finding). Re-verify the merges landed.