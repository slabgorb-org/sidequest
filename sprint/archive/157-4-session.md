---
story_id: "157-4"
jira_key: ""
epic: "157"
workflow: "tdd"
---
# Story 157-4: [ENGINE] factions on trope/seed + trope gate + seed-deck draw (Seams 3 & 4)

## Story Details
- **ID:** 157-4
- **Jira Key:** (none)
- **Workflow:** tdd
- **Stack Parent:** none (depends_on 157-2, which is complete)

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-21T01:48:06Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-21T01:11:24Z | 2026-06-21T01:13:28Z | 2m 4s |
| red | 2026-06-21T01:13:28Z | 2026-06-21T01:27:49Z | 14m 21s |
| green | 2026-06-21T01:27:49Z | 2026-06-21T01:38:15Z | 10m 26s |
| review | 2026-06-21T01:38:15Z | 2026-06-21T01:48:06Z | 9m 51s |
| finish | 2026-06-21T01:48:06Z | - | - |

## Sm Assessment

**Setup complete — routing to TEA (Amos Burton) for RED.**

- **Story:** 157-4 [ENGINE] factions on trope/seed + trope gate + seed-deck draw (Seams 3 & 4). 5 pts, tdd, server-only.
- **Dependency clear:** depends_on 157-2, merged to server develop as PR #1002 (commit 0f199b0f). Branch `feat/157-4-factions-trope-seed-gate-deck` cut fresh off origin/develop with 157-2 in ancestry. 157-4 does NOT depend on 157-3.
- **Reuse-first (no reinvention):** Seams 3 & 4 wire the existing `zone_eligibility` module from 157-2 — `is_eligible()` predicate + `active_factions(perspective=None)` union resolver. No new resolution logic; only a `factions` field on trope/seed models and candidate-filtering at the trope gate (`trope_tick._gate_activations`) and seed draw (`seed_deck.draw` / `seed_tick.draw_engaged_seed`).
- **Context:** sprint/context/context-story-157-4.md — technical approach + 16 ACs sourced from the design spec (docs/superpowers/specs/2026-06-20-faction-zone-content-eligibility-design.md) Seams 3 & 4 + epic context.
- **Wiring discipline:** ACs include per-seam wiring tests (AC-5.2/5.3) verified via OTEL `zone_eligibility.filtered` spans, not source-grep (AC-5.4). TEA: hold the line on the wiring tests — split-party union (AC-3.5/4.5) and determinism-preservation (AC-4.3) are the load-bearing edges.
- **Gates:** merge-ready clear (no open PRs); Jira explicitly skipped (jira: null in YAML).

## TEA Assessment

**Tests Required:** Yes
**Status:** RED (34 failing, 0 passing, 0 collection errors — verified via testing-runner, RUN_ID 157-4-tea-red)
**Commit:** server `6b2cd6ad` on `feat/157-4-factions-trope-seed-gate-deck`

**Test Files (all in sidequest-server):**
- `tests/game/test_zone_eligibility_trope_seed_models.py` (6) — AC-3.1: `factions` field on `TropeDefinition` + `SeedTrope` (default-empty, round-trip, per-instance/mutable-default guard).
- `tests/game/test_zone_eligibility_trope_gate.py` (14) — Seam 3: drives the real `tick_tropes(snapshot, pack, *, now_turn)` seam; asserts dormant-trope activation flips + the `zone_eligibility.filtered` span.
- `tests/game/test_zone_eligibility_seed_draw.py` (14) — Seam 4: drives the real `draw_engaged_seed(...)` seam; asserts `active_seeds` membership/order + the span.

**Design decisions the DEV must honor (these are what the tests pin):**
1. **Behavior + span only, no source-grep.** Seams are driven through their public functions (`tick_tropes`, `draw_engaged_seed`), NOT the private `_gate_activations` / `SeedDeck.draw()` signatures. The DEV is free to choose where to thread `active`/`zoned` (deck constructor vs. caller pre-pass) as long as behavior holds.
2. **Reuse 157-2.** Filter through `zone_eligibility.is_eligible(content.factions, active_factions(snapshot, pack, perspective=None), zoned=...)` and `world_is_zoned(cartography_for(...))`. No new resolution logic.
3. **Span shape is fixed by key** (matches Seam 1): `subsystem` ∈ {"trope","seed"}, `content_id`, `content_factions` (sorted), `active_factions` (sorted), `region`. A key rename breaks `test_*_emits_filtered_span_on_exclusion`.
4. **AC-4.3 is the trap (`test_zoned_draw_order_is_baseline_minus_excluded`).** The seed filter MUST be a *skip* over the already-shuffled `_ordered` (like `drawn_ids`). A pre-filter of the input `seeds` list re-keys the survivors' shuffle and fails this test. This is the load-bearing edge SM flagged.
5. **Duck-typed permissive fallback.** A pack with no `worlds` attr → `cartography_for` None → unzoned → no filtering, no crash. `test_pack_without_worlds_attr_is_permissive` (both files) guards the EXISTING `test_trope_tick.py` / `test_seed_draw_engagement.py` fixtures from regression. Keep them green.
6. **Both seed draw paths.** Spec/AC name `draw_engaged_seed` + `SeedDeck.draw()`; the bootstrap `ensure_initial_draw` also funnels through `deck.draw()`, so filtering at the deck level covers it for free. Tests exercise `draw_engaged_seed`; DEV should verify the opening hand is filtered too (see Delivery Finding).

### Rule Coverage (python-review-checklist)

| Rule | Test(s) | Status |
|------|---------|--------|
| #2 mutable defaults | `test_*_factions_not_shared_between_instances` (trope + seed) | failing (RED) |
| #6 test quality | self-check pass — every test asserts concrete state/span attrs; no `assert True`, no truthy-only, no `let _ =` | n/a |
| #1 silent failure | exclusion must emit a span (loud) — `test_*_emits_filtered_span_on_exclusion`; a silent skip fails the span assert | failing (RED) |

**Rules checked:** 3 of 13 lang-review rules apply to this additive/pydantic+filter change (the rest — async, path, deserialization, resource leaks, SQL — are not in scope). **Self-check:** 0 vacuous tests found.

**Handoff:** To Dev (Naomi Nagata) for GREEN implementation.

## Dev Assessment

**Implementation Complete:** Yes
**Tests:** 34/34 new passing (GREEN — verified via testing-runner RUN_ID 157-4-dev-green: 3569 passed, 17 skipped DB-gated, 0 regressions). ruff lint + format clean; pyright 0 errors.
**Branch:** `feat/157-4-factions-trope-seed-gate-deck` (pushed to origin)
**Commits:** RED `6b2cd6ad` (tests) → GREEN `feat(157-4): ...` (implementation, pushed)

**Files Changed:**
- `sidequest/genre/models/tropes.py` — AC-3.1: additive `factions: list[str] = Field(default_factory=list)` on `TropeDefinition` + `SeedTrope`.
- `sidequest/game/trope_tick.py` — Seam 3: `tick_tropes` resolves `zoned`/`active`/`region` once (only for a zoned world) and threads them + `pack_tropes_by_id` into `_gate_activations`, which now drops a dormant trope whose `factions` miss the active zone BEFORE the cooldown/cap gates and fires `zone_eligibility.filtered` (subsystem=trope).
- `sidequest/game/seed_deck.py` — Seam 4: `SeedDeck` gains `active_factions`/`zoned`/`region` (keyword, defaulted); `draw()` skips a wrong-zone seed over the already-shuffled `_ordered` (like `drawn_ids` — shuffle/resume-safety untouched, AC-4.3) without marking it drawn, and fires the span (subsystem=seed).
- `sidequest/game/seed_tick.py` — Seam 4 wiring: a `_zone_context(snapshot, pack)` helper feeds the new SeedDeck params at BOTH draw sites (`ensure_initial_draw` + `draw_engaged_seed`), so the opening hand is zone-filtered too.

**Reuse (no reinvention):** all gating runs through 157-2's `zone_eligibility.is_eligible` / `active_factions` / `world_is_zoned` / `cartography_for`. Span shape matches Seam 1 by key.

**Both TEA delivery findings resolved:**
- (Question) opening hand — filtered at the `SeedDeck.draw()` level, so `ensure_initial_draw` is covered, not just `draw_engaged_seed`.
- (Improvement) `_gate_activations` now receives `pack_tropes_by_id` + zone context from `tick_tropes`.

**Self-review (judgment):** ✅ wired end-to-end (the live `tick_tropes`/`draw_engaged_seed`/`ensure_initial_draw` call sites, not new dead helpers) · ✅ follows the Seam-1 pattern (cartography_for→world_is_zoned→active_factions→is_eligible→span) · ✅ ACs met · ✅ permissive-on-unzoned/unresolvable preserves the 11 single-zone packs (No Silent Fallbacks: exclusions are loud spans).

**Handoff:** To next phase (verify/review).

## Design Deviations

### TEA (test design)
- **AC-5.1 (is_eligible truth table) reused from 157-2, not re-authored**
  - Spec source: context-story-157-4.md, AC-5.1
  - Spec text: "Unit tests for `is_eligible()` covering: unzoned, unresolvable, untagged-permissive, tagged-match, tagged-mismatch, `*` sentinel, split-party union"
  - Implementation: That exact truth table already exists and passes in `tests/game/test_zone_eligibility.py` (157-2). I did NOT duplicate it — re-testing an unchanged pure function is noise. 157-4 adds only the NEW surface 157-2 didn't cover: the `factions` field on the trope/seed models + the Seam 3/4 wiring.
  - Rationale: Don't Reinvent; duplicate tests rot and give false coverage signal.
  - Severity: minor
  - Forward impact: none — the predicate is unchanged; if the DEV touches `is_eligible`, the 157-2 suite catches it.

## Delivery Findings

Agents record upstream observations discovered during their phase.
Each finding is one list item. Use "No upstream findings" if none.

**Types:** Gap, Conflict, Question, Improvement
**Urgency:** blocking, non-blocking

<!-- Agents: append findings below this line. Do not edit other agents' entries. -->

### TEA (test design)
- **Question** (non-blocking): The design spec names Seam 4 as `seed_deck.draw()` + `seed_tick.draw_engaged_seed()`, but the bootstrap opening hand (`seed_tick.ensure_initial_draw`) ALSO draws via `deck.draw()` and is not explicitly listed. Affects `sidequest/game/seed_tick.py::ensure_initial_draw` (the opening hand should be zone-filtered too, or a wrong-zone seed lands in the first hand even though it'd be excluded mid-session). Filtering at the `SeedDeck.draw()` level covers both paths for free; if the DEV filters at the caller level instead, wire `ensure_initial_draw` too. *Found by TEA during test design.*
- **Improvement** (non-blocking): `_gate_activations` currently takes only `(active_tropes, *, now_turn)` and has no access to `pack`/`snapshot`/`pack_tropes_by_id`. Seam 3 needs the trope DEFINITION's `factions` (which lives on `TropeDefinition`, looked up via `pack_tropes_by_id`, not on `TropeState`) plus the cartography for `active_factions`. Affects `sidequest/game/trope_tick.py` (thread snapshot/pack/pack_tropes_by_id into the gate — `tick_tropes` already holds all three). *Found by TEA during test design.*

### Dev (implementation)
- No upstream findings during implementation. Both TEA findings above were resolvable within this story and are addressed (see Dev Assessment); they leave no obligation for downstream stories.

### Reviewer (code review)
- **Improvement** (non-blocking): the module-level Pass D overview docstring in `trope_tick.py` (the `tick_tropes` module docstring, ~lines 31-37) was not updated for Seam 3 — it still describes activation as cooldown-then-cap with no mention of the new faction-zone candidate filter, and describes cooldown as `fire_cooldown_until > now_turn` though the gate uses `>=` (the latter is pre-existing drift). Affects `sidequest/game/trope_tick.py` (refresh the Pass D overview to mention the zone filter + fix `>`→`>=`). LOW — the inline comments at `_gate_activations` are accurate and complete. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): test-coverage symmetry gaps surfaced by the test-analyzer — no multi-faction content-tag test at the trope-gate/seed-draw *seams* (the `is_eligible` set-intersection IS covered at the predicate level by `test_zone_eligibility.py::test_is_eligible_no_intersection_is_excluded`, so marginal); no test pinning the cap×zone ordering contract (a zone-excluded trope should emit `zone_eligibility.filtered`, not `cap_blocked`, and not count as queued); and the resume-safety tests use a fresh snapshot per phase rather than one mutated snapshot. Affects `tests/game/test_zone_eligibility_{trope_gate,seed_draw}.py` (a fast-follow test-hardening pass; behavior is correct and GREEN). *Found by Reviewer during code review.*
- **Improvement** (non-blocking): in `ensure_initial_draw`, `SeedDeck.draw()` is called `hand_size` times on one deck, so a persistent wrong-zone seed re-emits `zone_eligibility.filtered` once per draw — span noise on a heavily multi-faction world's opening hand. Affects `sidequest/game/seed_deck.py` (optionally de-dup the per-deck filtered set if it ever matters). LOW — purely cosmetic GM-panel noise, no correctness impact. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 2 findings (0 Gap, 0 Conflict, 0 Question, 2 Improvement)
**Blocking:** None

- **Improvement:** `_gate_activations` currently takes only `(active_tropes, *, now_turn)` and has no access to `pack`/`snapshot`/`pack_tropes_by_id`. Seam 3 needs the trope DEFINITION's `factions` (which lives on `TropeDefinition`, looked up via `pack_tropes_by_id`, not on `TropeState`) plus the cartography for `active_factions`. Affects `sidequest/game/trope_tick.py`.
- **Improvement:** test-coverage symmetry gaps surfaced by the test-analyzer — no multi-faction content-tag test at the trope-gate/seed-draw *seams* (the `is_eligible` set-intersection IS covered at the predicate level by `test_zone_eligibility.py::test_is_eligible_no_intersection_is_excluded`, so marginal); no test pinning the cap×zone ordering contract (a zone-excluded trope should emit `zone_eligibility.filtered`, not `cap_blocked`, and not count as queued); and the resume-safety tests use a fresh snapshot per phase rather than one mutated snapshot. Affects `tests/game/test_zone_eligibility_{trope_gate,seed_draw}.py`.

### Downstream Effects

Cross-module impact: 2 findings across 2 modules

- **`sidequest/game`** — 1 finding
- **`tests/game`** — 1 finding

### Deviation Justifications

1 deviation

- **AC-5.1 (is_eligible truth table) reused from 157-2, not re-authored**
  - Rationale: Don't Reinvent; duplicate tests rot and give false coverage signal.
  - Severity: minor
  - Forward impact: none — the predicate is unchanged; if the DEV touches `is_eligible`, the 157-2 suite catches it.

## Design Deviations

Agents log spec deviations as they happen — not after the fact.
Each entry: what was changed, what the spec said, and why.

<!-- Agents: append deviations below this line. Do not edit other agents' entries. -->

### Dev (implementation)
- **Opening hand (`ensure_initial_draw`) is zone-filtered, slightly beyond the literal AC enumeration**
  - Spec source: context-story-157-4.md, AC-4.1
  - Spec text: "`draw()` and `draw_engaged_seed()` filter candidate seeds ... before selecting from the shuffled deck"
  - Implementation: filtered inside `SeedDeck.draw()` (the design-spec-named seam), which the bootstrap `ensure_initial_draw` also calls — so the opening hand is zone-filtered too, not only the mid-session engagement draw named in AC-4.1.
  - Rationale: filtering at `draw()` is exactly where the design spec ("`game/seed_deck.py draw()`") places it; covering the opening hand is the natural, correct consequence and resolves TEA's non-blocking Question finding. A wrong-zone seed in the very first hand would be the same bleed the epic exists to kill.
  - Severity: minor
  - Forward impact: none — additive; unzoned/legacy packs pass `zoned=False` so existing `ensure_initial_draw` behavior is unchanged (covered by `test_seed_draw_engagement.py` regressions, still green).

### Reviewer (audit)
- **TEA — AC-5.1 reuse of the 157-2 `is_eligible` truth table** → ✓ ACCEPTED by Reviewer: verified `tests/game/test_zone_eligibility.py` (157-2) covers the full truth table including multi-element content intersection (`test_is_eligible_no_intersection_is_excluded` uses `content_factions=[HOUYHNHNM, BROBDINGNAG]`). Re-authoring would be duplicate coverage of an unchanged pure function. Sound.
- **Dev — opening hand (`ensure_initial_draw`) zone-filtered beyond the literal AC-4.1 enumeration** → ✓ ACCEPTED by Reviewer: filtering at `SeedDeck.draw()` is exactly the design-spec-named seam (`game/seed_deck.py draw()`); covering the bootstrap hand prevents the same cross-zone bleed in the very first deal and resolves TEA's non-blocking Question. Regression-safe — unzoned/legacy packs pass `zoned=False` (confirmed by green `test_seed_draw_engagement.py`). Sound.
- **No undocumented deviations found.** The implementation matches the design spec (Seams 3 & 4) and context-story-157-4 ACs; the filter location, span shape, and permissive-fallback all conform.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | 3 minor smells | confirmed 0, dismissed 3 (established convention / readability) |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings — domain assessed manually ([EDGE]) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings — domain assessed manually ([SILENT]) |
| 4 | reviewer-test-analyzer | Yes | findings | 6 (missing-edge-case) | confirmed 0 blocking, deferred 6 (non-blocking coverage gaps) |
| 5 | reviewer-comment-analyzer | Yes | findings | 3 + 5 verified-accurate | confirmed 2 (non-blocking LOW doc), dismissed 1 (pre-existing `>`/`>=`) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings — domain assessed manually ([TYPE]) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings — domain assessed manually ([SEC]) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings — domain assessed manually ([SIMPLE]) |
| 9 | reviewer-rule-checker | Yes | findings | 4 | dismissed 4 (all false positives — evidence in assessment) |

**All received:** Yes (4 enabled returned; 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 0 confirmed blocking, 2 confirmed non-blocking (doc), 6 deferred (test coverage), 5 dismissed (4 rule-checker FPs + 1 pre-existing drift)

## Reviewer Assessment

**Verdict:** APPROVED

A clean, additive, well-tested change that wires Seams 3 & 4 onto the proven 157-2 `zone_eligibility` predicate. 34 new tests GREEN, full game/genre suite GREEN (116 passed in the focused run; 3569 in the broad run), ruff + pyright clean, no regressions (the 2 `test_barsoom_*` failures are pre-existing 89-5 RED, confirmed by a stash-and-rerun during GREEN). No Critical/High/Medium correctness issues across all four enabled subagents and my own pass over the five disabled domains.

**Data flow traced:** player turn → `tick_tropes(snapshot, pack)` resolves `world_is_zoned(cartography_for(...))`; if zoned, `active_factions(snapshot, pack)` (consensus region's `controlled_by`, or split-party union) + `region_for()` → `_gate_activations(..., zoned, active, region)` → per dormant trope, `is_eligible(tdef.factions, active, zoned)`; mismatch → `zone_eligibility.filtered` span + skip. Same shape for seeds: `draw_engaged_seed`/`ensure_initial_draw` → `_zone_context` → `SeedDeck(active_factions, zoned, region)` → `draw()` skips ineligible over the fixed shuffle. The active set is server-derived state, faction tags are authored pack YAML (trusted, opaque string tags) — no untrusted input reaches a query/path/shell.

**Pattern observed:** mirrors Seam 1 (`monster_manual_inject._npc_patches_for_encounters`) exactly — `cartography_for`→`world_is_zoned`→`active_factions`→`is_eligible`→`SPAN_ZONE_ELIGIBILITY_FILTERED` with the identical 5-key forensic attribute shape. No reinvention (SOUL "Don't Reinvent" honored).

**Error handling / failure direction:** fails OPEN, never closed — unzoned world, no-`worlds` pack, unresolvable region, empty active set all return `is_eligible=True` (show content), so the worst case is under-filtering (a wrong-zone item slips through), never a silent empty scene. This is the correct failure direction per the design and CLAUDE.md "No Silent Fallbacks" — every actual exclusion is a loud span.

### Rule Compliance (python-review-checklist, exhaustive)

- **#1 silent exceptions:** no `try/except` added in any changed file; the two skip paths (`seed_deck.draw`, `_gate_activations`) emit a loud span before `continue`. COMPLIANT.
- **#2 mutable defaults:** `TropeDefinition.factions` + `SeedTrope.factions` use `Field(default_factory=list)` (per-instance, pinned by `test_*_factions_not_shared_between_instances`); `SeedDeck.__init__ active_factions=None`, `_gate_activations active=None` — both None-sentinel resolved inside (`set(x) if x else set()` / `x or set()`); `zoned=False`/`region=""` immutable scalars. Every new default checked. COMPLIANT.
- **#3 type annotations:** every new boundary is annotated — `SeedDeck.__init__` (all params + `-> None`), `draw() -> SeedTrope | None`, `_zone_context(...) -> tuple[set[str], bool, str]`, `_gate_activations(...) -> int`, model fields `list[str]`. Pre-existing `ensure_initial_draw`/`draw_engaged_seed` retain `-> None` (verified `seed_tick.py:109`, `:206`). COMPLIANT.
- **#4 logging:** no new logging; existing `logger.warning` (empty-deck) preserved at correct level. COMPLIANT.
- **#5 path / #7 resources / #8 deserialization / #9 async / #12 deps:** not applicable — no file I/O, no resources, no deserialization of untrusted input, no async, no dependency changes. N/A.
- **#6 test quality:** all 34 new tests assert concrete values (status flips, drawn-id ordering/membership, span attrs by key); 0 vacuous (preflight + test-analyzer + my read concur). COMPLIANT.
- **#10 import hygiene:** explicit named imports, no star imports, no cycle (`game/__init__` imports none of these modules — verified). COMPLIANT.
- **#11 input validation:** faction tags are opaque string sets used only for membership tests; no SQL/HTML/path sink. COMPLIANT.
- **#13 fix-introduced regressions:** none — GREEN suite, pre-existing barsoom failures isolated. COMPLIANT.
- **SOUL No Silent Fallbacks + OTEL Observability Principle:** both seam decisions emit `zone_eligibility.filtered`; no silent skip. COMPLIANT.

### Observations

1. `[VERIFIED]` Determinism (AC-4.3) — the shuffle is built once on the full list in `SeedDeck.__init__` and `draw()` skips ineligible over `self._ordered` with `continue` BEFORE `self.drawn_ids.add()` — evidence: `seed_deck.py` draw() body; the skip neither reorders nor marks-drawn. `[TEST]` independently confirmed `test_zoned_draw_order_is_baseline_minus_excluded` is sound (same session_id ⇒ identical shuffle ⇒ a pre-filter impl would fail the `zoned == baseline-minus-s3` assertion).
2. `[VERIFIED]` OTEL/No-Silent-Fallbacks — both skip paths emit `SPAN_ZONE_ELIGIBILITY_FILTERED` with the 5-key shape (`subsystem`/`content_id`/`content_factions`/`active_factions`/`region`) matching Seam 1; `Span.open` (`span.py:17`, a `@contextmanager` that sets attributes at `start_as_current_span`) makes the empty-`pass` body the correct fire-and-forget idiom; emission proven by passing `test_*_emits_filtered_span_on_exclusion`.
3. `[VERIFIED]` Permissive fallback protects the 11 single-zone packs — `is_eligible` returns True for unzoned/no-`worlds`/empty-active; evidence `test_pack_without_worlds_attr_is_permissive` (both files), `test_unzoned_world_*`, and GREEN regression on `test_trope_tick.py` / `test_seed_draw_engagement.py`.
4. `[RULE]` rule-checker rule#3 (missing `-> None` on `ensure_initial_draw`/`draw_engaged_seed`) — DISMISSED: both signatures end `) -> None:` at `seed_tick.py:109` and `:206`. False positive (its cited line numbers were fabricated).
5. `[RULE]` rule-checker rule#6 (`otel_capture` fixture missing) — DISMISSED: defined at `tests/game/conftest.py:178` (yields `InMemorySpanExporter`); all span tests passed in preflight (116/116). False positive (couldn't see conftest in the diff).
6. `[DOC]` comment-analyzer — `trope_tick.py` module Pass D overview omits the new Seam 3 filter and uses `>` where the gate uses `>=`. CONFIRMED, LOW/non-blocking (inline gate comments are accurate); captured as a delivery finding. The `>`/`>=` half is pre-existing drift, not this story's regression.
7. `[TEST]` test-analyzer — 6 missing-edge-case coverage gaps (multi-faction seam tests, cap×zone ordering, single-snapshot resume tests, hub-region seed). MEDIUM/non-blocking — the `is_eligible` intersection is already covered at the predicate level by 157-2; deferred to a fast-follow.
8. `[EDGE]` (subagent disabled — manual) — boundaries handled: empty active set (permissive), `None`/unresolvable region (permissive), split-party union, `"*"` sentinel, missing `tdef`→permissive. No edge defect; the only gap is the seam-level multi-faction *test* (see #7), not behavior.
9. `[SILENT]` (disabled — manual + rule-checker A1) — no swallowed errors; both skip paths are loud spans; permissive branches are intentional and tested both ways. Clean.
10. `[TYPE]` (disabled — manual + rule-checker) — new fields/params fully typed; `tuple[set[str], bool, str]` return accurate; pyright 0 errors. Clean.
11. `[SEC]` (disabled — manual + rule-checker #11) — no auth/tenant/SQL/network/untrusted-deserialization; faction strings opaque; span attributes carry no secrets/PII. Clean.
12. `[SIMPLE]` (disabled — manual + preflight) — minor: `trope_tick` inlines the zone-context resolution while `seed_tick` extracts a `_zone_context` helper (3-line duplication). LOW/non-blocking; otherwise minimal and pattern-faithful. The empty-`pass` span idiom is the codebase convention, not over-engineering.

### Devil's Advocate

Assume it's broken. **Can a wrong-zone item still leak?** The trope/seed filters fail OPEN: if `active_factions` mis-resolves to ∅ (e.g., `region_for` returns None on a non-split party), `is_eligible(content, ∅, zoned=True)` returns True — content shows. So a resolution bug causes *under*-filtering (a Yahoo slips onto the shore), never a silent empty world. That is the deliberate, design-mandated failure direction; the load validator (157-7) is what will turn typo'd faction tags into loud load failures. **Until 157-7, a confused author who writes `factions: [the_houyhnhm_assembly]` (typo) gets silent non-activation in a zoned world** — a real but explicitly-deferred, documented gap, not this story's defect. **Could the determinism claim be a lie?** Only if the shuffle differed between the filtered and unfiltered paths — but it is keyed solely by `session_id` over the full seed list, identical in both, and the filter is a post-shuffle skip; the trap test would catch a pre-filter regression. **Could a malicious/garbage pack crash the engine?** A pack with no `worlds`, a `world_slug` absent from `worlds`, or a region absent from cartography all funnel through `cartography_for`→None→unzoned→permissive; a dormant trope id absent from `pack_tropes_by_id` yields `content_factions=[]`→permissive. No `KeyError`/`AttributeError` path. **Performance under a heavily multi-faction opening hand?** `ensure_initial_draw` re-runs `draw()` per card, re-emitting a filtered span for each persistent wrong-zone seed — GM-panel noise, not a fault (captured as LOW). **Save-compat?** The `factions` field is on the *definition* models (pack YAML), not the saved `TropeState`/`SeedState`, so no migration risk. Nothing here rises above LOW/MEDIUM, and every load-bearing claim (determinism, loud exclusion, permissive fallback) is independently verified. The implementation is correct.

**Handoff:** To SM (Camina Drummer) for finish-story.