---
story_id: "157-5"
jira_key: ""
epic: ""
workflow: "trivial"
---
# Story 157-5: [CONTENT] Tag gulliver by faction (proof world) + verify no bleed

## Story Details
- **ID:** 157-5
- **Jira Key:** (not applicable — no Jira integration)
- **Workflow:** trivial
- **Stack Parent:** 157-4 (done)

## Workflow Tracking
**Workflow:** trivial
**Phase:** finish
**Phase Started:** 2026-06-21T06:01:44Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T05:27:58Z | 2026-06-21T05:29:46Z | 1m 48s |
| implement | 2026-06-21T05:29:46Z | 2026-06-21T05:50:29Z | 20m 43s |
| review | 2026-06-21T05:50:29Z | 2026-06-21T06:01:44Z | 11m 15s |
| finish | 2026-06-21T06:01:44Z | - | - |

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

### Dev (implementation)
- **Gap** (blocking — fixed in this story): 157-4 added `factions` to `TropeDefinition` but `resolve.py::_merge_trope` never propagated it, so any world trope using `extends:` silently lost its faction scope. Affects `sidequest-server/sidequest/genre/resolve.py` (now propagates `factions`, child-overrides/empty-inherits, with 2 regression tests). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the strict load validator (story 157-7) should validate the **resolved** trope list (post-inheritance), not the raw authored `tropes.yaml`, since `_merge_trope` is where an `extends` child's factions are realized. Affects `sidequest-server/sidequest/genre/loader.py` (validator placement — after `resolve_trope_inheritance`). *Found by Dev during implementation.*
- **Improvement** (non-blocking): the genre-tier `wry_whimsy/tropes.yaml` + `seed_tropes.yaml` (parents of oz/wonderland content) are still untagged. 157-6's oz/wonderland fan-out should tag world-tier content; any world trope that `extends` a genre parent without its own factions will inherit `[]` and (correctly) fail the 157-7 validator in a zoned world. Affects `sidequest-content/genre_packs/wry_whimsy/` (157-6 scope). *Found by Dev during implementation.*

### Reviewer (code review)
- **Improvement** (non-blocking): the no-bleed proof stops at the `is_eligible` predicate; it never drives the real production seam (`trope_tick`/`monster_manual_inject`) against the real gulliver pack with a resolved `GameSnapshot`. The seam→predicate wiring IS covered by the approved 157-2/3/4 synthetic tests, so coverage composes — but the file docstring's "END-TO-END" claim overstates this file's scope. Affects `sidequest-server/tests/genre/test_157_5_gulliver_no_bleed.py` (soften the docstring, and ideally add one real-pack-through-seam test in 157-6's generalized proof). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): no behavioral no-bleed assertion exists for the `the_yahoo_within` trope (`[the_houyhnhnm_assembly, no_one]`); only the bestiary Yahoos are individually probed. The completeness check would still pass if a future author mistagged it `["*"]`. Adding a `the_yahoo_within`-not-eligible-in-Lilliput assertion would also lock the `no_one`-is-a-zone-not-a-wildcard semantic. Affects `sidequest-server/tests/genre/test_157_5_gulliver_no_bleed.py` (fold into 157-6). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): two gulliver header comments could mislead a future author (e.g. Jade on 157-6): `tropes.yaml` conflates the three `*` tropes with the three `extends:` tropes (overlapping but distinct sets — `the_petty_holy_war` is `extends` but voyage-scoped, `priced_violence_marks_the_yahoo` is `*` but standalone); `seed_tropes.yaml` says "every hook is voyage-anchored" right before noting one seed spans two voyages. Affects `sidequest-content/genre_packs/wry_whimsy/worlds/gulliver/{tropes,seed_tropes}.yaml` (reword in 157-6, which rewrites these headers). *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 5 findings (0 Gap, 0 Conflict, 0 Question, 5 Improvement)
**Blocking:** None

- **Improvement:** the strict load validator (story 157-7) should validate the **resolved** trope list (post-inheritance), not the raw authored `tropes.yaml`, since `_merge_trope` is where an `extends` child's factions are realized. Affects `sidequest-server/sidequest/genre/loader.py`.
- **Improvement:** the genre-tier `wry_whimsy/tropes.yaml` + `seed_tropes.yaml` (parents of oz/wonderland content) are still untagged. 157-6's oz/wonderland fan-out should tag world-tier content; any world trope that `extends` a genre parent without its own factions will inherit `[]` and (correctly) fail the 157-7 validator in a zoned world. Affects `sidequest-content/genre_packs/wry_whimsy/`.
- **Improvement:** the no-bleed proof stops at the `is_eligible` predicate; it never drives the real production seam (`trope_tick`/`monster_manual_inject`) against the real gulliver pack with a resolved `GameSnapshot`. The seam→predicate wiring IS covered by the approved 157-2/3/4 synthetic tests, so coverage composes — but the file docstring's "END-TO-END" claim overstates this file's scope. Affects `sidequest-server/tests/genre/test_157_5_gulliver_no_bleed.py`.
- **Improvement:** no behavioral no-bleed assertion exists for the `the_yahoo_within` trope (`[the_houyhnhnm_assembly, no_one]`); only the bestiary Yahoos are individually probed. The completeness check would still pass if a future author mistagged it `["*"]`. Adding a `the_yahoo_within`-not-eligible-in-Lilliput assertion would also lock the `no_one`-is-a-zone-not-a-wildcard semantic. Affects `sidequest-server/tests/genre/test_157_5_gulliver_no_bleed.py`.
- **Improvement:** two gulliver header comments could mislead a future author (e.g. Jade on 157-6): `tropes.yaml` conflates the three `*` tropes with the three `extends:` tropes (overlapping but distinct sets — `the_petty_holy_war` is `extends` but voyage-scoped, `priced_violence_marks_the_yahoo` is `*` but standalone); `seed_tropes.yaml` says "every hook is voyage-anchored" right before noting one seed spans two voyages. Affects `sidequest-content/genre_packs/wry_whimsy/worlds/gulliver/{tropes,seed_tropes}.yaml`.

### Downstream Effects

Cross-module impact: 5 findings across 4 modules

- **`sidequest-server/tests/genre`** — 2 findings
- **`sidequest-content/genre_packs`** — 1 finding
- **`sidequest-content/genre_packs/wry_whimsy/worlds/gulliver`** — 1 finding
- **`sidequest-server/sidequest/genre`** — 1 finding

### Deviation Justifications

1 deviation

- **Story expanded from content-only to content + server (one engine fix)**
  - Rationale: 157-4 added `factions` to `TropeDefinition` but never threaded it through `_merge_trope`, so the three gulliver tropes that `extends:` genre parents (`the_satire_turns_on_you`, `the_petty_holy_war`, `the_compulsion_to_reembark`) silently lost their tags → `[]` → permissive. `the_petty_holy_war` ([the_lilliput_court]) would have bled into all four voyages, so the story's "verify no bleed" acceptance gate was unreachable without the fix. User (Keith) explicitly authorized the engine fix ("just fix the model stuff too").
  - Severity: minor
  - Forward impact: positive for 157-6 (the oz/wonderland fan-out can rely on `extends`-trope factions surviving) and 157-7 (the validator should run on RESOLVED tropes, which now carry inherited factions).

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Story expanded from content-only to content + server (one engine fix)**
  - Spec source: `.session/157-5-session.md` → SM Assessment, "Scope (single repo — content): ... No engine work — the engine already consumes `factions:`/`controlled_by:` tags."
  - Spec text: the story was scoped content-only on the premise that all four engine seams (157-2/3/4) fully consume the new `factions` field.
  - Implementation: also patched `sidequest-server/sidequest/genre/resolve.py::_merge_trope` (+2 unit tests) to propagate `factions` through trope inheritance, and added a real-pack no-bleed proof test (`tests/genre/test_157_5_gulliver_no_bleed.py`).
  - Rationale: 157-4 added `factions` to `TropeDefinition` but never threaded it through `_merge_trope`, so the three gulliver tropes that `extends:` genre parents (`the_satire_turns_on_you`, `the_petty_holy_war`, `the_compulsion_to_reembark`) silently lost their tags → `[]` → permissive. `the_petty_holy_war` ([the_lilliput_court]) would have bled into all four voyages, so the story's "verify no bleed" acceptance gate was unreachable without the fix. User (Keith) explicitly authorized the engine fix ("just fix the model stuff too").
  - Severity: minor
  - Forward impact: positive for 157-6 (the oz/wonderland fan-out can rely on `extends`-trope factions surviving) and 157-7 (the validator should run on RESOLVED tropes, which now carry inherited factions).

### Reviewer (audit)
- **Story expanded from content-only to content + server** → ✓ ACCEPTED by Reviewer (Avasarala): sound and necessary. The `_merge_trope` field-drop was a genuine half-wiring of 157-4 (model field added, inheritance call-site missed). `the_petty_holy_war` ([the_lilliput_court], an `extends` trope) would have lost its scope to `[]`/permissive and bled into all four voyages — the story's "verify no bleed" gate was literally unreachable without it. User authorized it explicitly. The fix is minimal (one dict entry mirroring the sibling `tags`/`triggers`/`escalation` pattern), guarded by 2 RED-first regression tests, and introduces no regression to the other wry_whimsy worlds (empty-inherits-empty keeps oz/wonderland untagged tropes permissive until 157-6 tags them). Verified clean by rule-checker (13 checks, the fix consistent with the established merge idiom) and preflight (full genre suite green minus 3 pre-existing).
- No undocumented deviations found. The faction model, `*` sentinel usage, and the npcs.yaml exemption all match the 157-1 design spec.

## Story Summary

This is the CONTENT-side proof for epic 157 (Faction/zone-scoped content eligibility). 

**Context:** The engine seams are complete (157-2, 157-3, 157-4), but the actual content in the gulliver world still lacks faction tags. The problem: in session 2026-06-20-gulliver-e721409c, a 4th-voyage Yahoo surfaced on the 1st-voyage Lilliput shore because:

1. Creatures in the bestiary have no `factions:` tag, so they are eligible everywhere
2. The format_area_creatures function did zero location filtering

**The work:** 
- Tag the gulliver world's locations/regions/NPCs/creatures/tropes by faction using the design spec (docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md)
- Add `factions: [...]` field to creatures and content that belong to specific regions
- Verify no bleed: a 4th-voyage creature must NOT appear on 1st-voyage shore after tagging

**Reference:**
- Design spec: `/Users/slabgorb/Projects/oq-1/docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md`
- Gulliver world factions (from cartography.yaml `controlled_by` fields):
  - `the_lilliput_court` — Voyage 1 (Lilliput)
  - `the_brobdingnag_crown` — Voyage 2 (Brobdingnag)
  - `the_lagado_academy` — Voyage 3 (Laputa/Balnibarbi)
  - `the_houyhnhnm_assembly` — Voyage 4 (Houyhnhnm land)
  - `no_one` — The Open Sea / neutral hub

**Workflow:** trivial (content authoring, no TDD cycle)

## Sm Assessment

**Readiness:** GO. Dependency 157-4 (Seams 3 & 4) is `done`; all four engine seams (157-2/3/4) have landed, so the zone-eligibility filter path is live and waiting on content tags. No blocking open PRs in `content`. Merge gate clear.

**Scope (single repo — content):** This is the CONTENT-side proof of epic 157. No engine work — the engine already consumes `factions:`/`controlled_by:` tags. Dev authors faction tags in `genre_packs/wry_whimsy/worlds/gulliver` so the live engine scopes pools per voyage-region, then proves no cross-zone bleed.

**The acceptance gate that matters (do not skip):** Tagging is necessary but not sufficient — the story is named *"+ verify no bleed."* The proof is behavioral: a 4th-voyage creature (e.g. a Yahoo) must NOT be eligible on the 1st-voyage Lilliput shore after tagging. Reproduce the original leak condition (session 2026-06-20-gulliver-e721409c) or an equivalent eligibility check, and show the filter now excludes the out-of-zone content. Per project doctrine: **verify wiring, not just existence** — confirm the tags actually drive the engine's filtering end-to-end, not merely that the YAML fields are present.

**Routing notes for Dev (Naomi):**
- Read the design spec first: `docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md` (157-1, the authoritative model) and the ADR-059 amendment it references.
- Faction set is already enumerated from cartography `controlled_by` in the Story Summary above — reuse those, don't invent new faction ids.
- Reuse-first: regions already carry `controlled_by:<faction>`; the Monster Manual has `location_tags` + `culture` + `available_at_location()`. Tag against what exists.
- Trivial workflow = no RED/GREEN TDD cycle, but the verify-no-bleed check is mandatory evidence before handoff to review.

**Open question for Dev to resolve, not a blocker:** whether the no-bleed proof is best shown via an existing server-side eligibility helper/test fixture or a fresh gulliver playtest snapshot — Dev's call based on what the engine exposes. Log it under Delivery Findings if the chosen path reveals a gap in the content surface.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**

_Content (`sidequest-content`, branch `feat/157-5-tag-gulliver-faction-no-bleed`):_
- `genre_packs/wry_whimsy/worlds/gulliver/bestiary.yaml` — `factions:` on all 11 creatures (one voyage-faction each) + header note
- `genre_packs/wry_whimsy/worlds/gulliver/tropes.yaml` — `factions:` on all 9 tropes (6 voyage-scoped, 3 world-global `*` spines) + header note
- `genre_packs/wry_whimsy/worlds/gulliver/seed_tropes.yaml` — `factions:` on all 11 seeds (voyage-anchored; one spans the two scale-voyages) + header note

_Server (`sidequest-server`, branch `feat/157-5-merge-trope-factions-propagation`, base `develop`):_
- `sidequest/genre/resolve.py` — `_merge_trope` now propagates `factions` through trope inheritance (child-overrides / empty-inherits, mirroring `tags`)
- `tests/genre/test_resolve.py` — 2 regression tests (child-overrides, empty-inherits)
- `tests/genre/test_157_5_gulliver_no_bleed.py` — NEW: 12-test no-bleed proof, loads the **real** gulliver pack and drives `is_eligible`/`world_is_zoned` against the authored tags

**Tagging model (faction = region `controlled_by`):** the_lilliput_court (V1), the_brobdingnag_crown (V2), the_lagado_academy (V3), the_houyhnhnm_assembly (V4), no_one (sea/homecoming hub). World-global `*`: the_satire_turns_on_you, priced_violence_marks_the_yahoo, the_compulsion_to_reembark (the cross-voyage thematic spines). Authored cartography NPCs (`npcs.yaml`) are NOT tagged — their zone is derived (Seam 2), per spec.

**Verification (evidence):**
- No-bleed proof: `12 passed` — Yahoo (V4) NOT eligible on Lilliput shore + IS in Houyhnhnm-land; Lilliput/Brobdingnag creatures + Houyhnhnm seed don't bleed; `the_petty_holy_war` (an `extends` trope) correctly scoped `[the_lilliput_court]` after the merge fix; `*` spine eligible in every zone.
- Merge fix: `tests/genre/test_resolve.py` `30 passed` (was RED on the 2 new tests before the fix).
- Regression: full `tests/genre/` = `1081 passed, 3 failed` — the 3 failures (`test_wwn_spell_catalog_load`, `test_premise_loader` ×2) are **pre-existing** (Fate-SRD-reference / synthetic-tmp-world fixture issues), confirmed by re-running them with my `resolve.py` change stashed → still fail. Trope/seed/zone sweep `355 passed`.
- `ruff check` + `ruff format --check` + `pyright` on changed server files: clean (0 errors).
- Content validity: the proof test loads the real pack through the strict pydantic loader, so the YAML is schema-valid end-to-end.

**Tests:** 12/12 (proof) + 30/30 (resolve) passing (GREEN). No new failures introduced.

**Branches:** both pushed (see below). **DO NOT** open PRs — SM owns PR creation in finish.

**Handoff:** To review. Note for Reviewer (Avasarala): this is a **two-repo** story (content + server) — review both branches together; the server fix is what makes the content's `extends`-trope tags real.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none | N/A — all mechanical gates green; pre-existing failures verified |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (assessed by Reviewer below) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (assessed by Reviewer below) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 | confirmed 4 (non-blocking MEDIUM/LOW), dismissed 1, kept-by-rationale 1 |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 | confirmed 2 (LOW, non-blocking) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (assessed by Reviewer below) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (assessed by Reviewer below) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (assessed by Reviewer below) |
| 9 | reviewer-rule-checker | Yes | findings | 2 | dismissed 2 (rule #3 exempts private helpers; pyright clean) |

**All received:** Yes (4 enabled returned, 5 disabled pre-filled)
**Total findings:** 6 confirmed (all non-blocking), 3 dismissed (with rationale), 1 kept-with-rationale

## Reviewer Assessment

**Verdict:** APPROVED

**Data flow traced:** authored `factions:` in gulliver YAML → `load_genre_pack` → `resolve_trope_inheritance` (`_merge_trope` now propagates `factions`, child-overrides/empty-inherits) → `World.tropes`/`bestiary`/`seed_tropes` → production seam (`trope_tick._gate_activations` line 377 / `monster_manual_inject` / `seed_deck` / `seed_tick`) calls `is_eligible(content.factions, active_factions(snapshot), zoned)` → tagged-wrong-zone is the only exclusion. Safe because: untagged stays permissive (the 157-7 validator will close that hole), and every authored faction value is `"*"` or a real cartography `controlled_by` (the proof's `_assert_all_tagged` enforces referential integrity at load).

**Pattern observed:** the one production-code change (`resolve.py:157`) is a single dict entry `"factions": child.factions if child.factions else parent.factions` — byte-for-byte the sibling idiom of `tags` (line 149), `triggers`, and `escalation`. Correct, consistent, minimal. Verified independently by reviewer-rule-checker (check #13) and my own read.

**Error handling:** `_merge_trope` has no error path of its own; bad data raises loudly upstream via pydantic `model_validate` (No Silent Fallbacks honored — `sidequest/genre/resolve.py:161`).

### Observations (dispatch-tagged)

- `[VERIFIED]` **Merge fix correctness** — `resolve.py:157` mirrors the `tags` merge (line 149); a non-empty child wins, an empty child (default `[]`) inherits. Complies with the No-Silent-Fallbacks rule (raises on malformed data, no default swallow). Evidence: the 2 regression tests were RED before the line was added (`tests/genre/test_resolve.py:253,275`) and GREEN after.
- `[VERIFIED]` **No-bleed proven against REAL content** — `test_157_5_gulliver_no_bleed.py:118` drives `is_eligible(yahoo.factions, {the_lilliput_court}, zoned=True) is False` on the *real* loaded gulliver pack, reproducing session 2026-06-20-gulliver-e721409c as a falsifiable assertion. `world_is_zoned(...) is True` is separately asserted (line 58), closing the vacuous-proof short-circuit.
- `[VERIFIED]` **Referential integrity** — every faction value is `"*"` or a real `controlled_by`; the proof's `_assert_all_tagged` would fail on a typo'd slug; preflight independently confirmed `no_one` + `the_houyhnhnm_assembly` are real cartography slugs.
- `[VERIFIED]` **No regression** — full `tests/genre/` = 1081 passed; the 3 failures (`test_wwn_spell_catalog_load`, `test_premise_loader` ×2) are PRE-EXISTING (Fate-SRD-reference tmp-fixture issues), confirmed by preflight running them independent of this change. The global merge-fix does not disturb oz/wonderland (empty-inherits-empty keeps their untagged tropes permissive).
- `[TEST]` **Missing `the_yahoo_within` trope no-bleed assertion** (test-analyzer #1/#2) — MEDIUM, non-blocking. Bestiary Yahoos are probed; the trope sharing `[the_houyhnhnm_assembly, no_one]` is not. Recorded as a Delivery Finding for 157-6.
- `[TEST]` **"END-TO-END" docstring overclaims** (test-analyzer #4) — MEDIUM, non-blocking. The proof stops at the predicate; it does not drive the production seam with a resolved snapshot. MITIGATED: the seam→predicate wiring is covered by approved 157-2/3/4 tests (`tests/server/dispatch/test_zone_eligibility_seam.py`, `tests/game/test_zone_eligibility_trope_gate.py`) — I confirmed all four seams call `is_eligible`. Coverage composes; the docstring word should be softened (Delivery Finding for 157-6).
- `[TEST]` **Hardcoded counts (11/9/11)** (test-analyzer #3) — LOW, **kept with rationale (disagree with the suggestion to drop):** `_assert_all_tagged` iterates whatever loaded, so it cannot catch the loader *silently dropping* an item; the `== 11` count is the guard against silent truncation, which is exactly the kind of failure a "completeness" proof should catch. gulliver content is stable; a deliberate Swift addition *should* update the proof.
- `[TEST]` **Override-not-union + explicit `factions: []` not asserted** (test-analyzer #5/#6) — LOW, non-blocking. The override semantic is exercised by the gulliver `extends` tropes; the `factions: []`-vs-omitted ambiguity is a doc nuance (no way to clear inherited factions except `"*"`). Worth an inline note in 157-6.
- `[DOC]` **Two header comments could mislead** (comment-analyzer #1/#2) — LOW, non-blocking. `tropes.yaml` conflates the `*` set with the `extends` set; `seed_tropes.yaml` "every hook is voyage-anchored" vs the one 2-voyage seed. Recorded for 157-6 (which rewrites these headers).
- `[RULE]` **Type annotations on `_bestiary_entry`/`_trope`** (rule-checker) — **DISMISSED:** lang-review check #3 explicitly exempts "internal/private helpers"; these are underscore-prefixed test-local helpers using idiomatic pytest fixture-param style (untyped `gulliver` matches every test fn in the file), and pyright is clean (0 errors).
- `[EDGE]` / `[SILENT]` / `[TYPE]` / `[SEC]` / `[SIMPLE]` — subagents disabled via `workflow.reviewer_subagents`; I assessed each domain myself: **[EDGE]** the predicate's boundary cases (empty active, `"*"`, untagged) are unit-covered in `tests/game/test_zone_eligibility.py`; **[SILENT]** no swallowed errors — pydantic raises loudly; **[TYPE]** the field is a typed `list[str]` on a pydantic model, no stringly-typed surface added; **[SEC]** no user-input boundary (the fix operates on already-validated `TropeDefinition`; the test path derives from `__file__`, not input); **[SIMPLE]** a 1-line change is already minimal — nothing to simplify.

### Rule Compliance

- **No Silent Fallbacks** (CLAUDE.md) — COMPLIANT. `_merge_trope` adds no fallback; bad data raises via pydantic. The runtime `is_eligible` "untagged → permissive" branch is a *deliberate, documented* sequencing decision (not a silent fallback), and the 157-7 validator will make untagged-in-a-zoned-world a loud load failure.
- **No Stubbing** (CLAUDE.md) — COMPLIANT. No placeholder/skeleton code; the fix is a real, wired propagation.
- **Verify Wiring, Not Just Existence** (CLAUDE.md) — COMPLIANT. The proof drives real predicates against real loaded content (not field-presence asserts); the production seams are confirmed to call `is_eligible`. The one gap (real-pack-through-seam) is recorded, non-blocking, mitigated by existing seam tests.
- **Every Test Suite Needs a Wiring Test** (CLAUDE.md) — COMPLIANT at the system level. The seams carry wiring tests (157-2/3/4); this file adds content-correctness verification through the real loader + predicate.
- **No Source-Text Wiring Tests** (CLAUDE.md) — COMPLIANT. No `read_text()`/regex-on-source anywhere; the proof is fixture-driven behavior.
- **OTEL Observability** (CLAUDE.md) — COMPLIANT (N/A). This is a load-time data-transform fix, not a turn-decision subsystem; the decision seam (`trope_tick._gate_activations`) already emits `zone_eligibility.filtered` spans on exclusion (line 384). No new span warranted (rule-checker concurs).
- **python-review-checklist (13 checks)** — PASS. rule-checker enumerated 41 instances; 0 real violations (2 type-annotation flags fall under the private-helper exemption). ruff + ruff-format + pyright all clean.
- **Content/Design-spec fidelity** (157-1 spec) — COMPLIANT. Three pooled types tagged (bestiary/tropes/seeds); authored cartography NPCs (`npcs.yaml`) correctly NOT tagged (zone derived per Seam 2); `"*"` used only for genuine cross-voyage spines.

### Devil's Advocate

Let me try to break this. **First attack — the `no_one` multi-tag.** `the_yahoo_within` is `[the_houyhnhnm_assembly, no_one]`, and `no_one` is the `controlled_by` of BOTH `the_open_sea` AND `the_homecoming`. So this trope is eligible on the open sea — the reembark hub crossed at the end of every voyage, including voyages 1–3, *before* the traveler has ever reached Houyhnhnm-land. A pessimist says: the bleak-homecoming trope can now fire prematurely during the first sea crossing. Is that a real bleed? Verdict: it's an accepted limitation of the faction-only axis (the design explicitly defers finer within-zone placement), and the trope's own trigger/accelerator keywords gate temporal ordering inside a zone. The `no_one` tag is *necessary* — the trope's climactic 1.0 escalation IS the homecoming (`the_homecoming` = `no_one`); drop it and the trope is excluded at its own climax. So the multi-tag is correct, and the open-sea side-effect is bounded by triggers. Not a defect, but I recorded the predicate-level test gap. **Second attack — `*` on `the_satire_turns_on_you`.** World-global means it can fire in Lilliput and Laputa, where no canonical "vermin" verdict lands. A stricter author would scope it `[the_brobdingnag_crown, the_houyhnhnm_assembly]`. Verdict: defensible — the trope's own text frames it as "the central engine of the whole country... each society quietly turns the instrument round," so `*` matches authorial intent; it's a content judgment, not a correctness bug. **Third attack — the author wrote `factions: []` to opt out.** A future homebrewer might write an explicit empty list intending to clear an inherited scope, and instead silently inherit the parent's. Verdict: real ergonomic trap (test-analyzer #6), but a documentation gap, not a code bug — recorded for 157-6. **Fourth attack — a future seam refactor stops calling `is_eligible`.** This file wouldn't catch it (it tests the predicate, not the caller). Verdict: true, but the seam tests (157-2/3/4) WOULD catch it — that's their job; this file's job is content correctness. **Fifth — the counts drift and become noise.** Verdict: gulliver is a finished world; drift would be a deliberate content act that should update the proof, and the count guards silent loader truncation. None of these rises to Critical/High; all real ones are recorded as non-blocking findings.

**Handoff:** To SM (Camina Drummer) for finish-story. Two-repo merge: `sidequest-content` (`feat/157-5-tag-gulliver-faction-no-bleed`) + `sidequest-server` (`feat/157-5-merge-trope-factions-propagation`, base `develop`).

## Branch Information
**Branch Strategy:** gitflow
**Repos:** sidequest-content (`feat/157-5-tag-gulliver-faction-no-bleed`) + sidequest-server (`feat/157-5-merge-trope-factions-propagation`, base `develop`)