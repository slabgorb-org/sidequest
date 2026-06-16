---
story_id: "120-6"
jira_key: ""
epic: "120"
workflow: "trivial"
---
# Story 120-6: 120-5 review follow-ups (doc/comment-only)

## Story Details
- **ID:** 120-6
- **Jira Key:** (none — personal project, Jira skipped)
- **Workflow:** trivial
- **Stack Parent:** none

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-16T02:28:01Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-16T02:17:08Z | 2026-06-16T02:18:56Z | 1m 48s |
| implement | 2026-06-16T02:18:56Z | 2026-06-16T02:22:47Z | 3m 51s |
| review | 2026-06-16T02:22:47Z | 2026-06-16T02:28:01Z | 5m 14s |
| finish | 2026-06-16T02:28:01Z | - | - |

## Story Summary

Refresh 4 stale RED-status docstrings in `tests/genre/test_road_warrior_vessel_calibration.py` to GREEN (parser + damage content shipped in 86-5/120-2, tests pass) and add a clarifying inline comment on the `parse_vessel_tags(item.model_dump())` dict-bridge; test-file/comment-only, NO production code, NO logic change.

### Acceptance Criteria
1. All 5 text edits applied in the one test file. No assertion/logic changes whatsoever.
2. The file's 12 tests stay GREEN; ruff check + ruff format clean.
3. Zero production-code changes (git diff touches only `tests/genre/test_road_warrior_vessel_calibration.py`).

### Specific Edits Required

**Edit 1 (Line ~216, docstring of `test_starting_mounted_weapons_fit_in_starting_rig_slots`):**
- DROP the stale "— RED until mount_slots parses." sentence. The test is GREEN and the paragraph immediately below it already explains the merged-catalog approach; the "RED until" line now self-contradicts.

**Edit 2 (Line ~17, MODULE docstring):**
- Current: "RED until Dev (a) promotes speed/mount_slots to first-class parsed fields ... and (b) authors damage blocks on the mounted rig weapons"
- BOTH shipped (speed/mount_slots are first-class in vessel_tags.py per 86-5; mounted rig weapons carry CWN damage blocks per 120-2).
- Refresh to a GREEN statement (e.g. "GREEN as of 86-5 / 120-2: speed/mount_slots parse and mounted weapons carry CWN damage blocks").

**Edit 3 (Line ~95, docstring of `test_every_vessel_item_parses_cleanly`):**
- Current: "RED until speed/mount_slots are first-class (the parser contract this story introduces)"
- Parser contract is live; refresh to GREEN.

**Edit 4 (Line ~195, docstring of `test_mounted_rig_weapons_carry_vehicle_damage`):**
- Current: "RED today — mounted weapons ship `damage: None`."
- Damage blocks now authored; refresh to GREEN.

**Edit 5 (Line ~240, the `parse_vessel_tags(catalog[rig_ids[0]].model_dump())` call):**
- Add a brief inline comment explaining WHY model_dump() is used — `parse_vessel_tags` takes a plain `dict` (has an `isinstance(item, dict)` guard), so the typed `CatalogItem` is dumped to a dict; no field aliases exist on CatalogItem today so id/tags survive the dump.

### Out of Scope
The reviewer's heavier suggestion to add a `CatalogItem`-accepting overload/helper to production `sidequest/game/vessel_tags.py`. That is deferred as YAGNI (speculative; no aliases exist, the dict contract works). This story is comment/docstring text ONLY.

## Delivery Findings

No upstream findings.

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- No upstream findings. Pure doc/comment refresh; underlying parser (86-5) + content (120-2) are correct, tests stay green.

### Reviewer (code review)
- **Improvement** (non-blocking): The genre-tier `genre_packs/road_warrior/inventory.yaml` header comment (~line 13) still claims to own "mount weapons" that 120-2 relocated to the world tier — comment-analyzer confirmed the genre-tier catalog now has zero `mounted`+`rig` items; they live exclusively in `worlds/the_circuit/inventory.yaml`. Stale header, in the CONTENT repo, out of scope for 120-6 (server). Affects `sidequest-content/genre_packs/road_warrior/inventory.yaml` (refresh the header comment). *Found by Reviewer during code review.* [DOC][LOW]
- No other upstream findings.

## Impact Summary

**Upstream Effects:** No upstream effects noted
**Blocking:** None

### Deviation Justifications

1 deviation

- **Edit 2 touched slightly more of the module docstring than the literal "RED until" line, for coherence + factual accuracy**
  - Rationale: A "GREEN as of ..." line sitting directly below "Today every weapon ships damage: None" would be self-contradicting — the same class of staleness the story exists to fix. The path was also factually wrong post-120-2. Both are within the spirit of "refresh the stale module docstring," not new scope.
  - Severity: trivial
  - Forward impact: none — comment text only; no code, no test behavior.

## Design Deviations

No design deviations — story is documentation-only.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Edit 2 touched slightly more of the module docstring than the literal "RED until" line, for coherence + factual accuracy**
  - Spec source: .session/120-6-session.md, Edit 2
  - Spec text: "Refresh to a GREEN statement (e.g. 'GREEN as of 86-5 / 120-2: speed/mount_slots parse and mounted weapons carry CWN damage blocks')."
  - Implementation: Replaced the "RED until Dev (a)...(b)..." paragraph with the GREEN statement AND adjusted the adjacent AC1 bullet's tense ("Today every ... ships `damage: None`" → "Before Plan 5 every ... shipped `damage: None`"; "Plan 5 gives" → "gave"), and corrected the mounted-weapon path from `genre_packs/road_warrior/inventory.yaml` to `worlds/the_circuit/inventory.yaml` (the 120-2 world-tier move).
  - Rationale: A "GREEN as of ..." line sitting directly below "Today every weapon ships damage: None" would be self-contradicting — the same class of staleness the story exists to fix. The path was also factually wrong post-120-2. Both are within the spirit of "refresh the stale module docstring," not new scope.
  - Severity: trivial
  - Forward impact: none — comment text only; no code, no test behavior.

### Reviewer (audit)
- **Dev deviation — Edit 2 also tensed the AC1 bullet and corrected the mounted-weapon path** → ✓ ACCEPTED by Reviewer: both changes are correct and necessary. A "GREEN as of…" line directly below "Today…ships damage: None" would self-contradict (the exact staleness class this story fixes), so the tense fix is required for coherence. The path correction (`genre_packs/road_warrior/inventory.yaml` → `worlds/the_circuit/inventory.yaml`) is factually validated — comment-analyzer confirmed the genre-tier catalog has zero `mounted`+`rig` items and all five live at the world tier. Within the spirit of "refresh the stale module docstring," not new scope. No undocumented deviations found.

**Routing:** trivial workflow (phased) → handoff to **dev** for the `implement` phase. 1pt, p3, chore.

**Origin:** the three non-blocking findings Reviewer Avasarala logged on story 120-5. Deliberately filed as a separate tracked story (not folded into 120-5) because they were out of 120-5's stated scope; now actioned per Bossmang's "fix the followups."

**Scope is comment/docstring text ONLY, one file.** All edits land in `sidequest-server/tests/genre/test_road_warrior_vessel_calibration.py`. No production code, no assertion or logic changes. Four stale "RED until/today" markers (lines ~17, ~95, ~195, ~216) refresh to GREEN — the parser (speed/mount_slots, 86-5) and the mounted-weapon damage content (120-2) both shipped, so the markers now misdescribe a green suite. Plus one clarifying inline comment on the `parse_vessel_tags(...model_dump())` dict-bridge (finding #3, comment-only treatment).

**Explicitly deferred (YAGNI):** the reviewer's heavier suggestion to add a `CatalogItem`-accepting overload to production `vessel_tags.py`. No aliases exist; the dict contract works. Not worth a speculative production change. Dev: do NOT touch production code.

**DoD:** all 5 text edits applied; the file's 12 tests stay GREEN; ruff check + format clean; `git diff` touches only that one test file.

**Jira:** none — personal project. Claim skipped.

**No blockers.** Branch `feat/120-6-120-5-followups-doc-cleanup` cut from latest develop.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `tests/genre/test_road_warrior_vessel_calibration.py` — 5 doc/comment edits, no logic:
  1. Module docstring (`:11-19`): "RED until..." → "GREEN as of 86-5 / 120-2"; AC1 "Today...damage: None / Plan 5 gives" tensed to past; corrected mounted-weapon path to `worlds/the_circuit/inventory.yaml` (see deviation).
  2. `test_every_vessel_item_parses_cleanly` docstring: "RED until speed/mount_slots are first-class" → GREEN (parser requires both; fails loud via `InvalidVesselTagsError`).
  3. `test_mounted_rig_weapons_carry_vehicle_damage` docstring: "RED today — mounted weapons ship `damage: None`" → GREEN (every mounted rig weapon carries a CWN damage block).
  4. `test_starting_mounted_weapons_fit_in_starting_rig_slots` docstring: dropped the self-contradicting "— RED until mount_slots parses."
  5. Inline comment added at the `parse_vessel_tags(catalog[...].model_dump())` call explaining the dict-bridge (finding #3, comment-only — the production `CatalogItem` overload was deferred YAGNI per the SM scope).

**Tests:** 6/6 in the file passing (GREEN), 0 skipped — docstring/comment edits are behavior-neutral. ruff check + format clean.

**Scope:** comment/docstring text only, one file, no production code. `git diff` = 1 file (+17/-11). Zero remaining "RED until/today" markers in the file.

**Branch:** feat/120-6-120-5-followups-doc-cleanup (sidequest-server, base develop) — pushed.

**Handoff:** To review (Chrisjen Avasarala / Reviewer).

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — 6/6 GREEN, 0 skipped, ruff clean, 1-file diff |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings |
| 4 | reviewer-test-analyzer | Yes | clean | none | N/A — all 5 hunks docstring/comment-only; `slots=` line byte-identical; no behavior change |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | dismissed 1 (HIGH but factually incorrect — line evidence), confirmed 1 non-blocking out-of-scope [DOC][LOW] |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings |
| 9 | reviewer-rule-checker | Yes | clean | none (0 / 15 rules) | N/A — doc-only, no executable change, GREEN claims consistent |

**All received:** Yes (4 enabled returned, 5 disabled skipped)
**Total findings:** 0 confirmed blocking, 1 confirmed non-blocking ([DOC][LOW], content-repo, out of scope), 1 dismissed (factually incorrect subagent claim)

## Reviewer Assessment

**Verdict:** APPROVED

A doc/comment-only refresh that does exactly its job: four stale "RED until/today" status markers in `tests/genre/test_road_warrior_vessel_calibration.py` become accurate GREEN statements, and one inline comment documents the `model_dump()` dict-bridge. Tests GREEN (6/6, 0 skipped), zero executable lines changed, zero rule violations. No Critical/High.

**Data flow traced:** none — there is no executable change. The `slots = parse_vessel_tags(catalog[...].model_dump())` line is byte-identical (test-analyzer + rule-checker both confirm); only a comment was added above it. The four other hunks are entirely inside triple-quoted docstrings.

### Observations

- [VERIFIED] All five hunks are docstring/comment text only — evidence: test-analyzer + rule-checker both confirm the `slots=` statement is unchanged and no assert/return/assignment was added, removed, or reworded. Behavior is provably identical; preflight's 6/6 GREEN corroborates.
- [DOC] comment-analyzer finding #1 (`:243`, the new `model_dump()` comment, HIGH confidence) — **DISMISSED.** The subagent claimed a `CatalogItem` would fail with `AttributeError` on `item.get("tags")` (`vessel_tags.py:119`), making the comment's "isinstance guard" rationale misleading. I re-read `vessel_tags.py:111-112`: `raw_id = item.get("id") if isinstance(item, dict) else None` short-circuits a non-dict to `None` (the `.get` is never called — no AttributeError), then line 112 raises a clean `InvalidVesselTagsError`; line 119 is unreachable for a non-dict. The comment ("dict-typed, has an isinstance guard, so dump the CatalogItem") is accurate; the subagent's premise is wrong and its suggested rewrite would *introduce* the inaccuracy. Evidence: `sidequest/game/vessel_tags.py:111-112`. **Challenged:** subagent finding overridden with line-level proof.
- [DOC] comment-analyzer finding #2 (`:18`, LOW) — **CONFIRMED, non-blocking, out of scope.** The test-file GREEN claim is accurate, but a *stale header comment* in the content repo (`genre_packs/road_warrior/inventory.yaml:~13`) still claims to own the relocated mount weapons. Different repo, not this diff. Logged as a delivery finding.
- [VERIFIED] The new GREEN claims are factually grounded — evidence: comment-analyzer independently verified `vessel_tags.py:184-191` makes speed+mount_slots required (raises `InvalidVesselTagsError`), and that all five mounted rig weapons live in `worlds/the_circuit/inventory.yaml` with populated `damage` dicts (genre tier has zero). The Dev path-correction is therefore correct, not a regression.
- [RULE] reviewer-rule-checker: 0 violations / 15 rules. Checks #1-#5, #7-#12 have no applicable surface (no executable change); #6 test-quality and #13 fix-regression both pass (no assertion altered, GREEN claims consistent with the green assertions).
- [TEST] reviewer-test-analyzer: clean — explicitly confirmed no executable code changed, every changed line is docstring or `#` comment.
- [SILENT] / [TYPE] / [SEC] / [SIMPLE] / [EDGE] — no applicable surface in a docstring/comment diff (the four diff-hunt specialists for these are also disabled via settings). Self-assessed: nothing introduced.

### Rule Compliance

Python lang-review checklist (13) + project rules, against the diff (rule-checker corroborated, 0 violations):

- **#6 Test quality** — no assertion added/removed/weakened; the `slots=` call is byte-identical; no new skips. The file's existing guards (len≥5, spec-table equality, mounted≤slots, missing-id assert) are untouched and non-vacuous. PASS.
- **#13 Fix-introduced regressions / comment accuracy** — every refreshed marker is consistent with the green test it documents; the path correction is factually validated; the `model_dump()` comment is accurate (see dismissed finding). PASS.
- **Doc-only must not alter executable code** (project rule) — confirmed by test-analyzer + rule-checker: docstrings + one `#` comment only. PASS.
- **No new stale/misleading comments** — the one HIGH-confidence challenge was verified false against `vessel_tags.py:111-112`; comment stands accurate. PASS.
- #1-#5, #7-#12 — no applicable surface (no executable/import/dependency/path/logging change). PASS by vacuity, explicitly confirmed.

### Devil's Advocate

Let me try to break a doc-only change. The first attack: did Dev sneak a behavior change into a "doc" PR? This is the classic doc-PR failure mode — a stray edit to an executable line hidden among comment churn. I checked the one hunk that sits next to executable code (the `model_dump()` comment at `:243`): the `slots = parse_vessel_tags(catalog[rig_ids[0]].model_dump()).mount_slots` line appears in the diff as unchanged context, not a `+`/`-` line, and both test-analyzer and rule-checker independently confirm byte-identity. Preflight's 6/6 GREEN with identical assertions seals it. No behavior leaked in.

Second attack: a doc fix that *replaces* stale lies with *new* lies is worse than leaving the RED markers — a confident wrong GREEN is more dangerous than an obvious stale RED. So I treated every new GREEN claim as a hostile assertion to disprove. "speed/mount_slots are first-class required fields, fails loud via InvalidVesselTagsError" — verified against `vessel_tags.py:184-191`. "every mounted rig weapon lives in worlds/the_circuit/inventory.yaml with a CWN damage block" — verified: genre tier has zero mounted+rig items, world tier has all five with damage dicts. The path Dev corrected was genuinely wrong before. So the GREEN claims are not new lies; they're accurate.

Third attack, the subtle one: the new `model_dump()` comment. comment-analyzer came in HIGH-confidence that it inverts cause and effect. That is exactly the kind of finding I should respect — except I have to verify the *reviewer-subagent* too, not just the author. Reading the control flow, the subagent's claimed failure path (AttributeError on `.get("tags")`) is unreachable: the `isinstance(item, dict)` guard short-circuits a CatalogItem to `raw_id=None` and the function raises `InvalidVesselTagsError` two lines earlier. So the comment's framing is correct and the subagent's correction would itself be wrong. The lesson cuts both ways — adversarial review means challenging the specialist's confidence with code evidence, not just the author's.

What's left that could bite? Only the out-of-scope stale header in the content repo — real, but a different repo and a different story. Logged, not blocked. Nothing here rises above [DOC][LOW]. Approved.

**Handoff:** To SM (Camina Drummer) for finish-story.