---
story_id: "162-10"
jira_key: ""
epic: "162"
workflow: "tdd"
---
# Story 162-10: 162-2 non-blocking follow-ups

## Story Details
- **ID:** 162-10
- **Title:** 162-2 non-blocking follow-ups: unified-resolver adoption at remaining seams (mention-path, pool-member lookup, Fate seeder, edge-publish by_name); decoy-roster hardening for canonicalization tests; participant.joined pre-rename telemetry; NpcMention rebind via dataclasses.replace; two comment corrections; diacritic-leg seat integration test
- **Points:** 2
- **Priority:** p2
- **Type:** chore
- **Repos:** server
- **Workflow:** tdd
- **Stack Parent:** none

## Branch Information
- **Branch Strategy:** gitflow (feat/162-10-unified-resolver-seams-followups)
- **Repository:** sidequest-server
- **Base:** origin/develop

## Context
- sprint/context/context-story-162-10.md
- sprint/context/context-epic-162.md

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-07-06T22:59:58Z
**Round-Trip Count:** 1

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-07-06T21:20:27+00:00 | 2026-07-06T21:23:07Z | 2m 40s |
| red | 2026-07-06T21:23:07Z | 2026-07-06T21:46:18Z | 23m 11s |
| green | 2026-07-06T21:46:18Z | 2026-07-06T22:06:38Z | 20m 20s |
| review | 2026-07-06T22:06:38Z | 2026-07-06T22:23:44Z | 17m 6s |
| red | 2026-07-06T22:23:44Z | 2026-07-06T22:34:56Z | 11m 12s |
| green | 2026-07-06T22:34:56Z | 2026-07-06T22:48:45Z | 13m 49s |
| review | 2026-07-06T22:48:45Z | 2026-07-06T22:59:58Z | 11m 13s |
| finish | 2026-07-06T22:59:58Z | - | - |

## Sm Assessment

**Setup complete — ready for RED (TEA / Amos Burton).**

162-10 is a 2-pt chore bundling six non-blocking follow-ups the Reviewer filed across story 162-2's two review rounds. Unlike a discovery story, the scope is fully pre-specified: every item has a file:line anchor in `sprint/archive/162-2-session.md` (bundle list line 97; resolver-adoption gaps lines 64 & 76; findings table lines 355–359). Nothing to discover — TEA writes the failing tests directly against those anchors.

**Six items → six ACs** (context-story-162-10.md, AC1–AC6):
1. Unified-resolver adoption at four remaining exact-match `by_name` seams (mention-path `_apply_npc_mentions`; pool-member `NpcPoolMember` leg; Fate seeder `_seed_fate_opponents` ~L595; edge-publish `_publish_combat_edge_to_npcs` ~L808) → real seam + span wiring tests.
2. Decoy-roster hardening for the three canonicalization tests (mutation-confirmed single-entry blindspot) → assert by `creature_id`, not roster cardinality.
3. `participant.joined` / init-span pre-rename telemetry on the npcs_present path → behavioral test on canonical name emission.
4. NpcMention rebind via `dataclasses.replace` (flags currently dropped; inert today, latent trap) → behavioral test preserving is_new/is_creature/disengaged/is_place.
5. Two comment corrections at encounter_lifecycle.py:1791-1793 → verified by inspection.
6. Diacritic-leg seat **integration** test (162-2 landed the origin-model unit test; this exercises the seat seam) → RED against ASCII-query vs diacritic-roster resolution.

**Notes for TEA:** The `ruff format` one-file item from 162-2 (finding line 358) was already swept at 162-9 — confirm clean and drop if so; don't re-file. Items 1–4 and 6 are genuinely test-first; item 5 is inspection-only (no test). Server repo only. No blocking deps.

**Doctrine watch:** Item 1 is pure seam cutover to the *existing* shared resolver (`resolve_roster_npc`) — this is "Don't Reinvent — Wire Up What Exists," not new mechanics. Do not author a parallel resolver.

**Checklist:** session ✓ · fields ✓ · context+ACs ✓ · branch `feat/162-10-unified-resolver-seams-followups` ✓ · Jira skipped (not configured for this project).

## TEA Assessment

### Red Phase (test writing)

**Tests Required:** Yes
**Status:** RED (7 failing, ready for Dev) — full suite **14,658 passed / 7 (intended) failed / 341 skipped**, no regressions.

**Test Files:**
- `tests/server/test_162_10_resolver_seam_adoption.py` (NEW) — 9 tests: 7 RED + 2 green guards.
- `tests/server/test_162_2_identity_fork_seating.py` (EDITED) — hardened the 3 `TestSeatNameCanonicalization` tests with decoy rosters + specific-creature identity assertions (item 2). All 12 stay green.

**Commit:** `d1d047b1 test: add failing tests for 162-10 unified-resolver seam adoption`

**RED-vs-hardening split (the honest picture — this bundle is legitimately mixed):**

| # | Item | Test | Kind | Drives (real seam) |
|---|------|------|------|--------------------|
| 1a | mention-path alias leg | `test_mention_by_recorded_alias_hits_roster_not_phantom_mint` | RED | `narration_apply._apply_npc_mentions` |
| 1a | mention-path diacritic | `test_mention_by_diacritic_variant_hits_roster_not_phantom_mint` | RED | `narration_apply._apply_npc_mentions` |
| 1b | seeder pool-member lookup | `test_variant_named_pool_antagonist_is_promoted_not_fabricated` | RED | `_seed_fate_opponents` pool leg (`m.name == actor.name`) |
| 1c | Fate opponent seeder | `test_alias_named_fate_opponent_seats_canonical_no_twin` | RED | `_seed_fate_opponents` `by_name` dict |
| 1d | dial edge-publish | `test_alias_named_opponent_receives_published_edge` | RED | `_publish_combat_edge_to_npcs` `by_name` dict |
| 3 | participant.joined pre-rename | `test_participant_joined_span_carries_canonical_name` | RED | `instantiate_encounter_from_trigger` (explicit npcs_present path) |
| 3 | init-span combatant_names | `test_init_span_combatant_names_are_canonical` | RED | same |
| 6 | diacritic seat integration | `test_diacritic_roster_creature_seats_via_ascii_prose_no_stub` | GREEN guard | `_seed_combat_hp_depletion_to_npcs` (already correct — hardening) |
| 5 | comment-fix behavioral pin | `test_case_variant_head_check_rebind_is_span_silent` | GREEN guard | head-check rebind (already correct — pins the corrected comment) |
| 2 | decoy-roster hardening | 3 hardened tests in `test_162_2_identity_fork_seating.py` | GREEN | `_seed_combat_hp_depletion_to_npcs` canonicalization + head-check |

**Two items have NO behavioral test — by design, not omission (see Deviations):**
- **Item 4 (NpcMention rebind → `dataclasses.replace`)** — the dropped flags (`is_new/is_creature/disengaged/is_place`) are provably INERT: `disengaged` has zero consumers repo-wide; `is_creature` on `npcs_present` is read only by the ship-scale firewall (encounter_lifecycle.py ~1898) which runs BEFORE the head-check rebind (~1936); the rebind fires only on a roster HIT so nothing downstream mints from the mention. A behavioral test would be vacuous/contrived — banned by test-quality rules. **Inspection-only:** Dev applies `dataclasses.replace(materialized_threat, name=known.core.name)` at the head-check rebind; Reviewer verifies.
- **Item 5 (two comment corrections)** — one of the two IS behaviorally pinned (the case-variant-rebind span-silence guard above); the "edge publish uses find_creature_core" claim is a doc-only statement about a different function and can't be pinned without a source-shape test. Inspection.

### Rule Coverage

Applicable checks for a **test-writing** phase (server repo → `.pennyfarthing/gates/lang-review/python.md` + server `CLAUDE.md`):

| Rule | Coverage | Status |
|------|----------|--------|
| python #6 — test quality (no vacuous asserts, meaningful values) | every test asserts a concrete value/identity; Phase-C self-check ran (below) | pass |
| CLAUDE.md — **No Source-Text Wiring Tests** | zero `read_text()`/source-grep asserts; every test drives the real seam + asserts behavior or OTEL span | pass |
| CLAUDE.md — Every Test Suite Needs a Wiring/Integration Test | items 3 & 6 drive the full `instantiate_encounter_from_trigger` / seeder path end-to-end (not isolated units) | pass |
| CLAUDE.md — OTEL Observability Principle | participant.joined + combatant_names + identity.resolved + npc.edge_published are asserted via spans, not prose | pass |
| CLAUDE.md — Don't Reinvent (doctrine watch from SM) | tests pin the CONTRACT (canonical resolution), not a new resolver — Dev wires the existing `resolve_roster_npc`/`normalize_name` | pass |

**Self-check (Phase C):** 0 vacuous assertions. No `assert True`, no `let _ =`, no truthy-on-always-None. Identity assertions use `is` against the specific object; empty-pool checks use `== []`; span checks filter by name + assert exact attribute values. Removed 2 unused module symbols (`_seed_hp`, `_REFERENCED_SPAN`) before commit (No Stubbing).

**Handoff:** To Dev (Naomi Nagata) for GREEN.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 21/21 target passing (GREEN) — full suite **14,665 passed / 0 failed / 341 skipped**. pyright neutral (51 errors with AND without my changes — pre-existing debt, byte-identical). ruff clean + formatted.
**Branch:** `feat/162-10-unified-resolver-seams-followups` (pushed)
**Commit:** `feat(162-10): adopt unified resolver at the last four identity seams`

**Files Changed:**
- `sidequest/server/narration_apply.py` — (1a) `_npc_name_match_keys` now folds diacritics via the resolver's own `normalize_name` primitive (identical for ASCII single-space names, so article/comma tests unaffected); added a recorded-alias leg to `_apply_npc_mentions` Step 1 (the seam never checked `npc.aliases`); added a `diacritic_normalized` branch to `_reconciliation_form` for honest `match_form` telemetry.
- `sidequest/server/dispatch/encounter_lifecycle.py` — (1c) `_seed_fate_opponents` swaps the exact `by_name` dict for `resolve_roster_npc` + seat-name canonicalization (Amos's reachability finding); (1d) `_publish_combat_edge_to_npcs` same swap + canonicalization; (1b) both seeder pool-member legs (Fate + hp_depletion) use `normalize_name(m.name) == normalize_name(actor.name)`; (3) opponent seat names canonicalized at actor-BUILD time so `participant.joined` + init `combatant_names` + the exact-match presence-stamp lookup all read canonical; (4) head-check rebind uses `dataclasses.replace` (preserves the four flags); (5) corrected the two overclaiming comments, reconciled to the post-1d state.

**AC coverage:**
- AC1 (resolver adoption at 4 seams) — ✅ mention-path, pool-member (both legs), Fate seeder, edge-publish. All green.
- AC2 (decoy-roster hardening) — ✅ TEA's 3 hardened tests stay green.
- AC3 (participant.joined pre-rename) — ✅ span + combatant_names carry canonical names.
- AC4 (NpcMention `dataclasses.replace`) — ✅ implemented; inert-but-correct (inspection, per TEA deviation).
- AC5 (two comment corrections) — ✅ both corrected; comment #1 behaviorally pinned by the span-silence guard, #2 reconciled to post-1d.
- AC6 (diacritic seat integration) — ✅ green guard passes (with TEA's Conflict finding: the "identity.resolved fires" wording in AC6 is wrong — canonical-leg matches are span-silent; the test asserts the correct no-span behavior).

**Self-review (judgment checks):** wired to real production seams (all 4 have non-test callers) ✅ · follows project patterns (reuses `normalize_name`/`resolve_roster_npc`, no parallel resolver — SM's doctrine watch honored) ✅ · all ACs met ✅ · no new error handling needed (pure identity-resolution cutover) ✅.

**Handoff:** To next phase (verify/review).

## Subagent Results — Round 1 (REJECTED, archived)

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (21/21 pass · ruff+format clean · pyright 51 baseline unchanged · no smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled via settings; edge/boundary paths self-assessed (see Observations + Devil's Advocate) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled via settings; No-Silent-Fallbacks covered by rule-checker #14 (0 violations) + self-review |
| 4 | reviewer-test-analyzer | Yes | findings | 4 | confirmed 3 (1 corroborates my [HIGH]), downgraded 1 to LOW |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (LOW) | confirmed 2 (both precision nits, non-blocking) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled via settings; type/annotation covered by rule-checker #3 (0 violations) |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled via settings; no security surface — pure in-memory identity resolution, no I/O/auth/user-input |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled via settings; simplicity self-assessed — reuses existing primitives, no new abstraction |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 19 rules (13 lang-review + 6 project) | N/A |

**All received:** Yes (4 enabled returned; 5 disabled via workflow.reviewer_subagents, self-assessed)
**Total findings:** 6 confirmed (1 reviewer-found [HIGH] + 3 [TEST] + 2 [DOC] LOW), 0 dismissed, 1 deferred ([LOW] sealed-letter scope)

## Rule Compliance — Round 1 (archived)

Rubric = `.pennyfarthing/gates/lang-review/python.md` (#1–#13) + server CLAUDE.md principles. rule-checker enumerated 58 instances across 19 rules, 0 violations. My independent spot-checks:

- **No Silent Fallbacks** — enumerated every resolver-swap None path: `_publish_combat_edge_to_npcs` keeps `if npc is None: continue` byte-for-byte (encounter_lifecycle.py:979); both seeders keep the `if npc is None:` ladder; the build-time canonicalization and head-check rebind both no-op on `None`. No new swallow. ✅ (matches rule-checker #14)
- **Don't Reinvent** — all 5 roster seams call `resolve_roster_npc`; both pool legs use `normalize_name` (correct — pool members aren't `Npc`); the mention alias leg reuses `_npc_name_match_keys`→`normalize_name`. No parallel resolver. ✅ (SM doctrine watch satisfied)
- **Import hygiene** — 3 new imports (`replace`, `normalize_name`, `fold_to_ascii`); no cycle (origin.py/slug_fold.py have no path back to server.*); verified by the green suite. ✅
- **Type annotations at boundaries** — only public function touched is `instantiate_encounter_from_trigger` (signature unchanged, fully annotated). ✅
- **OTEL Observability** — spans preserved; `diacritic_normalized`/`alias` match_form flow into the existing `npc_referenced_span`; participant.joined/combatant_names now canonical. Wired, BUT the new labels are **unasserted by any test** (see [TEST] finding — observability half unverified).
- **Test quality** — decoy hardening in the 162-2 file is genuine; BUT the 9 new tests use size-1 rosters (mutation-blind — see [TEST]).

## Reviewer Assessment — Round 1 (REJECTED, archived)

**Verdict:** REJECTED

I found a correctness regression the green suite hides. Adversarial reproduction, not inference.

**[HIGH] [correctness] Pool-promotion reachability brick — the story's own reachability fix misses the pool-promotion path.**
The 162-10 pool-leg change (`m.name == actor.name` → `normalize_name(m.name) == normalize_name(actor.name)`) lets a case/diacritic-variant `actor.name` ("Dona Espina", or the far more common case-variant "the butcher") match a pool member stored canonically ("Doña Espina" / "The Butcher"). That member is then promoted to an `Npc` whose `core.name` is the **canonical** name — but `actor.name` is left as the **variant**. Neither seeder rewrites it (the `actor.name = npc.core.name` canonicalization at encounter_lifecycle.py:751 fires only on the `npc is not None` roster path, NOT the `npc is None` pool-promotion branch). `find_creature_core` is **exact-match** (session.py:1882-1888), so `find_creature_core(actor.name)` MISSES the promoted opponent → the Fate resolver reads `None` for the Other's sheet → the impossible-state brick (`decide_opponent_action`/`_resolve_attack`, the 150-2 re-brick class); the WN HP-bar filter drops it. **Empirically reproduced** (Fate path): `actor.name='Dona Espina'`, promoted `core.name='Doña Espina'`, `find_creature_core('Dona Espina') → None`. `_seed_combat_hp_depletion_to_npcs` (encounter_lifecycle.py:459-465) has the identical pattern. This REGRESSES the input: pre-162-10 the variant name didn't match the pool (exact) and fabricated a *reachable* opponent; post-162-10 it promotes the right identity but *unreachable* — the exact [HIGH] class the epic rejected 162-2 round 1 over ("before, at least a hollow stub fought back"). The RED test asserts promotion/no-stub but NOT reachability, so it passed green over a brick. tag: reviewer-found (corroborated by [TEST] #1).

| Severity | Issue | Location | Fix Required |
|----------|-------|----------|--------------|
| [HIGH] | Pool-promotion reachability brick: variant `actor.name` promotes a canonical-named Npc but stays the variant → `find_creature_core(actor.name)` misses → resolver brick. Reproduced (Fate); identical in hp_depletion. | `encounter_lifecycle.py:_seed_fate_opponents` ~782-788 + `_seed_combat_hp_depletion_to_npcs` ~459-465 | After `snapshot.npcs.append(npc)` in BOTH pool-promotion branches, set `actor.name = npc.core.name` (mirror L751). Add a reachability assertion (`snap.find_creature_core(actor.name) is not None`) to the pool-promotion test(s). |
| [MEDIUM] [TEST] | hp_depletion pool-leg `normalize_name` fix is UNTESTED — reverting it to exact leaves the full suite green (mutation-verified). | `tests/server/test_162_10_resolver_seam_adoption.py` | Add a hp_depletion variant-pool-promotion test (twin of the Fate one), asserting promotion + reachability. |
| [MEDIUM] [TEST] | All 9 new tests seat size-1 rosters/pools → "resolve the specific entity" is indistinguishable from "grab position 0". Mutation-verified: patching `resolve_roster_npc`→`npcs[0]` leaves all 9 green; the SAME decoy technique this diff added to the 162-2 file was not carried into the new file. | `tests/server/test_162_10_resolver_seam_adoption.py` | Add a co-located decoy (distinct id/name, seated FIRST) + `is`-identity assertion to each seam test, per the 162-2 hardening. |
| [MEDIUM] [TEST] | New telemetry labels `diacritic_normalized` + `alias` are unasserted — deleting the branch leaves all 21 green. OTEL half of the fix unverified (CLAUDE.md treats it as mandatory). | `tests/server/test_162_10_resolver_seam_adoption.py` | Capture `npc.referenced` span; assert `match_form == "diacritic_normalized"` / `"alias"` on the two mention tests. |
| [LOW] [self] | Sealed-letter build path (encounter_lifecycle.py:2171-2182) builds its opponent from `npcs_present[0]` WITHOUT the build-time canonicalization the generic path got → participant.joined pre-rename persists there. | `encounter_lifecycle.py:2171-2182` | Deferred — out of the filed finding's scope (ship-scale role-tagged mode; roster-alias sealed-letter opponents unobserved). Canonicalize if that ever occurs. |
| [LOW] [DOC] | (a) `_reconciliation_form` combined article+diacritic difference still labels `comma_normalized`; (b) `_publish_combat_edge_to_npcs` docstring "whose name matches an Npc" is now a looser relation post-resolver. | narration_apply.py:2125; encounter_lifecycle.py:920 | Optional precision polish. |

**Data flow traced:** narrator/router prose name → `_seed_fate_opponents`/`_seed_combat_hp_depletion_to_npcs` pool leg → `normalize_name` match → promote → **actor.name NOT canonicalized** → `find_creature_core(actor.name)` (exact) → `None` → resolver brick. This is the break.
**Pattern observed:** correct seat-canonicalization exists at encounter_lifecycle.py:751 (roster path) and 2228-2231 (build path) — the pool-promotion branch is the one place the pattern was NOT applied. Consistency gap, not a novel bug.
**Dispatch tags:** [RULE] rule-checker clean (0/19). [TEST] 3 confirmed (reachability-untested, decoy-missing, telemetry-unasserted). [DOC] 2 LOW (comment precision). [EDGE] self-assessed — the pool-promotion variant-name boundary IS the [HIGH]. [SILENT] no swallowed errors (rule-checker #14 + self). [TYPE] annotations clean (rule-checker #3). [SEC] no surface. [SIMPLE] reuses primitives, no over-engineering.

### Devil's Advocate

Argue the code is broken. The strongest case is the one I proved: the story's headline is "one identity, reachable everywhere," and its own seeder comments promise `find_creature_core(actor.name)` reachability — yet the pool-promotion branch ships an opponent the engine cannot find by its seat name. A confused-but-realistic table trips it trivially: the narrator establishes "The Butcher" on turn 3 (lands in `npc_pool`); on turn 5 the router seats "the butcher"; `normalize_name` now matches (didn't before), the cast member is promoted (good!), and then the confrontation bricks because the seat is addressed as "the butcher" while the entity is "The Butcher" — a lowercase letter turns a working promotion into a dead encounter. Worse than the bug it replaced: pre-162-10 that input fabricated a *reachable* (if duplicate) opponent, so the story converts a cosmetic twin into a hard brick — a net regression on a plausible path, and the GM panel's `identity.resolved`/`edge_published` spans won't even fire to explain the silence. Second angle — the test suite actively camouflages this: every new test uses a one-entry roster, so `resolve_roster_npc` could be replaced by `return npcs[0]` and 9/9 still pass (mutation-proven); the reachability the seeder comment brags about is asserted nowhere. Third angle — the observability the project calls mandatory is half-built: the new `diacritic_normalized`/`alias` labels exist but no test proves they emit, so a future refactor silently reverts them to `comma_normalized` and the lie-detector starts lying with no failing test. What a stressed system does: a diacritic-heavy world (Jade's perseus) hits the brick constantly; a case-sloppy narrator hits it intermittently — the worst kind, a flaky brick. None of this is style: it is a reproduced functional regression plus a test net with a hole shaped exactly like it. That is a REJECT.

**Handoff:** Back to TEA (red) — reachability is a logic bug needing a failing test first, then Dev canonicalizes both pool-promotion branches.

## TEA Assessment (rework R1)

**Tests Required:** Yes — pinned the reviewer's [HIGH] with a failing test, closed the [MEDIUM][TEST] gaps.
**Status:** RED (2 failing, ready for Dev) — full suite **2 failed / 14,664 passed / 341 skipped**, no regressions. Test file only; no production change this round.
**Commit:** `6cd13abc test(162-10): pin the pool-promotion reachability brick (review rework R1)`

**What I added (`tests/server/test_162_10_resolver_seam_adoption.py`):**
- **[HIGH] reachability — 2 RED tests** (the blocker Chrisjen reproduced):
  - `TestFateSeederResolverAdoption::test_variant_named_pool_antagonist_is_promoted_not_fabricated` — added `assert opp.name == "Doña Espina"` + `find_creature_core(opp.name) is not None` (+ a decoy pool member). RED: production leaves `actor.name` the variant on the pool-promotion path.
  - `TestHpDepletionPoolPromotionReachable::test_variant_pool_antagonist_promotes_and_stays_reachable` — NEW; drives `_seed_combat_hp_depletion_to_npcs` with a variant pool member. RED on the same reachability + closes the [MEDIUM][TEST] "hp_depletion pool leg untested" gap in one test.
  - Both fail on `pool-promotion left the seat un-canonicalized: actor.name='Dona Espina'` — the fork IS killed (right member promoted) but the seat is unreachable. **Dev fix: `actor.name = npc.core.name` after `snapshot.npcs.append(npc)` in BOTH seeder pool-promotion branches** (encounter_lifecycle.py ~_seed_fate_opponents:782-788 and ~_seed_combat_hp_depletion_to_npcs:459-465).
- **[MEDIUM][TEST] decoy hardening** (green): added a co-located decoy (distinct id, seated FIRST) + specific-entity assertions to the mention-alias, mention-diacritic, Fate-alias, Fate-pool, hp_depletion-pool, and edge-publish tests. Mutation-proofs "resolve the specific entity" vs "grab position 0."
- **[MEDIUM][TEST] telemetry** (green): the two mention tests now capture `npc.referenced` and assert `match_form == "alias"` / `"diacritic_normalized"` — production emits both correctly, so the OTEL half of the fix is now verified (was invisible).

**Deviations:** No deviations from spec — this rework is purely responsive to the reviewer's confirmed findings.

**Not addressed (deferred, per reviewer):** the [LOW] sealed-letter participant.joined pre-rename (out of scope) and the two [LOW][DOC] comment nits (Dev may fold the docstring/label-precision nits into the green fix at its discretion).

**Handoff:** To Dev (Naomi Nagata) for GREEN — canonicalize `actor.name` in both pool-promotion branches; the 2 RED tests + 8 green guards + the existing 12 in test_162_2 are the gate.

## Dev Assessment (rework R1)

**Implementation Complete:** Yes
**Tests:** 22/22 (GREEN) — full suite **14,665 passed / 0 failed / 341 skipped**. pyright neutral (14/14 on the changed file). ruff clean + formatted.
**Branch:** `feat/162-10-unified-resolver-seams-followups` (pushed)
**Commit:** `75acd68f fix(162-10): canonicalize the seat on pool-promotion (review rework R1)`

**Fix ([HIGH] reachability brick):** in BOTH seeder pool-promotion branches — `_seed_fate_opponents` (~encounter_lifecycle.py:797) and `_seed_combat_hp_depletion_to_npcs` (~465) — after `snapshot.npcs.append(npc)`, added:
```python
if npc.core.name != actor.name:
    actor.name = npc.core.name
```
This mirrors the roster-hit canonicalization at L425/L751 that the roster path already had — the pool-promotion path was the one branch that resolved-then-seated without rewriting the seat, so a `normalize_name` pool match against a variant `actor.name` promoted the canonical member but left the seat unreachable by `find_creature_core` (exact-match). Both TEA reachability tests now pass; no other test moved.

**Also (reviewer [LOW][DOC]):** tightened the `_publish_combat_edge_to_npcs` docstring — "whose `name` matches an `Npc`" → "whose `name` RESOLVES (via `resolve_roster_npc`: canonical / alias / invented_from) to an `Npc`".

**Deferred (reviewer [LOW], explicitly optional):** the `_reconciliation_form` combined article+diacritic case (a "The Doña X" vs "dona x" double-variant would still label `comma_normalized`). No test requires it; folding a diacritic check into the article branch risks the article_fold suite for a rare telemetry corner. Left as-is; captured as a Delivery Finding.

**Deviations:** No new spec deviations this round — the fix is exactly the canonicalization TEA's tests pin, in the two branches the Reviewer identified.

**Self-review:** wired (both seeders have live dispatch callers) ✅ · mirrors the existing roster-path pattern ✅ · reachability restored + reproduced-green ✅ · no new error handling needed (pure seat rewrite) ✅.

**Handoff:** Back to Reviewer (Chrisjen Avasarala) — the [HIGH] is closed and reproduced-green; the [MEDIUM][TEST] gaps (hp_depletion coverage, decoys, telemetry assertions) are landed by TEA's rework tests.

## Subagent Results

*(Round 2 — re-review after the rework fix. Round-1 table archived above.)*

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (22/22 pass · ruff+format clean · pyright 51 baseline unchanged · no smells) | N/A |
| 2 | reviewer-edge-hunter | Skipped | disabled | N/A | Disabled; delta is a 2-line conditional — boundary self-assessed (the variant-name pool case IS the fixed edge) |
| 3 | reviewer-silent-failure-hunter | Skipped | disabled | N/A | Disabled; covered by rule-checker #14 (0 violations — the seat correction is telemetry-visible, not a swallow) |
| 4 | reviewer-test-analyzer | Yes | clean | 0 | **Mutation-verified all 3 round-1 gaps CLOSED**: revert the fix → both reachability tests fail; grab-position-0 → decoy tests fail; delete the diacritic branch → telemetry test fails. No new test issues. |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 (LOW/MED, doc-only) | confirmed 2 non-blocking (docstring enumeration + off-by-one line refs) |
| 6 | reviewer-type-design | Skipped | disabled | N/A | Disabled; rule-checker #3 confirmed the one new annotation (`_seed → EncounterActor`) correct |
| 7 | reviewer-security | Skipped | disabled | N/A | Disabled; no surface — internal seeder mutation, no I/O/auth/input boundary |
| 8 | reviewer-simplifier | Skipped | disabled | N/A | Disabled; the fix reuses the existing roster-hit idiom — no new abstraction |
| 9 | reviewer-rule-checker | Yes | clean | 0 violations / 19 rules | N/A — independently confirmed No-Silent-Fallbacks + Don't-Reinvent on the delta |

**All received:** Yes (4 enabled returned; 5 disabled via workflow.reviewer_subagents, self-assessed)
**Total findings:** 2 confirmed (both [LOW]/[MED] doc-only, non-blocking), 0 dismissed, 0 blocking

## Reviewer Assessment

**Verdict:** APPROVED

Round 2 re-review after the rework. My round-1 [HIGH] and the [MEDIUM] test gaps are all resolved — verified two independent ways, not by trusting the green suite.

**[HIGH] pool-promotion reachability brick — CLOSED.** The fix adds `if npc.core.name != actor.name: actor.name = npc.core.name` after `snapshot.npcs.append(npc)` in BOTH pool-promotion branches (encounter_lifecycle.py:474-475 hp_depletion, :804-805 Fate) — mirroring the roster-hit canonicalization at L426/L758. I re-ran my original bricking repro: `actor.name='Doña Espina'`, `find_creature_core(actor.name)=REACHABLE`, sheet present. test-analyzer mutation-verified it independently: reverting the two blocks makes both reachability tests fail on the seat assertion; restoring makes them pass. Genuinely guarded.

**[MEDIUM][TEST] gaps — CLOSED (mutation-verified):** the hp_depletion pool leg now has its own reachability test; decoys were added to all six seam tests and grab-position-0 mutations make them fail; `match_form == "alias"`/`"diacritic_normalized"` are asserted and deleting the production branch makes the telemetry test fail. The round-1 "size-1 roster can't tell resolve-specific from grab-[0]" hole is closed.

**Remaining findings (non-blocking, [LOW]/[MED] doc-only — captured as Delivery Findings):**
- [MED][DOC] `_reconciliation_form` docstring (narration_apply.py:2127) still enumerates "either article OR comma" — the rework added a third `diacritic_normalized` branch, so the doc undercounts return values by one. Doc-only; behavior is correct and tested.
- [LOW][DOC] the two new comments' cross-references ("Mirror the roster-hit canonicalization at L425" / "L751") are off-by-one / point into their own comment block. Cosmetic.

These do not block (severity table: Medium/Low never block). A 3rd round-trip on a follow-up chore for a docstring enumeration + comment line-refs is disproportionate; the next touch of `_reconciliation_form` fixes them.

**Data flow re-traced:** prose/variant name → seeder pool leg (`normalize_name` match) → promote canonical Npc → **`actor.name = npc.core.name`** (the fix) → `find_creature_core(actor.name)` (exact) now HITS → resolver reads the sheet. The break is sealed.
**Pattern observed:** the fix reuses the established roster-hit canonicalization idiom (L426/L758) verbatim — the correct "don't reinvent" resolution, applied to the branch round 1 flagged.
**Dispatch tags:** [RULE] clean (0/19). [TEST] clean (all 3 round-1 gaps mutation-verified closed). [DOC] 2 non-blocking nits. [EDGE] the fixed variant-name pool case self-assessed. [SILENT] rule-checker #14 clean (telemetry-visible). [TYPE] the one new annotation correct. [SEC] no surface. [SIMPLE] no new abstraction.

### Devil's Advocate

Try to break the fix. The seat is now canonicalized on the pool-promotion path — is there a case it still misses? A pool member whose post-promotion `core.name` differs from `pool_member.name`? No — `_promote_pool_member_to_npc` carries the member's name verbatim, and rule-checker verified the comparison is against the true canonical name, not a guess. Does canonicalizing `actor.name` mid-loop corrupt a later consumer expecting the variant? No — the only downstream reads (`pool_origin = pool_member.name`, the edge/seeded spans) either use the member name directly or fire AFTER the mutation with the corrected name (rule-checker traced both). Could the fix double-fire on a re-seed? On a second pass the promoted Npc is now in `snapshot.npcs`, so `resolve_roster_npc` hits the roster leg and canonicalization is a no-op — idempotent. The one honest residue is telemetry-adjacent and pre-existing, not introduced here: an instantiate-driven combat that pool-promotes emits `participant.joined` with the variant at build time (the pool member isn't in `snapshot.npcs` yet, so the build-time canonicalization can't reach it) — but that path predates 162-10, isn't in the filed scope, and the entity is reachable regardless. Nothing I can construct turns the current diff into a brick or a wrong-target. The blocking defect is demonstrably closed and the residue is documentation. APPROVE.

**Handoff:** To SM (Camina Drummer) for finish-story.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)

- **Conflict** (non-blocking): AC6's expectation "identity.resolved span fires with the correct creature_id" is WRONG for a pure diacritic-vs-canonical match. `resolve_roster_npc` folds diacritics in its **canonical** leg (`normalize_name` = fold_to_ascii + casefold), so "Veyra Solne" ⇄ roster "Veyra Solnë" resolves on leg 1 and derives NOTHING — the span only fires on the alias / invented_from legs (origin.py:184-195). The green-guard test `test_diacritic_roster_creature_seats_via_ascii_prose_no_stub` asserts the CORRECT behavior (no-stub + reachable + **no** identity.resolved span). Affects `sprint/context/context-story-162-10.md` (AC6 wording). *Found by TEA during test design.*
- **Gap** (non-blocking): the pool-member seams (`_seed_combat_hp_depletion_to_npcs` ~L442, `_seed_fate_opponents` ~L748) match `m.name == actor.name` against `snapshot.npc_pool` — but `resolve_roster_npc` takes `Sequence[Npc]`, and pool members are `NpcPoolMember`, not `Npc`. Item 1b cannot literally call `resolve_roster_npc` on the pool; the honest cutover is `normalize_name(m.name) == normalize_name(actor.name)` (the shared primitive), OR a pool-aware sibling. The RED test pins the BEHAVIOR (variant-named pool antagonist promotes, not fabricates); Dev owns whether that's a normalize_name comparison or a new pool resolver. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Question** (non-blocking): item 5's comment #2 correction interacts with item 1d. Today the head-check comment (encounter_lifecycle.py ~L1930) lists "edge publish" as a `find_creature_core` consumer (false — edge-publish uses its own `by_name` dict). After 1d cuts edge-publish over to `resolve_roster_npc`, the corrected comment should say edge-publish resolves via the **unified resolver**, not "its own by_name dict" either. Dev should reconcile the comment to the POST-1d state, not the pre-162-10 state. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Improvement** (non-blocking): the Fate seeder (`_seed_fate_opponents`) does NOT canonicalize `actor.name` after a resolver hit the way the hp_depletion seeder does (encounter_lifecycle.py:425-426). For the same [HIGH] reachability reason (find_creature_core is exact-match on `actor.name`), an alias-resolved Fate seat should rewrite `actor.name` to canonical. The RED test only pins the fork-kill (no twin); Dev should add the canonicalization for reachability parity. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during test design.*
- **Gap** (rework R1, resolved-by-pinning): the reachability-parity improvement I flagged above (R1) covered the ROSTER-hit path (which Dev fixed at L751); the Reviewer found the POOL-promotion path shares the same gap and is a live brick. Now pinned by two RED reachability tests. Dev must canonicalize `actor.name` in both pool-promotion branches. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by TEA during rework test design.*

### Dev (implementation)

- **Improvement** (non-blocking): resolved TEA's four findings inline — (a) AC6 Conflict: kept the test asserting no-span (canonical-leg silent) and noted the AC wording is wrong; (b) pool-member Gap: used `normalize_name` comparison on BOTH legs (Fate + hp_depletion), not just the tested one; (c) comment #2 Question: reconciled the head-check comment to the post-1d state (edge-publish now resolves via `resolve_roster_npc`, removed from the `find_creature_core` exact-match list); (d) Fate reachability Improvement: added seat-name canonicalization to both `_seed_fate_opponents` and `_publish_combat_edge_to_npcs`. No new findings. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Dev during implementation.*
- **Improvement** (non-blocking): `_npc_name_match_keys` is shared by the mention Step-1 roster leg, the Step-2 pool leg, AND a seated-actor reconciliation — so folding diacritics there improves identity matching at all three consumers uniformly (the correct "one normalization" locus), not only the tested mention path. A follow-up could audit whether the seated-actor reconcile (narration_apply.py ~L2463) now wants an explicit alias leg too (out of 162-10 scope; no observed bug). Affects `sidequest/server/narration_apply.py`. *Found by Dev during implementation.*
- **Improvement** (rework R1, non-blocking, deferred): `_reconciliation_form` labels a COMBINED article+diacritic reconciliation ("The Doña X" ⇄ "dona x") as `comma_normalized` rather than a truer label — the diacritic branch only fires when diacritics are the *sole* difference. Rare telemetry corner; no test requires it, and touching the article branch risks the article_fold suite. Affects `sidequest/server/narration_apply.py` (`_reconciliation_form`). *Found by Dev during rework implementation.*

### Reviewer (code review)

- **Gap** (blocking): the pool-promotion branches of both seeders do not canonicalize `actor.name` to the promoted `npc.core.name`, so a variant-named pool antagonist is promoted-but-unreachable (`find_creature_core(actor.name)` exact-match misses it → resolver brick). The `normalize_name` pool-leg change enabled the variant match without the matching seat rewrite. Affects `sidequest/server/dispatch/encounter_lifecycle.py` (`_seed_fate_opponents` ~782-788, `_seed_combat_hp_depletion_to_npcs` ~459-465 — add `actor.name = npc.core.name` after `snapshot.npcs.append(npc)`). *Found by Reviewer during code review.*
- **Gap** (non-blocking): the new-file test suite uses size-1 rosters/pools throughout, so it cannot distinguish "resolve the matched entity" from "grab position 0" (mutation-verified). The decoy-hardening technique this same diff added to the 162-2 file must be carried into `tests/server/test_162_10_resolver_seam_adoption.py`. *Found by Reviewer during code review.*
- **Gap** (non-blocking): the `diacritic_normalized` + `alias` match_form telemetry labels are emitted but asserted by no test; the hp_depletion pool-leg fix is likewise untested (both mutation-verified invisible). Affects `tests/server/test_162_10_resolver_seam_adoption.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking, deferred): the sealed-letter build path (encounter_lifecycle.py:2171-2182) does not apply the participant.joined build-time canonicalization the generic path received — a roster-alias sealed-letter opponent would still emit a pre-rename span. Out of the filed finding's scope; deferred. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review.*
- **Improvement** (round 2, non-blocking): `_reconciliation_form`'s docstring (narration_apply.py:2127) enumerates "either leading-definite-article folding OR comma-register inversion" as exhaustive, but the 162-10 rework added a third `diacritic_normalized` branch — the doc now undercounts its own return values by one. Doc-only; behavior is correct and tested. Affects `sidequest/server/narration_apply.py`. *Found by Reviewer during code review (round 2).*
- **Improvement** (round 2, non-blocking): the two new seat-canonicalization comments' cross-references ("Mirror the roster-hit canonicalization at L425" / "Mirrors the roster-hit path (L751)") are off-by-one / point into their own comment block (actual canonicalization at L426-427 / L758-759). Cosmetic; prefer a symbolic anchor over line numbers. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review (round 2).*
- **Question** (round 2, non-blocking, pre-existing): an instantiate-driven combat that POOL-PROMOTES an opponent still emits `participant.joined` with the pre-promotion (variant) name — the pool member isn't in `snapshot.npcs` at build time, so item 3's build-time canonicalization can't reach it. Predates 162-10 and is out of scope (the entity is reachable post-fix); flagged for a future telemetry-completeness pass. Affects `sidequest/server/dispatch/encounter_lifecycle.py`. *Found by Reviewer during code review (round 2).*

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Item 4 (NpcMention rebind) ships with NO behavioral test**
  - Spec source: context-story-162-10.md, AC4 ("Behavioral test: a rebound mention with flags preserves the flags after rebind")
  - Spec text: AC4 asks for a behavioral test that a rebound mention preserves `is_new/is_creature/disengaged/is_place`
  - Implementation: no behavioral test written; item verified by inspection + the one-line `dataclasses.replace` change
  - Rationale: the dropped flags are provably INERT (verified this phase): `disengaged` has zero consumers repo-wide; `is_creature` on `npcs_present` is consumed only by the ship-scale firewall which runs BEFORE the rebind; the rebind fires only on a roster hit, so no downstream code reads the mention's flags. The mention object is never returned or exposed after the rebind. A behavioral test would therefore be vacuous or require a banned source-shape assertion — both forbidden by test-quality rules. This matches the Reviewer's own 162-2 classification ([LOW][TYPE], inert).
  - Severity: minor
  - Forward impact: Dev applies `dataclasses.replace(materialized_threat, name=known.core.name)` at the head-check rebind (~encounter_lifecycle.py:1940); Reviewer verifies by inspection. If a future story makes any of these flags load-bearing post-rebind, a behavioral guard becomes writable and should be added then.
- **Item 5 comment #2 ("edge publish uses find_creature_core") verified by inspection, not test**
  - Spec source: context-story-162-10.md, AC5
  - Spec text: "encounter_lifecycle.py comments are accurate (no false claims about span emission or resolution path)"
  - Implementation: comment #1 (case-variant rebind is span-silent) IS behaviorally pinned by `test_case_variant_head_check_rebind_is_span_silent`; comment #2 (which function edge-publish resolves through) is a doc-only claim about a sibling function's internals and is inspection-only
  - Rationale: asserting "function X does NOT call function Y" is a source-shape test (banned). The correct resolution-path is verified behaviorally elsewhere (1d edge-publish test) and by inspection.
  - Severity: trivial
  - Forward impact: Reviewer confirms the two comment lines against the post-1d code path (see the item-5/1d interaction Finding).

### Dev (implementation)
- **Fixed the untested hp_depletion pool-member leg alongside the tested Fate leg**
  - Spec source: context-story-162-10.md, AC1 (item 1b) + TEA pool-member Gap finding
  - Spec text: "pool-member lookup: seeder's `m.name == actor.name` (NpcPoolMember leg)"
  - Implementation: applied `normalize_name(m.name) == normalize_name(actor.name)` to BOTH `_seed_fate_opponents` (~L748, has a RED test) AND `_seed_combat_hp_depletion_to_npcs` (~L442, NO RED test)
  - Rationale: same bug class, same one-line fix; Amos's finding names both legs; fixing one exact-match while leaving the other is a No-Half-Wired violation
  - Severity: minor
  - Forward impact: none — behavior-preserving for exact-name pool members; only diacritic/case-variant names change (promote instead of fabricate a stub)
- **Added seat-name canonicalization to the Fate + edge-publish seams (no RED test asserts it directly)**
  - Spec source: TEA reachability Improvement finding; mirrors the hp_depletion seeder (encounter_lifecycle.py:425)
  - Spec text: "an alias-resolved Fate seat should rewrite `actor.name` to canonical (find_creature_core is exact-match)"
  - Implementation: `if npc.core.name != actor.name: actor.name = npc.core.name` after the resolver hit in both `_seed_fate_opponents` and `_publish_combat_edge_to_npcs`
  - Rationale: reachability parity — the Fate resolver / HP-bar filter read the Other by exact `actor.name`; a seat left under the alias is unreachable (the [HIGH] 162-2 bug class one seam over)
  - Severity: minor
  - Forward impact: none — canonical names are what every downstream consumer already expects
- **Added a `diacritic_normalized` match_form label (beyond the literal test requirement)**
  - Spec source: none (no test asserts `match_form` for the diacritic reconciliation)
  - Spec text: n/a
  - Implementation: added a fold-equal branch to `_reconciliation_form` returning `"diacritic_normalized"`
  - Rationale: OTEL honesty — without it a diacritic reconciliation mislabels as `comma_normalized`, a lie the GM-panel lie-detector would surface; the project treats telemetry accuracy as load-bearing (I was already modifying this exact matching path)
  - Severity: trivial
  - Forward impact: a new `match_form` value appears on `npc.referenced` spans; consumers already treat `match_form` as a free string

### Reviewer (audit)

- **TEA — Item 4 (NpcMention rebind) ships with no behavioral test** → ✓ ACCEPTED by Reviewer: the inertness reasoning is sound and independently corroborated (test-analyzer confirmed reverting/flag-setting is invisible today); `dataclasses.replace` is a genuine correctness improvement. A behavioral test would be contrived — agrees with author.
- **TEA — Item 5 comment #2 verified by inspection, not test** → ✓ ACCEPTED by Reviewer: "function X does not call Y" is a banned source-shape assertion; inspection is the correct verification. Comment-analyzer confirmed both corrected comments are accurate.
- **Dev — Fixed the untested hp_depletion pool-member leg alongside the tested Fate leg** → ✓ ACCEPTED (intent) by Reviewer: fixing both legs is correct (No Half-Wired). BUT the execution shares the [HIGH] reachability brick — both pool-promotion branches now match variant names without canonicalizing `actor.name`. The *decision to fix both* is right; the *omission of seat canonicalization* is the blocking finding above. Not a flaw in the deviation itself.
- **Dev — Added seat-name canonicalization to the Fate + edge-publish seams** → ✗ FLAGGED by Reviewer: the canonicalization was added to the roster-hit path (`npc is not None`) but NOT the pool-promotion path (`npc is None`) in either seeder — this is the exact gap that produces the [HIGH] brick. The deviation's own rationale ("find_creature_core is exact-match; a seat left under the alias is unreachable") applies verbatim to the pool-promotion path it skipped. Fix must extend the same canonicalization to the promotion branches. (See [HIGH] in the severity table.)
- **Dev — Added a `diacritic_normalized` match_form label** → ✓ ACCEPTED by Reviewer: OTEL honesty is a sound reason to exceed the literal test. Noted: the label is emitted but unasserted (folded into the [MEDIUM][TEST] telemetry finding — add the assertion in rework).
- **UNDOCUMENTED (Reviewer):** Item 3's build-time canonicalization was scoped to the generic combat build path only; the sealed-letter build path (encounter_lifecycle.py:2171-2182) was left un-canonicalized without a logged deviation. Severity: L (deferred — ship-scale mode, unobserved; captured as a Delivery Finding).

**Round 2 audit (re-review):**
- The round-1 ✗ FLAGGED deviation ("Dev — Added seat-name canonicalization to the Fate + edge-publish seams" — flagged for skipping the pool-promotion path) is now **RESOLVED**: the rework (commit `75acd68f`) extended the same canonicalization to BOTH pool-promotion branches (encounter_lifecycle.py:474-475, :804-805). Mutation-verified. The flag is cleared.
- No NEW spec deviations introduced by the rework. The Dev rework deviation entry ("No new spec deviations this round") is ✓ ACCEPTED — the fix is exactly the canonicalization the reviewer finding + TEA tests specified.