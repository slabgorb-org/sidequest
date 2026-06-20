---
story_id: "126-33"
jira_key: ""
epic: ""
workflow: "tdd"
---
# Story 126-33: [BUG] Dedup inventory grants

## Story Details
- **ID:** 126-33
- **Jira Key:** (none — Jira not enabled)
- **Workflow:** tdd
- **Points:** 2
- **Type:** bug
- **Priority:** p3
- **Stack Parent:** none
- **Repository:** sidequest-server
- **Branch:** feat/126-33-dedup-inventory-grants
- **Branch Strategy:** gitflow (base: develop, per .pennyfarthing/repos.yaml server.default_branch)

## Story Summary

When a character receives an inventory item via `state.inventory_update` with action='gained', the engine currently appends a duplicate if the character already holds an item with the same name/id. This violates the idempotency principle and creates redundant stacks.

**Observed bug:** In the Oz world (turn 7), the character was re-granted 'silver shoes' → inventory contained `['silver shoes','silver shoes']` (duplicate stack instead of merge).

**Root cause:** The inventory apply path does not check for existing item matches before appending.

**Fix scope:** Server-side dedup logic in the inventory_update handling — check if an item with the same name/id exists before adding; if so, merge or skip (no-op).

## Workflow Tracking
**Workflow:** tdd
**Phase:** finish
**Phase Started:** 2026-06-20T09:04:54Z

### Phase History
| Phase | Started | Ended | Duration |
|-------|---------|-------|----------|
| setup | 2026-06-20T08:34:20+00:00 | 2026-06-20T08:38:31Z | 4m 11s |
| red | 2026-06-20T08:38:31Z | 2026-06-20T08:48:59Z | 10m 28s |
| green | 2026-06-20T08:48:59Z | 2026-06-20T08:54:38Z | 5m 39s |
| review | 2026-06-20T08:54:38Z | 2026-06-20T09:04:54Z | 10m 16s |
| finish | 2026-06-20T09:04:54Z | - | - |

## Technical Approach

### Root Cause Analysis
The inventory grant mechanism in `sidequest/server/dispatch/inventory_lifecycle.py` (or equivalent location) applies granted items without checking for prior matches. The bug manifests when:
1. A character is initially granted an item (e.g., in an opening scene or via a placement effect).
2. The same item is re-granted later (e.g., via re-narration after a RESUME or a scenario re-trigger).
3. Instead of merging/skipping, a duplicate entry is added to `core.inventory`.

### Acceptance Criteria

1. **Dedup on match:** When `state.inventory_update` processes an action='gained' event for an item whose name or id matches an existing inventory entry, the engine must treat it as a no-op (or merge if quantities are tracked — verify the schema).

2. **No silent fallback:** The dedup must be explicit in the code; add an OTEL span or log entry so the GM panel can verify the dedup occurred (lie-detector principle).

3. **Preserve semantics:** If the item has quantity/charge metadata, the merge must preserve or increment the quantity (do not silently drop duplicates).

4. **Unit test:** Add a test case driving a state.inventory_update with a duplicate item and asserting the inventory does not grow (or quantity increases if tracked).

5. **Wiring test:** Repro the Oz turn-7 case — initial 'silver shoes' grant + re-grant on a snapshot → verify the inventory dedup fires and the span/log event is present.

### Implementation Plan

1. **Locate the apply path:** Find the inventory_update handler that processes action='gained' events (likely `sidequest/server/dispatch/inventory_lifecycle.py` or inlined in `narration_apply.py`).

2. **Add dedup check:** Before appending a new item, scan the existing `core.inventory` list for a match (by id first, then by name if id is missing; exact match to avoid false positives).

3. **Emit OTEL span:** On dedup detection, emit a span (or increment a counter) so the GM panel records the dedup event.

4. **Update tests:** 
   - Unit test: drive `state.inventory_update` with action='gained' for a duplicate item; assert no duplicate is added.
   - Wiring test: load the Oz snapshot (turn 7), re-grant the silver shoes, and verify the inventory does not grow and the dedup span fires.

### Files to Modify

- `sidequest/server/dispatch/inventory_lifecycle.py` (if separated from narration_apply.py)
- `sidequest/server/dispatch/narration_apply.py` (if inventory logic is inlined here)
- `tests/server/dispatch/test_inventory_*.py` (or equivalent)
- Possibly `sidequest/game/character.py` (if inventory model changes are needed)

## Workflow Execution

**Workflow Type:** phased (TDD: setup → red → green → review → finish)
**Next Agent:** tea (Test Engineer — RED phase to establish test coverage)
**Starting Command:** N/A (phased workflows transition via exit protocol)

## Delivery Findings

No upstream findings at setup phase.

### TEA (test design)
- **Question** (non-blocking): Should a duplicate `gained` of a quantity-tracked item no-op or merge quantities? AC #1 offers both; I pinned no-op (see Design Deviations). Affects `tests/server/test_126_33_inventory_dedup.py::test_dedup_does_not_increment_quantity` (flip expected quantity to 2 if merge is chosen) and the Dev fix's apply branch. This is adjacent to 126-35 (item→aspect promotion, a Keith design call). *Found by TEA during test design.*
- **Improvement** (non-blocking): The `gained` lane was the lone inventory lane without an identity check — `items_lost`/`items_discarded`/`items_consumed` already scan `core.inventory.items` by case-folded name (narration_apply.py ~5032/5057/5096), and the 45-13 container gate already blocks re-emitted *container* retrievals. Dev should reuse that case-fold matching idiom for consistency. Affects `sidequest/server/narration_apply.py` (the `for entry in result.items_gained` block, ~4856–5020; the dedup belongs right before the `recipient_char.core.inventory.items.append(item_dict)` at line ~4994, after recipient resolution so it dedups against the *recipient's* ledger per ADR-037 per-player inventory). *Found by TEA during test design.*

### Dev (implementation)
- **Improvement** (non-blocking): `_narrator_item_dict` mints the stored item `id` from the *name* (`narrator:{slug}`) and discards any `id` the narrator emitted on the entry. This is why the dedup must match against the entry's raw `entry["id"]` in addition to the minted `item_dict["id"]`. It is also a latent inconsistency — a narrator that re-references an item by its real id but renames it would otherwise mint a fresh id; out of 126-33 scope but worth a future hardening (have the bare mint honour an explicit `narrator:`-prefixed entry id). Affects `sidequest/server/narration_apply.py::_narrator_item_dict` (~4819-4834). *Found by Dev during implementation.*
- No other upstream findings during implementation.

### Reviewer (code review)
- **Improvement** (non-blocking): Dedup is state-blind — it matches against `Discarded`-state entries the `items_discarded` lane leaves in the list, so a legitimate re-acquisition of a previously-dropped item is suppressed (stays Discarded). Affects `sidequest/server/narration_apply.py` (the new dedup loop, ~5020-5025: match only `state=="Carried"` entries, or flip a matched Discarded entry back to Carried). Outside 126-33's ACs. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Comment accuracy in the new block — "id-first then case-folded name" (it's a flat set-intersection, no ordering) and "`_narrator_item_dict` mints id from name (dropping entry's id)" (true only on the mint branch, not the catalog branch). Code is correct; wording misleads. Affects `sidequest/server/narration_apply.py` (~5001, 5004) and the test docstring's "case-folded" vs `.lower()`. A quick wording fix. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): Test coverage gaps worth a follow-up — (a) intra-list duplicates (`items_gained=[shoes, shoes]` in one call), (b) catalog-resolved↔narrator-mint cross-path dedup (name-match path), (c) MP `for_player` multi-recipient dedup. All currently correct-but-unverified. Affects `tests/server/test_126_33_inventory_dedup.py`. *Found by Reviewer during code review.*
- **Improvement** (non-blocking): The 4 inventory lanes (gained dedup, lost, discarded, consumed) now each hand-roll case-folded identity matching; a shared `_inventory_identity_match` helper would DRY them. Affects `sidequest/server/narration_apply.py`. Out of scope here. *Found by Reviewer during code review.*

## Impact Summary

**Upstream Effects:** 1 findings (0 Gap, 0 Conflict, 0 Question, 1 Improvement)
**Blocking:** None

- **Improvement:** `_narrator_item_dict` mints the stored item `id` from the *name* (`narrator:{slug}`) and discards any `id` the narrator emitted on the entry. This is why the dedup must match against the entry's raw `entry["id"]` in addition to the minted `item_dict["id"]`. It is also a latent inconsistency — a narrator that re-references an item by its real id but renames it would otherwise mint a fresh id; out of 126-33 scope but worth a future hardening (have the bare mint honour an explicit `narrator:`-prefixed entry id). Affects `sidequest/server/narration_apply.py::_narrator_item_dict`.

### Downstream Effects

- **`sidequest/server`** — 1 finding

### Deviation Justifications

1 deviation

- **Dedup pinned as no-op (quantity unchanged), not quantity-merge**
  - Rationale: The observed bug is the narrator *re-narrating one acquisition* (Oz silver shoes — a single unique item mentioned twice), structurally identical to the 45-13 container double-retrieval, which is handled by *blocking* (no count-up). Incrementing quantity on every re-narration would reproduce the same inflation in a different field. The `quantity` model field exists (default 1) but items currently "arrive as quantity=1 singletons" (narration_apply.py comment), so there is no reliable signal distinguishing a genuine restock from a re-narration.
  - Severity: minor
  - Forward impact: If the team chooses quantity-merge instead (a Keith design call, adjacent to 126-35's item→aspect promotion question), exactly one test changes — flip the expected quantity in `test_dedup_does_not_increment_quantity` to 2. The no-duplicate-ENTRY contract (the other 7 tests) is unaffected either way. Surfaced as a non-blocking Question below.

## Design Deviations

### TEA (test design)
- **Dedup pinned as no-op (quantity unchanged), not quantity-merge**
  - Spec source: context-story-126-33.md, AC #1 + "Key Invariants" (Preserve semantics)
  - Spec text: "If a match exists, the grant is a no-op (or merges if the item tracks quantities)" / "If items track quantity, merge the quantities; do not silently drop the second grant."
  - Implementation: `test_dedup_does_not_increment_quantity` asserts the surviving entry's `quantity` stays at its prior value (1), i.e. the duplicate is suppressed, not counted up. The "do not silently drop" invariant is satisfied by the required `item_gain.deduped` watcher event (the dedup is loud, not silent) rather than by incrementing quantity.
  - Rationale: The observed bug is the narrator *re-narrating one acquisition* (Oz silver shoes — a single unique item mentioned twice), structurally identical to the 45-13 container double-retrieval, which is handled by *blocking* (no count-up). Incrementing quantity on every re-narration would reproduce the same inflation in a different field. The `quantity` model field exists (default 1) but items currently "arrive as quantity=1 singletons" (narration_apply.py comment), so there is no reliable signal distinguishing a genuine restock from a re-narration.
  - Severity: minor
  - Forward impact: If the team chooses quantity-merge instead (a Keith design call, adjacent to 126-35's item→aspect promotion question), exactly one test changes — flip the expected quantity in `test_dedup_does_not_increment_quantity` to 2. The no-duplicate-ENTRY contract (the other 7 tests) is unaffected either way. Surfaced as a non-blocking Question below.

### Dev (implementation)
- No deviations from spec. Implemented the dedup exactly per TEA's contract (id-first then case-folded name, no-op on match, `item_gain.deduped` watcher event). Agreed with the pinned no-op semantics over quantity-merge (it matches the 45-13 container-retrieval precedent and the singleton-only inventory today). One implementation detail required to satisfy `test_dedup_matches_by_id_when_names_differ` — the entry's *raw* `id` is included in the match key set because `_narrator_item_dict` mints the stored id from the name and discards the entry's declared id (see Delivery Findings). That is required by the test, not a deviation from it.

### Reviewer (audit)
- **TEA: "Dedup pinned as no-op (quantity unchanged), not quantity-merge"** → ✓ ACCEPTED by Reviewer: sound and well-evidenced. The observed bug is narrator re-narration of one acquisition (Oz silver shoes), structurally identical to the 45-13 container double-retrieval which blocks (no count-up); inventory items are quantity=1 singletons today with no restock-vs-re-narration signal; and "don't silently drop" is satisfied by the loud `item_gain.deduped` event. The no-op-vs-merge fork is correctly surfaced as a non-blocking Question for Keith's design call (adjacent to 126-35), with the single test to flip identified.
- **Dev: "No deviations from spec"** → ✓ ACCEPTED by Reviewer: confirmed — the implementation matches TEA's test contract exactly; including the entry's raw id in the match set is required by `test_dedup_matches_by_id_when_names_differ`, not a divergence.
- No undocumented deviations found. The fix's scope matches the ACs; the one behavior change beyond the ACs (state-blind dedup vs the discarded lane) is captured as a non-blocking Delivery Finding, not a silent spec divergence.

## SM Assessment

**Setup complete — routing to TEA (Amos Burton) for the RED phase.**

- **Story scope (confirmed):** Scoped 2pt server-only bug. A `state.inventory_update` with action `gained` for an item the character already holds (same name/id) must dedup/merge — a no-op or quantity-merge — instead of appending a duplicate stack. Repro: Oz turn-7 re-granted 'silver shoes' → inventory `['silver shoes','silver shoes']`.
- **Workflow:** `tdd` (phased). Explicit on the story; respected over the trivial fallback because a bug fix benefits from a failing repro test first (write the dup, then kill it).
- **Repo / branch:** `sidequest-server` on `feat/126-33-dedup-inventory-grants`, based on `develop` (gitflow, per `.pennyfarthing/repos.yaml server.default_branch`). Branch was missing after sm-setup returned and created manually; session branch-base note corrected.
- **Jira:** None — this project tracks in `pf sprint` YAML only (by design). Not a gap.
- **Merge gate:** Clear — no open PRs, nothing in progress/in-review.
- **For TEA:** File-location hints in the Technical Approach (`inventory_lifecycle.py` / `narration_apply.py`) are guesses from setup — verify the actual apply path before writing the RED test. The lie-detector requirement stands: the dedup must be observable (OTEL span / log) per the project's OTEL principle, and confirm whether inventory items carry quantity/charge metadata so the merge preserves it rather than silently dropping the dup.

## TEA Assessment

**Tests Required:** Yes
**Reason:** Scoped server bug fix — TDD repro-first is correct.

**Test Files:**
- `tests/server/test_126_33_inventory_dedup.py` — 8 tests driving the real `_apply_narration_result_to_snapshot` production path against the `gained` inventory lane.

**Verified apply path (setup hints were guesses):** There is no `inventory_lifecycle.py`. The bug lives in `sidequest/server/narration_apply.py`, function `_apply_narration_result_to_snapshot` (line 3734), in the `for entry in result.items_gained` block. Line 4994 `recipient_char.core.inventory.items.append(item_dict)` is a bare append with **no identity check** — that is the bug. Every sibling lane (`items_lost`/`items_discarded`/`items_consumed`) already matches by case-folded name before mutating; the 45-13 container gate already blocks re-emitted *container* retrievals. The `gained` lane is the outlier.

**Inventory model:** `core.inventory.items` is `list[dict]` (`creature_core.py:98`); each entry carries `id` (`narrator:<slug>` for mints), `name`, `quantity` (default 1), `state`, etc. Items "arrive as quantity=1 singletons" today.

**Tests Written:** 8 tests covering 4 of 5 ACs directly (AC #5 no-regression covered by the two guards).

| Test | AC | Asserts |
|------|----|---------|
| `test_regrant_same_item_does_not_create_duplicate_stack` | #1, #3 | Oz turn-7 repro — re-grant → exactly one entry |
| `test_dedup_against_preexisting_inventory_item` | #1 | dedup vs item already on a loaded snapshot |
| `test_dedup_is_case_insensitive_on_name` | #1 | 'Silver Shoes' vs 'silver shoes' → one entry |
| `test_dedup_matches_by_id_when_names_differ` | #1 | id-first identity match |
| `test_regrant_emits_inventory_dedup_watcher_event` | #2 | `item_gain.deduped` (component=inventory) fires, names item |
| `test_distinct_items_are_not_over_blocked` | #5 | distinct items still stack; no spurious dedup event |
| `test_fresh_first_grant_lands_and_emits_no_dedup` | #5 | happy path intact |
| `test_dedup_does_not_increment_quantity` | #1 | no-op semantics (quantity unchanged) — see deviation |

**Status:** RED confirmed (Machine Shop, RUN_ID 126-33-tea-red). 6 fail on real assertions (duplicate stack created; `item_gain.deduped` never fires — current emits two `item_gain.narrator_minted` + `state_transition`). 2 regression guards pass on current code (no over-block today). Zero collection/import/fixture errors.

### Rule Coverage

No `.claude/rules/` dir; `python.md` lang-review is a Dev self-review checklist (mostly implementation-side). The project rules that drove this test design:

| Rule (source) | Test(s) | Status |
|---------------|---------|--------|
| No Silent Fallbacks → dedup observable (CLAUDE.md / OTEL principle, AC #2) | `test_regrant_emits_inventory_dedup_watcher_event` | failing |
| Every suite needs a wiring test (CLAUDE.md) | all 8 drive the real `_apply_narration_result_to_snapshot` | failing/guard |
| No source-text wiring tests (CLAUDE.md) | (compliance) no `read_text()` sentinels — behavior + watcher-event assertions only | n/a |
| python.md #6 test quality — patch where used, no vacuous asserts | `captured_events` patches `narration_apply._watcher_publish`; every test asserts a concrete value | pass (self-check) |
| ADR-037 per-player inventory | dedup specified to run after recipient resolution (Delivery Finding) | n/a |

**Rules checked:** 5 applicable project rules have explicit coverage or compliance.
**Self-check:** 0 vacuous tests (every assertion checks a concrete list/count/field; no `assert True`, no bare truthy, no `let _`).

**Telemetry contract for Dev:** emit `_watcher_publish("item_gain.deduped", {"name": ..., "id": ..., ...}, component="inventory")` when a duplicate is suppressed. Captured in tests by monkeypatching `narration_apply._watcher_publish` (synchronous — no watcher-hub loop needed).

**Handoff:** To Dev (Naomi Nagata) for GREEN — implement the identity dedup (id-first, then case-folded name) before the line-4994 append, on the resolved recipient's ledger, emitting `item_gain.deduped`. Resolve the no-op-vs-merge Question (non-blocking) if you disagree with the pinned no-op.

## Dev Assessment

**Implementation Complete:** Yes

**Files Changed:**
- `sidequest/server/narration_apply.py` — added the gained-lane identity dedup in `_apply_narration_result_to_snapshot`, inserted after recipient resolution and before the inventory append (~line 4994). Matches id-first then case-folded name against the resolved recipient's ledger; the incoming key set is `{item_dict.id, item_dict.name, entry.id}` (all strip+casefold) vs each existing entry's `{id, name}`, matched on non-empty set intersection. On match: no-op (quantity untouched), emit `_watcher_publish("item_gain.deduped", {...}, component="inventory", severity="warning")` + a `state.inventory_dedup` warning log, then `continue` (skips the append, the `added_names` record, and the Fate item→aspect promotion). Net +64 lines, one block.

**Approach:** Minimal, mirrors the sibling lanes' case-fold matching idiom (no new helper). I confirmed `_narrator_item_dict` mints the id from the name (discarding the entry's declared id), which is why the entry's raw id is in the match set — captured as a Delivery Finding.

**Tests:** 8/8 story tests passing (GREEN, RUN_ID 126-33-dev-green). Regression: 46/46 neighboring inventory-apply-path tests passing (`test_item_gain_catalog_resolution`, `test_container_retrieval_state`, `test_fate_item_promotion_wiring`, `test_mp_item_recipient_attribution`, `test_126_25_world_tier_fate_gear_wiring`, `test_inventory_wiring`). 54/54 total.

**Quality gates:** `ruff check` clean, `ruff format` clean. `pyright` on the file shows 37 errors — verified identical count with and without my change (pre-existing, lines ~6981+, the WN/Fate `ResolutionSignal` typing drift); zero in my edited region (4990-5070).

**Branch:** feat/126-33-dedup-inventory-grants (pushed to origin).

**Handoff:** To Reviewer (Chrisjen Avasarala) for code review.

## Subagent Results

| # | Specialist | Received | Status | Findings | Decision |
|---|-----------|----------|--------|----------|----------|
| 1 | reviewer-preflight | Yes | clean | none (8/8 tests, 0 smells, 0 new pyright errors) | N/A |
| 2 | reviewer-edge-hunter | No | Skipped | disabled | Disabled via settings (covered by Reviewer) |
| 3 | reviewer-silent-failure-hunter | No | Skipped | disabled | Disabled via settings (covered by Reviewer) |
| 4 | reviewer-test-analyzer | Yes | findings | 3 medium (coverage gaps), 2 low | confirmed 0, deferred 5 (non-blocking improvements) |
| 5 | reviewer-comment-analyzer | Yes | findings | 2 high, 1 medium, 1 low (comment accuracy) | confirmed 4 (non-blocking, Low–Medium) |
| 6 | reviewer-type-design | No | Skipped | disabled | Disabled via settings (covered by Reviewer) |
| 7 | reviewer-security | No | Skipped | disabled | Disabled via settings (covered by Reviewer) |
| 8 | reviewer-simplifier | No | Skipped | disabled | Disabled via settings (covered by Reviewer) |
| 9 | reviewer-rule-checker | Yes | findings | 1 (rule #4/#13, high-confidence existence) | confirmed 1, downgraded to Low with evidence |

**All received:** Yes (4 ran, 5 disabled via `workflow.reviewer_subagents`)
**Total findings:** 5 confirmed (all non-blocking, Low–Medium), 5 deferred (non-blocking coverage improvements), 0 dismissed

## Rule Compliance

Rubric = `.pennyfarthing/gates/lang-review/python.md` (13 checks) + CLAUDE.md/SOUL.md principles. Exhaustive over the new dedup block (`narration_apply.py` ~4994-5060) and the test file.

| # | Rule | Verdict | Evidence |
|---|------|---------|----------|
| 1 | Silent exception swallowing | ✓ compliant | No try/except in the new block; `.get()`+`str()` coercions; `_watcher_publish`'s no-subscriber drop is documented/expected, not an error path. The dedup is the *anti*-silent-fallback: it fires `item_gain.deduped`. |
| 2 | Mutable default args | ✓ compliant | No new defaults; `_gain(*names)` is var-positional; `_silver_shoes_dict()` returns a fresh dict. |
| 3 | Type annotations at boundaries | ✓ compliant | `_apply_narration_result_to_snapshot` already annotated; no new params. Test helpers `_apply`/`_names` unannotated but private (rule-exempt). |
| 4 | Logging coverage AND correctness | ⚠ Low | `logger.warning` level correct (client-error path, parity with `container_retrieval_blocked`); %-args not f-string ✓. `[RULE]` finding: log uses `player_name` while the watcher uses `narrating_name` — **downgraded to Low**: every sibling log in this region (`container_gate_unreachable` 4866, `container_retrieval_blocked` 4900, `inventory_discard_miss` 5133) uses `player_name`; the file convention is logs→`player_name`, watchers→`narrating_name`. My log follows convention; the watcher (the GM-panel identity that matters) correctly carries `narrating_name`. |
| 5 | Path handling | ✓ n/a | No path ops. |
| 6 | Test quality | ✓ compliant | 8 tests, all with concrete assertions; monkeypatch targets `narration_apply._watcher_publish` (where USED); no `assert True`, no skips, no parametrized-same-path, no `read_text()` source-text sentinels. |
| 7 | Resource leaks | ✓ n/a | No resources opened. |
| 8 | Unsafe deserialization | ✓ n/a | No pickle/yaml.load/eval/subprocess. |
| 9 | Async pitfalls | ✓ n/a | Sync function, sync block. |
| 10 | Import hygiene | ✓ compliant | No new imports in prod block; `_watcher_publish` already imported (line 136). Test imports all used; no star/circular. |
| 11 | Input validation | ✓ compliant | All key values `str(...or"").strip().lower()`; empties filtered; no sink (SQL/HTML/path/regex). |
| 12 | Dependency hygiene | ✓ n/a | No dep changes. |
| 13 | Fix-introduced regressions | ✓ (see #4) | Only the #4 log-var item; downgraded as above. No exception/mutable/type regressions. |

**SOUL/CLAUDE principles:** No Silent Fallbacks ✓ (dedup observable via `item_gain.deduped`). OTEL Observability ✓ (subsystem decision emits a watcher event — GM-panel lie-detector). ADR-037 per-player inventory ✓ (dedup runs on the *resolved* `recipient_char` ledger — confirmed by comment-analyzer + rule-checker). Every-suite-needs-a-wiring-test ✓ (all 8 drive the real production fn). No source-text wiring tests ✓.

## Reviewer Assessment

**Verdict:** APPROVED

The fix is correct, minimal, and well-tested. The `items_gained` lane was the lone inventory lane appending without an identity check; the dedup closes it, runs on the ADR-037-resolved recipient ledger, is no-op (not count-up), and is observable via `item_gain.deduped` (the OTEL lie-detector AC #2 demands). 8/8 story tests + 46/46 neighbor tests green, lint/format clean, zero new type errors. No Critical/High findings; everything below is non-blocking.

**Observations (≥5, tagged by source):**
- `[VERIFIED]` Dedup runs on the resolved recipient's ledger — `narration_apply.py:4988-5024`: `resolve_item_recipient(...)` then the match loop over `recipient_char.core.inventory.items`. Complies with ADR-037 per-player inventory. Confirmed independently by `[DOC]` and `[RULE]`.
- `[VERIFIED]` Observability present and correct — `narration_apply.py:5033-5048` emits `item_gain.deduped` (component=inventory) with the item name; the test asserts it (`test_regrant_emits_inventory_dedup_watcher_event`). Satisfies the OTEL principle + AC #2.
- `[VERIFIED]` No-op semantics, no data loss — `continue` at the match branch skips `append`, `added_names`, and Fate promotion; quantity untouched. `test_dedup_does_not_increment_quantity` pins it. The "don't silently drop" invariant is met by the loud event, not by counting up. Design call documented + reviewer-accepted (see Deviation Audit).
- `[EDGE]` (Reviewer; edge-hunter disabled) **Intra-list duplicates handled** — `items_gained=[shoes, shoes]` in one call: the append is per-iteration, so the 2nd iteration sees the 1st in the ledger and dedups. Correct, but **untested** (test-analyzer #1, medium). Non-blocking gap → Delivery Finding.
- `[MEDIUM][EDGE]` (Reviewer) **State-blind dedup vs the discarded lane** — the match scans *all* `inventory.items` regardless of `state`; `items_discarded` (45-14) keeps the entry with `state="Discarded"`. So a player who drops "silver shoes" and later legitimately re-acquires them via narration gets the re-grant **suppressed** (item stays Discarded). Before this change that re-grant added a fresh Carried entry. Narrow behavior change *outside* the story ACs (re-narration dedup). Non-blocking → Delivery Finding (Improvement: match only Carried, or flip Discarded→Carried on match).
- `[TEST]` Coverage gaps (test-analyzer, medium, non-blocking, deferred): (a) intra-list dups; (b) catalog-resolved↔narrator-mint cross-path (id keys diverge; name-match still fires — behavior correct, just unverified); (c) MP `for_player` multi-recipient (dedup structurally uses the resolved recipient; recipient resolution itself is covered by the 11 passing `test_mp_item_recipient_attribution` tests). All → Delivery Findings.
- `[DOC]` Comment accuracy (comment-analyzer, confirmed, Low–Medium, non-blocking): (1) "id-first then case-folded name" overstates an ordering the flat set-intersection doesn't have; (2) "`_narrator_item_dict` mints id from name (dropping entry's id)" is true only on the mint branch, not the catalog branch; (3) "severity parity with container_retrieval_blocked" — same intent, different mechanism (span vs `_watcher_publish`); (4) test docstring "case-folded" vs code `.lower()`. Code is correct in all cases; the comments mislead. → Delivery Finding recommending a quick wording fix.
- `[RULE]` Log identity var (rule-checker, confirmed, **downgraded to Low**) — see Rule Compliance #4: follows the file's logs→`player_name` convention; the watcher correctly uses `narrating_name`. Non-blocking.
- `[SILENT]` (Reviewer; silent-failure-hunter disabled) `[VERIFIED]` No swallowed errors / silent fallback — the dedup is the explicit, loud handling of a previously-silent duplicate; `narration_apply.py:5033-5056` emits both an event and a log.
- `[TYPE]` (Reviewer; type-design disabled) `[VERIFIED]` No stringly-typed regressions — item dicts are the pre-existing `list[dict]` shape (`creature_core.py:98`); the change adds no new types, casts, or signatures.
- `[SEC]` (Reviewer; security disabled) `[VERIFIED]` No security surface — pure in-memory game-state mutation; no auth/tenant/external-input/injection sink. Player names already logged file-wide; not new exposure.
- `[SIMPLE]` (Reviewer; simplifier disabled) `[VERIFIED]` Minimal, no over-engineering — one inline match loop mirroring the sibling lanes; no new helper/abstraction. Could be extracted into a shared `_inventory_identity_match` helper for the 4 lanes, but that's out of scope and not worth the churn here.

**Data flow traced:** narrator `result.items_gained[entry]` → catalog-resolve-or-mint → `item_dict` → `resolve_item_recipient` → **dedup match** (`{item_dict.id, item_dict.name, entry.id}` ∩ existing `{id, name}`) → suppressed+event-emitted on match, else appended. Input is internal game state, not raw user input; safe.

### Devil's Advocate

Argue the code is broken. **First attack — the discard/regain hole.** It's real (see `[MEDIUM][EDGE]`): drop an item, try to pick it back up by narration, and the dedup eats the re-grant, leaving it `Discarded`. A player would experience "I picked up my shoes but I still don't have them." But this is outside the story's ACs and the pre-existing discard-keeps-entry design is the root; degraded gracefully (GM/narrator can correct), so non-blocking — not broken, narrow. **Second attack — over-dedup by name collision.** Two genuinely different items the narrator names identically ("a key" for the brass key and the iron key) would dedup to one. True, but that's an inherent property of name-based identity that already governs the lost/discarded/consumed lanes; consistent, not a new defect, and the narrator naming two distinct items identically is itself the upstream issue. **Third — the catalog cross-path.** Existing narrator-mint (`narrator:silver_shoes`) vs incoming catalog-resolved (`silver_shoes`): ids diverge, so does dedup silently fail? No — both carry name "silver shoes", and name is in the key set, so the name-match fires. Verified by reading the key construction; it's just untested (deferred finding). **Fourth — empty/whitespace identity.** A blank name+id would build an empty `incoming_keys` (the `if key` filter drops empties) → no false match against another blank existing entry. Safe. **Fifth — concurrency/replay.** The apply path is synchronous per turn; no race. On RESUME replay, the dedup is idempotent (that's the point — it makes re-applied grants safe). **Conclusion:** the attacks surface one narrow, out-of-scope behavior change (discard/regain) and a few untested-but-correct paths. None is data corruption or a broken core flow. The fix does exactly what AC #1–#5 require. APPROVED stands.

**Handoff:** To SM (Camina Drummer) for finish-story.